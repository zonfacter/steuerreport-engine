#!/usr/bin/env python3
"""Build read-only dossiers for zero-cost tax-lot issues."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from usdt_2022_zero_cost_dossier import (  # noqa: E402
    _asset_movements,
    _dec,
    _effective_processing_events,
    _latest_completed_job,
    _ledger,
    _line_report,
    _plain,
    _source_net_top,
    _source_windows,
    _yearly_net,
    _zero_cost_tax_lines,
)

from tax_engine.ingestion.store import STORE  # noqa: E402

CREATED_DATE = "2026-05-10"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a zero-cost issue dossier.")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--doc-number", type=int, default=182)
    args = parser.parse_args()
    year = args.year
    asset = args.asset.upper().strip()

    raw_events = STORE.list_raw_events()
    raw_events_by_id = {str(row.get("unique_event_id") or ""): row for row in raw_events}
    effective_events, processing_event_summary = _effective_processing_events(raw_events)
    effective_events_by_id = {str(row.get("unique_event_id") or ""): row for row in effective_events}
    tax_job = _latest_completed_job(year)
    if not tax_job:
        raise SystemExit(f"No completed processing job found for {year}")
    tax_lines = _zero_cost_tax_lines(str(tax_job["job_id"]), asset)
    movements = _asset_movements(effective_events, asset)
    ledger = _ledger(movements)
    dossier = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "read_only_dossier",
        "target_year": year,
        "target_asset": asset,
        "job": {
            "job_id": str(tax_job.get("job_id") or ""),
            "updated_at_utc": str(tax_job.get("updated_at_utc") or ""),
            "created_at_utc": str(tax_job.get("created_at_utc") or ""),
        },
        "processing_event_summary": processing_event_summary,
        "summary": _summary(asset, tax_lines, ledger),
        "zero_cost_lines": [
            _line_report(line, ledger, raw_events_by_id, effective_events_by_id)
            for line in tax_lines
        ],
        "source_windows": _source_windows(tax_lines, ledger),
        "evidence_interpretation": _interpretation(year, asset, tax_lines, ledger),
    }
    slug = f"{asset}_{year}_zero_cost_dossier_{CREATED_DATE}"
    json_path = ROOT / "var" / f"{slug.lower()}.json"
    doc_path = ROOT / "docs" / f"{args.doc_number}_{asset}_{year}_ZERO_COST_DOSSIER_{CREATED_DATE}.md"
    json_path.write_text(json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")
    doc_path.write_text(_render_doc(dossier, json_path), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "doc": str(doc_path), "lines": len(tax_lines)}, ensure_ascii=False, indent=2))


def _summary(asset: str, tax_lines: list[dict[str, Any]], ledger: list[dict[str, Any]]) -> dict[str, Any]:
    first_negative = next((row for row in ledger if row["balance_before"] >= 0 > row["balance_after"]), None)
    worst = min(ledger, key=lambda row: row["balance_after"], default=None)
    return {
        "zero_cost_line_count": len(tax_lines),
        "zero_cost_qty": _plain(sum((_dec(line.get("qty")) for line in tax_lines), start=Decimal("0"))),
        "zero_cost_proceeds_eur": _plain(sum((_dec(line.get("proceeds_eur")) for line in tax_lines), start=Decimal("0"))),
        "ledger_event_count": len(ledger),
        "final_balance": _plain(ledger[-1]["balance_after"]) if ledger else "0",
        "first_negative": _slim(first_negative),
        "worst_balance": _slim(worst),
        "yearly_net": _yearly_net(ledger),
        "source_net_top": _source_net_top(ledger),
        "asset": asset,
    }


def _interpretation(year: int, asset: str, tax_lines: list[dict[str, Any]], ledger: list[dict[str, Any]]) -> list[str]:
    first_negative = next((row for row in ledger if row["balance_before"] >= 0 > row["balance_after"]), None)
    lot_sources = {}
    source_events = {}
    for line in tax_lines:
        source_event_id = str(line.get("source_event_id") or "")
        row = next((item for item in ledger if item.get("event_id") == source_event_id), None)
        if row:
            key = f"{row.get('source')}/{row.get('event_type')}/{row.get('side')}"
            source_events[key] = source_events.get(key, 0) + 1
        lot_id = str(line.get("lot_source_event_id") or "empty_lot")
        lot_sources[lot_id] = lot_sources.get(lot_id, 0) + 1
    return [
        f"Die {len(tax_lines)} Zeilen sind steuerpflichtige {asset}-Verwendungen im Jahr {year} mit Cost Basis 0.",
        f"Erster aktiver {asset}-Bruch: {(first_negative or {}).get('timestamp', '')} after { _plain(_dec((first_negative or {}).get('balance_after'))) if first_negative else '0' }.",
        f"Source-Verteilung: {source_events}.",
        f"Lot-Source-Verteilung: {lot_sources}.",
        "Kein automatischer steuerwirksamer Import empfohlen, solange keine Primaerquelle die Anschaffungskette belegt.",
    ]


def _slim(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "timestamp": row.get("timestamp"),
        "source": row.get("source"),
        "event_type": row.get("event_type"),
        "side": row.get("side"),
        "quantity": _plain(_dec(row.get("quantity"))),
        "delta": _plain(_dec(row.get("delta"))),
        "balance_before": _plain(_dec(row.get("balance_before"))),
        "balance_after": _plain(_dec(row.get("balance_after"))),
        "tx_id": row.get("tx_id"),
        "event_id": row.get("event_id"),
    }


def _render_doc(dossier: dict[str, Any], json_path: Path) -> str:
    asset = dossier["target_asset"]
    year = dossier["target_year"]
    summary = dossier["summary"]
    first = summary.get("first_negative") or {}
    worst = summary.get("worst_balance") or {}
    lines = [
        f"# {asset} {year} Zero-Cost Dossier",
        "",
        f"Stand: {CREATED_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Status: `{dossier['status']}`",
        f"- Job: `{dossier['job']['job_id']}`",
        f"- Nullkosten-Zeilen: `{summary['zero_cost_line_count']}`",
        f"- Menge: `{summary['zero_cost_qty']} {asset}`",
        f"- Erloes: `{summary['zero_cost_proceeds_eur']} EUR`",
        f"- Erster aktiver {asset}-Bruch: `{first.get('timestamp', '')}` after `{first.get('balance_after', '')}` event `{first.get('event_id', '')}`",
        f"- Schlechtester aktiver {asset}-Stand: `{worst.get('balance_after', '')}` bei `{worst.get('timestamp', '')}`",
        f"- Finaler {asset}-Stand: `{summary['final_balance']}`",
        "",
        "## Betroffene Steuerzeilen",
        "",
        "| Line | Zeit | Quelle | Menge | Erloes EUR | Balance vorher | Balance nach | TX |",
        "|---:|---|---|---:|---:|---:|---:|---|",
    ]
    for item in dossier["zero_cost_lines"]:
        row = (item.get("ledger_rows_for_source_event") or [{}])[0]
        src = item.get("source_event_raw") or {}
        lines.append(
            f"| {item['line_no']} | `{item['sell_timestamp_utc']}` | `{src.get('source', '')}` `{src.get('event_type', '')}` `{src.get('side', '')}` | "
            f"{item['qty']} | {item['proceeds_eur']} | {row.get('balance_before', '')} | {row.get('balance_after', '')} | `{src.get('tx_id', '')}` |"
        )
    lines += ["", "## Interpretation", ""]
    lines.extend(f"- {item}" for item in dossier["evidence_interpretation"])
    lines += ["", "## Kritische Ledger-Kontexte", ""]
    for item in dossier["zero_cost_lines"][:8]:
        lines += [
            f"### Line {item['line_no']}",
            "",
            f"- Platform-Hinweis: `{item['platform_hint']}`",
            f"- Source Event: `{item['source_event_id']}`",
            f"- Lot Source Event: `{item['lot_source_event_id'] or 'empty_lot'}`",
            "",
        ]
        for row in item.get("ledger_context", [])[:25]:
            lines.append(
                f"- `{row.get('timestamp', '')}` `{row.get('source', '')}` / `{row.get('event_type', '')}` / `{row.get('side', '')}` "
                f"delta `{row.get('delta', '')}` before `{row.get('balance_before', '')}` after `{row.get('balance_after', '')}` tx `{row.get('tx_id', '')}`"
            )
        lines.append("")
    lines += [
        "## Naechste Belegziele",
        "",
        f"- Primaerquelle fuer {asset}-Zufluss/Erwerb vor dem ersten Bruch pruefen.",
        "- Wenn es ein Swap ist: Gegenseite, Transferkette und Bewertungsanker pruefen.",
        "- Wenn es ein Plattform-/Wallet-Kontext ist: Deposit-/Withdrawal-/Bridge-Historie vor dem Bruch pruefen.",
        "- Ohne Beleg keine steuerwirksame Zuflussfiktion importieren.",
        "",
        f"JSON: `{json_path.relative_to(ROOT)}`",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
