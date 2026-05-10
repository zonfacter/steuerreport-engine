#!/usr/bin/env python3
"""Evaluate Blockpit Binance BTC source-chain rows before importing them."""

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

from chronological_balance_break_audit import (  # noqa: E402
    _effective_events,
    _load_ignored_tokens,
    _load_token_aliases,
    _movement_sort_key,
    _movements,
)

from tax_engine.ingestion.store import STORE  # noqa: E402

CREATED_DATE = "2026-05-09"
OUTPUT_JSON = ROOT / "var" / f"binance_btc_source_chain_candidate_audit_{CREATED_DATE}.json"
OUTPUT_DOC = ROOT / "docs" / f"152_BINANCE_BTC_SOURCE_CHAIN_CANDIDATE_AUDIT_{CREATED_DATE}.md"
SECOND_SOL_BUY_TS = "2023-06-10T16:45:04+00:00"
BTC_BREAK_TS = "2023-05-04T04:24:52+00:00"


def main() -> None:
    active_rows = load_active_movements()
    active_balances = balances_before(active_rows, SECOND_SOL_BUY_TS)
    candidates = btc_reference_candidates(active_rows)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": {
            "source": "Blockpit Binance API reference rows",
            "cutoff_before": SECOND_SOL_BUY_TS,
            "purpose": "BTC source-chain check after SOL 2023 reconstruction",
        },
        "active_balances_before_second_sol_buy": {asset: plain(value) for asset, value in sorted(active_balances.items())},
        "candidate_count": len(candidates),
        "candidates": candidates,
        "summary": summarize(candidates),
        "assessment": assessment(candidates),
    }
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_DOC.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(OUTPUT_DOC), "summary": audit["summary"]}, ensure_ascii=False, indent=2))


def load_active_movements() -> list[dict[str, Any]]:
    token_aliases = _load_token_aliases()
    ignored_mints = set(_load_ignored_tokens().keys())
    rows = [
        movement
        for event in _effective_events()
        for movement in _movements(event, token_aliases=token_aliases, ignored_mints=ignored_mints)
    ]
    rows.sort(key=_movement_sort_key)
    return rows


def balances_before(movements: list[dict[str, Any]], timestamp: str) -> dict[str, Decimal]:
    balances: dict[str, Decimal] = defaultdict(Decimal)
    for row in movements:
        if str(row.get("timestamp") or "") >= timestamp:
            break
        balances[str(row.get("asset") or "")] += dec(row.get("delta"))
    return balances


def btc_reference_candidates(active_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in STORE.list_raw_events():
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        if str(payload.get("source") or "").lower() != "blockpit":
            continue
        if "binance" not in str(raw.get("Integration Name") or raw.get("Source Name") or "").lower():
            continue
        if str(raw.get("Label") or "").lower() != "trade":
            continue
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if not ts or ts >= SECOND_SOL_BUY_TS:
            continue
        incoming_asset = str(raw.get("Incoming Asset") or "").upper().strip()
        outgoing_asset = str(raw.get("Outgoing Asset") or "").upper().strip()
        if "BTC" not in {incoming_asset, outgoing_asset}:
            continue
        trx_id = str(raw.get("Trx. ID (optional)") or payload.get("tx_id") or "")
        if not trx_id:
            trx_id = str(payload.get("tx_id") or event.get("unique_event_id") or "")
        rows.append(
            {
                "event_id": str(event.get("unique_event_id") or ""),
                "timestamp_utc": ts,
                "trx_id": trx_id,
                "comment": str(raw.get("Comment (optional)") or ""),
                "incoming_asset": incoming_asset,
                "incoming_amount": plain(dec(raw.get("Incoming Amount"))),
                "outgoing_asset": outgoing_asset,
                "outgoing_amount": plain(dec(raw.get("Outgoing Amount"))),
                "fee_asset": str(raw.get("Fee Asset (optional)") or "").upper().strip(),
                "fee_amount": plain(dec(raw.get("Fee Amount (optional)"))),
            }
        )
    grouped: dict[str, dict[str, Any]] = {}
    for row in sorted(rows, key=lambda item: (item["timestamp_utc"], item["trx_id"], item["event_id"])):
        key = row["trx_id"]
        grouped.setdefault(key, row)
    return [evaluate_candidate(row, active_rows) for row in grouped.values()]


def evaluate_candidate(row: dict[str, Any], active_rows: list[dict[str, Any]]) -> dict[str, Any]:
    movements = candidate_movements(row)
    before = balances_before(active_rows, str(row["timestamp_utc"]))
    after_impacts = []
    blocking = []
    for movement in movements:
        asset = movement["asset"]
        before_value = before.get(asset, Decimal("0"))
        after_value = before_value + movement["delta"]
        after_impacts.append(
            {
                "asset": asset,
                "delta": plain(movement["delta"]),
                "active_before": plain(before_value),
                "projected_after": plain(after_value),
                "side": movement["side"],
            }
        )
        if after_value < 0:
            blocking.append(
                {
                    "asset": asset,
                    "shortfall": plain(abs(after_value)),
                    "active_before": plain(before_value),
                    "required_delta": plain(abs(movement["delta"])),
                }
            )
    btc_delta = sum((item["delta"] for item in movements if item["asset"] == "BTC"), Decimal("0"))
    status = "safe_candidate" if not blocking else "blocked_by_counterasset_undercoverage"
    if row["timestamp_utc"] >= BTC_BREAK_TS and btc_delta > 0:
        status = "late_candidate_after_first_btc_break" if not blocking else status
    return {
        **row,
        "candidate_movements": [
            {"asset": item["asset"], "delta": plain(item["delta"]), "side": item["side"]} for item in movements
        ],
        "net_btc_delta": plain(btc_delta),
        "projected_impacts_at_timestamp": after_impacts,
        "blocking_undercoverage": blocking,
        "status": status,
        "import_recommendation": recommendation(status, row, btc_delta),
    }


def candidate_movements(row: dict[str, Any]) -> list[dict[str, Any]]:
    incoming_asset = str(row["incoming_asset"])
    outgoing_asset = str(row["outgoing_asset"])
    incoming_amount = dec(row["incoming_amount"])
    outgoing_amount = dec(row["outgoing_amount"])
    fee_asset = str(row.get("fee_asset") or "")
    fee_amount = dec(row.get("fee_amount"))
    movements = [
        {"asset": incoming_asset, "delta": abs(incoming_amount), "side": "incoming"},
        {"asset": outgoing_asset, "delta": -abs(outgoing_amount), "side": "outgoing"},
    ]
    if fee_asset and fee_amount:
        movements.append({"asset": fee_asset, "delta": -abs(fee_amount), "side": "fee"})
    return [row for row in movements if row["asset"] and row["delta"]]


def recommendation(status: str, row: dict[str, Any], btc_delta: Decimal) -> str:
    if status == "safe_candidate" and btc_delta > 0:
        return "can_import_as_narrow_btc_source_reconstruction"
    if status == "late_candidate_after_first_btc_break" and btc_delta > 0:
        return "can_import_later_only_after_pre_break_source_is_resolved"
    if status == "blocked_by_counterasset_undercoverage":
        return "do_not_import_until_counterasset_source_is_found_or_review_adjustment_is_approved"
    return "reference_only"


def summarize(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = defaultdict(int)
    importable_btc = Decimal("0")
    blocked_btc = Decimal("0")
    for row in candidates:
        status_counts[str(row["status"])] += 1
        btc = dec(row.get("net_btc_delta"))
        if row["import_recommendation"].startswith("can_import"):
            importable_btc += btc
        if str(row["status"]).startswith("blocked"):
            blocked_btc += btc
    return {
        "status_counts": dict(sorted(status_counts.items())),
        "importable_positive_btc_delta": plain(importable_btc),
        "blocked_positive_btc_delta": plain(blocked_btc),
    }


def assessment(candidates: list[dict[str, Any]]) -> list[str]:
    safe = [row for row in candidates if row["import_recommendation"] == "can_import_as_narrow_btc_source_reconstruction"]
    blocked = [row for row in candidates if row["status"] == "blocked_by_counterasset_undercoverage"]
    return [
        f"{len(safe)} BTC-Quelle(n) sind aus aktivem Bestand am jeweiligen Zeitpunkt plausibel importierbar.",
        f"{len(blocked)} BTC-Quelle(n) sind als Referenz belegt, wuerden aber neue Gegenasset-Unterdeckungen erzeugen.",
        "Damit darf die BTC-Luecke nicht pauschal mit allen Blockpit-Referenzen geschlossen werden.",
        "Der erste sichere Schritt ist ein enges Importpaket nur fuer die plausiblen USDT/VET/WIN/DOGE/BTC-Quellen, sofern die Gegenassets am Zeitpunkt gedeckt bleiben.",
    ]


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Binance BTC Source Chain Candidate Audit - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Kandidaten: `{audit['candidate_count']}`",
        f"- Status: `{audit['summary']['status_counts']}`",
        f"- Importierbarer positiver BTC-Delta: `{audit['summary']['importable_positive_btc_delta']} BTC`",
        f"- Blockierter positiver BTC-Delta: `{audit['summary']['blocked_positive_btc_delta']} BTC`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {item}" for item in audit["assessment"])
    lines += ["", "## Kandidaten", ""]
    for row in audit["candidates"]:
        lines.append(
            f"- `{row['timestamp_utc']}` tx `{row['trx_id']}` `{row['incoming_amount']} {row['incoming_asset']}` "
            f"<- `{row['outgoing_amount']} {row['outgoing_asset']}` fee `{row['fee_amount']} {row['fee_asset']}` "
            f"net BTC `{row['net_btc_delta']}` status `{row['status']}` recommendation `{row['import_recommendation']}`"
        )
        for block in row["blocking_undercoverage"]:
            lines.append(
                f"  - blockiert `{block['asset']}`: aktiv `{block['active_before']}`, benoetigt `{block['required_delta']}`, Luecke `{block['shortfall']}`"
            )
    lines += [
        "",
        "## Konsequenz",
        "",
        "- Import nur fuer Kandidaten mit `can_import_as_narrow_btc_source_reconstruction`; blockierte Kandidaten bleiben Nachweis/Recherchepunkt.",
        "- BUSD bleibt separat zu klaeren, weil der grosse `BUSD -> BTC`-Trade ohne BUSD-Quelle die Bilanz verfaelschen wuerde.",
        "",
    ]
    return "\n".join(lines)


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


if __name__ == "__main__":
    main()
