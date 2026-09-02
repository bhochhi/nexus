# Development-agent workflow guide

Nexus uses one repository-owned development workflow across Codex, GitHub
Copilot, Claude Code, and other capable development agents. Agent-specific files
are discovery adapters only; they do not redefine requirements, stages, or
quality gates.

## Shared entry point

At the start of platform, contract, connector, capability, test, or release
work, every agent should:

1. read `specifications/constitution.md`;
2. read `workflow/skills/nexus-spec-driven-development/SKILL.md`;
3. inspect the relevant approved ADRs, foundations, features, contracts, and
   capability package;
4. infer and announce `Workflow stage: <stage>`;
5. use the narrow stage skill named by the router;
6. update the highest-authority affected artifact before or with its
   implementation;
7. validate acceptance traceability and produce proportionate evidence.

Natural-language requests are the primary interface. A person does not need to
remember a slash command or vendor-specific prompt.

## Lifecycle stages

| Stage | Use it when | Primary output |
| --- | --- | --- |
| `specification_analysis` | intent, scope, ownership, risk, or governing artifact is incomplete | clarified or new authoritative specification |
| `specification_validation` | specifications changed or drift is suspected | structural and semantic validation result |
| `impact_analysis` | a material platform or capability change is understood | capability-only, connector-extension, or platform-extension classification |
| `implementation_planning` | validated intent and impact exist | acceptance-mapped implementation plan |
| `implementation` | the approved plan is ready to build | implementation, tests, and synchronized specifications |
| `independent_verification` | implementation is ready for review | reproduced checks and findings from a verifier other than the author |
| `release_evidence` | verification passed | hashes, tests, evaluations, compatibility, and approval evidence |
| `promotion` | an authorized release is requested | controlled publication or activation of exact tested artifacts |

An agent may start at the smallest applicable stage. It must return to an
earlier stage when implementation reveals ambiguous or incorrect intent.

## Codex

Codex discovers the workflow through `AGENTS.md`. Open the repository or the
assigned worktree, describe the desired outcome normally, and include
constraints such as `specification work only` or `do not change runtime code`
when they matter.

Example:

```text
Review the session-expiration behavior against the platform specifications.
Start at the appropriate workflow stage. Update specifications and acceptance
criteria only; do not implement runtime changes.
```

For parallel local validation, use a dedicated Git worktree, virtual
environment, database, and ports. Do not switch or remove a worktree while an
agent or development server is using it.

## GitHub Copilot

The repository adapter is `.github/copilot-instructions.md`. In a Copilot chat
or coding task, explicitly reference the portable entry point if the client has
not loaded repository instructions:

```text
Follow workflow/skills/nexus-spec-driven-development/SKILL.md and
specifications/constitution.md. Announce the active workflow stage before
changing files. Treat the portable specifications as authoritative.
```

Ask Copilot to show the acceptance-to-test mapping in its plan and review the
diff for changes outside the declared impact set before accepting edits.

## Claude Code

Claude Code discovers the workflow through `CLAUDE.md`. A normal task prompt is
enough when repository instructions are active. Otherwise use the same explicit
portable-entrypoint prompt shown above. Claude-specific commands may improve
ergonomics, but no command file may override the constitution or stage skills.

## Other development agents

An additional agent needs only a thin repository adapter that points to:

- `specifications/constitution.md`;
- `workflow/skills/nexus-spec-driven-development/SKILL.md`;
- this guide.

Do not copy the eight stage skills into vendor-specific folders. Duplication
creates conflicting workflows and makes evidence dependent on the agent used.

## Deterministic helper commands

When the supporting package is installed:

```bash
member-assistant-specs select-stage --task "describe the requested change"
member-assistant-specs validate
python -m pytest -q
```

`select-stage` is a convenience for CI and explicit human checks; it does not
replace contextual judgment. `validate` checks the portable artifact surface.
The relevant deterministic tests and evaluations remain required.

## Cross-agent handoff

When one agent hands work to another, provide:

- active workflow stage and completed stages;
- source specification IDs and acceptance IDs;
- impact classification and affected artifacts;
- implementation or verification evidence already produced;
- unresolved decisions, known failures, and explicit non-goals;
- exact branch, worktree, source commit, and dirty-file status.

The receiving agent starts from the specifications and repository state, not
from the previous agent's confidence or prose summary.

## Guardrails

- Do not edit immutable published catalog artifacts in place.
- Do not hide a platform primitive inside one capability.
- Do not treat generated evidence or agent instructions as higher authority
  than approved specifications.
- Do not let the author be the sole verifier of a consequential change.
- Do not merge across a dirty worktree until ownership and overlap are resolved.
- Do not claim a specification-only rebuild guarantee until the baseline passes
  the clean-room certification described in
  `docs/specification-baseline-and-rebuild-readiness.md`.
