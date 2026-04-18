from __future__ import annotations

from tax_engine.api.app import import_confirm, import_detect_format, import_normalize_preview
from tax_engine.ingestion.models import (
    ConfirmImportRequest,
    DetectFormatRequest,
    NormalizePreviewRequest,
)
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_detect_format_endpoint_returns_numeric_and_datetime_fields() -> None:
    _reset_store()
    response = import_detect_format(
        DetectFormatRequest(
            source_name="binance.csv",
            rows=[{"timestamp": "2026-01-01T12:00:00Z", "amount": "1,234.50", "asset": "BTC"}],
        )
    )
    assert response.status == "success"
    assert "amount" in response.data["numeric_fields"]
    assert "timestamp" in response.data["datetime_fields"]


def test_normalize_preview_endpoint_converts_decimal_and_datetime() -> None:
    _reset_store()
    response = import_normalize_preview(
        NormalizePreviewRequest(
            source_name="solana.csv",
            rows=[{"timestamp": "2026-01-01T12:00:00Z", "amount": "1000000000"}],
            numeric_fields=["amount"],
            datetime_fields=["timestamp"],
            subunit_fields={"amount": "lamports"},
        )
    )
    assert response.status == "success"
    normalized_row = response.data["normalized_rows"][0]
    assert normalized_row["amount"] == "1.000000000"
    assert normalized_row["timestamp"].endswith("+00:00")


def test_confirm_endpoint_deduplicates_events_and_writes_audit() -> None:
    _reset_store()
    payload = ConfirmImportRequest(
        source_name="bitget.csv",
        rows=[{"timestamp": "2026-01-01T12:00:00Z", "amount": "1.0", "asset": "ETH"}],
    )
    first = import_confirm(payload)
    second = import_confirm(payload)

    assert first.data["inserted_events"] == 1
    assert second.data["inserted_events"] == 0
    assert second.data["duplicate_events"] == 1
    assert STORE.count_audit_entries() == 2
