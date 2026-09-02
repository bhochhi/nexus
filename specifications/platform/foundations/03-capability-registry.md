---
apiVersion: nexus.platform/v1
kind: PlatformFoundation
metadata: {id: PFND-CAPABILITY-REGISTRY, name: capability-registry, status: approved, version: 1.0.0, owner: Agentic Conversation Platform}
decisions: [ADR-0002, ADR-0004]
interfaces: [CapabilityDescriptor, ArtifactReference, CatalogRevision]
---
# Capability registry
## Purpose
Discover compatible capabilities dynamically while keeping full artifacts out of general routing context.
## Responsibilities
- Load compact discovery metadata, lazily resolve an exact immutable artifact, and atomically change active assignments.
- Preserve last-known-good assignments when validation fails.
## Invariants
- **INV-REGISTRY-001:** Routing uses bounded metadata; execution uses the exact versioned artifact.
- **INV-REGISTRY-002:** Unpublished files cannot change the active capability surface.
## Interfaces
- Catalog snapshot, artifact loader, compiler, and activation event contracts.
## Failure behavior
- Keep the last valid revision and expose validation errors operationally.
## Verification
- `tests/test_skill_authoring.py`, `tests/test_interruption_and_catalog.py`.
