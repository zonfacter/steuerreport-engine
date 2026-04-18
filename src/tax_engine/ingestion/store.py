from __future__ import annotations

import os
from pathlib import Path

from tax_engine.db import SQLiteImportStore


def _resolve_db_path() -> Path:
    configured = os.getenv("STEUERREPORT_DB_PATH")
    if configured:
        return Path(configured)
    return Path("/tmp/steuerreport/steuerreport.db")


STORE = SQLiteImportStore(db_path=_resolve_db_path())
