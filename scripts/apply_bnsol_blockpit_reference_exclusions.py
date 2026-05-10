#!/usr/bin/env python3
"""Exclude Blockpit BNSOL reference rows when Binance API primary BNSOL rows exist."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import put_admin_setting
from tax_engine.api.dashboard import _load_token_aliases, _payload_asset_canonical_symbol
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

SETTING_OVERRIDES = "runtime.tax_event_overrides"
REPORT_JSON = ROOT / "var" / "bnsol_blockpit_reference_exclusions_2026-05-09.json"
REPORT_MD = ROOT / "docs" / "121_BNSOL_BLOCKPIT_REFERENCE_EXCLUSIONS_2026-05-09.md"
REASON_CODE = "reference_import_only"
REASON_LABEL = "Nur Referenzimport, Primärdaten sind bereits vorhanden"


def main() -> None:
    raw, _ = apply_review_actions(STORE.list_raw_events())
    events, _ = apply_tax_event_overrides(raw)
    aliases = _load_token_aliases()
    candidates = []
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if not payload or str(payload.get("source") or "").lower() != "blockpit":
            continue
        if _payload_asset_canonical_symbol(payload, aliases) != "BNSOL":
            continue
        raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        integration = str(raw_row.get("Integration Name") or "").lower()
        if "binance" not in integration:
            continue
        candidates.append(
            {
                "event_id": str(event.get("unique_event_id") or ""),
                "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
                "event_type": str(payload.get("event_type") or ""),
                "side": str(payload.get("side") or ""),
                "quantity": str(payload.get("quantity") or ""),
                "tx_id": str(payload.get("tx_id") or ""),
                "raw_trx_id": str(raw_row.get("Trx. ID (optional)") or ""),
                "raw_label": str(raw_row.get("Label") or ""),
                "raw_comment": str(raw_row.get("Comment (optional)") or ""),
            }
        )
    now = datetime.now(UTC).isoformat()
    overrides = load_overrides()
    inserted = 0
    unchanged = 0
    for item in candidates:
        entry = {
            "tax_category": "EXCLUDED",
            "reason_code": REASON_CODE,
            "reason_label": REASON_LABEL,
            "note": "Blockpit BNSOL Binance reference excluded; Binance API primary staking/earn/convert rows are present.",
            "updated_at_utc": now,
        }
        if overrides.get(item["event_id"]) == entry:
            unchanged += 1
            continue
        overrides[item["event_id"]] = entry
        inserted += 1
    put_admin_setting(SETTING_OVERRIDES, overrides, is_secret=False)
    audit = {
        "created_at_utc": now,
        "candidate_count": len(candidates),
        "inserted_or_updated": inserted,
        "unchanged": unchanged,
        "candidates": candidates,
        "interpretation": [
            "This is intentionally limited to Blockpit/Binance BNSOL rows.",
            "Binance API primary rows cover staking conversion, daily BNSOL earn rewards and conversion out.",
            "Excluding Blockpit rows removes duplicate BNSOL micro-undercoverage without deleting evidence.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "candidate_count": len(candidates), "inserted_or_updated": inserted}, ensure_ascii=False, indent=2))


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
        "# BNSOL Blockpit Reference Exclusions - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Blockpit-BNSOL-Referenzzeilen ausschliessen, wenn Binance-API-Primary fuer Staking/Earn/Convert vorhanden ist.",
        "",
        f"- Kandidaten: `{audit['candidate_count']}`",
        f"- Eingetragen/aktualisiert: `{audit['inserted_or_updated']}`",
        f"- Unveraendert: `{audit['unchanged']}`",
        "",
        "## Beispiele",
        "",
    ]
    for item in audit["candidates"][:30]:
        lines.append(
            f"- `{item['timestamp_utc']}` `{item['event_type']}` `{item['side']}` qty `{item['quantity']}` "
            f"tx `{item['tx_id']}` raw `{item['raw_trx_id']}`"
        )
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
