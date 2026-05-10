#!/usr/bin/env python3
"""Probe and optionally import Bitget 2025 history via stored API credentials."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import resolve_cex_credentials
from tax_engine.connectors import (
    fetch_cex_transactions_preview,
    mask_api_key,
    verify_cex_credentials,
)
from tax_engine.ingestion import confirm_import

CREATED_DATE = "2026-05-09"
JSON_PATH = ROOT / "var" / f"bitget_2025_api_deep_probe_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"88_BITGET_2025_API_DEEP_PROBE_{CREATED_DATE}.md"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Persist fetched rows via confirm_import.")
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument("--timeout-seconds", type=int, default=45)
    parser.add_argument("--max-rows", type=int, default=5000)
    parser.add_argument("--start-date", default="2025-01-01")
    parser.add_argument("--end-date", default="2025-12-31")
    args = parser.parse_args()

    if args.window_days < 1:
        raise SystemExit("--window-days must be >= 1")
    if args.max_rows < 50:
        raise SystemExit("--max-rows must be >= 50")

    credentials = resolve_cex_credentials("bitget")
    api_key = credentials["api_key"]
    api_secret = credentials["api_secret"]
    passphrase = credentials["passphrase"]
    if not api_key or not api_secret or not passphrase:
        raise SystemExit("Bitget credentials incomplete in stored settings.")

    start_dt = parse_date_start(args.start_date)
    end_dt = parse_date_end(args.end_date)
    if start_dt >= end_dt:
        raise SystemExit("start-date must be before end-date.")

    verification = verify_cex_credentials(
        connector_id="bitget",
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
        timeout_seconds=args.timeout_seconds,
    )

    window_results: list[dict[str, Any]] = []
    total_rows = 0
    total_inserted = 0
    total_duplicates = 0
    source_counts: Counter[str] = Counter()
    event_type_counts: Counter[str] = Counter()
    asset_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()
    error_windows = 0

    for window_start, window_end in iter_windows(start_dt, end_dt, args.window_days):
        start_ms = int(window_start.timestamp() * 1000)
        end_ms = int(window_end.timestamp() * 1000)
        result: dict[str, Any] = {
            "start_utc": window_start.isoformat(),
            "end_utc": window_end.isoformat(),
            "start_time_ms": start_ms,
            "end_time_ms": end_ms,
            "status": "pending",
            "row_count": 0,
            "sources": {},
            "event_types": {},
            "assets": {},
            "warnings": [],
            "import_result": None,
        }
        try:
            preview = fetch_cex_transactions_preview(
                connector_id="bitget",
                api_key=api_key,
                api_secret=api_secret,
                passphrase=passphrase,
                timeout_seconds=args.timeout_seconds,
                max_rows=args.max_rows,
                start_time_ms=start_ms,
                end_time_ms=end_ms,
            )
            rows = preview.get("rows", [])
            if not isinstance(rows, list):
                rows = []
            warnings = [item for item in preview.get("warnings", []) if isinstance(item, dict)]
            result["status"] = "success"
            result["row_count"] = len(rows)
            result["warnings"] = warnings
            result["sources"] = top_counts(Counter(str(row.get("source") or "unknown") for row in rows), 20)
            result["event_types"] = top_counts(Counter(str(row.get("event_type") or "unknown") for row in rows), 20)
            result["assets"] = top_counts(Counter(str(row.get("asset") or "unknown").upper() for row in rows), 20)

            total_rows += len(rows)
            source_counts.update(str(row.get("source") or "unknown") for row in rows)
            event_type_counts.update(str(row.get("event_type") or "unknown") for row in rows)
            asset_counts.update(str(row.get("asset") or "unknown").upper() for row in rows)
            warning_counts.update(str(item.get("code") or "connector_warning") for item in warnings)

            if args.execute:
                source_name = f"bitget_api_2025_deep_{start_ms}_{end_ms}"
                import_result = confirm_import(source_name=source_name, rows=rows)
                result["import_result"] = {
                    "source_name": source_name,
                    "inserted_events": int(import_result.get("inserted_events", 0)),
                    "duplicate_events": int(import_result.get("duplicate_events", 0)),
                    "source_created": bool(import_result.get("source_created")),
                }
                total_inserted += int(import_result.get("inserted_events", 0))
                total_duplicates += int(import_result.get("duplicate_events", 0))
        except Exception as exc:
            error_windows += 1
            result["status"] = "error"
            result["error"] = str(exc)
        window_results.append(result)

    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": "execute" if args.execute else "preview",
        "connector_id": "bitget",
        "api_key_masked": mask_api_key(api_key),
        "scope": {
            "start_date": args.start_date,
            "end_date": args.end_date,
            "window_days": args.window_days,
            "timeout_seconds": args.timeout_seconds,
            "max_rows": args.max_rows,
        },
        "verification": verification,
        "summary": {
            "windows": len(window_results),
            "error_windows": error_windows,
            "fetched_rows": total_rows,
            "inserted_events": total_inserted,
            "duplicate_events": total_duplicates,
            "source_counts": top_counts(source_counts, 20),
            "event_type_counts": top_counts(event_type_counts, 20),
            "asset_counts": top_counts(asset_counts, 20),
            "warning_counts": top_counts(warning_counts, 30),
        },
        "windows": window_results,
        "interpretation": build_interpretation(args.execute, total_rows, total_inserted, warning_counts, error_windows),
    }

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": audit["summary"]}, indent=2, ensure_ascii=False))


def parse_date_start(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def parse_date_end(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC) + timedelta(days=1) - timedelta(milliseconds=1)


def iter_windows(start_dt: datetime, end_dt: datetime, window_days: int) -> list[tuple[datetime, datetime]]:
    windows: list[tuple[datetime, datetime]] = []
    current = start_dt
    delta = timedelta(days=window_days)
    while current <= end_dt:
        current_end = min(current + delta - timedelta(milliseconds=1), end_dt)
        windows.append((current, current_end))
        current = current_end + timedelta(milliseconds=1)
    return windows


def top_counts(counter: Counter[str], limit: int) -> dict[str, int]:
    return {key: int(value) for key, value in counter.most_common(limit)}


def build_interpretation(
    executed: bool,
    total_rows: int,
    inserted_events: int,
    warning_counts: Counter[str],
    error_windows: int,
) -> list[str]:
    lines: list[str] = []
    if total_rows == 0:
        lines.append("Die API hat fuer 2025 keine importierbaren Bitget-Zeilen geliefert.")
    elif executed and inserted_events == 0:
        lines.append("Die API-Zeilen waren bereits als Duplikate im Datenbestand vorhanden.")
    elif executed:
        lines.append(f"Der Lauf hat {inserted_events} neue Bitget-API-Events importiert.")
    else:
        lines.append("Der Lauf war Preview-only; es wurden keine RAW-Events geschrieben.")
    if error_windows:
        lines.append(f"{error_windows} Zeitfenster sind technisch fehlgeschlagen und muessen erneut geprueft werden.")
    if warning_counts:
        top = ", ".join(f"{key}={value}" for key, value in warning_counts.most_common(5))
        lines.append(f"Connector-Warnungen: {top}.")
    if "bitget_spot_account_bills_history_limit" in warning_counts:
        lines.append("Spot Account Bills bleiben fuer alte 2025-Zeitfenster API-seitig limitiert; dafuer sind Web-/Support-Exporte oder belegte Rekonstruktion noetig.")
    return lines


def render_doc(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        "# Bitget 2025 API Deep Probe - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Der Nutzer hat klargestellt, dass `bitget` `2025` soweit moeglich per API gezogen werden soll. Dieser Lauf nutzt ausschliesslich die gespeicherten Bitget-Secrets aus den Admin-Settings und gibt keine Secrets aus.",
        "",
        "## Lauf",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- API-Key: `{audit['api_key_masked']}`",
        f"- Credential-Check ok: `{bool(audit.get('verification', {}).get('ok'))}`",
        f"- Zeitraum: `{audit['scope']['start_date']}` bis `{audit['scope']['end_date']}`",
        f"- Fenster: `{audit['scope']['window_days']}` Tage",
        f"- Fenster gesamt: `{summary['windows']}`",
        f"- Fehlerfenster: `{summary['error_windows']}`",
        f"- API-Zeilen: `{summary['fetched_rows']}`",
        f"- Neu importiert: `{summary['inserted_events']}`",
        f"- Duplikate: `{summary['duplicate_events']}`",
        "",
        "## Quellen",
        "",
    ]
    for key, value in summary["source_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    if not summary["source_counts"]:
        lines.append("- Keine Zeilen.")
    lines += ["", "## Eventtypen", ""]
    for key, value in summary["event_type_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    if not summary["event_type_counts"]:
        lines.append("- Keine Zeilen.")
    lines += ["", "## Warnungen", ""]
    for key, value in summary["warning_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    if not summary["warning_counts"]:
        lines.append("- Keine Connector-Warnungen.")
    lines += ["", "## Fenster", ""]
    for window in audit["windows"]:
        import_result = window.get("import_result") or {}
        inserted = import_result.get("inserted_events", "")
        duplicates = import_result.get("duplicate_events", "")
        suffix = f", inserted `{inserted}`, duplicates `{duplicates}`" if import_result else ""
        lines.append(
            f"- `{window['start_utc']}` bis `{window['end_utc']}`: `{window['status']}`, "
            f"Zeilen `{window['row_count']}`{suffix}"
        )
    lines += ["", "## Bewertung", ""]
    for item in audit["interpretation"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
