---
name: nexus-release-evidence
description: Assemble reproducible Nexus release evidence connecting specifications, acceptance IDs, source commits, candidate artifact digests, contracts, tests, evaluations, compatibility, and approvals. Use after verification and before promotion.
---

# Nexus release evidence

Announce `Workflow stage: release_evidence`.

Produce evidence from declared inputs and exact content. Use
`member-assistant-specs evidence` for deterministic file hashes, supplemented by
machine-readable test and evaluation results.

Evidence identifies:

- constitution, ADR, feature, and capability specification revisions;
- implemented and verified acceptance IDs;
- source commit and candidate skill version/digest;
- platform runtime, connector, tool, and contract compatibility;
- deterministic test results and semantic evaluation rubric/version;
- known limitations and deviations;
- verifier and required business/risk approvals;
- target environment and rollback digest.

Do not edit evidence to hide a failing result. Regenerate it after any source,
skill, contract, or test change. Evidence supports an approval decision; it does
not grant promotion authority itself.
