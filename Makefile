.PHONY: format lint dev-lint

GIT_ROOT ?= $(shell git rev-parse --show-toplevel)

format:
	poetry run black .
	poetry run isort .

dev-lint: format
	poetry run mypy .
	poetry run ruff check . --fix
	poetry run pylint theoriq/. --max-line-length 120 --disable=R,C,I  --fail-under=9

lint:
	poetry run black . --check
	poetry run mypy . --disable-error-code=attr-defined
	poetry run ruff check .
	poetry run pylint theoriq/. --max-line-length 120 --disable=R,C,I,E0401,W1203,W0107 --fail-under=9
	poetry run isort . --check-only

test:
	poetry run pytest tests

ci-test:
	poetry run pytest tests/unit
