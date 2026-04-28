from __future__ import annotations

from tax_engine.api.app import (
    import_confirm,
    import_detect_format,
    import_jobs,
    import_normalize_preview,
    import_sources_summary,
)
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


def test_confirm_endpoint_deduplicates_across_different_source_names() -> None:
    _reset_store()
    rows = [
        {
            "timestamp_utc": "2026-01-01T12:00:00+00:00",
            "asset": "BTC",
            "quantity": "0.1",
            "event_type": "trade",
            "tx_id": "same-tx-1",
            "source": "binance_api",
        }
    ]
    first = import_confirm(ConfirmImportRequest(source_name="binance_part_a.csv", rows=rows))
    second = import_confirm(ConfirmImportRequest(source_name="binance_part_b.csv", rows=rows))

    assert first.data["inserted_events"] == 1
    assert second.data["inserted_events"] == 0
    assert second.data["duplicate_events"] == 1


def test_sources_summary_returns_imported_source_rows() -> None:
    _reset_store()
    payload = ConfirmImportRequest(
        source_name="coinbase.csv",
        rows=[
            {"timestamp": "2026-01-01T12:00:00Z", "amount": "1.0", "asset": "ETH"},
            {"timestamp": "2026-01-02T12:00:00Z", "amount": "2.0", "asset": "BTC"},
        ],
    )
    import_confirm(payload)
    response = import_sources_summary(limit=10)
    assert response.status == "success"
    assert response.data["count"] >= 1
    row = response.data["rows"][0]
    assert row["source_name"] == "coinbase.csv"
    assert int(row["declared_row_count"]) == 2


def test_import_jobs_returns_persisted_import_headers_with_filters() -> None:
    _reset_store()
    payload = ConfirmImportRequest(
        source_name="binance_api_full_2026.csv",
        rows=[
            {
                "timestamp_utc": "2026-01-01T12:00:00+00:00",
                "asset": "BTC",
                "quantity": "0.1",
                "event_type": "trade",
                "tx_id": "import-job-1",
                "source": "binance_api",
            }
        ],
    )
    import_confirm(payload)

    response = import_jobs(status="completed", integration="binance", limit=10)

    assert response.status == "success"
    assert response.data["count"] == 1
    row = response.data["rows"][0]
    assert row["connector"] == "binance"
    assert row["status"] == "completed"
    assert row["rows"] == 1
    assert row["inserted_events"] == 1
    assert row["duplicates"] == 0
