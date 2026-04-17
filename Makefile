.PHONY: install install-dev lint typecheck test test-cov audit verify ci

install:
	python3 -m pip install -r requirements.txt

install-dev:
	python3 -m pip install -r requirements-dev.txt

lint:
	ruff check . --no-cache

typecheck:
	mypy src/ --cache-dir=/tmp/steuerreport_mypy_cache

test:
	pytest -p no:cacheprovider

test-cov:
	pytest -p no:cacheprovider --cov=src/tax_engine --cov-report=term-missing

audit:
	pip-audit

verify:
	python3 scripts/verify_integrity.py --all-years

ci: lint typecheck test-cov verify
