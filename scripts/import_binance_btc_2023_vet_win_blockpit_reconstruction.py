#!/usr/bin/env python3
"""Import a narrow Binance VET/WIN -> BTC reconstruction backed by Blockpit references."""

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
SOURCE_NAME = "binance_btc_2023_vet_win_blockpit_reconstruction"
REPORT_JSON = ROOT / "var" / f"{SOURCE_NAME}_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"164_BINANCE_BTC_2023_VET_WIN_BLOCKPIT_RECONSTRUCTION_{CREATED_DATE}.md"

REFERENCE_EVENT_IDS = {
    "vet_auto_balance_in": "e4bd699f20bd9bd424a100e9f88aae4e6786a8802923cd9e3b88e494930367eb",
    "vet_to_btc_trade": "8dcccb77901b08ca24470d75a1716fd9be240c2fb52f589e49a2d9543699f92e",
    "win_auto_balance_in": "b4085bf368d17fb19b863bbee292c965492a403b6c9d501142c7d2960f2d7daa",
    "win_to_btc_trade": "6c8a5d5156ae9a027d72ceb30b937003d6da79564c91ceca619b5bf95d291484",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    references = {name: load_reference(event_id) for name, event_id in REFERENCE_EVENT_IDS.items()}
    rows = [
        auto_balance_row("vet_auto_balance_in", references["vet_auto_balance_in"]),
        trade_row("vet_to_btc_trade", references["vet_to_btc_trade"], expected_outgoing="VET"),
        auto_balance_row("win_auto_balance_in", references["win_auto_balance_in"]),
        trade_row("win_to_btc_trade", references["win_to_btc_trade"], expected_outgoing="WIN"),
    ]
    existing = find_existing(rows)
    import_result = None
    if args.execute and not existing:
        import_result = confirm_import(source_name=SOURCE_NAME, rows=rows)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": "execute" if args.execute else "preview",
        "source_name": SOURCE_NAME,
        "reference_event_ids": REFERENCE_EVENT_IDS,
        "selected_rows": rows,
        "existing_reconstruction_count": len(existing),
        "existing_reconstruction_events": existing,
        "import_result": import_result,
        "interpretation": [
            "The prior BTC candidate audit blocked VET/WIN -> BTC because the small VET/WIN source amounts were not active.",
            "Blockpit Binance references contain matching Auto-Balancing In rows immediately before both trades.",
            "This package imports only those two auto-balancing source rows and the two BTC trades.",
            "The package adds a net 0.00011653 BTC before the June 2023 SOL buys and should not shift the gap into VET/WIN.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(
        json.dumps(
            {
                "json": str(REPORT_JSON),
                "doc": str(REPORT_MD),
                "mode": audit["mode"],
                "existing": len(existing),
                "import_result": import_result,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def load_reference(event_id: str) -> dict[str, Any]:
    event = STORE.get_raw_event(event_id)
    if event is None:
        raise SystemExit(f"missing reference event {event_id}")
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    if not payload:
        raise SystemExit(f"reference event {event_id} has no payload")
    return {"event_id": event_id, "payload": payload}


def auto_balance_row(name: str, reference: dict[str, Any]) -> dict[str, Any]:
    payload = reference["payload"]
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    incoming_asset = str(raw.get("Incoming Asset") or payload.get("asset") or "").upper().strip()
    incoming_amount = str(raw.get("Incoming Amount") or payload.get("quantity") or "").strip()
    if not timestamp or not incoming_asset or not incoming_amount:
        raise SystemExit(f"reference {reference['event_id']} is not a complete auto-balance reference")
    return {
        "timestamp_utc": timestamp,
        "source": SOURCE_NAME,
        "event_type": "internal_balance_adjustment",
        "side": "in",
        "asset": incoming_asset,
        "quantity": incoming_amount,
        "tx_id": f"binance-btc-vet-win-reconstruction:{name}",
        "reference_event_id": reference["event_id"],
        "raw_row": {
            "reconstruction_reason": "binance_blockpit_auto_balance_source_before_vet_win_to_btc",
            "reference_source": "blockpit",
            "reference_label": str(raw.get("Label") or ""),
            "reference_tx_id": str(raw.get("Trx. ID (optional)") or ""),
            "incoming_amount": incoming_amount,
            "incoming_asset": incoming_asset,
        },
    }


def trade_row(name: str, reference: dict[str, Any], *, expected_outgoing: str) -> dict[str, Any]:
    payload = reference["payload"]
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    incoming_asset = str(raw.get("Incoming Asset") or payload.get("asset") or "").upper().strip()
    outgoing_asset = str(raw.get("Outgoing Asset") or "").upper().strip()
    incoming_amount = str(raw.get("Incoming Amount") or payload.get("quantity") or "").strip()
    outgoing_amount = str(raw.get("Outgoing Amount") or "").strip()
    timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    trx_id = str(raw.get("Trx. ID (optional)") or payload.get("tx_id") or name).strip()
    if incoming_asset != "BTC" or outgoing_asset != expected_outgoing or not incoming_amount or not outgoing_amount:
        raise SystemExit(f"reference {reference['event_id']} is not the expected {expected_outgoing}->BTC trade")
    return {
        "timestamp_utc": timestamp,
        "source": SOURCE_NAME,
        "event_type": "trade",
        "side": "buy",
        "asset": "BTC",
        "base_asset": "BTC",
        "quote_asset": outgoing_asset,
        "quantity": incoming_amount,
        "quote_quantity": outgoing_amount,
        "price": "",
        "fee": "0",
        "fee_asset": "",
        "tx_id": f"binance-btc-vet-win-reconstruction:{trx_id}",
        "reference_event_id": reference["event_id"],
        "raw_row": {
            "reconstruction_reason": "binance_missing_vet_win_to_btc_trade_before_2023_sol_buys",
            "reference_source": "blockpit",
            "reference_label": str(raw.get("Label") or ""),
            "reference_tx_id": trx_id,
            "incoming_amount": incoming_amount,
            "incoming_asset": incoming_asset,
            "outgoing_amount": outgoing_amount,
            "outgoing_asset": outgoing_asset,
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
        "# Binance BTC 2023 VET/WIN Blockpit Reconstruction - 2026-05-09",
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
        if row["event_type"] == "trade":
            lines.append(
                f"- `{row['timestamp_utc']}` trade `buy` `{row['quantity']} BTC` gegen "
                f"`{row['quote_quantity']} {row['quote_asset']}` reference `{row['reference_event_id']}`"
            )
        else:
            lines.append(
                f"- `{row['timestamp_utc']}` `{row['event_type']}` `{row['quantity']} {row['asset']}` "
                f"reference `{row['reference_event_id']}`"
            )
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {item}" for item in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
