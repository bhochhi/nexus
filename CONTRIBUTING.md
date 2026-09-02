# Contributing

Thank you for helping improve Nexus.

## Before contributing

- Do not submit confidential, proprietary, personal, customer, production, or
  regulated data.
- Do not commit credentials, tokens, private keys, local databases, or populated
  environment files.
- Open an issue before a large architectural or behavioral change so scope and
  ownership can be agreed.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development workflow

Platform, contract, connector, capability, test, and release changes follow the
portable spec-driven workflow in
[`workflow/skills/nexus-spec-driven-development/SKILL.md`](workflow/skills/nexus-spec-driven-development/SKILL.md).
Read [`specifications/constitution.md`](specifications/constitution.md) before
changing source artifacts or code.

Update the highest-authority specification affected by the change. Do not edit
an immutable `skills/catalog/<name>/<version>/SKILL.md` artifact in place; build
the next candidate under `specifications/capabilities/<name>/`.

## Local checks

Create a Python virtual environment and install the development dependencies as
described in the README, then run:

```bash
member-assistant-specs validate
python -m pytest
```

After modifying code, refresh the repository knowledge graph:

```bash
graphify update .
```

Pull requests should explain the problem, affected specifications and
acceptance IDs, compatibility impact, verification performed, and rollback
approach. Consequential changes require independent verification before
promotion.

## Contributions and licensing

Unless explicitly stated otherwise, intentionally submitted contributions are
provided under the Apache License 2.0, consistent with the repository license.
You must have the right to submit the contribution.
