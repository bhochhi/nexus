package main

import (
	"context"
	"testing"
)

func TestHandler_Success(t *testing.T) {
	req := Request{
		UserID:        "user-123",
		AccountID:     "acct-456",
		TransactionID: "txn-789",
		Description:   "Unrecognized charge at store",
	}
	resp, err := handler(context.Background(), req)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
	if resp.CaseID == "" {
		t.Error("expected non-empty case_id")
	}
	if resp.Status == "" {
		t.Error("expected non-empty status")
	}
}

func TestHandler_MissingUserID(t *testing.T) {
	req := Request{AccountID: "acct-456"}
	_, err := handler(context.Background(), req)
	if err == nil {
		t.Fatal("expected error for missing user_id")
	}
}

func TestHandler_MissingAccountID(t *testing.T) {
	req := Request{UserID: "user-123"}
	_, err := handler(context.Background(), req)
	if err == nil {
		t.Fatal("expected error for missing account_id")
	}
}
