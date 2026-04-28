from __future__ import annotations

import os
import sys
from pathlib import Path

from tax_engine.db import SQLiteImportStore

_DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "steuerreport" / "steuerreport.db"
_TEST_DB_PATH = Path("/tmp/steuerreport/steuerreport_test.db")


def _resolve_db_path() -> Path:
    configured = os.getenv("STEUERREPORT_DB_PATH")
    if configured:
        return Path(configured)
    if os.getenv("STEUERREPORT_ENV") == "testing" or "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST"):
        return _TEST_DB_PATH
    return _DEFAULT_DB_PATH


STORE = SQLiteImportStore(db_path=_resolve_db_path())
