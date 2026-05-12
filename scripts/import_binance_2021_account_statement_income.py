#!/usr/bin/env python3
"""Preview/import reviewed Binance 2021 account-statement income rows."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion import confirm_import
from tax_engine.ingestion.service import _build_event_identity
from tax_engine.ingestion.store import STORE
from tax_engine.integrity import event_fingerprint

CREATED_DATE = "2026-05-09"
SOURCE_XLSX = ROOT / "usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - PIVOT.xlsx"
SHEET = "part-00000-3d734e3b-9531-4c31-9"
JSON_PATH = ROOT / "var" / f"binance_2021_account_statement_income_import_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"101_BINANCE_2021_ACCOUNT_STATEMENT_INCOME_IMPORT_{CREATED_DATE}.md"
SOURCE_NAME = "legacy_binance_2021_account_statement_income_reviewed"
INCOME_OPERATION_MAP = {
    "Savings Interest": "interest",
    "Distribution": "asset_dividend",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Persist reviewed income rows.")
    parser.add_argument("--assets", default="", help="Optional comma-separated asset allow-list.")
    parser.add_argument("--exclude-assets", default="", help="Optional comma-separated asset deny-list.")
    args = parser.parse_args()

    rows = filter_rows(
        build_rows(),
        assets=parse_asset_filter(args.assets),
        exclude_assets=parse_asset_filter(args.exclude_assets),
    )
    existing_ids = {str(row["unique_event_id"]) for row in STORE.list_raw_events()}
    event_ids = [event_fingerprint(_build_event_identity(row)) for row in rows]
    duplicate_count = sum(1 for event_id in set(event_ids) if event_id in existing_ids)
    new_count = len(set(event_ids) - existing_ids)
    import_result = None
    if args.execute:
        import_result = confirm_import(source_name=SOURCE_NAME, rows=rows)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": "execute" if args.execute else "preview",
        "source_file": str(SOURCE_XLSX),
        "sheet": SHEET,
        "source_name": SOURCE_NAME,
        "asset_filter": {
            "assets": sorted(parse_asset_filter(args.assets)),
            "exclude_assets": sorted(parse_asset_filter(args.exclude_assets)),
        },
        "row_count": len(rows),
        "unique_event_count": len(set(event_ids)),
        "duplicate_existing_event_count": duplicate_count,
        "new_candidate_event_count": new_count,
        "summary": summarize(rows),
        "sample_rows": rows[:20],
        "import_result": summarize_import(import_result),
        "interpretation": build_interpretation(args.execute, rows, duplicate_count, new_count),
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": {k: audit[k] for k in ("mode", "row_count", "duplicate_existing_event_count", "new_candidate_event_count")}}, ensure_ascii=False, indent=2))


def build_rows() -> list[dict[str, Any]]:
    df = pd.read_excel(SOURCE_XLSX, sheet_name=SHEET, dtype=str, keep_default_na=False)
    out = []
    for idx, item in enumerate(df.to_dict(orient="records")):
        operation = str(item.get("Operation") or "").strip()
        event_type = INCOME_OPERATION_MAP.get(operation)
        if not event_type:
            continue
        quantity = dec(item.get("Change"))
        if quantity <= 0:
            continue
        timestamp = parse_ts(str(item.get("UTC_Time") or ""))
        asset = str(item.get("Coin") or "").strip().upper()
        tx_id = f"binance-account-statement:{operation}:{timestamp}:{asset}:{plain(quantity)}"
        out.append(
            {
                "timestamp_utc": timestamp,
                "asset": asset,
                "quantity": plain(quantity),
                "side": "in",
                "event_type": event_type,
                "tax_category": "INCOME_SO",
                "tx_id": tx_id,
                "source": "binance_account_statement",
                "source_exchange": "binance",
                "source_file": str(SOURCE_XLSX.relative_to(ROOT)),
                "source_sheet": SHEET,
                "source_row_index": idx,
                "raw_operation": operation,
                "raw_row": item,
            }
        )
    return out


def parse_asset_filter(value: str) -> set[str]:
    return {item.strip().upper() for item in str(value or "").split(",") if item.strip()}


def filter_rows(rows: list[dict[str, Any]], *, assets: set[str], exclude_assets: set[str]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        asset = str(row.get("asset") or "").upper().strip()
        if assets and asset not in assets:
            continue
        if exclude_assets and asset in exclude_assets:
            continue
        out.append(row)
    return out


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, Decimal] = {}
    counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    for row in rows:
        asset = str(row["asset"])
        totals[asset] = totals.get(asset, Decimal("0")) + dec(row["quantity"])
        counts[asset] = counts.get(asset, 0) + 1
        type_counts[row["event_type"]] = type_counts.get(row["event_type"], 0) + 1
    return {
        "counts_by_asset": dict(sorted(counts.items())),
        "totals_by_asset": {asset: plain(value) for asset, value in sorted(totals.items())},
        "counts_by_event_type": dict(sorted(type_counts.items())),
        "first_timestamp_utc": min((str(row["timestamp_utc"]) for row in rows), default=""),
        "last_timestamp_utc": max((str(row["timestamp_utc"]) for row in rows), default=""),
    }


def summarize_import(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "source_file_id": str(result.get("source_file_id") or ""),
        "source_created": bool(result.get("source_created")),
        "inserted_events": int(result.get("inserted_events") or 0),
        "duplicate_events": int(result.get("duplicate_events") or 0),
    }


def build_interpretation(executed: bool, rows: list[dict[str, Any]], duplicate_count: int, new_count: int) -> list[str]:
    lines = [
        "This importer only covers reviewed income-like rows: Savings Interest and Distribution.",
        "Savings purchase and principal redemption rows are intentionally excluded as principal/product movements.",
        f"Prepared {len(rows)} rows; {new_count} unique rows do not currently exist by import fingerprint.",
        "Rows have synthetic tx_id values because the Binance account statement sheet has no transaction ids.",
    ]
    if not executed:
        lines.append("Preview only: no RAW events were written.")
    else:
        lines.append("Execute mode: RAW events were written through confirm_import.")
    if duplicate_count:
        lines.append(f"{duplicate_count} rows already matched existing RAW event fingerprints.")
    return lines


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Binance 2021 Account Statement Income Import - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Dedizierter Importpfad fuer die geprueften Binance-Account-Statement-Income-Zeilen aus der Legacy-Pivot-Datei.",
        "",
        "## Lauf",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Quelle: `{audit['source_file']}`",
        f"- Sheet: `{audit['sheet']}`",
        f"- Asset Filter: `{audit['asset_filter']}`",
        f"- Zeilen: `{audit['row_count']}`",
        f"- Unique Events: `{audit['unique_event_count']}`",
        f"- Existing Duplikate: `{audit['duplicate_existing_event_count']}`",
        f"- Neue Kandidaten: `{audit['new_candidate_event_count']}`",
        f"- Summary: `{audit['summary']}`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    if audit["import_result"]:
        lines += ["", "## Import Result", "", f"- `{audit['import_result']}`"]
    lines += [
        "",
        "## Hinweis",
        "",
        "Diese Zeilen sind klein, aber potentiell steuerlich relevant. Vor Execute sollten Preise/EUR-Bewertung und NFT-Symbolbehandlung geprueft werden.",
    ]
    return "\n".join(lines) + "\n"


def parse_ts(value: str) -> str:
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return value
    return parsed.isoformat()


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Decimal) -> str:
    return value.normalize().to_eng_string() if value else "0"


if __name__ == "__main__":
    main()
