#!/usr/bin/env python3
"""Import Binance SOL staking primary record that minted BNSOL."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.service import confirm_import

PROBE_JSON = ROOT / "var" / "binance_bnsol_jan_mar2025_probe_2026-05-08.json"
OUTPUT_JSON = ROOT / "var" / "binance_sol_staking_bnsol_primary_import_2026-05-08.json"
SOURCE_NAME = "binance_sol_staking_bnsol_primary_2025_api_2026-05-08"


def main() -> None:
    probe = json.loads(PROBE_JSON.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for result in probe.get("results", []):
        if not isinstance(result, dict):
            continue
        if result.get("path") != "/sapi/v1/sol-staking/sol/history/stakingHistory":
            continue
        for raw in result.get("rows", []):
            if not isinstance(raw, dict):
                continue
            normalized = normalize_staking_row(raw)
            if normalized:
                rows.extend(normalized)
    import_result = confirm_import(SOURCE_NAME, rows)
    out = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_probe": str(PROBE_JSON),
        "source_name": SOURCE_NAME,
        "normalized_event_count": len(rows),
        "import_result": import_result,
        "normalized_rows": rows,
    }
    OUTPUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"normalized_event_count": len(rows), "import": import_result}, ensure_ascii=False, indent=2))


def normalize_staking_row(raw: dict[str, Any]) -> list[dict[str, Any]]:
    asset = str(raw.get("asset") or "").upper().strip()
    distribute_asset = str(raw.get("distributeAsset") or "").upper().strip()
    amount = str(raw.get("amount") or "").strip()
    distribute_amount = str(raw.get("distributeAmount") or "").strip()
    if asset != "SOL" or distribute_asset != "BNSOL" or not amount or not distribute_amount:
        return []
    timestamp = _to_utc_iso(raw.get("time"))
    if not timestamp:
        return []
    tx_base = f"binance-sol-staking:{raw.get('time')}:{asset}:{amount}:{distribute_asset}:{distribute_amount}"
    raw_row = {**raw, "__source_endpoint": "sol-staking/sol/history/stakingHistory"}
    return [
        {
            "timestamp_utc": timestamp,
            "asset": asset,
            "quantity": amount,
            "price": "",
            "fee": "0",
            "fee_asset": "",
            "side": "out",
            "event_type": "staking_conversion",
            "tx_id": f"{tx_base}:out:{asset}",
            "source": "binance_api",
            "source_endpoint": "sol_staking_history",
            "raw_row": raw_row,
        },
        {
            "timestamp_utc": timestamp,
            "asset": distribute_asset,
            "quantity": distribute_amount,
            "price": "",
            "fee": "0",
            "fee_asset": "",
            "side": "in",
            "event_type": "staking_conversion",
            "tx_id": f"{tx_base}:in:{distribute_asset}",
            "source": "binance_api",
            "source_endpoint": "sol_staking_history",
            "raw_row": raw_row,
        },
    ]


def _to_utc_iso(value: Any) -> str:
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC).isoformat()
    except (TypeError, ValueError):
        return ""


if __name__ == "__main__":
    main()
