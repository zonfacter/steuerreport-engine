#!/usr/bin/env python3
"""Import narrow Binance SOL 2023 reconstruction rows from Blockpit Binance API references."""

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
SOURCE_NAME = "binance_sol_2023_blockpit_reconstruction"
REPORT_JSON = ROOT / "var" / f"binance_sol_2023_blockpit_reconstruction_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"149_BINANCE_SOL_2023_BLOCKPIT_RECONSTRUCTION_{CREATED_DATE}.md"

REFERENCE_EVENT_IDS = {
    "buy_2023_05_04": "ef04828f55b9b59f38e855ab46522200d066bc034c95f8233ff474bbac18ed8a",
    "buy_2023_06_10_0_36": "309d4bdad0c18c5dfa74a3160f9e1ba61b0ffe77f7e4d5d3967ee3f870937999",
    "buy_2023_06_10_21_89": "4a82efdc8a4bf041a13a8333d258f6123a8db6e1d06f46c3ba0acae2f5f83afd",
    "buy_2023_06_10_31_88": "92b0168c781ebabe4a5ec6923e47cd32260e4056583c053081ac77b04f6b0ff4",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    references = {name: load_reference(event_id) for name, event_id in REFERENCE_EVENT_IDS.items()}
    rows = [trade_row(reference) for reference in references.values()]
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
            "Active Binance SOL inventory turns negative before the 2023-05-08 and 2023-06-10 withdrawals.",
            "Blockpit contains Binance API reference spot buys immediately before those withdrawals.",
            "Only four SOL buy rows are imported as narrow reconstruction evidence; matching Blockpit withdrawal rows are not imported because Binance API withdrawals and Solana wallet counterflows already exist as active primary rows.",
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
    if incoming_asset != "SOL" or not outgoing_asset or not incoming_amount or not outgoing_amount or not timestamp:
        raise SystemExit(f"reference {reference['event_id']} is not a SOL buy reference")
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
        "tx_id": f"binance-sol-2023-reconstruction:{reference['event_id']}",
        "reference_event_id": reference["event_id"],
        "raw_row": {
            "reconstruction_reason": "binance_api_missing_sol_spot_buy_before_withdrawal",
            "reference_source": "blockpit",
            "reference_label": str(raw.get("Label") or ""),
            "reference_comment": str(raw.get("Comment (optional)") or ""),
            "reference_tx_id": str(raw.get("Trx. ID (optional)") or payload.get("tx_id") or ""),
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
        "# Binance SOL 2023 Blockpit Reconstruction - 2026-05-09",
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
            f"- `{row['timestamp_utc']}` `buy` `{row['quantity']} {row['asset']}` gegen "
            f"`{row['quote_quantity']} {row['quote_asset']}` fee `{row['fee']} {row['fee_asset']}` "
            f"reference `{row['reference_event_id']}`"
        )
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {item}" for item in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
