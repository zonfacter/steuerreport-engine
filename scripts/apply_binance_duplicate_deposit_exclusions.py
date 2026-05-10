#!/usr/bin/env python3
"""Exclude duplicate Binance file/API deposit rows when Binance API primary exists."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import put_admin_setting
from tax_engine.api.dashboard import _payload_asset_canonical_symbol
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions

CREATED_DATE = "2026-05-09"
SETTING_OVERRIDES = "runtime.tax_event_overrides"
REPORT_JSON = ROOT / "var" / f"binance_duplicate_deposit_exclusions_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"138_BINANCE_DUPLICATE_DEPOSIT_EXCLUSIONS_{CREATED_DATE}.md"
REASON_CODE = "duplicate_primary_import"
REASON_LABEL = "Doppelte Binance-Deposit-Quelle, Binance API bleibt aktiv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    matches = find_matches()
    now = datetime.now(UTC).isoformat()
    import_result = None
    if args.execute:
        overrides = load_overrides()
        inserted = 0
        unchanged = 0
        for item in matches:
            event_id = item["binance_file_event_id"]
            entry = {
                "tax_category": "EXCLUDED",
                "reason_code": REASON_CODE,
                "reason_label": REASON_LABEL,
                "note": (
                    "Binance file/import deposit duplicates Binance API primary deposit for same tx/asset/quantity. "
                    f"TX {item['tx_id']} asset {item['asset']} quantity {item['quantity']}. "
                    "Keep binance_api row because it contains API id/network/address status fields."
                ),
                "updated_at_utc": now,
            }
            if overrides.get(event_id) == entry:
                unchanged += 1
                continue
            overrides[event_id] = entry
            inserted += 1
        put_admin_setting(SETTING_OVERRIDES, overrides, is_secret=False)
        import_result = {"excluded_event_count": inserted, "unchanged_exclusions": unchanged}
    audit = {
        "created_at_utc": now,
        "mode": "execute" if args.execute else "preview",
        "match_count": len(matches),
        "asset_counts": count_by(matches, "asset"),
        "matches": matches[:1000],
        "import_result": import_result,
        "interpretation": [
            "Only source=binance deposit-like rows are excluded when an exact source=binance_api deposit exists.",
            "The match key is tx_id + asset + quantity. Withdrawals and trades are not touched.",
            "This removes file/API duplicate deposits from platform-ledger and transfer-group matching.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "mode": audit["mode"], "match_count": len(matches), "asset_counts": audit["asset_counts"], "import_result": import_result}, ensure_ascii=False, indent=2))


def find_matches() -> list[dict[str, Any]]:
    reviewed, _ = apply_review_actions(STORE.list_raw_events())
    api_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    file_rows: list[dict[str, Any]] = []
    for event in reviewed:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if not payload:
            continue
        source = str(payload.get("source") or "").lower().strip()
        side = str(payload.get("side") or "").lower().strip()
        event_type = str(payload.get("event_type") or "").lower().strip()
        if side != "in" or event_type not in {"deposit", ""}:
            continue
        tx_id = str(payload.get("tx_id") or "").strip()
        if not tx_id:
            continue
        asset = _payload_asset_canonical_symbol(payload)
        quantity = plain(abs(dec(payload.get("quantity"))))
        item = {"event": event, "payload": payload, "tx_id": tx_id, "asset": asset, "quantity": quantity}
        key = (tx_id, asset, quantity)
        if source == "binance_api":
            api_by_key[key].append(item)
        elif source == "binance":
            file_rows.append(item)
    matches = []
    for item in file_rows:
        primary = api_by_key.get((item["tx_id"], item["asset"], item["quantity"]), [])
        if not primary:
            continue
        payload = item["payload"]
        api_payload = primary[0]["payload"]
        matches.append(
            {
                "binance_file_event_id": str(item["event"].get("unique_event_id") or ""),
                "binance_api_event_id": str(primary[0]["event"].get("unique_event_id") or ""),
                "timestamp_utc": str(payload.get("timestamp_utc") or ""),
                "api_timestamp_utc": str(api_payload.get("timestamp_utc") or ""),
                "asset": item["asset"],
                "quantity": item["quantity"],
                "tx_id": item["tx_id"],
                "file_event_type": str(payload.get("event_type") or ""),
                "api_event_type": str(api_payload.get("event_type") or ""),
            }
        )
    return sorted(matches, key=lambda row: (row["timestamp_utc"], row["asset"], row["tx_id"], row["binance_file_event_id"]))


def load_overrides() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting(SETTING_OVERRIDES)
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    return {str(key): value for key, value in raw.items() if isinstance(value, dict)} if isinstance(raw, dict) else {}


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        counts[value] = counts.get(value, 0) + 1
    return counts


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Binance Duplicate Deposit Exclusions - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Matches: `{audit['match_count']}`",
        f"- Assets: `{audit['asset_counts']}`",
        f"- Import: `{audit['import_result']}`",
        "",
        "## Matches",
        "",
    ]
    for item in audit["matches"][:120]:
        lines.append(
            f"- `{item['timestamp_utc']}` `{item['asset']}` `{item['quantity']}` "
            f"tx `{item['tx_id']}` file `{item['binance_file_event_id']}` api `{item['binance_api_event_id']}`"
        )
    if len(audit["matches"]) > 120:
        lines.append(f"- ... weitere `{len(audit['matches']) - 120}` Matches im JSON.")
    lines += [
        "",
        "## Bewertung",
        "",
        "- Binance API bleibt aktiv als primaere Quelle fuer Deposits.",
        "- Datei-/CSV-Deposit-Zeilen mit identischer TXID/Asset/Menge werden ausgeschlossen.",
        "- Dadurch werden Transfergruppen und Plattform-Salden nicht durch doppelte Binance-Zufluesse verzerrt.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
