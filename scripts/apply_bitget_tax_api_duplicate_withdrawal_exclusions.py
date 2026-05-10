#!/usr/bin/env python3
"""Exclude Bitget Tax API withdrawal duplicates when Bitget API gross withdrawal exists."""

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
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions

CREATED_DATE = "2026-05-09"
SETTING_OVERRIDES = "runtime.tax_event_overrides"
REPORT_JSON = ROOT / "var" / f"bitget_tax_api_duplicate_withdrawal_exclusions_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"136_BITGET_TAX_API_DUPLICATE_WITHDRAWAL_EXCLUSIONS_{CREATED_DATE}.md"
REASON_CODE = "duplicate_primary_import"
REASON_LABEL = "Doppelte Primärquelle, Bitget API Bruttowert bleibt aktiv"


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
            event_id = item["tax_api_event_id"]
            entry = {
                "tax_category": "EXCLUDED",
                "reason_code": REASON_CODE,
                "reason_label": REASON_LABEL,
                "note": (
                    "Bitget Tax API withdrawal is a net withdrawal plus fee field for the same Bitget API gross "
                    f"withdrawal order {item['api_order_id']} / asset {item['asset']}. "
                    "Keep bitget_api because it contains chain address, tradeId and gross amount including fee."
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
        "matches": matches,
        "import_result": import_result,
        "interpretation": [
            "This excludes only Bitget Tax API withdrawal duplicates that have a matching Bitget API gross withdrawal.",
            "It does not exclude Bitget Tax API transfer-in rows; those can be necessary to explain internal account movement.",
            "For withdrawal inventory simulation, bitget_api size is used as gross outflow and tax_api net withdrawal is duplicate.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "mode": audit["mode"], "match_count": len(matches), "import_result": import_result}, ensure_ascii=False, indent=2))


def find_matches() -> list[dict[str, Any]]:
    reviewed, _ = apply_review_actions(STORE.list_raw_events())
    api_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    tax_rows: list[dict[str, Any]] = []
    for event in reviewed:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if not payload:
            continue
        source = str(payload.get("source") or "").lower().strip()
        event_type = str(payload.get("event_type") or "").lower().strip()
        if event_type != "withdrawal":
            continue
        raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        asset = str(payload.get("asset") or raw_row.get("coin") or "").upper().strip()
        if source == "bitget_api":
            order_id = str(raw_row.get("orderId") or payload.get("tx_id") or "").strip()
            api_by_key[(order_id, asset)].append({"event": event, "payload": payload, "raw": raw_row})
        elif source == "bitget_tax_api":
            biz_order_id = str(raw_row.get("bizOrderId") or "").strip()
            tax_rows.append({"event": event, "payload": payload, "raw": raw_row, "biz_order_id": biz_order_id, "asset": asset})
    matches: list[dict[str, Any]] = []
    for tax in tax_rows:
        candidates = api_by_key.get((tax["biz_order_id"], tax["asset"]), [])
        if not candidates:
            continue
        tax_qty = abs(dec(tax["payload"].get("quantity")))
        tax_fee = abs(dec(tax["payload"].get("fee")))
        for api in candidates:
            api_qty = abs(dec(api["payload"].get("quantity")))
            if abs((tax_qty + tax_fee) - api_qty) > Decimal("0.00000001"):
                continue
            matches.append(
                {
                    "tax_api_event_id": str(tax["event"].get("unique_event_id") or ""),
                    "bitget_api_event_id": str(api["event"].get("unique_event_id") or ""),
                    "asset": tax["asset"],
                    "timestamp_utc": str(tax["payload"].get("timestamp_utc") or ""),
                    "tax_api_order_id": str(tax["raw"].get("id") or ""),
                    "api_order_id": str(api["raw"].get("orderId") or ""),
                    "api_trade_id": str(api["raw"].get("tradeId") or ""),
                    "tax_net_quantity": plain(tax_qty),
                    "tax_fee": plain(tax_fee),
                    "api_gross_quantity": plain(api_qty),
                    "to_address": str(api["raw"].get("toAddress") or ""),
                }
            )
            break
    return sorted(matches, key=lambda row: (row["timestamp_utc"], row["asset"], row["api_order_id"]))


def load_overrides() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting(SETTING_OVERRIDES)
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    return {str(key): value for key, value in raw.items() if isinstance(value, dict)} if isinstance(raw, dict) else {}


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
        "# Bitget Tax API Duplicate Withdrawal Exclusions - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Matches: `{audit['match_count']}`",
        f"- Import: `{audit['import_result']}`",
        "",
        "## Matches",
        "",
    ]
    for item in audit["matches"]:
        lines.append(
            f"- `{item['timestamp_utc']}` `{item['asset']}` tax net `{item['tax_net_quantity']}` "
            f"fee `{item['tax_fee']}` api gross `{item['api_gross_quantity']}` "
            f"tax `{item['tax_api_order_id']}` api `{item['api_order_id']}` tx `{item['api_trade_id']}`"
        )
    lines += [
        "",
        "## Bewertung",
        "",
        "- Bitget API bleibt aktiv, weil diese Quelle Bruttobetrag, Zieladresse und Onchain-Trade-ID enthaelt.",
        "- Bitget Tax API Withdrawal ist fuer diese Matches ein doppelter Nettobeleg plus Fee-Feld.",
        "- Bitget Tax API Transfer-In bleibt aktiv, weil diese internen Bewegungen fuer Plattform-Salden relevant sein koennen.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
