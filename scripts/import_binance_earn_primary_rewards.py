#!/usr/bin/env python3
"""Import Binance Simple Earn primary rewards and exclude matched Blockpit references."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import put_admin_setting
from tax_engine.ingestion.service import confirm_import
from tax_engine.ingestion.store import STORE

PROBE_JSON = ROOT / "var" / "binance_earn_primary_probe_2026-05-08.json"
SETTING_KEY = "runtime.tax_event_overrides"
REASON_CODE = "reference_import_only"
REASON_LABEL = "Nur Referenzimport, Primärdaten sind bereits vorhanden"


def main() -> None:
    audit = json.loads(PROBE_JSON.read_text(encoding="utf-8"))
    primary_rows = [normalize_primary_row(row) for row in audit.get("primary_rows", []) if isinstance(row, dict)]
    import_result = confirm_import("binance_simple_earn_primary_2025_api_2026-05-08", primary_rows)

    matched_reference_ids = sorted(
        {
            str(row.get("reference_event_id") or "").strip()
            for row in audit.get("matches", [])
            if str(row.get("reference_event_id") or "").strip()
        }
    )
    override_result = apply_reference_exclusions(matched_reference_ids)
    print(json.dumps({"import": import_result, "overrides": override_result}, indent=2, ensure_ascii=False))


def normalize_primary_row(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("raw_row") if isinstance(row.get("raw_row"), dict) else {}
    tx_id = str(row.get("source_tx_id") or "").strip()
    if not tx_id:
        tx_id = (
            f"binance-simple-earn:{row.get('source_endpoint')}:{row.get('reward_type')}:"
            f"{row.get('asset')}:{row.get('timestamp_utc')}:{row.get('amount')}"
        )
    return {
        "timestamp_utc": str(row.get("timestamp_utc") or ""),
        "asset": str(row.get("asset") or "").upper(),
        "quantity": str(row.get("amount") or "0"),
        "price": "",
        "fee": "0",
        "fee_asset": "",
        "side": "in",
        "event_type": "interest",
        "tx_id": tx_id,
        "source": "binance_api",
        "source_endpoint": str(row.get("source_endpoint") or ""),
        "reward_type": str(row.get("reward_type") or ""),
        "raw_row": {
            **raw,
            "__source_endpoint": str(row.get("source_endpoint") or ""),
            "__reward_type": str(row.get("reward_type") or ""),
        },
    }


def apply_reference_exclusions(event_ids: list[str]) -> dict[str, Any]:
    if not event_ids:
        return {"candidate_count": 0, "inserted_or_updated": 0, "unchanged": 0}
    overrides = load_overrides()
    now = datetime.now(UTC).isoformat()
    inserted = 0
    unchanged = 0
    for event_id in event_ids:
        entry = {
            "tax_category": "EXCLUDED",
            "reason_code": REASON_CODE,
            "reason_label": REASON_LABEL,
            "note": (
                "Binance Simple Earn Primary Reward wurde per API importiert; Blockpit-Earn-Referenz matcht exakt "
                "nach Zeit/Asset/Betrag. Quelle: binance_earn_primary_probe_2026-05-08.json"
            ),
            "updated_at_utc": now,
        }
        if overrides.get(event_id) == entry:
            unchanged += 1
            continue
        overrides[event_id] = entry
        inserted += 1
    put_admin_setting(SETTING_KEY, overrides, is_secret=False)
    return {"candidate_count": len(event_ids), "inserted_or_updated": inserted, "unchanged": unchanged}


def load_overrides() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting(SETTING_KEY)
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items() if isinstance(value, dict)}


if __name__ == "__main__":
    main()
