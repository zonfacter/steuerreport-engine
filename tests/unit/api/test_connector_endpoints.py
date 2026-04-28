from __future__ import annotations

from base64 import b64encode
from io import BytesIO

import pandas as pd

from tax_engine.api.app import import_connectors, import_parse_preview, import_upload_preview
from tax_engine.ingestion.models import ConnectorParseRequest, UploadPreviewRequest
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_import_connectors_lists_supported_sources() -> None:
    _reset_store()
    response = import_connectors()
    assert response.status == "success"
    connector_ids = {item["connector_id"] for item in response.data["connectors"]}
    assert {"binance", "bitget", "coinbase", "pionex", "blockpit", "heliumgeek"}.issubset(connector_ids)


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


def test_parse_preview_binance_convert_row_is_split_into_out_and_in() -> None:
    _reset_store()
    response = import_parse_preview(
        ConnectorParseRequest(
            connector_id="binance",
            rows=[
                {
                    "Date(UTC)": "2026-01-01T12:00:00Z",
                    "Operation": "Convert",
                    "From Coin": "USDT",
                    "From Amount": "100",
                    "To Coin": "BTC",
                    "To Amount": "0.0025",
                    "Transaction ID": "conv-1",
                }
            ],
        )
    )
    assert response.status == "success"
    assert response.data["count"] == 2
    sides = {item["side"] for item in response.data["normalized_rows"]}
    tx_ids = {item["tx_id"] for item in response.data["normalized_rows"]}
    assert sides == {"out", "in"}
    assert tx_ids == {"conv-1:out", "conv-1:in"}


def test_upload_preview_parses_csv_and_maps_rows() -> None:
    _reset_store()
    content = b"""Date(UTC),Coin,Amount,Price,Fee,Fee Coin,Side,Operation,OrderId
2026-01-01T12:00:00Z,BTC,0.5,40000,0.0005,BTC,BUY,Spot Trade,ord-1
"""
    encoded = b64encode(content).decode("ascii")

    response = import_upload_preview(
        UploadPreviewRequest(
            connector_id="binance",
            max_rows=1000,
            filename="binance.csv",
            file_content_base64=encoded,
        )
    )
    assert response.status == "success"
    assert response.data["count"] == 1
    assert response.data["normalized_rows"][0]["asset"] == "BTC"


def test_upload_preview_parses_semicolon_csv() -> None:
    _reset_store()
    content = b"""Date(UTC);Coin;Amount;Price;Fee;Fee Coin;Side;Operation;OrderId
2026-01-01T12:00:00Z;BTC;0.5;40000;0.0005;BTC;BUY;Spot Trade;ord-1
"""
    encoded = b64encode(content).decode("ascii")

    response = import_upload_preview(
        UploadPreviewRequest(
            connector_id="binance",
            max_rows=1000,
            filename="binance_semicolon.csv",
            file_content_base64=encoded,
        )
    )
    assert response.status == "success"
    assert response.data["count"] == 1
    assert response.data["normalized_rows"][0]["tx_id"] == "ord-1"


def test_parse_preview_blockpit_splits_row_in_out_fee() -> None:
    _reset_store()
    response = import_parse_preview(
        ConnectorParseRequest(
            connector_id="blockpit",
            rows=[
                {
                    "Date (UTC)": "30.12.2025 23:59:59",
                    "Label": "Swap",
                    "Outgoing Asset": "SOL",
                    "Outgoing Amount": "1.5",
                    "Incoming Asset": "JUP",
                    "Incoming Amount": "100",
                    "Fee Asset (optional)": "SOL",
                    "Fee Amount (optional)": "0.01",
                    "Trx. ID (optional)": "bp-1",
                }
            ],
        )
    )
    assert response.status == "success"
    assert response.data["count"] == 3
    event_types = {item["event_type"] for item in response.data["normalized_rows"]}
    assert "swap" in event_types
    assert "fee" in event_types


def test_parse_preview_heliumgeek_maps_monthly_rewards() -> None:
    _reset_store()
    response = import_parse_preview(
        ConnectorParseRequest(
            connector_id="heliumgeek",
            rows=[
                {
                    "Gateway Address": "gw-1",
                    "Name": "Hotspot 1",
                    "Tag": "My Hotspots",
                    "Period Start (UTC)": "01.05.23",
                    "IOT Tokens": "10191.13605",
                    "IOT Token": "IOT",
                    "MOBILE Tokens": "3.5",
                    "MOBILE Token": "MOBILE",
                }
            ],
        )
    )
    assert response.status == "success"
    assert response.data["count"] == 2
    assets = {item["asset"] for item in response.data["normalized_rows"]}
    quantities = {item["asset"]: item["quantity"] for item in response.data["normalized_rows"]}
    assert assets == {"IOT", "MOBILE"}
    assert quantities["IOT"] == "10191.13605"
    assert quantities["MOBILE"] == "3.5"


def test_upload_preview_parses_binance_xlsx_with_banner_rows() -> None:
    _reset_store()
    rows = [
        ["", "", "", "", "", "", "", "", "", "", "", "www.binance.com"],
        ["", "", "Deposit History", "", "", "", "", "", "", "", "", ""],
        ["", "", "Time", "Coin", "", "Network", "", "Amount", "", "Address", "TXID", "Status"],
        [
            "",
            "",
            "25-06-15 09:47:02",
            "SOL",
            "",
            "SOL",
            "",
            "7.0700475",
            "",
            "addr1",
            "tx1",
            "Completed",
        ],
    ]
    frame = pd.DataFrame(rows)
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, header=False)
    encoded = b64encode(bio.getvalue()).decode("ascii")

    response = import_upload_preview(
        UploadPreviewRequest(
            connector_id="binance",
            max_rows=1000,
            filename="binance_deposit.xlsx",
            file_content_base64=encoded,
        )
    )
    assert response.status == "success"
    assert response.data["count"] == 1
    row = response.data["normalized_rows"][0]
    assert row["asset"] == "SOL"
    assert row["tx_id"] == "tx1"
