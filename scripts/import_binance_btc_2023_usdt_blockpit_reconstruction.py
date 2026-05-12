#!/usr/bin/env python3
"""Import the narrow Binance USDT->BTC 2023 source-chain reconstruction."""

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
SOURCE_NAME = "binance_btc_2023_usdt_blockpit_reconstruction"
REPORT_JSON = ROOT / "var" / f"binance_btc_2023_usdt_blockpit_reconstruction_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"153_BINANCE_BTC_2023_USDT_BLOCKPIT_RECONSTRUCTION_{CREATED_DATE}.md"
REFERENCE_EVENT_ID = "2c7b321092f19acd0280eb378b8b3ee7e7b4e8359ec5b8ec0806a3053b1b6390"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    reference = load_reference(REFERENCE_EVENT_ID)
    row = trade_row(reference)
    existing = find_existing([row])
    import_result = None
    if args.execute and not existing:
        import_result = confirm_import(source_name=SOURCE_NAME, rows=[row])
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": "execute" if args.execute else "preview",
        "source_name": SOURCE_NAME,
        "reference_event_id": REFERENCE_EVENT_ID,
        "selected_rows": [row],
        "existing_reconstruction_count": len(existing),
        "existing_reconstruction_events": existing,
        "import_result": import_result,
        "interpretation": [
            "The BTC source-chain candidate audit marks this Blockpit Binance API row as covered by active USDT balance at the event timestamp.",
            "Only this USDT->BTC trade is imported. BUSD, DOGE, VET and WIN references remain blocked because they need separate counterasset evidence first.",
            "This reduces the active BTC gap without shifting it into an uncovered counterasset.",
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


def trade_row(reference: dict[str, Any]) -> dict[str, Any]:
    payload = reference["payload"]
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    incoming_asset = str(raw.get("Incoming Asset") or payload.get("asset") or "").upper().strip()
    outgoing_asset = str(raw.get("Outgoing Asset") or "").upper().strip()
    incoming_amount = str(raw.get("Incoming Amount") or payload.get("quantity") or "").strip()
    outgoing_amount = str(raw.get("Outgoing Amount") or "").strip()
    fee = str(raw.get("Fee Amount (optional)") or "0").strip() or "0"
    fee_asset = str(raw.get("Fee Asset (optional)") or "").upper().strip()
    timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    trx_id = str(raw.get("Trx. ID (optional)") or payload.get("tx_id") or "").strip()
    if incoming_asset != "BTC" or outgoing_asset != "USDT" or not timestamp or not trx_id:
        raise SystemExit(f"reference {reference['event_id']} is not the expected USDT->BTC trade")
    return {
        "timestamp_utc": timestamp,
        "source": SOURCE_NAME,
        "event_type": "trade",
        "side": "buy",
        "asset": incoming_asset,
        "base_asset": incoming_asset,
        "quote_asset": outgoing_asset,
        "quantity": incoming_amount,
        "quote_quantity": outgoing_amount,
        "price": "",
        "fee": fee,
        "fee_asset": fee_asset,
        "tx_id": f"binance-btc-2023-usdt-reconstruction:{trx_id}",
        "reference_event_id": reference["event_id"],
        "raw_row": {
            "reconstruction_reason": "binance_api_missing_usdt_to_btc_trade_before_sol_buys",
            "reference_source": "blockpit",
            "reference_label": str(raw.get("Label") or ""),
            "reference_comment": str(raw.get("Comment (optional)") or ""),
            "reference_tx_id": trx_id,
            "incoming_amount": incoming_amount,
            "incoming_asset": incoming_asset,
            "outgoing_amount": outgoing_amount,
            "outgoing_asset": outgoing_asset,
            "fee": fee,
            "fee_asset": fee_asset,
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
        "# Binance BTC 2023 USDT Blockpit Reconstruction - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Importierte Events: `{result.get('inserted_events', 0)}`",
        f"- Duplikate: `{result.get('duplicate_events', 0)}`",
        f"- Bestehende Rekonstruktionszeilen: `{audit['existing_reconstruction_count']}`",
        "",
        "## Rekonstruktionszeile",
        "",
    ]
    for row in audit["selected_rows"]:
        lines.append(
            f"- `{row['timestamp_utc']}` `buy` `{row['quantity']} {row['asset']}` gegen "
            f"`{row['quote_quantity']} {row['quote_asset']}` fee `{row['fee']} {row['fee_asset']}` "
            f"reference `{row['reference_event_id']}`"
        )
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {item}" for item in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
