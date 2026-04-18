from __future__ import annotations

from base64 import b64encode

from fastapi.testclient import TestClient

from tax_engine.api.app import app, import_parse_preview
from tax_engine.ingestion.models import ConnectorParseRequest
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_import_connectors_lists_supported_sources() -> None:
    _reset_store()
    client = TestClient(app)
    response = client.get("/api/v1/import/connectors")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    connector_ids = {item["connector_id"] for item in body["data"]["connectors"]}
    assert {"binance", "bitget", "coinbase", "pionex", "blockpit"}.issubset(connector_ids)


def test_parse_preview_normalizes_binance_rows() -> None:
    _reset_store()
    response = import_parse_preview(
        ConnectorParseRequest(
            connector_id="binance",
            rows=[
                {
                    "Date(UTC)": "2026-01-01T12:00:00Z",
                    "Coin": "BTC",
                    "Amount": "0.5",
                    "Price": "40000",
                    "Fee": "0.0005",
                    "Fee Coin": "BTC",
                    "Side": "BUY",
                    "Operation": "Spot Trade",
                    "OrderId": "ord-1",
                }
            ],
        )
    )
    assert response.status == "success"
    row = response.data["normalized_rows"][0]
    assert row["asset"] == "BTC"
    assert row["quantity"] == "0.5"
    assert row["price"] == "40000"
    assert row["source"] == "binance"
    assert row["tx_id"] == "ord-1"
    assert row["side"] == "buy"


def test_upload_preview_parses_csv_and_maps_rows() -> None:
    _reset_store()
    client = TestClient(app)
    content = b"""Date(UTC),Coin,Amount,Price,Fee,Fee Coin,Side,Operation,OrderId
2026-01-01T12:00:00Z,BTC,0.5,40000,0.0005,BTC,BUY,Spot Trade,ord-1
"""
    encoded = b64encode(content).decode("ascii")

    response = client.post(
        "/api/v1/import/upload-preview",
        json={
            "connector_id": "binance",
            "max_rows": 1000,
            "filename": "binance.csv",
            "file_content_base64": encoded,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["count"] == 1
    assert body["data"]["normalized_rows"][0]["asset"] == "BTC"
