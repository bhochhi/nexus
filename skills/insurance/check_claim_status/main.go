package main

import (
	"context"
	"fmt"
	"log"

	"github.com/aws/aws-lambda-go/lambda"
)

// Request is the input for check_claim_status.
type Request struct {
	UserID  string `json:"user_id"`
	ClaimID string `json:"claim_id"`
}

// Response is the output for check_claim_status.
type Response struct {
	ClaimID     string `json:"claim_id"`
	Status      string `json:"status"`
	LastUpdated string `json:"last_updated"`
	Details     string `json:"details"`
}

func handler(ctx context.Context, req Request) (Response, error) {
	log.Printf("check_claim_status invoked: user_id=%s claim_id=%s", req.UserID, req.ClaimID)

	if req.UserID == "" {
		return Response{}, fmt.Errorf("user_id is required")
	}
	if req.ClaimID == "" {
		return Response{}, fmt.Errorf("claim_id is required")
	}

	// TODO: replace with claims management system lookup
	resp := Response{
		ClaimID:     req.ClaimID,
		Status:      "in_review",
		LastUpdated: "2024-01-01",
		Details:     "Your claim is currently under review.",
	}

	log.Printf("check_claim_status succeeded: claim_id=%s status=%s", resp.ClaimID, resp.Status)
	return resp, nil
}

func main() {
	lambda.Start(handler)
}
