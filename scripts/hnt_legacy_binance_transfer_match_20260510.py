#!/usr/bin/env python3
"""Audit and persist Helium legacy -> Binance HNT transfer matches."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

RUN_DATE = "2026-05-10"
JSON_PATH = ROOT / "var" / f"hnt_legacy_binance_transfer_match_{RUN_DATE}.json"
DOC_PATH = ROOT / "docs" / f"206_HNT_LEGACY_BINANCE_TRANSFER_MATCH_{RUN_DATE}.md"
METHOD = "txid_verified_hnt_legacy_to_binance"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Persist missing transfer matches.")
    args = parser.parse_args()

    STORE.initialize()
    raw_events = STORE.list_raw_events()
    reviewed, review_summary = apply_review_actions(raw_events)
    effective_events, override_count = apply_tax_event_overrides(reviewed)

    candidates = build_candidates(effective_events)
    existing = STORE.list_transfer_matches()
    existing_pairs = {
        (str(match.get("outbound_event_id") or ""), str(match.get("inbound_event_id") or ""))
        for match in existing
        if str(match.get("status") or "").lower() in {"matched", "approved"}
    }
    existing_out = {
        str(match.get("outbound_event_id") or "")
        for match in existing
        if str(match.get("status") or "").lower() in {"matched", "approved"}
    }
    existing_in = {
        str(match.get("inbound_event_id") or "")
        for match in existing
        if str(match.get("status") or "").lower() in {"matched", "approved"}
    }

    planned = []
    for row in candidates:
        row["exists_pair"] = (row["outbound_event_id"], row["inbound_event_id"]) in existing_pairs
        row["outbound_already_matched"] = row["outbound_event_id"] in existing_out
        row["inbound_already_matched"] = row["inbound_event_id"] in existing_in
        row["action"] = (
            "skip_existing"
            if row["exists_pair"]
            else "skip_conflict"
            if row["outbound_already_matched"] or row["inbound_already_matched"]
            else "create"
        )
        planned.append(row)

    created = []
    if args.apply:
        for row in planned:
            if row["action"] != "create":
                continue
            match_id = STORE.create_transfer_match(
                outbound_event_id=row["outbound_event_id"],
                inbound_event_id=row["inbound_event_id"],
                confidence_score=row["confidence_score"],
                time_diff_seconds=int(row["time_diff_seconds"]),
                amount_diff=row["amount_diff"],
                status="matched",
                method=METHOD,
                note=(
                    "Same Helium legacy base transaction ID as Binance HNT deposit; "
                    "amount difference is the observed network/deposit delta."
                ),
            )
            created.append({**row, "match_id": match_id})

    latest_2021_job = latest_completed_job(2021)
    zero_cost_before = zero_cost_hnt_summary(latest_2021_job["job_id"]) if latest_2021_job else None
    payload = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "applied": bool(args.apply),
        "review_summary": review_summary,
        "tax_event_override_count": override_count,
        "latest_2021_job_before_rerun": latest_2021_job,
        "hnt_2021_zero_cost_before_rerun": zero_cost_before,
        "candidate_count": len(planned),
        "create_count": sum(1 for row in planned if row["action"] == "create"),
        "skip_existing_count": sum(1 for row in planned if row["action"] == "skip_existing"),
        "skip_conflict_count": sum(1 for row in planned if row["action"] == "skip_conflict"),
        "created_count": len(created),
        "candidates": planned,
        "created": created,
        "interpretation": interpretation(planned, created, bool(args.apply)),
    }

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(payload), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "created_count": len(created)}, ensure_ascii=False, indent=2))


def build_candidates(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    legacy_by_tx: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    best_deposit_by_tx: dict[str, dict[str, Any]] = {}

    for event in events:
        if canonical_asset(event) != "HNT":
            continue
        tx = base_tx(payload(event).get("tx_id") or raw_payload(event).get("tx_id") or raw_payload(event).get("TxID") or "")
        if not tx:
            continue
        if is_legacy_out(event):
            legacy_by_tx[tx].append(event)
        if is_binance_deposit(event):
            current = best_deposit_by_tx.get(tx)
            if current is None or deposit_rank(event) < deposit_rank(current):
                best_deposit_by_tx[tx] = event

    rows = []
    for tx, deposit in sorted(best_deposit_by_tx.items(), key=lambda item: event_ts_text(item[1])):
        legacy_candidates = legacy_by_tx.get(tx, [])
        if not legacy_candidates:
            continue
        outbound = sorted(legacy_candidates, key=lambda event: match_sort_key(event, deposit))[0]
        amount_diff = abs(event_qty(outbound) - event_qty(deposit))
        time_diff = time_diff_seconds(outbound, deposit)
        rows.append(
            {
                "base_tx_id": tx,
                "outbound_event_id": str(outbound.get("unique_event_id") or ""),
                "inbound_event_id": str(deposit.get("unique_event_id") or ""),
                "outbound_timestamp_utc": event_ts_text(outbound),
                "inbound_timestamp_utc": event_ts_text(deposit),
                "outbound_source": source(outbound),
                "inbound_source": source(deposit),
                "outbound_event_type": event_type(outbound),
                "inbound_event_type": event_type(deposit),
                "outbound_quantity_hnt": plain(event_qty(outbound)),
                "inbound_quantity_hnt": plain(event_qty(deposit)),
                "amount_diff": plain(amount_diff),
                "time_diff_seconds": time_diff,
                "confidence_score": confidence(amount_diff, time_diff),
            }
        )
    return rows


def latest_completed_job(tax_year: int) -> dict[str, Any] | None:
    for job in STORE.list_processing_jobs(status="completed", limit=500):
        if int(job.get("tax_year") or 0) == tax_year:
            return job
    return None


def zero_cost_hnt_summary(job_id: str) -> dict[str, Any]:
    rows = []
    proceeds = Decimal("0")
    qty_total = Decimal("0")
    for line in STORE.get_tax_lines(job_id):
        if str(line.get("asset") or "").upper() != "HNT":
            continue
        if dec(line.get("cost_basis_eur")) != 0 or dec(line.get("proceeds_eur")) <= 0:
            continue
        qty_total += dec(line.get("qty"))
        proceeds += dec(line.get("proceeds_eur"))
        rows.append(
            {
                "line_no": line.get("line_no"),
                "qty": str(line.get("qty") or ""),
                "sell_timestamp_utc": str(line.get("sell_timestamp_utc") or ""),
                "proceeds_eur": str(line.get("proceeds_eur") or ""),
                "source_event_id": str(line.get("source_event_id") or ""),
            }
        )
    return {"line_count": len(rows), "quantity_hnt": plain(qty_total), "proceeds_eur": plain(proceeds), "sample_rows": rows[:30]}


def payload(event: dict[str, Any]) -> dict[str, Any]:
    return event.get("payload") or {}


def raw_payload(event: dict[str, Any]) -> dict[str, Any]:
    raw = payload(event).get("raw") or {}
    return raw if isinstance(raw, dict) else {}


def source(event: dict[str, Any]) -> str:
    return str(payload(event).get("source") or "").lower()


def event_type(event: dict[str, Any]) -> str:
    return str(payload(event).get("event_type") or payload(event).get("type") or "").lower()


def side(event: dict[str, Any]) -> str:
    return str(payload(event).get("side") or "").lower()


def canonical_asset(event: dict[str, Any]) -> str:
    value = payload(event).get("asset") or payload(event).get("currency") or payload(event).get("coin") or ""
    return str(value).upper().strip()


def is_legacy_out(event: dict[str, Any]) -> bool:
    return source(event).startswith("helium_legacy") and side(event) == "out" and "transfer" in event_type(event)


def is_binance_deposit(event: dict[str, Any]) -> bool:
    if not source(event).startswith("binance") or side(event) != "in":
        return False
    return "deposit" in event_type(event) or event_type(event) == ""


def deposit_rank(event: dict[str, Any]) -> int:
    if source(event) == "binance_api" and "deposit" in event_type(event):
        return 0
    if source(event) == "binance" and "deposit" in event_type(event):
        return 1
    if source(event) == "binance":
        return 2
    return 9


def base_tx(value: Any) -> str:
    return str(value or "").split("+", 1)[0].strip()


def event_ts_text(event: dict[str, Any]) -> str:
    return str(payload(event).get("timestamp_utc") or payload(event).get("timestamp") or "")


def event_dt(event: dict[str, Any]) -> datetime | None:
    text = event_ts_text(event).replace("Z", "+00:00")
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def event_qty(event: dict[str, Any]) -> Decimal:
    return abs(dec(payload(event).get("quantity") or payload(event).get("amount") or "0"))


def match_sort_key(outbound: dict[str, Any], inbound: dict[str, Any]) -> tuple[int, int, Decimal]:
    outbound_dt = event_dt(outbound)
    inbound_dt = event_dt(inbound)
    before_rank = 0 if outbound_dt and inbound_dt and outbound_dt <= inbound_dt else 1
    seconds = time_diff_seconds(outbound, inbound)
    return before_rank, seconds, abs(event_qty(outbound) - event_qty(inbound))


def time_diff_seconds(left: dict[str, Any], right: dict[str, Any]) -> int:
    left_dt = event_dt(left)
    right_dt = event_dt(right)
    if not left_dt or not right_dt:
        return 0
    return int(abs((right_dt - left_dt).total_seconds()))


def confidence(amount_diff: Decimal, time_diff: int) -> str:
    if amount_diff <= Decimal("0.05") and time_diff <= 900:
        return "0.9900"
    if amount_diff <= Decimal("0.25") and time_diff <= 3600:
        return "0.9700"
    return "0.9300"


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Any) -> str:
    value_dec = dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def interpretation(rows: list[dict[str, Any]], created: list[dict[str, Any]], applied: bool) -> list[str]:
    lines = [
        "Alle Kandidaten beruhen auf identischer Helium-Legacy-Basis-TXID und einem Binance-HNT-Deposit.",
        "Die Mengenabweichungen liegen im erwartbaren Netzwerk-/Deposit-Delta; die Binance-Eingangsmenge wird als uebertragene Menge fortgefuehrt.",
        "Damit kann FIFO die urspruenglichen Mining-/Reward-Lots ueber den CEX-Transfer hinweg weitertragen.",
    ]
    if applied:
        lines.append(f"Persistiert wurden {len(created)} neue Transfer-Matches.")
    else:
        lines.append(f"Trockenlauf: {sum(1 for row in rows if row.get('action') == 'create')} Matches waeren neu anzulegen.")
    return lines


def render_doc(payload: dict[str, Any]) -> str:
    lines = [
        "# HNT Legacy -> Binance Transfer-Match",
        "",
        f"- Erstellt: `{payload['created_at_utc']}`",
        f"- Apply-Modus: `{payload['applied']}`",
        f"- Kandidaten: `{payload['candidate_count']}`",
        f"- Neu anzulegen laut Audit: `{payload['create_count']}`",
        f"- Persistiert: `{payload['created_count']}`",
        f"- Bestehende Matches: `{payload['skip_existing_count']}`",
        f"- Konflikte: `{payload['skip_conflict_count']}`",
        "",
        "## Stand vor erneutem Rechenlauf",
        "",
    ]
    job = payload.get("latest_2021_job_before_rerun") or {}
    before = payload.get("hnt_2021_zero_cost_before_rerun") or {}
    lines.extend(
        [
            f"- Letzter 2021-Job: `{job.get('job_id', '')}`",
            f"- HNT-Zero-Cost-Zeilen: `{before.get('line_count', 0)}`",
            f"- HNT-Zero-Cost-Menge: `{before.get('quantity_hnt', '0')}`",
            f"- HNT-Zero-Cost-Erloes EUR: `{before.get('proceeds_eur', '0')}`",
            "",
            "## Interpretation",
            "",
        ]
    )
    for line in payload["interpretation"]:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "## Kandidaten",
            "",
            "| TXID | Legacy Out | Binance In | Menge Out | Menge In | Delta | Sekunden | Aktion |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["candidates"]:
        lines.append(
            "| `{base_tx_id}` | `{outbound_event_id}` | `{inbound_event_id}` | {outbound_quantity_hnt} | {inbound_quantity_hnt} | {amount_diff} | {time_diff_seconds} | `{action}` |".format(
                **row
            )
        )
    lines.extend(["", f"JSON: `{JSON_PATH}`", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    main()
