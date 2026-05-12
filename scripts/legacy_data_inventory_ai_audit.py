#!/usr/bin/env python3
"""Inventory legacy usertransfer data and ask the local LLM for a source triage."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import resolve_effective_runtime_config

CREATED_DATE = "2026-05-09"
LEGACY_DIR = ROOT / "usertransfer" / "legacy_daten"
JSON_PATH = ROOT / "var" / f"legacy_data_inventory_ai_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"97_LEGACY_DATA_INVENTORY_AI_AUDIT_{CREATED_DATE}.md"
SUPPORTED_TABLE_EXTS = {".csv", ".xlsx", ".xlsm"}


def main() -> None:
    files = sorted(path for path in LEGACY_DIR.rglob("*") if path.is_file())
    inventory = [inspect_file(path) for path in files]
    duplicates = summarize_duplicates(inventory)
    source_summary = summarize_sources(inventory)
    candidates = build_candidate_lists(inventory)
    ai_input = compact_for_ai(inventory, duplicates, source_summary, candidates)
    ai_review = run_ai_review(ai_input)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "legacy_dir": str(LEGACY_DIR),
        "file_count": len(inventory),
        "source_summary": source_summary,
        "duplicates": duplicates,
        "candidates": candidates,
        "files": inventory,
        "ai_input": ai_input,
        "ai_review": ai_review,
        "interpretation": build_interpretation(source_summary, candidates, ai_review),
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": compact_summary(audit)}, ensure_ascii=False, indent=2))


def inspect_file(path: Path) -> dict[str, Any]:
    rel = str(path.relative_to(ROOT))
    suffix = path.suffix.lower()
    stat = path.stat()
    item: dict[str, Any] = {
        "path": rel,
        "name": path.name,
        "suffix": suffix,
        "size_bytes": stat.st_size,
        "sha256": sha256(path),
        "category": classify_path(path),
        "table": None,
        "warnings": [],
    }
    if suffix == ".csv":
        item["table"] = inspect_csv(path, item["warnings"])
    elif suffix in {".xlsx", ".xlsm"}:
        item["table"] = inspect_excel(path, item["warnings"])
    elif suffix == ".pdf":
        item["table"] = {"type": "pdf_evidence_only"}
    elif suffix in {".zip", ".gz"}:
        item["table"] = {"type": "archive_evidence_only"}
    else:
        item["warnings"].append("unsupported_extension")
    return item


def inspect_csv(path: Path, warnings: list[str]) -> dict[str, Any]:
    delimiter = detect_delimiter(path)
    try:
        df = pd.read_csv(path, sep=delimiter, dtype=str, nrows=200000, encoding="utf-8-sig", engine="python")
    except Exception as exc:
        try:
            df = pd.read_csv(path, sep=delimiter, dtype=str, nrows=200000, encoding="latin1", engine="python")
            warnings.append(f"csv_latin1_fallback:{type(exc).__name__}")
        except Exception as exc2:
            warnings.append(f"csv_read_failed:{type(exc2).__name__}:{exc2}")
            return {"type": "csv", "delimiter": delimiter, "readable": False}
    return summarize_dataframe(df, table_type="csv", delimiter=delimiter)


def inspect_excel(path: Path, warnings: list[str]) -> dict[str, Any]:
    try:
        xls = pd.ExcelFile(path)
    except Exception as exc:
        warnings.append(f"excel_open_failed:{type(exc).__name__}:{exc}")
        return {"type": "excel", "readable": False}
    sheets = []
    for sheet_name in xls.sheet_names[:10]:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str, nrows=200000)
            summary = summarize_dataframe(df, table_type="excel_sheet", delimiter="")
            summary["sheet_name"] = str(sheet_name)
            sheets.append(summary)
        except Exception as exc:
            sheets.append({"sheet_name": str(sheet_name), "readable": False, "warning": f"{type(exc).__name__}:{exc}"})
    return {"type": "excel", "readable": True, "sheet_count": len(xls.sheet_names), "sheets": sheets}


def summarize_dataframe(df: pd.DataFrame, *, table_type: str, delimiter: str) -> dict[str, Any]:
    columns = [str(col) for col in df.columns]
    date_candidates = find_date_range(df)
    assets = find_assets(df)
    numeric_totals = find_numeric_totals(df)
    samples = []
    for row in df.head(3).to_dict(orient="records"):
        samples.append({str(k): safe_cell(v) for k, v in row.items() if str(k) and not str(k).startswith("Unnamed")})
    return {
        "type": table_type,
        "readable": True,
        "delimiter": delimiter,
        "row_count_sampled": int(len(df)),
        "columns": columns[:80],
        "column_count": len(columns),
        "date_range": date_candidates,
        "assets": assets,
        "numeric_totals": numeric_totals,
        "sample_rows": samples,
    }


def detect_delimiter(path: Path) -> str:
    sample = path.read_bytes()[:8192].decode("utf-8-sig", errors="ignore")
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        return ";" if sample.count(";") > sample.count(",") else ","


def find_date_range(df: pd.DataFrame) -> dict[str, Any]:
    date_cols = [col for col in df.columns if any(key in str(col).lower() for key in ("date", "datum", "time", "zeit", "buchungstag"))]
    best: dict[str, Any] = {"columns_checked": [str(col) for col in date_cols[:8]], "min": "", "max": "", "count": 0}
    for col in date_cols[:8]:
        parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True, utc=True)
        parsed = parsed.dropna()
        if len(parsed) > int(best["count"]):
            best = {
                "columns_checked": [str(col) for col in date_cols[:8]],
                "best_column": str(col),
                "min": parsed.min().isoformat(),
                "max": parsed.max().isoformat(),
                "count": int(len(parsed)),
            }
    return best


def find_assets(df: pd.DataFrame) -> dict[str, Any]:
    asset_cols = [
        col
        for col in df.columns
        if any(key in str(col).lower() for key in ("currency", "coin", "asset", "token", "cur", "sellcurrency", "buycurrency"))
    ]
    counts: Counter[str] = Counter()
    for col in asset_cols[:12]:
        for value in df[col].dropna().astype(str).head(200000):
            normalized = value.strip().upper()
            if 1 <= len(normalized) <= 12 and not normalized.replace(".", "").isdigit():
                counts[normalized] += 1
    return {"columns_checked": [str(col) for col in asset_cols[:12]], "top_values": dict(counts.most_common(30))}


def find_numeric_totals(df: pd.DataFrame) -> dict[str, str]:
    totals: dict[str, str] = {}
    interesting = (
        "amount",
        "betrag",
        "mining rewards",
        "commissions",
        "hnt_amount",
        "iot",
        "mobile",
        "buyamount",
        "sellamount",
        "fee",
    )
    for col in df.columns:
        lowered = str(col).lower().replace(" ", "")
        if not any(key.replace(" ", "") in lowered for key in interesting):
            continue
        values = [parse_decimal(value) for value in df[col].dropna().head(200000)]
        nonzero = [value for value in values if value != 0]
        if nonzero:
            totals[str(col)] = plain(sum(nonzero))
    return dict(list(totals.items())[:30])


def classify_path(path: Path) -> str:
    text = str(path.relative_to(LEGACY_DIR)).lower()
    if "heliumtracker" in text:
        return "heliumtracker_rewards"
    if "helium-" in text and "raw" in text:
        return "helium_legacy_raw"
    if "helium-" in text and "cointracking" in text:
        return "helium_legacy_cointracking"
    if "cointracking" in text:
        return "cointracking_tax_or_export"
    if "binance" in text:
        return "binance_export"
    if "solscan" in text:
        return "solscan_export"
    if "kontist" in text:
        return "bank_kontist_evidence"
    if "barclays" in text or "kontoauszug" in text:
        return "bank_barclays_evidence"
    if "rechnung" in text or "invoice" in text or "nebra" in text or "sensecap" in text:
        return "hardware_invoice_evidence"
    if "blockpit" in text:
        return "blockpit_manual_template"
    return "other"


def summarize_sources(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: Counter[str] = Counter()
    by_suffix: Counter[str] = Counter()
    readable_tables = 0
    date_ranges = []
    for item in inventory:
        by_category[item["category"]] += 1
        by_suffix[item["suffix"]] += 1
        table = item.get("table")
        if table_has_rows(table):
            readable_tables += 1
            date_range = table_date_range(table)
            if date_range.get("min") or date_range.get("max"):
                date_ranges.append({"path": item["path"], **date_range})
    return {
        "by_category": dict(by_category.most_common()),
        "by_suffix": dict(by_suffix.most_common()),
        "readable_table_files": readable_tables,
        "date_ranges": sorted(date_ranges, key=lambda row: row.get("min") or "")[:120],
    }


def summarize_duplicates(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    by_hash: defaultdict[str, list[str]] = defaultdict(list)
    by_name: defaultdict[str, list[str]] = defaultdict(list)
    for item in inventory:
        by_hash[item["sha256"]].append(item["path"])
        by_name[item["name"].lower()].append(item["path"])
    exact = {key: paths for key, paths in by_hash.items() if len(paths) > 1}
    name = {key: paths for key, paths in by_name.items() if len(paths) > 1}
    return {
        "exact_duplicate_groups": len(exact),
        "exact_duplicate_files": sum(len(paths) for paths in exact.values()),
        "same_name_groups": len(name),
        "exact_duplicates": list(exact.values())[:50],
        "same_name_duplicates": list(name.values())[:50],
    }


def build_candidate_lists(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    primary = []
    reference = []
    evidence = []
    risky = []
    for item in inventory:
        table = item.get("table")
        category = item["category"]
        row_count = table_row_count(table)
        candidate = {
            "path": item["path"],
            "category": category,
            "suffix": item["suffix"],
            "rows": row_count,
            "date_range": table_date_range(table),
            "assets": table_assets(table),
            "warnings": item.get("warnings", []),
        }
        if category in {"helium_legacy_raw", "helium_legacy_cointracking", "binance_export", "solscan_export"} and row_count > 0:
            primary.append(candidate)
        elif category in {"heliumtracker_rewards", "cointracking_tax_or_export", "blockpit_manual_template"} and row_count > 0:
            reference.append(candidate)
        elif category.startswith("bank_") or category == "hardware_invoice_evidence" or item["suffix"] == ".pdf":
            evidence.append(candidate)
        else:
            risky.append(candidate)
    return {
        "primary_import_or_match_candidates": sorted(primary, key=lambda row: (-row["rows"], row["path"]))[:80],
        "reference_or_crosscheck_candidates": sorted(reference, key=lambda row: (-row["rows"], row["path"]))[:80],
        "evidence_only_candidates": sorted(evidence, key=lambda row: row["path"])[:120],
        "needs_manual_review": sorted(risky, key=lambda row: row["path"])[:80],
    }


def compact_for_ai(
    inventory: list[dict[str, Any]],
    duplicates: dict[str, Any],
    source_summary: dict[str, Any],
    candidates: dict[str, Any],
) -> dict[str, Any]:
    table_files = [item for item in inventory if table_has_rows(item.get("table"))]
    top_tables = sorted(
        table_files,
        key=lambda item: (table_row_count(item.get("table")), item["size_bytes"]),
        reverse=True,
    )[:35]
    return {
        "task": "Triage legacy crypto/tax data from 2021 onward. Identify primary import candidates, duplicate risks, and gaps for German crypto tax reconstruction.",
        "source_summary": source_summary,
        "duplicates": {
            "exact_duplicate_groups": duplicates["exact_duplicate_groups"],
            "same_name_groups": duplicates["same_name_groups"],
            "exact_duplicates_preview": duplicates["exact_duplicates"][:12],
        },
        "top_table_files": [
            {
                "path": item["path"],
                "category": item["category"],
                "suffix": item["suffix"],
                "rows": table_row_count(item.get("table")),
                "date_range": table_date_range(item.get("table")),
                "assets": table_assets(item.get("table")),
                "columns": table_columns(item.get("table"))[:25],
                "warnings": item.get("warnings", []),
            }
            for item in top_tables
        ],
        "candidate_counts": {key: len(value) for key, value in candidates.items()},
        "primary_candidates_preview": candidates["primary_import_or_match_candidates"][:25],
        "reference_candidates_preview": candidates["reference_or_crosscheck_candidates"][:25],
    }


def run_ai_review(ai_input: dict[str, Any]) -> dict[str, Any]:
    config = resolve_effective_runtime_config().get("runtime", {}).get("ai_review", {})
    base_url = str(config.get("llama_cpp_base_url") or "http://192.168.2.203:11435").rstrip("/")
    model = str(config.get("llama_cpp_model") or "qwen3.6-35b-a3b-iq4xs")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du darfst keinen Thinking-/Reasoning-Modus verwenden. "
                    "Gib ausschliesslich die finale sichtbare Antwort im Feld content aus."
                ),
            },
            {
                "role": "user",
                "content": (
                    "/no_think\n"
                    "Du bist Datenforensiker fuer einen deutschen Krypto-Steuerreport. "
                    "Bewerte diese Legacy-Datei-Inventur. Antworte als kompaktes JSON mit keys: "
                    "primary_imports, reference_only, evidence_only, duplicate_risks, missing_gaps, next_actions, confidence. "
                    "Keine Steuerberatung, nur Datenqualitaet und Rekonstruktionsplan.\n\n"
                    f"INVENTUR:\n{json.dumps(ai_input, ensure_ascii=False)}"
                ),
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1800,
    }
    started = datetime.now(UTC)
    try:
        req = urllib.request.Request(
            f"{base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=float(config.get("llama_cpp_timeout_seconds") or 900)) as response:
            decoded = json.loads(response.read().decode("utf-8"))
        elapsed = (datetime.now(UTC) - started).total_seconds()
        usage = decoded.get("usage") if isinstance(decoded, dict) else {}
        message = decoded.get("choices", [{}])[0].get("message", {})
        content = str(message.get("content") or "").strip()
        reasoning_present = bool(str(message.get("reasoning_content") or "").strip())
        if not content:
            return {
                "status": "invalid_empty_content",
                "base_url": base_url,
                "model": model,
                "elapsed_seconds": elapsed,
                "usage": usage,
                "reasoning_present": reasoning_present,
                "error": "Local model returned no visible content. Reasoning output was intentionally ignored.",
            }
        return {
            "status": "success",
            "base_url": base_url,
            "model": model,
            "elapsed_seconds": elapsed,
            "usage": usage,
            "reasoning_present": reasoning_present,
            "content": content,
        }
    except Exception as exc:
        return {
            "status": "error",
            "base_url": base_url,
            "model": model,
            "error": f"{type(exc).__name__}: {exc}",
        }


def build_interpretation(source_summary: dict[str, Any], candidates: dict[str, Any], ai_review: dict[str, Any]) -> list[str]:
    return [
        f"Inventar enthaelt {sum(source_summary.get('by_suffix', {}).values())} Dateien; wichtigste Kategorien: {source_summary.get('by_category')}.",
        f"Primaer-/Match-Kandidaten: {len(candidates['primary_import_or_match_candidates'])}; Referenz-/Crosscheck-Kandidaten: {len(candidates['reference_or_crosscheck_candidates'])}.",
        "Bankauszuege und Hardware-Rechnungen sind Belege fuer Fiat-/Anschaffungsketten, aber keine direkten Krypto-Events.",
        f"Lokale KI-Review Status: {ai_review.get('status')}.",
    ]


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Legacy Data Inventory + AI Audit - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Inventur von `/workspace/steuerreport/usertransfer/legacy_daten/` mit aktiver lokaler KI-Vorauswertung. Ziel ist, Primaerdaten, Referenzen, Belege und Duplikatrisiken fuer die Rekonstruktion ab 2021 zu trennen.",
        "",
        "## Summary",
        "",
        f"- Dateien: `{audit['file_count']}`",
        f"- Kategorien: `{audit['source_summary']['by_category']}`",
        f"- Endungen: `{audit['source_summary']['by_suffix']}`",
        f"- Lesbare Tabellendateien: `{audit['source_summary']['readable_table_files']}`",
        f"- Exakte Duplikatgruppen: `{audit['duplicates']['exact_duplicate_groups']}`",
        f"- Gleiche Dateinamen-Gruppen: `{audit['duplicates']['same_name_groups']}`",
        "",
        "## Kandidaten",
        "",
        f"- Primaer/Match: `{len(audit['candidates']['primary_import_or_match_candidates'])}`",
        f"- Referenz/Crosscheck: `{len(audit['candidates']['reference_or_crosscheck_candidates'])}`",
        f"- Evidence-only: `{len(audit['candidates']['evidence_only_candidates'])}`",
        f"- Manuell pruefen: `{len(audit['candidates']['needs_manual_review'])}`",
        "",
        "## Primaer-/Match-Kandidaten Top",
        "",
    ]
    for row in audit["candidates"]["primary_import_or_match_candidates"][:30]:
        lines.append(
            f"- `{row['path']}` rows `{row['rows']}` category `{row['category']}` dates `{row['date_range']}` assets `{row['assets']}`"
        )
    lines += ["", "## Referenz-/Crosscheck-Kandidaten Top", ""]
    for row in audit["candidates"]["reference_or_crosscheck_candidates"][:30]:
        lines.append(
            f"- `{row['path']}` rows `{row['rows']}` category `{row['category']}` dates `{row['date_range']}` assets `{row['assets']}`"
        )
    lines += ["", "## Duplikate", ""]
    for group in audit["duplicates"]["exact_duplicates"][:20]:
        lines.append(f"- Exact: `{group}`")
    lines += ["", "## Lokale KI", ""]
    ai = audit["ai_review"]
    lines += [
        f"- Status: `{ai.get('status')}`",
        f"- Modell: `{ai.get('model')}`",
        f"- Endpoint: `{ai.get('base_url')}`",
        f"- Dauer Sekunden: `{ai.get('elapsed_seconds', '')}`",
        f"- Usage: `{ai.get('usage', {})}`",
        "",
        "```text",
        str(ai.get("content") or ai.get("error") or "").strip(),
        "```",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    lines += [
        "",
        "## Naechste Aktionen",
        "",
        "- Nicht blind importieren: zuerst gegen vorhandene RAW-Events per Hash/Zeitraum/TxID matchen.",
        "- Helium Legacy raw + CoinTracking 2021-2023 als Primaer-/TXID-Abgleich nutzen, Heliumtracker als Reward-Referenz.",
        "- Binance-Alt-Exports mit vorhandenen Binance/Binance-API Events deduplizieren, besonders 2021/2022.",
        "- Bank-/Rechnungs-PDFs als Belegindex fuer Fiat- und Hardware-Anschaffungsketten erfassen, nicht als Krypto-Ledger.",
    ]
    return "\n".join(lines) + "\n"


def table_has_rows(table: Any) -> bool:
    return table_row_count(table) > 0


def table_row_count(table: Any) -> int:
    if not isinstance(table, dict):
        return 0
    if "row_count_sampled" in table:
        return int(table.get("row_count_sampled") or 0)
    sheets = table.get("sheets")
    if isinstance(sheets, list):
        return sum(table_row_count(sheet) for sheet in sheets)
    return 0


def table_date_range(table: Any) -> dict[str, Any]:
    if not isinstance(table, dict):
        return {}
    if "date_range" in table:
        return table.get("date_range") or {}
    sheets = table.get("sheets")
    if isinstance(sheets, list):
        ranges = [table_date_range(sheet) for sheet in sheets]
        ranges = [row for row in ranges if row.get("min") or row.get("max")]
        if ranges:
            return {"min": min(row.get("min", "") for row in ranges if row.get("min")), "max": max(row.get("max", "") for row in ranges if row.get("max"))}
    return {}


def table_assets(table: Any) -> dict[str, Any]:
    if not isinstance(table, dict):
        return {}
    if "assets" in table:
        return table.get("assets") or {}
    merged: Counter[str] = Counter()
    sheets = table.get("sheets")
    if isinstance(sheets, list):
        for sheet in sheets:
            assets = table_assets(sheet).get("top_values", {})
            merged.update(assets)
    return {"top_values": dict(merged.most_common(20))}


def table_columns(table: Any) -> list[str]:
    if not isinstance(table, dict):
        return []
    if isinstance(table.get("columns"), list):
        return list(table["columns"])
    sheets = table.get("sheets")
    if isinstance(sheets, list) and sheets:
        return table_columns(sheets[0])
    return []


def safe_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    return text[:160]


def parse_decimal(value: Any) -> Decimal:
    if value is None or pd.isna(value):
        return Decimal("0")
    text = str(value).strip()
    if not text:
        return Decimal("0")
    text = text.replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".") if text.rfind(",") > text.rfind(".") else text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Decimal) -> str:
    return value.normalize().to_eng_string() if value else "0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact_summary(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_count": audit["file_count"],
        "by_category": audit["source_summary"]["by_category"],
        "duplicates": {
            "exact_duplicate_groups": audit["duplicates"]["exact_duplicate_groups"],
            "same_name_groups": audit["duplicates"]["same_name_groups"],
        },
        "candidate_counts": {key: len(value) for key, value in audit["candidates"].items()},
        "ai_status": audit["ai_review"].get("status"),
        "ai_usage": audit["ai_review"].get("usage"),
    }


if __name__ == "__main__":
    main()
