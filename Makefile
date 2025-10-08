.PHONY: format lint typecheck test run sync

sync:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run mypy .

test:
	uv run pytest

run:
	uv run python -m coman.modules.main api
