from __future__ import annotations

import json

from tax_engine.db import SQLiteImportStore


def test_solscan_transaction_cache_roundtrip(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STEUERREPORT_ENV", "testing")
    store = SQLiteImportStore(tmp_path / "solscan.db")
    store.reset_for_tests()

    store.upsert_solscan_transaction(
        signature="sig-1",
        wallet_address="wallet-1",
        endpoint="https://pro-api.solscan.io/v2.0/transaction/detail",
        http_status=200,
        success=True,
        block_time_utc="2024-12-04T18:30:59+00:00",
        slot=123,
        raw_json=json.dumps({"success": True, "data": {"slot": 123}}),
        summary_json=json.dumps({"signature": "sig-1", "success": True}),
    )

    row = store.get_solscan_transaction("sig-1")

    assert row is not None
    assert row["signature"] == "sig-1"
    assert row["wallet_address"] == "wallet-1"
    assert row["success"] is True
    assert row["raw"]["data"]["slot"] == 123
    assert store.list_solscan_transactions(limit=10)[0]["signature"] == "sig-1"


def test_list_distinct_transaction_ids_filters_source_and_wallet(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STEUERREPORT_ENV", "testing")
    store = SQLiteImportStore(tmp_path / "solscan-txids.db")
    store.reset_for_tests()
    store.upsert_source_file("src", "test", "hash", 4)

    payloads = [
        ("evt-1", {"source": "solana_rpc", "wallet_address": "wallet-1", "tx_id": "sig-1"}),
        ("evt-2", {"source": "solana_rpc", "wallet_address": "wallet-1", "signature": "sig-2"}),
        ("evt-3", {"source": "solana_rpc", "wallet_address": "wallet-2", "transaction_hash": "sig-3"}),
        ("evt-4", {"source": "binance_api", "wallet_address": "wallet-1", "tx_id": "ignored"}),
    ]
    for row_index, (event_id, payload) in enumerate(payloads, start=1):
        store.insert_raw_event(event_id, "src", row_index, json.dumps(payload))

    signatures = store.list_distinct_transaction_ids(
        source="solana_rpc",
        wallet_address="wallet-1",
        limit=10,
    )

    assert signatures == ["sig-1", "sig-2"]


def test_solscan_account_discovery_cache_counts(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STEUERREPORT_ENV", "testing")
    store = SQLiteImportStore(tmp_path / "solscan-account.db")
    store.reset_for_tests()

    store.upsert_solscan_account_transaction(
        wallet_address="wallet-1",
        signature="sig-1",
        slot=123,
        block_time_utc="2026-05-07T14:54:00+00:00",
        status="Success",
        raw_json=json.dumps({"tx_hash": "sig-1"}),
    )
    store.upsert_solscan_account_transfer(
        transfer_id="transfer-1",
        wallet_address="wallet-1",
        signature="sig-1",
        block_time_utc="2026-05-07T14:54:00+00:00",
        flow="in",
        activity_type="ACTIVITY_SPL_TRANSFER",
        token_address="hntyVP6YFm1Hg25TN9WGLqM12b8TQmcknKrdu1oxWux",
        token_decimals=8,
        amount="4536555",
        value_usd="0.042",
        from_address="from",
        to_address="wallet-1",
        raw_json=json.dumps({"trans_id": "sig-1"}),
    )

    assert store.count_solscan_account_transactions("wallet-1") == 1
    assert store.count_solscan_account_transfers("wallet-1") == 1
    assert store.list_solscan_account_signatures("wallet-1") == ["sig-1"]
