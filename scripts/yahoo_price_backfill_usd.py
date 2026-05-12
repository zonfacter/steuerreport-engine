#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import httpx

from tax_engine.fx.yahoo_prices import (
    DEFAULT_CONFIG,
    build_yahoo_alias_map,
    collect_yahoo_jobs,
    fetch_yahoo_history,
    has_cached_price,
    load_yahoo_assets,
    upsert_yahoo_price,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill historical crypto USD prices from Yahoo Finance.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Price source config JSON")
    parser.add_argument("--start-date", default="2020-01-01", help="Inclusive YYYY-MM-DD")
    parser.add_argument("--end-date", default=datetime.utcnow().date().isoformat(), help="Inclusive YYYY-MM-DD")
    parser.add_argument("--assets", default="", help="Comma separated symbols/aliases; default all configured Yahoo assets found in events")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--refresh", action="store_true", help="Overwrite existing cached prices")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    assets = load_yahoo_assets(Path(args.config))
    alias_map = build_yahoo_alias_map(assets)
    requested = {item.strip().upper() for item in args.assets.split(",") if item.strip()}
    jobs = collect_yahoo_jobs(
        alias_map=alias_map,
        requested=requested,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    date_count = sum(len(dates) for dates in jobs.values())
    print(
        f"assets={len(jobs)} dates={date_count} refresh={args.refresh} dry_run={args.dry_run}",
        flush=True,
    )

    attempted_assets = 0
    completed = 0
    skipped_cached = 0
    missing_provider = 0
    failed_assets = 0
    with httpx.Client(timeout=args.timeout_seconds) as client:
        for asset, needed_dates in sorted(jobs.items(), key=lambda item: item[0].symbol):
            dates = sorted(needed_dates)
            if not dates:
                continue
            fetch_dates = [
                date_str
                for date_str in dates
                if args.refresh or not has_cached_price(asset=asset, date_str=date_str)
            ]
            skipped_cached += len(dates) - len(fetch_dates)
            if not fetch_dates:
                continue
            attempted_assets += 1
            if args.dry_run:
                print(
                    f"dry-run asset={asset.symbol} ticker={asset.yahoo_ticker} dates={len(fetch_dates)} "
                    f"range={fetch_dates[0]}..{fetch_dates[-1]}",
                    flush=True,
                )
                completed += len(fetch_dates)
                continue
            try:
                history = fetch_yahoo_history(
                    client,
                    ticker=asset.yahoo_ticker,
                    start_date=fetch_dates[0],
                    end_date=fetch_dates[-1],
                )
            except Exception as exc:  # noqa: BLE001
                failed_assets += 1
                print(f"failed asset={asset.symbol} ticker={asset.yahoo_ticker} error={type(exc).__name__}", flush=True)
                continue
            for date_str in fetch_dates:
                price = history.get(date_str)
                if price is None:
                    missing_provider += 1
                    print(f"missing asset={asset.symbol} ticker={asset.yahoo_ticker} date={date_str}", flush=True)
                    continue
                upsert_yahoo_price(asset=asset, price=price)
                completed += 1
                print(
                    f"cached asset={asset.symbol} ticker={asset.yahoo_ticker} date={date_str} "
                    f"usd={price.close_usd} keys={','.join(asset.store_keys)}",
                    flush=True,
                )

    print(
        "done "
        f"attempted_assets={attempted_assets} completed={completed} skipped_cached={skipped_cached} "
        f"missing_provider={missing_provider} failed_assets={failed_assets}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
