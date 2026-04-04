package main

import (
	"context"
	"fmt"
	"log"

	"github.com/aws/aws-lambda-go/lambda"
)

// Request is the input for answer_faq.
type Request struct {
	UserID   string `json:"user_id"`
	Question string `json:"question"`
	Intent   string `json:"intent"`
}

// Response is the output for answer_faq.
type Response struct {
	Answer  string `json:"answer"`
	Source  string `json:"source"`
	Matched bool   `json:"matched"`
}

func handler(ctx context.Context, req Request) (Response, error) {
	log.Printf("answer_faq invoked: user_id=%s intent=%s", req.UserID, req.Intent)

	if req.Question == "" && req.Intent == "" {
		return Response{}, fmt.Errorf("question or intent is required")
	}

	// TODO: replace with knowledge base / FAQ lookup
	resp := Response{
		Answer:  "I'm sorry, I don't have a specific answer for that. Please contact support for assistance.",
		Source:  "default",
		Matched: false,
	}

	log.Printf("answer_faq completed: intent=%s matched=%v", req.Intent, resp.Matched)
	return resp, nil
}

func main() {
	lambda.Start(handler)
}
