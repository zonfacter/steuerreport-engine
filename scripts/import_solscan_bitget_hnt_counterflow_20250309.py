#!/usr/bin/env python3
"""Import confirmed Solscan HNT counterflow for Bitget withdrawal on 2025-03-09."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.service import confirm_import  # noqa: E402
from tax_engine.ingestion.store import STORE  # noqa: E402

WALLET = "wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB"
SIGNATURE = "4ZpJtYcs4fYuH5sTtMhCc4h2QZSmBHeKLDgUEukFW8jfq4q7KMe9gjFwjXnAWLn142PM5qu19rn76VLQJ1bMm4Hc"
HNT_MINT = "hntyVP6YFm1Hg25TN9WGLqM12b8TQmcknKrdu1oxWux"
SOURCE_NAME = "solscan_bitget_hnt_counterflow_20250309"
JSON_OUT = ROOT / "var" / "solscan_bitget_hnt_counterflow_20250309_import_2026-05-09.json"
MD_OUT = ROOT / "docs" / "159_SOLSCAN_BITGET_HNT_COUNTERFLOW_20250309_IMPORT_2026-05-09.md"


def main() -> None:
    row = load_transfer_row()
    normalized = normalize_row(row)
    existing = find_existing(normalized)
    result = None
    if not existing:
        result = confirm_import(SOURCE_NAME, [normalized])
    payload = {
        "source_name": SOURCE_NAME,
        "wallet": WALLET,
        "signature": SIGNATURE,
        "source_table": "solscan_account_transfers",
        "existing_events": existing,
        "import_result": result,
        "row": normalized,
        "note": (
            "Confirmed on-chain HNT inflow matching the Bitget withdrawal 1282705829779644421 "
            "and the later same-wallet HNT->JUP swap. Imported because the transfer existed in "
            "Solscan storage but was not active as a raw_event."
        ),
    }
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(render_md(payload), encoding="utf-8")
    print(json.dumps({"json": str(JSON_OUT), "md": str(MD_OUT), "existing": len(existing), "import": result}, ensure_ascii=False, indent=2))


def load_transfer_row() -> dict[str, Any]:
    with STORE._connect() as conn:
        row = conn.execute(
            """
            SELECT signature, flow, activity_type, token_address, token_decimals, amount, value_usd,
                   block_time_utc, from_address, to_address, raw_json
            FROM solscan_account_transfers
            WHERE wallet_address = ? AND signature = ? AND lower(token_address) = lower(?)
            """,
            (WALLET, SIGNATURE, HNT_MINT),
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
        "asset": "HNT",
        "asset_address": HNT_MINT,
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
            "counterflow_for_platform": "bitget",
            "counterflow_tx_id": "1282705829779644421",
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


def find_existing(row: dict[str, Any]) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for event in STORE.list_raw_events():
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if (
            str(payload.get("tx_id") or "") == row["tx_id"]
            and str(payload.get("asset") or "").upper() == "HNT"
            and str(payload.get("quantity") or "") == row["quantity"]
            and str(payload.get("side") or "").lower() == row["side"]
        ):
            matches.append(
                {
                    "event_id": str(event.get("unique_event_id") or ""),
                    "timestamp_utc": str(payload.get("timestamp_utc") or ""),
                    "source": str(payload.get("source") or ""),
                    "event_type": str(payload.get("event_type") or ""),
                    "side": str(payload.get("side") or ""),
                    "asset": str(payload.get("asset") or ""),
                    "quantity": str(payload.get("quantity") or ""),
                    "tx_id": str(payload.get("tx_id") or ""),
                }
            )
    return matches


def render_md(payload: dict[str, Any]) -> str:
    row = payload["row"]
    result = payload.get("import_result") or {}
    return "\n".join(
        [
            "# Solscan Bitget HNT Counterflow 2025-03-09 Import - 2026-05-09",
            "",
            "## Zweck",
            "",
            "Import einer bestaetigten Solscan-HNT-Gegenbuchung zum Bitget-Withdrawal und direkt folgenden Solana-HNT->JUP-Swap.",
            "",
            "## Import",
            "",
            "- Quelle: `solscan_account_transfers`",
            f"- Source Name: `{payload['source_name']}`",
            f"- Wallet: `{payload['wallet']}`",
            f"- Signatur: `{payload['signature']}`",
            f"- Zeit: `{row['timestamp_utc']}`",
            f"- Event: `{row['event_type']}` `{row['side']}` `{row['quantity']} {row['asset']}`",
            f"- Inserted Events: `{result.get('inserted_events', 0)}`",
            f"- Duplicate Events: `{result.get('duplicate_events', 0)}`",
            f"- Bestehende Events: `{len(payload['existing_events'])}`",
            "",
            "## Bewertung",
            "",
            "Die Zeile lag bereits in der Solscan-Transferdatenbank, war aber nicht als `raw_event` aktiv. Sie erklaert die fehlende On-Chain-Gegenbuchung zwischen Bitget-Withdrawal `1282705829779644421` und dem Solana-Swap `3cGd6Sf...`.",
            "",
        ]
    )


if __name__ == "__main__":
    main()
