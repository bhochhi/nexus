---
apiVersion: nexus.platform/v1
kind: PlatformFeature
metadata:
  id: PF-CAPABILITY-AUTHORING-DELIVERY
  name: capability-authoring-and-delivery
  status: draft
  version: 0.2.0
  owner: Agentic Conversation Platform
enforces:
  - INV-CAPABILITY-PULL-001
  - INV-DELIVERY-SEPARATION-001
  - INV-PRODUCTION-APPROVAL-001
---

# Capability authoring and delivery

## Purpose

Let business and IT users collaboratively specify, generate, preview, test, and
release governed capabilities while the deployed platform discovers compatible
skills without a runtime redeployment.

## Required behavior

- The authoring experience stores business intent in Markdown-first capability
  specifications and displays generated skill and contract changes as a diff.
- An authoring agent performs mandatory platform-impact analysis before
  implementation and classifies work as capability-only, connector extension,
  or platform extension.
- Drafts can run in an isolated local preview without publication.
- A local preview consumes a worktree-private catalog assembled from a released
  baseline and explicit candidate overrides; the production runtime never scans
  the business specification tree.
- A shared test request may create a short-lived OCI preview artifact scoped to
  the authoring workspace and test environment.
- Shared-development assignments include a workspace or preview identity, and a
  runtime observes only assignments for its own identity.
- Artifact publishing occurs through a backend publication service, never from
  credentials exposed to the browser.
- Production publication or promotion references an approved change request and
  is executed by an authorized GitLab pipeline or equivalent controlled service.
- Published artifacts are immutable and identified by digest.
- Activation is a separate catalog operation from artifact publication.
- A runtime receiving a catalog change pulls, verifies, validates, and caches
  the referenced artifact before atomically routing new goals to it.
- Missed events are repaired by periodic catalog reconciliation.
- A failed artifact retains the last-known-good active capability and produces
  an operationally visible rejection.
- In-flight plans remain pinned to their original version and digest.
- Test and production assignments use fixed versions and digests. Promotion to
  production copies the tested content without rebuilding it.
- Repository topology does not determine delivery topology. Platform and
  capability source may share one repository while using independent pipelines.

## Acceptance criteria

- **AC-PF-CAP-001 — Immediate local preview:** Given a structurally valid draft,
  when an author requests local testing, then it can be chatted with without
  approval, shared publication, or production routing.
- **AC-PF-CAP-002 — Impact classification:** Given a new capability request,
  when it requires an unsupported operation, lifecycle, policy control, or state
  transition, then the workflow creates platform-extension work rather than
  embedding the behavior silently in the skill.
- **AC-PF-CAP-003 — Connector dependency:** Given a capability uses a new data
  operation, when the platform execution model is otherwise sufficient, then
  the tool contract and connector are deployed and verified before activation.
- **AC-PF-CAP-004 — Controlled test publication:** Given an author requests a
  shared test, then the exact draft digest is published only to the allowed test
  namespace and is scoped to the preview workspace or cohort.
- **AC-PF-CAP-005 — Approved production release:** Given a capability passes its
  tests, when production publication is requested, then an approved change and
  authorized pipeline are required.
- **AC-PF-CAP-006 — Event-assisted pull:** Given a catalog assignment changes,
  when a runtime receives the event or observes a newer revision, then it pulls
  and verifies the assigned digest before activation.
- **AC-PF-CAP-007 — Last-known-good:** Given a new artifact fails verification or
  compatibility validation, then the previous valid assignment remains usable
  and the failure is reported.
- **AC-PF-CAP-008 — Version continuity:** Given an active plan uses one artifact
  digest, when a newer capability activates, then that plan continues with its
  original digest while new goals may use the new assignment.
- **AC-PF-CAP-009 — Worktree-isolated local catalog:** Given two developers or
  agents preview candidates from different worktrees, when either candidate is
  changed or activated, then only the runtime using that worktree's private
  catalog observes the change.
- **AC-PF-CAP-010 — Scoped shared-development assignment:** Given two shared-dev
  runtimes use different preview identities, when a snapshot is assigned to one
  identity, then the other runtime neither routes to nor downloads that
  snapshot through its catalog assignment.
- **AC-PF-CAP-011 — Exact-content promotion:** Given a capability digest passed
  the test gates, when it is promoted to production, then production receives
  the same content digest and no build step recreates the capability package.
- **AC-PF-CAP-012 — Catalog projection:** Given the production catalog uses a
  database-backed control plane, when a runtime requests its active catalog,
  then it receives a coherent environment-scoped revision equivalent to the
  local `active.yaml` contract without treating that file as production source.

## Examples

### Business-authored draft

A product owner describes an address-change capability in chat. The authoring
agent produces a readable capability specification, identifies authentication
and confirmation requirements, and creates a local preview using mock profile
data. No artifact is published merely to run the local conversation.

### Shared test

The owner selects “Test with QA.” The publication service packages the exact
draft hash, publishes it to a non-production OCI namespace, assigns it only to
the QA preview workspace, and returns the evaluation and conversation results.

### Required platform extension

A proposed capability needs a long-running callback after the member leaves the
conversation. Impact analysis finds that only synchronous lifecycle behavior is
supported. The workflow creates a platform lifecycle feature and blocks skill
activation until that platform version is deployed.

## Edge cases

- The Artifactory push succeeds but catalog registration fails.
- Catalog registration succeeds but an activation event is missed.
- One runtime instance rejects a dependency that other instances support.
- A mutable OCI tag points at a different digest after testing.
- An author edits a draft while a preview conversation is active.
- Two worktrees use the same capability version but contain different draft
  hashes.
- A shared-dev activation event is delivered to a runtime in another preview
  workspace.
- A production request references an expired or unapproved change.
- The platform deploy rolls back while a capability requires its newer runtime
  contract.
- The browser session expires during publication.

## Verification

- Contract tests for publication-service backends and catalog adapters.
- Artifact digest, signature, compatibility, and dependency failure tests.
- Local and shared-preview isolation tests.
- Worktree overlay, preview-scope filtering, and temporary-catalog cleanup
  tests.
- Event-loss and periodic-reconciliation tests.
- Cross-repository content-copy tests proving test and production use the same
  OCI digest when separate registries are configured.
- Mixed-version, in-flight pinning, and rollback tests.
- Authorization tests proving browser identities cannot publish directly to a
  production repository or activate a production assignment.
- End-to-end GitLab approval-to-publication evidence for production releases.
