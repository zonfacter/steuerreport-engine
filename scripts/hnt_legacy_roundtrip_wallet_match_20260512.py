#!/usr/bin/env python3
"""Audit and optionally persist a Fairspot-backed HNT roundtrip transfer match."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE

RUN_DATE = "2026-05-12"
OUT_JSON = ROOT / "var" / "hnt_legacy_roundtrip_wallet_match_2026-05-12.json"
OUT_MD = ROOT / "docs" / "237_HNT_LEGACY_ROUNDTRIP_WALLET_MATCH_2026-05-12.md"
METHOD = "fairspot_roundtrip_14o7_self_custody"

MAIN_WALLET = "133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j"
ROUNDTRIP_WALLET = "14o7quYAMQZFE8UCNPN89yK9fwtxMW8wvht8MQZkSiSgizeqSme"
OUTBOUND_EVENT_ID = "7946d3580ddf0a4d5c27af9a4a961cc2361d09e52fd5814d02c23c5ac77acdb5"
INBOUND_EVENT_ID = "67cbdab2e2f2a75cdb15d83eefc5f01baec731e2ddc47a670e79fd654773d06b"

EXPECTED_OUT_TX = "Kk7ZTefj1fQOZ-1rPwt4aIOXpTmckgt8JA28IJ6XF_8"
EXPECTED_IN_TX = "tLOGE2C0v-CGYSJfvKU6KvI7oQq4OALrz3rh6SbC8Qs"
EXPECTED_OUT_QTY = Decimal("100.03130590339893")
EXPECTED_TRANSFER_QTY = Decimal("100")
EXPECTED_IN_QTY = Decimal("99.75")
EXPECTED_AMOUNT_DIFF = Decimal("0.28130590339893")
EXPECTED_SECONDS = 1289051


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Any) -> str:
    value_dec = dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def payload(event: dict[str, Any] | None) -> dict[str, Any]:
    if not event:
        return {}
    loaded = event.get("payload") or {}
    return loaded if isinstance(loaded, dict) else {}


def base_tx(tx_id: str) -> str:
    return str(tx_id or "").split("+", 1)[0].strip()


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
        if dec(line.get("cost_basis_eur")) != 0 or dec(line.get("proceeds_eur")) < Decimal("50"):
            continue
        qty_total += dec(line.get("qty"))
        proceeds += dec(line.get("proceeds_eur"))
        rows.append(
            {
                "line_no": str(line.get("line_no") or ""),
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
        "rows": rows,
    }


def event_summary(event: dict[str, Any] | None) -> dict[str, str]:
    data = payload(event)
    return {
        "event_id": str((event or {}).get("unique_event_id") or ""),
        "source_file_id": str((event or {}).get("source_file_id") or ""),
        "row_index": str((event or {}).get("row_index") or ""),
        "timestamp_utc": str(data.get("timestamp_utc") or ""),
        "source": str(data.get("source") or ""),
        "event_type": str(data.get("event_type") or ""),
        "side": str(data.get("side") or ""),
        "asset": str(data.get("asset") or ""),
        "quantity": str(data.get("quantity") or ""),
        "fee": str(data.get("fee") or ""),
        "value_usd": str(data.get("value_usd") or ""),
        "tx_id": str(data.get("tx_id") or ""),
        "from_wallet": str(data.get("from_wallet") or ""),
        "to_wallet": str(data.get("to_wallet") or ""),
        "counterparty_wallet": str(data.get("counterparty_wallet") or ""),
    }


def validate_candidate(outbound: dict[str, Any] | None, inbound: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    out = payload(outbound)
    inc = payload(inbound)
    if base_tx(str(out.get("tx_id") or "")) != EXPECTED_OUT_TX:
        errors.append("outbound_tx_mismatch")
    if base_tx(str(inc.get("tx_id") or "")) != EXPECTED_IN_TX:
        errors.append("inbound_tx_mismatch")
    if str(out.get("from_wallet") or "") != MAIN_WALLET or str(out.get("to_wallet") or "") != ROUNDTRIP_WALLET:
        errors.append("outbound_wallets_mismatch")
    if str(inc.get("from_wallet") or "") != ROUNDTRIP_WALLET or str(inc.get("to_wallet") or "") != MAIN_WALLET:
        errors.append("inbound_wallets_mismatch")
    if dec(out.get("quantity")) != EXPECTED_OUT_QTY:
        errors.append("outbound_quantity_mismatch")
    if dec(inc.get("quantity")) != EXPECTED_IN_QTY:
        errors.append("inbound_quantity_mismatch")
    return errors


def existing_match_state() -> dict[str, Any]:
    matches = STORE.list_transfer_matches()
    pair_matches = [
        match
        for match in matches
        if str(match.get("outbound_event_id") or "") == OUTBOUND_EVENT_ID
        and str(match.get("inbound_event_id") or "") == INBOUND_EVENT_ID
    ]
    outbound_conflicts = [
        match
        for match in matches
        if str(match.get("outbound_event_id") or "") == OUTBOUND_EVENT_ID
        and str(match.get("inbound_event_id") or "") != INBOUND_EVENT_ID
        and str(match.get("status") or "").lower() in {"matched", "approved"}
    ]
    inbound_conflicts = [
        match
        for match in matches
        if str(match.get("inbound_event_id") or "") == INBOUND_EVENT_ID
        and str(match.get("outbound_event_id") or "") != OUTBOUND_EVENT_ID
        and str(match.get("status") or "").lower() in {"matched", "approved"}
    ]
    return {
        "pair_matches": pair_matches,
        "outbound_conflicts": outbound_conflicts,
        "inbound_conflicts": inbound_conflicts,
    }


def build_report(apply: bool) -> dict[str, Any]:
    STORE.initialize()
    outbound = STORE.get_raw_event(OUTBOUND_EVENT_ID)
    inbound = STORE.get_raw_event(INBOUND_EVENT_ID)
    validation_errors = validate_candidate(outbound, inbound)
    existing = existing_match_state()
    latest_2021 = latest_completed_job(2021)
    before = zero_cost_hnt_summary((latest_2021 or {}).get("job_id"))
    action = "create"
    if validation_errors:
        action = "blocked_validation_error"
    elif existing["pair_matches"]:
        action = "skip_existing"
    elif existing["outbound_conflicts"] or existing["inbound_conflicts"]:
        action = "blocked_conflict"

    created: dict[str, Any] | None = None
    if apply and action == "create":
        match_id = STORE.create_transfer_match(
            outbound_event_id=OUTBOUND_EVENT_ID,
            inbound_event_id=INBOUND_EVENT_ID,
            confidence_score="0.970",
            time_diff_seconds=EXPECTED_SECONDS,
            amount_diff=plain(EXPECTED_AMOUNT_DIFF),
            status="matched",
            method=METHOD,
            note=(
                "Fairspot-backed roundtrip: 100 HNT sent from main wallet to 14o7... "
                "and 99.75 HNT returned to main wallet; preserves lot continuity for returned HNT only."
            ),
        )
        created = {"match_id": match_id}
        action = "created"

    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "applied": apply,
        "method": METHOD,
        "action": action,
        "created": created,
        "wallets": {"main_wallet": MAIN_WALLET, "roundtrip_wallet": ROUNDTRIP_WALLET},
        "amounts": {
            "fairspot_sent_hnt": plain(EXPECTED_TRANSFER_QTY),
            "project_out_event_quantity_hnt_including_fee": plain(EXPECTED_OUT_QTY),
            "returned_hnt": plain(EXPECTED_IN_QTY),
            "unreturned_hnt": plain(EXPECTED_TRANSFER_QTY - EXPECTED_IN_QTY),
            "network_fee_hnt": plain(EXPECTED_OUT_QTY - EXPECTED_TRANSFER_QTY),
            "out_event_minus_return_hnt": plain(EXPECTED_AMOUNT_DIFF),
        },
        "timing": {"time_diff_seconds": EXPECTED_SECONDS},
        "candidate": {"outbound": event_summary(outbound), "inbound": event_summary(inbound)},
        "validation_errors": validation_errors,
        "existing": existing,
        "zero_cost_before": before,
        "interpretation": [
            "Der Match erzeugt keine neuen Anschaffungskosten und verwendet keine Fairspot-USD-Werte als Preisanker.",
            "Er markiert nur den belegten Rueckfluss von 99.75 HNT als Lot-Continuity aus dem vorherigen 100-HNT-Abgang.",
            "Die nicht zurueckgekehrten 0.25 HNT und die Netzwerkfee werden nicht als Rueckfluss behandelt.",
        ],
    }


def render_doc(report: dict[str, Any]) -> str:
    amounts = report["amounts"]
    before = report.get("zero_cost_before") or {}
    lines = [
        "# HNT Legacy Roundtrip Wallet Match",
        "",
        f"Stand: {RUN_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Applied: `{report['applied']}`",
        f"- Aktion: `{report['action']}`",
        f"- Methode: `{report['method']}`",
        f"- Persistierter Match: `{(report.get('created') or {}).get('match_id', '')}`",
        "",
        "## Menge",
        "",
        f"- Fairspot-Abgang an `14o7...`: `{amounts['fairspot_sent_hnt']} HNT`",
        f"- Rueckfluss von `14o7...`: `{amounts['returned_hnt']} HNT`",
        f"- Nicht zurueckgekehrte Transferdifferenz: `{amounts['unreturned_hnt']} HNT`",
        f"- Netzwerkfee im Projekt-Out-Event: `{amounts['network_fee_hnt']} HNT`",
        f"- Out-Event minus Rueckfluss: `{amounts['out_event_minus_return_hnt']} HNT`",
        "",
        "## Events",
        "",
        "| Richtung | Zeit | Event | Tx | Menge HNT | Fee HNT | Von | An |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for direction, item in (("Out", report["candidate"]["outbound"]), ("In", report["candidate"]["inbound"])):
        lines.append(
            "| {direction} | `{timestamp_utc}` | `{event_id}` | `{tx_id}` | {quantity} | {fee} | `{from_wallet}` | `{to_wallet}` |".format(
                direction=direction,
                **item,
            )
        )
    lines.extend(
        [
            "",
            "## Zero-Cost HNT vor Apply",
            "",
            f"- 2021 HNT-Zeilen >= 50 EUR: `{before.get('line_count', 0)}`",
            f"- Menge: `{before.get('quantity_hnt', '0')} HNT`",
            f"- Erloes: `{before.get('proceeds_eur', '0')} EUR`",
            "",
            "## Einordnung",
            "",
        ]
    )
    for item in report["interpretation"]:
        lines.append(f"- {item}")
    if report["validation_errors"]:
        lines.extend(["", "## Validierungsfehler", ""])
        lines.extend(f"- `{item}`" for item in report["validation_errors"])
    lines.extend(["", f"JSON: `{OUT_JSON.relative_to(ROOT)}`", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Persist the roundtrip transfer match.")
    args = parser.parse_args()

    report = build_report(apply=args.apply)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    OUT_MD.write_text(render_doc(report), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "doc": str(OUT_MD), "action": report["action"]}, indent=2))
    return 0 if report["action"] in {"create", "created", "skip_existing"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
