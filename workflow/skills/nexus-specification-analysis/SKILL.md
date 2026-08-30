---
name: nexus-specification-analysis
description: Analyze a Nexus change request to identify its intended outcome, ambiguity, governing specifications, and correct source artifact before planning or coding. Use at the start of new platform or capability work and when implementation exposes missing requirements.
---

# Nexus specification analysis

Announce `Workflow stage: specification_analysis`.

Read the constitution, then inspect only relevant accepted ADRs, platform
features, capability packages, contracts, published behavior, and tests.

Determine:

- the member, business, operational, or platform outcome;
- what is in and out of scope;
- unresolved behavior, examples, failures, risk, ownership, and terminology;
- whether an existing specification should change or a new one is required;
- which acceptance criteria need stable IDs;
- whether current code and specifications already disagree.

Update the highest-authority applicable Markdown specification when intent is
clear. Ask for direction only when a missing choice materially changes scope,
risk, or business behavior. Do not begin implementation from an ambiguous
request merely because the code path seems obvious.

Finish with sufficient specification detail for structural validation.
