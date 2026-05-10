#!/usr/bin/env python3
"""Mark stale dust residual review candidates as superseded by current clean balance audit."""

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

SETTING_KEY = "runtime.balance_adjustment_candidates"
TARGET_IDS = {
    "binance-vtho-dust-residual-2023-05-02",
    "mixed-busd-dust-residual-2023-05-02",
}
REPORT_JSON = ROOT / "var" / "superseded_dust_residual_candidates_2026-05-09.json"
REPORT_MD = ROOT / "docs" / "127_SUPERSEDED_DUST_RESIDUAL_CANDIDATES_2026-05-09.md"


def main() -> None:
    candidates = load_candidates()
    now = datetime.now(UTC).isoformat()
    changed = []
    for candidate_id in TARGET_IDS:
        row = candidates.get(candidate_id)
        if not row:
            continue
        previous_status = row.get("status")
        row["status"] = "superseded_by_current_balance_audit"
        row["tax_effective"] = False
        row["updated_at_utc"] = now
        row["superseded_by"] = {
            "report": "docs/156_CHRONOLOGICAL_BALANCE_BREAK_AUDIT_AFTER_BINANCE_SOURCE_CHAIN_RECONSTRUCTION_2026-05-09.md",
            "reason": "Current balance audit has zero negative final assets after the Binance source-chain reconstruction; dust residual candidate is no longer an active blocker.",
        }
        changed.append({"candidate_id": candidate_id, "previous_status": previous_status, "new_status": row["status"]})
    put_admin_setting(SETTING_KEY, candidates, is_secret=False)
    payload = {
        "created_at_utc": now,
        "changed_count": len(changed),
        "changed": sorted(changed, key=lambda row: row["candidate_id"]),
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(payload), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "changed_count": len(changed)}, ensure_ascii=False, indent=2))


def load_candidates() -> dict[str, dict[str, Any]]:
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


def render_doc(payload: dict[str, Any]) -> str:
    lines = [
        "# Superseded Dust Residual Candidates - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Aktualisiert: `{payload['changed_count']}`",
        "",
    ]
    for row in payload["changed"]:
        lines.append(f"- `{row['candidate_id']}`: `{row['previous_status']}` -> `{row['new_status']}`")
    lines += [
        "",
        "## Bewertung",
        "",
        "- Die Kandidaten bleiben als Historie erhalten und werden nicht steuerwirksam gebucht.",
        "- Sie sind kein aktiver Blocker mehr, weil der aktuelle chronologische Endbestands-Audit keine negativen Endbestaende mehr hat.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
