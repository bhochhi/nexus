# Quarter-One Capability Publication and Runtime Activation

**Status:** Proposed quarter-one delivery design  
**Scope:** Capability artifacts and catalog activation for AWS Lambda runtimes  
**Applies to:** Member Search AI Overview and the reusable capability platform spine

## 1. Decision summary

Quarter one uses three separate stores of truth:

1. **Git** stores the reviewable capability source, specifications, tests, and
   evaluation scenarios.
2. **Amazon S3** stores immutable, versioned skill artifacts separately in each
   AWS environment account.
3. **Amazon DynamoDB** stores the small environment-specific catalog records
   that identify which exact skill versions are active.

GitLab CI/CD is the only production publisher. It builds a skill artifact once,
tests that exact content in the test environment, and promotes the same bytes
into the production S3 bucket after the required approvals. Test workloads do
not communicate with production, and the production runtime never reads from a
test bucket or table.

Terraform provisions the buckets, tables, stream processing, encryption,
policies, alarms, and narrowly scoped CI/CD and runtime identities. Terraform
does not activate individual skill versions during normal capability releases;
the promotion pipeline changes catalog assignments through the catalog API or
a controlled DynamoDB update.

This Q1 recommendation selects S3 instead of the OCI/JFrog repository named in
the currently proposed `ADR-0002`. Before implementation, architecture owners
must revise that proposed ADR or accept a superseding decision. The durable
architectural boundary remains unchanged: immutable artifact storage is
separate from environment activation state.

## 2. Why artifact storage and activation are separate

Publishing an artifact means that an immutable skill version exists and passed
the publication checks. Activation means that an approved environment is
allowed to route new work to that exact version.

These are intentionally different operations:

```text
Git source
  -> validate, test, evaluate, and package
  -> publish immutable artifact to S3
  -> approve promotion
  -> assign exact version and digest in DynamoDB
  -> runtime verifies and activates for new goals
```

Uploading an object to S3 must not make it active automatically. This prevents
draft, rejected, or partially promoted artifacts from entering production
routing.

## 3. Environment isolation

Each AWS account owns its environment resources.

```text
Test AWS account
  - test capability-artifact S3 bucket
  - test capability-catalog DynamoDB table
  - test conversation runtime

Production AWS account
  - production capability-artifact S3 bucket
  - production capability-catalog DynamoDB table
  - production conversation runtime
```

The production runtime has no permission to read test resources. The test
runtime and test deployment identity have no permission to write production
resources.

GitLab uses separate protected deployment identities:

| Identity | Minimum responsibility |
|---|---|
| Build identity | Validate, test, evaluate, package, hash, and retain the pipeline artifact |
| Test publisher | Write the approved candidate to test S3 and update only the test catalog |
| Production promoter | Write the approved release to production S3 and conditionally update only the production catalog |
| Conversation runtime | Read the catalog and referenced artifacts in its own account; report activation health separately |

Business, risk, and release authorities approve production promotion, but
neither a business browser nor an engineer's workstation writes directly to
production S3 or DynamoDB.

## 4. Build once and promote the same content

The build pipeline creates one deterministic bundle, for example:

```text
member-search-ai-overview-1.0.0.tar.gz
sha256:a81f...
```

The SHA-256 digest is the identity of the exact content. Changing any byte
changes the digest. The release evidence records the capability name, semantic
version, digest, source commit, runtime contract, tool dependencies, evaluation
dataset, test results, and approvals.

The sequence is:

1. GitLab builds the bundle once and calculates its digest.
2. The test publisher uploads that bundle to the test S3 bucket.
3. Test runtime, integration, security, and evaluation checks exercise that
   exact digest.
4. GitLab retains the original pipeline artifact or an approved release escrow
   retains it outside the test account.
5. After approval, the protected production job retrieves the retained
   original—not the copy from test S3—and verifies its digest.
6. The production promoter uploads the same bytes to production S3.
7. It reads the object back or otherwise verifies that the production object
   has the approved content digest.
8. It transactionally assigns that artifact in the production DynamoDB
   catalog.

Production therefore receives what was tested without establishing a test-to-
production connection and without rebuilding the release.

## 5. S3 artifact layout

Use an immutable, content-addressed key rather than a mutable `latest` object.

```text
s3://<environment>-nexus-capability-releases/
  capabilities/
    member-search-ai-overview/
      1.0.0/
        sha256-a81f.../
          capability-bundle.tar.gz
          manifest.json
          evidence.json
          signature.json
```

Required controls include:

- S3 versioning and encryption;
- public access blocked;
- append-only publication behavior for released keys;
- bucket policies limited to the environment's publisher and runtime roles;
- lifecycle and retention rules appropriate to audit and rollback needs;
- CloudTrail data events or equivalent publication audit evidence;
- digest and, when available, signature verification before activation.

Semantic versions are useful for people. The digest is the integrity boundary.
The same name and version cannot be overwritten with different content.

## 6. DynamoDB catalog model

DynamoDB contains catalog and activation metadata, not complete skill bundles.
At minimum, maintain an immutable release record and a mutable environment
assignment.

Example release record:

```yaml
PK: CAPABILITY#member_search_ai_overview
SK: VERSION#1.0.0
artifactUri: s3://prod-nexus-capability-releases/capabilities/...
artifactDigest: sha256:a81f...
runtimeApi: nexus.runtime/v1
status: published
evidenceId: release-2026-104
```

Example active assignment:

```yaml
PK: ENVIRONMENT#production
SK: CAPABILITY#member_search_ai_overview
activeVersion: 1.0.0
artifactDigest: sha256:a81f...
state: active
catalogRevision: 42
rolloutScope: global
```

The production promotion job updates the assignment with a conditional write,
for example, "replace revision 41 only if it is still revision 41." This avoids
lost updates when promotions or rollbacks overlap.

The runtime does not change desired assignments. It may write activation health
to a separate table, event stream, or observability destination so desired
state and observed state cannot be confused.

## 7. Catalog update and Lambda runtime behavior

DynamoDB Streams can detect an assignment change and invoke a catalog-change
processor Lambda. The processor validates the event, emits an operational
notification, and can warm or validate shared caches. It must not treat the
stream event itself as the complete catalog or executable skill content.

An important Lambda constraint is that existing execution environments are not
addressable as a stable fleet. Invoking a conversation Lambda with a refresh
event does not guarantee that every warm execution environment updates its
in-memory cache. Therefore, event-driven refresh improves speed but does not
provide correctness by itself.

The conversation runtime uses this rule:

1. On cold start, read the current catalog revision and assignments.
2. Before handling a turn, compare a cached revision with the authoritative
   environment revision, either every invocation or within a short bounded TTL.
3. When the revision differs, fetch a coherent assignment snapshot.
4. Download newly referenced artifacts from the environment's S3 bucket.
5. Verify digest, signature, runtime compatibility, contracts, policies, and
   required tools.
6. Compile the skill into the execution environment's private cache.
7. Atomically replace the local routing snapshot only after all checks pass.
8. Keep the last-known-good snapshot when any check fails.
9. Pin existing goals to their original version and digest; use the new version
   only for newly selected goals unless an explicit migration policy exists.

For Q1, a revision check on every invocation is the simplest correctness model.
If measurement shows excessive DynamoDB reads or latency, add a small TTL cache
while retaining cold-start and periodic reconciliation.

## 8. End-to-end publication and activation sequence

```text
Business and IT approve capability behavior
  -> merge reviewed source
  -> GitLab validates specifications and contracts
  -> GitLab runs tests and evaluations
  -> GitLab builds one immutable bundle and digest
  -> test publisher uploads it to test S3
  -> test publisher assigns it in test DynamoDB
  -> test runtime verifies and activates it
  -> release evidence and approvals complete
  -> protected production promoter verifies the original bundle
  -> promoter uploads it to production S3
  -> promoter conditionally updates production DynamoDB
  -> DynamoDB Stream invokes catalog-change processor
  -> conversation Lambda observes the new revision
  -> runtime downloads, verifies, compiles, and atomically activates
  -> runtime reports activation success or rejection
```

The promotion pipeline must not mark the rollout complete merely because the
DynamoDB write succeeded. Completion requires the expected runtime population
or production synthetic checks to confirm the assigned digest is usable.

## 9. Rollback and deactivation

Rollback changes the active assignment to a previously published and retained
digest. It does not rebuild or overwrite an artifact.

```text
catalog revision 42 -> member_search_ai_overview 1.0.0 sha256:a81f...
catalog revision 43 -> member_search_ai_overview 0.9.2 sha256:73c6...
```

The same runtime verification and atomic activation path applies to rollback.
Emergency deactivation removes the capability from selection for new goals but
does not delete its artifact while in-flight work, evidence retention, or audit
requirements still reference it.

## 10. Failure behavior

| Failure | Required behavior |
|---|---|
| S3 upload or verification fails | Do not update the environment assignment |
| Conditional catalog update fails | Stop and reconcile; do not overwrite the newer revision |
| DynamoDB Stream delivery is delayed or duplicated | Revision comparison makes processing idempotent |
| Runtime cannot download the artifact | Retain last-known-good catalog and alert |
| Digest, signature, or compatibility validation fails | Reject the revision, retain last-known-good, and report evidence |
| One Lambda execution environment has stale cache | Invocation-time revision check converges it before serving changed routing |
| Production activation is unhealthy | Roll back the assignment to the prior approved digest |

## 11. Terraform responsibility

Terraform provisions stable infrastructure and permissions:

- environment-owned S3 buckets and policies;
- DynamoDB catalog tables, indexes, streams, backups, and point-in-time recovery;
- catalog-change processor Lambda and event-source mapping;
- KMS keys and key policies;
- GitLab workload identities and environment-specific IAM roles;
- runtime read permissions and activation-health write permissions;
- logs, metrics, alarms, dead-letter handling, and dashboards.

Normal capability publication and activation are release data changes, not
Terraform changes. Terraform should not be applied every time a business skill
version changes.

## 12. Quarter-one definition of done

- Test and production accounts have independent S3 buckets and DynamoDB tables.
- Terraform can reproduce the infrastructure and least-privilege identities.
- GitLab builds one artifact and promotes the exact digest without rebuilding.
- The test environment cannot write to or supply artifacts directly to
  production.
- Only a protected production promotion identity can publish and assign a
  production version.
- Publishing and activation are distinct, auditable operations.
- The conversation Lambda detects a catalog revision change on cold start and
  before serving changed routing.
- Runtime validation preserves the last-known-good catalog on failure.
- In-flight goals remain pinned to their original skill digest.
- Rollback and emergency deactivation are tested.
- Release evidence connects source commit, artifact digest, tests, evaluations,
  approvals, production assignment, and observed activation health.

## 13. Future evolution

The Q1 design preserves interfaces that can later support an OCI registry,
canary or tenant-specific assignments, a business-facing Capability Studio,
central release orchestration, signed attestations, and a dedicated catalog
service. Those additions should not change the core boundary:

> The artifact repository stores immutable capability bytes; the catalog
> control plane decides which verified digest an environment may activate.
