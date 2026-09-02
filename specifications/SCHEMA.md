# Nexus specification schema

The specification system separates durable intent from implementation and
generated evidence. Platform artifacts use domain-neutral nouns; concrete
skill names belong only in capability packages and implementation traceability.

The specifications are normative for behavior within their stated scope. That
authority does not by itself mean the complete application can be reproduced
from specifications alone. The current baseline classification, known gaps,
required portable package, and clean-room certification gate are documented in
`docs/specification-baseline-and-rebuild-readiness.md`.

## Authority layers

1. `constitution.md` — governing principles and precedence.
2. `platform/adr/` — why durable architectural choices were made.
3. `platform/foundations/` — stable responsibilities, invariants, and interfaces.
4. `platform/features/` — observable cross-capability behavior and acceptance.
5. `contracts/` — exact machine boundaries and compatibility surfaces.
6. `capabilities/<name>/CAPABILITY.md` — business intent and acceptance.
7. candidate `SKILL.md`, code, tests, and evaluations — implementations.
8. `changes/<change-id>/` — impact, plan, verification, and release evidence.

## Common identity

Every governed Markdown artifact has YAML frontmatter containing `apiVersion`,
`kind`, and `metadata`. Metadata contains a globally stable `id`, lifecycle
`status`, accountable `owner`, and a version or decision date. References use
stable IDs for semantic traceability and repository paths for resolvability.

Acceptance criteria use globally unique IDs. Renaming headings or files must
not change IDs. Deleting an accepted criterion requires an explicit superseding
decision or versioned specification change.

## Artifact boundaries

- A foundation describes what the platform owns for every capability. It must
  not mention a concrete catalog skill, member utterance, or generated goal.
- A feature describes observable shared behavior and may use generic examples.
- A capability names one business behavior and may reference its candidate and
  published skill implementations.
- A skill is executable, immutable after publication, and is never the source
  of platform architecture.
- A contract is machine-readable and contains no prose-only requirement that
  cannot be validated by a consumer or conformance test.
- Evidence records exact inputs and outcomes but never becomes authoritative
  intent.

## Lifecycle

Specifications use `draft -> in_review -> approved -> deprecated -> retired`
where applicable. ADRs use `proposed -> accepted -> superseded`. Published
runtime artifacts are immutable; specifications evolve by version and Git
history. A change advances only when its acceptance-to-evidence mapping is
complete for its risk tier.

## Change package

Material work should create `changes/<change-id>/` containing `proposal.md`,
`impact.md`, `plan.md`, `verification.md`, and generated `evidence.json` when the
change reaches those stages. Small changes may keep these records in a pull
request when policy permits, but the same fields and gates apply.
