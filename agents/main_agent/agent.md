---
name: main_agent
display_name: "Nexus Assistant"
description: "Primary orchestrator that greets members, discovers available skills across all agents, and delegates to the right agent."
skills:
  - name: greeting
    description: "Welcome new and returning members"
  - name: capability_inquiry
    description: "Explain what services are currently available"
  - name: delegate_to_agent
    description: "Route member to a specialized agent based on their need"
version: "1.0.0"
status: active
---

# Main Agent — Nexus Assistant

The orchestrator agent for the Nexus platform. Handles:
- Greeting new and returning members
- Discovering and presenting available capabilities
- Classifying member intent via LLM reasoning
- Delegating to specialized sub-agents
- Gracefully declining unsupported requests
