.PHONY: setup test lint format typecheck run clean

setup:
	python3 -m venv venv
	venv/bin/pip install -e ".[dev]"

test:
	venv/bin/pytest tests/ -v --tb=short

lint:
	venv/bin/ruff check src/ tests/

format:
	venv/bin/ruff format src/ tests/

typecheck:
	venv/bin/mypy src/nexus/

run:
	venv/bin/python -m nexus.app

clean:
	rm -rf venv/ dist/ *.egg-info __pycache__ .pytest_cache .mypy_cache .ruff_cache
