# Specs — Format Guide

Every component in Nexus follows a two-tier spec process:

```
Feature Specs (business-readable)  →  "WHAT and WHY"
     ↓ derived from
Blueprints (technical)             →  "HOW exactly"
     ↓ derived from
Implementation (code)              →  "The code"
     ↓ derived from
Tests                              →  "Proof it works"
```

## Directory Structure

```
specs/
├── README.md                       # This file
├── features/                       # Business-readable specs — reviewed by stakeholders
│   ├── _template.md                # Feature spec template
│   ├── F-001-greeting.md
│   ├── F-002-agent-discovery.md
│   └── ...
└── blueprints/                     # Technical specs — derived from features
    ├── _template.md                # Blueprint template
    └── core/
        ├── types.spec.md
        ├── session.spec.md
        └── ...
```

## Rules

1. **Feature first.** No blueprint without an approved feature spec.
2. **Blueprint second.** No implementation code without a blueprint derived from the feature.
3. **Spec wins.** If code and spec disagree, fix the code (or update the spec with approval).
4. **Acceptance criteria are tests.** Each criterion maps to at least one test case.
5. **Reproducible.** Given only `specs/`, any engineer should be able to rebuild the system.

## Feature Spec vs Blueprint

| Aspect | Feature Spec | Blueprint |
|--------|-------------|-----------|
| **Audience** | Business stakeholders, product owners | Engineers, AI agents |
| **Language** | Plain English, no code | Code contracts, data models |
| **Focus** | What & Why | How exactly |
| **Approval** | Must be approved before blueprint | Must be approved before implementation |
| **Durability** | Survives tech stack changes | Tied to specific tech choices |
