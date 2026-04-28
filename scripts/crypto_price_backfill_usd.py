#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx

from tax_engine.admin import resolve_secret_value
from tax_engine.ingestion.store import STORE

COINGECKO_DEMO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_PRO_BASE_URL = "https://pro-api.coingecko.com/api/v3"
DEFILLAMA_COINS_BASE_URL = "https://coins.llama.fi"
DEFAULT_CONFIG = Path("configs/crypto_price_sources.json")
EXAMPLE_CONFIG = Path("configs/crypto_price_sources.example.json")
STABLES = {"USD", "USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD"}


@dataclass(frozen=True)
class PriceAsset:
    symbol: str
    coingecko_id: str
    store_keys: tuple[str, ...]
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class PriceResult:
    price: Decimal
    source: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill historical crypto USD prices into fx_cache.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Price source config JSON")
    parser.add_argument("--start-date", default="2020-01-01", help="Inclusive YYYY-MM-DD")
    parser.add_argument("--end-date", default=datetime.utcnow().date().isoformat(), help="Inclusive YYYY-MM-DD")
    parser.add_argument("--assets", default="", help="Comma separated symbols/aliases; default all configured assets found in events")
    parser.add_argument("--max-requests", type=int, default=250, help="Safety limit for one run")
    parser.add_argument("--sleep-seconds", type=float, default=7.0, help="Delay between provider calls")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument(
        "--provider",
        choices=["auto", "coingecko", "defillama"],
        default="auto",
        help="Price provider strategy. auto uses CoinGecko when allowed and DefiLlama as fallback.",
    )
    parser.add_argument("--refresh", action="store_true", help="Overwrite existing cached prices")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    assets = _load_assets(Path(args.config))
    alias_map = _build_alias_map(assets)
    requested = {item.strip().upper() for item in args.assets.split(",") if item.strip()}
    jobs = _collect_jobs(alias_map=alias_map, requested=requested, start_date=args.start_date, end_date=args.end_date)
    print(f"jobs={len(jobs)} max_requests={args.max_requests} dry_run={args.dry_run}", flush=True)

    attempted = 0
    completed = 0
    skipped_cached = 0
    failed = 0
    with httpx.Client(timeout=args.timeout_seconds) as client:
        for asset, date_str in jobs:
            if attempted >= args.max_requests:
                print("max_requests reached", flush=True)
                break
            if not args.refresh and _has_cached_price(asset=asset, date_str=date_str):
                skipped_cached += 1
                continue
            if args.dry_run:
                print(f"dry-run asset={asset.symbol} date={date_str} id={asset.coingecko_id}", flush=True)
                attempted += 1
                completed += 1
                continue
            result = _fetch_history_price(client=client, asset=asset, date_str=date_str, provider=args.provider)
            attempted += 1
            if result.price <= 0:
                failed += 1
                print(f"failed asset={asset.symbol} date={date_str} id={asset.coingecko_id}", flush=True)
                time.sleep(max(args.sleep_seconds, 0))
                continue
            for key in asset.store_keys:
                STORE.upsert_fx_rate(
                    rate_date=date_str,
                    base_ccy=key.upper(),
                    quote_ccy="USD",
                    rate=result.price.to_eng_string(),
                    source=result.source,
                    source_rate_date=date_str,
                )
            completed += 1
            print(
                f"cached asset={asset.symbol} date={date_str} usd={result.price} "
                f"source={result.source} keys={','.join(asset.store_keys)}",
                flush=True,
            )
            time.sleep(max(args.sleep_seconds, 0))

    print(f"done attempted={attempted} completed={completed} skipped_cached={skipped_cached} failed={failed}", flush=True)
    return 0


def _load_assets(config_path: Path) -> list[PriceAsset]:
    path = config_path if config_path.exists() else EXAMPLE_CONFIG
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: list[PriceAsset] = []
    for item in payload.get("assets", []):
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol", "")).upper().strip()
        coingecko_id = str(item.get("coingecko_id", "")).strip()
        store_keys = tuple(str(v).upper().strip() for v in item.get("store_keys", []) if str(v).strip())
        aliases = tuple(str(v).upper().strip() for v in item.get("aliases", []) if str(v).strip())
        if symbol and coingecko_id and store_keys and aliases:
            result.append(PriceAsset(symbol=symbol, coingecko_id=coingecko_id, store_keys=store_keys, aliases=aliases))
    return result


def _build_alias_map(assets: list[PriceAsset]) -> dict[str, PriceAsset]:
    alias_map: dict[str, PriceAsset] = {}
    for asset in assets:
        alias_map[asset.symbol] = asset
        for alias in asset.aliases:
            alias_map[alias] = asset
        for key in asset.store_keys:
            alias_map[key] = asset
    return alias_map


def _collect_jobs(alias_map: dict[str, PriceAsset], requested: set[str], start_date: str, end_date: str) -> list[tuple[PriceAsset, str]]:
    jobs: set[tuple[str, str]] = set()
    by_symbol = {asset.symbol: asset for asset in alias_map.values()}
    for row in STORE.list_raw_events():
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
        jobs.add((asset.symbol, date_str))
    return [(by_symbol[symbol], date_str) for symbol, date_str in sorted(jobs, key=lambda item: (item[1], item[0]))]


def _event_date(payload: dict[str, Any]) -> str:
    raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    return raw[:10] if len(raw) >= 10 else ""


def _has_cached_price(asset: PriceAsset, date_str: str) -> bool:
    for key in asset.store_keys:
        row = STORE.get_fx_rate(rate_date=date_str, base_ccy=key, quote_ccy="USD")
        if row and _to_decimal(row.get("rate")) > 0:
            return True
    return False


def _fetch_history_price(client: httpx.Client, asset: PriceAsset, date_str: str, provider: str) -> PriceResult:
    if provider != "defillama" and not _should_skip_coingecko_history(date_str):
        price = _fetch_coingecko_history_price(client=client, coin_id=asset.coingecko_id, date_str=date_str)
        if price > 0:
            return PriceResult(price=price, source="coingecko_history")
    if provider != "coingecko":
        price = _fetch_defillama_history_price(client=client, token_id=f"coingecko:{asset.coingecko_id}", date_str=date_str)
        if price > 0:
            return PriceResult(price=price, source="defillama_coingecko_history")
    return PriceResult(price=Decimal("0"), source="")


def _should_skip_coingecko_history(date_str: str) -> bool:
    if _coingecko_plan() != "demo":
        return False
    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    return (date.today() - dt).days > 365


def _fetch_coingecko_history_price(client: httpx.Client, coin_id: str, date_str: str) -> Decimal:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    plan = _coingecko_plan()
    base_url = COINGECKO_PRO_BASE_URL if plan == "pro" else COINGECKO_DEMO_BASE_URL
    response = client.get(
        f"{base_url}/coins/{coin_id}/history",
        params={"date": dt.strftime("%d-%m-%Y"), "localization": "false"},
        headers=_coingecko_headers(plan),
    )
    if response.status_code == 429:
        retry_after = _to_decimal(response.headers.get("Retry-After"))
        if retry_after > 0:
            time.sleep(float(retry_after))
        return Decimal("0")
    if response.status_code in {401, 403}:
        return Decimal("0")
    response.raise_for_status()
    data = response.json()
    status = data.get("status") if isinstance(data, dict) else None
    if isinstance(status, dict) and status.get("error_code"):
        return Decimal("0")
    market_data = data.get("market_data") if isinstance(data, dict) else None
    current_price = market_data.get("current_price") if isinstance(market_data, dict) else None
    if not isinstance(current_price, dict):
        return Decimal("0")
    return _to_decimal(current_price.get("usd"))


def _fetch_defillama_history_price(client: httpx.Client, token_id: str, date_str: str) -> Decimal:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    timestamp = int(dt.replace(tzinfo=UTC).timestamp())
    response = client.get(
        f"{DEFILLAMA_COINS_BASE_URL}/prices/historical/{timestamp}/{token_id}",
        headers={"accept": "application/json", "user-agent": "steuerreport-engine/0.1"},
    )
    if response.status_code == 429:
        retry_after = _to_decimal(response.headers.get("Retry-After"))
        if retry_after > 0:
            time.sleep(float(retry_after))
        return Decimal("0")
    if response.status_code >= 500:
        return Decimal("0")
    response.raise_for_status()
    data = response.json()
    coins = data.get("coins") if isinstance(data, dict) else None
    coin = coins.get(token_id) if isinstance(coins, dict) else None
    if not isinstance(coin, dict):
        return Decimal("0")
    return _to_decimal(coin.get("price"))


def _coingecko_headers(plan: str) -> dict[str, str]:
    headers = {"accept": "application/json", "user-agent": "steuerreport-engine/0.1"}
    demo_key = os.getenv("COINGECKO_DEMO_API_KEY", "").strip() or _stored_coingecko_key()
    pro_key = os.getenv("COINGECKO_PRO_API_KEY", "").strip()
    if plan == "pro" and pro_key:
        headers["x-cg-pro-api-key"] = pro_key
    elif plan == "pro" and demo_key:
        # Falls der Nutzer einen Pro-Key in der Admin-UI statt per Env gespeichert hat.
        headers["x-cg-pro-api-key"] = demo_key
    elif demo_key:
        headers["x-cg-demo-api-key"] = demo_key
    return headers


def _coingecko_plan() -> str:
    raw = os.getenv("COINGECKO_PLAN", "").strip().lower()
    if raw not in {"demo", "pro"}:
        row = STORE.get_setting("runtime.coingecko.plan")
        if row is not None:
            try:
                loaded = json.loads(str(row["value_json"]))
                raw = str(loaded).strip().lower()
            except json.JSONDecodeError:
                raw = ""
    return raw if raw in {"demo", "pro"} else "demo"


def _stored_coingecko_key() -> str:
    try:
        return str(resolve_secret_value("secret.coingecko.api_key")).strip()
    except Exception:
        return ""


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


if __name__ == "__main__":
    raise SystemExit(main())
