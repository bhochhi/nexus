---
apiVersion: nexus.platform/v1
kind: ArchitectureDecision
metadata:
  id: ADR-0002
  title: Separate platform deployment from capability distribution
  status: proposed
  owners: [Agentic Conversation Platform, Platform Engineering]
  decisionDate: 2026-08-30
  supersedes: []
enforcement:
  invariants:
    - id: INV-CAPABILITY-PULL-001
      statement: Runtimes pull and verify immutable capability artifacts by digest before activation.
    - id: INV-DELIVERY-SEPARATION-001
      statement: Capability activation does not require rebuilding or redeploying the platform runtime.
    - id: INV-PRODUCTION-APPROVAL-001
      statement: A browser authoring client cannot bypass production change approval.
  features: [PF-CAPABILITY-AUTHORING-DELIVERY]
  tests: []
---

# Separate platform deployment from capability distribution

## Context

The platform runtime has its own GitLab CI/CD lifecycle. Business capabilities
must evolve and become discoverable more frequently without rebuilding the
stable orchestrator. Business and IT users also need an approachable way to
author, preview, test, and release capabilities.

The local POC represents active catalog assignments in `active.yaml`. That file
is useful for local discovery, but it is not an appropriate production control
plane or artifact registry.

Repository topology is independent of this delivery boundary. Platform and
capability source can remain in one Git repository while their CI/CD pipelines
produce and promote different deployable artifacts.

## Decision

Deploy platform code through the platform CI/CD pipeline and distribute
capability releases independently as immutable OCI artifacts.

- Use a capability publication service as the only writer to artifact and
  catalog backends.
- Target JFrog Artifactory OCI repositories for immutable capability bundles,
  subject to enterprise platform and security approval.
- Keep environment assignments, activation revision, dependency metadata, and
  rollout status in a capability catalog control plane.
- Notify runtimes of catalog changes, then require runtimes to pull artifacts
  by digest, verify them, compile them, and atomically activate them.
- Periodically reconcile catalog state so event delivery is an optimization,
  not the only recovery mechanism.
- Keep draft preview isolated. Production publication or promotion must be tied
  to an approved GitLab change and controlled service identity.
- Keep platform and capability sources in one repository initially. Reconsider
  a separate capability repository only when ownership, access control, scale,
  or release throughput justifies it.
- Compose local development through an explicit, worktree-private catalog or
  capability-workspace path. Never make a production runtime scan authoring
  directories.
- Scope shared-development assignments by a workspace or preview identifier so
  one branch cannot change routing for another branch's runtime.
- Promote the exact tested OCI content into production without rebuilding it.

The exact catalog database and event transport remain replaceable behind
platform interfaces. `active.yaml` remains the local implementation and may be
materialized as a non-authoritative cache.

If DynamoDB is selected for the catalog, it stores environment-scoped
assignments, content digests, compatibility requirements, and catalog revisions
as records. It does not store `active.yaml` as the authoritative production
artifact. A change stream may provide low-latency notification, while periodic
reconciliation remains the recovery path.

## Alternatives considered

- **Package every skill in the platform image.** Rejected because every
  capability change would require platform deployment and dynamic discovery
  would be lost.
- **Push skill content directly to running instances.** Rejected because it
  weakens verification, caching, reconciliation, and last-known-good recovery.
- **Let the browser publish directly to Artifactory.** Rejected because browser
  credentials cannot safely enforce repository scope and production approval.
- **Use Git alone as the runtime registry.** Rejected because Git review is
  useful for source governance but is not an artifact distribution or fleet
  activation control plane.
- **Require separate Git repositories immediately.** Rejected for the initial
  implementation because repository separation adds cross-repository workflow
  before ownership or scale requires it. Independent build and publication
  pipelines provide the needed delivery separation inside one repository.
- **Use symlinks as the platform/capability integration contract.** Rejected
  because symlinks create machine-specific hidden state and are unreliable
  across containers and CI. Explicit workspace paths and bind mounts remain
  available as local composition mechanisms.

## Consequences

- Platform and capability releases can proceed independently when compatibility
  requirements are already satisfied.
- A publication service, catalog API, runtime catalog client, artifact cache,
  and activation health reporting become platform responsibilities.
- Capability manifests must declare runtime, tool, contract, and connector
  dependencies.
- Connector or platform extensions must deploy before dependent capabilities.
- Production availability depends on catalog reconciliation and the cached
  last-known-good artifact set, not on every event being delivered.
- Local preview requires a private catalog per worktree or preview session.
- A future repository split requires a versioned platform capability contract,
  not a circular source dependency between the repositories.

## Enforcement

- `INV-CAPABILITY-PULL-001` requires digest and signature verification before a
  downloaded artifact enters the active runtime cache.
- `INV-DELIVERY-SEPARATION-001` is enforced by keeping activation in the catalog
  control plane rather than the platform deployment manifest.
- `INV-PRODUCTION-APPROVAL-001` is enforced by routing production release
  requests through GitLab CI/CD and backend workload identity.
- `PF-CAPABILITY-AUTHORING-DELIVERY` defines the observable authoring, preview,
  publication, discovery, and failure behavior.
- `docs/capability-development-and-release-environments.md` defines the current
  local composition workflow and the intended environment model.

## Supersession

This ADR is proposed until the enterprise JFrog, GitLab, identity, and change
management integrations are validated. Clarifications use Git edits. A new ADR
is required if the chosen delivery boundary or pull model changes.
