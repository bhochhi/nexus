---
apiVersion: nexus.platform/v1
kind: PlatformFoundation
metadata: {id: PFND-MODEL-PROVIDER-BOUNDARY, name: model-provider-boundary, status: approved, version: 1.0.0, owner: Agentic Conversation Platform}
decisions: [ADR-0003]
interfaces: [ModelProvider, TurnAnalysis, ResponseDraft]
---
# Model provider boundary
## Purpose
Keep model vendors replaceable and probabilistic output outside official control state.
## Responsibilities
- Normalize provider requests, structured turn analysis, response generation, guardrail outcomes, diagnostics, and fallback behavior.
## Invariants
- **INV-PROVIDER-001:** Provider-specific payloads never become durable domain state.
- **INV-PROVIDER-002:** Safety interventions and provider failures cannot be bypassed by fallback.
## Interfaces
- Provider gateway, structured analysis contract, and response-composition request.
## Failure behavior
- Return safe typed errors with secrets redacted and preserve safety classification.
## Verification
- `tests/test_providers.py`, `tests/test_bedrock_provider.py`.
