#!/usr/bin/env python3
"""Import narrow Bitget HNT 2024 source-chain rows from Blockpit reference evidence."""

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
SOURCE_NAME = "bitget_hnt_2024_blockpit_source_chain"
REPORT_JSON = ROOT / "var" / f"bitget_hnt_2024_blockpit_source_chain_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"161_BITGET_HNT_2024_BLOCKPIT_SOURCE_CHAIN_{CREATED_DATE}.md"

TARGET_TRX_IDS = [
    "1149662750789283849",  # USDT deposit
    "1149663063353012237-1149663063353012239",  # USDT -> HNT
    "1149665078305042434",  # USDT deposit
    "1149665846282104838",  # USDT automatic withdrawal
    "1149666673075892227",  # USDT automatic withdrawal
    "1149723296817426454",  # HNT automatic deposit/mining label
    "1149723296540602374",  # USDT automatic deposit
    "1149723331042947074",  # USDT automatic deposit
    "1149723792982618118",  # USDT automatic withdrawal
    "1151050117659963402-1151050117659963403",  # USDT -> HNT
    "1151150847725088768",  # USDT automatic deposit
    "1151151935480082439",  # USDT automatic withdrawal
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    references = load_references()
    rows = [normalize_reference(reference) for reference in references]
    existing = find_existing(rows)
    import_result = None
    if args.execute and not existing:
        import_result = confirm_import(SOURCE_NAME, rows)
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
            "Bitget Tax API starts HNT with sell rows on 2024-04-02, but Blockpit's Bitget API reference contains a preceding internal source chain.",
            "The selected rows explain 12.499488 HNT before the first sell: 4.993 HNT buy minus fee, 6.561432 HNT automatic deposit, and 0.951 HNT buy minus fee.",
            "The USDT deposits/automatic withdrawals around those buys are imported with the HNT rows so the gap is not shifted into USDT.",
            "The already imported Bitget BTC->USDT reconstruction is not duplicated.",
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
        if "bitget" not in str(raw.get("Integration Name") or raw.get("Source Name") or "").lower():
            continue
        trx_id = str(raw.get("Trx. ID (optional)") or "").strip()
        if trx_id not in TARGET_TRX_IDS or trx_id in by_trx:
            continue
        by_trx[trx_id] = {"event_id": str(event.get("unique_event_id") or ""), "payload": payload}
    missing = [trx_id for trx_id in TARGET_TRX_IDS if trx_id not in by_trx]
    if missing:
        raise SystemExit(f"missing Blockpit reference trx ids: {missing}")
    return [by_trx[trx_id] for trx_id in TARGET_TRX_IDS]


def normalize_reference(reference: dict[str, Any]) -> dict[str, Any]:
    payload = reference["payload"]
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    label = str(raw.get("Label") or "").strip().lower()
    incoming_asset = str(raw.get("Incoming Asset") or "").upper().strip()
    outgoing_asset = str(raw.get("Outgoing Asset") or "").upper().strip()
    incoming_amount = str(raw.get("Incoming Amount") or "").strip()
    outgoing_amount = str(raw.get("Outgoing Amount") or "").strip()
    fee = str(raw.get("Fee Amount (optional)") or "0").strip() or "0"
    fee_asset = str(raw.get("Fee Asset (optional)") or "").upper().strip()
    timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    trx_id = str(raw.get("Trx. ID (optional)") or "").strip()
    if not timestamp or not trx_id:
        raise SystemExit(f"reference {reference['event_id']} has no timestamp/trx id")
    base = {
        "timestamp_utc": timestamp,
        "source": SOURCE_NAME,
        "price": "",
        "fee": fee,
        "fee_asset": fee_asset,
        "tx_id": f"bitget-hnt-2024-source-chain:{trx_id}",
        "reference_event_id": reference["event_id"],
        "raw_row": {
            "reconstruction_reason": "bitget_tax_api_missing_hnt_pre_break_source_chain",
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
    if label == "trade":
        return {
            **base,
            "event_type": "trade",
            "side": "buy",
            "asset": incoming_asset,
            "base_asset": incoming_asset,
            "quote_asset": outgoing_asset,
            "quantity": incoming_amount,
            "quote_quantity": outgoing_amount,
        }
    if incoming_asset and incoming_amount:
        return {
            **base,
            "event_type": "automatic_deposit" if "automatic" in str(raw.get("Comment (optional)") or "").lower() else "deposit",
            "side": "in",
            "asset": incoming_asset,
            "quantity": incoming_amount,
        }
    if outgoing_asset and outgoing_amount:
        return {
            **base,
            "event_type": "automatic_withdrawal" if "automatic" in str(raw.get("Comment (optional)") or "").lower() else "withdrawal",
            "side": "out",
            "asset": outgoing_asset,
            "quantity": outgoing_amount,
        }
    raise SystemExit(f"reference {reference['event_id']} is not a supported source-chain row")


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
        "# Bitget HNT 2024 Blockpit Source Chain - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Ausgewaehlte Zeilen: `{audit['selected_row_count']}`",
        f"- Importierte Events: `{result.get('inserted_events', 0)}`",
        f"- Duplikate: `{result.get('duplicate_events', 0)}`",
        f"- Bestehende Rekonstruktionszeilen: `{audit['existing_reconstruction_count']}`",
        "",
        "## Rekonstruktionszeilen",
        "",
    ]
    for row in audit["selected_rows"]:
        if row["event_type"] == "trade":
            lines.append(
                f"- `{row['timestamp_utc']}` trade `{row['quantity']} {row['asset']}` gegen "
                f"`{row['quote_quantity']} {row['quote_asset']}` fee `{row['fee']} {row['fee_asset']}` tx `{row['tx_id']}`"
            )
        else:
            lines.append(
                f"- `{row['timestamp_utc']}` `{row['event_type']}` `{row['side']}` `{row['quantity']} {row['asset']}` tx `{row['tx_id']}`"
            )
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {item}" for item in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
