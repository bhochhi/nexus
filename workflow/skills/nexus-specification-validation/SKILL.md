---
name: nexus-specification-validation
description: Validate Nexus constitutions, ADRs, platform features, capability packages, candidate skills, contracts, and traceability before impact analysis or publication. Use after specification edits and when diagnosing specification drift.
---

# Nexus specification validation

Announce `Workflow stage: specification_validation`.

Run `member-assistant-specs validate` or the module equivalent. For capability
work, also compile the candidate `SKILL.md` against installed tool contracts.

Verify more than syntax:

- required Markdown sections contain concrete behavior rather than placeholders;
- acceptance IDs are stable, unique, and traced by the candidate skill;
- examples and edge cases exercise the stated scope;
- risk, authentication, authorization, confirmation, and failure behavior agree;
- referenced ADRs, features, contracts, skills, and published artifacts exist;
- candidate versions do not overwrite a different immutable release;
- the platform capability-surface contract matches runtime primitives.

Report validation failures against the source artifact that must change. Do not
weaken a contract or delete an acceptance criterion merely to make validation
pass.
