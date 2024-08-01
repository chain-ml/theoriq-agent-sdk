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

test:
	pytest tests