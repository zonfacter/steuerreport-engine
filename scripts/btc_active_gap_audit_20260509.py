#!/usr/bin/env python3
"""Summarize the BTC gap opened by the Binance SOL reconstruction."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE  # noqa: E402

BALANCE_JSON = ROOT / "var" / "chronological_balance_break_audit_after_binance_source_chain_reconstruction_2026-05-09.json"
OUTPUT_JSON = ROOT / "var" / "btc_active_gap_audit_2026-05-09.json"
OUTPUT_DOC = ROOT / "docs" / "151_BTC_ACTIVE_GAP_AUDIT_2026-05-09.md"


def main() -> None:
    balance = read_json(BALANCE_JSON)
    btc = next((row for row in balance.get("asset_reports") or [] if row.get("asset") == "BTC"), {})
    refs = btc_blockpit_binance_references()
    payload = {
        "active_btc": {
            "final_balance": btc.get("final_balance"),
            "first_negative": btc.get("first_negative"),
            "worst_balance": btc.get("worst_balance"),
            "yearly_net": btc.get("yearly_net"),
            "source_net_top": (btc.get("source_net_top") or [])[:12],
        },
        "blockpit_binance_reference_before_first_sol_buy": refs["before_first_sol_buy"],
        "blockpit_binance_reference_before_second_sol_buy": refs["before_second_sol_buy"],
        "reference_net_btc_before_second_sol_buy": plain(refs["net_before_second_sol_buy"]),
        "assessment": [
            "Die SOL-Luecke wurde nicht durch ein freies Opening geschlossen, sondern als echte Binance-SOL-Kaeufe gegen BTC rekonstruiert.",
            "Dadurch ist BTC nun der naechste aktive Bestandsgap.",
            "Blockpit enthaelt BTC-Referenzzufluesse vor den SOL-Kaeufen, aber diese Zufluesse kommen wiederum aus BUSD/USDT/VET/WIN/DOGE-Trades.",
            "Naechster Schritt ist eine kontrollierte BTC-Quellenketten-Rekonstruktion, damit der Fehler nicht unkontrolliert in andere Assets verschoben wird.",
        ],
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_DOC.write_text(render_doc(payload), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(OUTPUT_DOC), "reference_net_btc": payload["reference_net_btc_before_second_sol_buy"]}, ensure_ascii=False, indent=2))


def btc_blockpit_binance_references() -> dict[str, Any]:
    before_first: list[dict[str, str]] = []
    before_second: list[dict[str, str]] = []
    net_before_second = Decimal("0")
    for event in STORE.list_raw_events():
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        if str(payload.get("source") or "").lower() != "blockpit":
            continue
        if "binance" not in str(raw.get("Integration Name") or raw.get("Source Name") or "").lower():
            continue
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if ts >= "2023-06-10T16:45:04+00:00":
            continue
        asset = str(payload.get("asset") or "").upper()
        if asset != "BTC":
            continue
        side = str(payload.get("side") or "").lower()
        qty = dec(payload.get("quantity"))
        delta = qty if side in {"in", "buy"} else -qty if side in {"out", "sell"} else qty
        row = {
            "event_id": str(event.get("unique_event_id") or ""),
            "timestamp_utc": ts,
            "delta_btc": plain(delta),
            "event_type": str(payload.get("event_type") or ""),
            "side": side,
            "quantity": str(payload.get("quantity") or ""),
            "tx_id": str(payload.get("tx_id") or ""),
            "label": str(raw.get("Label") or ""),
            "comment": str(raw.get("Comment (optional)") or ""),
            "incoming": str(raw.get("Incoming Amount") or ""),
            "incoming_asset": str(raw.get("Incoming Asset") or ""),
            "outgoing": str(raw.get("Outgoing Amount") or ""),
            "outgoing_asset": str(raw.get("Outgoing Asset") or ""),
        }
        if ts < "2023-05-04T04:24:52+00:00":
            before_first.append(row)
        before_second.append(row)
        net_before_second += delta
    before_first.sort(key=lambda row: row["timestamp_utc"])
    before_second.sort(key=lambda row: row["timestamp_utc"])
    return {
        "before_first_sol_buy": before_first,
        "before_second_sol_buy": before_second,
        "net_before_second_sol_buy": net_before_second,
    }


def read_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def render_doc(payload: dict[str, Any]) -> str:
    btc = payload["active_btc"]
    first = btc.get("first_negative") or {}
    worst = btc.get("worst_balance") or {}
    lines = [
        "# BTC Active Gap Audit - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Aktiver BTC-Endsaldo: `{btc.get('final_balance')}`",
        f"- Erster BTC-Bruch: `{first.get('timestamp')}` `{first.get('source')}` delta `{first.get('delta')}` after `{first.get('balance_after')}`",
        f"- Schlimmster BTC-Stand: `{worst.get('balance_after')}` am `{worst.get('timestamp')}`",
        f"- Blockpit-Binance-Referenznetto bis zum zweiten SOL-Kauf: `{payload['reference_net_btc_before_second_sol_buy']} BTC`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["assessment"])
    lines += [
        "",
        "## BTC-Referenzen vor dem ersten SOL-Kauf",
        "",
    ]
    for row in payload["blockpit_binance_reference_before_first_sol_buy"]:
        lines.append(
            f"- `{row['timestamp_utc']}` delta `{row['delta_btc']}` `{row['label']}` `{row['comment']}` "
            f"in `{row['incoming']} {row['incoming_asset']}` out `{row['outgoing']} {row['outgoing_asset']}` ref `{row['event_id']}`"
        )
    lines += [
        "",
        "## BTC-Referenzen bis zum zweiten SOL-Kauf",
        "",
    ]
    for row in payload["blockpit_binance_reference_before_second_sol_buy"]:
        lines.append(
            f"- `{row['timestamp_utc']}` delta `{row['delta_btc']}` `{row['label']}` `{row['comment']}` "
            f"in `{row['incoming']} {row['incoming_asset']}` out `{row['outgoing']} {row['outgoing_asset']}` ref `{row['event_id']}`"
        )
    lines += [
        "",
        "## Naechster Schritt",
        "",
        "- Nicht pauschal alle BTC-Referenzen aktivieren. Zuerst die BTC-Zufluesse mit ihren Gegenassets als Kette pruefen und dann in einem begrenzten Importpaket buchen.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
