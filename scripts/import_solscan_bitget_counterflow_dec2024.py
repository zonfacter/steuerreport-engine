#!/usr/bin/env python3
"""Import confirmed Solscan USDT counterflow for Bitget withdrawal on 2024-12-01."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.service import confirm_import
from tax_engine.ingestion.store import STORE

WALLET = "wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB"
SIGNATURE = "mxDAzS4vybHXsuUscyeXTrAQwsjKz3pbs9hHpZp6Ld68iMjHetSWahTCVf1MG4Uakbme7ZsWGMcJPEUTkXPhNus"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
SOURCE_NAME = "solscan_bitget_counterflow_dec2024_2026-05-08"
JSON_OUT = ROOT / "var" / "solscan_bitget_counterflow_dec2024_import_2026-05-08.json"
MD_OUT = ROOT / "docs" / "71_SOLSCAN_BITGET_COUNTERFLOW_DEC2024_IMPORT_2026-05-08.md"


def main() -> None:
    row = load_transfer_row()
    normalized = normalize_row(row)
    result = confirm_import(SOURCE_NAME, [normalized])
    payload = {
        "source_name": SOURCE_NAME,
        "wallet": WALLET,
        "signature": SIGNATURE,
        "source_table": "solscan_account_transfers",
        "import_result": result,
        "row": normalized,
        "note": "Confirmed on-chain USDT inflow matching the Bitget withdrawal window; imported because it existed in Solscan transfer storage but not in raw_events.",
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(render_md(payload), encoding="utf-8")
    print(json.dumps({"json": str(JSON_OUT), "md": str(MD_OUT), "import": result}, ensure_ascii=False, indent=2))


def load_transfer_row() -> dict[str, Any]:
    with STORE._connect() as conn:
        row = conn.execute(
            """
            SELECT signature, flow, activity_type, token_address, token_decimals, amount, value_usd,
                   block_time_utc, from_address, to_address, raw_json
            FROM solscan_account_transfers
            WHERE wallet_address = ? AND signature = ? AND lower(token_address) = lower(?)
            """,
            (WALLET, SIGNATURE, USDT_MINT),
        ).fetchone()
    if row is None:
        raise SystemExit(f"Solscan transfer not found for {SIGNATURE}")
    return dict(row)


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    decimals = int(row.get("token_decimals") or 0)
    quantity = Decimal(str(row["amount"])) / (Decimal(10) ** decimals)
    side = "in" if str(row.get("flow") or "").lower() == "in" else "out"
    return {
        "timestamp_utc": str(row["block_time_utc"]),
        "wallet_address": WALLET,
        "asset": "USDT",
        "asset_address": USDT_MINT,
        "quantity": quantity.normalize().to_eng_string(),
        "price": "",
        "fee": "0",
        "fee_asset": "",
        "side": side,
        "event_type": "token_transfer",
        "defi_label": "transfer",
        "tx_id": SIGNATURE,
        "source": "solscan_wallet_discovery",
        "raw_row": {
            "source_table": "solscan_account_transfers",
            "activity_type": str(row.get("activity_type") or ""),
            "flow": str(row.get("flow") or ""),
            "token_address": str(row.get("token_address") or ""),
            "token_decimals": decimals,
            "amount_raw": str(row.get("amount") or ""),
            "value_usd": str(row.get("value_usd") or ""),
            "from_address": str(row.get("from_address") or ""),
            "to_address": str(row.get("to_address") or ""),
            "raw_json": json.loads(str(row.get("raw_json") or "{}")),
        },
    }


def render_md(payload: dict[str, Any]) -> str:
    row = payload["row"]
    result = payload["import_result"]
    return "\n".join(
        [
            "# Solscan Bitget Counterflow Dec 2024 Import - 2026-05-08",
            "",
            "## Zweck",
            "",
            "Import einer bestaetigten Solscan-USDT-Gegenbuchung zum Bitget-Abgang vom `2024-12-01`.",
            "",
            "## Import",
            "",
            "- Quelle: `solscan_account_transfers`",
            f"- Source Name: `{payload['source_name']}`",
            f"- Wallet: `{payload['wallet']}`",
            f"- Signatur: `{payload['signature']}`",
            f"- Zeit: `{row['timestamp_utc']}`",
            f"- Event: `{row['event_type']}` `{row['side']}` `{row['quantity']} {row['asset']}`",
            f"- Inserted Events: `{result['inserted_events']}`",
            f"- Duplicate Events: `{result['duplicate_events']}`",
            "",
            "## Bewertung",
            "",
            "Die Zeile lag bereits in der Solscan-Transferdatenbank, war aber nicht als `raw_event` aktiv. Sie erklaert die fehlende On-Chain-Gegenbuchung zum Bitget-Withdrawal-Fenster und darf nicht als manueller Adjustment-Kandidat behandelt werden.",
            "",
        ]
    )


if __name__ == "__main__":
    main()
