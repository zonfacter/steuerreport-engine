#!/usr/bin/env python3
"""Audit Binance 2021 account-statement income rows from legacy pivot export."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

CREATED_DATE = "2026-05-09"
SOURCE_XLSX = ROOT / "usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - PIVOT.xlsx"
SHEET = "part-00000-3d734e3b-9531-4c31-9"
JSON_PATH = ROOT / "var" / f"binance_2021_account_statement_income_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"100_BINANCE_2021_ACCOUNT_STATEMENT_INCOME_AUDIT_{CREATED_DATE}.md"
INCOME_OPERATIONS = {"Savings Interest", "Distribution"}
PRINCIPAL_OPERATIONS = {"Savings purchase", "Savings Principal redemption"}


def main() -> None:
    rows = load_rows()
    existing = effective_events()
    existing_keys = build_existing_keys(existing)
    operation_summary = summarize_operations(rows)
    income_rows = [row for row in rows if row["operation"] in INCOME_OPERATIONS]
    principal_rows = [row for row in rows if row["operation"] in PRINCIPAL_OPERATIONS]
    income_report = summarize_income_rows(income_rows, existing_keys)
    principal_report = summarize_principal_rows(principal_rows)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_file": str(SOURCE_XLSX),
        "sheet": SHEET,
        "row_count": len(rows),
        "operation_summary": operation_summary,
        "income_report": income_report,
        "principal_report": principal_report,
        "interpretation": build_interpretation(income_report, principal_report),
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": compact_summary(audit)}, ensure_ascii=False, indent=2))


def load_rows() -> list[dict[str, Any]]:
    df = pd.read_excel(SOURCE_XLSX, sheet_name=SHEET, dtype=str, keep_default_na=False)
    rows = []
    for item in df.to_dict(orient="records"):
        ts = parse_ts(str(item.get("UTC_Time") or ""))
        rows.append(
            {
                "timestamp_utc": ts,
                "operation": str(item.get("Operation") or "").strip(),
                "account": str(item.get("Account") or "").strip(),
                "asset": str(item.get("Coin") or "").strip().upper(),
                "quantity": plain(dec(item.get("Change"))),
                "remark": str(item.get("Remark") or "").strip(),
                "raw": item,
            }
        )
    return rows


def effective_events() -> list[dict[str, Any]]:
    raw = STORE.list_raw_events()
    reviewed, _ = apply_review_actions(raw)
    effective, _ = apply_tax_event_overrides(reviewed)
    return effective


def build_existing_keys(events: list[dict[str, Any]]) -> set[tuple[str, str, str]]:
    keys = set()
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        asset = str(payload.get("asset") or "").upper()
        qty = abs(dec(payload.get("quantity") or payload.get("amount")))
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if len(ts) < 16 or not asset or qty == 0:
            continue
        keys.add((ts[:16], asset, plain(qty)))
    return keys


def summarize_operations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_operation: Counter[str] = Counter()
    by_operation_asset: Counter[str] = Counter()
    totals: defaultdict[tuple[str, str], Decimal] = defaultdict(Decimal)
    for row in rows:
        op = row["operation"] or "unknown"
        asset = row["asset"] or "unknown"
        qty = dec(row["quantity"])
        by_operation[op] += 1
        by_operation_asset[f"{op}:{asset}"] += 1
        totals[(op, asset)] += qty
    return {
        "by_operation": dict(by_operation.most_common()),
        "by_operation_asset_top": dict(by_operation_asset.most_common(60)),
        "totals_by_operation_asset": {f"{op}:{asset}": plain(value) for (op, asset), value in sorted(totals.items()) if value != 0},
    }


def summarize_income_rows(rows: list[dict[str, Any]], existing_keys: set[tuple[str, str, str]]) -> dict[str, Any]:
    matched = []
    unmatched = []
    totals: defaultdict[str, Decimal] = defaultdict(Decimal)
    counts: Counter[str] = Counter()
    for row in rows:
        key = (row["timestamp_utc"][:16], row["asset"], plain(abs(dec(row["quantity"]))))
        target = matched if key in existing_keys else unmatched
        target.append(row)
        totals[row["asset"]] += dec(row["quantity"])
        counts[f"{row['operation']}:{row['asset']}"] += 1
    return {
        "row_count": len(rows),
        "matched_existing_count": len(matched),
        "unmatched_count": len(unmatched),
        "counts": dict(counts.most_common()),
        "totals_by_asset": {asset: plain(value) for asset, value in sorted(totals.items())},
        "first_timestamp_utc": min((row["timestamp_utc"] for row in rows), default=""),
        "last_timestamp_utc": max((row["timestamp_utc"] for row in rows), default=""),
        "unmatched_rows": [slim(row) for row in unmatched[:400]],
    }


def summarize_principal_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals: defaultdict[str, Decimal] = defaultdict(Decimal)
    counts: Counter[str] = Counter()
    for row in rows:
        totals[row["asset"]] += dec(row["quantity"])
        counts[f"{row['operation']}:{row['asset']}"] += 1
    return {
        "row_count": len(rows),
        "counts": dict(counts.most_common()),
        "totals_by_asset": {asset: plain(value) for asset, value in sorted(totals.items()) if value != 0},
        "classification": "principal_internal_transfer_or_product_position_change",
        "tax_effective_recommendation": "do_not_import_as_income; use only for balance/evidence unless missing inventory requires explicit internal transfer modelling",
    }


def build_interpretation(income: dict[str, Any], principal: dict[str, Any]) -> list[str]:
    return [
        f"Income-like Binance account statement rows: {income['row_count']}; matched existing by timestamp/asset/quantity: {income['matched_existing_count']}; unmatched: {income['unmatched_count']}.",
        f"Income totals are small but potentially taxable/relevant: {income['totals_by_asset']}.",
        "Savings purchase/redemption rows are principal/product-position movements and should not be booked as income.",
        "Because the account statement rows have no tx_id, import should only happen through a dedicated reviewed importer with stable synthetic IDs and source documentation.",
    ]


def render_doc(audit: dict[str, Any]) -> str:
    income = audit["income_report"]
    principal = audit["principal_report"]
    lines = [
        "# Binance 2021 Account Statement Income Audit - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Isolierte Pruefung der Binance Legacy Account-Statement/Pivot-Datei. Es wurde nichts importiert.",
        "",
        "## Quelle",
        "",
        f"- Datei: `{audit['source_file']}`",
        f"- Sheet: `{audit['sheet']}`",
        f"- Zeilen: `{audit['row_count']}`",
        "",
        "## Operationen",
        "",
        f"- By Operation: `{audit['operation_summary']['by_operation']}`",
        f"- Totals: `{audit['operation_summary']['totals_by_operation_asset']}`",
        "",
        "## Income-Kandidaten",
        "",
        f"- Zeilen: `{income['row_count']}`",
        f"- Existing Match: `{income['matched_existing_count']}`",
        f"- Unmatched: `{income['unmatched_count']}`",
        f"- Counts: `{income['counts']}`",
        f"- Totals by Asset: `{income['totals_by_asset']}`",
        f"- Zeitraum: `{income['first_timestamp_utc']}` bis `{income['last_timestamp_utc']}`",
        "",
        "## Principal / Produktbewegungen",
        "",
        f"- Zeilen: `{principal['row_count']}`",
        f"- Counts: `{principal['counts']}`",
        f"- Totals by Asset: `{principal['totals_by_asset']}`",
        f"- Empfehlung: `{principal['tax_effective_recommendation']}`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    lines += [
        "",
        "## Entscheidung",
        "",
        "- `Savings Interest` und `Distribution` sind Kandidaten fuer einen dedizierten, review-pflichtigen Binance-Account-Statement-Income-Import.",
        "- `Savings purchase` und `Savings Principal redemption` bleiben vorerst nicht steuerwirksam; sie dokumentieren interne Produkt-/Principal-Bewegungen.",
    ]
    return "\n".join(lines) + "\n"


def slim(row: dict[str, Any]) -> dict[str, str]:
    return {
        "timestamp_utc": row["timestamp_utc"],
        "operation": row["operation"],
        "asset": row["asset"],
        "quantity": row["quantity"],
    }


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


def compact_summary(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "income": {
            "row_count": audit["income_report"]["row_count"],
            "matched_existing_count": audit["income_report"]["matched_existing_count"],
            "unmatched_count": audit["income_report"]["unmatched_count"],
            "totals_by_asset": audit["income_report"]["totals_by_asset"],
        },
        "principal": {
            "row_count": audit["principal_report"]["row_count"],
            "totals_by_asset": audit["principal_report"]["totals_by_asset"],
        },
    }


if __name__ == "__main__":
    main()
