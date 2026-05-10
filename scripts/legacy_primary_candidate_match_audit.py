#!/usr/bin/env python3
"""Normalize legacy primary candidates and compare them with existing RAW events."""

from __future__ import annotations

import csv
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

from tax_engine.ingestion.connectors import normalize_connector_rows
from tax_engine.ingestion.service import _build_event_identity
from tax_engine.ingestion.store import STORE
from tax_engine.integrity import event_fingerprint

CREATED_DATE = "2026-05-09"
INVENTORY_JSON = ROOT / "var" / f"legacy_data_inventory_ai_audit_{CREATED_DATE}.json"
JSON_PATH = ROOT / "var" / f"legacy_primary_candidate_match_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"98_LEGACY_PRIMARY_CANDIDATE_MATCH_AUDIT_{CREATED_DATE}.md"
MAX_ROWS = 250000


def main() -> None:
    inventory = json.loads(INVENTORY_JSON.read_text(encoding="utf-8"))
    candidates = inventory["candidates"]["primary_import_or_match_candidates"]
    existing_ids = {str(row["unique_event_id"]) for row in STORE.list_raw_events()}
    file_reports = []
    aggregate_new_by_connector: Counter[str] = Counter()
    aggregate_dup_by_connector: Counter[str] = Counter()
    aggregate_new_by_year: Counter[str] = Counter()
    aggregate_new_by_asset: Counter[str] = Counter()

    for candidate in candidates:
        path = ROOT / candidate["path"]
        connector_id = connector_for_candidate(candidate)
        if connector_id is None:
            file_reports.append({"path": candidate["path"], "status": "skipped", "reason": "no_connector_mapping"})
            continue
        raw_rows, read_warnings = read_table(path)
        normalized, warnings, errors = normalize_connector_rows(connector_id, raw_rows, max_rows=MAX_ROWS)
        event_ids = [event_fingerprint(_build_event_identity(row)) for row in normalized]
        unique_event_ids = set(event_ids)
        duplicate_ids = unique_event_ids & existing_ids
        new_ids = unique_event_ids - existing_ids
        new_rows = [row for row, event_id in zip(normalized, event_ids, strict=False) if event_id in new_ids]
        duplicate_rows = [row for row, event_id in zip(normalized, event_ids, strict=False) if event_id in duplicate_ids]
        report = {
            "path": candidate["path"],
            "connector_id": connector_id,
            "status": "ok",
            "raw_row_count": len(raw_rows),
            "normalized_row_count": len(normalized),
            "unique_normalized_event_count": len(unique_event_ids),
            "duplicate_existing_event_count": len(duplicate_ids),
            "new_candidate_event_count": len(new_ids),
            "internal_duplicate_event_count": len(event_ids) - len(unique_event_ids),
            "read_warnings": read_warnings[:20],
            "normalizer_warning_count": len(warnings),
            "normalizer_warnings": warnings[:30],
            "normalizer_errors": errors[:30],
            "date_range": summarize_date_range(normalized),
            "asset_counts": summarize_assets(normalized),
            "event_type_counts": summarize_event_types(normalized),
            "new_candidate_summary": summarize_rows(new_rows),
            "duplicate_existing_summary": summarize_rows(duplicate_rows),
            "sample_new_rows": [slim_row(row) for row in new_rows[:20]],
        }
        file_reports.append(report)
        aggregate_new_by_connector[connector_id] += len(new_ids)
        aggregate_dup_by_connector[connector_id] += len(duplicate_ids)
        for year, count in report["new_candidate_summary"]["years"].items():
            aggregate_new_by_year[year] += count
        for asset, count in report["new_candidate_summary"]["assets"].items():
            aggregate_new_by_asset[asset] += count

    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "inventory_json": str(INVENTORY_JSON),
        "existing_raw_event_count": len(existing_ids),
        "candidate_file_count": len(candidates),
        "file_reports": file_reports,
        "summary": {
            "new_candidate_events_by_connector": dict(aggregate_new_by_connector.most_common()),
            "duplicate_existing_events_by_connector": dict(aggregate_dup_by_connector.most_common()),
            "new_candidate_events_by_year": dict(sorted(aggregate_new_by_year.items())),
            "new_candidate_events_by_asset": dict(aggregate_new_by_asset.most_common(30)),
            "files_with_new_events": [
                {
                    "path": row["path"],
                    "connector_id": row.get("connector_id", ""),
                    "new_candidate_event_count": row.get("new_candidate_event_count", 0),
                    "duplicate_existing_event_count": row.get("duplicate_existing_event_count", 0),
                }
                for row in file_reports
                if int(row.get("new_candidate_event_count") or 0) > 0
            ],
        },
        "interpretation": build_interpretation(file_reports),
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": audit["summary"]}, ensure_ascii=False, indent=2))


def connector_for_candidate(candidate: dict[str, Any]) -> str | None:
    category = str(candidate.get("category") or "")
    if category == "helium_legacy_raw":
        return "helium_legacy_raw"
    if category == "helium_legacy_cointracking":
        return "helium_legacy_cointracking"
    if category == "binance_export":
        return "binance"
    if category == "solscan_export":
        return None
    return None


def read_table(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            delimiter = detect_delimiter(path)
            try:
                df = pd.read_csv(path, sep=delimiter, dtype=str, keep_default_na=False, engine="python")
            except UnicodeDecodeError:
                df = pd.read_csv(path, sep=delimiter, dtype=str, keep_default_na=False, encoding="latin1", engine="python")
                warnings.append("latin1_fallback")
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
            return [], [f"unsupported_extension:{suffix}"]
    except Exception as exc:
        return [], [f"read_failed:{type(exc).__name__}:{exc}"]
    rows = []
    for row in df.head(MAX_ROWS).to_dict(orient="records"):
        clean = {str(key): "" if pd.isna(value) else value for key, value in row.items()}
        clean["__file_name"] = path.name
        clean["__source_name"] = str(path.relative_to(ROOT))
        rows.append(clean)
    return rows, warnings


def detect_delimiter(path: Path) -> str:
    sample = path.read_bytes()[:8192].decode("utf-8-sig", errors="ignore")
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        return ";" if sample.count(";") > sample.count(",") else ","


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    years: Counter[str] = Counter()
    assets: Counter[str] = Counter()
    event_types: Counter[str] = Counter()
    sides: Counter[str] = Counter()
    quantities: defaultdict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        ts = str(row.get("timestamp_utc") or row.get("timestamp") or "")
        year = ts[:4] if len(ts) >= 4 else "unknown"
        asset = str(row.get("asset") or "").upper() or "unknown"
        event_type = str(row.get("event_type") or "unknown")
        side = str(row.get("side") or "unknown")
        years[year] += 1
        assets[asset] += 1
        event_types[event_type] += 1
        sides[side] += 1
        quantities[asset] += decimal(row.get("quantity"))
    return {
        "count": len(rows),
        "years": dict(years.most_common(20)),
        "assets": dict(assets.most_common(30)),
        "event_types": dict(event_types.most_common(30)),
        "sides": dict(sides.most_common(10)),
        "quantity_totals": {asset: plain(value) for asset, value in sorted(quantities.items()) if value != 0},
    }


def summarize_date_range(rows: list[dict[str, Any]]) -> dict[str, str]:
    dates = [str(row.get("timestamp_utc") or "") for row in rows if len(str(row.get("timestamp_utc") or "")) >= 10]
    return {"min": min(dates) if dates else "", "max": max(dates) if dates else ""}


def summarize_assets(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("asset") or "unknown").upper() for row in rows).most_common(30))


def summarize_event_types(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("event_type") or "unknown") for row in rows).most_common(30))


def slim_row(row: dict[str, Any]) -> dict[str, str]:
    raw = row.get("raw_row") if isinstance(row.get("raw_row"), dict) else {}
    return {
        "timestamp_utc": str(row.get("timestamp_utc") or ""),
        "source": str(row.get("source") or ""),
        "event_type": str(row.get("event_type") or ""),
        "side": str(row.get("side") or ""),
        "asset": str(row.get("asset") or ""),
        "quantity": str(row.get("quantity") or ""),
        "tx_id": str(row.get("tx_id") or ""),
        "raw_type": str(raw.get("type") or raw.get("Type") or raw.get("Operation") or ""),
    }


def build_interpretation(file_reports: list[dict[str, Any]]) -> list[str]:
    with_new = [row for row in file_reports if int(row.get("new_candidate_event_count") or 0) > 0]
    return [
        f"{len(with_new)} Legacy-Primärdateien enthalten nach aktueller Fingerprint-Logik potenziell neue Events.",
        "Ein hoher New-Count bedeutet noch keinen Importfreigabe: alte Excel-Pivots und CoinTracking-Workbooks koennen abgeleitete Tabellen enthalten.",
        "CSV-Quellen mit Roh-/TXID-Bezug sind priorisiert; XLSX/Pivot-Dateien zuerst nur gegen bestehende Events und Summen abgleichen.",
        "Solscan-CSV wird separat behandelt, weil dafuer kein generischer Connector existiert und TokenAddress/Decimals korrekt gemappt werden muessen.",
    ]


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Legacy Primary Candidate Match Audit - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Die Primaer-/Match-Kandidaten aus dem Legacy-Datenordner werden mit den bestehenden RAW-Events verglichen. Es wurde nichts importiert.",
        "",
        "## Summary",
        "",
        f"- Bestehende RAW-Events: `{audit['existing_raw_event_count']}`",
        f"- Kandidatendateien: `{audit['candidate_file_count']}`",
        f"- Neue Kandidaten nach Connector: `{audit['summary']['new_candidate_events_by_connector']}`",
        f"- Duplikate nach Connector: `{audit['summary']['duplicate_existing_events_by_connector']}`",
        f"- Neue Kandidaten nach Jahr: `{audit['summary']['new_candidate_events_by_year']}`",
        f"- Neue Kandidaten nach Asset: `{audit['summary']['new_candidate_events_by_asset']}`",
        "",
        "## Dateien mit potenziell neuen Events",
        "",
    ]
    for row in audit["summary"]["files_with_new_events"]:
        lines.append(
            f"- `{row['path']}` connector `{row['connector_id']}` new `{row['new_candidate_event_count']}` duplicate `{row['duplicate_existing_event_count']}`"
        )
    lines += ["", "## Datei-Details", ""]
    for row in audit["file_reports"]:
        if row.get("status") != "ok":
            lines.append(f"- `{row['path']}` skipped `{row.get('reason')}`")
            continue
        lines += [
            f"### `{row['path']}`",
            "",
            f"- Connector: `{row['connector_id']}`",
            f"- Rohzeilen: `{row['raw_row_count']}`, normalisiert: `{row['normalized_row_count']}`, unique: `{row['unique_normalized_event_count']}`",
            f"- Bestehende Duplikate: `{row['duplicate_existing_event_count']}`, neue Kandidaten: `{row['new_candidate_event_count']}`, interne Duplikate: `{row['internal_duplicate_event_count']}`",
            f"- Zeitraum: `{row['date_range']}`",
            f"- Assets: `{row['asset_counts']}`",
            f"- Eventtypen: `{row['event_type_counts']}`",
            f"- Neue Summary: `{row['new_candidate_summary']}`",
            "",
        ]
    lines += ["## Bewertung", ""]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    lines += [
        "",
        "## Naechster Schritt",
        "",
        "- Fuer Dateien mit neuen Kandidaten pro Quelle entscheiden: echte Primaerquelle, abgeleitete Pivot-/Steuerdatei oder reiner Crosscheck.",
        "- Danach nur sicher primaere CSV/Export-Dateien per Import ausfuehren; XLSX-Pivots nicht automatisch steuerwirksam machen.",
    ]
    return "\n".join(lines) + "\n"


def decimal(value: Any) -> Decimal:
    try:
        text = str(value or "0").replace(",", ".")
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Decimal) -> str:
    return value.normalize().to_eng_string() if value else "0"


if __name__ == "__main__":
    main()
