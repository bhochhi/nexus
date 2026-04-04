package main

import (
	"context"
	"testing"
)

func TestHandler_Success(t *testing.T) {
	req := Request{
		UserID:      "user-123",
		PolicyID:    "policy-456",
		ClaimType:   "auto",
		Description: "Rear-end collision on Highway 101",
	}
	resp, err := handler(context.Background(), req)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
	if resp.ClaimID == "" {
		t.Error("expected non-empty claim_id")
	}
	if resp.Status == "" {
		t.Error("expected non-empty status")
	}
}

func TestHandler_MissingPolicyID(t *testing.T) {
	req := Request{UserID: "user-123", ClaimType: "auto", Description: "accident"}
	_, err := handler(context.Background(), req)
	if err == nil {
		t.Fatal("expected error for missing policy_id")
	}
}

func TestHandler_MissingDescription(t *testing.T) {
	req := Request{UserID: "user-123", PolicyID: "policy-456", ClaimType: "auto"}
	_, err := handler(context.Background(), req)
	if err == nil {
		t.Fatal("expected error for missing description")
	}
}
