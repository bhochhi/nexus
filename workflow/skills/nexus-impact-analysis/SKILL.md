---
name: nexus-impact-analysis
description: Classify a Nexus change as capability-only, connector extension, or platform extension and identify affected specifications, contracts, code, tests, and release ordering. Use before implementation planning for every material capability or platform change.
---

# Nexus impact analysis

Announce `Workflow stage: impact_analysis`.

Read `specifications/templates/impact-analysis-template.md`, the relevant
capability specification, applicable platform features, and
`specifications/contracts/capability-runtime-contract.yaml`.

Compare the requested behavior with supported interaction, execution, lifecycle,
workflow operations, validation rules, risk controls, tools, events, and state.
Choose one primary classification:

- **capability-only:** existing primitives and dependencies are sufficient;
- **connector extension:** the execution model fits, but a new tool operation or
  integration binding is required;
- **platform extension:** a new cross-cutting behavior, primitive, lifecycle,
  policy control, or state transition is required.

Record affected artifacts, compatibility requirements, acceptance impact,
release order, risks, and rollback boundaries. A new connector requires a typed
contract and contract tests. A platform extension requires a platform feature
specification and an ADR when it makes a durable architectural choice.

Do not hide new platform behavior inside one skill. If classification remains
materially uncertain, stop before implementation planning and request the
missing architectural or business decision.
