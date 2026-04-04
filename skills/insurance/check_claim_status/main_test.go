package main

import (
	"context"
	"testing"
)

func TestHandler_Success(t *testing.T) {
	req := Request{
		UserID:  "user-123",
		ClaimID: "claim-456",
	}
	resp, err := handler(context.Background(), req)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
	if resp.ClaimID != req.ClaimID {
		t.Errorf("expected claim_id %s, got %s", req.ClaimID, resp.ClaimID)
	}
	if resp.Status == "" {
		t.Error("expected non-empty status")
	}
}

func TestHandler_MissingUserID(t *testing.T) {
	req := Request{ClaimID: "claim-456"}
	_, err := handler(context.Background(), req)
	if err == nil {
		t.Fatal("expected error for missing user_id")
	}
}

func TestHandler_MissingClaimID(t *testing.T) {
	req := Request{UserID: "user-123"}
	_, err := handler(context.Background(), req)
	if err == nil {
		t.Fatal("expected error for missing claim_id")
	}
}
