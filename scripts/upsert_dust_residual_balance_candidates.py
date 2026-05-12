#!/usr/bin/env python3
"""Persist non-tax-effective review candidates for remaining tiny dust residuals."""

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
OUTPUT_JSON = ROOT / "var" / "dust_residual_balance_candidates_2026-05-08.json"


def main() -> None:
    now = datetime.now(UTC).isoformat()
    candidates = load_candidates()
    entries = {
        "binance-vtho-dust-residual-2023-05-02": {
            "candidate_id": "binance-vtho-dust-residual-2023-05-02",
            "platform": "binance",
            "asset": "VTHO",
            "quantity_delta": "42.39387934",
            "effective_timestamp_utc": "2023-05-02T04:13:22+00:00",
            "adjustment_type": "dust_residual_candidate",
            "status": "needs_evidence",
            "reason_code": "missing_binance_dust_source_balance",
            "note": (
                "Binance Dust Convert transId 136251331484 consumes 42.39387934 VTHO, "
                "but no prior VTHO inflow is present in current effective events. "
                "Binance asset-dividend probe 2021-2023 found no VTHO rows. Candidate is review-only."
            ),
            "evidence": {
                "balance_audit_report": "docs/76_CHRONOLOGICAL_BALANCE_BREAK_AUDIT_AFTER_BINANCE_BNSOL_PRIMARY_2026-05-08.md",
                "dust_tx_id": "136251331484",
                "dust_timestamp_utc": "2023-05-02T04:13:23+00:00",
                "event_id": "61f4964558fe99fefaf53cbb118095ae2953e13528b8a34ef8a167ba3c42ef8d",
                "dividend_probe": "var/binance_asset_dividend_2021_2023_90d_probe_2026-05-08.json",
            },
            "tax_effective": False,
            "updated_at_utc": now,
        },
        "mixed-busd-dust-residual-2023-05-02": {
            "candidate_id": "mixed-busd-dust-residual-2023-05-02",
            "platform": "mixed",
            "asset": "BUSD",
            "quantity_delta": "0.55168701480000000000",
            "effective_timestamp_utc": "2023-01-14T08:14:02+00:00",
            "adjustment_type": "dust_residual_candidate",
            "status": "needs_review",
            "reason_code": "mixed_pionex_binance_busd_dust_residual",
            "note": (
                "Global BUSD ledger ends at -0.55168701480000000000 after Pionex BUSD fees/trades "
                "and Binance Dust Convert transId 136251331484. This is a tiny residual and not a "
                "safe platform-specific primary import. Candidate is review-only and must not be "
                "made tax-effective without explicit fachliche Entscheidung."
            ),
            "evidence": {
                "balance_audit_report": "docs/76_CHRONOLOGICAL_BALANCE_BREAK_AUDIT_AFTER_BINANCE_BNSOL_PRIMARY_2026-05-08.md",
                "first_negative_event_id": "266f6a64a54bf3d60213ca7cf8cd651995d597291edb5487b90ff8dc6f374543",
                "worst_event_id": "bbdf8fcb5f2c87f9d1a826fbc4b2c16de49a42b06cda2ea373279da7aa01b148",
                "dust_tx_id": "136251331484",
                "dust_timestamp_utc": "2023-05-02T04:13:23+00:00",
                "dividend_probe": "var/binance_asset_dividend_2021_2023_90d_probe_2026-05-08.json",
            },
            "tax_effective": False,
            "updated_at_utc": now,
        },
    }
    candidates.update(entries)
    put_admin_setting(SETTING_KEY, candidates, is_secret=False)
    out = {"created_at_utc": now, "saved_candidate_ids": sorted(entries), "entries": entries}
    OUTPUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"saved": sorted(entries), "tax_effective": False}, indent=2, ensure_ascii=False))


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
