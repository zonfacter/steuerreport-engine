.PHONY: install install-dev lint typecheck test test-cov audit verify smoke ci

install:
	python3 -m pip install -r requirements.txt

install-dev:
	python3 -m pip install -r requirements-dev.txt

lint:
	ruff check . --no-cache

typecheck:
	mypy src/ --cache-dir=/tmp/steuerreport_mypy_cache

test:
	STEUERREPORT_ENV=testing STEUERREPORT_DB_PATH=/tmp/steuerreport/steuerreport_test.db pytest -p no:cacheprovider

test-cov:
	rm -f .coverage .coverage.* 2>/dev/null || true
	STEUERREPORT_ENV=testing STEUERREPORT_DB_PATH=/tmp/steuerreport/steuerreport_test.db COVERAGE_FILE=/tmp/steuerreport-coverage python3 -m pytest -p no:cacheprovider --cov=src/tax_engine --cov-report=term-missing

audit:
	pip-audit

verify:
	python3 scripts/verify_integrity.py --all-years

smoke:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/smoke_test.py

ci: lint typecheck test-cov verify
