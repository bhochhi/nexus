package main

import (
	"context"
	"fmt"
	"log"

	"github.com/aws/aws-lambda-go/lambda"
)

// Request is the input for report_fraud.
type Request struct {
	UserID        string `json:"user_id"`
	AccountID     string `json:"account_id"`
	TransactionID string `json:"transaction_id"`
	Description   string `json:"description"`
}

// Response is the output for report_fraud.
type Response struct {
	CaseID  string `json:"case_id"`
	Status  string `json:"status"`
	Message string `json:"message"`
}

func handler(ctx context.Context, req Request) (Response, error) {
	log.Printf("report_fraud invoked: user_id=%s account_id=%s transaction_id=%s",
		req.UserID, req.AccountID, req.TransactionID)

	if req.UserID == "" {
		return Response{}, fmt.Errorf("user_id is required")
	}
	if req.AccountID == "" {
		return Response{}, fmt.Errorf("account_id is required")
	}

	// TODO: replace with fraud reporting service call
	resp := Response{
		CaseID:  "CASE-PLACEHOLDER",
		Status:  "open",
		Message: "Your fraud report has been received and is under review.",
	}

	log.Printf("report_fraud succeeded: case_id=%s status=%s", resp.CaseID, resp.Status)
	return resp, nil
}

func main() {
	lambda.Start(handler)
}
