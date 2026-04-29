VENV        := .venv
PYTHON      := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
MEMBER_ID   ?= M12345
MSR_QUEUE   ?= banking
MSR_NAME    ?= Alice

.DEFAULT_GOAL := help

# ─── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo ""
	@echo "  Nexus — Multi-Agent Financial AI Platform"
	@echo ""
	@echo "  Usage: make <target>"
	@echo ""
	@echo "  Setup"
	@echo "    venv          Create the virtual environment (.venv)"
	@echo "    install       Install dependencies into the virtual environment"
	@echo "    setup         Create venv + install dependencies (run once)"
	@echo ""
	@echo "  Run"
	@echo "    run           Run the member CLI (MEMBER_ID=M12345)"
	@echo "    run-debug     Run the member CLI with debug panel enabled"
	@echo "    contact-center  Start the contact center WebSocket server"
	@echo "    msr-cli       Start the MSR console (MSR_QUEUE=banking MSR_NAME=Alice)"
	@echo ""
	@echo "  Dev"
	@echo "    test          Run the test suite"
	@echo "    clean         Remove the virtual environment and caches"
	@echo ""

# ─── Setup ────────────────────────────────────────────────────────────────────

.PHONY: venv
venv:
	@echo "→ Creating virtual environment in $(VENV)/"
	python3 -m venv $(VENV)
	@echo "✓ Virtual environment created. Activate with: source $(VENV)/bin/activate"

.PHONY: install
install: venv
	@echo "→ Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✓ Dependencies installed."

.PHONY: setup
setup: install
	@echo "✓ Setup complete. Run 'make run' to start."

# ─── Run ──────────────────────────────────────────────────────────────────────

.PHONY: run
run:
	@echo "→ Starting Nexus (member: $(MEMBER_ID))..."
	$(PYTHON) app.py --member-id $(MEMBER_ID)

.PHONY: run-debug
run-debug:
	@echo "→ Starting Nexus in debug mode (member: $(MEMBER_ID))..."
	$(PYTHON) app.py --member-id $(MEMBER_ID) --debug

.PHONY: contact-center
contact-center:
	@echo "→ Starting contact center WebSocket server..."
	$(PYTHON) scripts/run_contact_center.py

.PHONY: msr-cli
msr-cli:
	@echo "→ Starting MSR console (queue: $(MSR_QUEUE), name: $(MSR_NAME))..."
	$(PYTHON) contact_center/msr_console.py --queue $(MSR_QUEUE) --name "$(MSR_NAME)"

# ─── Dev ──────────────────────────────────────────────────────────────────────

.PHONY: test
test:
	@echo "→ Running tests..."
	$(PYTHON) -m pytest tests/ -v

.PHONY: clean
clean:
	@echo "→ Removing virtual environment and caches..."
	rm -rf $(VENV) .pytest_cache __pycache__ **/__pycache__
	@echo "✓ Clean complete."
