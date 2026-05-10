#!/usr/bin/env python3
"""Preview/import inferred VTHO reward needed by Binance dust-convert evidence."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion import confirm_import
from tax_engine.ingestion.service import _build_event_identity
from tax_engine.ingestion.store import STORE
from tax_engine.integrity import event_fingerprint

CREATED_DATE = "2026-05-09"
SOURCE_NAME = "reviewed_inferred_vtho_reward_from_binance_dust_20230502"
JSON_PATH = ROOT / "var" / f"inferred_vtho_reward_from_binance_dust_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"107_INFERRED_VTHO_REWARD_FROM_BINANCE_DUST_{CREATED_DATE}.md"

DUST_EVIDENCE = {
    "timestamp_utc": "2023-05-02T04:13:23+00:00",
    "inferred_timestamp_utc": "2023-05-02T04:13:22+00:00",
    "asset": "VTHO",
    "quantity": "42.39387934",
    "binance_trans_id": "136251331484",
    "target_asset": "BNB",
    "transfered_amount_bnb": "0.00017775",
    "service_charge_bnb": "0.00000355",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    rows = build_rows()
    existing_ids = {str(row["unique_event_id"]) for row in STORE.list_raw_events()}
    event_ids = [event_fingerprint(_build_event_identity(row)) for row in rows]
    duplicates = sum(1 for event_id in set(event_ids) if event_id in existing_ids)
    import_result = confirm_import(source_name=SOURCE_NAME, rows=rows) if args.execute else None
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": "execute" if args.execute else "preview",
        "source_name": SOURCE_NAME,
        "row_count": len(rows),
        "duplicate_existing_event_count": duplicates,
        "new_candidate_event_count": len(set(event_ids) - existing_ids),
        "rows": rows,
        "import_result": summarize_import(import_result),
        "interpretation": [
            "The Binance API dust-convert outflow proves that 42.39387934 VTHO existed immediately before conversion.",
            "No primary incoming VTHO row is available in the local exports, so this row is explicitly marked as reviewed/inferred.",
            "The income value is derived from gross BNB consideration, using cached BNB/USD and USD/EUR rates for 2023-05-02.",
            "This is not a generic balancing row; it is tied to Binance transId 136251331484.",
        ],
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "mode": audit["mode"], "duplicates": duplicates, "new": audit["new_candidate_event_count"], "import_result": audit["import_result"]}, ensure_ascii=False, indent=2))


def build_rows() -> list[dict[str, Any]]:
    bnb_price = rate("2023-05-02", "BNB", "USD")
    usd_eur = rate("2023-05-02", "USD", "EUR")
    gross_bnb = dec(DUST_EVIDENCE["transfered_amount_bnb"]) + dec(DUST_EVIDENCE["service_charge_bnb"])
    value_usd = gross_bnb * bnb_price
    value_eur = value_usd * usd_eur
    return [
        {
            "timestamp_utc": DUST_EVIDENCE["inferred_timestamp_utc"],
            "asset": "VTHO",
            "quantity": DUST_EVIDENCE["quantity"],
            "side": "in",
            "event_type": "asset_dividend",
            "tax_category": "INCOME_SO",
            "tx_id": f"binance-inferred-vtho-reward:{DUST_EVIDENCE['binance_trans_id']}",
            "source": "binance_api_inferred",
            "source_exchange": "binance",
            "evidence_type": "inferred_from_primary_dust_convert",
            "evidence_tx_id": DUST_EVIDENCE["binance_trans_id"],
            "value_usd": plain(value_usd),
            "value_eur": plain(value_eur),
            "price_usd": plain(value_usd / dec(DUST_EVIDENCE["quantity"])),
            "fx_rate_usd_eur": plain(usd_eur),
            "raw_row": DUST_EVIDENCE | {"gross_bnb": plain(gross_bnb), "bnb_usd": plain(bnb_price), "usd_eur": plain(usd_eur)},
        }
    ]


def rate(date: str, base: str, quote: str) -> Decimal:
    row = STORE.get_fx_rate(rate_date=date, base_ccy=base, quote_ccy=quote)
    if row is None:
        row = STORE.get_fx_rate_on_or_before(rate_date=date, base_ccy=base, quote_ccy=quote)
    value = dec(row.get("rate") if isinstance(row, dict) else "0")
    if value <= 0:
        raise SystemExit(f"Missing rate {base}/{quote} for {date}")
    return value


def summarize_import(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "source_file_id": str(result.get("source_file_id") or ""),
        "source_created": bool(result.get("source_created")),
        "inserted_events": int(result.get("inserted_events") or 0),
        "duplicate_events": int(result.get("duplicate_events") or 0),
    }


def render_doc(audit: dict[str, Any]) -> str:
    row = audit["rows"][0]
    lines = [
        "# Inferred VTHO Reward From Binance Dust - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Eng begrenzte Rekonstruktion eines fehlenden VTHO-Zugangs aus einem belegten Binance-API-Dust-Convert.",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Duplikate: `{audit['duplicate_existing_event_count']}`",
        f"- Neue Kandidaten: `{audit['new_candidate_event_count']}`",
        f"- Asset/Menge: `{row['quantity']} {row['asset']}`",
        f"- Timestamp: `{row['timestamp_utc']}`",
        f"- Evidence TX: `{row['evidence_tx_id']}`",
        f"- Wert USD/EUR: `{row['value_usd']}` / `{row['value_eur']}`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    if audit["import_result"]:
        lines += ["", "## Import Result", "", f"- `{audit['import_result']}`"]
    return "\n".join(lines) + "\n"


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Decimal) -> str:
    return value.normalize().to_eng_string() if value else "0"


if __name__ == "__main__":
    main()
