#!/usr/bin/env python3
"""Exclude exact Blockpit Binance transfer references when Binance API primary rows exist."""

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
from tax_engine.api.dashboard import _payload_asset_canonical_symbol
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

CREATED_DATE = "2026-05-09"
SETTING_OVERRIDES = "runtime.tax_event_overrides"
REPORT_JSON = ROOT / "var" / f"binance_blockpit_transfer_reference_exclusions_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"115_BINANCE_BLOCKPIT_TRANSFER_REFERENCE_EXCLUSIONS_{CREATED_DATE}.md"
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
        for item in matches:
            entry = {
                "tax_category": "EXCLUDED",
                "reason_code": REASON_CODE,
                "reason_label": REASON_LABEL,
                "note": (
                    "Blockpit Binance transfer reference excluded because Binance API primary transfer exists "
                    f"for id/tx {item['match_id']} / asset {item['asset']} / quantity {item['quantity']}. "
                    "Related Blockpit fee rows are not excluded by this script."
                ),
                "updated_at_utc": now,
            }
            event_id = item["blockpit_event_id"]
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
        "matches": matches[:500],
        "import_result": import_result,
        "interpretation": [
            "Only Blockpit Binance transfer legs are excluded, not Blockpit fee rows.",
            "A match requires Binance API raw id/txId to match Blockpit Trx. ID or same tx plus timestamp/asset/side/quantity.",
            "This keeps primary exchange evidence and avoids double-counting transfer legs.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "mode": audit["mode"], "match_count": len(matches), "import_result": import_result}, ensure_ascii=False, indent=2))


def find_matches() -> list[dict[str, Any]]:
    raw, _ = apply_review_actions(STORE.list_raw_events())
    events, _ = apply_tax_event_overrides(raw)
    primary: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    refs: list[dict[str, Any]] = []
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if not payload:
            continue
        source = str(payload.get("source") or "").lower().strip()
        event_type = str(payload.get("event_type") or "").lower().strip()
        if event_type not in {"withdrawal", "deposit"}:
            continue
        asset = _payload_asset_canonical_symbol(payload)
        item = {
            "event_id": str(event.get("unique_event_id") or ""),
            "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
            "asset": asset,
            "side": str(payload.get("side") or "").lower().strip(),
            "quantity": plain(dec(payload.get("quantity"))),
            "match_ids": match_ids(payload),
            "source": source,
            "event_type": event_type,
        }
        if source == "binance_api":
            for match_id in item["match_ids"]:
                primary[(match_id, asset, item["side"], item["quantity"])].append(item)
        elif source == "blockpit" and is_blockpit_binance_reference(payload):
            refs.append(item)
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ref in refs:
        for match_id in ref["match_ids"]:
            primary_rows = primary.get((match_id, ref["asset"], ref["side"], ref["quantity"]), [])
            if not primary_rows or ref["event_id"] in seen:
                continue
            seen.add(ref["event_id"])
            matches.append(
                {
                    "blockpit_event_id": ref["event_id"],
                    "binance_api_event_id": primary_rows[0]["event_id"],
                    "match_id": match_id,
                    "timestamp_utc": ref["timestamp_utc"],
                    "asset": ref["asset"],
                    "side": ref["side"],
                    "quantity": ref["quantity"],
                    "blockpit_event_type": ref["event_type"],
                    "binance_api_event_type": primary_rows[0]["event_type"],
                }
            )
            break
    return sorted(matches, key=lambda item: (item["timestamp_utc"], item["asset"], item["match_id"]))


def match_ids(payload: dict[str, Any]) -> set[str]:
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    values = {
        payload.get("tx_id"),
        raw.get("id"),
        raw.get("txId"),
        raw.get("txID"),
        raw.get("Trx. ID (optional)"),
    }
    return {str(value).strip() for value in values if str(value or "").strip()}


def is_blockpit_binance_reference(payload: dict[str, Any]) -> bool:
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    integration = str(raw.get("Integration Name") or "").lower()
    source_type = str(raw.get("Source Type") or "").lower()
    return "binance" in integration and source_type == "api"


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
        "# Binance Blockpit Transfer Reference Exclusions - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Exakte Blockpit-Binance-Transferreferenzen ausschliessen, wenn Binance-API-Primary vorhanden ist.",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Exact Matches: `{audit['match_count']}`",
        f"- Import Result: `{audit['import_result']}`",
        "",
        "## Beispiele",
        "",
    ]
    for item in audit["matches"][:25]:
        lines.append(
            f"- `{item['timestamp_utc']}` `{item['asset']}` `{item['quantity']}` `{item['side']}` "
            f"id `{item['match_id']}` blockpit `{item['blockpit_event_id']}` binance `{item['binance_api_event_id']}`"
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
