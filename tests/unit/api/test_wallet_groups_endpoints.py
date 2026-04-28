from __future__ import annotations

import importlib

from tax_engine.api.app import (
    connectors_solana_balance_snapshot,
    connectors_solana_group_balance_snapshot,
    connectors_solana_group_import_confirm,
    dashboard_portfolio_set_history,
    dashboard_wallet_snapshots,
    import_confirm,
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
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_wallet_group_upsert_list_delete_roundtrip() -> None:
    _reset_store()
    upsert = wallet_groups_upsert(
        WalletGroupUpsertRequest(
            name="Core Solana",
            wallet_addresses=["wallet-1", "wallet-2"],
            source_filters=["solana_rpc", "binance_api"],
            description="Testgruppe",
        )
    )
    assert upsert.status == "success"
    group_id = upsert.data["group_id"]

    listed = wallet_groups_list()
    assert listed.status == "success"
    assert listed.data["count"] == 1
    assert listed.data["groups"][0]["group_id"] == group_id
    assert listed.data["groups"][0]["source_filters"] == ["solana_rpc", "binance_api"]

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


def test_portfolio_set_history_filters_by_group_sources() -> None:
    _reset_store()
    solana = [
        {
            "timestamp_utc": "2026-01-15T00:00:00+00:00",
            "asset": "SOL",
            "quantity": "1",
            "side": "in",
            "event_type": "buy",
            "source": "solana_rpc",
            "value_usd": "100",
            "tx_id": "set-sol-1",
        }
    ]
    binance = [
        {
            "timestamp_utc": "2026-01-16T00:00:00+00:00",
            "asset": "BTC",
            "quantity": "1",
            "side": "in",
            "event_type": "buy",
            "source": "binance_api",
            "value_usd": "100000",
            "tx_id": "set-btc-1",
        }
    ]
    import_confirm(ConfirmImportRequest(source_name="solana.csv", rows=solana))
    import_confirm(ConfirmImportRequest(source_name="binance.csv", rows=binance))
    upsert = wallet_groups_upsert(
        WalletGroupUpsertRequest(
            name="Solana Set",
            wallet_addresses=["wallet-1"],
            source_filters=["solana_rpc"],
        )
    )

    response = dashboard_portfolio_set_history(group_id=upsert.data["group_id"], window_days=3650)

    assert response.status == "success"
    assert response.data["event_count"] == 1
    assert response.data["source_filters"] == ["solana_rpc"]
    assert response.data["group"]["source_event_count"] == 1


def test_portfolio_set_history_empty_sources_means_all_sources() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="all_sources.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-15T00:00:00+00:00",
                    "asset": "SOL",
                    "quantity": "1",
                    "side": "in",
                    "event_type": "buy",
                    "source": "solana_rpc",
                    "value_usd": "100",
                    "tx_id": "all-sol-1",
                },
                {
                    "timestamp_utc": "2026-01-16T00:00:00+00:00",
                    "asset": "BTC",
                    "quantity": "1",
                    "side": "in",
                    "event_type": "buy",
                    "source": "binance_api",
                    "value_usd": "100000",
                    "tx_id": "all-btc-1",
                },
            ],
        )
    )
    upsert = wallet_groups_upsert(
        WalletGroupUpsertRequest(
            name="All Set",
            wallet_addresses=["wallet-1"],
            source_filters=[],
        )
    )

    response = dashboard_portfolio_set_history(group_id=upsert.data["group_id"], window_days=3650)

    assert response.status == "success"
    assert response.data["event_count"] == 2
    assert response.data["source_filters"] == []
    assert response.data["group"]["source_event_count"] == 2
