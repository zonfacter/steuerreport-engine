#!/usr/bin/env python3
"""Import the 2026-05-09 Blockpit export as reference rows."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion import confirm_import
from tax_engine.ingestion.connectors import normalize_connector_rows

CREATED_DATE = "2026-05-09"
DEFAULT_INPUT = ROOT / "usertransfer" / "blockpit" / "blockpit 09052026 Transactions.csv"
JSON_PATH = ROOT / "var" / f"blockpit_reference_export_import_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"89_BLOCKPIT_REFERENCE_EXPORT_IMPORT_{CREATED_DATE}.md"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--execute", action="store_true", help="Persist normalized rows.")
    parser.add_argument("--max-rows", type=int, default=20000)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    raw_rows = read_csv(input_path)
    normalized, warnings, errors = normalize_connector_rows("blockpit", raw_rows, max_rows=args.max_rows)
    import_result: dict[str, Any] | None = None
    if args.execute:
        import_result = confirm_import(source_name=input_path.name, rows=normalized)

    raw_summary = summarize_raw_rows(raw_rows)
    normalized_summary = summarize_normalized_rows(normalized)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": "execute" if args.execute else "preview",
        "input_path": str(input_path),
        "raw_row_count": len(raw_rows),
        "normalized_row_count": len(normalized),
        "normalizer_warnings": warnings[:200],
        "normalizer_warning_count": len(warnings),
        "normalizer_errors": errors[:200],
        "normalizer_error_count": len(errors),
        "raw_summary": raw_summary,
        "normalized_summary": normalized_summary,
        "import_result": summarize_import(import_result),
        "interpretation": build_interpretation(args.execute, raw_summary, normalized_summary, import_result),
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": compact_summary(audit)}, indent=2, ensure_ascii=False))


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter=";")]


def summarize_raw_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    years: Counter[str] = Counter()
    integrations: Counter[str] = Counter()
    source_names: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    bitget_years: Counter[str] = Counter()
    bitget_labels: Counter[str] = Counter()
    bitget_2025_labels: Counter[str] = Counter()
    for row in rows:
        year = year_from_blockpit_date(str(row.get("Date (UTC)") or ""))
        integration = str(row.get("Integration Name") or "").strip() or "unknown"
        source_name = str(row.get("Source Name") or "").strip() or "unknown"
        label = str(row.get("Label") or "").strip() or "unknown"
        years[year] += 1
        integrations[integration] += 1
        source_names[source_name] += 1
        labels[label] += 1
        if integration.lower() == "bitget" or source_name.lower() == "bitget":
            bitget_years[year] += 1
            bitget_labels[label] += 1
            if year == "2025":
                bitget_2025_labels[label] += 1
    return {
        "years": top_counts(years, 20),
        "integrations": top_counts(integrations, 20),
        "source_names": top_counts(source_names, 20),
        "labels": top_counts(labels, 30),
        "bitget_years": top_counts(bitget_years, 20),
        "bitget_labels": top_counts(bitget_labels, 30),
        "bitget_2025_labels": top_counts(bitget_2025_labels, 30),
    }


def summarize_normalized_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    years: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    event_types: Counter[str] = Counter()
    assets: Counter[str] = Counter()
    sides: Counter[str] = Counter()
    bitget_2025_event_types: Counter[str] = Counter()
    bitget_2025_assets: Counter[str] = Counter()
    for row in rows:
        raw = row.get("raw_row") if isinstance(row.get("raw_row"), dict) else {}
        ts = str(row.get("timestamp_utc") or "")
        year = ts[:4] if len(ts) >= 4 else year_from_blockpit_date(str(raw.get("Date (UTC)") or ""))
        source_name = str(raw.get("Source Name") or raw.get("Integration Name") or "").strip().lower()
        sources[str(row.get("source") or "unknown")] += 1
        event_type = str(row.get("event_type") or "unknown")
        asset = str(row.get("asset") or "unknown").upper()
        years[year] += 1
        event_types[event_type] += 1
        assets[asset] += 1
        sides[str(row.get("side") or "unknown")] += 1
        if source_name == "bitget" and year == "2025":
            bitget_2025_event_types[event_type] += 1
            bitget_2025_assets[asset] += 1
    return {
        "years": top_counts(years, 20),
        "sources": top_counts(sources, 20),
        "event_types": top_counts(event_types, 40),
        "assets": top_counts(assets, 40),
        "sides": top_counts(sides, 10),
        "bitget_2025_event_types": top_counts(bitget_2025_event_types, 40),
        "bitget_2025_assets": top_counts(bitget_2025_assets, 40),
    }


def year_from_blockpit_date(value: str) -> str:
    value = value.strip()
    if len(value) >= 10 and value[2] == "." and value[5] == ".":
        return value[6:10]
    if len(value) >= 4 and value[:4].isdigit():
        return value[:4]
    return "unknown"


def top_counts(counter: Counter[str], limit: int) -> dict[str, int]:
    return {key: int(value) for key, value in counter.most_common(limit)}


def summarize_import(import_result: dict[str, Any] | None) -> dict[str, Any] | None:
    if import_result is None:
        return None
    return {
        "source_file_id": str(import_result.get("source_file_id") or ""),
        "source_created": bool(import_result.get("source_created")),
        "inserted_events": int(import_result.get("inserted_events", 0)),
        "duplicate_events": int(import_result.get("duplicate_events", 0)),
    }


def build_interpretation(
    executed: bool,
    raw_summary: dict[str, Any],
    normalized_summary: dict[str, Any],
    import_result: dict[str, Any] | None,
) -> list[str]:
    lines = [
        "Der Export wurde als Blockpit-Referenzdatenquelle behandelt. Blockpit ist im System standardmaessig reference und wird nicht automatisch als Primaerquelle in Steuerlaeufe uebernommen.",
    ]
    bitget_2025 = raw_summary.get("bitget_years", {}).get("2025", 0)
    lines.append(f"Der Export enthaelt {bitget_2025} rohe Bitget-Zeilen fuer 2025.")
    if normalized_summary.get("bitget_2025_event_types"):
        lines.append("Die Bitget-2025-Zeilen koennen fuer Matching gegen Bitget-API, On-Chain-Transfers und Supportexporte genutzt werden.")
    if not executed:
        lines.append("Preview-only: Es wurden keine RAW-Events geschrieben.")
    elif import_result is not None:
        lines.append(
            f"Importiert: {int(import_result.get('inserted_events', 0))} neue RAW-Events, "
            f"{int(import_result.get('duplicate_events', 0))} Duplikate."
        )
    return lines


def compact_summary(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": audit["mode"],
        "raw_row_count": audit["raw_row_count"],
        "normalized_row_count": audit["normalized_row_count"],
        "bitget_years": audit["raw_summary"]["bitget_years"],
        "bitget_2025_event_types": audit["normalized_summary"]["bitget_2025_event_types"],
        "import_result": audit["import_result"],
    }


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Blockpit Reference Export Import - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Der neue Blockpit-Export aus `/workspace/steuerreport/usertransfer/blockpit/` wird als Referenz- und Abgleichsquelle gesichert. Er kann Bitget-Historie enthalten, die bei Bitget selbst ueber normale API/GUI-Retention nicht mehr vollstaendig sichtbar ist.",
        "",
        "## Lauf",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Datei: `{audit['input_path']}`",
        f"- Rohzeilen: `{audit['raw_row_count']}`",
        f"- Normalisierte Zeilen: `{audit['normalized_row_count']}`",
        f"- Normalizer-Warnungen: `{audit['normalizer_warning_count']}`",
        f"- Normalizer-Errors: `{audit['normalizer_error_count']}`",
    ]
    if audit["import_result"]:
        result = audit["import_result"]
        lines += [
            f"- Neu importierte RAW-Events: `{result['inserted_events']}`",
            f"- Duplikate: `{result['duplicate_events']}`",
            f"- Source File ID: `{result['source_file_id']}`",
        ]
    lines += ["", "## Rohdaten: Jahre", ""]
    for key, value in audit["raw_summary"]["years"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Rohdaten: Integrationen", ""]
    for key, value in audit["raw_summary"]["integrations"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Bitget Rohdaten", ""]
    for key, value in audit["raw_summary"]["bitget_years"].items():
        lines.append(f"- Jahr `{key}`: `{value}`")
    lines += ["", "## Bitget 2025 Labels", ""]
    for key, value in audit["raw_summary"]["bitget_2025_labels"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Bitget 2025 normalisierte Eventtypen", ""]
    for key, value in audit["normalized_summary"]["bitget_2025_event_types"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Bewertung", ""]
    for item in audit["interpretation"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
