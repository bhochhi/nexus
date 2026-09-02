---
apiVersion: nexus.capabilities/v1
kind: Capability
metadata:
  id: CAP-APPROVED-KNOWLEDGE
  name: approved-knowledge
  status: approved
  owner: Member Knowledge Product
archetype: declarative
risk: informational
implementation:
  skill: specifications/capabilities/approved-knowledge/SKILL.md
  publishedSkill: skills/catalog/approved_knowledge/2.1.0/SKILL.md
---

# Approved knowledge answers

## Purpose and member value

Give members useful banking and insurance answers drawn only from approved,
current knowledge while retaining source identity and required disclosures.

## Scope

- Answer supported FAQ and policy questions from the approved knowledge source.
- Return at most the configured number of sources.
- Preserve the approved answer, source identifier, source title, and disclosure.
- Exclude open-ended financial advice and any answer unsupported by retrieved
  approved content.

## Member scenarios

### Supported question

> How does overdraft protection work?

The capability retrieves a matching approved entry and returns its controlled
answer with source and disclosure.

### No approved source

> What investment should I buy today?

The capability does not answer from model memory and offers governed assistance
or handoff.

## Required behavior

1. Use the complete member question as the retrieval query.
2. Search only the configured approved source.
3. Render an answer only when the tool returns an approved match.
4. Retain source ID, title, and disclosure in the member-visible response and
   structured outcome.
5. Return controlled no-source behavior without supplementing from model memory.

## Acceptance criteria

- **AC-KNOWLEDGE-001 — Approved grounding:** Every substantive answer is derived
  from an approved retrieved record.
- **AC-KNOWLEDGE-002 — Source retention:** A successful answer contains its
  source identifier, title, and required disclosure.
- **AC-KNOWLEDGE-003 — No-source safety:** No approved match produces no invented
  answer and follows configured assistance behavior.
- **AC-KNOWLEDGE-004 — Query fidelity:** The member's complete question is sent
  to retrieval without converting it into an unsupported claim.
- **AC-KNOWLEDGE-005 — Controlled result count:** Retrieval never exceeds the
  configured maximum source count.

## Examples

> Are my deposits insured?

The response uses the approved deposit-insurance entry and identifies that
entry. It does not generalize beyond the retrieved material.

## Edge cases and failures

- Retrieval returns no matches, several matches, or an unavailable source.
- An approved record has a required disclosure.
- A question combines a supported FAQ with unsupported personal advice.
- Retrieved content is stale, malformed, or missing source metadata.

## Governance and integrations

- Risk tier: informational.
- Authentication is not required for the current public FAQ material.
- Approved tool: local approved-knowledge retrieval in the POC.
- Failure behavior: offer governed handoff rather than answer from memory.

## Verification

- Deterministic tests cover grounded answer and no-source paths.
- Contract tests validate required source metadata.
- LLM judging may evaluate clarity but not whether grounding occurred.
