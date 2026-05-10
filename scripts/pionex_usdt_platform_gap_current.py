#!/usr/bin/env python3
"""Create a current Pionex USDT platform gap report from the normalized platform ledger."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CREATED_DATE = "2026-05-09"
LEDGER_JSONL = ROOT / "var" / f"platform_ledger_{CREATED_DATE}.jsonl"
OUTPUT_JSON = ROOT / "var" / f"pionex_usdt_platform_gap_current_{CREATED_DATE}.json"
OUTPUT_DOC = ROOT / "docs" / f"146_PIONEX_USDT_PLATFORM_GAP_CURRENT_{CREATED_DATE}.md"


def main() -> None:
    rows = [
        row
        for row in load_ledger()
        if row.get("source_mode") == "active" and row.get("platform") == "pionex" and row.get("asset") == "USDT"
    ]
    rows.sort(key=lambda row: (row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or "", row.get("ledger_id") or ""))
    audit = build_audit(rows)
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_DOC.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(OUTPUT_DOC), "required_opening": audit["required_opening_to_avoid_negative"]}, ensure_ascii=False, indent=2))


def load_ledger() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with LEDGER_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def build_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    balance = Decimal("0")
    worst: dict[str, Any] | None = None
    first_negative: dict[str, Any] | None = None
    negative_segments: list[dict[str, Any]] = []
    current_segment: dict[str, Any] | None = None
    yearly_net: dict[str, Decimal] = {}
    event_type_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    enriched: list[dict[str, Any]] = []

    for row in rows:
        delta = dec(row.get("quantity_delta"))
        before = balance
        after = before + delta
        balance = after
        year = str(row.get("year") or "")
        yearly_net[year] = yearly_net.get(year, Decimal("0")) + delta
        event_type_counts[str(row.get("event_type") or "")] += 1
        source_counts[str(row.get("source") or "")] += 1
        item = {
            **row,
            "balance_before": plain(before),
            "balance_after": plain(after),
        }
        enriched.append(item)
        if after < 0 and first_negative is None:
            first_negative = item
        if worst is None or after < dec(worst.get("balance_after")):
            worst = item
        if before >= 0 > after:
            current_segment = {
                "start_timestamp_utc": item.get("normalized_timestamp_utc") or item.get("timestamp_utc"),
                "start_ledger_id": item.get("ledger_id"),
                "start_tx_id": item.get("tx_id"),
                "start_balance_after": plain(after),
                "worst_balance": plain(after),
                "worst_timestamp_utc": item.get("normalized_timestamp_utc") or item.get("timestamp_utc"),
                "event_count": 1,
            }
        elif current_segment is not None and after < 0:
            current_segment["event_count"] = int(current_segment["event_count"]) + 1
            if after < dec(current_segment["worst_balance"]):
                current_segment["worst_balance"] = plain(after)
                current_segment["worst_timestamp_utc"] = item.get("normalized_timestamp_utc") or item.get("timestamp_utc")
        if current_segment is not None and before < 0 <= after:
            current_segment["end_timestamp_utc"] = item.get("normalized_timestamp_utc") or item.get("timestamp_utc")
            current_segment["end_ledger_id"] = item.get("ledger_id")
            current_segment["end_balance_after"] = plain(after)
            negative_segments.append(current_segment)
            current_segment = None

    if current_segment is not None:
        current_segment["end_timestamp_utc"] = ""
        current_segment["end_ledger_id"] = ""
        current_segment["end_balance_after"] = plain(balance)
        negative_segments.append(current_segment)

    worst_balance = dec((worst or {}).get("balance_after"))
    first_ts = str((first_negative or {}).get("normalized_timestamp_utc") or (first_negative or {}).get("timestamp_utc") or "")
    worst_ts = str((worst or {}).get("normalized_timestamp_utc") or (worst or {}).get("timestamp_utc") or "")
    worst_window = [
        slim(row)
        for row in enriched
        if "2022-01-19T12:40:00" <= str(row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or "") <= "2022-01-19T23:55:00"
    ]
    early_window = [
        slim(row)
        for row in enriched
        if "2021-12-25T00:00:00" <= str(row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or "") <= "2021-12-29T23:59:59"
    ]
    deposits_until_worst = [
        slim(row)
        for row in enriched
        if dec(row.get("quantity_delta")) > 0
        and str(row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or "") <= worst_ts
        and str(row.get("event_type") or "").lower() in {"deposit", "transfer", "withdrawal"}
    ]
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "ledger": str(LEDGER_JSONL),
        "event_count": len(rows),
        "final_balance": plain(balance),
        "first_negative": slim(first_negative) if first_negative else None,
        "worst_balance": slim(worst) if worst else None,
        "required_opening_to_avoid_first_negative": plain(abs(dec((first_negative or {}).get("balance_after")))),
        "required_opening_to_avoid_negative": plain(abs(worst_balance)) if worst_balance < 0 else "0",
        "first_negative_timestamp_utc": first_ts,
        "worst_timestamp_utc": worst_ts,
        "negative_segment_count": len(negative_segments),
        "negative_segments": negative_segments[:30],
        "yearly_net": {year: plain(value) for year, value in sorted(yearly_net.items())},
        "event_type_counts": dict(event_type_counts.most_common()),
        "source_counts": dict(source_counts.most_common()),
        "early_window": early_window,
        "worst_window": worst_window,
        "deposits_until_worst": deposits_until_worst,
        "assessment": [
            "Pionex USDT is a platform-local bot/opening-capital gap, not a single missing on-chain transfer.",
            "The first negative balance starts before the 2022-01-19 large deposit window.",
            "The worst point follows a Pionex trade-out shortly after the visible 1245.38419 USDT deposit.",
            "Do not create a tax-effective synthetic opening balance without Pionex evidence or an explicit review decision.",
        ],
    }


def slim(row: dict[str, Any] | None) -> dict[str, str]:
    if not row:
        return {}
    keys = [
        "ledger_id",
        "timestamp_utc",
        "normalized_timestamp_utc",
        "platform",
        "asset",
        "quantity_delta",
        "balance_before",
        "balance_after",
        "event_type",
        "source",
        "tx_id",
        "counterparty_platform",
        "counterparty_address",
    ]
    return {key: str(row.get(key) or "") for key in keys}


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def render_doc(audit: dict[str, Any]) -> str:
    first = audit["first_negative"] or {}
    worst = audit["worst_balance"] or {}
    lines = [
        "# Pionex USDT Platform Gap Current - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Aktive Pionex/USDT-Ledgerzeilen: `{audit['event_count']}`",
        f"- Finaler Pionex/USDT-Saldo: `{audit['final_balance']}`",
        f"- Erster negativer Stand: `{first.get('normalized_timestamp_utc', '')}` Ledger `{first.get('ledger_id', '')}` TX `{first.get('tx_id', '')}` nach `{first.get('balance_after', '')}`",
        f"- Schlimmster Stand: `{worst.get('normalized_timestamp_utc', '')}` Ledger `{worst.get('ledger_id', '')}` TX `{worst.get('tx_id', '')}` nach `{worst.get('balance_after', '')}`",
        f"- Opening noetig ab erstem Bruch: `{audit['required_opening_to_avoid_first_negative']} USDT`",
        f"- Opening noetig, damit Pionex nie negativ wird: `{audit['required_opening_to_avoid_negative']} USDT`",
        f"- Negative Segmente: `{audit['negative_segment_count']}`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {item}" for item in audit["assessment"])
    lines += [
        "",
        "## Worst Window 2022-01-19",
        "",
    ]
    for row in audit["worst_window"][:40]:
        lines.append(
            f"- `{row['normalized_timestamp_utc']}` `{row['ledger_id']}` `{row['event_type']}` "
            f"delta `{row['quantity_delta']}` before `{row['balance_before']}` after `{row['balance_after']}` tx `{row['tx_id']}`"
        )
    lines += [
        "",
        "## Early Window 2021-12-25 bis 2021-12-29",
        "",
    ]
    for row in audit["early_window"][:80]:
        lines.append(
            f"- `{row['normalized_timestamp_utc']}` `{row['ledger_id']}` `{row['event_type']}` "
            f"delta `{row['quantity_delta']}` before `{row['balance_before']}` after `{row['balance_after']}` tx `{row['tx_id']}`"
        )
    lines += [
        "",
        "## Sichtbare Deposits bis Worst",
        "",
    ]
    for row in audit["deposits_until_worst"][:30]:
        lines.append(
            f"- `{row['normalized_timestamp_utc']}` `{row['event_type']}` `{row['quantity_delta']} USDT` tx `{row['tx_id']}`"
        )
    lines += [
        "",
        "## Jahresnetto",
        "",
        f"`{audit['yearly_net']}`",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
