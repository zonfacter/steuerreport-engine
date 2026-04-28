from __future__ import annotations

from decimal import Decimal

from tax_engine.fx.service import FallbackFxResolver, FxResolveResult
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_enrich_events_converts_usd_fields(monkeypatch) -> None:
    _reset_store()

    def _fake_rate(self: FallbackFxResolver, rate_date: str) -> FxResolveResult | None:
        return FxResolveResult(
            rate_date=rate_date,
            source_rate_date=rate_date,
            rate=Decimal("0.9"),
            source="test",
            from_cache=False,
        )

    monkeypatch.setattr(FallbackFxResolver, "get_usd_to_eur_rate", _fake_rate)
    resolver = FallbackFxResolver()
    events = [
        {
            "unique_event_id": "evt-1",
            "payload": {
                "timestamp_utc": "2026-01-02T12:00:00Z",
                "asset": "BTC",
                "side": "buy",
                "amount": "1",
                "price": "100",
                "quote_asset": "USDT",
                "fee": "2",
                "fee_asset": "USD",
                "amount_usd": "100",
            },
        }
    ]

    enriched, summary = resolver.enrich_events_with_fx(events)
    payload = enriched[0]["payload"]
    assert payload["price_eur"] == "90.0"
    assert payload["fee_eur"] == "1.8"
    assert payload["amount_eur"] == "90.0"
    assert payload["fx_rate_usd_eur"] == "0.9"
    assert summary["converted_event_count"] == 1
    assert summary["unresolved_count"] == 0


def test_enrich_events_marks_unresolved_when_rate_missing(monkeypatch) -> None:
    _reset_store()

    monkeypatch.setattr(FallbackFxResolver, "get_usd_to_eur_rate", lambda self, rate_date: None)
    resolver = FallbackFxResolver()
    events = [
        {
            "unique_event_id": "evt-missing-fx",
            "payload": {
                "timestamp_utc": "2026-01-03T12:00:00Z",
                "asset": "ETH",
                "side": "buy",
                "amount": "1",
                "price": "3000",
                "quote_asset": "USD",
            },
        }
    ]
    _, summary = resolver.enrich_events_with_fx(events)
    assert summary["converted_event_count"] == 0
    assert summary["unresolved_count"] == 1
    unresolved = summary["unresolved_events"][0]
    assert unresolved["source_event_id"] == "evt-missing-fx"


def test_enrich_events_uses_fallback_rate_when_api_unavailable(monkeypatch) -> None:
    _reset_store()

    monkeypatch.setattr(FallbackFxResolver, "_fetch_frankfurter", lambda self, rate_date: None)
    monkeypatch.setattr(FallbackFxResolver, "_fetch_ecb_csv", lambda self, rate_date: None)
    resolver = FallbackFxResolver(fallback_rate="0.92")
    events = [
        {
            "unique_event_id": "evt-fallback",
            "payload": {
                "timestamp_utc": "2026-02-01T12:00:00Z",
                "asset": "ETH",
                "side": "buy",
                "amount": "1",
                "price_usd": "100",
                "quote_asset": "USD",
            },
        }
    ]

    enriched, summary = resolver.enrich_events_with_fx(events)
    payload = enriched[0]["payload"]
    assert summary["converted_event_count"] == 1
    assert summary["unresolved_count"] == 0
    assert payload["price_eur"] == "92.00"
    assert payload["fx_rate_usd_eur"] == "0.92"
