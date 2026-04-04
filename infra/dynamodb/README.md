# DynamoDB Configuration

This directory contains DynamoDB table definitions for Nexus memory storage.

## Tables

### nexus-sessions
- **Partition key**: `user_id` (String)
- **Sort key**: `session_id` (String)
- **TTL attribute**: `expires_at`
- **Schema**: see `/memory/schema.json`

## Deployment
```bash
aws dynamodb create-table \
  --table-name nexus-sessions \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=session_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=session_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```
