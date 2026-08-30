---
name: nexus-implementation-planning
description: Produce an ordered, verifiable Nexus implementation plan from validated specifications and impact analysis. Use before changing platform code, connectors, contracts, candidate skills, or tests for material work.
---

# Nexus implementation planning

Announce `Workflow stage: implementation_planning`.

Plan from validated source specifications and the recorded impact classification.
Order dependencies so platform and connector support exists before a dependent
skill can be activated.

The plan identifies:

- source specifications and acceptance IDs being implemented;
- files and interfaces expected to change;
- platform, connector, candidate-skill, and migration steps;
- deterministic tests for safety and contract behavior;
- evaluations for semantic or conversational quality;
- backward-compatibility and durable-state concerns;
- release evidence and independent-verification requirements;
- explicit non-goals and rollback boundaries.

Prefer the smallest vertical increment that demonstrates behavior end to end.
Do not plan publication of an artifact whose declared runtime or connector
dependencies are unavailable.
