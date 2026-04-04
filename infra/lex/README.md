# Lex Bot Configuration

This directory contains Amazon Lex bot definitions for Nexus.

## Structure
- `bot.json` – Lex bot resource definition
- `intents/` – Intent configurations imported from `/intents/*.yaml`

## Deployment
```bash
aws lex-models put-bot --cli-input-json file://bot.json
```
