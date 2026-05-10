#!/usr/bin/env python3
"""Reactivate BUSD dust candidate after active-source balance filtering."""

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
CANDIDATE_ID = "mixed-busd-dust-residual-2023-05-02"
REPORT_JSON = ROOT / "var" / "busd_dust_candidate_active_filter_refresh_2026-05-09.json"
REPORT_DOC = ROOT / "docs" / "147_BUSD_DUST_CANDIDATE_ACTIVE_FILTER_REFRESH_2026-05-09.md"


def main() -> None:
    candidates = load_candidates()
    now = datetime.now(UTC).isoformat()
    entry = dict(candidates.get(CANDIDATE_ID, {}))
    entry.update(
        {
            "candidate_id": CANDIDATE_ID,
            "platform": "mixed",
            "asset": "BUSD",
            "quantity_delta": "0.55168701480000000000",
            "effective_timestamp_utc": "2023-05-02T04:13:22+00:00",
            "adjustment_type": "dust_residual_candidate",
            "status": "needs_review",
            "reason_code": "mixed_pionex_binance_busd_dust_residual",
            "note": (
                "Reactivated after active-source filtering: global active BUSD balance is "
                "-0.5516870148 after Binance dust convert tx 136251331484. Candidate remains "
                "review-only and tax_effective=false."
            ),
            "tax_effective": False,
            "updated_at_utc": now,
        }
    )
    evidence = dict(entry.get("evidence") or {})
    evidence.update(
        {
            "current_active_balance_report": "docs/145_CHRONOLOGICAL_BALANCE_BREAK_AUDIT_AFTER_ACTIVE_SOURCE_FILTER_2026-05-09.md",
            "current_transient_report": "docs/119_TRANSIENT_BALANCE_UNDERCOVERAGE_AUDIT_2026-05-09.md",
            "current_negative_final_balance": "-0.55168701480000000000",
            "dust_tx_id": "136251331484",
            "dust_timestamp_utc": "2023-05-02T04:13:23+00:00",
            "previous_superseded_status": "superseded_by_current_balance_audit",
        }
    )
    entry["evidence"] = evidence
    entry.pop("superseded_by", None)
    candidates[CANDIDATE_ID] = entry
    put_admin_setting(SETTING_KEY, candidates, is_secret=False)

    payload = {
        "created_at_utc": now,
        "candidate_id": CANDIDATE_ID,
        "status": entry["status"],
        "tax_effective": entry["tax_effective"],
        "quantity_delta": entry["quantity_delta"],
        "current_negative_final_balance": evidence["current_negative_final_balance"],
        "reports": {
            "balance": evidence["current_active_balance_report"],
            "transient": evidence["current_transient_report"],
        },
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_DOC.write_text(render_doc(payload), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_DOC), "candidate_id": CANDIDATE_ID}, ensure_ascii=False, indent=2))


def load_candidates() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting(SETTING_KEY)
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    return {str(key): value for key, value in raw.items() if isinstance(value, dict)} if isinstance(raw, dict) else {}


def render_doc(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# BUSD Dust Candidate Active Filter Refresh - 2026-05-09",
            "",
            "## Ergebnis",
            "",
            f"- Candidate: `{payload['candidate_id']}`",
            f"- Status: `{payload['status']}`",
            f"- Steuerwirksam: `{payload['tax_effective']}`",
            f"- Review-Menge: `{payload['quantity_delta']} BUSD`",
            f"- Aktiver negativer Endsaldo: `{payload['current_negative_final_balance']} BUSD`",
            "",
            "## Bewertung",
            "",
            "- Der Kandidat war durch einen alten referenzgestuetzten Audit als erledigt markiert.",
            "- Nach aktiver Quellenfilterung ist BUSD wieder ein kleiner offener Dust-/Rundungsfall.",
            "- Keine automatische Steuerbuchung; fachlich als Dust/Rundung pruefen oder mit aktiver Mini-Rekonstruktion belegen.",
            "",
            "## Referenzen",
            "",
            f"- Balance: `{payload['reports']['balance']}`",
            f"- Transient: `{payload['reports']['transient']}`",
            "",
        ]
    )


if __name__ == "__main__":
    main()
