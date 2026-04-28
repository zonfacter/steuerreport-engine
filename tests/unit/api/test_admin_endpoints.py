from __future__ import annotations

import importlib

from tax_engine.api.app import (
    AdminSettingsPutRequest,
    CexCredentialsLoadRequest,
    DashboardRoleOverrideRequest,
    IgnoredTokenDeleteRequest,
    IgnoredTokenUpsertRequest,
    admin_cex_credentials_load,
    admin_ignored_tokens_delete,
    admin_ignored_tokens_list,
    admin_ignored_tokens_upsert,
    admin_runtime_config,
    admin_settings_list,
    admin_settings_put,
    dashboard_overview,
    dashboard_role_override,
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


def test_dashboard_role_override_and_overview() -> None:
    _reset_store()
    override_resp = dashboard_role_override(DashboardRoleOverrideRequest(mode="business"))
    assert override_resp.status == "success"

    overview_resp = dashboard_overview()
    assert overview_resp.status == "success"
    role = overview_resp.data.get("role_detection", {})
    assert role.get("override_mode") == "business"
    assert role.get("effective_mode") == "business"


def test_dashboard_yearly_values_ignore_transfers_and_deduplicate_trade_pairs_for_all_assets() -> None:
    _reset_store()
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

    assert rows_by_asset_source[("SOL", "test")]["value_usd"] == "200"
    assert rows_by_asset_source[("HNT", "test")]["value_usd"] == "115"
    assert rows_by_asset_source[("USDC", "test")]["value_usd"] == "100"
    assert rows_by_asset_source[("USDT", "test")]["value_usd"] == "200"
    assert rows_by_asset_source[("USDT", "blockpit")]["value_usd"] == "1000"
    assert totals[2025]["value_usd"] == "1315"
    assert totals[2025]["trading_value_usd"] == "1300"
    breakdown = {(item["year"], item["category"]): item for item in activity["event_breakdown"]}
    assert breakdown[(2025, "trade_swap")]["events"] == 6
    assert breakdown[(2025, "transfer")]["events"] == 1
    assert breakdown[(2025, "reward_einkunft")]["events"] == 1
    source_breakdown = {(item["year"], item["source"]): item for item in activity["source_breakdown"]}
    assert source_breakdown[(2025, "blockpit")]["events"] == 2
    assert overview_resp.data["portfolio_value_history"]


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
