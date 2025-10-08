.PHONY: format lint typecheck test run sync coverage

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

coverage: test
	mkdir -p docs/assets
	uv run coverage-badge -o docs/assets/coverage.svg -f
	@echo "Coverage badge written to docs/assets/coverage.svg"

run:
        uv run python -m coman.modules.main api
