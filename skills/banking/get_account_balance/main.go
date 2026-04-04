package main

import (
	"context"
	"fmt"
	"log"

	"github.com/aws/aws-lambda-go/lambda"
)

// Request is the input for get_account_balance.
type Request struct {
	UserID    string `json:"user_id"`
	AccountID string `json:"account_id"`
}

// Response is the output for get_account_balance.
type Response struct {
	AccountID string  `json:"account_id"`
	Balance   float64 `json:"balance"`
	Currency  string  `json:"currency"`
}

func handler(ctx context.Context, req Request) (Response, error) {
	log.Printf("get_account_balance invoked: user_id=%s account_id=%s", req.UserID, req.AccountID)

	if req.UserID == "" {
		return Response{}, fmt.Errorf("user_id is required")
	}
	if req.AccountID == "" {
		return Response{}, fmt.Errorf("account_id is required")
	}

	// TODO: replace with DynamoDB / core banking lookup
	resp := Response{
		AccountID: req.AccountID,
		Balance:   0.00,
		Currency:  "USD",
	}

	log.Printf("get_account_balance succeeded: account_id=%s balance=%.2f", resp.AccountID, resp.Balance)
	return resp, nil
}

func main() {
	lambda.Start(handler)
}
