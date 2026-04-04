# Nexus – Agentic Chatbot Platform

Nexus is a production-ready agentic chatbot platform for financial services, built on AWS.

## Architecture

```
User → Lex → Lambda → Bedrock → conversation_agent → Skills → Response
```

### AWS Services
| Service         | Role                                      |
|-----------------|-------------------------------------------|
| Amazon Lex      | Intent detection and slot filling         |
| Amazon Bedrock  | LLM reasoning (Claude)                    |
| AWS Lambda      | Stateless skill execution                 |
| Amazon DynamoDB | Session memory and conversation history   |

## Project Structure

```
nexus/
├── agents/          # Runtime agent definitions
├── skills/          # Go-based Lambda skill handlers
├── instructions/    # Behavioral rules and guardrails
├── intents/         # 30 domain intents (banking, insurance, FAQ)
├── prompts/         # LLM system and routing prompts
├── memory/          # DynamoDB session schema
├── infra/           # AWS infrastructure definitions
└── tests/           # Conversation and load tests
```

## Skills (Lambda Functions)

| Domain    | Skill                 |
|-----------|-----------------------|
| Banking   | get_account_balance   |
| Banking   | transfer_funds        |
| Banking   | report_fraud          |
| Insurance | check_claim_status    |
| Insurance | file_claim            |
| FAQ       | answer_faq            |

## Getting Started

### Prerequisites
- Go 1.21+
- AWS CLI configured
- Python 3 (for test validation)

### Build
```bash
make build
```

### Test
```bash
make test
```

### Lint
```bash
make lint
```

### Deploy
```bash
make deploy
```

## Intents (30 Total)
- **Banking (10):** check_balance, transfer_money, view_transactions, report_fraud, freeze_card, activate_card, update_contact_info, open_account, close_account, dispute_transaction
- **Insurance (10):** file_claim, check_claim_status, update_policy, get_policy_details, add_vehicle, remove_vehicle, request_quote, renew_policy, cancel_policy, roadside_assistance
- **FAQ (10):** hours_of_operation, contact_support, reset_password, app_help, website_help, fees_info, eligibility, locations, security_info, general_info
