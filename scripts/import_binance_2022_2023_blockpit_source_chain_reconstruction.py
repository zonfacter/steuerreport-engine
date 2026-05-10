#!/usr/bin/env python3
"""Import the closed Binance 2022/2023 Blockpit source-chain reconstruction."""

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
SOURCE_NAME = "binance_2022_2023_blockpit_source_chain_reconstruction"
REPORT_JSON = ROOT / "var" / f"binance_2022_2023_blockpit_source_chain_reconstruction_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"155_BINANCE_2022_2023_BLOCKPIT_SOURCE_CHAIN_RECONSTRUCTION_{CREATED_DATE}.md"

TARGET_TRX_IDS = [
    "N01288537375393490944111444",  # EUR -> BUSD
    "85361646",  # BUSD -> DOGE
    "59571809",  # DOGE -> BTC
    "59817964",  # BTC -> DOGE
    "59817965",  # BTC -> DOGE
    "N01333135634309321728031744",  # EUR -> BUSD
    "6019749",  # BUSD -> HNT
    "6019751",  # BUSD -> HNT
    "6019758",  # BUSD -> HNT
    "6026452",  # HNT -> BUSD
    "6026453",  # HNT -> BUSD
    "953994324",  # BUSD -> BTC
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    references = load_references()
    rows = [trade_row(reference) for reference in references]
    existing = find_existing(rows)
    import_result = None
    if args.execute and not existing:
        import_result = confirm_import(source_name=SOURCE_NAME, rows=rows)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": "execute" if args.execute else "preview",
        "source_name": SOURCE_NAME,
        "target_trx_ids": TARGET_TRX_IDS,
        "selected_row_count": len(rows),
        "existing_reconstruction_count": len(existing),
        "selected_rows": rows,
        "existing_reconstruction_events": existing,
        "import_result": import_result,
        "interpretation": [
            "The earlier BTC and BUSD gaps are explained by one closed Binance source chain in Blockpit's Binance API reference data.",
            "The full sequence starts with EUR->BUSD, continues through DOGE/HNT spot trades, and ends with BUSD->BTC before the SOL buys.",
            "The full chain is imported together because isolated rows would shift the gap between BTC, BUSD and DOGE/HNT.",
            "The chain leaves the BUSD dust conversion amount effectively covered without creating new negative intermediate balances in the pre-import simulation.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "mode": audit["mode"], "existing": len(existing), "import_result": import_result}, ensure_ascii=False, indent=2))


def load_references() -> list[dict[str, Any]]:
    by_trx: dict[str, dict[str, Any]] = {}
    for event in STORE.list_raw_events():
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        if str(payload.get("source") or "").lower() != "blockpit":
            continue
        if "binance" not in str(raw.get("Integration Name") or raw.get("Source Name") or "").lower():
            continue
        trx_id = str(raw.get("Trx. ID (optional)") or "").strip()
        if trx_id not in TARGET_TRX_IDS or trx_id in by_trx:
            continue
        by_trx[trx_id] = {"event_id": str(event.get("unique_event_id") or ""), "payload": payload}
    missing = [trx_id for trx_id in TARGET_TRX_IDS if trx_id not in by_trx]
    if missing:
        raise SystemExit(f"missing Blockpit reference trx ids: {missing}")
    return [by_trx[trx_id] for trx_id in TARGET_TRX_IDS]


def trade_row(reference: dict[str, Any]) -> dict[str, Any]:
    payload = reference["payload"]
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    incoming_asset = str(raw.get("Incoming Asset") or "").upper().strip()
    outgoing_asset = str(raw.get("Outgoing Asset") or "").upper().strip()
    incoming_amount = str(raw.get("Incoming Amount") or "").strip()
    outgoing_amount = str(raw.get("Outgoing Amount") or "").strip()
    fee = str(raw.get("Fee Amount (optional)") or "0").strip() or "0"
    fee_asset = str(raw.get("Fee Asset (optional)") or "").upper().strip()
    timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    trx_id = str(raw.get("Trx. ID (optional)") or "").strip()
    if not incoming_asset or not outgoing_asset or not incoming_amount or not outgoing_amount or not timestamp or not trx_id:
        raise SystemExit(f"reference {reference['event_id']} is not a complete trade reference")
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
        "tx_id": f"binance-source-chain-reconstruction:{trx_id}",
        "reference_event_id": reference["event_id"],
        "raw_row": {
            "reconstruction_reason": "binance_missing_closed_source_chain_before_2023_sol_buys",
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
        "# Binance 2022/2023 Blockpit Source Chain Reconstruction - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Ausgewaehlte Trades: `{audit['selected_row_count']}`",
        f"- Importierte Events: `{result.get('inserted_events', 0)}`",
        f"- Duplikate: `{result.get('duplicate_events', 0)}`",
        f"- Bestehende Rekonstruktionszeilen: `{audit['existing_reconstruction_count']}`",
        "",
        "## Rekonstruktionszeilen",
        "",
    ]
    for row in audit["selected_rows"]:
        lines.append(
            f"- `{row['timestamp_utc']}` tx `{row['tx_id']}`: `{row['quantity']} {row['asset']}` gegen "
            f"`{row['quote_quantity']} {row['quote_asset']}` fee `{row['fee']} {row['fee_asset']}`"
        )
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {item}" for item in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
