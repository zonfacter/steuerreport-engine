#!/usr/bin/env python3
"""Exclude reviewed Blockpit dust-convert reference rows when Binance primary rows exist."""

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

SETTING_KEY = "runtime.tax_event_overrides"
REPORT_JSON = ROOT / "var" / "binance_dust_blockpit_reference_exclusions_2026-05-09.json"
REPORT_MD = ROOT / "docs" / "105_BINANCE_DUST_BLOCKPIT_REFERENCE_EXCLUSIONS_2026-05-09.md"
REASON_CODE = "reference_import_only"
REASON_LABEL = "Nur Referenzimport, Primärdaten sind bereits vorhanden"

EXCLUSIONS = [
    {
        "event_id": "60a6999481873ae7bd8c6bb5a0373b89297497257a9faab26a8a411705c3b670",
        "asset": "VTHO",
        "blockpit_tx_id": "blockpit-7068:out",
        "primary_source": "binance_api",
        "primary_tx_id": "136251331484",
        "quantity": "42.39387934",
        "timestamp_utc": "2023-05-02T04:13:23+00:00",
    },
    {
        "event_id": "4dbbe2b81106a5e333c5208d360f775d54e4340e470147d8960610d682cb3b8e",
        "asset": "BUSD",
        "blockpit_tx_id": "blockpit-7074:out",
        "primary_source": "binance_api",
        "primary_tx_id": "136251331484",
        "quantity": "0.55379925",
        "timestamp_utc": "2023-05-02T04:13:23+00:00",
    },
    {
        "event_id": "bfaeb566d635a01a81a9384b9c3958145e0619975559b5bf7da90de40b26f4ca",
        "asset": "GFT",
        "blockpit_tx_id": "blockpit-7619:out",
        "primary_source": "binance_api",
        "primary_tx_id": "47394524243",
        "quantity": "0.0081",
        "timestamp_utc": "2021-03-29T16:48:07+00:00",
        "note": "Blockpit labels the dust row as GFT while Binance primary and trade history use legacy GTO.",
    },
]


def main() -> None:
    overrides = load_overrides()
    now = datetime.now(UTC).isoformat()
    inserted = 0
    unchanged = 0
    for item in EXCLUSIONS:
        entry = {
            "tax_category": "EXCLUDED",
            "reason_code": REASON_CODE,
            "reason_label": REASON_LABEL,
            "note": (
                f"Blockpit dust-convert reference for {item['asset']} excluded because Binance API primary "
                f"transaction {item['primary_tx_id']} exists with the same timestamp/quantity. "
                "Raw data remains stored for evidence."
            ),
            "updated_at_utc": now,
        }
        current = overrides.get(item["event_id"])
        if current == entry:
            unchanged += 1
            continue
        overrides[item["event_id"]] = entry
        inserted += 1
    put_admin_setting(SETTING_KEY, overrides, is_secret=False)
    audit = {
        "created_at_utc": now,
        "setting_key": SETTING_KEY,
        "reason_code": REASON_CODE,
        "candidate_count": len(EXCLUSIONS),
        "inserted_or_updated": inserted,
        "unchanged": unchanged,
        "exclusions": EXCLUSIONS,
        "interpretation": [
            "Only Blockpit reference rows are excluded; Binance API primary rows stay tax-effective.",
            "This removes duplicate dust-convert movements without deleting evidence.",
            "VTHO may still need a separate acquisition/reward evidence decision after duplicate removal.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "inserted_or_updated": inserted, "unchanged": unchanged}, ensure_ascii=False, indent=2))


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


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Binance Dust / Blockpit Reference Exclusions - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Gezielte Exclusion von Blockpit-Referenzzeilen, wenn dieselbe Dust-Convert-Bewegung bereits aus Binance API als Primaerdatensatz vorhanden ist.",
        "",
        f"- Kandidaten: `{audit['candidate_count']}`",
        f"- Eingetragen/aktualisiert: `{audit['inserted_or_updated']}`",
        f"- Unveraendert: `{audit['unchanged']}`",
        "",
        "## Exclusions",
        "",
    ]
    for item in audit["exclusions"]:
        lines.append(
            f"- `{item['asset']}` {item['timestamp_utc']} qty `{item['quantity']}`: "
            f"`{item['blockpit_tx_id']}` -> primary `{item['primary_source']}:{item['primary_tx_id']}`"
        )
        if item.get("note"):
            lines.append(f"  - {item['note']}")
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
