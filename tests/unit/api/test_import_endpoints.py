from fastapi.testclient import TestClient

from tax_engine.api import app, import_router


def _reset_import_state() -> None:
    import_router._PERSISTED_SOURCE_FILES.clear()
    import_router._PERSISTED_RAW_EVENTS.clear()


def test_detect_format_endpoint_returns_detections() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/import/detect-format",
        json={
            "rows": [
                {
                    "Date(UTC)": "2026-01-01 12:00:00",
                    "Pair": "BTCUSDT",
                    "Side": "BUY",
                    "Price": "1,234.56",
                    "Executed": "0.1",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["row_count"] == 1
    assert "/api/v1/import/detect-format" in client.get("/openapi.json").json()["paths"]


def test_normalize_preview_endpoint_partial_on_ambiguous_value() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/import/normalize-preview",
        json={
            "rows": [{"asset": "BTC", "amount": "1,234"}],
            "profile": {"profile_id": "btc", "profile_version": "1.0.0"},
            "numeric_fields": ["amount"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "partial"
    assert len(payload["warnings"]) == 1


def test_confirm_endpoint_generates_deterministic_duplicate_event_ids() -> None:
    _reset_import_state()
    client = TestClient(app)
    body = {
        "source_files": [{"source_name": "binance", "file_name": "b.csv", "file_hash": "abc"}],
        "raw_events": [
            {
                "Date(UTC)": "2026-01-01 12:00:00",
                "Pair": "BTCUSDT",
                "Side": "BUY",
                "Price": "1,000.00",
                "Executed": "0.1",
                "OrderId": "42",
            }
        ],
        "profile": {"profile_id": "binance_default", "profile_version": "1.0.0"},
    }

    first = client.post("/api/v1/import/confirm", json=body)
    second = client.post("/api/v1/import/confirm", json=body)

    assert first.status_code == 200
    assert second.status_code == 200

    first_payload = first.json()
    second_payload = second.json()

    first_event_id = first_payload["data"]["persisted_raw_events"][0]["unique_event_id"]
    assert second_payload["data"]["duplicate_event_ids"] == [first_event_id]
    assert second_payload["status"] == "partial"
