#!/usr/bin/env python3
"""Exclude composite Blockpit SOL withdrawal+fee groups matched by one Solana RPC SOL outflow."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import put_admin_setting
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

CREATED_DATE = "2026-05-09"
SETTING_OVERRIDES = "runtime.tax_event_overrides"
REPORT_JSON = ROOT / "var" / f"solana_blockpit_composite_sol_exclusions_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"117_SOLANA_BLOCKPIT_COMPOSITE_SOL_EXCLUSIONS_{CREATED_DATE}.md"
REASON_CODE = "reference_import_only"
REASON_LABEL = "Nur Referenzimport, Primärdaten sind bereits vorhanden"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    matches = find_matches()
    now = datetime.now(UTC).isoformat()
    import_result = None
    if args.execute:
        overrides = load_overrides()
        inserted = 0
        unchanged = 0
        for match in matches:
            for event_id in match["blockpit_event_ids"]:
                entry = {
                    "tax_category": "EXCLUDED",
                    "reason_code": REASON_CODE,
                    "reason_label": REASON_LABEL,
                    "note": (
                        "Blockpit Solana SOL split reference excluded because withdrawal+fee group equals "
                        f"Solana RPC native SOL balance outflow for tx {match['tx_id']}."
                    ),
                    "updated_at_utc": now,
                }
                if overrides.get(event_id) == entry:
                    unchanged += 1
                    continue
                overrides[event_id] = entry
                inserted += 1
        put_admin_setting(SETTING_OVERRIDES, overrides, is_secret=False)
        import_result = {"excluded_event_count": inserted, "unchanged_exclusions": unchanged}
    audit = {
        "created_at_utc": now,
        "mode": "execute" if args.execute else "preview",
        "match_count": len(matches),
        "excluded_event_candidate_count": sum(len(item["blockpit_event_ids"]) for item in matches),
        "matches": matches[:500],
        "import_result": import_result,
        "interpretation": [
            "This handles native SOL only, where Solana RPC balance changes include transfer amount plus fee.",
            "A match requires same Solana signature, same timestamp and exact sum of Blockpit SOL out components.",
            "Matched Blockpit rows are retained as RAW evidence and excluded only tax-effectively.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "mode": audit["mode"], "match_count": len(matches), "excluded_event_candidate_count": audit["excluded_event_candidate_count"], "import_result": import_result}, ensure_ascii=False, indent=2))


def find_matches() -> list[dict[str, Any]]:
    raw, _ = apply_review_actions(STORE.list_raw_events())
    events, _ = apply_tax_event_overrides(raw)
    rpc_out: dict[tuple[str, str], dict[str, Any]] = {}
    blockpit_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if not payload:
            continue
        source = str(payload.get("source") or "").lower().strip()
        asset = str(payload.get("asset") or "").upper().strip()
        side = str(payload.get("side") or "").lower().strip()
        timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        qty = dec(payload.get("quantity"))
        if asset != "SOL" or side != "out" or qty <= 0:
            continue
        if source == "solana_rpc" and str(payload.get("event_type") or "").lower() == "sol_transfer":
            tx_id = str(payload.get("tx_id") or "").strip()
            if tx_id:
                rpc_out[(tx_id, timestamp)] = {
                    "event_id": str(event.get("unique_event_id") or ""),
                    "quantity": qty,
                    "tx_id": tx_id,
                    "timestamp_utc": timestamp,
                }
        elif source == "blockpit" and is_blockpit_solana_reference(payload):
            tx_id = blockpit_raw_tx(payload)
            if tx_id:
                blockpit_groups[(tx_id, timestamp)].append(
                    {
                        "event_id": str(event.get("unique_event_id") or ""),
                        "quantity": qty,
                        "event_type": str(payload.get("event_type") or ""),
                        "tx_id": tx_id,
                        "timestamp_utc": timestamp,
                    }
                )
    matches: list[dict[str, Any]] = []
    for key, group in blockpit_groups.items():
        rpc = rpc_out.get(key)
        if not rpc or len(group) < 2:
            continue
        group_sum = sum((item["quantity"] for item in group), Decimal("0"))
        if group_sum != rpc["quantity"]:
            continue
        matches.append(
            {
                "tx_id": key[0],
                "timestamp_utc": key[1],
                "solana_rpc_event_id": rpc["event_id"],
                "solana_rpc_quantity": plain(rpc["quantity"]),
                "blockpit_sum": plain(group_sum),
                "blockpit_event_ids": [item["event_id"] for item in group],
                "blockpit_parts": [
                    {"event_id": item["event_id"], "event_type": item["event_type"], "quantity": plain(item["quantity"])}
                    for item in group
                ],
            }
        )
    return sorted(matches, key=lambda item: (item["timestamp_utc"], item["tx_id"]))


def is_blockpit_solana_reference(payload: dict[str, Any]) -> bool:
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    integration = str(raw.get("Integration Name") or "").lower()
    source_type = str(raw.get("Source Type") or "").lower()
    return "solana" in integration and source_type == "chain"


def blockpit_raw_tx(payload: dict[str, Any]) -> str:
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    return str(raw.get("Trx. ID (optional)") or "").strip()


def load_overrides() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting(SETTING_OVERRIDES)
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items() if isinstance(v, dict)}


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Solana Blockpit Composite SOL Exclusions - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Blockpit-Solana SOL-Splitbuchungen ausschliessen, wenn Withdrawal+Fee exakt einer Solana-RPC-Native-SOL-Balance-Aenderung entsprechen.",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Composite Matches: `{audit['match_count']}`",
        f"- Event-Kandidaten: `{audit['excluded_event_candidate_count']}`",
        f"- Import Result: `{audit['import_result']}`",
        "",
        "## Beispiele",
        "",
    ]
    for item in audit["matches"][:25]:
        lines.append(
            f"- `{item['timestamp_utc']}` SOL out `{item['solana_rpc_quantity']}` tx `{item['tx_id']}` "
            f"parts `{item['blockpit_parts']}`"
        )
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    return "\n".join(lines) + "\n"


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Decimal) -> str:
    return value.normalize().to_eng_string() if value else "0"


if __name__ == "__main__":
    main()
