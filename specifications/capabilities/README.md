# Capability authoring packages

Every business capability is developed as one cohesive package under
`specifications/capabilities/<capability-name>/`.

```text
<capability-name>/
  CAPABILITY.md          # human-authored source of intent and acceptance
  SKILL.md               # generated or maintained candidate runtime artifact
  contracts/             # optional capability-specific schemas
  evaluations/           # optional conversations, rubrics, and datasets
  tests/                 # optional capability-local executable acceptance tests
```

Only `CAPABILITY.md` is required when an idea is first drafted. The development
workflow creates the other artifacts when the capability needs them. Shared
contracts stay in `specifications/contracts/`; a package references rather than
copies them.

`CAPABILITY.md` is the behavioral source of truth. `SKILL.md` is its executable
implementation and must trace its acceptance cases back to stable capability
acceptance IDs. Publication copies a validated skill into the immutable catalog;
the published catalog copy is not edited in place.

Candidate skills record traceability under `metadata.capability`: capability ID,
repository specification path, and the complete acceptance-ID set. Executable
acceptance scenarios reuse those stable IDs. The compiler includes this
traceability in the candidate artifact hash.

`implementation.skill` points to the current candidate in the package.
`implementation.publishedSkill` may point to the immutable POC artifact that is
currently released; it is historical/runtime evidence, not the file to edit.

## Current capability packages

| Capability | Authoring profile | Candidate skill | Published baseline |
| --- | --- | --- | --- |
| Approved knowledge | declarative | `2.1.0` | `2.0.0` |
| Guided balance | guided | `2.2.0` | `2.1.0` |
| Internal transfer | deterministic | `2.1.0` | `2.0.0` |
| Live-agent handoff | human handoff | `3.1.0` | `3.0.0` |
| Online-ID recovery | navigation | `3.1.0` | `3.0.0` |

Candidate versions are not active merely because they exist in the source
package. They must pass verification and the separate publication/activation
workflow.

## Archetype templates

Choose the closest template from `specifications/templates/capabilities/`:

- `declarative.md` for grounded knowledge or controlled responses;
- `guided.md` for progressive collection and read-only resolution;
- `navigation.md` for approved destinations or journeys;
- `deterministic.md` for consequential ordered workflows;
- `human-handoff.md` for governed transfer of ownership to a person.

Archetypes are safe starting profiles, not separate runtime engines. A capability
may combine characteristics, but risk controls take precedence. When no profile
fits, specify the behavior first and treat any new execution primitive as a
platform feature.

## Two related lifecycles

Authoring status belongs to `CAPABILITY.md`:

```text
draft -> in_review -> approved -> retired
             |            |
             +-> draft    +-> draft (material revision)
```

Catalog status belongs to an exact version and hash of `SKILL.md`:

```text
approved source -> staged/published -> active -> deactivated
                         ^              |
                         +-- rollback --+
```

- **Draft:** editable in Git; never routable.
- **In review:** acceptance, risk, contracts, and implementation are reviewed.
- **Approved:** source is authorized to produce a release candidate.
- **Staged/published:** an immutable artifact exists but does not receive new
  work.
- **Active:** the catalog pointer routes new goals to the artifact.
- **Deactivated:** new routing stops; pinned in-flight plans may still load the
  exact artifact.
- **Retired:** the business capability is no longer developed or activated.

Publishing and activation remain separate operations. Dynamic loading watches
only the lightweight active index, so adding review states does not complicate
the runtime. Rollback moves the pointer to an already-published version/hash.
Audit events record publication, activation, rollback, and deactivation.

Git retains authoring history. The source tree keeps the current capability
package; immutable release versions belong in the local POC catalog and, at
scale, an external artifact registry with retention rules.
