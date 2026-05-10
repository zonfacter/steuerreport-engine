#!/usr/bin/env python3
"""Import the missing Solscan primary JUP inflow that funds the June 2025 wallet transfer."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.connectors.token_metadata import resolve_token_metadata  # noqa: E402
from tax_engine.ingestion.service import confirm_import  # noqa: E402
from tax_engine.ingestion.store import STORE  # noqa: E402

CREATED_DATE = "2026-05-09"
WALLET = "wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB"
SIGNATURE = "GuZCyW2WRCYSAwgwzn5bPYV7HTRdKMVPiMADwGX2bUg9A3wjnmNzyVgtPZ5uMdqqmPPvJSPqtPGCZtEmKA89Gqy"
SOURCE_NAME = "solscan_jup_counterflow_20250323"
REPORT_JSON = ROOT / "var" / f"solscan_jup_counterflow_20250323_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"141_SOLSCAN_JUP_COUNTERFLOW_20250323_{CREATED_DATE}.md"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    transfer = load_transfer()
    row = build_import_row(transfer)
    existing = find_existing_primary(row)
    import_result = None
    if args.execute and not existing:
        import_result = confirm_import(source_name=SOURCE_NAME, rows=[row])
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": "execute" if args.execute else "preview",
        "wallet": WALLET,
        "signature": SIGNATURE,
        "existing_primary_count": len(existing),
        "selected_row_count": 1 if row else 0,
        "selected_rows": [row],
        "existing_primary_events": existing,
        "import_result": import_result,
        "interpretation": [
            "Solscan account_transfers proves a 5530.555703 JUP inflow to the wallet on 2025-03-23.",
            "The same tx exists as Binance API withdrawal and Blockpit Solana reference deposit, but the active Solana wallet primary row was missing.",
            "This import does not touch raw rows or Blockpit references; it adds the missing primary on-chain counterflow.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "mode": audit["mode"], "existing_primary_count": len(existing), "import_result": import_result}, ensure_ascii=False, indent=2))


def load_transfer() -> dict[str, Any]:
    with STORE._connect() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM solscan_account_transfers
            WHERE wallet_address = ? AND signature = ?
            """,
            (WALLET, SIGNATURE),
        ).fetchone()
    if row is None:
        raise SystemExit(f"missing solscan_account_transfer for {SIGNATURE}")
    return dict(row)


def build_import_row(transfer: dict[str, Any]) -> dict[str, Any]:
    token = str(transfer.get("token_address") or "")
    metadata = resolve_token_metadata(token)
    decimals = int(transfer.get("token_decimals") or 0)
    amount = Decimal(str(transfer.get("amount") or "0")) / (Decimal(10) ** decimals)
    flow = str(transfer.get("flow") or "").lower()
    side = "in" if flow == "in" else "out"
    return {
        "timestamp_utc": str(transfer.get("block_time_utc") or ""),
        "source": "solscan_wallet_discovery",
        "event_type": "token_transfer",
        "side": side,
        "asset": metadata["symbol"],
        "quantity": format(amount.normalize(), "f"),
        "price": "",
        "fee": "0",
        "fee_asset": "",
        "tx_id": str(transfer.get("signature") or ""),
        "wallet_address": WALLET,
        "from_address": str(transfer.get("from_address") or ""),
        "to_address": str(transfer.get("to_address") or ""),
        "counterparty_address": str(transfer.get("from_address") or "") if side == "in" else str(transfer.get("to_address") or ""),
        "token_address": token,
        "token_decimals": str(decimals),
        "value_usd": str(transfer.get("value_usd") or ""),
        "raw_row": {
            "source_table": "solscan_account_transfers",
            "transfer_id": str(transfer.get("transfer_id") or ""),
            "activity_type": str(transfer.get("activity_type") or ""),
            "flow": flow,
            "token_address": token,
            "token_decimals": decimals,
            "amount_base_units": str(transfer.get("amount") or ""),
            "value_usd": str(transfer.get("value_usd") or ""),
            "from_address": str(transfer.get("from_address") or ""),
            "to_address": str(transfer.get("to_address") or ""),
            "signature": str(transfer.get("signature") or ""),
            "raw_json": transfer.get("raw_json") or "",
        },
    }


def find_existing_primary(row: dict[str, Any]) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for event in STORE.list_raw_events():
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if not payload:
            continue
        if str(payload.get("source") or "") != "solscan_wallet_discovery":
            continue
        if str(payload.get("tx_id") or "") != str(row.get("tx_id") or ""):
            continue
        if str(payload.get("asset") or "") != str(row.get("asset") or ""):
            continue
        if str(payload.get("quantity") or "") != str(row.get("quantity") or ""):
            continue
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
    row = audit["selected_rows"][0]
    result = audit.get("import_result") or {}
    lines = [
        "# Solscan JUP Counterflow 2025-03-23 - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Wallet: `{audit['wallet']}`",
        f"- Signatur: `{audit['signature']}`",
        f"- Bestehende Primaerzeilen: `{audit['existing_primary_count']}`",
        f"- Importierte Events: `{result.get('inserted_events', 0)}`",
        f"- Duplikate: `{result.get('duplicate_events', 0)}`",
        "",
        "## Importierte Primaerzeile",
        "",
        f"- `{row['timestamp_utc']}` `{row['source']}` `{row['event_type']}` `{row['side']}` `{row['quantity']} {row['asset']}`",
        f"- Von: `{row['from_address']}`",
        f"- Nach: `{row['to_address']}`",
        f"- TX: `{row['tx_id']}`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {item}" for item in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
