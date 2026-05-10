#!/usr/bin/env python3
"""Semantic overlap checks for legacy files that fingerprint as new."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.connectors import normalize_connector_rows
from tax_engine.ingestion.store import STORE

CREATED_DATE = "2026-05-09"
JSON_PATH = ROOT / "var" / f"legacy_semantic_overlap_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"99_LEGACY_SEMANTIC_OVERLAP_AUDIT_{CREATED_DATE}.md"

HELIUM_RAW_FILES = [
    ROOT / "usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-raw.csv",
    ROOT / "usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2022-raw.csv",
    ROOT / "usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2023-raw.csv",
]
HELIUM_WORKBOOKS = [
    ROOT / "usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-2023 cointracking.xlsx",
    ROOT / "usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-2023 cointracking.xlsm",
]
BINANCE_PIVOTS = [
    ROOT / "usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - PIVOT.xlsx",
    ROOT / "usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - Skalierung angepasst.xlsx",
]


def main() -> None:
    existing = STORE.list_raw_events()
    existing_helium_base_tx = collect_existing_helium_base_tx(existing)
    existing_binance_keys = collect_existing_binance_semantic_keys(existing)

    helium_raw_reports = [
        semantic_tx_overlap(path, "helium_legacy_raw", existing_helium_base_tx)
        for path in HELIUM_RAW_FILES
    ]
    helium_workbook_reports = [
        semantic_tx_overlap(path, "helium_legacy_cointracking", existing_helium_base_tx)
        for path in HELIUM_WORKBOOKS
    ]
    binance_reports = [
        semantic_binance_overlap(path, existing_binance_keys)
        for path in BINANCE_PIVOTS
    ]

    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "existing_helium_base_tx_count": len(existing_helium_base_tx),
        "existing_binance_semantic_key_count": len(existing_binance_keys),
        "helium_raw_reports": helium_raw_reports,
        "helium_workbook_reports": helium_workbook_reports,
        "binance_pivot_reports": binance_reports,
        "interpretation": build_interpretation(helium_raw_reports, helium_workbook_reports, binance_reports),
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": summarize(audit)}, ensure_ascii=False, indent=2))


def collect_existing_helium_base_tx(events: list[dict[str, Any]]) -> set[str]:
    result = set()
    for event in events:
        payload = payload_of(event)
        source = str(payload.get("source") or "")
        asset = str(payload.get("asset") or "").upper()
        if not source.startswith("helium_legacy") or asset != "HNT":
            continue
        tx_id = base_tx(str(payload.get("tx_id") or ""))
        if tx_id:
            result.add(tx_id)
    return result


def collect_existing_binance_semantic_keys(events: list[dict[str, Any]]) -> set[tuple[str, str, str, str, str, str]]:
    result = set()
    for event in events:
        payload = payload_of(event)
        if not str(payload.get("source") or "").startswith("binance"):
            continue
        key = semantic_key(payload)
        if key:
            result.add(key)
    return result


def semantic_tx_overlap(path: Path, connector_id: str, existing_base_tx: set[str]) -> dict[str, Any]:
    rows = read_rows(path)
    normalized, warnings, errors = normalize_connector_rows(connector_id, rows, max_rows=250000)
    tx_ids = [base_tx(str(row.get("tx_id") or "")) for row in normalized]
    tx_ids = [tx_id for tx_id in tx_ids if tx_id]
    unique_tx = set(tx_ids)
    matched = unique_tx & existing_base_tx
    unmatched = unique_tx - existing_base_tx
    return {
        "path": str(path.relative_to(ROOT)),
        "connector_id": connector_id,
        "raw_rows": len(rows),
        "normalized_rows": len(normalized),
        "unique_base_tx_count": len(unique_tx),
        "matched_existing_base_tx_count": len(matched),
        "unmatched_base_tx_count": len(unmatched),
        "match_ratio": ratio(len(matched), len(unique_tx)),
        "event_type_counts": dict(Counter(str(row.get("event_type") or "unknown") for row in normalized).most_common()),
        "side_counts": dict(Counter(str(row.get("side") or "unknown") for row in normalized).most_common()),
        "warnings": warnings[:20],
        "errors": errors[:20],
        "unmatched_examples": sorted(unmatched)[:20],
    }


def semantic_binance_overlap(path: Path, existing_keys: set[tuple[str, str, str, str, str, str]]) -> dict[str, Any]:
    rows = read_rows(path)
    normalized, warnings, errors = normalize_connector_rows("binance", rows, max_rows=250000)
    keys = [semantic_key(row) for row in normalized]
    keys = [key for key in keys if key]
    unique_keys = set(keys)
    matched = unique_keys & existing_keys
    unmatched = unique_keys - existing_keys
    tx_id_count = sum(1 for row in normalized if str(row.get("tx_id") or "").strip())
    return {
        "path": str(path.relative_to(ROOT)),
        "raw_rows": len(rows),
        "normalized_rows": len(normalized),
        "unique_semantic_key_count": len(unique_keys),
        "matched_existing_semantic_key_count": len(matched),
        "unmatched_semantic_key_count": len(unmatched),
        "match_ratio": ratio(len(matched), len(unique_keys)),
        "normalized_rows_with_tx_id": tx_id_count,
        "event_type_counts": dict(Counter(str(row.get("event_type") or "unknown") for row in normalized).most_common()),
        "asset_counts": dict(Counter(str(row.get("asset") or "unknown").upper() for row in normalized).most_common(30)),
        "warnings": warnings[:20],
        "errors": errors[:20],
        "unmatched_examples": [
            dict(zip(("day", "asset", "event_type", "side", "quantity", "tx_id"), key, strict=True))
            for key in sorted(unmatched)[:20]
        ],
    }


def read_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        delimiter = detect_delimiter(path)
        try:
            df = pd.read_csv(path, sep=delimiter, dtype=str, keep_default_na=False, engine="python")
        except UnicodeDecodeError:
            df = pd.read_csv(path, sep=delimiter, dtype=str, keep_default_na=False, encoding="latin1", engine="python")
    elif suffix in {".xlsx", ".xlsm"}:
        sheets = pd.read_excel(path, sheet_name=None, dtype=str, keep_default_na=False)
        frames = []
        for sheet_name, sheet_df in sheets.items():
            if sheet_df.empty:
                continue
            sheet_df = sheet_df.copy()
            sheet_df["__sheet_name"] = str(sheet_name)
            frames.append(sheet_df)
        df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    else:
        return []
    rows = []
    for row in df.to_dict(orient="records"):
        clean = {str(key): "" if pd.isna(value) else value for key, value in row.items()}
        clean["__file_name"] = path.name
        clean["__source_name"] = str(path.relative_to(ROOT))
        rows.append(clean)
    return rows


def detect_delimiter(path: Path) -> str:
    sample = path.read_bytes()[:8192].decode("utf-8-sig", errors="ignore")
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        return ";" if sample.count(";") > sample.count(",") else ","


def semantic_key(payload: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    day = ts[:16] if len(ts) >= 16 else ts[:10]
    return (
        day,
        str(payload.get("asset") or "").upper(),
        str(payload.get("event_type") or "").lower(),
        str(payload.get("side") or "").lower(),
        normalize_decimal(payload.get("quantity")),
        base_tx(str(payload.get("tx_id") or "")),
    )


def payload_of(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def base_tx(value: str) -> str:
    value = value.strip()
    if "+" in value:
        return value.split("+", 1)[0]
    for suffix in (":in", ":out", ":fee"):
        if value.endswith(suffix):
            return value[: -len(suffix)]
    return value


def normalize_decimal(value: Any) -> str:
    try:
        text = str(value or "0").strip().replace(",", ".")
        return Decimal(text).normalize().to_eng_string()
    except (InvalidOperation, ValueError):
        return str(value or "").strip()


def ratio(part: int, whole: int) -> str:
    if whole <= 0:
        return "0"
    return f"{part / whole:.6f}"


def build_interpretation(
    helium_raw: list[dict[str, Any]],
    helium_workbooks: list[dict[str, Any]],
    binance_reports: list[dict[str, Any]],
) -> list[str]:
    lines = []
    raw_unmatched = sum(int(row["unmatched_base_tx_count"]) for row in helium_raw)
    raw_total = sum(int(row["unique_base_tx_count"]) for row in helium_raw)
    lines.append(f"Helium raw overlap by base TXID: {raw_total - raw_unmatched}/{raw_total} matched existing Helium legacy TXIDs.")
    workbook_unmatched = sum(int(row["unmatched_base_tx_count"]) for row in helium_workbooks)
    workbook_total = sum(int(row["unique_base_tx_count"]) for row in helium_workbooks)
    lines.append(f"Helium workbook overlap by base TXID: {workbook_total - workbook_unmatched}/{workbook_total} matched existing Helium legacy TXIDs.")
    for row in binance_reports:
        lines.append(
            f"Binance derived file `{row['path']}` has {row['normalized_rows_with_tx_id']} normalized rows with tx_id and semantic match ratio {row['match_ratio']}."
        )
    lines.append("If Helium raw matches by base TXID, it should be kept as evidence/validation unless replacing the CoinTracking layer deliberately.")
    lines.append("Binance Pivot/Skalierung files have weak/no tx_id coverage and should not be imported automatically as primary ledger rows.")
    return lines


def summarize(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "helium_raw": [
            {key: row[key] for key in ("path", "unique_base_tx_count", "matched_existing_base_tx_count", "unmatched_base_tx_count", "match_ratio")}
            for row in audit["helium_raw_reports"]
        ],
        "helium_workbooks": [
            {key: row[key] for key in ("path", "unique_base_tx_count", "matched_existing_base_tx_count", "unmatched_base_tx_count", "match_ratio")}
            for row in audit["helium_workbook_reports"]
        ],
        "binance_pivots": [
            {key: row[key] for key in ("path", "unique_semantic_key_count", "matched_existing_semantic_key_count", "unmatched_semantic_key_count", "normalized_rows_with_tx_id", "match_ratio")}
            for row in audit["binance_pivot_reports"]
        ],
    }


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Legacy Semantic Overlap Audit - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Semantischer Abgleich der Legacy-Dateien, die per Fingerprint als neu erschienen. Es wurde nichts importiert.",
        "",
        "## Helium Raw vs bestehende Helium-TXIDs",
        "",
    ]
    for row in audit["helium_raw_reports"]:
        lines.append(
            f"- `{row['path']}` unique_tx `{row['unique_base_tx_count']}` matched `{row['matched_existing_base_tx_count']}` unmatched `{row['unmatched_base_tx_count']}` ratio `{row['match_ratio']}` event_types `{row['event_type_counts']}` sides `{row['side_counts']}`"
        )
    lines += ["", "## Helium Workbooks vs bestehende Helium-TXIDs", ""]
    for row in audit["helium_workbook_reports"]:
        lines.append(
            f"- `{row['path']}` unique_tx `{row['unique_base_tx_count']}` matched `{row['matched_existing_base_tx_count']}` unmatched `{row['unmatched_base_tx_count']}` ratio `{row['match_ratio']}`"
        )
    lines += ["", "## Binance Pivot/Skalierung", ""]
    for row in audit["binance_pivot_reports"]:
        lines.append(
            f"- `{row['path']}` unique_keys `{row['unique_semantic_key_count']}` matched `{row['matched_existing_semantic_key_count']}` unmatched `{row['unmatched_semantic_key_count']}` rows_with_tx_id `{row['normalized_rows_with_tx_id']}` ratio `{row['match_ratio']}`"
        )
        lines.append(f"  - Eventtypen: `{row['event_type_counts']}`")
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    lines += [
        "",
        "## Entscheidung",
        "",
        "- Helium raw ist primaer als Evidenz-/Validierungsschicht zu behandeln, solange CoinTracking-Helium bereits steuerwirksam ist.",
        "- Binance Pivot/Skalierung nicht automatisch importieren; nur konkrete fehlende Earn/Savings/Distribution-Zeilen mit Primaerbeleg/API-Abgleich isolieren.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
