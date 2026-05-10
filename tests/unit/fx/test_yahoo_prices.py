from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import httpx

from tax_engine.fx.yahoo_prices import (
    YahooDailyPrice,
    YahooPriceAsset,
    build_yahoo_alias_map,
    collect_yahoo_jobs,
    fetch_yahoo_history,
    has_cached_price,
    load_yahoo_assets,
    upsert_yahoo_price,
)
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_load_yahoo_assets_requires_explicit_ticker(tmp_path: Path) -> None:
    config = tmp_path / "prices.json"
    config.write_text(
        json.dumps(
            {
                "assets": [
                    {
                        "symbol": "SOL",
                        "coingecko_id": "solana",
                        "yahoo_ticker": "SOL-USD",
                        "store_keys": ["SOL"],
                        "aliases": ["SOL"],
                    },
                    {
                        "symbol": "IOT",
                        "coingecko_id": "helium-iot",
                        "store_keys": ["IOT"],
                        "aliases": ["IOT"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    assets = load_yahoo_assets(config)

    assert assets == [
        YahooPriceAsset(symbol="SOL", yahoo_ticker="SOL-USD", store_keys=("SOL",), aliases=("SOL",))
    ]


def test_fetch_yahoo_history_parses_daily_close() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/SOL-USD")
        return httpx.Response(
            200,
            json={
                "chart": {
                    "result": [
                        {
                            "timestamp": [1704067200, 1704153600, 1704240000],
                            "indicators": {"quote": [{"close": [101.25, None, 98.125]}]},
                        }
                    ]
                }
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))

    prices = fetch_yahoo_history(
        client,
        ticker="SOL-USD",
        start_date="2024-01-01",
        end_date="2024-01-03",
    )

    assert prices["2024-01-01"].close_usd == Decimal("101.25")
    assert "2024-01-02" not in prices
    assert prices["2024-01-03"].close_usd == Decimal("98.125")


def test_collect_jobs_and_cache_write_preserve_existing_prices() -> None:
    _reset_store()
    STORE.upsert_source_file(source_file_id="src", source_name="test", source_hash="hash", row_count=2)
    STORE.insert_raw_event(
        unique_event_id="evt-sol",
        source_file_id="src",
        row_index=1,
        payload_json=json.dumps({"timestamp_utc": "2024-01-01T00:00:00Z", "asset": "SOL"}),
    )
    STORE.insert_raw_event(
        unique_event_id="evt-usdc",
        source_file_id="src",
        row_index=2,
        payload_json=json.dumps({"timestamp_utc": "2024-01-01T00:00:00Z", "asset": "USDC"}),
    )
    asset = YahooPriceAsset(
        symbol="SOL",
        yahoo_ticker="SOL-USD",
        store_keys=("SOL", "SO11111111111111111111111111111111111111112"),
        aliases=("SOL", "SO11111111111111111111111111111111111111112"),
    )
    alias_map = build_yahoo_alias_map([asset])

    jobs = collect_yahoo_jobs(
        alias_map=alias_map,
        requested=set(),
        start_date="2024-01-01",
        end_date="2024-01-01",
    )

    assert jobs == {asset: {"2024-01-01"}}
    assert has_cached_price(asset, "2024-01-01") is False

    upsert_yahoo_price(
        asset,
        YahooDailyPrice(
            rate_date="2024-01-01",
            close_usd=Decimal("101.25"),
            source_rate_date="2024-01-01",
        ),
    )

    row = STORE.get_fx_rate(rate_date="2024-01-01", base_ccy="SOL", quote_ccy="USD")
    assert row is not None
    assert row["rate"] == "101.25"
    assert row["source"] == "yahoo_finance_history:SOL-USD"
    assert has_cached_price(asset, "2024-01-01") is True
