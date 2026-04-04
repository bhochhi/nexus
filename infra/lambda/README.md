# Lambda Infra Configuration

This directory contains infrastructure definitions for deploying Nexus Lambda functions.

## Skills → Lambda Mapping
| Skill               | Handler File                          |
|---------------------|---------------------------------------|
| get_account_balance | skills/banking/get_account_balance.go |
| transfer_funds      | skills/banking/transfer_funds.go      |
| report_fraud        | skills/banking/report_fraud.go        |
| check_claim_status  | skills/insurance/check_claim_status.go|
| file_claim          | skills/insurance/file_claim.go        |
| answer_faq          | skills/faq/answer_faq.go              |

## Deployment
```bash
make build   # compiles Go binaries
make deploy  # packages and deploys to AWS Lambda
```
