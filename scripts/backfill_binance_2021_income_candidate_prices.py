#!/usr/bin/env python3
"""Backfill Yahoo USD prices needed by reviewed Binance 2021 income candidates."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from import_binance_2021_account_statement_income import build_rows

from tax_engine.fx.yahoo_prices import (
    build_yahoo_alias_map,
    fetch_yahoo_history,
    load_yahoo_assets,
    upsert_yahoo_price,
)

CREATED_DATE = "2026-05-09"
JSON_PATH = ROOT / "var" / f"binance_2021_income_candidate_price_backfill_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"103_BINANCE_2021_INCOME_CANDIDATE_PRICE_BACKFILL_{CREATED_DATE}.md"
DEFAULT_ASSETS = {"ADA", "DOGE"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", default="ADA,DOGE", help="Comma-separated configured Yahoo symbols to backfill.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    args = parser.parse_args()

    requested = {item.strip().upper() for item in args.assets.split(",") if item.strip()} or DEFAULT_ASSETS
    assets = load_yahoo_assets()
    alias_map = build_yahoo_alias_map(assets)
    needed_dates = collect_needed_dates(requested)
    results = []
    with httpx.Client(timeout=args.timeout_seconds) as client:
        for symbol in sorted(needed_dates):
            asset = alias_map.get(symbol)
            dates = sorted(needed_dates[symbol])
            if asset is None or not dates:
                results.append({"symbol": symbol, "status": "missing_config", "dates": len(dates)})
                continue
            if args.dry_run:
                results.append(
                    {
                        "symbol": symbol,
                        "ticker": asset.yahoo_ticker,
                        "status": "dry_run",
                        "dates": len(dates),
                        "first_date": dates[0],
                        "last_date": dates[-1],
                    }
                )
                continue
            history = fetch_yahoo_history(client, ticker=asset.yahoo_ticker, start_date=dates[0], end_date=dates[-1])
            cached = 0
            missing = []
            for date_str in dates:
                price = history.get(date_str)
                if price is None:
                    missing.append(date_str)
                    continue
                upsert_yahoo_price(asset=asset, price=price)
                cached += 1
            results.append(
                {
                    "symbol": symbol,
                    "ticker": asset.yahoo_ticker,
                    "status": "ok",
                    "dates": len(dates),
                    "cached": cached,
                    "missing": missing,
                    "first_date": dates[0],
                    "last_date": dates[-1],
                }
            )
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "dry_run": bool(args.dry_run),
        "requested_assets": sorted(requested),
        "results": results,
        "interpretation": [
            "This backfill is restricted to configured Yahoo tickers needed by the reviewed Binance 2021 income candidates.",
            "NFT/APENFT is intentionally excluded here because the Binance symbol needs explicit mapping before automated price use.",
        ],
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "results": results}, ensure_ascii=False, indent=2))
    return 0


def collect_needed_dates(requested: set[str]) -> dict[str, set[str]]:
    dates: dict[str, set[str]] = {}
    for row in build_rows():
        asset = str(row.get("asset") or "").upper().strip()
        if asset not in requested:
            continue
        date = str(row.get("timestamp_utc") or "")[:10]
        if len(date) == 10:
            dates.setdefault(asset, set()).add(date)
    return dates


def render_doc(audit: dict[str, object]) -> str:
    lines = [
        "# Binance 2021 Income Candidate Price Backfill - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Gezielter Yahoo-Preisbackfill fuer bewertbare Binance-2021-Ertragskandidaten vor Importentscheidung.",
        "",
        f"- Dry Run: `{audit['dry_run']}`",
        f"- Assets: `{audit['requested_assets']}`",
        "",
        "## Ergebnis",
        "",
    ]
    for item in audit["results"]:  # type: ignore[index]
        lines.append(f"- `{item}`")
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {line}" for line in audit["interpretation"])  # type: ignore[index]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
