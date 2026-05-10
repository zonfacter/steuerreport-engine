#!/usr/bin/env python3
"""Import narrow Bitget BTC 2024 reconstruction rows from Blockpit reference evidence."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.service import confirm_import  # noqa: E402
from tax_engine.ingestion.store import STORE  # noqa: E402

CREATED_DATE = "2026-05-09"
SOURCE_NAME = "bitget_btc_2024_blockpit_reconstruction"
REPORT_JSON = ROOT / "var" / f"bitget_btc_2024_blockpit_reconstruction_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"143_BITGET_BTC_2024_BLOCKPIT_RECONSTRUCTION_{CREATED_DATE}.md"

REFERENCE_EVENT_IDS = {
    "deposit": "5ad748422708de3e9af93735d7f1c1be19ba9e6311028487d9a24966def5c0bd",
    "trade": "1f629f06d8033d4d04ee82c522f0f208d0c635abae91fb142311f4c0add4d3ea",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    references = {name: load_reference(event_id) for name, event_id in REFERENCE_EVENT_IDS.items()}
    rows = [deposit_row(references["deposit"]), trade_row(references["trade"])]
    existing = find_existing(rows)
    import_result = None
    if args.execute and not existing:
        import_result = confirm_import(source_name=SOURCE_NAME, rows=rows)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": "execute" if args.execute else "preview",
        "source_name": SOURCE_NAME,
        "reference_event_ids": REFERENCE_EVENT_IDS,
        "selected_row_count": len(rows),
        "existing_reconstruction_count": len(existing),
        "selected_rows": rows,
        "existing_reconstruction_events": existing,
        "import_result": import_result,
        "interpretation": [
            "Bitget Tax API starts the BTC sequence with four BTC out legs on 2024-04-14, causing a platform-local negative BTC balance.",
            "Blockpit's Bitget API reference contains an earlier BTC deposit on 2024-03-07 and a small BTC sell on 2024-03-11.",
            "Only these two pre-break rows are imported as narrow reconstruction evidence; the 2024-04-14 Blockpit merged trade is not imported to avoid duplicating Bitget Tax API rows.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "mode": audit["mode"], "existing": len(existing), "import_result": import_result}, ensure_ascii=False, indent=2))


def load_reference(event_id: str) -> dict[str, Any]:
    event = STORE.get_raw_event(event_id)
    if event is None:
        raise SystemExit(f"missing reference event {event_id}")
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    if not payload:
        raise SystemExit(f"reference event {event_id} has no payload")
    return {"event_id": event_id, "payload": payload}


def deposit_row(reference: dict[str, Any]) -> dict[str, Any]:
    payload = reference["payload"]
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    return {
        "timestamp_utc": "2024-03-07T19:55:23+00:00",
        "source": SOURCE_NAME,
        "event_type": "deposit",
        "side": "in",
        "asset": "BTC",
        "quantity": "0.0046913",
        "price": "",
        "fee": "0",
        "fee_asset": "",
        "tx_id": "1149723330782900226",
        "reference_event_id": reference["event_id"],
        "raw_row": {
            "reconstruction_reason": "bitget_tax_api_missing_pre_break_btc_deposit",
            "reference_source": "blockpit",
            "reference_tx_id": str(raw.get("Trx. ID (optional)") or payload.get("tx_id") or ""),
            "reference_label": str(raw.get("Label") or ""),
            "reference_comment": str(raw.get("Comment (optional)") or ""),
        },
    }


def trade_row(reference: dict[str, Any]) -> dict[str, Any]:
    payload = reference["payload"]
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    return {
        "timestamp_utc": "2024-03-11T11:47:00+00:00",
        "source": SOURCE_NAME,
        "event_type": "trade",
        "side": "sell",
        "asset": "BTC",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "quantity": "0.000121",
        "quote_quantity": "8.73522595",
        "price": "",
        "fee": "0.00873522595",
        "fee_asset": "USDT",
        "tx_id": "1151049976081231876-1151049976081231877",
        "reference_event_id": reference["event_id"],
        "raw_row": {
            "reconstruction_reason": "bitget_tax_api_missing_pre_break_btc_sell",
            "reference_source": "blockpit",
            "reference_tx_id": str(raw.get("Trx. ID (optional)") or payload.get("tx_id") or ""),
            "reference_label": str(raw.get("Label") or ""),
            "reference_comment": str(raw.get("Comment (optional)") or ""),
        },
    }


def find_existing(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    wanted = {(str(row["tx_id"]), str(row["asset"]), str(row["quantity"]), str(row["source"])) for row in rows}
    matches: list[dict[str, str]] = []
    for event in STORE.list_raw_events():
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        key = (
            str(payload.get("tx_id") or ""),
            str(payload.get("asset") or ""),
            str(payload.get("quantity") or ""),
            str(payload.get("source") or ""),
        )
        if key in wanted:
            matches.append(
                {
                    "event_id": str(event.get("unique_event_id") or ""),
                    "timestamp_utc": str(payload.get("timestamp_utc") or ""),
                    "source": str(payload.get("source") or ""),
                    "asset": str(payload.get("asset") or ""),
                    "quantity": str(payload.get("quantity") or ""),
                    "tx_id": str(payload.get("tx_id") or ""),
                }
            )
    return matches


def render_doc(audit: dict[str, Any]) -> str:
    result = audit.get("import_result") or {}
    lines = [
        "# Bitget BTC 2024 Blockpit Reconstruction - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Importierte Events: `{result.get('inserted_events', 0)}`",
        f"- Duplikate: `{result.get('duplicate_events', 0)}`",
        f"- Bestehende Rekonstruktionszeilen: `{audit['existing_reconstruction_count']}`",
        "",
        "## Rekonstruktionszeilen",
        "",
    ]
    for row in audit["selected_rows"]:
        lines.append(
            f"- `{row['timestamp_utc']}` `{row['event_type']}` `{row['side']}` `{row['quantity']} {row['asset']}` "
            f"tx `{row['tx_id']}` reference `{row['reference_event_id']}`"
        )
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {item}" for item in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
