# Specification baseline and rebuild readiness

This document defines what it means for Nexus specifications to be a source of
truth, what the current baseline guarantees, and what must be true before the
application is certified as reproducible from specifications alone.

## Current baseline classification

The current specification set is ready to pin as:

```text
baseline: Nexus specifications v0.1
classification: architecture and capability baseline
authority: normative for covered intent and behavior
clean-room rebuild certification: not certified
```

Pinning this baseline records a stable constitution, ADR set, platform
foundations, cross-capability features, machine-contract baseline, and business
capability specifications. It does not claim that every implementation detail
needed to recreate the present application has been specified.

## Two meanings of source of truth

Nexus distinguishes two claims that are often conflated:

1. **Normative authority:** When an approved specification and implementation
   disagree within the specification's stated scope, the specification wins and
   the implementation must be corrected or the specification deliberately
   revised.
2. **Rebuild completeness:** An independent team or development agent can
   recreate an implementation with equivalent observable behavior using only a
   pinned specification package and its declared inputs.

The v0.1 baseline satisfies the first claim for the behavior it covers. It does
not yet satisfy the second claim for the complete application. Unspecified
behavior remains an implementation detail and must not be presented as if it
were already governed by a specification.

## What the baseline covers well

- specification authority, terminology, governance, and quality gates;
- durable architectural choices and platform/capability separation;
- platform ownership boundaries and cross-capability invariants;
- the business purpose, risk, scenarios, failures, and acceptance criteria for
  the current capability packages;
- the bounded declarative capability surface and core state, event, provider,
  and tool contract shapes;
- the portable development lifecycle used by Codex, GitHub Copilot, Claude
  Code, and other development agents.

## Why a specification-only rebuild is not certified

The current specifications do not yet determine all observable details of the
running application. A clean-room implementation would still need to infer
material behavior from source code, tests, runtime artifacts, or documentation
outside the pinned specification package, including:

- complete HTTP and WebSocket endpoints, message schemas, sequencing, replay,
  reconnect, error, and session-expiration behavior;
- persistence tables, transactional boundaries, migrations, cleanup, audit
  retention, and restart recovery;
- the full decision precedence and task-transition state machine;
- exact catalog snapshot, artifact hashing, compilation, activation,
  last-known-good, and rollback behavior;
- provider request/response normalization, parsing, fallback, and safety-error
  contracts;
- member and service-representative UI journeys, state, accessibility, and
  browser failure behavior;
- configuration keys, defaults, environment precedence, ports, packaging, and
  deployment topology;
- exact active catalog assignments, immutable artifact digests, controlled
  response copy, and reference data required for behavioral parity.

The portable workflow skills guide an agent through development, but they do
not fill these product-specification gaps. A capable agent can build a
recognizable and architecturally aligned application from v0.1; it cannot be
expected to reproduce the current application consistently.

## Rebuild-complete package

A rebuild-certified baseline must declare and hash all required inputs. The
portable package should include:

```text
specifications/       constitution, ADRs, foundations, features, capabilities,
                      UI/transport/configuration specs, and machine contracts
workflow/             portable lifecycle and thin agent adapters
capabilities/         candidate executable capability artifacts
conformance/          black-box scenarios, golden event sequences, contract
                      tests, fixtures, and expected validation failures
manifest.yaml         baseline version, artifact hashes, compatibility,
                      acceptance coverage, and required toolchain versions
```

Published catalog artifacts remain immutable release evidence rather than the
source of business intent. The baseline manifest must nevertheless identify the
exact candidate sources and deterministic process used to reproduce them.

## Certification gate

Rebuild completeness is demonstrated, not asserted:

1. Pin the candidate specification package and its manifest.
2. Create an empty repository with no access to the Nexus implementation.
3. Give one or more development agents only the pinned package and declared
   toolchain.
4. Build and run the resulting application independently.
5. Execute the same black-box conformance suite against the reference and
   reconstructed applications.
6. Compare externally observable API events, state transitions, capability
   outcomes, failures, restart behavior, and UI journeys.
7. Record every implementation question or divergent result as a specification
   gap, then revise the appropriate authoritative artifact.
8. Repeat until the required coverage and parity gates pass.

Only a baseline that passes this exercise may use the classification
`rebuild-certified`. Passing once is not permanent: a material feature or
contract change invalidates certification until its conformance evidence is
regenerated.

## Pinning and change policy

- Pin v0.1 by an immutable Git tag after the baseline is merged and validation
  passes from a clean checkout.
- Record the source commit, specification evidence hashes, validation result,
  and known gaps in the release notes or baseline manifest.
- Do not retag altered content. Corrections produce a new baseline version.
- Approved specifications remain normative within their scope even while the
  overall baseline is not rebuild-certified.
- Track rebuild-readiness work as platform specification and conformance work,
  not as undocumented implementation cleanup.

The schema and authority order are defined in
`specifications/SCHEMA.md`. The operating lifecycle is defined in
`docs/spec-driven-development.md`.
