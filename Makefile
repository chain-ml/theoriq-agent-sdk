.PHONY: format lint dev-lint

GIT_ROOT ?= $(shell git rev-parse --show-toplevel)

format:
	black .

dev-lint:
	black .
	mypy .
	ruff check . --fix
	isort .
	pylint theoriq/. --max-line-length 120 --disable=R,C,I  --fail-under=9

lint:
	black . --check
	mypy . --disable-error-code=attr-defined
	ruff check .
	pylint theoriq/. --max-line-length 120 --disable=R,C,I,W1203,W0107 --fail-under=9
	isort . --check-only

test:
	pytest tests