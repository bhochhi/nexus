# Operating Model Context for Codex / AI Development Agent

Use this context when extending the enterprise conversational AI platform repository with organizational delivery assets, developer workflow support, evaluation tooling, and capability onboarding automation.

## Purpose

The platform is not only a runtime chatbot. It is supported by a development-time agentic workflow that helps teams create, implement, validate, and publish business capabilities from specifications.

## Core distinction

- **Development-time agentic workflow:** AI-assisted engineering process that helps write capability specs, architecture mapping, implementation tasks, tests, validation suites, and publication artifacts.
- **Runtime agentic platform:** member-facing conversational runtime that understands member objectives, manages goals, advances execution plans, calls approved capabilities/tools, composes responses, and applies guardrails.

## Organizational principle

Build the platform once. Build capabilities many times.

## Workstreams to reflect in code and tooling

1. **Platform Runtime**
   - Owns orchestration, LangGraph state, session/goal management, model provider abstraction, capability runtime, tool execution, response composition, guardrail integration, and channel adapters.

2. **Developer Platform**
   - Owns Codex/Copilot instructions, templates, scaffolding, capability packaging, validation commands, CI/CD hooks, and registry publication workflows.

3. **Capability Pods**
   - Own capability specs, prompts/contracts, tool adapters, response contracts, golden conversation tests, and business acceptance criteria.

4. **AI Quality & Evaluation Engineering**
   - Owns golden conversation suites, synthetic scenario generation, evaluation gates, regression dashboards, response compliance validation, and production quality feedback.

5. **Observability / Ops / FinOps**
   - Owns tracing, dashboards, cost per completed objective, latency/error monitoring, model/tool visibility, and incident/release health.

6. **Cloud / Security / Infrastructure**
   - Owns AWS deployment, IAM, secrets, network controls, logging, security review, and runtime environment management.

7. **AI COE Enablement**
   - Provides reference architecture, standards, model/provider guidance, evaluation patterns, guardrail guidance, training, reusable assets, and architecture review support.

## Implementation guidance

When building the prototype, do not create a monolithic agent. Preserve boundaries between runtime orchestration, capability definitions, developer workflow tooling, and evaluation tooling.

Every capability should have:

- A capability specification.
- A conversation contract.
- An execution contract.
- A response contract.
- Guardrail requirements.
- Tool permissions.
- Golden conversation tests.
- Acceptance criteria.

Every release should include:

- Unit tests.
- Integration tests.
- Golden conversation evaluation.
- Response contract validation.
- Guardrail compliance checks.
- Observability/tracing confirmation.
- Cost and latency baseline.

## AI COE boundary

Do not encode AI COE as the owner of every capability. Treat AI COE as an enablement and standards function. Product/platform teams own delivery and runtime operations.
