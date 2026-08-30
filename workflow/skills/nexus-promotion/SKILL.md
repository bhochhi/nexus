---
name: nexus-promotion
description: Gate and coordinate promotion of verified Nexus platform or capability changes to an authorized environment. Use only when release evidence and required approvals exist and the user has requested release or activation work.
---

# Nexus promotion

Announce `Workflow stage: promotion`.

Promotion is an externally mutating stage and requires explicit scope and
authority. Before acting, verify:

- exact source commit, artifact version, and immutable digest;
- complete release evidence and acceptance coverage;
- independent verification for consequential changes;
- approved change request and environment authorization;
- target runtime, connector, tool, and contract compatibility;
- rollback artifact and operational monitoring.

Build once and promote the tested digest; do not rebuild different content for
production. Publication and activation are separate. Activation affects new
goals while in-flight plans remain pinned.

If the production publication service, catalog control plane, or approval
integration is not implemented, report the missing control instead of simulating
success or editing the POC active index as a substitute.
