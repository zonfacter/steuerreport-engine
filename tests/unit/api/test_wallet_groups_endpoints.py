from __future__ import annotations

import importlib

from tax_engine.api.app import (
    connectors_solana_balance_snapshot,
    connectors_solana_group_balance_snapshot,
    connectors_solana_group_import_confirm,
    dashboard_wallet_snapshots,
    wallet_groups_delete,
    wallet_groups_list,
    wallet_groups_upsert,
)
from tax_engine.connectors.models import (
    SolanaBalanceSnapshotRequest,
    SolanaGroupBalanceSnapshotRequest,
    SolanaGroupImportConfirmRequest,
    WalletGroupDeleteRequest,
    WalletGroupUpsertRequest,
)
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_wallet_group_upsert_list_delete_roundtrip() -> None:
    _reset_store()
    upsert = wallet_groups_upsert(
        WalletGroupUpsertRequest(
            name="Core Solana",
            wallet_addresses=["wallet-1", "wallet-2"],
            description="Testgruppe",
        )
    )
    assert upsert.status == "success"
    group_id = upsert.data["group_id"]

    listed = wallet_groups_list()
    assert listed.status == "success"
    assert listed.data["count"] == 1
    assert listed.data["groups"][0]["group_id"] == group_id

    deleted = wallet_groups_delete(WalletGroupDeleteRequest(group_id=group_id))
    assert deleted.status == "success"
    assert deleted.data["deleted"] is True
    assert deleted.data["count"] == 0


def test_group_balance_snapshot_aggregates_wallets(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.connectors")

    def _fake_balances(**kwargs):
        wallet = kwargs["wallet_address"]
        if wallet == "wallet-1":
            return {
                "wallet_address": wallet,
                "sol_balance": "1.5",
                "total_estimated_usd": "100",
                "tokens": [{"asset": "AAA", "quantity": "10", "usd_value": "25"}],
            }
        return {
            "wallet_address": wallet,
            "sol_balance": "0.5",
            "total_estimated_usd": "40",
            "tokens": [{"asset": "AAA", "quantity": "2", "usd_value": "5"}],
        }

    monkeypatch.setattr(app_module, "fetch_solana_wallet_balances", _fake_balances)
    response = connectors_solana_group_balance_snapshot(
        SolanaGroupBalanceSnapshotRequest(
            wallet_addresses=["wallet-1", "wallet-2"],
            rpc_url="https://rpc.test",
            rpc_fallback_urls=[],
            include_prices=True,
        )
    )
    assert response.status == "success"
    assert response.data["wallet_count"] == 2
    assert response.data["total_sol_balance"] == "2"
    assert response.data["total_estimated_usd"] == "140"
    assert response.data["tokens"][0]["asset"] == "AAA"
    assert response.data["tokens"][0]["quantity"] == "12"


def test_group_import_confirm_merges_rows(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.connectors")

    def _fake_preview(**kwargs):
        wallet = kwargs["wallet_address"]
        return {
            "wallet_address": wallet,
            "signature_count": 1,
            "last_signature": f"sig-{wallet}",
            "warnings": [],
            "rows": [
                {
                    "timestamp_utc": "2026-01-01T00:00:00+00:00",
                    "asset": "SOL",
                    "quantity": "0.1",
                    "price": "",
                    "fee": "0",
                    "fee_asset": "SOL",
                    "side": "in",
                    "event_type": "sol_transfer",
                    "tx_id": f"tx-{wallet}",
                    "source": "solana_rpc",
                    "raw_row": {},
                }
            ],
        }

    monkeypatch.setattr(app_module, "fetch_solana_wallet_preview", _fake_preview)
    response = connectors_solana_group_import_confirm(
        SolanaGroupImportConfirmRequest(
            wallet_addresses=["wallet-1", "wallet-2"],
            rpc_url="https://rpc.test",
            rpc_fallback_urls=[],
            source_name="group_import_test",
        )
    )
    assert response.status == "success"
    assert response.data["wallet_count"] == 2
    assert response.data["fetched_rows"] == 2
    assert response.data["import_result"]["inserted_events"] == 2


def test_wallet_snapshot_history_tracks_balance_requests(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.connectors")

    def _fake_balances(**kwargs):
        return {
            "wallet_address": kwargs["wallet_address"],
            "sol_balance": "1.0",
            "total_estimated_usd": "50",
            "tokens": [],
        }

    monkeypatch.setattr(app_module, "fetch_solana_wallet_balances", _fake_balances)
    balance_response = connectors_solana_balance_snapshot(
        SolanaBalanceSnapshotRequest(
            wallet_address="11111111111111111111111111111111",
            rpc_url="https://rpc.test",
            rpc_fallback_urls=[],
            include_prices=True,
        )
    )
    assert balance_response.status == "success"

    snapshots = dashboard_wallet_snapshots(scope="wallet", entity_id="11111111111111111111111111111111")
    assert snapshots.status == "success"
    assert snapshots.data["count"] >= 1
    assert snapshots.data["points"][-1]["entity_id"] == "11111111111111111111111111111111"
