# Reviewer Agent

## Goal
Review code quality and system integrity for all Nexus contributions.

## Checks

### Correctness
- Logic handles all edge cases
- Error paths are properly handled
- No data races in concurrent code

### Security
- No hardcoded secrets or credentials
- Input is validated before use
- IAM permissions follow least-privilege principle

### Performance
- Lambda cold start impact is minimized
- DynamoDB access patterns are efficient
- No unnecessary external calls

### Naming Consistency
- Intent names match across `intents/`, `agents/`, and skill handlers
- Skill names in `conversation_agent.yaml` match deployed Lambda function names
- Go package and function names follow Go conventions
