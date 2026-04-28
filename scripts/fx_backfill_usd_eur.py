#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx

from tax_engine.fx.service import FallbackFxResolver
from tax_engine.ingestion.store import STORE


def _date_iter(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def _fetch_frankfurter_timeseries(start: date, end: date, timeout_seconds: int) -> dict[str, Decimal]:
    url = f"https://api.frankfurter.dev/v1/{start.isoformat()}..{end.isoformat()}"
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(url, params={"base": "USD", "symbols": "EUR"})
        response.raise_for_status()
        payload = response.json()
    rates_obj = payload.get("rates") if isinstance(payload, dict) else {}
    result: dict[str, Decimal] = {}
    if not isinstance(rates_obj, dict):
        return result
    for day, row in rates_obj.items():
        if not isinstance(row, dict):
            continue
        raw = row.get("EUR")
        try:
            rate = Decimal(str(raw))
        except Exception:
            continue
        if rate <= 0:
            continue
        result[str(day)] = rate
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill USD->EUR FX cache into SQLite.")
    parser.add_argument("--start", default="2020-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=date.today().isoformat(), help="End date (YYYY-MM-DD)")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    start = datetime.fromisoformat(args.start).date()
    end = datetime.fromisoformat(args.end).date()
    if end < start:
        raise SystemExit("end must be >= start")

    STORE.initialize()
    resolver = FallbackFxResolver(timeout_seconds=args.timeout_seconds)

    total_days = 0
    created = 0
    from_timeseries = 0
    from_resolver = 0
    skipped_existing = 0
    unresolved = 0

    timeseries: dict[str, Decimal] = {}
    try:
        timeseries = _fetch_frankfurter_timeseries(start=start, end=end, timeout_seconds=args.timeout_seconds)
        print(f"[info] Frankfurter timeseries loaded: {len(timeseries)} business-day points")
    except Exception as exc:
        print(f"[warn] Frankfurter timeseries failed, fallback per-day resolver only: {exc}")

    # Wochenenden/Feiertage werden mit letztem bekannten Handelstag gefüllt.
    carry_rate: Decimal | None = None
    carry_source_date: str = ""
    for current in _date_iter(start, end):
        total_days += 1
        day = current.isoformat()
        existing = STORE.get_fx_rate(rate_date=day, base_ccy="USD", quote_ccy="EUR")
        if existing is not None and not args.force_refresh:
            skipped_existing += 1
            continue

        if day in timeseries:
            carry_rate = timeseries[day]
            carry_source_date = day
        if carry_rate is not None:
            STORE.upsert_fx_rate(
                rate_date=day,
                base_ccy="USD",
                quote_ccy="EUR",
                rate=carry_rate.to_eng_string(),
                source="frankfurter_timeseries",
                source_rate_date=carry_source_date or day,
            )
            created += 1
            from_timeseries += 1
            continue

        # Falls Timeseries den Anfang nicht liefert, per Resolver nachziehen.
        resolved = resolver.get_usd_to_eur_rate(day)
        if resolved is None:
            unresolved += 1
            continue
        STORE.upsert_fx_rate(
            rate_date=day,
            base_ccy="USD",
            quote_ccy="EUR",
            rate=resolved.rate.to_eng_string(),
            source=resolved.source,
            source_rate_date=resolved.source_rate_date,
        )
        created += 1
        from_resolver += 1
        carry_rate = resolved.rate
        carry_source_date = resolved.source_rate_date

    STORE.upsert_setting(
        setting_key="runtime.fx.backfill_status",
        value_json=(
            "{"
            f"\"start\":\"{start.isoformat()}\","
            f"\"end\":\"{end.isoformat()}\","
            f"\"updated_at_utc\":\"{datetime.now(UTC).isoformat()}\","
            f"\"total_days\":{total_days},"
            f"\"created\":{created},"
            f"\"skipped_existing\":{skipped_existing},"
            f"\"unresolved\":{unresolved}"
            "}"
        ),
        is_secret=False,
    )

    print(
        "[done] "
        f"range={start.isoformat()}..{end.isoformat()} total_days={total_days} "
        f"created={created} skipped_existing={skipped_existing} unresolved={unresolved} "
        f"from_timeseries={from_timeseries} from_resolver={from_resolver}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
