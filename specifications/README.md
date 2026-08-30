# Portable platform specifications

This directory is the agent-agnostic source of truth for shared platform
behavior. It deliberately does not replace business-owned versioned
`skills/**/SKILL.md` artifacts.

## Terms

The member expresses an **objective**. The platform decomposes it into one or
more **goals**. A goal selects a **skill**; that skill supplies an execution
**plan** made of ordered **steps**. “Job” is not used here: it adds a second
business noun without identifying a distinct durable runtime entity in the POC.
If the platform later introduces independently scheduled, owned, and
audited background work, that entity can be specified separately.

## Layout

- `platform/adr/` records durable architectural decisions.
- `platform/features/` holds human-readable, executable shared conversational
  behavior in Markdown.
- `capabilities/` holds cohesive business capability authoring packages.
- `contracts/` holds machine-readable tool and event contracts.
- `workflow/` at the repository root defines the engineering lifecycle and
  contains provider adapters only; it is not a business or runtime contract.

Validate the portable artifacts with:

```bash
member-assistant-specs validate
```

Markdown carries purpose, scenarios, acceptance criteria, examples, and edge
cases. YAML is reserved for small frontmatter and exact machine contracts.

The command is deterministic and emits JSON suitable for CI. `select-stage`
uses task text to choose and announce one lifecycle stage; explicit stage input
is available for CI and humans. `evidence` emits stable file hashes for release
evidence without creating generated source-of-truth files.

The operating model is documented in `docs/spec-driven-development.md`. Every
capability change uses `templates/impact-analysis-template.md` to decide whether
it is capability-only, needs a connector extension, or depends on a platform
extension.
