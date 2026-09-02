from decimal import Decimal

from member_assistant.config import PROJECT_ROOT
from member_assistant.providers import (
    DeterministicProvider,
    SkillGap,
    SkillMatch,
    SlotUpdate,
    TurnAnalysis,
)
from member_assistant.tools.accounts import AccountBalance


class _NoisyBalanceProvider(DeterministicProvider):
    """Simulates an LLM that speculatively fills account from the intent text."""

    semantic_turn_understanding = True

    def identify_skills(self, message, catalog, context=None):
        if "balance" in message.casefold():
            return [
                SkillMatch(
                    skill_name="guided_balance",
                    confidence=0.99,
                    inputs={"account": "balance"},
                )
            ]
        return super().identify_skills(message, catalog, context)


class _GapAwareProvider(DeterministicProvider):
    def understand_turn(self, message, catalog, context=None):
        analysis = super().understand_turn(message, catalog, context)
        if not analysis.goals and "online id" in message.casefold():
            return TurnAnalysis(
                goals=[],
                skill_gap=SkillGap(
                    objective="recover your online ID",
                    category="online_id_recovery",
                    confidence=0.96,
                ),
            )
        return analysis


class _CapabilityGapProvider(DeterministicProvider):
    """Simulates a model that incorrectly marks capability help as a skill gap."""

    def understand_turn(self, message, catalog, context=None):
        if "what else" in message.casefold():
            return TurnAnalysis(
                goals=[],
                skill_gap=SkillGap(
                    objective="learn what services are available",
                    category="capability_discovery",
                    confidence=0.96,
                ),
            )
        return super().understand_turn(message, catalog, context)


class _UnknownSkillProvider(DeterministicProvider):
    """Simulates a semantic model returning a skill absent from the catalog."""

    def understand_turn(self, message, catalog, context=None):
        if "online id" in message.casefold():
            return TurnAnalysis(
                goals=[
                    SkillMatch(
                        skill_name="online_id_recovery",
                        confidence=0.86,
                    )
                ]
            )
        return super().understand_turn(message, catalog, context)


class _NaturalTurnProvider(DeterministicProvider):
    """Models semantic multi-slot extraction and natural-number normalization."""

    semantic_turn_understanding = True

    def understand_turn(self, message, catalog, context=None):
        analysis = super().understand_turn(message, catalog, context)
        normalized = message.casefold()
        slot_updates = list(analysis.slot_updates)
        conversation_act = analysis.conversation_act
        relation = analysis.active_goal_relation
        if "from savings 2002 to checking 1001" in normalized:
            slot_updates.extend(
                [
                    SlotUpdate(
                        "source_account", "savings 2002", 1.0, "pending_answer"
                    ),
                    SlotUpdate(
                        "destination_account", "checking 1001", 1.0, "explicit"
                    ),
                ]
            )
            conversation_act = "provide_information"
            relation = "continue"
        if "two hundred" in normalized:
            slot_updates.append(
                SlotUpdate(
                    "amount",
                    "200.00",
                    1.0,
                    "correction" if "actually" in normalized else "pending_answer",
                )
            )
            conversation_act = (
                "correction" if "actually" in normalized else "provide_information"
            )
            relation = "continue"
        if "one hundreds" in normalized:
            slot_updates.append(SlotUpdate("amount", "100.00", 0.98, "pending_answer"))
            conversation_act = "provide_information"
            relation = "continue"
        if "checking ending in 1001" in normalized:
            slot_updates.extend(
                [
                    SlotUpdate(
                        "source_account",
                        "checking ending in 1001",
                        0.99,
                        "pending_answer",
                    ),
                    SlotUpdate("amount", "1001", 0.20, "explicit"),
                ]
            )
            conversation_act = "provide_information"
            relation = "continue"
        return TurnAnalysis(
            goals=analysis.goals,
            skill_gap=analysis.skill_gap,
            slot_updates=slot_updates,
            conversation_act=conversation_act,
            active_goal_relation=relation,
        )


class _SemanticBindingProvider(_NaturalTurnProvider):
    """Exercises generic pending-answer and correction controls."""

    def understand_turn(self, message, catalog, context=None):
        normalized = message.casefold().strip()
        if normalized == "1002" and (context or {}).get("missing_field") == "destination_account":
            return TurnAnalysis(
                slot_updates=[
                    SlotUpdate(
                        "destination_account", "1002", 0.99, "pending_answer"
                    ),
                    SlotUpdate("amount", "1002", 0.20, "explicit"),
                ],
                conversation_act="provide_information",
                active_goal_relation="continue",
            )
        if "actually use checking 1003 for source" in normalized:
            if "make it 75" in normalized:
                return TurnAnalysis(
                    slot_updates=[
                        SlotUpdate(
                            "source_account", "checking 1003", 0.99, "correction"
                        ),
                        SlotUpdate("amount", "75.00", 0.99, "explicit"),
                    ],
                    conversation_act="correction",
                    active_goal_relation="continue",
                )
            return TurnAnalysis(
                slot_updates=[
                    SlotUpdate(
                        "source_account", "checking 1003", 0.99, "correction"
                    )
                ],
                conversation_act="correction",
                active_goal_relation="continue",
            )
        return super().understand_turn(message, catalog, context)


class _SemanticInitialGoalProvider(DeterministicProvider):
    """Returns semantic goal inputs that conflict with shape-based extraction."""

    semantic_turn_understanding = True

    def understand_turn(self, message, catalog, context=None):
        if "make it $50" in message.casefold():
            return TurnAnalysis(
                goals=[
                    SkillMatch(
                        skill_name="internal_transfer",
                        confidence=0.99,
                        inputs={
                            "source_account": "savings 2003",
                            "destination_account": "checking 1002",
                            "amount": "50.00",
                        },
                    )
                ],
                conversation_act="new_goal",
            )
        return super().understand_turn(message, catalog, context)


class _NoSlotSemanticProvider(DeterministicProvider):
    """Simulates an LLM declining to bind an ambiguous-looking reply."""

    semantic_turn_understanding = True

    def understand_turn(self, message, catalog, context=None):
        if message.strip() == "1002":
            return TurnAnalysis(
                conversation_act="provide_information",
                active_goal_relation="continue",
            )
        return super().understand_turn(message, catalog, context)


class _ContextAwareSemanticProvider(DeterministicProvider):
    """Uses bounded conversation state to resolve an ordinal reference."""

    semantic_turn_understanding = True

    def __init__(self):
        super().__init__()
        self.reference_context = {}

    def understand_turn(self, message, catalog, context=None):
        if message.casefold().strip() == "the second one":
            self.reference_context = dict(context or {})
            return TurnAnalysis(
                slot_updates=[
                    SlotUpdate(
                        "destination_account", "1002", 0.99, "pending_answer"
                    )
                ],
                conversation_act="provide_information",
                active_goal_relation="continue",
            )
        return super().understand_turn(message, catalog, context)


class _QueuedHistoryRecoveryProvider(DeterministicProvider):
    """Recovers initially missed queued-goal inputs from member evidence."""

    semantic_turn_understanding = True

    def understand_turn(self, message, catalog, context=None):
        normalized = message.casefold()
        if "check checking 1001" in normalized and "then transfer" in normalized:
            return TurnAnalysis(
                goals=[
                    SkillMatch(
                        "guided_balance",
                        0.99,
                        {"account_type": "checking", "account_number": "1001"},
                    ),
                    # Simulate the model recognizing the second goal but missing
                    # its values during initial extraction.
                    SkillMatch(
                        "internal_transfer",
                        0.98,
                        {},
                    ),
                ],
                conversation_act="new_goal",
            )
        if (
            normalized.strip() == "yes"
            and (context or {}).get("active_skill") == "internal_transfer"
            and (context or {}).get("pending_task_transition")
        ):
            return TurnAnalysis(
                slot_updates=[
                    SlotUpdate(
                        "source_account",
                        "savings 2003",
                        0.99,
                        "context_recovery",
                        "savings 2003",
                    ),
                    SlotUpdate(
                        "destination_account",
                        "checking 1002",
                        0.99,
                        "context_recovery",
                        "checking 1002",
                    ),
                    SlotUpdate(
                        "amount",
                        "50.00",
                        0.99,
                        "context_recovery",
                        "$50",
                    ),
                ],
                conversation_act="confirmation",
                active_goal_relation="continue",
            )
        return super().understand_turn(message, catalog, context)


def test_grounded_faq_uses_approved_source(runtime_factory):
    runtime = runtime_factory()

    reply = runtime.chat("faq", "How does overdraft protection work?")

    assert "linked savings account" in reply.text
    assert "KB-001" in reply.text
    assert reply.outcome["grounded"] is True
    assert reply.selected_skill == "approved_knowledge"


def test_speculative_model_slot_uses_neutral_elicitation_then_validates_reply(
    runtime_factory,
):
    runtime = runtime_factory(provider=_NoisyBalanceProvider())

    prompt = runtime.chat("neutral-slot", "What about balance?")

    assert "Which account type would you like" in prompt.text
    assert "couldn't match" not in prompt.text

    invalid = runtime.chat("neutral-slot", "my mystery account")
    assert "Which account type would you like" in invalid.text
    assert "account_type" not in runtime.inspect_state("neutral-slot")[
        "active_task"
    ]["inputs"]

    completed = runtime.chat("neutral-slot", "2002")
    assert "$8,250.25" in completed.text


def test_balance_clarification_and_durable_resume_after_restart(runtime_factory):
    first_runtime = runtime_factory(db_name="durable.db")

    prompt = first_runtime.chat("balance", "What is my account balance?")
    assert "Which account type" in prompt.text
    saved = first_runtime.inspect_state("balance")
    assert saved["pending_clarification"]["field"] == "account_type"
    first_runtime.close()

    second_runtime = runtime_factory(db_name="durable.db")
    answer = second_runtime.chat("balance", "saving 2002")

    assert "$8,250.25" in answer.text
    assert second_runtime.inspect_state("balance")["active_task"] is None


def test_balance_collects_account_type_then_allows_correction(runtime_factory):
    runtime = runtime_factory()

    prompt = runtime.chat("balance-correction", "What is my balance?")
    assert "Which account type" in prompt.text

    savings = runtime.chat("balance-correction", "savings")
    assert "Savings ending in 2002" in savings.text
    assert "Savings ending in 2003" in savings.text
    assert "Which account would you like" not in savings.text

    checking_prompt = runtime.chat("balance-correction", "Actually, checking")
    assert "Which account would you like" in checking_prompt.text

    checking = runtime.chat("balance-correction", "1001")
    assert "Checking ending in 1001: $2,450.75" in checking.text
    assert "Checking ending in 1002" not in checking.text
    assert "Checking ending in 1003" not in checking.text


def test_balance_account_number_follow_up_continues_last_read_only_skill(runtime_factory):
    runtime = runtime_factory()

    runtime.chat("balance-follow-up", "What is my balance?")
    runtime.chat("balance-follow-up", "checking")
    runtime.chat("balance-follow-up", "1001")
    savings = runtime.chat("balance-follow-up", "What about 2002?")

    assert "Savings ending in 2002: $8,250.25" in savings.text


def test_balance_displays_all_accounts_when_member_has_two_or_fewer(runtime_factory):
    runtime = runtime_factory()
    runtime.tools.accounts._accounts = [
        AccountBalance("chk-001", "checking", "••••1001", Decimal("2450.75")),
        AccountBalance("sav-001", "savings", "••••2002", Decimal("8250.25")),
    ]

    reply = runtime.chat("two-balance-accounts", "What is my balance?")

    assert "Checking ending in 1001: $2,450.75" in reply.text
    assert "Savings ending in 2002: $8,250.25" in reply.text


def test_transfer_requires_immediate_confirmation(runtime_factory):
    runtime = runtime_factory()

    review = runtime.chat("transfer", "Transfer $50 from chk-001 to sav-001")

    assert "Review mock transfer" in review.text
    assert "yes or no" in review.text
    assert runtime.tools.transfers.submission_count == 0
    assert runtime.inspect_state("transfer")["confirmation_status"] == "pending"

    completed = runtime.chat("transfer", "yes")

    assert "Mock transfer completed" in completed.text
    assert "MOCK-" in completed.text
    assert runtime.tools.transfers.submission_count == 1
    audits = runtime.store.audit_events("transfer")
    assert any(event["event_type"] == "policy_approved" for event in audits)
    assert any(event["payload"].get("status") == "completed" for event in audits)


def test_account_reference_with_type_and_suffix_prefers_the_specific_account(
    runtime_factory,
):
    runtime = runtime_factory()

    account = runtime.tools.accounts.resolve("checking 1003")

    assert account is not None
    assert account.account_id == "chk-003"


def test_transfer_requires_a_specific_account_when_type_has_multiple_accounts(
    runtime_factory,
):
    runtime = runtime_factory()

    source = runtime.chat("transfer-specific-account", "Transfer $200 from checking to savings")
    assert "I found multiple checking accounts" in source.text

    destination = runtime.chat("transfer-specific-account", "checking 1003")
    assert "I found multiple savings accounts" in destination.text

    review = runtime.chat("transfer-specific-account", "savings 2003")
    assert "Review mock transfer" in review.text
    assert "Checking ending in 1003" in review.text
    assert "Savings ending in 2003" in review.text


def test_transfer_lists_eligible_accounts_for_an_ambiguous_account_type(
    runtime_factory,
):
    runtime = runtime_factory(provider=_SemanticBindingProvider())

    runtime.chat("transfer-account-choice", "I want to make a transfer")
    runtime.chat("transfer-account-choice", "savings 2003")
    choices = runtime.chat("transfer-account-choice", "checking")

    assert "I found multiple checking accounts" in choices.text
    assert "Checking ending in 1001" in choices.text
    assert "Checking ending in 1002" in choices.text
    assert "Checking ending in 1003" in choices.text

    amount = runtime.chat("transfer-account-choice", "1002")
    assert "How much would you like to transfer" in amount.text
    state = runtime.inspect_state("transfer-account-choice")
    assert state["active_task"]["inputs"]["destination_account"] == "1002"
    assert "amount" not in state["active_task"]["inputs"]

    review = runtime.chat("transfer-account-choice", "$200")
    assert "Savings ending in 2003" in review.text
    assert "Checking ending in 1002" in review.text


def test_runtime_does_not_blindly_bind_raw_text_when_semantics_return_no_slot(
    runtime_factory,
):
    runtime = runtime_factory(provider=_NoSlotSemanticProvider())

    runtime.chat("no-raw-slot", "I want to make a transfer")
    runtime.chat("no-raw-slot", "savings 2003")
    choices = runtime.chat("no-raw-slot", "checking")
    retry = runtime.chat("no-raw-slot", "1002")

    assert retry.text == choices.text
    state = runtime.inspect_state("no-raw-slot")
    assert state["active_task"]["missing_field"] == "destination_account"
    assert "destination_account" not in state["active_task"]["inputs"]
    assert "amount" not in state["active_task"]["inputs"]


def test_semantic_provider_can_resolve_slot_from_bounded_conversation_context(
    runtime_factory,
):
    provider = _ContextAwareSemanticProvider()
    runtime = runtime_factory(provider=provider)

    runtime.chat("contextual-slot", "I want to make a transfer")
    runtime.chat("contextual-slot", "savings 2003")
    choices = runtime.chat("contextual-slot", "checking")
    amount = runtime.chat("contextual-slot", "the second one")

    assert "Checking ending in 1002" in choices.text
    assert "How much would you like to transfer" in amount.text
    assert "1002" in provider.reference_context["pending_question"]
    assert provider.reference_context["missing_field"] == "destination_account"
    assert any(
        item["role"] == "assistant" and "Checking ending in 1002" in item["content"]
        for item in provider.reference_context["recent_messages"]
    )


def test_semantic_slot_correction_restarts_validation_while_collecting_input(
    runtime_factory,
):
    runtime = runtime_factory(provider=_SemanticBindingProvider())

    runtime.chat("collecting-correction", "I want to make a transfer")
    runtime.chat("collecting-correction", "checking 1001")
    amount = runtime.chat("collecting-correction", "savings 2002")
    assert "How much would you like to transfer" in amount.text

    corrected = runtime.chat(
        "collecting-correction", "actually use checking 1003 for source"
    )
    assert "How much would you like to transfer" in corrected.text
    state = runtime.inspect_state("collecting-correction")
    assert state["active_task"]["inputs"]["source_account"] == "checking 1003"

    review = runtime.chat("collecting-correction", "$50")
    assert "Checking ending in 1003" in review.text
    assert "Savings ending in 2002" in review.text


def test_semantic_correction_can_update_and_fill_multiple_slots(runtime_factory):
    runtime = runtime_factory(provider=_SemanticBindingProvider())

    runtime.chat("multi-correction", "I want to make a transfer")
    runtime.chat("multi-correction", "checking 1001")
    runtime.chat("multi-correction", "savings 2002")
    review = runtime.chat(
        "multi-correction",
        "actually use checking 1003 for source and make it 75 dollars",
    )

    assert "$75.00" in review.text
    assert "Checking ending in 1003" in review.text
    assert "Savings ending in 2002" in review.text
    assert runtime.inspect_state("multi-correction")["active_task"]["inputs"] == {
        "source_account": "checking 1003",
        "destination_account": "savings 2002",
        "amount": "75.00",
    }


def test_semantic_goal_inputs_override_shape_based_fallback_extraction(
    runtime_factory,
):
    runtime = runtime_factory(provider=_SemanticInitialGoalProvider())

    review = runtime.chat(
        "semantic-initial",
        "Transfer from savings 2003 to checking 1002; make it $50",
    )

    assert "Review mock transfer: $50.00" in review.text
    assert "Savings ending in 2003" in review.text
    assert "Checking ending in 1002" in review.text
    assert "$2003.00" not in review.text


def test_pending_transfer_confirmation_survives_restart(runtime_factory):
    first_runtime = runtime_factory(db_name="confirmation.db")
    first_runtime.chat("confirmation", "I want to make a transfer")
    first_runtime.chat("confirmation", "checking 1001")
    first_runtime.chat("confirmation", "savings 2002")
    first_runtime.chat("confirmation", "$12")
    first_runtime.close()

    second_runtime = runtime_factory(db_name="confirmation.db")
    completed = second_runtime.chat("confirmation", "yes")

    assert "Mock transfer completed" in completed.text
    assert second_runtime.tools.transfers.submission_count == 1


def test_multi_goal_orders_read_only_before_consequential(runtime_factory):
    runtime = runtime_factory()

    first = runtime.chat(
        "multi",
        "Transfer $25 from chk-002 to sav-001 and check my chk-001 balance",
    )
    assert "$2,450.75" in first.text
    assert "I'll start by helping you check an account balance" in first.text
    assert "then continue by helping you make an internal transfer" in first.text
    assert "Would you like me to continue" not in first.text
    assert "Review mock transfer" in first.text
    assert runtime.tools.transfers.submission_count == 0
    state = runtime.inspect_state("multi")
    assert state["active_task"]["skill_name"] == "internal_transfer"
    assert state["active_task"]["status"] == "awaiting_confirmation"
    assert state["queued_tasks"] == []
    assert state["pending_task_transition"] is None

    second = runtime.chat("multi", "yes")
    assert "Mock transfer completed" in second.text
    assert runtime.tools.transfers.submission_count == 1


def test_queued_task_missing_inputs_are_elicited_without_reconsent(
    runtime_factory,
):
    runtime = runtime_factory(provider=_QueuedHistoryRecoveryProvider())

    first = runtime.chat(
        "queued-history",
        "Check checking 1001, then transfer $50 from savings 2003 to checking 1002",
    )

    assert "$2,450.75" in first.text
    assert "Would you like me to continue" not in first.text
    assert "Which account should the money come from" in first.text
    active = runtime.inspect_state("queued-history")["active_task"]
    assert active["skill_name"] == "internal_transfer"
    assert active["inputs"] == {}

    runtime.chat("queued-history", "savings 2003")
    runtime.chat("queued-history", "checking 1002")
    review = runtime.chat("queued-history", "$50")

    assert "Review mock transfer: $50.00" in review.text
    assert "Savings ending in 2003" in review.text
    assert "Checking ending in 1002" in review.text
    assert "Which account should" not in review.text


def test_member_can_decline_consequential_confirmation_after_automatic_transition(
    runtime_factory,
):
    runtime = runtime_factory()
    first = runtime.chat(
        "multi-decline",
        "Check my chk-001 balance and transfer $25 from chk-002 to sav-001",
    )
    assert "$2,450.75" in first.text
    assert "Would you like me to continue" not in first.text
    assert "Review mock transfer" in first.text

    declined = runtime.chat("multi-decline", "no")

    assert "Transfer cancelled" in declined.text
    state = runtime.inspect_state("multi-decline")
    assert state["active_task"] is None
    assert state["queued_tasks"] == []
    assert state["pending_task_transition"] is None
    assert runtime.tools.transfers.submission_count == 0


def test_automatically_advanced_goal_confirmation_survives_restart(runtime_factory):
    first_runtime = runtime_factory(db_name="planned-transition.db")
    first_runtime.chat(
        "multi-durable",
        "Transfer $25 from chk-002 to sav-001 and check my chk-001 balance",
    )
    first_runtime.close()

    second_runtime = runtime_factory(db_name="planned-transition.db")
    continued = second_runtime.chat("multi-durable", "yes")

    assert "Mock transfer completed" in continued.text
    assert second_runtime.inspect_state("multi-durable")["active_task"] is None


def test_live_agent_handoff(runtime_factory):
    runtime = runtime_factory()

    offer = runtime.chat("handoff", "This is not helping—get me a person")

    assert "I understand you'd like to talk with a live agent" in offer.text
    assert "Would you like me to connect" in offer.text
    assert runtime.inspect_state("handoff")["pending_handoff_offer"] is not None
    assert runtime.inspect_state("handoff")["handoff_status"] is None

    reply = runtime.chat("handoff", "yes")

    assert "what would you like" in reply.text

    queue_question = runtime.chat(
        "handoff", "I need help with a problem in my credit card balance"
    )
    assert "insurance, banking, or financial advice" in queue_question.text

    queued = runtime.chat("handoff", "banking")
    assert "banking live-support queue" in queued.text
    assert "CASE-" in queued.text
    assert queued.outcome["status"] == "queued"
    assert queued.outcome["queue"] == "banking"
    assert "Goal:" in queued.outcome["summary"]
    assert runtime.inspect_state("handoff")["handoff_status"] == "queued"


def test_live_agent_handoff_reuses_context_provided_before_confirmation(runtime_factory):
    runtime = runtime_factory()

    offer = runtime.chat("handoff-context", "Let's talk to a live agent for my auto policy")

    assert "Would you like me to connect" in offer.text

    queued = runtime.chat("handoff-context", "yes")

    assert "insurance live-support queue" in queued.text
    assert queued.outcome["status"] == "queued"
    assert queued.outcome["queue"] == "insurance"


def test_repeated_negative_sentiment_offers_live_support(runtime_factory):
    runtime = runtime_factory()

    first = runtime.chat("sentiment-escalation", "I have a problem with something")
    assert "Would you like me to connect" not in first.text

    second = runtime.chat("sentiment-escalation", "This is still wrong and I am worried")
    assert "Would you like me to connect" in second.text
    state = runtime.inspect_state("sentiment-escalation")
    assert state["sentiment"] == "negative"
    assert state["negative_sentiment_streak"] >= 2


def test_greeting_loads_mock_member_profile_and_explains_capabilities(runtime_factory):
    runtime = runtime_factory()

    reply = runtime.chat("reception", "hello")

    assert reply.text.startswith("Hi Jordan.")
    assert "check an account balance" in reply.text
    assert "make an internal transfer" in reply.text
    assert "live agent" not in reply.text
    state = runtime.inspect_state("reception")
    assert state["member_profile"]["preferred_name"] == "Jordan"
    assert state["reception_variant"] in {0, 1, 2}
    assert state["greeted"] is True


def test_capability_responses_cycle_controlled_copy_within_a_session(runtime_factory):
    runtime = runtime_factory()

    first = runtime.chat("reception-variation", "what can you do")
    second = runtime.chat("reception-variation", "what can you do")

    assert first.text != second.text
    assert first.text.startswith("Hi Jordan.")
    assert not second.text.startswith("Hi Jordan.")


def test_capability_question_word_order_variant_uses_catalog_response(runtime_factory):
    runtime = runtime_factory()

    runtime.chat("capability-word-order", "hey")
    reply = runtime.chat("capability-word-order", "what can else you do?")

    assert "Thanks for explaining" not in reply.text
    assert "check an account balance" in reply.text
    assert "make an internal transfer" in reply.text


def test_capability_question_with_else_before_can_uses_catalog_response(runtime_factory):
    runtime = runtime_factory(provider=_CapabilityGapProvider())

    reply = runtime.chat("capability-else-before-can", "what else you can do?")

    assert "don't currently have the ability" not in reply.text
    assert "Thanks for explaining" not in reply.text
    assert "check an account balance" in reply.text
    assert not any(
        event["event_type"] == "skill_gap"
        for event in runtime.store.audit_events("capability-else-before-can")
    )


def test_capability_question_does_not_replace_an_active_transfer(runtime_factory):
    runtime = runtime_factory()

    runtime.chat("capability-during-transfer", "I want to make a transfer")
    reply = runtime.chat("capability-during-transfer", "what else can you do?")

    assert "check an account balance" in reply.text
    assert "Which account should the money come from" in reply.text
    state = runtime.inspect_state("capability-during-transfer")
    assert state["active_task"]["skill_name"] == "internal_transfer"
    assert state["active_task"]["inputs"] == {}


def test_balance_before_transfer_is_planned_as_two_requests(runtime_factory):
    runtime = runtime_factory()

    reply = runtime.chat(
        "balance-before-transfer",
        "transfer the balance but I want to know how much I have",
    )

    assert "I'll start by helping you check an account balance" in reply.text
    assert "Which account type would you like" in reply.text
    state = runtime.inspect_state("balance-before-transfer")
    assert state["queued_tasks"][0]["skill_name"] == "internal_transfer"


def test_affirmative_answer_to_two_goal_choice_requests_a_specific_choice(runtime_factory):
    runtime = runtime_factory()

    runtime.chat("clarification-yes", "balance transfer")
    reply = runtime.chat("clarification-yes", "yes please")

    assert "Please choose one first" in reply.text
    assert "check an account balance" in reply.text
    assert "make an internal transfer" in reply.text


def test_reception_only_advertises_currently_installed_skills(runtime_factory):
    runtime = runtime_factory()

    before = runtime.chat("before-install", "hello")
    assert "recover your online ID" not in before.text

    runtime.catalog.install(
        PROJECT_ROOT
        / "skills"
        / "available"
        / "online_id_recovery"
        / "SKILL.md"
    )

    after = runtime.chat("after-install", "hello")
    assert "recover your online ID" in after.text


def test_no_goal_uses_friendly_catalog_aware_reception(runtime_factory):
    runtime = runtime_factory()

    reply = runtime.chat("unavailable-online-id", "recover my online id")

    assert reply.text.startswith("Hi Jordan. Thanks for explaining.")
    assert "check an account balance" in reply.text
    assert "recover your online ID" not in reply.text


def test_clear_unsupported_objective_is_acknowledged_and_audited(runtime_factory):
    runtime = runtime_factory(provider=_GapAwareProvider())

    reply = runtime.chat("skill-gap", "recover my online id")

    assert "I understand that you'd like to recover your online ID" in reply.text
    assert "don't currently have the ability" in reply.text
    gap_events = [
        event
        for event in runtime.store.audit_events("skill-gap")
        if event["event_type"] == "skill_gap"
    ]
    assert len(gap_events) == 1
    assert gap_events[0]["payload"]["category"] == "online_id_recovery"
    assert gap_events[0]["payload"]["objective"] == "recover your online ID"
    assert gap_events[0]["payload"]["confidence"] == 0.96
    assert "member_message" not in gap_events[0]["payload"]


def test_fraud_reporting_gap_offers_handoff_immediately(runtime_factory):
    runtime = runtime_factory()

    reply = runtime.chat("fraud-gap", "I need to report fraud on my account")

    assert "report suspected fraud" in reply.text
    assert "Would you like me to connect" in reply.text
    assert runtime.inspect_state("fraud-gap")["pending_handoff_offer"] is not None
    gap_events = runtime.store.audit_events("fraud-gap")
    assert any(
        event["event_type"] == "skill_gap"
        and event["payload"]["category"] == "fraud_reporting"
        for event in gap_events
    )


def test_skill_gap_during_slot_collection_preserves_the_active_goal(runtime_factory):
    runtime = runtime_factory(provider=_GapAwareProvider())
    runtime.chat("gap-interruption", "check my balance")

    reply = runtime.chat("gap-interruption", "recover my online id")

    assert "I understand that you'd like to recover your online ID" in reply.text
    assert "Your current request is still here" in reply.text
    state = runtime.inspect_state("gap-interruption")
    assert state["active_task"]["skill_name"] == "guided_balance"
    assert state["active_task"]["status"] == "awaiting_input"


def test_installed_skill_is_not_reported_as_a_gap(runtime_factory):
    runtime = runtime_factory(provider=_GapAwareProvider())
    runtime.catalog.install(
        PROJECT_ROOT
        / "skills"
        / "available"
        / "online_id_recovery"
        / "SKILL.md"
    )

    reply = runtime.chat("gap-closed", "recover my online id")

    assert reply.selected_skill == "online_id_recovery"
    assert "approved online-ID recovery page" in reply.text
    assert not any(
        event["event_type"] == "skill_gap"
        for event in runtime.store.audit_events("gap-closed")
    )


def test_installed_skill_match_routes_without_provider_goal_identifier(
    runtime_factory,
):
    runtime = runtime_factory(provider=_UnknownSkillProvider())
    runtime.catalog.install(
        PROJECT_ROOT
        / "skills"
        / "available"
        / "online_id_recovery"
        / "SKILL.md"
    )

    reply = runtime.chat("goal-alias", "What is my online ID?")

    assert reply.selected_skill == "online_id_recovery"
    assert "approved online-ID recovery page" in reply.text
    assert runtime.inspect_state("goal-alias")["pending_goal_clarification"] is None


def test_persisted_duplicate_goal_clarification_recovers_on_yes(runtime_factory):
    runtime = runtime_factory(provider=_UnknownSkillProvider())
    runtime.catalog.install(
        PROJECT_ROOT
        / "skills"
        / "available"
        / "online_id_recovery"
        / "SKILL.md"
    )
    state = runtime.inspect_state("old-goal-alias")
    state["pending_goal_clarification"] = {
        "candidates": [
            {
                "skill_name": "online_id_recovery",
                "goal": "recover your online ID",
                "confidence": 0.86,
                "inputs": {},
            },
            {
                "skill_name": "online_id_recovery",
                "goal": "recover_online_id",
                "confidence": 0.84,
                "inputs": {},
            },
        ],
        "question": "Did you want to recover your online ID or recover your online ID?",
    }
    runtime.store.save("old-goal-alias", state)

    reply = runtime.chat("old-goal-alias", "yes")

    assert reply.selected_skill == "online_id_recovery"
    assert "approved online-ID recovery page" in reply.text
    assert runtime.inspect_state("old-goal-alias")["pending_goal_clarification"] is None


def test_repeated_no_goal_turns_offer_but_do_not_auto_start_handoff(runtime_factory):
    runtime = runtime_factory()

    for index in range(3):
        reply = runtime.chat("no-goal", "unsupported topic {}".format(index))
        assert "Would you like me to connect" not in reply.text
    offer = runtime.chat("no-goal", "still unsupported")

    assert "Would you like me to connect" in offer.text
    state = runtime.inspect_state("no-goal")
    assert state["pending_handoff_offer"] is not None
    assert state["handoff_status"] is None

    declined = runtime.chat("no-goal", "no")
    assert "won't connect" in declined.text
    assert runtime.inspect_state("no-goal")["pending_handoff_offer"] is None


def test_unsupported_turn_counter_is_not_reset_by_a_greeting(runtime_factory):
    runtime = runtime_factory()

    for index in range(3):
        runtime.chat("no-goal-greeting", "unsupported topic {}".format(index))
    runtime.chat("no-goal-greeting", "hello")
    offer = runtime.chat("no-goal-greeting", "one more unsupported topic")

    assert "Would you like me to connect" in offer.text


def test_ambiguous_goals_are_clarified_and_answer_is_durable(runtime_factory):
    first_runtime = runtime_factory(db_name="goal-clarification.db")

    question = first_runtime.chat("ambiguous", "balance transfer")

    assert "Did you want to" in question.text
    state = first_runtime.inspect_state("ambiguous")
    assert len(state["pending_goal_clarification"]["candidates"]) == 2
    first_runtime.close()

    second_runtime = runtime_factory(db_name="goal-clarification.db")
    selected = second_runtime.chat("ambiguous", "balance")
    assert "Which account" in selected.text
    assert second_runtime.inspect_state("ambiguous")["selected_skill"] == "guided_balance"


def test_ambiguous_goal_reply_can_select_both_requests_in_order(runtime_factory):
    runtime = runtime_factory()

    runtime.chat("ambiguous-both", "balance transfer")
    reply = runtime.chat("ambiguous-both", "both")

    assert "I'll start by helping you check an account balance" in reply.text
    state = runtime.inspect_state("ambiguous-both")
    assert state["active_task"]["skill_name"] == "guided_balance"
    assert state["queued_tasks"][0]["skill_name"] == "internal_transfer"


def test_ambiguous_goal_reply_can_state_an_ordered_plan(runtime_factory):
    runtime = runtime_factory()

    runtime.chat("ambiguous-ordered", "balance transfer")
    reply = runtime.chat("ambiguous-ordered", "I want to do balance then transfer")

    assert "I'll start by helping you check an account balance" in reply.text
    assert runtime.inspect_state("ambiguous-ordered")["queued_tasks"][0][
        "skill_name"
    ] == "internal_transfer"


def test_natural_slot_answers_continue_transfer_without_reclassifying(runtime_factory):
    runtime = runtime_factory()

    source = runtime.chat("natural-slots", "I want to make a transfer")
    assert "money come from" in source.text

    destination = runtime.chat("natural-slots", "checking in 1001")
    assert "receive the money" in destination.text

    amount = runtime.chat("natural-slots", "saving 2002")
    assert "How much" in amount.text

    review = runtime.chat("natural-slots", "$25 please")
    assert "Review mock transfer" in review.text
    assert "Checking ending in 1001" in review.text
    assert "Savings ending in 2002" in review.text


def test_semantic_turn_understanding_collects_multiple_slots_and_word_amount(
    runtime_factory,
):
    runtime = runtime_factory(provider=_NaturalTurnProvider())

    source = runtime.chat("semantic-slots", "I want to make a transfer")
    assert "money come from" in source.text

    accounts = runtime.chat(
        "semantic-slots", "from savings 2002 to checking 1001"
    )
    assert "How much" in accounts.text
    assert "source account and destination account" in accounts.text
    state = runtime.inspect_state("semantic-slots")
    assert state["active_task"]["inputs"]["source_account"] == "savings 2002"
    assert state["active_task"]["inputs"]["destination_account"] == "checking 1001"
    assert state["no_goal_turn_count"] == 0

    review = runtime.chat("semantic-slots", "two hundred")
    assert "$200.00" in review.text
    assert "Savings ending in 2002" in review.text
    assert "Checking ending in 1001" in review.text
    assert "live agent" not in review.text


def test_semantic_turn_understanding_normalizes_disfluent_word_amount(
    runtime_factory,
):
    runtime = runtime_factory(provider=_NaturalTurnProvider())
    runtime.chat("semantic-disfluency", "I want to make a transfer")
    runtime.chat(
        "semantic-disfluency", "from savings 2002 to checking 1001"
    )

    review = runtime.chat("semantic-disfluency", "one hundreds dollar")

    assert "$100.00" in review.text
    assert "Review mock transfer" in review.text


def test_uninterpreted_word_amount_is_reelicited_not_reported_as_over_limit(
    runtime_factory,
):
    runtime = runtime_factory()
    runtime.chat("amount-retry", "I want to make a transfer")
    runtime.chat("amount-retry", "checking 1001")
    runtime.chat("amount-retry", "saving 2002")

    retry = runtime.chat("amount-retry", "one hundreds dollar")

    assert "How much would you like to transfer" in retry.text
    assert "configured transfer limit" not in retry.text
    assert "amount" not in runtime.inspect_state("amount-retry")["active_task"]["inputs"]


def test_semantic_correction_revalidates_and_replaces_confirmation(runtime_factory):
    runtime = runtime_factory(provider=_NaturalTurnProvider())
    first_review = runtime.chat(
        "semantic-correction", "Transfer $50 from chk-001 to sav-001"
    )
    assert "$50.00" in first_review.text

    corrected_review = runtime.chat(
        "semantic-correction", "actually make it two hundred"
    )

    assert "$200.00" in corrected_review.text
    assert "I've updated the amount" in corrected_review.text
    assert "Confirm this transfer" in corrected_review.text
    state = runtime.inspect_state("semantic-correction")
    assert state["confirmation_status"] == "pending"
    assert state["active_task"]["inputs"]["amount"] == "200.00"
    assert state["outcome"] is None


def test_semantic_understanding_continues_an_inflight_deactivated_version(
    runtime_factory,
):
    runtime = runtime_factory(provider=_NaturalTurnProvider())
    runtime.chat("semantic-pinned", "I want to make a transfer")
    runtime.catalog.deactivate("internal_transfer")

    reply = runtime.chat(
        "semantic-pinned", "from savings 2002 to checking 1001"
    )

    assert "How much" in reply.text
    state = runtime.inspect_state("semantic-pinned")
    assert state["active_task"]["skill_version"] == "2.1.0"
    assert state["active_task"]["inputs"]["source_account"] == "savings 2002"
    assert state["active_task"]["inputs"]["destination_account"] == "checking 1001"


def test_low_confidence_account_suffix_is_not_accepted_as_amount(runtime_factory):
    runtime = runtime_factory(provider=_NaturalTurnProvider())
    runtime.chat("semantic-confidence", "I want to make a transfer")

    reply = runtime.chat("semantic-confidence", "checking ending in 1001")

    assert "receive the money" in reply.text
    state = runtime.inspect_state("semantic-confidence")
    assert (
        state["active_task"]["inputs"]["source_account"]
        == "checking ending in 1001"
    )
    assert "amount" not in state["active_task"]["inputs"]


def test_clear_new_goal_interrupts_slot_collection_then_offers_resume(runtime_factory):
    runtime = runtime_factory()
    runtime.chat("context-switch", "I want to make a transfer")

    balance = runtime.chat("context-switch", "What is my checking 1001 balance?")

    assert "$2,450.75" in balance.text
    assert "resume or discard" in balance.text
    assert "make an internal transfer" in balance.text
    assert "internal_transfer" not in balance.text
    state = runtime.inspect_state("context-switch")
    assert state["paused_tasks"][0]["skill_name"] == "internal_transfer"


def test_policy_denies_account_data_when_not_authenticated(runtime_factory):
    runtime = runtime_factory()
    runtime.authenticated = False

    reply = runtime.chat("signed-out", "What is my balance?")

    assert "sign in" in reply.text
    assert reply.outcome["status"] == "policy_denied"
    assert runtime.tools.transfers.submission_count == 0
