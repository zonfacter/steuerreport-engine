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
    assert {
        "binance",
        "bitget",
        "coinbase",
        "pionex",
        "blockpit",
        "heliumgeek",
        "heliumtracker",
        "helium_legacy_cointracking",
        "helium_legacy_raw",
    }.issubset(
        connector_ids
    )


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


def test_parse_preview_binance_trade_history_splits_market_row() -> None:
    _reset_store()
    response = import_parse_preview(
        ConnectorParseRequest(
            connector_id="binance",
            rows=[
                {
                    "Date(UTC)": "2021-06-22 08:57:27",
                    "Market": "HNTEUR",
                    "Type": "BUY",
                    "Price": "10.00",
                    "Amount": "2.5",
                    "Total": "25.00",
                    "Fee": "0.01",
                    "Fee Coin": "HNT",
                    "Order ID": "trade-1",
                }
            ],
        )
    )
    assert response.status == "success"
    rows = response.data["normalized_rows"]
    assert response.data["count"] == 2
    assert {(row["asset"], row["side"], row["quantity"]) for row in rows} == {
        ("EUR", "out", "25.00"),
        ("HNT", "in", "2.5"),
    }
    assert next(row for row in rows if row["asset"] == "HNT")["fee"] == "0.01"


def test_parse_preview_binance_deposit_utc_plus_two_is_shifted_to_utc() -> None:
    _reset_store()
    response = import_parse_preview(
        ConnectorParseRequest(
            connector_id="binance",
            rows=[
                {
                    "__source_name": "BINANCE - EINZAHLUNG - Export Deposit History.xlsx",
                    "Date(UTC+2)": "2021-07-01 10:30:00",
                    "Coin": "HNT",
                    "Amount": "10",
                    "Order ID": "dep-1",
                }
            ],
        )
    )
    assert response.status == "success"
    row = response.data["normalized_rows"][0]
    assert row["timestamp_utc"] == "2021-07-01T08:30:00+00:00"
    assert row["side"] == "in"
    assert row["event_type"] == "deposit"


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


def test_parse_preview_helium_legacy_cointracking_maps_rewards_transfers_and_fees() -> None:
    _reset_store()
    legacy_wallet = "133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j"
    counterparty = "137tZvaxM4zjvfU9GcDzzmAsdMjkESCULx9XaVrGWKj989izPue"
    response = import_parse_preview(
        ConnectorParseRequest(
            connector_id="helium_legacy_cointracking",
            rows=[
                {
                    "type": "Mining",
                    "buyAmount": "0.5",
                    "buyCurrency": "HNT2",
                    "exchange": "Helium Wallet History",
                    "comment": "",
                    "date": "2021-06-01 12:00:00",
                    "txId": f"reward-tx+{legacy_wallet}",
                    "buyValueUSD": "7.50",
                },
                {
                    "type": "Withdrawal",
                    "sellAmount": "2.25",
                    "sellCurrency": "HNT2",
                    "feeAmount": "0.00035",
                    "feeCurrency": "HNT2",
                    "exchange": "Helium Wallet History",
                    "comment": f"payment_v2 to {counterparty}",
                    "date": "2022-01-05 08:30:00",
                    "txId": f"withdraw-tx+{legacy_wallet}",
                    "sellValueUSD": "72.00",
                },
                {
                    "type": "Deposit",
                    "buyAmount": "1.25",
                    "buyCurrency": "HNT2",
                    "exchange": "Helium Wallet History",
                    "comment": f"payment_v1 from {counterparty}",
                    "date": "2022-02-05 08:30:00",
                    "txId": f"deposit-tx+{legacy_wallet}",
                    "buyValueUSD": "31.00",
                },
                {
                    "type": "Other Fee",
                    "sellAmount": "0.00001",
                    "sellCurrency": "HNT2",
                    "exchange": "Helium Wallet History",
                    "comment": "fee",
                    "date": "2022-03-05 08:30:00",
                    "txId": f"fee-tx+{legacy_wallet}",
                    "sellValueUSD": "0.01",
                },
            ],
        )
    )

    assert response.status == "success"
    assert response.data["count"] == 4
    rows = response.data["normalized_rows"]
    mining, withdrawal, deposit, fee = rows

    assert mining["event_type"] == "mining_reward"
    assert mining["asset"] == "HNT"
    assert mining["quantity"] == "0.5"
    assert mining["value_usd"] == "7.50"
    assert mining["wallet_address"] == legacy_wallet

    assert withdrawal["event_type"] == "legacy_transfer"
    assert withdrawal["side"] == "out"
    assert withdrawal["from_wallet"] == legacy_wallet
    assert withdrawal["to_wallet"] == counterparty
    assert withdrawal["fee"] == "0.00035"
    assert withdrawal["fee_asset"] == "HNT"

    assert deposit["event_type"] == "legacy_transfer"
    assert deposit["side"] == "in"
    assert deposit["from_wallet"] == counterparty
    assert deposit["to_wallet"] == legacy_wallet

    assert fee["event_type"] == "legacy_network_fee"
    assert fee["side"] == "out"
    assert fee["asset"] == "HNT"


def test_parse_preview_heliumtracker_maps_rewards() -> None:
    _reset_store()
    response = import_parse_preview(
        ConnectorParseRequest(
            connector_id="heliumtracker",
            rows=[
                {
                    "Hotspot Name": "calm-hawk",
                    "Date": "2022-03-01",
                    "Mining Rewards HNT": "0.25",
                    "Mining Rewards IOT": "10.5",
                    "Mining Rewards MOBILE": "",
                    "Commissions HNT": "0",
                    "Commissions IOT": "0",
                    "Commissions MOBILE": "0",
                    "HNT (USD)": "6.50",
                    "HNT (EUR)": "5.90",
                }
            ],
        )
    )
    assert response.status == "success"
    rows = response.data["normalized_rows"]
    assert response.data["count"] == 2
    assert {(row["asset"], row["event_type"], row["side"]) for row in rows} == {
        ("HNT", "mining_reward", "in"),
        ("IOT", "mining_reward", "in"),
    }
    assert next(row for row in rows if row["asset"] == "HNT")["price_eur"] == "5.90"


def test_parse_preview_helium_legacy_raw_maps_wallet_direction() -> None:
    _reset_store()
    wallet = "14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA"
    counterparty = "133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j"
    response = import_parse_preview(
        ConnectorParseRequest(
            connector_id="helium_legacy_raw",
            rows=[
                {
                    "__source_name": f"helium-Staking Wallet {wallet}-all-raw.csv",
                    "date": "2021-08-01T12:00:00Z",
                    "transaction_hash": "raw-tx-1",
                    "hnt_amount": "5",
                    "hnt_fee": "0.00035",
                    "usd_amount": "75",
                    "payer": counterparty,
                    "payee": wallet,
                }
            ],
        )
    )
    assert response.status == "success"
    row = response.data["normalized_rows"][0]
    assert row["wallet_address"] == wallet
    assert row["from_wallet"] == counterparty
    assert row["to_wallet"] == wallet
    assert row["side"] == "in"
    assert row["event_type"] == "legacy_transfer"


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
