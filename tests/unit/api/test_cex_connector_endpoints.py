from __future__ import annotations

import importlib

from tax_engine.api.app import (
    connectors_cex_balances_preview,
    connectors_cex_import_confirm,
    connectors_cex_transactions_preview,
    connectors_cex_verify,
    connectors_solana_import_confirm,
    connectors_solana_wallet_preview,
)
from tax_engine.connectors.models import (
    CexBalancesPreviewRequest,
    CexImportConfirmRequest,
    CexTransactionsPreviewRequest,
    CexVerifyRequest,
    SolanaImportConfirmRequest,
    SolanaWalletPreviewRequest,
)
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_cex_verify_endpoint_with_unsupported_connector_returns_partial() -> None:
    _reset_store()
    response = connectors_cex_verify(
        CexVerifyRequest(
            connector_id="unknown",
            api_key="abcd1234",
            api_secret="secret",
            passphrase=None,
        )
    )
    assert response.status == "partial"
    assert response.data["ok"] is False
    assert response.data["error_code"] == "unsupported_connector"


def test_cex_balances_preview_endpoint_success_with_monkeypatched_service(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.app")

    def _fake_fetch(**kwargs):
        return {
            "connector_id": kwargs["connector_id"],
            "count": 1,
            "rows": [
                {
                    "timestamp_utc": "2026-01-01T00:00:00+00:00",
                    "asset": "BTC",
                    "quantity": "0.5",
                    "event_type": "balance_snapshot",
                    "source": "binance_api",
                }
            ],
        }

    monkeypatch.setattr(app_module, "fetch_cex_balance_preview", _fake_fetch)

    response = connectors_cex_balances_preview(
        CexBalancesPreviewRequest(
            connector_id="binance",
            api_key="abcd12345678",
            api_secret="secret",
            passphrase=None,
            max_rows=100,
        )
    )
    assert response.status == "success"
    assert response.data["count"] == 1
    assert response.data["rows"][0]["asset"] == "BTC"


def test_cex_transactions_preview_endpoint_success_with_monkeypatched_service(
    monkeypatch,
) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.app")

    def _fake_fetch(**kwargs):
        return {
            "connector_id": kwargs["connector_id"],
            "count": 1,
            "rows": [
                {
                    "timestamp_utc": "2026-01-01T00:00:00+00:00",
                    "asset": "USDT",
                    "quantity": "100",
                    "price": "",
                    "fee": "0",
                    "fee_asset": "",
                    "side": "in",
                    "event_type": "deposit",
                    "tx_id": "tx-1",
                    "source": "binance_api",
                    "raw_row": {"txId": "tx-1"},
                }
            ],
            "warnings": [],
        }

    monkeypatch.setattr(app_module, "fetch_cex_transactions_preview", _fake_fetch)

    response = connectors_cex_transactions_preview(
        CexTransactionsPreviewRequest(
            connector_id="binance",
            api_key="abcd12345678",
            api_secret="secret",
            passphrase=None,
            max_rows=100,
        )
    )
    assert response.status == "success"
    assert response.data["count"] == 1
    assert response.data["rows"][0]["event_type"] == "deposit"


def test_cex_import_confirm_persists_preview_rows(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.app")

    def _fake_fetch(**kwargs):
        return {
            "connector_id": kwargs["connector_id"],
            "count": 1,
            "rows": [
                {
                    "timestamp_utc": "2026-01-01T00:00:00+00:00",
                    "asset": "USDT",
                    "quantity": "100",
                    "price": "",
                    "fee": "0",
                    "fee_asset": "",
                    "side": "in",
                    "event_type": "deposit",
                    "tx_id": "tx-1",
                    "source": "binance_api",
                    "raw_row": {"txId": "tx-1"},
                }
            ],
            "warnings": [],
        }

    monkeypatch.setattr(app_module, "fetch_cex_transactions_preview", _fake_fetch)

    response = connectors_cex_import_confirm(
        CexImportConfirmRequest(
            connector_id="binance",
            api_key="abcd12345678",
            api_secret="secret",
            passphrase=None,
            max_rows=100,
            source_name="binance_api_import",
        )
    )
    assert response.status == "success"
    assert response.data["fetched_rows"] == 1
    assert response.data["import_result"]["inserted_events"] == 1


def test_solana_wallet_preview_endpoint_success_with_monkeypatched_service(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.app")

    def _fake_fetch(**kwargs):
        return {
            "wallet_address": kwargs["wallet_address"],
            "rpc_url": kwargs["rpc_url"],
            "signature_count": 1,
            "count": 1,
            "rows": [
                {
                    "timestamp_utc": "2026-01-01T00:00:00+00:00",
                    "asset": "SOL",
                    "quantity": "0.1",
                    "price": "",
                    "fee": "0.000005",
                    "fee_asset": "SOL",
                    "side": "in",
                    "event_type": "sol_transfer",
                    "tx_id": "sig-1",
                    "source": "solana_rpc",
                    "raw_row": {"signature": "sig-1"},
                }
            ],
            "warnings": [],
        }

    monkeypatch.setattr(app_module, "fetch_solana_wallet_preview", _fake_fetch)

    response = connectors_solana_wallet_preview(
        SolanaWalletPreviewRequest(
            wallet_address="11111111111111111111111111111111",
            rpc_url="https://rpc.test",
            rpc_fallback_urls=[],
        )
    )
    assert response.status == "success"
    assert response.data["count"] == 1
    assert response.data["rows"][0]["asset"] == "SOL"


def test_solana_import_confirm_persists_preview_rows(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.app")

    def _fake_fetch(**kwargs):
        return {
            "wallet_address": kwargs["wallet_address"],
            "rpc_url": kwargs["rpc_url"],
            "signature_count": 1,
            "count": 1,
            "rows": [
                {
                    "timestamp_utc": "2026-01-01T00:00:00+00:00",
                    "asset": "SOL",
                    "quantity": "0.1",
                    "price": "",
                    "fee": "0.000005",
                    "fee_asset": "SOL",
                    "side": "in",
                    "event_type": "sol_transfer",
                    "tx_id": "sig-1",
                    "source": "solana_rpc",
                    "raw_row": {"signature": "sig-1"},
                }
            ],
            "warnings": [],
        }

    monkeypatch.setattr(app_module, "fetch_solana_wallet_preview", _fake_fetch)

    response = connectors_solana_import_confirm(
        SolanaImportConfirmRequest(
            wallet_address="11111111111111111111111111111111",
            rpc_url="https://rpc.test",
            rpc_fallback_urls=[],
            source_name="solana_wallet_import",
        )
    )
    assert response.status == "success"
    assert response.data["fetched_rows"] == 1
    assert response.data["import_result"]["inserted_events"] == 1
