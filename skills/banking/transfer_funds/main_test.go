package main

import (
	"context"
	"testing"
)

func TestHandler_Success(t *testing.T) {
	req := Request{
		UserID:        "user-123",
		FromAccountID: "acct-100",
		ToAccountID:   "acct-200",
		Amount:        150.00,
	}
	resp, err := handler(context.Background(), req)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
	if resp.TransactionID == "" {
		t.Error("expected non-empty transaction_id")
	}
	if resp.Status == "" {
		t.Error("expected non-empty status")
	}
	if resp.Currency == "" {
		t.Error("expected non-empty currency")
	}
}

func TestHandler_MissingUserID(t *testing.T) {
	req := Request{FromAccountID: "acct-100", ToAccountID: "acct-200", Amount: 10}
	_, err := handler(context.Background(), req)
	if err == nil {
		t.Fatal("expected error for missing user_id")
	}
}

func TestHandler_ZeroAmount(t *testing.T) {
	req := Request{UserID: "user-123", FromAccountID: "acct-100", ToAccountID: "acct-200", Amount: 0}
	_, err := handler(context.Background(), req)
	if err == nil {
		t.Fatal("expected error for zero amount")
	}
}

func TestHandler_NegativeAmount(t *testing.T) {
	req := Request{UserID: "user-123", FromAccountID: "acct-100", ToAccountID: "acct-200", Amount: -50}
	_, err := handler(context.Background(), req)
	if err == nil {
		t.Fatal("expected error for negative amount")
	}
}
