package main

import (
	"context"
	"testing"
)

func TestHandler_WithIntent(t *testing.T) {
	req := Request{
		UserID: "user-123",
		Intent: "hours_of_operation",
	}
	resp, err := handler(context.Background(), req)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
	if resp.Answer == "" {
		t.Error("expected non-empty answer")
	}
}

func TestHandler_WithQuestion(t *testing.T) {
	req := Request{
		UserID:   "user-123",
		Question: "What are your business hours?",
	}
	resp, err := handler(context.Background(), req)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
	if resp.Answer == "" {
		t.Error("expected non-empty answer")
	}
}

func TestHandler_MissingInput(t *testing.T) {
	req := Request{UserID: "user-123"}
	_, err := handler(context.Background(), req)
	if err == nil {
		t.Fatal("expected error when both question and intent are empty")
	}
}
