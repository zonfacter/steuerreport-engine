from __future__ import annotations

import importlib
from pathlib import Path
from subprocess import CompletedProcess

from tax_engine.api.app import (
    AdminServiceActionRequest,
    AdminSettingsPutRequest,
    CexCredentialsLoadRequest,
    DashboardRoleOverrideRequest,
    IgnoredTokenDeleteRequest,
    IgnoredTokenUpsertRequest,
    TokenAliasDeleteRequest,
    TokenAliasUpsertRequest,
    _build_solana_backfill_status,
    _tail_file,
    admin_cex_credentials_load,
    admin_ignored_tokens_delete,
    admin_ignored_tokens_list,
    admin_ignored_tokens_upsert,
    admin_runtime_config,
    admin_settings_list,
    admin_settings_put,
    admin_solana_backfill_action,
    admin_solana_backfill_status,
    admin_token_aliases_delete,
    admin_token_aliases_list,
    admin_token_aliases_upsert,
    dashboard_overview,
    dashboard_role_override,
    dashboard_transaction_search,
    portfolio_helium_legacy_transfers,
)
from tax_engine.ingestion.service import confirm_import
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_admin_settings_put_and_list_roundtrip() -> None:
    _reset_store()
    put_resp = admin_settings_put(
        AdminSettingsPutRequest(
            setting_key="runtime.solana.rpc_url",
            value="https://rpc.example",
            is_secret=False,
        )
    )
    assert put_resp.status == "success"

    list_resp = admin_settings_list()
    assert list_resp.status == "success"
    settings = list_resp.data.get("settings", [])
    assert any(item.get("setting_key") == "runtime.solana.rpc_url" for item in settings)


def test_admin_runtime_config_masks_secret() -> None:
    _reset_store()
    app_module = importlib.import_module("tax_engine.api.app")
    put_resp = app_module.admin_settings_put(
        AdminSettingsPutRequest(
            setting_key="secret.alchemy.api_key",
            value="abcd1234SECRET5678",
            is_secret=True,
        )
    )
    assert put_resp.status == "success"

    runtime_resp = admin_runtime_config()
    assert runtime_resp.status == "success"
    credentials = runtime_resp.data.get("credentials", {})
    assert credentials.get("alchemy_configured") is True
    assert "..." in str(credentials.get("alchemy_api_key_masked", ""))


def test_admin_runtime_config_ignores_corrupt_secret() -> None:
    _reset_store()
    STORE.upsert_setting(
        setting_key="secret.coingecko.api_key",
        value_json="v1:corrupt",
        is_secret=True,
    )

    runtime_resp = admin_runtime_config()

    assert runtime_resp.status == "success"
    credentials = runtime_resp.data.get("credentials", {})
    assert credentials.get("coingecko_configured") is False
    assert credentials.get("coingecko_api_key_masked") == ""


def test_dashboard_role_override_and_overview() -> None:
    _reset_store()
    override_resp = dashboard_role_override(DashboardRoleOverrideRequest(mode="business"))
    assert override_resp.status == "success"

    overview_resp = dashboard_overview()
    assert overview_resp.status == "success"
    role = overview_resp.data.get("role_detection", {})
    assert role.get("override_mode") == "business"
    assert role.get("effective_mode") == "business"


def test_dashboard_transaction_search_filters_wallet_tx_and_asset() -> None:
    _reset_store()
    rows = [
        {
            "timestamp_utc": "2024-11-23T05:43:01+00:00",
            "asset": "USDC",
            "quantity": "9999.989803",
            "side": "out",
            "event_type": "swap_out_aggregated",
            "source": "solana_rpc",
            "tx_id": "tx-search-1",
            "wallet_address": "wallet-main-123",
            "raw_row": {"from_asset": "USDC", "to_asset": "JUP", "jupiter_aggregated": True},
        },
        {
            "timestamp_utc": "2024-11-23T05:43:01+00:00",
            "asset": "JUP",
            "quantity": "8524.295277",
            "side": "in",
            "event_type": "swap_in_aggregated",
            "source": "solana_rpc",
            "tx_id": "tx-search-1",
            "wallet_address": "wallet-main-123",
            "raw_row": {"from_asset": "USDC", "to_asset": "JUP", "jupiter_aggregated": True},
        },
        {
            "timestamp_utc": "2025-01-01T00:00:00+00:00",
            "asset": "HNT",
            "quantity": "1",
            "side": "in",
            "event_type": "mining_reward",
            "source": "heliumgeek",
            "tx_id": "reward-search-1",
            "gateway_address": "gateway-1",
        },
    ]
    confirm_import("transaction-search-test", rows)

    response = dashboard_transaction_search(year=2024, wallet="wallet-main", asset="JUP", tx_id="tx-search-1")

    assert response.status == "success"
    found = response.data["rows"]
    assert len(found) == 1
    assert found[0]["symbol"] == "JUP"
    assert found[0]["wallet_address"] == "wallet-main-123"
    assert found[0]["tx_id"] == "tx-search-1"


def test_dashboard_yearly_values_ignore_transfers_and_deduplicate_trade_pairs_for_all_assets() -> None:
    _reset_store()
    admin_token_aliases_upsert(
        TokenAliasUpsertRequest(
            mint="FAKEUSDCMINT1111111111111111111111111111",
            symbol="USDC",
            name="USD Coin Alias",
        )
    )
    STORE.upsert_fx_rate("2025-01-01", "SOL", "USD", "100", "test", "2025-01-01")
    STORE.upsert_fx_rate("2025-01-01", "USDT", "USD", "1", "test", "2025-01-01")
    STORE.upsert_fx_rate("2025-01-01", "HNT", "USD", "5", "test", "2025-01-01")
    STORE.upsert_fx_rate("2025-01-01", "USDC", "USD", "1", "test", "2025-01-01")
    rows = [
        {
            "timestamp_utc": "2025-01-01T00:00:00+00:00",
            "asset": "SOL",
            "quantity": "10",
            "side": "in",
            "event_type": "deposit",
            "source": "test",
            "tx_id": "transfer-sol",
        },
        {
            "timestamp_utc": "2025-01-01T01:00:00+00:00",
            "asset": "SOL",
            "quantity": "2",
            "side": "out",
            "event_type": "trade",
            "source": "test",
            "tx_id": "trade-sol-usdt",
        },
        {
            "timestamp_utc": "2025-01-01T01:00:00+00:00",
            "asset": "USDT",
            "quantity": "200",
            "side": "in",
            "event_type": "trade",
            "source": "test",
            "tx_id": "trade-sol-usdt",
        },
        {
            "timestamp_utc": "2025-01-02T01:00:00+00:00",
            "asset": "SOL",
            "quantity": "1",
            "side": "out",
            "event_type": "trade",
            "source": "test",
            "tx_id": "trade-sol-usdc-mint",
        },
        {
            "timestamp_utc": "2025-01-02T01:00:00+00:00",
            "asset": "FAKEUSDCMINT1111111111111111111111111111",
            "quantity": "50",
            "side": "in",
            "event_type": "trade",
            "source": "test",
            "tx_id": "trade-sol-usdc-mint",
        },
        {
            "timestamp_utc": "2025-01-01T02:00:00+00:00",
            "asset": "HNT",
            "quantity": "20",
            "side": "out",
            "event_type": "swap_out_aggregated",
            "source": "test",
            "tx_id": "swap-hnt-usdc",
        },
        {
            "timestamp_utc": "2025-01-01T02:00:00+00:00",
            "asset": "USDC",
            "quantity": "100",
            "side": "in",
            "event_type": "swap_in_aggregated",
            "source": "test",
            "tx_id": "swap-hnt-usdc",
        },
        {
            "timestamp_utc": "2025-01-01T03:00:00+00:00",
            "asset": "HNT",
            "quantity": "3",
            "side": "in",
            "event_type": "mining_reward",
            "source": "test",
            "tx_id": "reward-hnt",
        },
        {
            "timestamp_utc": "2025-01-01T04:00:00+00:00",
            "asset": "BTC",
            "quantity": "0.01",
            "side": "out",
            "event_type": "trade",
            "source": "blockpit",
            "tx_id": "blockpit-99:out",
        },
        {
            "timestamp_utc": "2025-01-01T04:00:00+00:00",
            "asset": "USDT",
            "quantity": "1000",
            "side": "in",
            "event_type": "trade",
            "source": "blockpit",
            "tx_id": "blockpit-99:in",
        },
    ]
    confirm_import("dashboard-test", rows)

    overview_resp = dashboard_overview()
    assert overview_resp.status == "success"
    activity = overview_resp.data["yearly_asset_activity"]
    totals = {item["year"]: item for item in activity["totals_by_year"]}
    rows_by_asset_source = {(item["asset"], item["source"]): item for item in activity["rows"]}

    assert rows_by_asset_source[("SOL", "test")]["value_usd"] == "300"
    assert rows_by_asset_source[("SOL", "test")]["unpriced_events"] == 0
    assert rows_by_asset_source[("HNT", "test")]["value_usd"] == "115"
    assert rows_by_asset_source[("USDC", "test")]["value_usd"] == "100"
    assert rows_by_asset_source[("FAKEUSDCMINT1111111111111111111111111111", "test")]["value_usd"] == "50"
    assert rows_by_asset_source[("USDT", "test")]["value_usd"] == "200"
    assert rows_by_asset_source[("USDT", "blockpit")]["value_usd"] == "1000"
    assert totals[2025]["value_usd"] == "1415"
    assert totals[2025]["trading_value_usd"] == "1400"
    breakdown = {(item["year"], item["category"]): item for item in activity["event_breakdown"]}
    assert breakdown[(2025, "trade_swap")]["events"] == 8
    assert breakdown[(2025, "transfer")]["events"] == 1
    assert breakdown[(2025, "transfer")]["unpriced_events"] == 0
    assert breakdown[(2025, "reward_einkunft")]["events"] == 1
    source_breakdown = {(item["year"], item["source"]): item for item in activity["source_breakdown"]}
    assert source_breakdown[(2025, "blockpit")]["events"] == 2
    assert overview_resp.data["portfolio_value_history"]


def test_portfolio_helium_legacy_transfers_groups_counterparties() -> None:
    _reset_store()
    legacy_wallet = "133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j"
    counterparty = "137tZvaxM4zjvfU9GcDzzmAsdMjkESCULx9XaVrGWKj989izPue"
    confirm_import(
        "helium_legacy_cointracking:test.csv",
        [
            {
                "timestamp_utc": "2022-01-05T08:30:00+00:00",
                "asset": "HNT",
                "quantity": "2.25",
                "fee": "0.00035",
                "fee_asset": "HNT",
                "side": "out",
                "event_type": "legacy_transfer",
                "tx_id": f"withdraw-tx+{legacy_wallet}",
                "wallet_address": legacy_wallet,
                "from_wallet": legacy_wallet,
                "to_wallet": counterparty,
                "counterparty_wallet": counterparty,
                "legacy_chain": "helium_l1",
                "source": "helium_legacy_cointracking",
                "raw_comment": f"payment_v2 to {counterparty}",
            },
            {
                "timestamp_utc": "2022-02-05T08:30:00+00:00",
                "asset": "HNT",
                "quantity": "1.25",
                "side": "in",
                "event_type": "legacy_transfer",
                "tx_id": f"deposit-tx+{legacy_wallet}",
                "wallet_address": legacy_wallet,
                "from_wallet": counterparty,
                "to_wallet": legacy_wallet,
                "counterparty_wallet": counterparty,
                "legacy_chain": "helium_l1",
                "source": "helium_legacy_cointracking",
                "raw_comment": f"payment_v1 from {counterparty}",
            },
            {
                "timestamp_utc": "2022-03-05T08:30:00+00:00",
                "asset": "HNT",
                "quantity": "9",
                "side": "in",
                "event_type": "mining_reward",
                "tx_id": f"reward-tx+{legacy_wallet}",
                "wallet_address": legacy_wallet,
                "source": "helium_legacy_cointracking",
            },
        ],
    )

    response = portfolio_helium_legacy_transfers()

    assert response.status == "success"
    summary = response.data["summary"]
    assert summary["origin_wallets"] == [legacy_wallet]
    assert summary["transfer_count"] == 2
    assert summary["sent_hnt"] == "2.25"
    assert summary["received_hnt"] == "1.25"
    assert summary["fees_hnt"] == "0.00035"
    assert summary["net_hnt"] == "-1.00035"
    rows = response.data["counterparties"]
    assert rows[0]["counterparty_wallet"] == counterparty
    assert rows[0]["outbound_count"] == 1
    assert rows[0]["inbound_count"] == 1


def test_admin_ignored_tokens_upsert_list_delete_roundtrip() -> None:
    _reset_store()
    mint = "CM8VSESV7MBHAFD5UDXH84QFGXMAVWJCVVHOPB1DZIF4"
    put_resp = admin_ignored_tokens_upsert(
        IgnoredTokenUpsertRequest(
            mint=mint,
            reason="Spam-Airdrop ohne wirtschaftlichen Wert",
        )
    )
    assert put_resp.status == "success"
    assert put_resp.data.get("mint") == mint

    list_resp = admin_ignored_tokens_list()
    assert list_resp.status == "success"
    items = list_resp.data.get("ignored_tokens", [])
    assert any(item.get("mint") == mint for item in items)

    delete_resp = admin_ignored_tokens_delete(IgnoredTokenDeleteRequest(mint=mint))
    assert delete_resp.status == "success"
    assert delete_resp.data.get("deleted") is True


def test_admin_cex_credentials_load_returns_saved_secret_values() -> None:
    _reset_store()
    admin_settings_put(
        AdminSettingsPutRequest(
            setting_key="secret.cex.binance.api_key",
            value="binance-key-1234",
            is_secret=True,
        )
    )
    admin_settings_put(
        AdminSettingsPutRequest(
            setting_key="secret.cex.binance.api_secret",
            value="binance-secret-5678",
            is_secret=True,
        )
    )
    admin_settings_put(
        AdminSettingsPutRequest(
            setting_key="secret.cex.binance.passphrase",
            value="",
            is_secret=True,
        )
    )

    response = admin_cex_credentials_load(CexCredentialsLoadRequest(connector_id="binance"))
    assert response.status == "success"
    assert response.data.get("api_key") == "binance-key-1234"
    assert response.data.get("api_secret") == "binance-secret-5678"


def test_admin_token_aliases_upsert_list_delete_roundtrip() -> None:
    _reset_store()
    mint = "cm8vSesV7mBHaFD5uDxH84qFgxmAvWJCvVHOpb1dZIF4"

    put_resp = admin_token_aliases_upsert(
        TokenAliasUpsertRequest(mint=mint, symbol="iot", name="Helium IOT", notes="Known token")
    )
    assert put_resp.status == "success"
    assert put_resp.data.get("mint") == mint.upper()

    list_resp = admin_token_aliases_list()
    assert list_resp.status == "success"
    aliases = list_resp.data.get("aliases", [])
    assert any(item.get("symbol") == "IOT" and item.get("name") == "Helium IOT" for item in aliases)

    delete_resp = admin_token_aliases_delete(TokenAliasDeleteRequest(mint=mint))
    assert delete_resp.status == "success"
    assert delete_resp.data.get("deleted") is True


def test_admin_solana_backfill_status_and_action_paths(monkeypatch) -> None:
    _reset_store()
    admin_module = importlib.import_module("tax_engine.api.admin")
    calls: list[list[str]] = []

    def fake_run_systemctl(args: list[str]) -> CompletedProcess[str]:
        calls.append(args)
        if args[0] == "show":
            return CompletedProcess(
                args=args,
                returncode=0,
                stdout="ActiveState=active\nSubState=running\nLoadState=loaded\nMainPID=123\nResult=success\n",
                stderr="",
            )
        if args[0] == "is-enabled":
            return CompletedProcess(args=args, returncode=0, stdout="enabled\n", stderr="")
        return CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(admin_module, "_run_systemctl", fake_run_systemctl)

    status = admin_solana_backfill_status()
    assert status.status == "success"
    assert status.data["active_state"] == "active"
    assert status.data["enabled"] is True

    action = admin_solana_backfill_action(AdminServiceActionRequest(action="restart"))
    assert action.status == "success"
    assert action.data["command"]["action"] == "restart"
    assert ["restart", "steuerreport-solana-backfill.service"] in calls


def test_admin_solana_backfill_error_and_helper_edge_paths(monkeypatch, tmp_path: Path) -> None:
    _reset_store()
    admin_module = importlib.import_module("tax_engine.api.admin")
    STORE.upsert_setting("runtime.scan.stats.wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB", "{bad-json", False)
    STORE.upsert_setting(
        "runtime.scan.cursor.wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB",
        "{bad-json",
        False,
    )

    def fake_run_systemctl(args: list[str]) -> CompletedProcess[str]:
        if args[0] == "show":
            return CompletedProcess(args=args, returncode=0, stdout="ActiveState=failed\nMainPID=0\n", stderr="")
        if args[0] == "is-enabled":
            return CompletedProcess(args=args, returncode=1, stdout="disabled\n", stderr="")
        return CompletedProcess(args=args, returncode=1, stdout="", stderr="unit failed")

    monkeypatch.setattr(admin_module, "_run_systemctl", fake_run_systemctl)

    status = _build_solana_backfill_status()
    assert status["active_state"] == "failed"
    assert status["enabled"] is False
    assert status["stats"] == "{bad-json"
    assert status["last_before_signature"] == "{bad-json"

    action = admin_solana_backfill_action(AdminServiceActionRequest(action="stop"))
    assert action.status == "error"
    assert action.errors[0]["code"] == "service_action_failed"

    log_file = tmp_path / "service.log"
    log_file.write_text("a\nb\nc\n", encoding="utf-8")
    assert _tail_file(log_file, max_lines=2) == ["b", "c"]
    assert _tail_file(tmp_path / "missing.log", max_lines=2) == []


def test_admin_loaders_ignore_invalid_json_and_credentials_error(monkeypatch) -> None:
    _reset_store()
    admin_module = importlib.import_module("tax_engine.api.admin")
    STORE.upsert_setting("runtime.token_aliases", "{bad-json", False)
    STORE.upsert_setting("runtime.ignored_tokens", "[]", False)

    assert admin_token_aliases_list().data["count"] == 0
    assert admin_ignored_tokens_list().data["count"] == 0

    monkeypatch.setattr(
        admin_module,
        "resolve_cex_credentials",
        lambda connector_id: (_ for _ in ()).throw(RuntimeError(f"missing {connector_id}")),
    )
    response = admin_cex_credentials_load(CexCredentialsLoadRequest(connector_id="binance"))
    assert response.status == "error"
    assert response.errors[0]["code"] == "cex_credentials_load_failed"
