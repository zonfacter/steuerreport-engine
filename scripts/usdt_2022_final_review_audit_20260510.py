#!/usr/bin/env python3
"""Create a final review audit for the remaining 2022 USDT zero-cost issue."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
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
    _plain,
    _zero_cost_tax_lines,
)

from tax_engine.ingestion.store import STORE  # noqa: E402

CREATED_DATE = "2026-05-10"
TARGET_YEAR = 2022
TARGET_ASSET = "USDT"
DOC_PATH = ROOT / "docs" / f"194_USDT_2022_FINAL_REVIEW_AUDIT_{CREATED_DATE}.md"
JSON_PATH = ROOT / "var" / f"usdt_2022_final_review_audit_{CREATED_DATE}.json"


def main() -> None:
    raw_events = STORE.list_raw_events()
    effective_events, processing_summary = _effective_processing_events(raw_events)
    tax_job = _latest_completed_job(TARGET_YEAR)
    if not tax_job:
        raise SystemExit(f"No completed processing job found for {TARGET_YEAR}")

    job_id = str(tax_job["job_id"])
    tax_lines = _zero_cost_tax_lines(job_id, TARGET_ASSET)
    ledger = _ledger(_asset_movements(effective_events, TARGET_ASSET))
    line_contexts = [_line_context(line, ledger) for line in tax_lines]

    audit = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "final_read_only_review",
        "target_year": TARGET_YEAR,
        "target_asset": TARGET_ASSET,
        "job_id": job_id,
        "processing_summary": processing_summary,
        "summary": _summary(tax_lines, ledger, line_contexts),
        "line_contexts": line_contexts,
        "checked_evidence": _checked_evidence(),
        "decision_options": _decision_options(),
        "conclusion": [
            "Die verbliebenen drei USDT-Zeilen sind keine Preis-/FX- oder Stable-Pair-Fehlbewertung.",
            "Die Pionex-HNT- und Stable-Pair-Korrekturen wurden bereits eingerechnet; HNT 2023, USDC 2024 und JUP 2024 sind geschlossen.",
            "Automatische steuerwirksame Rekonstruktion bleibt fachlich nicht sauber, weil ein Primaerbeleg fuer die konkrete USDT-Anschaffungskette fehlt.",
            "Das Issue kann technisch im Dashboard/API als Nullbasis bestaetigt werden; das ist eine Review-Entscheidung und keine RAW-Daten-Aenderung.",
        ],
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(_render_doc(audit), encoding="utf-8")
    print(json.dumps({"doc": str(DOC_PATH), "json": str(JSON_PATH), "lines": len(tax_lines)}, ensure_ascii=False, indent=2))


def _summary(
    tax_lines: list[dict[str, Any]],
    ledger: list[dict[str, Any]],
    line_contexts: list[dict[str, Any]],
) -> dict[str, Any]:
    first_negative = next((row for row in ledger if row["balance_before"] >= 0 > row["balance_after"]), None)
    worst = min(ledger, key=lambda row: row["balance_after"], default=None)
    by_platform: defaultdict[str, Decimal] = defaultdict(Decimal)
    for item in line_contexts:
        by_platform[str(item.get("source") or "unknown")] += _dec(item.get("zero_cost_qty"))
    return {
        "zero_cost_line_count": len(tax_lines),
        "zero_cost_qty": _plain(sum((_dec(line.get("qty")) for line in tax_lines), start=Decimal("0"))),
        "zero_cost_proceeds_eur": _plain(sum((_dec(line.get("proceeds_eur")) for line in tax_lines), start=Decimal("0"))),
        "first_negative": _slim_ledger_row(first_negative),
        "worst_balance": _slim_ledger_row(worst),
        "final_balance": _plain(ledger[-1]["balance_after"]) if ledger else "0",
        "platform_qty": {platform: _plain(qty) for platform, qty in sorted(by_platform.items())},
    }


def _line_context(line: dict[str, Any], ledger: list[dict[str, Any]]) -> dict[str, Any]:
    event_id = str(line.get("source_event_id") or "")
    row = next((item for item in ledger if str(item.get("event_id") or "") == event_id), None)
    if row is None:
        row = _nearest_row(ledger, str(line.get("sell_timestamp_utc") or ""))
    focus_index = int(row.get("index") or 0) if row else 0
    previous_rows = ledger[max(0, focus_index - 12) : focus_index]
    following_rows = ledger[focus_index + 1 : focus_index + 9]
    return {
        "line_no": int(line.get("line_no") or 0),
        "sell_timestamp_utc": str(line.get("sell_timestamp_utc") or ""),
        "zero_cost_qty": str(line.get("qty") or ""),
        "proceeds_eur": str(line.get("proceeds_eur") or ""),
        "source_event_id": event_id,
        "source": str((row or {}).get("source") or ""),
        "event_type": str((row or {}).get("event_type") or ""),
        "tx_id": str((row or {}).get("tx_id") or ""),
        "balance_before": _plain(_dec((row or {}).get("balance_before"))),
        "balance_after": _plain(_dec((row or {}).get("balance_after"))),
        "observed_context": _observed_context(line, row, previous_rows, following_rows),
        "previous_rows": [_slim_ledger_row(item) for item in previous_rows],
        "following_rows": [_slim_ledger_row(item) for item in following_rows],
    }


def _observed_context(
    line: dict[str, Any],
    row: dict[str, Any] | None,
    previous_rows: list[dict[str, Any]],
    following_rows: list[dict[str, Any]],
) -> str:
    source = str((row or {}).get("source") or "").lower()
    sell_ts = str(line.get("sell_timestamp_utc") or "")
    if source == "binance":
        return (
            f"Binance-USDT-Verwendung am {sell_ts}; im unmittelbaren Fenster liegen mehrere "
            "gleichzeitige HNT-Kaeufe/USDT-Spends. Der Bruch entsteht nach der letzten USDT-Verwendung "
            "und benoetigt eine vorherige USDT-Erwerbskette."
        )
    if source == "pionex" and sell_ts.startswith("2022-01-19T12:45"):
        return (
            "Pionex-MXC-Kauf wenige Minuten vor der belegten Binance-USDT-Auszahlung und Pionex-USDT-Einzahlung. "
            "Das spricht fuer Pionex-Opening-/Bot-Kontext oder nicht exportierte interne Historie."
        )
    if source == "pionex" and sell_ts.startswith("2022-01-19T12:56"):
        deposits = [item for item in previous_rows + following_rows if str(item.get("event_type") or "") == "deposit"]
        deposit_note = "mit naher Pionex-Deposit-Zeile" if deposits else "ohne nahe Deposit-Zeile"
        return (
            f"Pionex-MXC-Kauf nach der bekannten 1245.38419-USDT-Transferkette, aber der Kaufbedarf uebersteigt "
            f"den belegten Bestand; {deposit_note}. Rest erklaert sich nur mit Opening-/Bot-Historie."
        )
    return "Keine automatische Rekonstruktion aus dem unmittelbaren Ledger-Fenster ableitbar."


def _checked_evidence() -> list[dict[str, str]]:
    return [
        {
            "source": "Binance Transaction History Jan 2022",
            "path": "usertransfer/Binance/export 2021/Binance-Transaction-History-202605061835(UTC+2)_344d77e2.xlsx",
            "result": "liefert die HNT/USDT-Trades am 2022-01-05 und 2022-01-19, aber keine zusaetzliche vorherige USDT-Anschaffung fuer die Nullbasis-Reste",
        },
        {
            "source": "Pionex Komplett-Export",
            "path": "usertransfer/pionex/",
            "result": "liefert MXC_USDT-Bot-/Trade-Zeilen und die bekannten Deposits; fuer den 2022-01-19-Rest fehlt weiterhin eine belegte Opening-/Bot-Historie",
        },
        {
            "source": "Binance API/CSV Transferkette",
            "path": "raw_events/binance_api + usertransfer/Binance/export 2021/",
            "result": "belegt die 1245.38419-USDT-Auszahlung zu Pionex am 2022-01-19, deckt aber nicht den kompletten Pionex-Kaufbedarf",
        },
        {
            "source": "Aktueller Gesamtlauf 2020..2026",
            "path": "docs/190_CURRENT_TAX_RUNS_2026-05-10.md",
            "result": "Review-Gate ist exportfaehig; nur dieses Medium-Issue bleibt offen",
        },
    ]


def _decision_options() -> list[dict[str, str]]:
    return [
        {
            "option": "offen lassen",
            "effect": "Report bleibt mit Medium-Issue dokumentiert; keine fachliche Nullbasis-Freigabe",
        },
        {
            "option": "Nullbasis bestaetigen",
            "effect": "Issue per API/Dashboard auf wont_fix setzen; Steuerzeilen bleiben mit Cost Basis 0 sichtbar",
        },
        {
            "option": "Primaerbeleg nachreichen",
            "effect": "Neue Quelle importieren und Job neu rechnen; nur dann waere eine echte Cost-Basis-Korrektur sauber",
        },
    ]


def _nearest_row(ledger: list[dict[str, Any]], timestamp: str) -> dict[str, Any] | None:
    if not timestamp:
        return None
    candidates = [row for row in ledger if str(row.get("timestamp") or "") == timestamp]
    return candidates[0] if candidates else None


def _slim_ledger_row(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "timestamp": row.get("timestamp"),
        "source": row.get("source"),
        "event_type": row.get("event_type"),
        "side": row.get("side"),
        "delta": _plain(_dec(row.get("delta"))),
        "balance_before": _plain(_dec(row.get("balance_before"))),
        "balance_after": _plain(_dec(row.get("balance_after"))),
        "tx_id": row.get("tx_id"),
        "event_id": row.get("event_id"),
    }


def _render_doc(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    first = summary.get("first_negative") or {}
    worst = summary.get("worst_balance") or {}
    lines = [
        "# USDT 2022 Finaler Review-Audit",
        "",
        f"Stand: {CREATED_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Status: `{audit['status']}`",
        f"- Job: `{audit['job_id']}`",
        f"- Offene Nullbasis-Zeilen: `{summary['zero_cost_line_count']}`",
        f"- Betroffene Menge: `{summary['zero_cost_qty']} USDT`",
        f"- Erloes: `{summary['zero_cost_proceeds_eur']} EUR`",
        f"- Erster aktiver Bruch: `{first.get('timestamp', '')}` nach `{first.get('balance_after', '')} USDT`",
        f"- Schlechtester Stand: `{worst.get('balance_after', '')} USDT` bei `{worst.get('timestamp', '')}`",
        f"- Finaler USDT-Stand nach allen Daten: `{summary['final_balance']} USDT`",
        f"- Plattform-Mengen: `{summary['platform_qty']}`",
        "",
        "## Schlussfolgerung",
        "",
    ]
    lines.extend(f"- {item}" for item in audit["conclusion"])
    lines += [
        "",
        "## Betroffene Zeilen",
        "",
        "| Line | Zeit | Quelle | Menge | Erloes EUR | Balance vorher | Balance nach | Befund |",
        "|---:|---|---|---:|---:|---:|---:|---|",
    ]
    for item in audit["line_contexts"]:
        lines.append(
            f"| {item['line_no']} | `{item['sell_timestamp_utc']}` | `{item['source']}` `{item['event_type']}` | "
            f"{item['zero_cost_qty']} | {item['proceeds_eur']} | {item['balance_before']} | {item['balance_after']} | "
            f"{item['observed_context']} |"
        )
    lines += [
        "",
        "## Gepruefte Belege",
        "",
    ]
    for item in audit["checked_evidence"]:
        lines.append(f"- `{item['source']}`: `{item['path']}` -> {item['result']}.")
    lines += [
        "",
        "## Saubere Entscheidungswege",
        "",
    ]
    for item in audit["decision_options"]:
        lines.append(f"- `{item['option']}`: {item['effect']}.")
    lines += [
        "",
        "## Wichtig fuer den Report",
        "",
        "- Keine RAW-Datei wurde veraendert.",
        "- Keine automatische Zuflussfiktion wurde importiert.",
        "- Eine Bestaetigung der Nullbasis ist nur eine Review-Freigabe, keine Aenderung der Steuerlogik.",
        "- Bei neuen Pionex-/Binance-/Bitget-Exporten muss dieser Audit erneut ausgefuehrt und der 2022-Job neu gerechnet werden.",
        "",
        f"JSON: `{JSON_PATH.relative_to(ROOT)}`",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
