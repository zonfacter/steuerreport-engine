#!/usr/bin/env python3
"""Refresh Pionex USDT opening candidate with current active-source evidence."""

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
CANDIDATE_ID = "pionex-usdt-opening-balance-2021-12-28"
REPORT_JSON = ROOT / "var" / "pionex_opening_candidate_refresh_2026-05-09.json"
REPORT_MD = ROOT / "docs" / "125_PIONEX_OPENING_CANDIDATE_REFRESH_2026-05-09.md"


def main() -> None:
    candidates = load_candidates()
    now = datetime.now(UTC).isoformat()
    existing = candidates.get(CANDIDATE_ID, {})
    entry = dict(existing)
    entry.update(
        {
            "candidate_id": CANDIDATE_ID,
            "platform": "pionex",
            "asset": "USDT",
            "quantity_delta": "1643.2312211162",
            "effective_timestamp_utc": "2021-12-28T00:49:11+00:00",
            "adjustment_type": "opening_balance_candidate",
            "status": "needs_evidence_or_explicit_review_decision",
            "reason_code": "missing_pionex_bot_start_capital",
            "note": (
                "Current normalized active-source platform ledger requires 1643.2312211162 USDT start inventory "
                "to avoid negative Pionex bot ledger. The active-source global transient audit still shows a "
                "material USDT residual of 1569.9102818462 USDT at 2022-01-19T12:56:19Z. Candidate remains "
                "review-only and tax_effective=false."
            ),
            "tax_effective": False,
            "updated_at_utc": now,
        }
    )
    evidence = dict(entry.get("evidence") or {})
    evidence.update(
        {
            "pionex_platform_required_opening_usdt": "1643.2312211162",
            "pionex_first_negative_required_opening_usdt": "13.53043343",
            "current_active_source_global_transient_required_usdt": "1569.91028184620000000000",
            "current_global_residual_event": "2022-01-19T12:56:19+00:00 pionex trade/out s_11:68:out:USDT",
            "current_global_residual_report": "docs/119_TRANSIENT_BALANCE_UNDERCOVERAGE_AUDIT_2026-05-09.md",
            "current_detail_report": "docs/146_PIONEX_USDT_PLATFORM_GAP_CURRENT_2026-05-09.md",
            "current_end_balance_report": "docs/145_CHRONOLOGICAL_BALANCE_BREAK_AUDIT_AFTER_ACTIVE_SOURCE_FILTER_2026-05-09.md",
        }
    )
    entry["evidence"] = evidence
    candidates[CANDIDATE_ID] = entry
    put_admin_setting(SETTING_KEY, candidates, is_secret=False)

    payload = {
        "created_at_utc": now,
        "candidate_id": CANDIDATE_ID,
        "tax_effective": False,
        "pionex_platform_required_opening_usdt": evidence["pionex_platform_required_opening_usdt"],
        "pionex_first_negative_required_opening_usdt": evidence["pionex_first_negative_required_opening_usdt"],
        "current_active_source_global_transient_required_usdt": evidence["current_active_source_global_transient_required_usdt"],
        "status": entry["status"],
        "reports": {
            "transient": evidence["current_global_residual_report"],
            "detail": evidence["current_detail_report"],
            "end_balance": evidence["current_end_balance_report"],
        },
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(payload), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "candidate_id": CANDIDATE_ID}, ensure_ascii=False, indent=2))


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
    return "\n".join(
        [
            "# Pionex Opening Candidate Refresh - 2026-05-09",
            "",
            "## Ergebnis",
            "",
            f"- Candidate: `{payload['candidate_id']}`",
            f"- Steuerwirksam gebucht: `{payload['tax_effective']}`",
            f"- Status: `{payload['status']}`",
            f"- Pionex-Plattform erforderlicher Startbestand: `{payload['pionex_platform_required_opening_usdt']} USDT`",
            f"- Opening ab erstem Bruch: `{payload['pionex_first_negative_required_opening_usdt']} USDT`",
            f"- Aktueller aktiver globaler transienter Rest: `{payload['current_active_source_global_transient_required_usdt']} USDT`",
            "",
            "## Bewertung",
            "",
            "- Der Kandidat bleibt ein Review-/Nachweisobjekt, keine automatische Steuerbuchung.",
            "- Der globale Rest ist nach aktiver Quellenfilterung weiterhin materiell und ohne Pionex-Kontosnapshot/Bot-Startnachweis nicht automatisch zu buchen.",
            "- Fuer einen finalen Report braucht es entweder Pionex-Evidence oder eine dokumentierte fachliche Entscheidung zur Ersatzrekonstruktion.",
            "",
            "## Referenzen",
            "",
            f"- Transient: `{payload['reports']['transient']}`",
            f"- Detail: `{payload['reports']['detail']}`",
            f"- Endbestand: `{payload['reports']['end_balance']}`",
            "",
        ]
    )


if __name__ == "__main__":
    main()
