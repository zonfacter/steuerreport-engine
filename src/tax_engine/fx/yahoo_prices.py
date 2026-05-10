from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx

from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions

YAHOO_CHART_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
DEFAULT_CONFIG = Path("configs/crypto_price_sources.json")
EXAMPLE_CONFIG = Path("configs/crypto_price_sources.example.json")
STABLES = {"USD", "USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD"}


@dataclass(frozen=True)
class YahooPriceAsset:
    symbol: str
    yahoo_ticker: str
    store_keys: tuple[str, ...]
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class YahooDailyPrice:
    rate_date: str
    close_usd: Decimal
    source_rate_date: str


def load_yahoo_assets(config_path: Path = DEFAULT_CONFIG) -> list[YahooPriceAsset]:
    path = config_path if config_path.exists() else EXAMPLE_CONFIG
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: list[YahooPriceAsset] = []
    for item in payload.get("assets", []):
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol", "")).upper().strip()
        yahoo_ticker = str(item.get("yahoo_ticker", "")).upper().strip()
        store_keys = tuple(str(v).upper().strip() for v in item.get("store_keys", []) if str(v).strip())
        aliases = tuple(str(v).upper().strip() for v in item.get("aliases", []) if str(v).strip())
        if symbol and yahoo_ticker and store_keys and aliases:
            result.append(
                YahooPriceAsset(
                    symbol=symbol,
                    yahoo_ticker=yahoo_ticker,
                    store_keys=store_keys,
                    aliases=aliases,
                )
            )
    return result


def build_yahoo_alias_map(assets: list[YahooPriceAsset]) -> dict[str, YahooPriceAsset]:
    alias_map: dict[str, YahooPriceAsset] = {}
    for asset in assets:
        alias_map[asset.symbol] = asset
        for alias in asset.aliases:
            alias_map[alias] = asset
        for key in asset.store_keys:
            alias_map[key] = asset
    return alias_map


def collect_yahoo_jobs(
    alias_map: dict[str, YahooPriceAsset],
    requested: set[str],
    start_date: str,
    end_date: str,
) -> dict[YahooPriceAsset, set[str]]:
    jobs: dict[YahooPriceAsset, set[str]] = {}
    events, _summary = apply_review_actions(STORE.list_raw_events())
    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        date_str = _event_date(payload)
        if not date_str or date_str < start_date or date_str > end_date:
            continue
        asset_key = str(payload.get("asset", "")).upper().strip()
        if not asset_key or asset_key in STABLES:
            continue
        asset = alias_map.get(asset_key)
        if asset is None:
            continue
        if requested and asset.symbol not in requested and asset_key not in requested:
            continue
        jobs.setdefault(asset, set()).add(date_str)
    return jobs


def fetch_yahoo_history(
    client: httpx.Client,
    *,
    ticker: str,
    start_date: str,
    end_date: str,
) -> dict[str, YahooDailyPrice]:
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=UTC)
    # Yahoo period2 is exclusive; include the full requested end date.
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=UTC) + timedelta(days=1)
    response = client.get(
        f"{YAHOO_CHART_BASE_URL}/{ticker}",
        params={
            "period1": int(start_dt.timestamp()),
            "period2": int(end_dt.timestamp()),
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        },
        headers={"accept": "application/json", "user-agent": "steuerreport-engine/0.1"},
    )
    if response.status_code in {401, 403, 404, 429}:
        return {}
    response.raise_for_status()
    payload = response.json()
    chart = payload.get("chart") if isinstance(payload, dict) else None
    result_rows = chart.get("result") if isinstance(chart, dict) else None
    if not isinstance(result_rows, list) or not result_rows:
        return {}
    first = result_rows[0]
    if not isinstance(first, dict):
        return {}
    timestamps = first.get("timestamp")
    indicators = first.get("indicators")
    quote_rows = indicators.get("quote") if isinstance(indicators, dict) else None
    quote = quote_rows[0] if isinstance(quote_rows, list) and quote_rows else None
    if not isinstance(timestamps, list) or not isinstance(quote, dict):
        return {}
    closes = quote.get("close")
    if not isinstance(closes, list):
        return {}

    prices: dict[str, YahooDailyPrice] = {}
    for timestamp, close in zip(timestamps, closes, strict=False):
        price = _to_decimal(close)
        if price <= 0:
            continue
        try:
            day = datetime.fromtimestamp(int(timestamp), tz=UTC).date().isoformat()
        except (TypeError, ValueError, OSError):
            continue
        prices[day] = YahooDailyPrice(rate_date=day, close_usd=price, source_rate_date=day)
    return prices


def has_cached_price(asset: YahooPriceAsset, date_str: str) -> bool:
    for key in asset.store_keys:
        row = STORE.get_fx_rate(rate_date=date_str, base_ccy=key, quote_ccy="USD")
        if row and _to_decimal(row.get("rate")) > 0:
            return True
    return False


def upsert_yahoo_price(asset: YahooPriceAsset, price: YahooDailyPrice) -> None:
    for key in asset.store_keys:
        STORE.upsert_fx_rate(
            rate_date=price.rate_date,
            base_ccy=key.upper(),
            quote_ccy="USD",
            rate=price.close_usd.to_eng_string(),
            source=f"yahoo_finance_history:{asset.yahoo_ticker}",
            source_rate_date=price.source_rate_date,
        )


def _event_date(payload: dict[str, Any]) -> str:
    raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    return raw[:10] if len(raw) >= 10 else ""


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")
