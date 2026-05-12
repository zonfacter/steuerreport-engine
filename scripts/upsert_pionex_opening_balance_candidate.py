#!/usr/bin/env python3
"""Persist the Pionex USDT opening-balance candidate for review/API access."""

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


def main() -> None:
    candidates = load_candidates()
    entry = {
        "candidate_id": CANDIDATE_ID,
        "platform": "pionex",
        "asset": "USDT",
        "quantity_delta": "1643.40556756620000000000",
        "effective_timestamp_utc": "2021-12-28T00:49:11+00:00",
        "adjustment_type": "opening_balance_candidate",
        "status": "needs_evidence",
        "reason_code": "missing_pionex_bot_start_capital",
        "note": (
            "Pionex-only USDT ledger is nearly closed at final balance, but reaches "
            "-1643.40556756620000000000 USDT before known later deposits. Candidate is not tax-effective; "
            "requires Pionex account statement, bot start capital evidence, support response, or explicit manual review."
        ),
        "evidence": {
            "report": "docs/65_PIONEX_USDT_OPENING_BALANCE_REVIEW_2026-05-08.md",
            "balance_audit_report": "docs/64_CHRONOLOGICAL_BALANCE_BREAK_AUDIT_AFTER_BINANCE_EARN_2026-05-08.md",
            "pionex_only_event_count": 906,
            "pionex_only_final_balance_usdt": "0.89137980652611250000",
            "pionex_only_worst_balance_usdt": "-1643.40556756620000000000",
            "first_negative_event_id": "dbf50e86f138a6ee50238468278e3f19517edfa373ab9b1e025a92c4e21139dd",
            "worst_event_id": "7ba599acc2c76180d3f572985a30b19b379e5391fedb433874d042464142e12c",
        },
        "tax_effective": False,
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    candidates[CANDIDATE_ID] = entry
    put_admin_setting(SETTING_KEY, candidates, is_secret=False)
    print(json.dumps({"saved": True, "candidate_id": CANDIDATE_ID, "tax_effective": False}, indent=2))


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


if __name__ == "__main__":
    main()
