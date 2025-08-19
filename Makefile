.PHONY: install dev test lint format clean api sdk

install:
	poetry install

dev:
	poetry install --with dev

test:
	poetry run pytest

lint:
	poetry run ruff check .

format:
	poetry run ruff format .

clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/

api:
	poetry run uvicorn ziz.api.main:app --reload --host 0.0.0.0 --port 8000

sdk-example:
	poetry run python -c "from ziz.sdk import ZizClient; print('SDK ready for use')"

setup: dev
	poetry run pre-commit install