.PHONY: format lint dev-lint

GIT_ROOT ?= $(shell git rev-parse --show-toplevel)

format:
	black .

lint:
	black . --check
	mypy .
	ruff check .
	pylint ./ --max-line-length 120 --disable=R,C,I,W1203,W0107 --fail-under=9

test:
	pytest tests