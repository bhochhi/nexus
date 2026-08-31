# Capability development and release environments

This guide separates four concerns that are easy to conflate:

1. where capability source is authored;
2. where an immutable capability package is stored;
3. which package an environment is assigned; and
4. how a runtime obtains and activates that assignment.

They do not need to use the same repository or lifecycle.

## Decisions at a glance

- Keep platform and capability source in this repository for the initial
  implementation. Independent capability delivery does not require separate Git
  repositories.
- Treat `specifications/capabilities/<name>/CAPABILITY.md` as business intent and
  the adjacent `SKILL.md` as its editable candidate runtime implementation.
- Never make a production runtime scan `specifications/capabilities/`.
- Use an isolated file catalog for local development. It contains the normal
  baseline plus candidate overrides from one worktree.
- Use immutable OCI capability packages in JFrog Artifactory for shared dev,
  test, and production environments.
- Keep environment and workspace assignments in a catalog control plane. The
  artifact registry stores bytes; the catalog says which digest is active.
- Pin every assignment and in-flight plan to a digest. Tags and semantic
  versions are useful names, but they are not the integrity boundary.
- Promote the exact tested content into production; do not rebuild it.

## The Java dependency analogy

A published capability package is similar to a Maven JAR in several useful
ways: source is built and validated, an immutable version is published to an
artifact repository, and a consumer resolves a specific version.

There is one important difference. A typical JAR is resolved while building or
starting an application. A Nexus capability is a governed runtime extension.
The platform can discover and activate a compatible capability after the
platform was deployed. Consequently, JFrog is not also the activation system.
The catalog control plane selects the exact version and digest that a runtime is
allowed to use.

```text
Git or authoring database       JFrog OCI registry       catalog control plane
-------------------------       ------------------       ---------------------
CAPABILITY.md             -->   immutable package   <--  environment assignment
candidate SKILL.md              version + digest         revision + rollout state
contracts/tests/evals                                      |
                                                           v
                                                   runtime verified cache
```

## Local development in the current repository

### What works today

The current publisher can write to any catalog directory, and the server can
start against any catalog directory. The server does not currently scan the
capability specification directory directly.

Each developer should create a private, temporary catalog, copy the checked-in
POC baseline into it, publish only the candidate versions needed for the task,
and point that developer's server at the private catalog:

```bash
NEXUS_DEV_CATALOG="$(mktemp -d /tmp/nexus-dev-catalog.XXXXXX)"
cp -R skills/catalog/. "$NEXUS_DEV_CATALOG/"

member-assistant-skills \
  --catalog "$NEXUS_DEV_CATALOG" \
  publish specifications/capabilities/internal-transfer/SKILL.md

MODEL_PROVIDER=mock member-assistant-server \
  --catalog "$NEXUS_DEV_CATALOG" \
  --db data/local-internal-transfer.db
```

This local publication is neither shared nor a production release. It copies
the exact candidate into an ephemeral versioned catalog and activates it only
for the server process using that directory. A second worktree uses a different
directory and cannot observe the first worktree's changes.

Do not point multiple developers at the checked-in `skills/catalog/` directory
and mutate it while testing. That creates shared branch state and makes test
results depend on whoever published last.

### Target local-preview experience

The next local improvement should automate the preceding steps behind one
development command or UI action:

1. read an approved baseline catalog or a selected released catalog revision;
2. discover candidate `SKILL.md` files below one explicitly configured
   capability workspace;
3. validate and compile them into a worktree-private temporary catalog;
4. overlay matching candidates on the baseline;
5. watch only that workspace for changes; and
6. retain the last-known-good local candidate when an edit is invalid.

The runtime should still consume the catalog interface. The development adapter
builds the ephemeral catalog; it does not teach the production runtime to read
business specifications. This keeps local behavior close to production while
remaining fast.

A symlink can make one repository appear inside another, much like `npm link`,
but it is not the preferred contract. Symlinks create machine-specific hidden
state and behave inconsistently in containers and CI. An explicit capability
workspace path or bind mount is easier to inspect, reproduce, and isolate.

## Repository strategy

### Near term: one repository

Keep the following together until ownership or scale makes the split valuable:

```text
nexus/
  specifications/capabilities/   business specs and candidate packages
  specifications/platform/       platform features and ADRs
  src/                            runtime and publication implementation
  skills/catalog/                 local POC catalog only
```

Platform CI can ignore capability-only changes for platform deployment while
capability CI validates and publishes capability packages independently. One
Git repository does not imply one deployable unit.

### Possible later split

If capabilities move to their own repository, use sibling checkouts rather than
copying or symlinking one repository into the other:

```text
workspace/
  nexus-platform/
  nexus-capabilities/
```

The platform accepts an explicit capability-workspace path for local preview.
Neither repository has to pull the other's source during ordinary work:

- The platform publishes a versioned capability-authoring kit containing the
  supported runtime contract, schemas, validator, compiler, and test harness.
- The capability repository declares which kit/runtime API version it targets
  and validates against that released contract.
- Platform CI tests the runtime against representative released capability
  packages and may check out the capability repository only for an intentional
  cross-repository compatibility job.
- Capability CI tests candidates against a released platform contract and uses
  a deployed development runtime for end-to-end preview.

A change that needs both repositories uses a two-phase release. First deploy a
backward-compatible platform or connector extension. Then publish the dependent
capability. Remove old platform behavior only after no active capability or
in-flight plan depends on it. This avoids a circular source dependency.

## Authoring UI and portable source

The future authoring UI may persist drafts in a database, but the canonical
content of a revision remains a portable capability package: Markdown
specification, candidate `SKILL.md`, contracts, and relevant evaluation data.
The database can index fields, ownership, discussions, and workflow state; it
must also be able to export the exact portable revision used to build a release.

The authoring service, not the browser, performs publication:

1. save a content-addressed draft revision;
2. run specification validation and platform-impact analysis;
3. generate or update the candidate skill, contracts, tests, and evaluations;
4. run an isolated preview;
5. build an OCI package from the exact reviewed revision;
6. push through a scoped service identity;
7. record the returned registry digest and evidence; and
8. request an environment assignment through the catalog control plane.

## Environment and version model

Authoring status, artifact state, and environment assignment are separate. A
capability does not become production-active merely because a file or artifact
has an `approved` label.

| Concern | Example states |
| --- | --- |
| Authoring | `draft`, `in_review`, `approved`, `retired` |
| Artifact | `snapshot`, `release`, `withdrawn` |
| Assignment | not assigned, staged, active, rolled back |

Recommended environment behavior:

| Environment | Allowed artifact | Assignment scope | Isolation |
| --- | --- | --- | --- |
| Local | Workspace candidate | One process/worktree | Private temporary catalog |
| Shared dev | Snapshot digest | Branch, workspace, or preview ID | TTL and owner/cohort restriction |
| Test | Fixed release-candidate version and digest | Test environment | Stable until explicitly changed |
| Production | Approved release version and digest | Production environment or rollout cohort | Change approval and controlled promotion |

Snapshot names such as `2.1.0-dev.<build-id>` are helpful for people, but a dev
assignment still records the immutable digest. A branch-scoped assignment key
might be `(environment=dev, workspace=<preview-id>, capability=<name>)`. A dev
runtime supplies its preview ID and therefore cannot observe another branch's
assignment.

Test should exercise the release content intended for production. When test and
production use different JFrog repositories or instances, promotion copies the
same OCI content and verifies its digest and evidence; it does not rebuild the
package from source. The repository URL may change while the content identity
remains fixed.

## Production catalog and hot reload

`active.yaml` is the local POC serialization of a catalog revision. Do not put
that file in the platform image and do not treat a shared file as the production
writer interface.

In production, the catalog control plane stores small assignment records such
as:

```yaml
environment: production
scope: global
capability: internal_transfer
version: 2.1.0
artifact: company.jfrog.io/nexus-capability-release/internal-transfer
digest: sha256:...
runtimeApi: nexus.runtime/v1
state: active
catalogRevision: 1842
```

DynamoDB is a reasonable implementation for these records and atomic revision
updates, but it is not an architectural requirement. A relational database or
another durable store can satisfy the same catalog API. If DynamoDB is chosen,
store assignments and revisions as records rather than storing `active.yaml` as
one opaque production blob.

Hot reload is an event-assisted pull process:

1. Publication or promotion commits a new environment-scoped catalog revision.
2. The catalog emits an event containing only the environment, scope, and new
   revision—not executable skill content.
3. Matching runtime instances fetch the coherent assignment snapshot.
4. Each runtime pulls newly referenced OCI packages by digest.
5. It verifies identity, signature, compatibility, contracts, and required
   tools, then compiles them into a private cache.
6. If every required check passes, it atomically swaps routing for new goals.
7. In-flight plans remain pinned to their original digest.
8. If verification fails, the runtime retains its last-known-good catalog and
   reports the rejection.
9. Periodic reconciliation repairs missed or delayed events.

DynamoDB Streams with EventBridge, or an equivalent change-event mechanism,
can implement the notification path. Runtimes still reconcile periodically;
the event reduces latency but is not the sole source of correctness.

## What is implemented and what remains

Implemented in the POC:

- validated Markdown skill compilation;
- immutable file publication by name and version;
- separate publication and activation operations;
- runtime polling of `active.yaml`;
- last-known-good behavior for an invalid catalog update;
- exact version and hash pinning for active work; and
- explicit catalog paths for isolated local servers and publishers.

Still to build:

- automatic capability-workspace overlay and file watching;
- worktree/preview ID generation and cleanup;
- OCI package builder and JFrog backend;
- authoring and publication service APIs;
- catalog database and environment-scoped assignment API;
- event delivery and periodic remote reconciliation;
- signing, provenance, compatibility, and rollout health enforcement; and
- the business/IT authoring UI.

## Technology references

- JFrog Artifactory supports OCI repositories and ORAS push, pull, and referrer
  operations: <https://docs.jfrog.com/artifactory/docs/oci-repositories>.
- ORAS artifacts can be pulled by tag or digest and stored in a local
  content-addressable cache:
  <https://oras.land/docs/commands/oras_pull/>.
- DynamoDB conditional expressions can protect catalog revision updates from
  concurrent overwrites:
  <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html>.
- DynamoDB Streams and EventBridge Pipes can distribute item-level change
  notifications:
  <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/eventbridge-for-dynamodb.html>.
