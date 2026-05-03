from __future__ import annotations

import importlib
from decimal import Decimal

from tax_engine.admin import put_admin_setting
from tax_engine.api.app import (
    CexFullHistoryImportRequest,
    connectors_cex_balances_preview,
    connectors_cex_import_confirm,
    connectors_cex_import_full_history,
    connectors_cex_transactions_preview,
    connectors_cex_verify,
    connectors_solana_import_confirm,
    connectors_solana_import_full_history,
    connectors_solana_rpc_probe,
    connectors_solana_wallet_preview,
)
from tax_engine.connectors.models import (
    CexBalancesPreviewRequest,
    CexImportConfirmRequest,
    CexTransactionsPreviewRequest,
    CexVerifyRequest,
    SolanaFullHistoryImportRequest,
    SolanaImportConfirmRequest,
    SolanaRpcProbeRequest,
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
    app_module = importlib.import_module("tax_engine.api.connectors")

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
    app_module = importlib.import_module("tax_engine.api.connectors")

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
    app_module = importlib.import_module("tax_engine.api.connectors")

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
    app_module = importlib.import_module("tax_engine.api.connectors")

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


def test_solana_rpc_probe_endpoint_success_with_monkeypatched_service(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.connectors")

    def _fake_probe(**kwargs):
        return {
            "rpc_url": kwargs["rpc_url"],
            "rpc_endpoints": [kwargs["rpc_url"], *kwargs["rpc_fallback_urls"]],
            "probe_count": 2,
            "ok_count": 1,
            "first_working_endpoint": kwargs["rpc_url"],
            "results": [
                {
                    "endpoint": kwargs["rpc_url"],
                    "ok": True,
                    "block_height": 123,
                    "error": "",
                },
                {
                    "endpoint": "https://bad.rpc",
                    "ok": False,
                    "block_height": None,
                    "error": "timeout",
                },
            ],
        }

    monkeypatch.setattr(app_module, "probe_solana_rpc_endpoints", _fake_probe)

    response = connectors_solana_rpc_probe(
        SolanaRpcProbeRequest(
            rpc_url="https://rpc.test",
            rpc_fallback_urls=["https://bad.rpc"],
        )
    )
    assert response.status == "success"
    assert response.data["ok_count"] == 1
    assert response.data["first_working_endpoint"] == "https://rpc.test"


def test_solana_import_confirm_persists_preview_rows(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.connectors")

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


def test_cex_import_full_history_binance(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.connectors")

    def _fake_fetch(**kwargs):
        return {
            "connector_id": kwargs["connector_id"],
            "count": 1,
            "rows": [
                {
                    "timestamp_utc": "2026-01-01T00:00:00+00:00",
                    "asset": "USDT",
                    "quantity": "10",
                    "price": "",
                    "fee": "0",
                    "fee_asset": "",
                    "side": "in",
                    "event_type": "deposit",
                    "tx_id": f"tx-{kwargs.get('start_time_ms')}",
                    "source": "binance_api",
                    "raw_row": {"txId": f"tx-{kwargs.get('start_time_ms')}"},
                }
            ],
            "warnings": [],
        }

    monkeypatch.setattr(app_module, "fetch_cex_transactions_preview", _fake_fetch)

    response = connectors_cex_import_full_history(
        CexFullHistoryImportRequest(
            connector_id="binance",
            api_key="key",
            api_secret="secret",
            start_time_ms=1704067200000,  # 2024-01-01
            end_time_ms=1704240000000,  # 2024-01-03
            window_days=1,
            max_rows_per_call=1000,
        )
    )
    assert response.status == "success"
    assert response.data["windows_processed"] >= 2
    assert response.data["total_inserted_events"] >= 1


def test_cex_import_full_history_splits_failed_windows(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.connectors")

    def _fake_fetch(**kwargs):
        start_ms = int(kwargs.get("start_time_ms") or 0)
        end_ms = int(kwargs.get("end_time_ms") or 0)
        duration = end_ms - start_ms + 1
        # Simuliert einen Provider, der große Fenster ablehnt (Rate-Limit/Timeout).
        if duration > 12 * 60 * 60 * 1000:
            raise RuntimeError("window_too_large")
        return {
            "connector_id": kwargs["connector_id"],
            "count": 1,
            "rows": [
                {
                    "timestamp_utc": "2026-01-01T00:00:00+00:00",
                    "asset": "USDT",
                    "quantity": "10",
                    "price": "",
                    "fee": "0",
                    "fee_asset": "",
                    "side": "in",
                    "event_type": "deposit",
                    "tx_id": f"tx-{start_ms}-{end_ms}",
                    "source": "binance_api",
                    "raw_row": {"txId": f"tx-{start_ms}-{end_ms}"},
                }
            ],
            "warnings": [],
        }

    monkeypatch.setattr(app_module, "fetch_cex_transactions_preview", _fake_fetch)

    response = connectors_cex_import_full_history(
        CexFullHistoryImportRequest(
            connector_id="binance",
            api_key="key",
            api_secret="secret",
            start_time_ms=1704067200000,
            end_time_ms=1704153600000,  # 1 Tag
            window_days=1,
            max_rows_per_call=1000,
        )
    )
    assert response.status in {"success", "partial"}
    assert response.data["windows_processed"] >= 2
    assert response.data["total_inserted_events"] >= 1


def test_solana_import_full_history_endpoint_paginates_with_cursor(monkeypatch) -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.connectors")

    call_state: dict[str, int] = {"call": 0}

    def _fake_fetch(**kwargs):
        call_state["call"] += 1
        call = int(call_state["call"])
        if call == 1:
            return {
                "wallet_address": kwargs["wallet_address"],
                "rpc_url": kwargs["rpc_url"],
                "signature_scanned_count": 2,
                "next_before_signature": "sig-002",
                "reached_start": False,
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
                        "tx_id": "sig-001",
                        "source": "solana_rpc",
                        "raw_row": {"signature": "sig-001"},
                    }
                ],
            }
        if call == 2:
            return {
                "wallet_address": kwargs["wallet_address"],
                "rpc_url": kwargs["rpc_url"],
                "signature_scanned_count": 1,
                "next_before_signature": None,
                "reached_start": True,
                "count": 1,
                "rows": [
                    {
                        "timestamp_utc": "2025-12-31T23:59:59+00:00",
                        "asset": "SOL",
                        "quantity": "0.2",
                        "price": "",
                        "fee": "0.000005",
                        "fee_asset": "SOL",
                        "side": "out",
                        "event_type": "sol_transfer",
                        "tx_id": "sig-002",
                        "source": "solana_rpc",
                        "raw_row": {"signature": "sig-002"},
                    }
                ],
            }
        raise AssertionError("unexpected third call")

    monkeypatch.setattr(app_module, "fetch_solana_wallet_full_history", _fake_fetch)

    response = connectors_solana_import_full_history(
        SolanaFullHistoryImportRequest(
            wallet_address="11111111111111111111111111111111",
            rpc_url="https://rpc.test",
            rpc_fallback_urls=[],
            start_time_ms=1704067200000,
            end_time_ms=1704240000000,
            max_signatures_per_call=100,
            max_signatures_total=100,
            source_name="solana_wallet_full_import",
        )
    )
    assert response.status == "success"
    assert response.data["calls"] == 2
    assert response.data["chunks_processed"] == 2
    assert response.data["total_inserted_events"] == 2
    assert response.data["reached_start"] is True
    assert call_state["call"] == 2


def test_solana_import_full_history_endpoint_invalid_window() -> None:
    _reset_store()
    response = connectors_solana_import_full_history(
        SolanaFullHistoryImportRequest(
            wallet_address="11111111111111111111111111111111",
            rpc_url="https://rpc.test",
            rpc_fallback_urls=[],
            start_time_ms=1704240000000,
            end_time_ms=1704067200000,
        )
    )
    assert response.status == "error"
    assert response.data == {}
    assert response.errors[0]["code"] == "invalid_time_window"


def test_connector_token_display_helpers_cover_alias_ignore_and_spam_paths() -> None:
    _reset_store()
    connector_module = importlib.import_module("tax_engine.api.connectors")

    put_admin_setting(
        "runtime.token_aliases",
        {
            "mint1": {"symbol": "abc", "name": "Alias Coin", "notes": "test"},
            "invalid": {"symbol": "", "name": ""},
        },
        is_secret=False,
    )
    put_admin_setting(
        "runtime.ignored_tokens",
        {
            "mint1": {"reason": "Spam", "updated_at_utc": "2026-01-01T00:00:00+00:00"},
            "invalid": {"reason": ""},
        },
        is_secret=False,
    )

    assert connector_module._safe_decimal("invalid") == Decimal("0")
    assert connector_module._normalize_mint(" mint1 ") == "MINT1"
    assert connector_module._load_token_aliases()["MINT1"]["symbol"] == "ABC"
    assert connector_module._load_ignored_tokens()["MINT1"]["reason"] == "Spam"
    assert connector_module._resolve_token_display("mint1")["display_source"] == "alias"
    assert connector_module._is_spam_candidate("UNKNOWN", Decimal("0.001"), known=False) is True
    assert connector_module._is_spam_candidate("UNKNOWN", Decimal("0"), known=False) is False
    assert connector_module._is_spam_candidate("SOL", Decimal("10000000"), known=True) is False

    decorated = connector_module._decorate_token_rows(
        [
            {"asset": "mint1", "quantity": "1.2300"},
            "not-a-row",
        ]
    )
    assert decorated == [
        {
            "asset": "mint1",
            "quantity": "1.23",
            "symbol": "ABC",
            "name": "Alias Coin",
            "display_source": "alias",
            "ignored": "true",
            "ignored_reason": "Spam",
            "spam_candidate": "false",
        }
    ]
