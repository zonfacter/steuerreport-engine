from __future__ import annotations

from decimal import Decimal
from typing import Any

from tax_engine.api import dashboard


def _event(event_id: str, source: str, timestamp: str, event_type: str, asset: str, side: str, value: str) -> dict[str, Any]:
    return {
        "unique_event_id": event_id,
        "payload": {
            "source": source,
            "timestamp_utc": timestamp,
            "event_type": event_type,
            "asset": asset,
            "side": side,
            "quantity": value,
            "value_eur": value,
            "price": "50000",
            "price_eur": "45000",
        },
    }


def test_net_eur_flow_sankey_nets_trade_asset_values(monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "_runtime_usd_to_eur_rate", lambda: Decimal("1"))
    monkeypatch.setattr(dashboard, "_load_fx_lookup", lambda: {})

    events = [
        _event("pionex-usdt-out-1", "pionex", "2022-01-01T00:00:00+00:00", "trade", "USDT", "out", "150"),
        _event("binance-out", "binance", "2022-01-02T00:00:00+00:00", "withdrawal", "USDT", "out", "100"),
        _event("pionex-in", "pionex", "2022-01-02T00:05:00+00:00", "deposit", "USDT", "in", "100"),
        _event("pionex-usdt-in-1", "pionex", "2022-01-03T00:00:00+00:00", "trade", "USDT", "in", "20"),
        _event("pionex-mxc-in-1", "pionex", "2022-01-03T00:00:01+00:00", "trade", "MXC", "in", "80"),
    ]
    result = dashboard._build_net_eur_flow_sankey(
        events=events,
        transfer_matches=[
            {
                "outbound_event_id": "binance-out",
                "inbound_event_id": "pionex-in",
                "status": "matched",
            }
        ],
        year=2022,
        min_value_eur=Decimal("1"),
        limit=20,
    )

    links = {(item["kind"], item["source_label"], item["target_label"], item["asset"]): item for item in result["links"]}
    assert links[("transfer_match", "Binance", "Pionex", "USDT")]["value_eur"] == "100"
    assert links[("net_asset_reduce", "Asset USDT", "Pionex", "USDT")]["value_eur"] == "130"
    assert links[("net_asset_build", "Pionex", "Asset MXC", "MXC")]["value_eur"] == "80"
    assert links[("missing_opening_balance", "Unbelegter Startbestand", "Pionex", "USDT")]["value_eur"] == "150"


def test_portfolio_history_does_not_reuse_stale_non_stable_prices(monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "_load_token_aliases", lambda: {})

    events = [
        _event("btc-in", "binance", "2026-01-10T00:00:00+00:00", "deposit", "BTC", "in", "1"),
        _event("usdt-in", "binance", "2026-01-10T00:00:00+00:00", "deposit", "USDT", "in", "25"),
    ]
    points = dashboard._build_portfolio_value_history(
        events=events,
        ignored_mints=set(),
        runtime_fx=Decimal("1"),
        fx_rate_cache={},
        asset_usd_price_cache={},
        fx_lookup={
            ("BTC", "USD"): [("2021-12-31", Decimal("50000"))],
            ("USD", "EUR"): [("2026-01-10", Decimal("1"))],
        },
        interval="day",
        max_points=10,
    )

    assert points[-1]["value_usd"] == "25"
    assert points[-1]["priced_assets"] == 1
    assert points[-1]["unpriced_assets"] == 1


def test_portfolio_history_endpoint_uses_processing_effective_events(monkeypatch) -> None:
    events = [_event("usdt-in", "binance", "2026-01-10T00:00:00+00:00", "deposit", "USDT", "in", "25")]

    def fail_if_legacy_path_is_used() -> list[dict[str, Any]]:
        raise AssertionError("portfolio history must use processing-effective events")

    monkeypatch.setattr(dashboard, "_list_processing_effective_raw_events", lambda: events)
    monkeypatch.setattr(dashboard, "_list_effective_raw_events", fail_if_legacy_path_is_used)
    monkeypatch.setattr(dashboard, "_runtime_usd_to_eur_rate", lambda: Decimal("1"))
    monkeypatch.setattr(dashboard, "_load_ignored_tokens", lambda: {})
    monkeypatch.setattr(dashboard, "_load_fx_lookup", lambda: {("USD", "EUR"): [("2026-01-10", Decimal("1"))]})
    monkeypatch.setattr(dashboard, "_load_token_aliases", lambda: {})

    response = dashboard.dashboard_portfolio_history(window_days=0, year=2026, max_points=20)

    assert response.status == "success"
    assert response.data["summary"]["end_value_usd"] == "25"
