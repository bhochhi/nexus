package main

import (
	"context"
	"fmt"
	"log"

	"github.com/aws/aws-lambda-go/lambda"
)

// Request is the input for file_claim.
type Request struct {
	UserID       string `json:"user_id"`
	PolicyID     string `json:"policy_id"`
	ClaimType    string `json:"claim_type"`
	Description  string `json:"description"`
	IncidentDate string `json:"incident_date"`
}

// Response is the output for file_claim.
type Response struct {
	ClaimID string `json:"claim_id"`
	Status  string `json:"status"`
	Message string `json:"message"`
}

func handler(ctx context.Context, req Request) (Response, error) {
	log.Printf("file_claim invoked: user_id=%s policy_id=%s claim_type=%s",
		req.UserID, req.PolicyID, req.ClaimType)

	if req.UserID == "" {
		return Response{}, fmt.Errorf("user_id is required")
	}
	if req.PolicyID == "" {
		return Response{}, fmt.Errorf("policy_id is required")
	}
	if req.ClaimType == "" {
		return Response{}, fmt.Errorf("claim_type is required")
	}
	if req.Description == "" {
		return Response{}, fmt.Errorf("description is required")
	}

	// TODO: replace with claims management system submission
	resp := Response{
		ClaimID: "CLM-PLACEHOLDER",
		Status:  "submitted",
		Message: "Your claim has been submitted and will be reviewed within 3-5 business days.",
	}

	log.Printf("file_claim succeeded: claim_id=%s status=%s", resp.ClaimID, resp.Status)
	return resp, nil
}

func main() {
	lambda.Start(handler)
}
