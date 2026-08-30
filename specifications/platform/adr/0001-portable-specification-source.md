# ADR 0001: Portable specifications are the engineering source of truth

- Status: accepted
- Date: 2026-08-30

## Decision

Use repository-owned, portable specifications for platform behavior, tool and
event contracts, and the development lifecycle. Codex, GitHub Copilot, and
Claude Code consume thin instructions that point to this material; none owns a
parallel workflow or behavioral specification.

Business capabilities continue to use immutable, versioned `SKILL.md`
artifacts and their existing publication controls. The member-assistant runtime
continues to select a skill and execute its governed plan; this workflow does
not alter that path.

## Consequences

Every consequential change requires independent verification and recorded
release evidence before promotion. An author may prepare a specification,
implementation, or evidence, but may not approve their own consequential
change. Vendor adapters contain only navigation and stage-announcement guidance.
