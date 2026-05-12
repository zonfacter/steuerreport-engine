#!/usr/bin/env python3
"""Apply reviewed Bitget/Blockpit duplicate exclusions from the match audit."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import put_admin_setting
from tax_engine.ingestion.store import STORE

MATCH_JSON = ROOT / "var" / "bitget_blockpit_reference_match_2026-05-08.json"
SETTING_KEY = "runtime.tax_event_overrides"
REASON_CODE = "reference_import_only"
REASON_LABEL = "Nur Referenzimport, Primärdaten sind bereits vorhanden"


def main() -> None:
    audit = json.loads(MATCH_JSON.read_text(encoding="utf-8"))
    candidate_ids = [str(item).strip() for item in audit.get("safe_exclusion_candidate_event_ids", []) if str(item).strip()]
    if not candidate_ids:
        raise SystemExit("No safe exclusion candidates found.")

    overrides = load_overrides()
    now = datetime.now(UTC).isoformat()
    inserted = 0
    unchanged = 0
    for event_id in candidate_ids:
        entry = {
            "tax_category": "EXCLUDED",
            "reason_code": REASON_CODE,
            "reason_label": REASON_LABEL,
            "note": (
                "Bitget Tax API ist Primärquelle; Blockpit-Zeile matcht im Liquidationsfenster "
                "2025-02-20..2025-03-05 gegen Bitget-Primary nach Zeit/Asset/Betrag bzw. Bitget-ID-Basis. "
                f"Quelle: {MATCH_JSON.name}"
            ),
            "updated_at_utc": now,
        }
        if overrides.get(event_id) == entry:
            unchanged += 1
            continue
        overrides[event_id] = entry
        inserted += 1

    put_admin_setting(SETTING_KEY, overrides, is_secret=False)
    print(json.dumps({"candidate_count": len(candidate_ids), "inserted_or_updated": inserted, "unchanged": unchanged}, indent=2))


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
