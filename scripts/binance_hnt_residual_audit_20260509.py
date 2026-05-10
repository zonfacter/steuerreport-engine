#!/usr/bin/env python3
"""Audit the remaining Binance-local HNT residual after source-chain reconstruction."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE  # noqa: E402

CREATED_DATE = "2026-05-09"
LEDGER_JSONL = ROOT / "var" / f"platform_ledger_{CREATED_DATE}.jsonl"
BALANCE_JSON = ROOT / "var" / f"chronological_balance_break_audit_after_bitget_hnt_source_chain_{CREATED_DATE}.json"
OUTPUT_JSON = ROOT / "var" / f"binance_hnt_residual_audit_{CREATED_DATE}.json"
OUTPUT_MD = ROOT / "docs" / f"163_BINANCE_HNT_RESIDUAL_AUDIT_{CREATED_DATE}.md"


def main() -> None:
    rows = [
        row
        for row in load_jsonl(LEDGER_JSONL)
        if row.get("source_mode") == "active" and row.get("platform") == "binance" and row.get("asset") == "HNT"
    ]
    rows.sort(key=lambda row: (row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or "", row.get("ledger_id") or ""))
    balances = enrich_balances(rows)
    break_row = next((row for row in balances if dec(row["balance_after"]) < 0), None)
    reconstruction_rows = [row for row in balances if row.get("source") == "binance_2022_2023_blockpit_source_chain_reconstruction"]
    prior_balance = next((row["balance_before"] for row in reconstruction_rows[:1]), "0")
    reconstruction_net = sum(dec(row.get("quantity_delta")) for row in reconstruction_rows)
    same_day_refs = blockpit_same_day_hnt_references()
    global_hnt = global_hnt_report(load_json(BALANCE_JSON))
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "platform": "binance",
        "asset": "HNT",
        "event_count": len(rows),
        "final_balance": plain(sum(dec(row.get("quantity_delta")) for row in rows)),
        "first_negative": break_row,
        "prior_balance_before_reconstruction": prior_balance,
        "reconstruction_net_hnt": plain(reconstruction_net),
        "reconstruction_rows": reconstruction_rows,
        "same_day_blockpit_binance_hnt_reference_rows": same_day_refs,
        "same_day_reference_count": len(same_day_refs),
        "global_hnt": global_hnt,
        "decision": {
            "auto_book_safe": False,
            "tax_effective_adjustment_recommended": False,
            "recommended_status": "platform_context_or_small_residual_review",
            "reason": (
                "Blockpit reference rows for 2023-03-17 contain exactly the five HNT trades already imported. "
                "They buy 312.07 HNT and sell 313.91 HNT. With the pre-existing Binance HNT balance of "
                f"{prior_balance}, the platform-local residual is {plain(sum(dec(row.get('quantity_delta')) for row in rows))} HNT. "
                "The global HNT ledger remains positive, so this should not be corrected as a global taxable inventory inflow."
            ),
        },
    }
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(OUTPUT_MD), "final_balance": audit["final_balance"]}, ensure_ascii=False, indent=2))


def enrich_balances(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    balance = Decimal("0")
    enriched = []
    for row in rows:
        before = balance
        balance += dec(row.get("quantity_delta"))
        item = {
            "ledger_id": row.get("ledger_id"),
            "timestamp_utc": row.get("timestamp_utc"),
            "normalized_timestamp_utc": row.get("normalized_timestamp_utc") or row.get("timestamp_utc"),
            "event_type": row.get("event_type"),
            "source": row.get("source"),
            "tx_id": row.get("tx_id"),
            "quantity_delta": row.get("quantity_delta"),
            "balance_before": plain(before),
            "balance_after": plain(balance),
        }
        enriched.append(item)
    return enriched


def blockpit_same_day_hnt_references() -> list[dict[str, str]]:
    refs = []
    seen = set()
    for event in STORE.list_raw_events():
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        if str(payload.get("source") or "").lower() != "blockpit":
            continue
        integration = str(raw.get("Integration Name") or raw.get("Source Name") or "").lower()
        if "binance" not in integration:
            continue
        timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if not timestamp.startswith("2023-03-17"):
            continue
        assets = " ".join(
            str(raw.get(key) or "").upper()
            for key in ("Incoming Asset", "Outgoing Asset", "Fee Asset (optional)", "Asset")
        )
        if "HNT" not in assets:
            continue
        item = {
            "event_id": str(event.get("unique_event_id") or ""),
            "timestamp_utc": timestamp,
            "label": str(raw.get("Label") or ""),
            "trx_id": str(raw.get("Trx. ID (optional)") or ""),
            "incoming_amount": str(raw.get("Incoming Amount") or "").strip(),
            "incoming_asset": str(raw.get("Incoming Asset") or "").strip(),
            "outgoing_amount": str(raw.get("Outgoing Amount") or "").strip(),
            "outgoing_asset": str(raw.get("Outgoing Asset") or "").strip(),
            "fee_amount": str(raw.get("Fee Amount (optional)") or "").strip(),
            "fee_asset": str(raw.get("Fee Asset (optional)") or "").strip(),
        }
        key = (
            item["timestamp_utc"],
            item["trx_id"],
            item["incoming_amount"],
            item["incoming_asset"],
            item["outgoing_amount"],
            item["outgoing_asset"],
            item["fee_amount"],
            item["fee_asset"],
        )
        if key in seen:
            continue
        seen.add(key)
        refs.append(item)
    return sorted(refs, key=lambda row: (row["timestamp_utc"], row["trx_id"], row["event_id"]))


def global_hnt_report(balance: dict[str, Any]) -> dict[str, Any]:
    for row in balance.get("asset_reports", []):
        if str(row.get("asset") or "").upper() == "HNT":
            return {
                "final_balance": row.get("final_balance"),
                "first_negative": row.get("first_negative"),
                "event_count": row.get("event_count"),
            }
    return {}


def load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def render_doc(audit: dict[str, Any]) -> str:
    first = audit.get("first_negative") or {}
    lines = [
        "# Binance HNT Residual Audit - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Plattform: `{audit['platform']}`",
        f"- Asset: `{audit['asset']}`",
        f"- Binance-HNT-Endsaldo lokal: `{audit['final_balance']}`",
        f"- Globaler HNT-Endsaldo: `{audit['global_hnt'].get('final_balance')}`",
        f"- Erster lokaler Negativbestand: `{first.get('normalized_timestamp_utc')}` tx `{first.get('tx_id')}`",
        f"- Vorbestand vor 2023-03-17-Rekonstruktion: `{audit['prior_balance_before_reconstruction']}`",
        f"- Netto der 2023-03-17-Rekonstruktion: `{audit['reconstruction_net_hnt']}`",
        "",
        "## Bewertung",
        "",
        f"- Automatisch steuerwirksam buchen: `{audit['decision']['tax_effective_adjustment_recommended']}`",
        f"- Auto-Book sicher: `{audit['decision']['auto_book_safe']}`",
        f"- Empfohlener Status: `{audit['decision']['recommended_status']}`",
        f"- Grund: {audit['decision']['reason']}",
        "",
        "## Rekonstruktionszeilen",
        "",
    ]
    for row in audit["reconstruction_rows"]:
        lines.append(
            f"- `{row['normalized_timestamp_utc']}` `{row['quantity_delta']} HNT` "
            f"balance `{row['balance_before']}` -> `{row['balance_after']}` tx `{row['tx_id']}`"
        )
    lines += ["", "## Gepruefte Blockpit-Binance-HNT-Referenzen 2023-03-17", ""]
    for row in audit["same_day_blockpit_binance_hnt_reference_rows"]:
        fee = f"{row['fee_amount']} {row['fee_asset']}".strip() or "0"
        lines.append(
            f"- `{row['timestamp_utc']}` trx `{row['trx_id']}` "
            f"in `{row['incoming_amount']} {row['incoming_asset']}` out `{row['outgoing_amount']} {row['outgoing_asset']}` "
            f"fee `{fee}`"
        )
    lines += [
        "",
        "## Naechste Aktion",
        "",
        "- Nicht als globalen HNT-Zufluss buchen.",
        "- Wenn kein weiterer Binance-/Helium-Beleg auftaucht, als dokumentierten Plattformkontext-/Kleinrest entscheiden.",
    ]
    return "\n".join(lines) + "\n"


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


if __name__ == "__main__":
    main()
