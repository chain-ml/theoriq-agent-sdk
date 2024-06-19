.PHONY: format lint dev-lint

GIT_ROOT ?= $(shell git rev-parse --show-toplevel)

format:
	black .

lint:
	black . --check
	mypy . --disable-error-code=attr-defined
	ruff check .

test:
	pytest tests