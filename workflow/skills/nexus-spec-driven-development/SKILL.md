---
name: nexus-spec-driven-development
description: Route Nexus platform, contract, connector, and business-capability changes through the repository's portable spec-driven workflow. Use for feature work, capability authoring, architectural changes, implementation, verification, and release preparation in this repository.
---

# Nexus spec-driven development

Read `specifications/constitution.md` and
`workflow/spec-driven-development.yaml` before changing source artifacts or
code. Treat vendor instruction files as adapters, not authority.

Infer the active stage from the request and repository state. Announce
`Workflow stage: <stage>` before substantive work. Do not require a slash command
for normal use.

Use the narrow stage skill that matches the current work:

- specification analysis: `../nexus-specification-analysis/SKILL.md`
- specification validation: `../nexus-specification-validation/SKILL.md`
- impact analysis: `../nexus-impact-analysis/SKILL.md`
- implementation planning: `../nexus-implementation-planning/SKILL.md`
- implementation: `../nexus-implementation/SKILL.md`
- independent verification: `../nexus-independent-verification/SKILL.md`
- release evidence: `../nexus-release-evidence/SKILL.md`
- promotion: `../nexus-promotion/SKILL.md`

Read only the stage skill and specifications relevant to the change. Advance to
the next stage when its inputs exist; return to an earlier stage if implementation
reveals missing or incorrect intent.

Preserve these boundaries:

- business intent belongs in `CAPABILITY.md`;
- shared behavior belongs in platform feature specifications;
- architectural reasons belong in ADRs;
- exact interfaces belong in contracts;
- `SKILL.md` is an executable capability implementation;
- immutable published catalog artifacts are not edited in place;
- a consequential change cannot be self-approved.
