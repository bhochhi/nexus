"""Safe interpreter for catalog-defined skill workflows."""

from decimal import Decimal, InvalidOperation
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional

from member_assistant.catalog import BUILTIN_ARCHETYPES
from .base import SkillContext, SkillExecutor, SkillResult


class DeclarativeSkillExecutor(SkillExecutor):
    """Executes only the small, validated operation set defined by the platform."""

    archetypes = tuple(sorted(BUILTIN_ARCHETYPES))

    def execute(self, task: Dict[str, Any], context: SkillContext) -> SkillResult:
        steps = context.definition.workflow["steps"]
        variables = task.setdefault("variables", {})
        task.setdefault("workflow_step", 0)
        completed_steps = task.setdefault("completed_steps", [])
        changed_fields = set(task.pop("updated_input_fields", []))
        current_step = steps[task["workflow_step"]] if task["workflow_step"] < len(steps) else {}
        restart_fields = set(current_step.get("restart_on_input_change", []))
        if changed_fields.intersection(restart_fields):
            task["workflow_step"] = int(current_step["restart_step"])

        while task["workflow_step"] < len(steps):
            step_index = task["workflow_step"]
            step = steps[step_index]
            operation = step["op"]

            with context.observability.observe(
                "workflow.{}".format(operation),
                "chain",
                metadata={
                    "skill": context.definition.name,
                    "skill_version": context.definition.version,
                    "skill_artifact_hash": context.definition.artifact_hash,
                    "risk_tier": context.definition.risk_tier,
                    "step_index": step_index,
                    "operation": operation,
                },
            ) as observation:
                if operation == "collect":
                    result = self._collect(step, task, completed_steps)
                elif operation == "call_tool":
                    result = self._call_tool(
                        step, task, context, variables, completed_steps
                    )
                elif operation == "select":
                    result = self._select(step, task, context, variables, completed_steps)
                elif operation == "validate":
                    result = self._validate(step, task, context, variables, completed_steps)
                elif operation == "validate_decimal":
                    result = self._validate_decimal(
                        step, task, context, variables, completed_steps
                    )
                elif operation == "set":
                    variables[step["save_as"]] = self._resolve(
                        step.get("value"), task, context, variables
                    )
                    self._complete_step(step, completed_steps)
                    task["workflow_step"] += 1
                    result = None
                elif operation == "confirm":
                    result = self._confirm(step, task, context, variables, completed_steps)
                elif operation == "respond":
                    result = self._respond(
                        step, task, context, variables, completed_steps
                    )
                else:  # Catalog validation prevents this branch.
                    raise ValueError("Unsupported workflow operation: {}".format(operation))

                observation.update(
                    output={
                        "status": result.status if result is not None else "continued",
                        "next_step": task.get("workflow_step"),
                    }
                )

            if result is not None:
                return result

        return SkillResult(
            status="completed",
            response=context.definition.response_template,
            inputs=task.get("inputs", {}),
            outcome={"status": "completed"},
            completed_steps=list(completed_steps),
        )

    def _collect(
        self, step: Mapping[str, Any], task: Dict[str, Any], completed_steps: List[str]
    ) -> Optional[SkillResult]:
        inputs = task.setdefault("inputs", {})
        for field in step.get("fields", []):
            name = field["name"]
            if inputs.get(name) in {None, ""}:
                return self._awaiting_input(task, name, field["prompt"], completed_steps)
        self._complete_step(step, completed_steps)
        task["workflow_step"] += 1
        return None

    def _call_tool(
        self,
        step: Mapping[str, Any],
        task: Dict[str, Any],
        context: SkillContext,
        variables: Dict[str, Any],
        completed_steps: List[str],
    ) -> Optional[SkillResult]:
        arguments = self._resolve(step.get("arguments", {}), task, context, variables)
        with context.observability.observe(
            "tool.{}.{}".format(step["tool"], step["action"]),
            "tool",
            input_value=context.observability.content(
                arguments,
                {"argument_names": sorted(arguments), "content_redacted": True},
            ),
            metadata={
                "skill": context.definition.name,
                "tool": step["tool"],
                "action": step["action"],
                "consequential": bool(step.get("consequential", False)),
            },
        ) as observation:
            result = context.tools.invoke(step["tool"], step["action"], arguments)
            summary = {
                "result_type": type(result).__name__,
                "result_count": len(result) if isinstance(result, list) else None,
            }
            observation.update(
                output=context.observability.content(result, summary),
                metadata={"tool_status": "success"},
            )
        if not result and step.get("on_empty"):
            return self._configured_failure(step["on_empty"], task, completed_steps)
        if step.get("save_as"):
            variables[step["save_as"]] = result
        self._complete_step(step, completed_steps)
        task["workflow_step"] += 1
        return None

    def _select(
        self,
        step: Mapping[str, Any],
        task: Dict[str, Any],
        context: SkillContext,
        variables: Dict[str, Any],
        completed_steps: List[str],
    ) -> Optional[SkillResult]:
        collection = self._resolve(step["collection"], task, context, variables) or []
        field_name = step["input"]
        selected_value = str(task.setdefault("inputs", {}).get(field_name, "")).strip()
        threshold = int(
            self._resolve(step.get("auto_select_threshold", 0), task, context, variables)
        )

        if not selected_value and len(collection) <= threshold:
            selected = list(collection)
        elif not selected_value:
            question = self._selection_question(step, collection, invalid=False)
            return self._awaiting_input(task, field_name, question, completed_steps)
        else:
            selected = [
                item for item in collection if self._matches(item, selected_value, step)
            ]
            if not selected:
                task["inputs"].pop(field_name, None)
                # Model-extracted inputs are untrusted hints. Use failure wording only
                # after this exact field was explicitly elicited from the member.
                was_explicit_slot_answer = task.get("missing_field") == field_name
                question = self._selection_question(
                    step, collection, invalid=was_explicit_slot_answer
                )
                return self._awaiting_input(task, field_name, question, completed_steps)

        variables[step["save_as"]] = selected
        self._complete_step(step, completed_steps)
        if (
            not selected_value
            and len(collection) <= int(step.get("jump_if_collection_at_most", -1))
        ) or len(selected) <= int(step.get("jump_if_selected_at_most", -1)):
            task["workflow_step"] = int(step["jump_step"])
        else:
            task["workflow_step"] += 1
        return None

    def _validate(
        self,
        step: Mapping[str, Any],
        task: Dict[str, Any],
        context: SkillContext,
        variables: Dict[str, Any],
        completed_steps: List[str],
    ) -> Optional[SkillResult]:
        rule = step["rule"]
        left = self._resolve(step.get("left"), task, context, variables)
        right = self._resolve(step.get("right"), task, context, variables)
        valid = left != right if rule == "not_equal" else bool(left)
        if not valid:
            return self._configured_failure(step["on_fail"], task, completed_steps)
        self._complete_step(step, completed_steps)
        task["workflow_step"] += 1
        return None

    def _validate_decimal(
        self,
        step: Mapping[str, Any],
        task: Dict[str, Any],
        context: SkillContext,
        variables: Dict[str, Any],
        completed_steps: List[str],
    ) -> Optional[SkillResult]:
        try:
            amount = Decimal(
                str(self._resolve(step["value"], task, context, variables))
            ).quantize(Decimal("0.01"))
            minimum = Decimal(
                str(self._resolve(step.get("minimum", "0.01"), task, context, variables))
            )
            maximum_value = self._resolve(step.get("maximum"), task, context, variables)
            maximum = Decimal(str(maximum_value)) if maximum_value is not None else None
            valid = amount >= minimum and (maximum is None or amount <= maximum)
        except (InvalidOperation, TypeError, ValueError):
            valid = False
            amount = Decimal("0")
        if not valid:
            return self._configured_failure(step["on_fail"], task, completed_steps)
        variables[step["save_as"]] = format(amount, ".2f")
        self._complete_step(step, completed_steps)
        task["workflow_step"] += 1
        return None

    def _confirm(
        self,
        step: Mapping[str, Any],
        task: Dict[str, Any],
        context: SkillContext,
        variables: Dict[str, Any],
        completed_steps: List[str],
    ) -> Optional[SkillResult]:
        review = self._render(
            step["template"], step.get("values", {}), task, context, variables
        )
        if context.confirmation_status != "confirmed":
            self._complete_step(step, completed_steps)
            return SkillResult(
                status="awaiting_confirmation",
                response=review,
                inputs=task.get("inputs", {}),
                pending_question=review,
                completed_steps=list(completed_steps),
            )
        self._append_once(completed_steps, step.get("confirmed_step"))
        task["workflow_step"] += 1
        return None

    def _respond(
        self,
        step: Mapping[str, Any],
        task: Dict[str, Any],
        context: SkillContext,
        variables: Dict[str, Any],
        completed_steps: List[str],
    ) -> SkillResult:
        values = self._resolve(step.get("values", {}), task, context, variables)
        if step.get("items"):
            collection = self._resolve(step["items"], task, context, variables) or []
            values["items"] = step.get("separator", "; ").join(
                step["item_template"].format(**item) for item in collection
            )
        template = step.get("template", context.definition.response_template)
        if step.get("use_model", False):
            generation_input = {"instruction": template, "facts": values}
            with context.observability.observe(
                "llm.grounded_response",
                "generation",
                input_value=context.observability.content(
                    generation_input,
                    {"fact_names": sorted(values), "content_redacted": True},
                ),
                metadata={
                    "skill": context.definition.name,
                    "grounded": True,
                    **context.provider.observability_metadata(),
                },
            ) as observation:
                response = context.provider.generate_response(
                    template, dict(values, template=template)
                )
                observation.update(
                    output=context.observability.content(
                        response, {"response_length": len(response), "content_redacted": True}
                    ),
                    metadata=context.provider.observability_metadata(),
                )
        else:
            trace_name = (
                "response.grounded_template"
                if context.definition.archetype == "knowledge"
                else "response.template"
            )
            with context.observability.observe(
                trace_name,
                "chain",
                metadata={
                    "skill": context.definition.name,
                    "grounded": context.definition.archetype == "knowledge",
                    "model_used": False,
                },
            ) as observation:
                response = template.format(**values)
                observation.update(output={"response_length": len(response)})
        self._complete_step(step, completed_steps)
        task["workflow_step"] += 1
        outcome = self._resolve(
            step.get("outcome", {"status": "completed"}), task, context, variables
        )
        return SkillResult(
            status="completed",
            response=response,
            inputs=task.get("inputs", {}),
            outcome=outcome,
            completed_steps=list(completed_steps),
        )

    def _configured_failure(
        self,
        failure: Mapping[str, Any],
        task: Dict[str, Any],
        completed_steps: List[str],
    ) -> SkillResult:
        field_name = failure.get("field")
        if field_name:
            task.setdefault("inputs", {}).pop(field_name, None)
        if "retry_step" in failure:
            task["workflow_step"] = int(failure["retry_step"])
        status = failure.get("status", "failed")
        response = failure["response"]
        if status == "awaiting_input":
            return self._awaiting_input(task, field_name, response, completed_steps)
        return SkillResult(
            status=status,
            response=response,
            inputs=task.get("inputs", {}),
            outcome=failure.get("outcome", {"status": status}),
            completed_steps=list(completed_steps),
        )

    @staticmethod
    def _awaiting_input(
        task: Dict[str, Any],
        field_name: str,
        question: str,
        completed_steps: List[str],
    ) -> SkillResult:
        return SkillResult(
            status="awaiting_input",
            response=question,
            inputs=task.get("inputs", {}),
            missing_field=field_name,
            pending_question=question,
            completed_steps=list(completed_steps),
        )

    @staticmethod
    def _selection_question(
        step: Mapping[str, Any],
        collection: Iterable[Mapping[str, Any]],
        invalid: bool,
    ) -> str:
        choices_collection = list(collection)
        distinct_by = step.get("choice_distinct_by")
        if distinct_by:
            seen = set()
            choices_collection = [
                item
                for item in choices_collection
                if item.get(distinct_by) not in seen
                and not seen.add(item.get(distinct_by))
            ]
        choices = step.get("separator", "; ").join(
            step["choice_template"].format(**item) for item in choices_collection
        )
        prefix = step.get("invalid_prefix", "") if invalid else ""
        return prefix + step["prompt_template"].format(choices=choices)

    @staticmethod
    def _matches(item: Mapping[str, Any], selected_value: str, step: Mapping[str, Any]) -> bool:
        normalized = " ".join(re.findall(r"[a-z0-9]+", selected_value.casefold()))
        selected_tokens = set(normalized.split())
        if "saving" in selected_tokens:
            selected_tokens.add("savings")
        candidates: List[str] = []
        for field_name in step.get("match_fields", []):
            value = item.get(field_name)
            if isinstance(value, list):
                candidates.extend(str(candidate) for candidate in value)
            elif value is not None:
                candidates.append(str(value))
        for candidate in candidates:
            normalized_candidate = " ".join(
                re.findall(r"[a-z0-9]+", candidate.casefold())
            )
            if normalized == normalized_candidate:
                return True
            candidate_tokens = set(normalized_candidate.split())
            if candidate_tokens and candidate_tokens.issubset(selected_tokens):
                return True
        return False

    def _render(
        self,
        template: str,
        values: Mapping[str, Any],
        task: Dict[str, Any],
        context: SkillContext,
        variables: Dict[str, Any],
    ) -> str:
        return template.format(**self._resolve(values, task, context, variables))

    def _resolve(
        self,
        value: Any,
        task: Dict[str, Any],
        context: SkillContext,
        variables: Dict[str, Any],
    ) -> Any:
        if isinstance(value, str) and value.startswith("$"):
            return self._lookup(value, task, context, variables)
        if isinstance(value, dict):
            return {
                key: self._resolve(item, task, context, variables)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._resolve(item, task, context, variables) for item in value]
        return value

    @staticmethod
    def _lookup(
        reference: str,
        task: Dict[str, Any],
        context: SkillContext,
        variables: Dict[str, Any],
    ) -> Any:
        roots = {
            "inputs": task.get("inputs", {}),
            "vars": variables,
            "task": task,
            "config": context.definition.config,
            "context": {
                "member_ref": context.member_ref,
                "session_id": context.session_id,
                "member_profile": context.member_profile,
            },
        }
        parts = reference[1:].split(".")
        current: Any = roots[parts[0]]
        for part in parts[1:]:
            if isinstance(current, list):
                current = current[int(part)]
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part)
        return current

    @staticmethod
    def _complete_step(step: Mapping[str, Any], completed_steps: List[str]) -> None:
        DeclarativeSkillExecutor._append_once(completed_steps, step.get("completed_step"))

    @staticmethod
    def _append_once(completed_steps: List[str], value: Optional[str]) -> None:
        if value and value not in completed_steps:
            completed_steps.append(value)
