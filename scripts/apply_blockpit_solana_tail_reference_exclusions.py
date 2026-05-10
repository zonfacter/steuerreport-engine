#!/usr/bin/env python3
"""Exclude reviewed Blockpit Solana tail duplicates with existing primary Solana rows."""

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

OUTPUT_JSON = ROOT / "var" / "blockpit_solana_tail_reference_exclusions_2026-05-08.json"
SETTING_KEY = "runtime.tax_event_overrides"
REASON_CODE = "reference_import_only"
REASON_LABEL = "Nur Referenzimport, Primaerdaten sind bereits vorhanden"

REVIEWED_SIGNATURES = {
    "27KoLKddp5wYAvkJftuKL2EMrewvvNj91H83BB64LMUakFKXd32ArEVCv6Y6nq29L4c86y6joeXGUGB7wayNVMrj",
    "4oFUuoh2rhCCA8KiG1evNgb3pmYkyLwhYoiusvEWUozfjWiSg85L11zhwqQiKEU2EbJ1zMAGmKbJkDJUMrfKDNgz",
    "2h9rkbgcgaXAnNtHYCupfwrNzTnaJ9TUpbKzHSuB3B9kLmxUrwfwrHHL8gWMQfvPJ82LksmDEkxQhNHbd9AWj9kb",
}


def main() -> None:
    raw_events = STORE.list_raw_events()
    primary_by_sig = {sig: [] for sig in REVIEWED_SIGNATURES}
    blockpit_by_sig = {sig: [] for sig in REVIEWED_SIGNATURES}

    for event in raw_events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        source = str(payload.get("source") or "")
        tx_id = str(payload.get("tx_id") or "")
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        blockpit_sig = str(raw.get("Trx. ID (optional)") or "")
        for sig in REVIEWED_SIGNATURES:
            if source in {"solana_rpc", "solscan_wallet_discovery"} and tx_id == sig:
                primary_by_sig[sig].append(_slim(event))
            if source == "blockpit" and blockpit_sig == sig:
                blockpit_by_sig[sig].append(_slim(event))

    safe_ids: list[str] = []
    evidence: dict[str, Any] = {"signatures": {}}
    for sig in sorted(REVIEWED_SIGNATURES):
        primaries = primary_by_sig[sig]
        blockpit_rows = blockpit_by_sig[sig]
        if not primaries or not blockpit_rows:
            continue
        safe_ids.extend(row["event_id"] for row in blockpit_rows)
        evidence["signatures"][sig] = {
            "primary_count": len(primaries),
            "blockpit_reference_count": len(blockpit_rows),
            "primary_events": primaries,
            "blockpit_reference_events": blockpit_rows,
        }

    overrides = _load_overrides()
    now = datetime.now(UTC).isoformat()
    inserted = 0
    unchanged = 0
    for event_id in safe_ids:
        entry = {
            "tax_category": "EXCLUDED",
            "reason_code": REASON_CODE,
            "reason_label": REASON_LABEL,
            "note": (
                "Blockpit Solana-Referenzzeile ausgeschlossen, weil fuer dieselbe On-Chain-Signatur "
                "bereits Solana/Solscan-Primaerevents vorhanden sind. "
                f"Quelle: {OUTPUT_JSON.name}"
            ),
            "updated_at_utc": now,
        }
        if overrides.get(event_id) == entry:
            unchanged += 1
            continue
        overrides[event_id] = entry
        inserted += 1

    put_admin_setting(SETTING_KEY, overrides, is_secret=False)
    evidence.update(
        {
            "generated_at_utc": now,
            "safe_exclusion_candidate_event_ids": safe_ids,
            "inserted_or_updated": inserted,
            "unchanged": unchanged,
        }
    )
    OUTPUT_JSON.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"candidate_count": len(safe_ids), "inserted_or_updated": inserted, "unchanged": unchanged}, indent=2))


def _slim(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    return {
        "event_id": str(event.get("unique_event_id") or ""),
        "timestamp_utc": str(payload.get("timestamp_utc") or ""),
        "source": str(payload.get("source") or ""),
        "event_type": str(payload.get("event_type") or ""),
        "side": str(payload.get("side") or ""),
        "asset": str(payload.get("asset") or ""),
        "quantity": str(payload.get("quantity") or ""),
        "tx_id": str(payload.get("tx_id") or ""),
        "blockpit_signature": str(raw.get("Trx. ID (optional)") or ""),
    }


def _load_overrides() -> dict[str, dict[str, Any]]:
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
