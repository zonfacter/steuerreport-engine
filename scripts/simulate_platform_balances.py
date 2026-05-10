#!/usr/bin/env python3
"""Simulate chronological balances per platform and asset from the platform ledger."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CREATED_DATE = "2026-05-09"
LEDGER_JSONL = ROOT / "var" / f"platform_ledger_{CREATED_DATE}.jsonl"
OUTPUT_JSON = ROOT / "var" / f"platform_balance_simulation_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"132_PLATFORM_BALANCE_SIMULATION_{CREATED_DATE}.md"
DUST_THRESHOLD = Decimal("0.000001")


def main() -> None:
    rows = load_ledger()
    rows.sort(key=lambda row: (effective_timestamp(row), row.get("timestamp_utc", ""), row.get("ledger_id", "")))
    balances: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    stats: dict[tuple[str, str], dict[str, Any]] = {}
    yearly_net: dict[tuple[str, str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    timeline_breaks: list[dict[str, Any]] = []

    for row in rows:
        key = (row.get("platform", "unknown"), row.get("asset", ""))
        delta = Decimal(str(row.get("quantity_delta") or "0"))
        before = balances[key]
        after = before + delta
        balances[key] = after
        stat = stats.setdefault(
            key,
            {
                "platform": key[0],
                "asset": key[1],
                "event_count": 0,
                "first_timestamp_utc": row.get("timestamp_utc", ""),
                "first_normalized_timestamp_utc": effective_timestamp(row),
                "last_timestamp_utc": row.get("timestamp_utc", ""),
                "last_normalized_timestamp_utc": effective_timestamp(row),
                "final_balance": Decimal("0"),
                "worst_balance": Decimal("0"),
                "first_negative": None,
                "last_event": None,
            },
        )
        stat["event_count"] += 1
        stat["last_timestamp_utc"] = row.get("timestamp_utc", "")
        stat["last_normalized_timestamp_utc"] = effective_timestamp(row)
        stat["final_balance"] = after
        if after < stat["worst_balance"]:
            stat["worst_balance"] = after
        if after < -DUST_THRESHOLD and stat["first_negative"] is None:
            first = slim_event(row, before, after)
            stat["first_negative"] = first
            timeline_breaks.append(first)
        stat["last_event"] = slim_event(row, before, after)
        year = str(row.get("year") or row.get("timestamp_utc", "")[:4] or "unknown")
        yearly_net[(key[0], key[1], year)] += delta

    assets = [serialize_stat(stat, yearly_net) for stat in stats.values()]
    negatives = [
        row
        for row in assets
        if Decimal(str(row["worst_balance"])) < -DUST_THRESHOLD or Decimal(str(row["final_balance"])) < -DUST_THRESHOLD
    ]
    negatives.sort(key=lambda row: (Decimal(str(row["worst_balance"])), row["platform"], row["asset"]))
    assets.sort(key=lambda row: (row["platform"], row["asset"]))
    audit = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "ledger_rows": len(rows),
        "platform_asset_count": len(assets),
        "negative_platform_asset_count": len(negatives),
        "dust_threshold": plain(DUST_THRESHOLD),
        "assets": assets,
        "negative_assets": negatives,
        "first_timeline_breaks": sorted(timeline_breaks, key=lambda row: (row.get("normalized_timestamp_utc") or row["timestamp_utc"], row["platform"], row["asset"]))[:500],
    }
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(DOC_PATH), "negative_assets": len(negatives)}, ensure_ascii=False, indent=2))


def load_ledger() -> list[dict[str, str]]:
    rows = []
    with LEDGER_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if str(row.get("source_mode") or "active").lower() != "active":
                continue
            rows.append(row)
    return rows


def slim_event(row: dict[str, str], before: Decimal, after: Decimal) -> dict[str, str]:
    return {
        "ledger_id": row.get("ledger_id", ""),
        "timestamp_utc": row.get("timestamp_utc", ""),
        "normalized_timestamp_utc": effective_timestamp(row),
        "timestamp_offset_seconds": row.get("timestamp_offset_seconds", "0"),
        "timestamp_normalization_reason": row.get("timestamp_normalization_reason", ""),
        "platform": row.get("platform", ""),
        "asset": row.get("asset", ""),
        "quantity_delta": row.get("quantity_delta", ""),
        "balance_before": plain(before),
        "balance_after": plain(after),
        "event_type": row.get("event_type", ""),
        "source": row.get("source", ""),
        "tx_id": row.get("tx_id", ""),
        "counterparty_platform": row.get("counterparty_platform", ""),
        "counterparty_address": row.get("counterparty_address", ""),
    }


def serialize_stat(stat: dict[str, Any], yearly_net: dict[tuple[str, str, str], Decimal]) -> dict[str, Any]:
    platform = str(stat["platform"])
    asset = str(stat["asset"])
    years = [
        {"year": year, "net_quantity": plain(value)}
        for (p, a, year), value in sorted(yearly_net.items())
        if p == platform and a == asset and value != 0
    ]
    return {
        "platform": platform,
        "asset": asset,
        "event_count": stat["event_count"],
        "first_timestamp_utc": stat["first_timestamp_utc"],
        "first_normalized_timestamp_utc": stat.get("first_normalized_timestamp_utc", stat["first_timestamp_utc"]),
        "last_timestamp_utc": stat["last_timestamp_utc"],
        "last_normalized_timestamp_utc": stat.get("last_normalized_timestamp_utc", stat["last_timestamp_utc"]),
        "final_balance": plain(stat["final_balance"]),
        "worst_balance": plain(stat["worst_balance"]),
        "first_negative": stat["first_negative"],
        "last_event": stat["last_event"],
        "yearly_net": years,
    }


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def effective_timestamp(row: dict[str, str]) -> str:
    return str(row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or "")


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Platform Balance Simulation - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Ledger-Zeilen: `{audit['ledger_rows']}`",
        f"- Plattform/Asset-Konten: `{audit['platform_asset_count']}`",
        f"- Konten mit negativem Verlauf oder Endsaldo: `{audit['negative_platform_asset_count']}`",
        f"- Dust-Grenze: `{audit['dust_threshold']}`",
        "",
        "## Erste Bruchstellen",
        "",
    ]
    if not audit["first_timeline_breaks"]:
        lines.append("- Keine negativen Plattform-Salden oberhalb der Dust-Grenze gefunden.")
    for row in audit["first_timeline_breaks"][:80]:
        lines.append(
            f"- `{row['timestamp_utc']}` `{row['platform']}` `{row['asset']}` "
            f"delta `{row['quantity_delta']}` saldo `{row['balance_after']}` "
            f"quelle `{row['source']}` tx `{row['tx_id']}`"
        )
    lines += [
        "",
        "## Bewertung",
        "",
        "- Diese Simulation trennt Plattformen bewusst. Ein negativer Plattform-Saldo bedeutet nicht automatisch fehlendes Gesamtportfolio, sondern markiert fehlende Transfers, fehlende CEX-Historie oder falsche Quellenzuordnung.",
        "- Die Ausgabe ist die Arbeitsbasis fuer Pionex/Binance/Bitget/Solana/Helium-Abgleich und KI-Hypothesen.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
