.PHONY: build test lint deploy clean

SKILLS_DIR := skills
LAMBDA_OUT  := dist

SKILL_DIRS := \
	$(SKILLS_DIR)/banking/get_account_balance \
	$(SKILLS_DIR)/banking/transfer_funds \
	$(SKILLS_DIR)/banking/report_fraud \
	$(SKILLS_DIR)/insurance/check_claim_status \
	$(SKILLS_DIR)/insurance/file_claim \
	$(SKILLS_DIR)/faq/answer_faq

build:
	@echo "Building Lambda functions..."
	@mkdir -p $(LAMBDA_OUT)
	@for dir in $(SKILL_DIRS); do \
		name=$$(basename $$dir); \
		echo "  Building $$name..."; \
		(cd $$dir && GOOS=linux GOARCH=amd64 go build -o ../../../$(LAMBDA_OUT)/$$name .); \
	done
	@echo "Build complete."

test:
	@echo "Running Go unit tests..."
	@for dir in $(SKILL_DIRS); do \
		echo "  Testing $$(basename $$dir)..."; \
		(cd $$dir && go test ./...); \
	done
	@echo "Validating conversation tests..."
	@python3 -c "\
import yaml; \
data = yaml.safe_load(open('tests/conversation_tests.yaml')); \
assert 'tests' in data, 'Missing tests key'; \
print(f'  Found {len(data[\"tests\"])} conversation tests - OK')"
	@echo "Tests complete."

lint:
	@echo "Running linter..."
	@for dir in $(SKILL_DIRS); do \
		echo "  Linting $$(basename $$dir)..."; \
		(cd $$dir && go vet ./...); \
	done
	@echo "Lint complete."

deploy:
	@echo "Deploying Lambda functions..."
	@for skill in $(LAMBDA_OUT)/*; do \
		name=$$(basename $$skill); \
		zip -j $(LAMBDA_OUT)/$$name.zip $$skill; \
		aws lambda update-function-code --function-name nexus-$$name --zip-file fileb://$(LAMBDA_OUT)/$$name.zip; \
	done
	@echo "Deploy complete."

clean:
	rm -rf $(LAMBDA_OUT)
