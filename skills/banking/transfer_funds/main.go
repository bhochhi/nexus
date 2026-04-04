package main

import (
	"context"
	"fmt"
	"log"

	"github.com/aws/aws-lambda-go/lambda"
)

// Request is the input for transfer_funds.
type Request struct {
	UserID        string  `json:"user_id"`
	FromAccountID string  `json:"from_account_id"`
	ToAccountID   string  `json:"to_account_id"`
	Amount        float64 `json:"amount"`
	Currency      string  `json:"currency"`
}

// Response is the output for transfer_funds.
type Response struct {
	TransactionID string  `json:"transaction_id"`
	Status        string  `json:"status"`
	Amount        float64 `json:"amount"`
	Currency      string  `json:"currency"`
}

func handler(ctx context.Context, req Request) (Response, error) {
	log.Printf("transfer_funds invoked: user_id=%s from=%s to=%s amount=%.2f",
		req.UserID, req.FromAccountID, req.ToAccountID, req.Amount)

	if req.UserID == "" {
		return Response{}, fmt.Errorf("user_id is required")
	}
	if req.FromAccountID == "" || req.ToAccountID == "" {
		return Response{}, fmt.Errorf("from_account_id and to_account_id are required")
	}
	if req.Amount <= 0 {
		return Response{}, fmt.Errorf("amount must be greater than zero")
	}

	currency := req.Currency
	if currency == "" {
		currency = "USD"
	}

	// TODO: replace with core banking transfer logic
	resp := Response{
		TransactionID: "TXN-PLACEHOLDER",
		Status:        "pending",
		Amount:        req.Amount,
		Currency:      currency,
	}

	log.Printf("transfer_funds succeeded: transaction_id=%s status=%s", resp.TransactionID, resp.Status)
	return resp, nil
}

func main() {
	lambda.Start(handler)
}
