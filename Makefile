PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

.PHONY: venv install test lint format

venv:
	python -m venv .venv

install: venv
	$(PIP) install -U pip
	$(PIP) install -e ".[dev,test]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m bandit -r src -ll
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m black .
