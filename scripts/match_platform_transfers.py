#!/usr/bin/env python3
"""Match platform ledger rows into transfer groups."""

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
OUTPUT_JSON = ROOT / "var" / f"platform_transfer_groups_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"131_PLATFORM_TRANSFER_GROUPS_{CREATED_DATE}.md"
TRANSFER_TYPES = {"deposit", "withdrawal", "transfer", "legacy_transfer", "token_transfer", "fiat_deposit", "fiat_withdrawal"}


def main() -> None:
    rows = load_ledger()
    groups = exact_txid_groups(rows)
    unmatched = unmatched_transfer_like(rows, groups)
    audit = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "ledger_rows": len(rows),
        "transfer_group_count": len(groups),
        "matched_ledger_row_count": sum(len(group["ledger_ids"]) for group in groups),
        "unmatched_transfer_like_count": len(unmatched),
        "groups": groups,
        "unmatched_transfer_like": unmatched[:500],
    }
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(DOC_PATH), "groups": len(groups), "unmatched": len(unmatched)}, ensure_ascii=False, indent=2))


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


def exact_txid_groups(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        tx_id = str(row.get("tx_id") or "").strip()
        if not tx_id or tx_id.startswith("s_") or tx_id.startswith("blockpit-"):
            continue
        by_key[(tx_id, row.get("asset", ""))].append(row)

    groups = []
    for (tx_id, asset), items in by_key.items():
        ins = [row for row in items if Decimal(row["quantity_delta"]) > 0]
        outs = [row for row in items if Decimal(row["quantity_delta"]) < 0]
        if not ins or not outs:
            continue
        platforms = {row["platform"] for row in items}
        if len(platforms) < 2:
            continue
        in_total = sum(Decimal(row["quantity_delta"]) for row in ins)
        out_total = abs(sum(Decimal(row["quantity_delta"]) for row in outs))
        diff = abs(in_total - out_total)
        confidence = "high" if diff <= max(Decimal("0.000001"), out_total * Decimal("0.001")) else "medium"
        groups.append(
            {
                "transfer_group_id": f"txid:{tx_id}:{asset}",
                "match_type": "exact_txid",
                "confidence": confidence,
                "tx_id": tx_id,
                "asset": asset,
                "from_platforms": sorted({row["platform"] for row in outs}),
                "to_platforms": sorted({row["platform"] for row in ins}),
                "quantity_out": plain(out_total),
                "quantity_in": plain(in_total),
                "quantity_diff": plain(diff),
                "first_timestamp_utc": min(row["timestamp_utc"] for row in items),
                "last_timestamp_utc": max(row["timestamp_utc"] for row in items),
                "first_normalized_timestamp_utc": min(row.get("normalized_timestamp_utc") or row["timestamp_utc"] for row in items),
                "last_normalized_timestamp_utc": max(row.get("normalized_timestamp_utc") or row["timestamp_utc"] for row in items),
                "ledger_ids": [row["ledger_id"] for row in items],
                "rows": [slim(row) for row in sorted(items, key=lambda row: (row.get("normalized_timestamp_utc") or row["timestamp_utc"], row["timestamp_utc"]))],
            }
        )
    return sorted(groups, key=lambda row: (row["first_normalized_timestamp_utc"], row["transfer_group_id"]))


def unmatched_transfer_like(rows: list[dict[str, str]], groups: list[dict[str, Any]]) -> list[dict[str, str]]:
    matched = {ledger_id for group in groups for ledger_id in group["ledger_ids"]}
    result = []
    for row in rows:
        if row["ledger_id"] in matched:
            continue
        event_type = str(row.get("event_type") or "").lower()
        if event_type in TRANSFER_TYPES or row.get("counterparty_address"):
            result.append(slim(row))
    return sorted(result, key=lambda row: (row.get("normalized_timestamp_utc") or row["timestamp_utc"], row["timestamp_utc"]))


def slim(row: dict[str, str]) -> dict[str, str]:
    return {
        "ledger_id": row.get("ledger_id", ""),
        "timestamp_utc": row.get("timestamp_utc", ""),
        "normalized_timestamp_utc": row.get("normalized_timestamp_utc", row.get("timestamp_utc", "")),
        "timestamp_offset_seconds": row.get("timestamp_offset_seconds", "0"),
        "timestamp_normalization_reason": row.get("timestamp_normalization_reason", ""),
        "platform": row.get("platform", ""),
        "asset": row.get("asset", ""),
        "quantity_delta": row.get("quantity_delta", ""),
        "event_type": row.get("event_type", ""),
        "source": row.get("source", ""),
        "tx_id": row.get("tx_id", ""),
        "counterparty_platform": row.get("counterparty_platform", ""),
        "counterparty_address": row.get("counterparty_address", ""),
    }


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Platform Transfer Groups - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Ledger-Zeilen: `{audit['ledger_rows']}`",
        f"- Transfergruppen: `{audit['transfer_group_count']}`",
        f"- Gematchte Ledger-Zeilen: `{audit['matched_ledger_row_count']}`",
        f"- Unmatched transfer-like: `{audit['unmatched_transfer_like_count']}`",
        "",
        "## Top Transfergruppen",
        "",
    ]
    for group in audit["groups"][:40]:
        lines.append(
            f"- `{group['first_timestamp_utc']}` `{group['asset']}` `{group['quantity_out']}` "
            f"{','.join(group['from_platforms'])} -> {','.join(group['to_platforms'])} "
            f"diff `{group['quantity_diff']}` tx `{group['tx_id']}`"
        )
    lines += ["", "## Bewertung", ""]
    lines.append("- Exakte TXID-Matches sind Transfergruppen-Kandidaten; steuerliche Wirkung bleibt beim Originalevent.")
    lines.append("- Unmatched transfer-like Rows sind die Arbeitsliste fuer Address-/Amount-Time- und KI-Analyse.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
