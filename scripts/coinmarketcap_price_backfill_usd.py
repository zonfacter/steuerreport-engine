#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx

from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions

COINMARKETCAP_HISTORICAL_URL = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/historical"
DEFAULT_CONFIG = Path("configs/crypto_price_sources.json")
EXAMPLE_CONFIG = Path("configs/crypto_price_sources.example.json")
STABLES = {"USD", "USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD"}


@dataclass(frozen=True)
class CmcPriceAsset:
    symbol: str
    coinmarketcap_id: str
    store_keys: tuple[str, ...]
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class CmcDailyPrice:
    rate_date: str
    close_usd: Decimal
    source_rate_date: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill historical crypto USD prices from CoinMarketCap public data API.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Price source config JSON")
    parser.add_argument("--start-date", default="2020-01-01", help="Inclusive YYYY-MM-DD")
    parser.add_argument("--end-date", default=datetime.utcnow().date().isoformat(), help="Inclusive YYYY-MM-DD")
    parser.add_argument("--assets", default="", help="Comma separated symbols/aliases; default all configured assets found in events")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--refresh", action="store_true", help="Overwrite existing cached prices")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    assets = load_cmc_assets(Path(args.config))
    alias_map = build_alias_map(assets)
    requested = {item.strip().upper() for item in args.assets.split(",") if item.strip()}
    jobs = collect_jobs(alias_map=alias_map, requested=requested, start_date=args.start_date, end_date=args.end_date)

    print(
        f"assets={len(jobs)} dates={sum(len(v) for v in jobs.values())} refresh={args.refresh} dry_run={args.dry_run}",
        flush=True,
    )
    completed = 0
    skipped_cached = 0
    missing_provider = 0
    failed_assets = 0
    with httpx.Client(timeout=args.timeout_seconds) as client:
        for asset, date_set in sorted(jobs.items(), key=lambda item: item[0].symbol):
            missing_dates = sorted(
                date_str
                for date_str in date_set
                if args.refresh or not has_cached_price(asset=asset, date_str=date_str)
            )
            skipped_cached += len(date_set) - len(missing_dates)
            if not missing_dates:
                continue
            if args.dry_run:
                print(
                    f"dry-run asset={asset.symbol} cmc_id={asset.coinmarketcap_id} "
                    f"dates={len(missing_dates)} range={missing_dates[0]}..{missing_dates[-1]}",
                    flush=True,
                )
                completed += len(missing_dates)
                continue
            try:
                history = fetch_cmc_history(
                    client=client,
                    coinmarketcap_id=asset.coinmarketcap_id,
                    start_date=missing_dates[0],
                    end_date=missing_dates[-1],
                )
            except httpx.HTTPError as exc:
                failed_assets += 1
                print(f"failed asset={asset.symbol} cmc_id={asset.coinmarketcap_id} error={exc}", flush=True)
                continue
            for date_str in missing_dates:
                price = history.get(date_str)
                if price is None:
                    missing_provider += 1
                    print(f"missing asset={asset.symbol} cmc_id={asset.coinmarketcap_id} date={date_str}", flush=True)
                    continue
                upsert_price(asset=asset, price=price)
                completed += 1
                print(
                    f"cached asset={asset.symbol} cmc_id={asset.coinmarketcap_id} "
                    f"date={date_str} usd={price.close_usd} keys={','.join(asset.store_keys)}",
                    flush=True,
                )

    print(
        f"done completed={completed} skipped_cached={skipped_cached} "
        f"missing_provider={missing_provider} failed_assets={failed_assets}",
        flush=True,
    )
    return 0


def load_cmc_assets(config_path: Path = DEFAULT_CONFIG) -> list[CmcPriceAsset]:
    path = config_path if config_path.exists() else EXAMPLE_CONFIG
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: list[CmcPriceAsset] = []
    for item in payload.get("assets", []):
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol", "")).upper().strip()
        coinmarketcap_id = str(item.get("coinmarketcap_id", "")).strip()
        store_keys = tuple(str(v).upper().strip() for v in item.get("store_keys", []) if str(v).strip())
        aliases = tuple(str(v).upper().strip() for v in item.get("aliases", []) if str(v).strip())
        if symbol and coinmarketcap_id and store_keys and aliases:
            result.append(
                CmcPriceAsset(
                    symbol=symbol,
                    coinmarketcap_id=coinmarketcap_id,
                    store_keys=store_keys,
                    aliases=aliases,
                )
            )
    return result


def build_alias_map(assets: list[CmcPriceAsset]) -> dict[str, CmcPriceAsset]:
    alias_map: dict[str, CmcPriceAsset] = {}
    for asset in assets:
        alias_map[asset.symbol] = asset
        for alias in asset.aliases:
            alias_map[alias] = asset
        for key in asset.store_keys:
            alias_map[key] = asset
    return alias_map


def collect_jobs(
    alias_map: dict[str, CmcPriceAsset],
    requested: set[str],
    start_date: str,
    end_date: str,
) -> dict[CmcPriceAsset, set[str]]:
    jobs: dict[CmcPriceAsset, set[str]] = {}
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


def fetch_cmc_history(
    client: httpx.Client,
    *,
    coinmarketcap_id: str,
    start_date: str,
    end_date: str,
) -> dict[str, CmcDailyPrice]:
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=UTC)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=UTC) + timedelta(days=1)
    response = client.get(
        COINMARKETCAP_HISTORICAL_URL,
        params={
            "id": coinmarketcap_id,
            "convertId": "2781",
            "timeStart": int(start_dt.timestamp()),
            "timeEnd": int(end_dt.timestamp()),
        },
        headers={"accept": "application/json", "user-agent": "steuerreport-engine/0.1"},
    )
    if response.status_code in {401, 403, 404, 429}:
        return {}
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") if isinstance(payload, dict) else None
    quotes = data.get("quotes") if isinstance(data, dict) else None
    if not isinstance(quotes, list):
        return {}
    prices: dict[str, CmcDailyPrice] = {}
    for item in quotes:
        if not isinstance(item, dict):
            continue
        quote = item.get("quote")
        usd = quote.get("close") if isinstance(quote, dict) else None
        close = _to_decimal(usd)
        if close <= 0:
            continue
        timestamp_raw = str((quote or {}).get("timestamp") or item.get("timeClose") or "")
        try:
            day = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            continue
        prices[day] = CmcDailyPrice(rate_date=day, close_usd=close, source_rate_date=day)
    return prices


def has_cached_price(asset: CmcPriceAsset, date_str: str) -> bool:
    for key in asset.store_keys:
        row = STORE.get_fx_rate(rate_date=date_str, base_ccy=key, quote_ccy="USD")
        if row and _to_decimal(row.get("rate")) > 0:
            return True
    return False


def upsert_price(asset: CmcPriceAsset, price: CmcDailyPrice) -> None:
    for key in asset.store_keys:
        STORE.upsert_fx_rate(
            rate_date=price.rate_date,
            base_ccy=key.upper(),
            quote_ccy="USD",
            rate=price.close_usd.to_eng_string(),
            source=f"coinmarketcap_public_historical:{asset.symbol.lower()}",
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


if __name__ == "__main__":
    raise SystemExit(main())
