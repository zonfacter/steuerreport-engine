#!/usr/bin/env python3
"""Summarize remaining HNT platform-local breaks after global balance cleanup."""

from __future__ import annotations

import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CREATED_DATE = "2026-05-09"
LEDGER_JSONL = ROOT / "var" / f"platform_ledger_{CREATED_DATE}.jsonl"
SIM_JSON = ROOT / "var" / f"platform_balance_simulation_{CREATED_DATE}.json"
BALANCE_JSON = ROOT / "var" / f"chronological_balance_break_audit_after_bitget_hnt_source_chain_{CREATED_DATE}.json"
OUTPUT_JSON = ROOT / "var" / f"hnt_platform_context_audit_{CREATED_DATE}.json"
OUTPUT_MD = ROOT / "docs" / f"158_HNT_PLATFORM_CONTEXT_AUDIT_{CREATED_DATE}.md"


def main() -> None:
    ledger = [row for row in load_jsonl(LEDGER_JSONL) if row.get("source_mode") == "active" and row.get("asset") == "HNT"]
    ledger.sort(key=lambda row: (row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or "", row.get("ledger_id") or ""))
    simulation = load_json(SIM_JSON)
    global_balance = load_json(BALANCE_JSON)
    negative = [
        row
        for row in simulation.get("negative_assets", [])
        if str(row.get("asset") or "").upper() == "HNT"
    ]
    audit = {
        "global_hnt": global_hnt_report(global_balance),
        "negative_platform_hnt": negative,
        "platform_summaries": platform_summaries(ledger),
        "focused_windows": {
            f"{row.get('platform')}:{row.get('asset')}": focused_window(ledger, row)
            for row in negative
        },
        "assessment": [
            "HNT is not a global negative-final-balance problem after the current cleanup.",
            "Remaining HNT issues are platform-local allocation/context problems across Binance and Pionex.",
            "Binance HNT residual is small and was introduced by the closed Blockpit source-chain reconstruction; it likely needs transfer/context or a small dust decision, not a global inventory fix.",
            "The Solana-wallet HNT gap is closed by the Solscan counterflow import for the 2025 Bitget withdrawal.",
            "The Bitget HNT gap is closed by the Blockpit-Bitget source-chain reconstruction before the April 2024 sells.",
        ],
    }
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(OUTPUT_MD), "negative_platform_hnt": len(negative)}, ensure_ascii=False, indent=2))


def platform_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_platform: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_platform[str(row.get("platform") or "")].append(row)
    summaries = []
    for platform, platform_rows in sorted(by_platform.items()):
        total = sum(dec(row.get("quantity_delta")) for row in platform_rows)
        by_source: dict[str, Decimal] = defaultdict(Decimal)
        by_type: dict[str, Decimal] = defaultdict(Decimal)
        for row in platform_rows:
            delta = dec(row.get("quantity_delta"))
            by_source[str(row.get("source") or "")] += delta
            by_type[str(row.get("event_type") or "")] += delta
        summaries.append(
            {
                "platform": platform,
                "event_count": len(platform_rows),
                "first": platform_rows[0].get("normalized_timestamp_utc") or platform_rows[0].get("timestamp_utc"),
                "last": platform_rows[-1].get("normalized_timestamp_utc") or platform_rows[-1].get("timestamp_utc"),
                "net_hnt": plain(total),
                "source_net_top": [
                    {"source": source, "net_hnt": plain(value)}
                    for source, value in sorted(by_source.items(), key=lambda item: abs(item[1]), reverse=True)[:8]
                ],
                "event_type_net_top": [
                    {"event_type": event_type, "net_hnt": plain(value)}
                    for event_type, value in sorted(by_type.items(), key=lambda item: abs(item[1]), reverse=True)[:8]
                ],
            }
        )
    return summaries


def focused_window(rows: list[dict[str, Any]], break_row: dict[str, Any]) -> list[dict[str, Any]]:
    platform = str(break_row.get("platform") or "")
    ts = str((break_row.get("first_negative") or {}).get("normalized_timestamp_utc") or "")
    if not ts:
        return []
    selected = [
        row
        for row in rows
        if str(row.get("platform") or "") == platform
        and ts[:10] <= str(row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or "")[:10] <= ts[:10]
    ]
    if not selected:
        selected = [row for row in rows if str(row.get("platform") or "") == platform][-20:]
    balance = Decimal("0")
    enriched = []
    for row in [item for item in rows if str(item.get("platform") or "") == platform]:
        before = balance
        delta = dec(row.get("quantity_delta"))
        balance += delta
        if row in selected:
            enriched.append(
                {
                    "ledger_id": row.get("ledger_id"),
                    "timestamp_utc": row.get("normalized_timestamp_utc") or row.get("timestamp_utc"),
                    "event_type": row.get("event_type"),
                    "source": row.get("source"),
                    "quantity_delta": row.get("quantity_delta"),
                    "balance_before": plain(before),
                    "balance_after": plain(balance),
                    "tx_id": row.get("tx_id"),
                }
            )
    return enriched


def global_hnt_report(balance: dict[str, Any]) -> dict[str, Any]:
    for row in balance.get("asset_reports", []):
        if str(row.get("asset") or "").upper() == "HNT":
            return {
                "final_balance": row.get("final_balance"),
                "first_negative": row.get("first_negative"),
                "worst_balance": row.get("worst_balance"),
                "event_count": row.get("event_count"),
            }
    return {}


def load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# HNT Platform Context Audit - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Globaler HNT-Endsaldo: `{audit['global_hnt'].get('final_balance')}`",
        f"- Plattformlokale negative HNT-Konten: `{len(audit['negative_platform_hnt'])}`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {item}" for item in audit["assessment"])
    lines += ["", "## Negative Plattformkonten", ""]
    for row in audit["negative_platform_hnt"]:
        first = row.get("first_negative") or {}
        lines.append(
            f"- `{row.get('platform')}` final `{row.get('final_balance')}` worst `{row.get('worst_balance')}` "
            f"first `{first.get('normalized_timestamp_utc')}` tx `{first.get('tx_id')}`"
        )
    lines += ["", "## Plattform-Summaries", ""]
    for row in audit["platform_summaries"]:
        lines.append(
            f"- `{row['platform']}` events `{row['event_count']}` net `{row['net_hnt']}` "
            f"range `{row['first']}`..`{row['last']}`"
        )
    lines += ["", "## Naechste Aktion", ""]
    lines += [
        "- Nicht global HNT korrigieren; global ist HNT positiv.",
        "- Solana-HNT und Bitget-HNT sind durch belegte Gegenfluesse geschlossen.",
        "- Binance-HNT als kleine Restdifferenz aus der rekonstruierten Kette separat behandeln, wenn kein Transferbeleg gefunden wird.",
        "- Pionex-HNT als Bot-/Dust-Rest zusammen mit dem Pionex-USDT-Opening entscheiden.",
        "",
    ]
    return "\n".join(lines)


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


if __name__ == "__main__":
    main()
