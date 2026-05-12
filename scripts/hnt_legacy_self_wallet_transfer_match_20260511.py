#!/usr/bin/env python3
"""Audit and optionally persist HNT self-wallet transfer matches."""

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

RUN_DATE = "2026-05-11"
JSON_PATH = ROOT / "var" / f"hnt_legacy_self_wallet_transfer_match_{RUN_DATE}.json"
DOC_PATH = ROOT / "docs" / f"231_HNT_LEGACY_SELF_WALLET_TRANSFER_MATCH_{RUN_DATE}.md"
METHOD = "txid_verified_hnt_legacy_self_wallet"
MAIN_WALLET = "133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j"
STAKING_WALLET = "14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA"
KNOWN_SELF_WALLETS = {MAIN_WALLET, STAKING_WALLET}


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Any) -> str:
    value_dec = dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def payload(event: dict[str, Any]) -> dict[str, Any]:
    loaded = event.get("payload") or {}
    return loaded if isinstance(loaded, dict) else {}


def source(event: dict[str, Any]) -> str:
    return str(payload(event).get("source") or "").lower().strip()


def side(event: dict[str, Any]) -> str:
    return str(payload(event).get("side") or "").lower().strip()


def event_type(event: dict[str, Any]) -> str:
    return str(payload(event).get("event_type") or "").lower().strip()


def asset(event: dict[str, Any]) -> str:
    return str(payload(event).get("asset") or "").upper().strip()


def tx_id(event: dict[str, Any]) -> str:
    return str(payload(event).get("tx_id") or "").split("+", 1)[0].strip()


def qty(event: dict[str, Any]) -> Decimal:
    return dec(payload(event).get("quantity"))


def timestamp(event: dict[str, Any]) -> str:
    return str(payload(event).get("timestamp_utc") or payload(event).get("timestamp") or "")


def wallet_set(event: dict[str, Any]) -> set[str]:
    data = payload(event)
    output = {
        str(data.get("wallet_address") or "").strip(),
        str(data.get("from_wallet") or "").strip(),
        str(data.get("to_wallet") or "").strip(),
        str(data.get("counterparty_wallet") or "").strip(),
    }
    return {item for item in output if item}


def is_known_self_wallet_event(event: dict[str, Any]) -> bool:
    if asset(event) != "HNT":
        return False
    if "transfer" not in event_type(event):
        return False
    if not source(event).startswith("helium_legacy"):
        return False
    if not tx_id(event):
        return False
    return bool(wallet_set(event) & KNOWN_SELF_WALLETS)


def time_diff_seconds(outbound: dict[str, Any], inbound: dict[str, Any]) -> int:
    left = datetime.fromisoformat(timestamp(outbound).replace("Z", "+00:00"))
    right = datetime.fromisoformat(timestamp(inbound).replace("Z", "+00:00"))
    return int(abs((right - left).total_seconds()))


def confidence(amount_diff: Decimal, seconds: int) -> str:
    if amount_diff <= Decimal("0.05") and seconds <= 60:
        return "0.995"
    if amount_diff <= Decimal("0.25") and seconds <= 900:
        return "0.980"
    return "0.900"


def build_candidates(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        if is_known_self_wallet_event(event):
            grouped[tx_id(event)].append(event)

    candidates: list[dict[str, Any]] = []
    for base_tx, group in sorted(grouped.items(), key=lambda item: min(timestamp(event) for event in item[1])):
        outbound_events = [event for event in group if side(event) == "out"]
        inbound_events = [event for event in group if side(event) == "in"]
        if not outbound_events or not inbound_events:
            continue
        for inbound in inbound_events:
            outbound = sorted(outbound_events, key=lambda event: (abs(qty(event) - qty(inbound)), timestamp(event)))[0]
            amount_diff = abs(qty(outbound) - qty(inbound))
            seconds = time_diff_seconds(outbound, inbound)
            out_wallets = wallet_set(outbound)
            in_wallets = wallet_set(inbound)
            if not (out_wallets & KNOWN_SELF_WALLETS and in_wallets & KNOWN_SELF_WALLETS):
                continue
            candidates.append(
                {
                    "base_tx_id": base_tx,
                    "outbound_event_id": str(outbound.get("unique_event_id") or ""),
                    "inbound_event_id": str(inbound.get("unique_event_id") or ""),
                    "outbound_timestamp_utc": timestamp(outbound),
                    "inbound_timestamp_utc": timestamp(inbound),
                    "outbound_source": source(outbound),
                    "inbound_source": source(inbound),
                    "outbound_quantity_hnt": plain(qty(outbound)),
                    "inbound_quantity_hnt": plain(qty(inbound)),
                    "amount_diff": plain(amount_diff),
                    "time_diff_seconds": seconds,
                    "confidence_score": confidence(amount_diff, seconds),
                    "outbound_wallets": sorted(out_wallets),
                    "inbound_wallets": sorted(in_wallets),
                }
            )
    return candidates


def latest_completed_job(tax_year: int) -> dict[str, Any] | None:
    for job in STORE.list_processing_jobs(status="completed", limit=1000):
        if int(job.get("tax_year") or 0) == tax_year:
            return job
    return None


def zero_cost_hnt_summary(job_id: str | None) -> dict[str, Any] | None:
    if not job_id:
        return None
    rows = []
    qty_total = Decimal("0")
    proceeds = Decimal("0")
    for line in STORE.get_tax_lines(job_id):
        if str(line.get("asset") or "").upper() != "HNT":
            continue
        if dec(line.get("cost_basis_eur")) != 0 or dec(line.get("proceeds_eur")) <= 0:
            continue
        qty_total += dec(line.get("qty"))
        proceeds += dec(line.get("proceeds_eur"))
        rows.append(
            {
                "tax_year": line.get("tax_year"),
                "line_no": line.get("line_no"),
                "qty": str(line.get("qty") or ""),
                "sell_timestamp_utc": str(line.get("sell_timestamp_utc") or ""),
                "proceeds_eur": str(line.get("proceeds_eur") or ""),
                "source_event_id": str(line.get("source_event_id") or ""),
                "lot_source_event_id": str(line.get("lot_source_event_id") or ""),
            }
        )
    return {
        "line_count": len(rows),
        "quantity_hnt": plain(qty_total),
        "proceeds_eur": plain(proceeds),
        "sample_rows": rows[:30],
    }


def render_doc(report: dict[str, Any]) -> str:
    before_2021 = report["zero_cost_before"].get("2021") or {}
    before_2022 = report["zero_cost_before"].get("2022") or {}
    lines = [
        "# HNT Legacy Self-Wallet Transfer Match",
        "",
        f"Stand: {RUN_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Applied: `{report['applied']}`",
        f"- Kandidaten: `{report['candidate_count']}`",
        f"- Neu zu erstellen: `{report['create_count']}`",
        f"- Bereits vorhanden: `{report['skip_existing_count']}`",
        f"- Konflikte: `{report['skip_conflict_count']}`",
        f"- Erstellt: `{report['created_count']}`",
        "",
        "## Scope",
        "",
        f"- Haupt-Wallet: `{MAIN_WALLET}`",
        f"- Staking-Wallet: `{STAKING_WALLET}`",
        "- Gematcht werden nur HNT-Legacy-Transfers mit gleicher Helium-Transaktions-ID zwischen diesen bekannten eigenen Wallets.",
        "- Die Fairspot-Counterparty `14aDLshY...` wird hier bewusst nicht gematcht, weil die Rueckgabe mehrteilig ist und steuerlich/fachlich separat entschieden werden muss.",
        "",
        "## Kandidaten",
        "",
        "| Zeitpunkt | Tx | Out HNT | In HNT | Delta | Aktion | Match |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in report["candidates"]:
        lines.append(
            f"| `{row['outbound_timestamp_utc']}` | `{row['base_tx_id']}` | "
            f"{row['outbound_quantity_hnt']} | {row['inbound_quantity_hnt']} | {row['amount_diff']} | "
            f"`{row['action']}` | `{row.get('match_id', '')}` |"
        )

    lines.extend(
        [
            "",
            "## Zero-Cost HNT vor Apply",
            "",
            (
                f"- 2021: `{before_2021.get('line_count', 0)}` HNT-Zeilen, "
                f"`{before_2021.get('quantity_hnt', '0')} HNT`, "
                f"Erloes `{before_2021.get('proceeds_eur', '0')} EUR`."
            ),
            (
                f"- 2022: `{before_2022.get('line_count', 0)}` HNT-Zeilen, "
                f"`{before_2022.get('quantity_hnt', '0')} HNT`, "
                f"Erloes `{before_2022.get('proceeds_eur', '0')} EUR`."
            ),
            "",
            "## Bewertung",
            "",
            "- Diese Matches sind technische Continuity-Belege fuer eigene Wallets und erzeugen selbst keine neuen Anschaffungskosten.",
            "- Erwarteter Effekt: spaetere Inbound-Events der Staking-Wallet koennen die vorherigen FIFO-Lots aus der Haupt-Wallet weitertragen.",
            "- Nicht abgedeckt: `14e...` <-> `14a...` als Staking-/Custody-/Pool-Rueckgabe.",
            "",
            f"JSON: `{JSON_PATH.relative_to(ROOT)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Persist missing self-wallet transfer matches.")
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

    planned: list[dict[str, Any]] = []
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

    zero_cost_before = {
        str(year): zero_cost_hnt_summary((latest_completed_job(year) or {}).get("job_id"))
        for year in (2021, 2022)
    }

    created: list[dict[str, Any]] = []
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
                    "Same Helium legacy transaction ID between known self-wallets "
                    "133... and 14e...; preserves HNT lot continuity."
                ),
            )
            row["match_id"] = match_id
            created.append(row)

    report = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "applied": bool(args.apply),
        "review_summary": review_summary,
        "tax_event_override_count": override_count,
        "candidate_count": len(planned),
        "create_count": sum(1 for row in planned if row["action"] == "create"),
        "skip_existing_count": sum(1 for row in planned if row["action"] == "skip_existing"),
        "skip_conflict_count": sum(1 for row in planned if row["action"] == "skip_conflict"),
        "created_count": len(created),
        "zero_cost_before": zero_cost_before,
        "candidates": planned,
        "created": created,
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    DOC_PATH.write_text(render_doc(report), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "created_count": len(created)}, indent=2))


if __name__ == "__main__":
    main()
