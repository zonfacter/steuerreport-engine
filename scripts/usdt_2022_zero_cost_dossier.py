#!/usr/bin/env python3
"""Build a read-only dossier for the remaining 2022 USDT zero-cost tax lots."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from chronological_balance_break_audit import (  # noqa: E402
    _load_ignored_tokens,
    _load_token_aliases,
    _movement_sort_key,
    _movements,
    _plain,
    _year,
)

from tax_engine.ingestion.store import STORE  # noqa: E402
from tax_engine.integrations import filter_events_for_processing  # noqa: E402
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides  # noqa: E402
from tax_engine.queue.service import (  # noqa: E402
    attach_reference_usd_value_anchors,
    drop_exact_pionex_duplicate_events,
    drop_solscan_duplicates_when_solana_rpc_is_active,
)

CREATED_DATE = "2026-05-10"
TARGET_YEAR = 2022
TARGET_ASSET = "USDT"
JSON_PATH = ROOT / "var" / f"usdt_2022_zero_cost_dossier_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"181_USDT_2022_ZERO_COST_DOSSIER_{CREATED_DATE}.md"


def main() -> None:
    raw_events = STORE.list_raw_events()
    raw_events_by_id = {str(row.get("unique_event_id") or ""): row for row in raw_events}
    effective_events, processing_event_summary = _effective_processing_events(raw_events)
    effective_events_by_id = {str(row.get("unique_event_id") or ""): row for row in effective_events}
    tax_job = _latest_completed_job(TARGET_YEAR)
    if not tax_job:
        raise SystemExit(f"No completed processing job found for {TARGET_YEAR}")
    tax_lines = _zero_cost_tax_lines(str(tax_job["job_id"]), TARGET_ASSET)
    movements = _asset_movements(effective_events, TARGET_ASSET)
    ledger = _ledger(movements)
    dossier = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "read_only_dossier",
        "target_year": TARGET_YEAR,
        "target_asset": TARGET_ASSET,
        "job": {
            "job_id": str(tax_job.get("job_id") or ""),
            "updated_at_utc": str(tax_job.get("updated_at_utc") or ""),
            "created_at_utc": str(tax_job.get("created_at_utc") or ""),
        },
        "processing_event_summary": processing_event_summary,
        "summary": _summary(tax_lines, ledger),
        "zero_cost_lines": [
            _line_report(line, ledger, raw_events_by_id, effective_events_by_id)
            for line in tax_lines
        ],
        "source_windows": _source_windows(tax_lines, ledger),
        "evidence_interpretation": _interpretation(tax_lines, ledger),
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(_render_doc(dossier), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "lines": len(tax_lines)}, ensure_ascii=False, indent=2))


def _latest_completed_job(year: int) -> dict[str, Any] | None:
    latest: dict[str, Any] | None = None
    for job in STORE.list_processing_jobs(status="completed", limit=5000):
        if int(job.get("tax_year") or 0) != year:
            continue
        if latest is None or str(job.get("updated_at_utc") or "") > str(latest.get("updated_at_utc") or ""):
            latest = job
    return latest


def _zero_cost_tax_lines(job_id: str, asset: str) -> list[dict[str, Any]]:
    rows = []
    for line in STORE.get_tax_lines(job_id):
        if str(line.get("asset") or "").upper() != asset:
            continue
        if str(line.get("tax_status") or "").lower() != "taxable":
            continue
        if _dec(line.get("cost_basis_eur")) != 0:
            continue
        if _dec(line.get("proceeds_eur")) <= 0:
            continue
        rows.append(line)
    rows.sort(key=lambda row: (str(row.get("sell_timestamp_utc") or ""), int(row.get("line_no") or 0)))
    return rows


def _asset_movements(events: list[dict[str, Any]], asset: str) -> list[dict[str, Any]]:
    token_aliases = _load_token_aliases()
    ignored_mints = set(_load_ignored_tokens().keys())
    movements = [
        movement
        for row in events
        for movement in _movements(row, token_aliases=token_aliases, ignored_mints=ignored_mints)
        if _year(movement["timestamp"]) >= 2020 and movement["asset"] == asset
    ]
    movements.sort(key=_movement_sort_key)
    return movements


def _effective_processing_events(raw_events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    filtered, integration_filter_summary = filter_events_for_processing(raw_events, {"include_reference_sources": False})
    deduped_pionex, pionex_duplicate_summary = drop_exact_pionex_duplicate_events(filtered)
    deduped_solscan, solscan_duplicate_summary = drop_solscan_duplicates_when_solana_rpc_is_active(deduped_pionex)
    valued, valuation_anchor_summary = attach_reference_usd_value_anchors(deduped_solscan, raw_events)
    reviewed, review_action_summary = apply_review_actions(valued)
    effective, override_count = apply_tax_event_overrides(reviewed)
    return effective, {
        "basis": "processing_pipeline_event_basis",
        "integration_filter": integration_filter_summary,
        "pionex_dedupe": pionex_duplicate_summary,
        "solscan_dedupe": solscan_duplicate_summary,
        "valuation_anchors": valuation_anchor_summary,
        "review_actions": review_action_summary,
        "tax_event_override_count": override_count,
    }


def _ledger(movements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    balance = Decimal("0")
    rows = []
    for index, row in enumerate(movements):
        before = balance
        after = before + row["delta"]
        balance = after
        rows.append(
            {
                **row,
                "index": index,
                "balance_before": before,
                "balance_after": after,
            }
        )
    return rows


def _summary(tax_lines: list[dict[str, Any]], ledger: list[dict[str, Any]]) -> dict[str, Any]:
    first_negative = next((row for row in ledger if row["balance_before"] >= 0 > row["balance_after"]), None)
    worst = min(ledger, key=lambda row: row["balance_after"], default=None)
    return {
        "zero_cost_line_count": len(tax_lines),
        "zero_cost_qty": _plain(sum((_dec(line.get("qty")) for line in tax_lines), start=Decimal("0"))),
        "zero_cost_proceeds_eur": _plain(sum((_dec(line.get("proceeds_eur")) for line in tax_lines), start=Decimal("0"))),
        "ledger_event_count": len(ledger),
        "final_balance": _plain(ledger[-1]["balance_after"]) if ledger else "0",
        "first_negative": _slim_ledger_row(first_negative),
        "worst_balance": _slim_ledger_row(worst),
        "yearly_net": _yearly_net(ledger),
        "source_net_top": _source_net_top(ledger),
    }


def _line_report(
    line: dict[str, Any],
    ledger: list[dict[str, Any]],
    raw_events_by_id: dict[str, dict[str, Any]],
    effective_events_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_event_id = str(line.get("source_event_id") or "")
    sell_ts = str(line.get("sell_timestamp_utc") or "")
    related_ledger = [row for row in ledger if row.get("event_id") == source_event_id]
    focus_index = related_ledger[0]["index"] if related_ledger else _nearest_index(ledger, sell_ts)
    raw_event = raw_events_by_id.get(source_event_id)
    effective_event = effective_events_by_id.get(source_event_id)
    return {
        "line_no": int(line.get("line_no") or 0),
        "qty": str(line.get("qty") or ""),
        "proceeds_eur": str(line.get("proceeds_eur") or ""),
        "cost_basis_eur": str(line.get("cost_basis_eur") or ""),
        "gain_loss_eur": str(line.get("gain_loss_eur") or ""),
        "buy_timestamp_utc": str(line.get("buy_timestamp_utc") or ""),
        "sell_timestamp_utc": sell_ts,
        "source_event_id": source_event_id,
        "lot_source_event_id": str(line.get("lot_source_event_id") or ""),
        "source_event_raw": _event_brief(raw_event),
        "source_event_effective": _event_brief(effective_event),
        "ledger_rows_for_source_event": [_slim_ledger_row(row) for row in related_ledger],
        "ledger_context": [_slim_ledger_row(row) for row in _index_window(ledger, focus_index, before=12, after=8)],
        "same_tx_or_trade_group": _same_tx_or_group(source_event_id, ledger, raw_events_by_id),
        "platform_hint": _platform_hint(raw_event or effective_event),
    }


def _source_windows(tax_lines: list[dict[str, Any]], ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    windows = []
    seen: set[tuple[str, str]] = set()
    for line in tax_lines:
        event_id = str(line.get("source_event_id") or "")
        sell_ts = str(line.get("sell_timestamp_utc") or "")
        key = (event_id, sell_ts)
        if key in seen:
            continue
        seen.add(key)
        focus_index = _nearest_index(ledger, sell_ts)
        focus_rows = _index_window(ledger, focus_index, before=30, after=15)
        windows.append(
            {
                "source_event_id": event_id,
                "sell_timestamp_utc": sell_ts,
                "window_start": focus_rows[0]["timestamp"] if focus_rows else "",
                "window_end": focus_rows[-1]["timestamp"] if focus_rows else "",
                "net_in_window": _plain(sum((row["delta"] for row in focus_rows), start=Decimal("0"))),
                "rows": [_slim_ledger_row(row) for row in focus_rows],
            }
        )
    return windows


def _interpretation(tax_lines: list[dict[str, Any]], ledger: list[dict[str, Any]]) -> list[str]:
    source_counter = Counter()
    for line in tax_lines:
        row = next((item for item in ledger if item.get("event_id") == str(line.get("source_event_id") or "")), None)
        if row:
            source_counter[(str(row.get("source") or ""), str(row.get("event_type") or ""), str(row.get("side") or ""))] += 1
    return [
        "Die drei Zeilen sind echte steuerpflichtige USDT-Verwendungen mit Cost Basis 0 aus dem neuesten 2022-Job, nicht nur Bewertungsfehler.",
        "Der erste Bruch liegt vor dem Pionex-19.01.-Fenster in einer Binance-USDT-Verwendung am 2022-01-05; daher muss die Erwerbskette ab 2021/Anfang 2022 global betrachtet werden.",
        "Die zwei spaeteren Nullbasis-Zeilen liegen im Pionex-Fenster am 2022-01-19 und passen zum bekannten Bot-/Opening-Balance-Thema.",
        f"Source-Verteilung der betroffenen Tax-Lines: {dict(source_counter)}.",
        "Keine automatische steuerwirksame Buchung empfohlen: erforderlich ist ein Primaerbeleg oder eine explizite nicht steuerwirksame Review-Entscheidung mit Dokumentation.",
    ]


def _same_tx_or_group(source_event_id: str, ledger: list[dict[str, Any]], raw_events_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    payload = _payload(raw_events_by_id.get(source_event_id))
    tx_id = str(payload.get("tx_id") or payload.get("txid") or payload.get("transaction_id") or "").strip()
    timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    source = str(payload.get("source") or "")
    if tx_id:
        rows = [row for row in ledger if str(row.get("tx_id") or "") == tx_id]
    else:
        rows = [row for row in ledger if str(row.get("timestamp") or "") == timestamp and str(row.get("source") or "") == source]
    return [_slim_ledger_row(row) for row in rows[:40]]


def _index_window(ledger: list[dict[str, Any]], focus_index: int | None, *, before: int, after: int) -> list[dict[str, Any]]:
    if focus_index is None or focus_index < 0:
        return []
    return ledger[max(0, focus_index - before) : min(len(ledger), focus_index + after + 1)]


def _nearest_index(ledger: list[dict[str, Any]], timestamp: str) -> int | None:
    target = _parse_ts(timestamp)
    if target is None:
        return None
    best: tuple[timedelta, int] | None = None
    for row in ledger:
        ts = _parse_ts(str(row.get("timestamp") or ""))
        if ts is None:
            continue
        diff = abs(ts - target)
        if best is None or diff < best[0]:
            best = (diff, int(row["index"]))
    return best[1] if best else None


def _yearly_net(ledger: list[dict[str, Any]]) -> dict[str, str]:
    totals: defaultdict[int, Decimal] = defaultdict(Decimal)
    for row in ledger:
        totals[int(row["year"])] += row["delta"]
    return {str(year): _plain(total) for year, total in sorted(totals.items())}


def _source_net_top(ledger: list[dict[str, Any]]) -> list[dict[str, str]]:
    totals: Counter[tuple[str, str, str]] = Counter()
    for row in ledger:
        totals[(str(row.get("source") or ""), str(row.get("event_type") or ""), str(row.get("side") or ""))] += row["delta"]
    return [
        {"source": key[0], "event_type": key[1], "side": key[2], "net": _plain(value)}
        for key, value in sorted(totals.items(), key=lambda item: abs(item[1]), reverse=True)[:20]
    ]


def _event_brief(event: dict[str, Any] | None) -> dict[str, Any]:
    payload = _payload(event)
    if not payload:
        return {"found": False}
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    return {
        "found": True,
        "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
        "source": str(payload.get("source") or ""),
        "event_type": str(payload.get("event_type") or ""),
        "side": str(payload.get("side") or ""),
        "asset": str(payload.get("asset") or ""),
        "quantity": str(payload.get("quantity") or payload.get("amount") or ""),
        "tx_id": str(payload.get("tx_id") or payload.get("txid") or payload.get("transaction_id") or ""),
        "base_asset": str(payload.get("base_asset") or ""),
        "quote_asset": str(payload.get("quote_asset") or ""),
        "quote_quantity": str(payload.get("quote_quantity") or payload.get("quote_amount") or ""),
        "fee": str(payload.get("fee") or ""),
        "fee_asset": str(payload.get("fee_asset") or ""),
        "raw_label": str(raw.get("Label") or raw.get("label") or ""),
        "raw_comment": str(raw.get("Comment (optional)") or raw.get("comment") or ""),
    }


def _platform_hint(event: dict[str, Any] | None) -> str:
    source = str(_payload(event).get("source") or "").lower()
    if "pionex" in source:
        return "pionex_opening_or_bot_history"
    if "binance" in source:
        return "binance_2021_2022_acquisition_chain"
    return "global_acquisition_chain"


def _slim_ledger_row(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "index": row.get("index"),
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


def _payload(event: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(event, dict):
        return {}
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip())
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _render_doc(dossier: dict[str, Any]) -> str:
    summary = dossier["summary"]
    first = summary.get("first_negative") or {}
    worst = summary.get("worst_balance") or {}
    lines = [
        "# USDT 2022 Zero-Cost Dossier",
        "",
        f"Stand: {CREATED_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Status: `{dossier['status']}`",
        f"- Job: `{dossier['job']['job_id']}`",
        f"- Nullkosten-Zeilen: `{summary['zero_cost_line_count']}`",
        f"- Menge: `{summary['zero_cost_qty']} USDT`",
        f"- Erloes: `{summary['zero_cost_proceeds_eur']} EUR`",
        f"- Erster aktiver USDT-Bruch: `{first.get('timestamp', '')}` after `{first.get('balance_after', '')}` event `{first.get('event_id', '')}`",
        f"- Schlechtester aktiver USDT-Stand: `{worst.get('balance_after', '')}` bei `{worst.get('timestamp', '')}`",
        f"- Finaler USDT-Stand: `{summary['final_balance']}`",
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
    lines += [
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in dossier["evidence_interpretation"])
    lines += [
        "",
        "## Kritische Ledger-Kontexte",
        "",
    ]
    for item in dossier["zero_cost_lines"]:
        lines += [
            f"### Line {item['line_no']}",
            "",
            f"- Platform-Hinweis: `{item['platform_hint']}`",
            f"- Source Event: `{item['source_event_id']}`",
            f"- Lot Source Event: `{item['lot_source_event_id'] or 'empty_lot'}`",
            "",
        ]
        for row in item.get("ledger_context", []):
            lines.append(
                f"- `{row.get('timestamp', '')}` `{row.get('source', '')}` / `{row.get('event_type', '')}` / `{row.get('side', '')}` "
                f"delta `{row.get('delta', '')}` before `{row.get('balance_before', '')}` after `{row.get('balance_after', '')}` tx `{row.get('tx_id', '')}`"
            )
        lines.append("")
    lines += [
        "## Naechste saubere Belegziele",
        "",
        "- Fuer Line 106: Binance Erwerbskette vor `2022-01-05T15:36:46Z` pruefen, insbesondere 2021/Anfang-2022 Account-Statement/Trade-History/Convert/Pay/Earn-Kontext.",
        "- Fuer Lines 136 und 149: Pionex Bot-/Opening-Balance am `2022-01-19` oder interne Bot-Fill-Historie belegen.",
        "- Ohne Beleg keine steuerwirksame Zuflussfiktion importieren; wenn fachlich entschieden, dann explizit als nicht steuerwirksame Review-/Inventar-Normalisierung dokumentieren.",
        "",
        f"JSON: `{JSON_PATH.relative_to(ROOT)}`",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
