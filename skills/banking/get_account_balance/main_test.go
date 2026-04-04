package main

import (
	"context"
	"testing"
)

func TestHandler_Success(t *testing.T) {
	req := Request{
		UserID:    "user-123",
		AccountID: "acct-456",
	}
	resp, err := handler(context.Background(), req)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
	if resp.AccountID != req.AccountID {
		t.Errorf("expected account_id %s, got %s", req.AccountID, resp.AccountID)
	}
	if resp.Currency == "" {
		t.Error("expected non-empty currency")
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
