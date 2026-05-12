from __future__ import annotations

import os

import pytest

from tax_engine.db import SQLiteImportStore


def test_reset_for_tests_requires_testing_environment(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("STEUERREPORT_ENV", raising=False)
    store = SQLiteImportStore(tmp_path / "safety.db")

    with pytest.raises(PermissionError):
        store.reset_for_tests()


def test_reset_for_tests_allowed_in_testing_environment(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("STEUERREPORT_ENV", "testing")
    store = SQLiteImportStore(tmp_path / "test.db")

    store.reset_for_tests()

    assert os.getenv("STEUERREPORT_ENV") == "testing"
