#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from tax_engine.ingestion.store import STORE


def main() -> int:
    parser = argparse.ArgumentParser(description="Import manual OHLCV CSV close prices into fx_cache.")
    parser.add_argument("--csv", required=True, help="CSV path exported from Kaggle/Yahoo/CoinMarketCap")
    parser.add_argument("--asset", required=True, help="Base asset symbol, e.g. SOL or HNT")
    parser.add_argument("--store-keys", default="", help="Comma separated additional store keys/mints")
    parser.add_argument("--quote", default="USD", help="Quote currency, default USD")
    parser.add_argument("--source", required=True, help="Audit source label, e.g. kaggle:dataset-slug")
    parser.add_argument("--date-column", default="Date", help="Date column name")
    parser.add_argument("--close-column", default="Close", help="Close price column name")
    parser.add_argument(
        "--timestamp-unit",
        choices=["auto", "s", "ms"],
        default="auto",
        help="Use when the date column contains UNIX timestamps",
    )
    parser.add_argument("--refresh", action="store_true", help="Overwrite existing cached prices")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    asset = str(args.asset).upper().strip()
    quote = str(args.quote).upper().strip()
    store_keys = [asset]
    for item in args.store_keys.split(","):
        key = item.upper().strip()
        if key and key not in store_keys:
            store_keys.append(key)
    source = f"manual_ohlcv_csv:{args.source.strip()}"

    read_rows = 0
    imported = 0
    skipped_existing = 0
    skipped_invalid = 0
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            read_rows += 1
            date_str = _parse_date(row.get(args.date_column), timestamp_unit=args.timestamp_unit)
            close = _to_decimal(row.get(args.close_column))
            if not date_str or close <= 0:
                skipped_invalid += 1
                continue
            if not args.refresh and _has_any_cached_price(store_keys, quote=quote, rate_date=date_str):
                skipped_existing += 1
                continue
            if args.dry_run:
                imported += 1
                continue
            for key in store_keys:
                STORE.upsert_fx_rate(
                    rate_date=date_str,
                    base_ccy=key,
                    quote_ccy=quote,
                    rate=close.to_eng_string(),
                    source=source,
                    source_rate_date=date_str,
                )
            imported += 1

    print(
        "done "
        f"rows={read_rows} imported={imported} skipped_existing={skipped_existing} "
        f"skipped_invalid={skipped_invalid} asset={asset} quote={quote} source={source}",
        flush=True,
    )
    return 0


def _has_any_cached_price(store_keys: list[str], *, quote: str, rate_date: str) -> bool:
    for key in store_keys:
        row = STORE.get_fx_rate(rate_date=rate_date, base_ccy=key, quote_ccy=quote)
        if row and _to_decimal(row.get("rate")) > 0:
            return True
    return False


def _parse_date(value: Any, *, timestamp_unit: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.isdigit():
        timestamp = int(raw)
        if timestamp_unit == "ms" or (timestamp_unit == "auto" and timestamp > 10_000_000_000):
            timestamp = timestamp // 1000
        return datetime.fromtimestamp(timestamp, tz=UTC).date().isoformat()
    normalized = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date().isoformat()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def _to_decimal(value: Any) -> Decimal:
    raw = str(value or "").strip().replace(",", "")
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return Decimal("0")


if __name__ == "__main__":
    raise SystemExit(main())
