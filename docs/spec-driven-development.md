# Spec-driven development for Nexus

This document describes how people and development agents evolve the Nexus
platform and its business capabilities. Portable specifications are the source
of intent; code and runtime skill artifacts implement that intent.

## Authority and artifact model

```text
platform constitution
        |
architectural decisions
        |
platform feature specifications -------- machine contracts
        |                                      |
business capability specifications ------------+
        |
impact analysis and implementation plan
        |
platform code, candidate SKILL.md, tests, and evaluations
        |
independent verification and release evidence
```

- ADRs explain why a durable architectural choice was made.
- Platform feature specifications define shared observable behavior.
- `CAPABILITY.md` defines the business purpose, scenarios, behavior, acceptance
  criteria, examples, edge cases, risk, and integrations for one capability.
- Tool, event, state, and runtime contracts define exact machine boundaries.
- A candidate `SKILL.md` is an executable implementation of a capability, not
  the source of business intent.

Git retains the current authoring sources and their history. Immutable runtime
skill versions are publication artifacts.

## Development workflow

Every change enters the smallest applicable stage. An agent announces the
active stage and advances through later stages only when the required inputs
and evidence exist.

1. **Specification analysis:** identify the member or platform outcome,
   ambiguity, applicable constitution principles, ADRs, platform features, and
   capability specifications.
2. **Specification validation:** verify required sections, stable acceptance
   IDs, examples, edge cases, ownership, risk, and references.
3. **Impact analysis:** classify the change and identify affected platform
   features, contracts, connectors, capabilities, code, tests, and releases.
4. **Implementation planning:** define ordered implementation steps and map
   every acceptance criterion to deterministic tests or evaluations.
5. **Implementation:** change the specifications and their implementations
   together. Preserve unrelated runtime and business behavior.
6. **Independent verification:** a verifier other than the author validates
   consequential changes and the acceptance-to-evidence mapping.
7. **Release evidence:** produce reproducible hashes, test/evaluation results,
   compatibility results, provenance, and approvals.
8. **Promotion:** publish and activate only artifacts whose required gates pass.

Explicit commands may provide repeatable CI entry points, but people should be
able to describe a change naturally without knowing agent-specific commands.
The portable agent entrypoint is
`workflow/skills/nexus-spec-driven-development/SKILL.md`; its eight stage skills
contain the detailed operating instructions. `AGENTS.md`,
`.github/copilot-instructions.md`, and `CLAUDE.md` are thin discovery adapters.

## Mandatory platform-impact decision

The capability-building workflow must not assume every request can be solved by
authoring a new skill. During impact analysis it compares the proposed behavior
with the platform capability surface:

- supported interaction, execution, and lifecycle modes;
- allowlisted workflow operations and validation rules;
- available tool and event contracts;
- authentication, authorization, confirmation, and policy controls;
- state, interruption, version-pinning, and response behavior;
- supported connector protocols and runtime API versions.

It then records exactly one primary classification:

| Classification | Meaning | Required path |
| --- | --- | --- |
| Capability-only | Existing operations, contracts, tools, and controls are sufficient. | Build and verify the capability package without platform code changes. |
| Connector extension | The behavior fits the platform, but a new data operation or binding is required. | Specify the tool contract, generate or implement the connector, deploy that dependency, then publish the skill. |
| Platform extension | A new cross-cutting behavior, workflow primitive, lifecycle, policy control, or state transition is required. | Specify the platform feature and usually an ADR, deploy the platform change, then publish the dependent skill. |

The impact result uses
`specifications/templates/impact-analysis-template.md`. If the classification is
uncertain, implementation pauses for architecture clarification. A development
agent may propose platform changes; it may not silently invent a platform
primitive inside one skill.

## Capability authoring experience

The long-term authoring product is a browser application for business and IT:

1. A user describes a capability conversationally.
2. An authoring agent asks about purpose, scenarios, risk, data, behavior,
   acceptance criteria, examples, and failures.
3. The UI renders the evolving `CAPABILITY.md` in business-readable form.
4. The agent performs platform-impact analysis.
5. It proposes a candidate `SKILL.md`, contracts, connector bindings, tests, and
   evaluations.
6. The user starts an isolated preview against a deployed development or test
   runtime and approved sandbox integrations.
7. The UI shows conversations, tool calls, state changes, acceptance results,
   and the difference from the currently active capability.
8. Draft iteration remains immediate. Shared test and production releases use
   the appropriate review and approval controls.

The browser, CLI, GitLab pipeline, and coding-agent adapters must call the same
authoring, validation, preview, and publication APIs. The UI is not a second
source of truth.

## Draft preview and shared test

Local draft preview does not require publication. It compiles the capability
package into an isolated, temporary catalog and hot-loads valid draft hashes.

A shared test environment may publish a preview OCI artifact on every requested
test. These preview artifacts:

- use a non-production repository or namespace;
- are identified by content digest and draft/build identifier;
- have short retention;
- are visible only to the requesting preview workspace or test cohort;
- cannot be promoted by changing a mutable tag;
- use sandbox credentials and integrations;
- never become production-active without an approved change request.

## Capability publication and runtime discovery

Nexus separates platform deployment from capability distribution.

```text
authoring UI or GitLab pipeline
        |
validate, test, evaluate, package
        |
push immutable OCI capability artifact to JFrog Artifactory
        |
record artifact digest and environment assignment in capability catalog
        |
emit catalog revision / activation event
        |
runtime pulls, verifies, compiles, caches, and atomically activates
```

JFrog documents OCI repositories and ORAS push/pull for arbitrary OCI artifacts:
<https://docs.jfrog.com/artifactory/docs/oci-repositories>. The authoring service
should use a backend workload identity or short-lived, repository-scoped token;
browser clients must never receive Artifactory publishing credentials.

An initial repository topology can be:

```text
nexus-capability-preview-local   short-lived development and QA artifacts
nexus-capability-release-local   approved immutable release artifacts
nexus-capability-virtual         read access for authorized runtimes
```

If test and production use separate JFrog instances, the release pipeline copies
or promotes the already-tested digest; it does not rebuild the capability. The
catalog activates only that verified digest. JFrog's OCI/ORAS interface is the
publication API boundary, while GitLab CI or the publication-service backend
holds the credentials and records build provenance.

For development and test, the UI may call the publication service directly.
Production release should create or reference an approved GitLab change and let
the controlled pipeline publish or promote the exact tested digest. The UI may
display and initiate that workflow, but it must not bypass CI/CD approval.

The runtime does not accept pushed executable content. An event tells it that
catalog state changed; the runtime pulls the named digest, verifies signature
and compatibility, validates required tools and contracts, and retains its
last-known-good catalog if any check fails. Periodic reconciliation detects
missed events. In-flight plans remain pinned to their original version/digest.

The POC's `skills/catalog/active.yaml` is the local representation of the
catalog assignment and revision. In production, the authoritative assignment
belongs to a catalog control plane; a generated local snapshot is only a cache.

## Platform and capability release ordering

A capability manifest declares its required runtime API, operations, tool
contracts, and connector versions. Activation is blocked until the target
environment reports those dependencies.

```text
capability-only:
  publish capability -> activate capability

connector extension:
  deploy connector -> verify contract -> publish capability -> activate

platform extension:
  approve platform spec/ADR -> deploy platform -> verify capability surface
  -> publish capability -> activate
```

This dependency ordering lets the stable runtime discover capabilities
dynamically without allowing a skill to smuggle unsupported architecture into
the platform.

## Near-term implementation sequence

1. Keep the initial platform capability surface synchronized with runtime code
   and expand tool/event contract detail.
2. Require a persisted impact-analysis result for each capability change.
3. Build local draft preview and hot reload.
4. Exercise the complete workflow with internal transfer.
5. Add a publication-service interface with a local filesystem backend.
6. Add JFrog OCI and catalog-control-plane adapters behind that interface.
7. Add the browser authoring and test experience over the same APIs.
