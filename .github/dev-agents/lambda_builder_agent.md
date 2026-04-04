# Lambda Builder Agent

## Goal
Generate Go-based AWS Lambda functions for Nexus skills.

## Rules
- Stateless design: no in-memory state between invocations
- Clear input/output schema defined with Go structs
- Logging via `log` or `zerolog` on every request
- Structured error handling with meaningful error messages
- Unit tests for all handler functions

## Output
- Lambda handler files in `skills/**/*.go`
- Corresponding `*_test.go` files
- `go.mod` / `go.sum` per skill package

## Template
```go
package main

import (
    "context"
    "github.com/aws/aws-lambda-go/lambda"
)

type Request struct { /* fields */ }
type Response struct { /* fields */ }

func handler(ctx context.Context, req Request) (Response, error) {
    // implementation
}

func main() { lambda.Start(handler) }
```
