#!/usr/bin/env python3
"""Audit and optionally persist Binance -> Pionex USDT transfer matches."""

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
OUT_JSON = ROOT / "var" / "usdt_binance_pionex_transfer_match_2026-05-12.json"
OUT_MD = ROOT / "docs" / "240_USDT_BINANCE_PIONEX_TRANSFER_MATCH_2026-05-12.md"
METHOD = "txid_verified_binance_pionex_usdt_trc20"

TRANSFERS = (
    {
        "label": "2021-12-25 Binance -> Pionex 200 USDT",
        "outbound_event_id": "64e981e7438b47954fa93df3832e3ce00e00bcc8349c2a431bd3b110151e3531",
        "inbound_event_id": "b35419d6564b5d54785849cd46c9b2dd0c897ece7226aedbbab32b405f725b11",
        "tx_id": "b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182",
        "quantity": Decimal("200"),
        "time_diff_seconds": 204,
        "tronscan_url": (
            "https://tronscan.org/#/transaction/"
            "b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182"
        ),
    },
    {
        "label": "2022-01-19 Binance -> Pionex 1245.38419 USDT",
        "outbound_event_id": "3450aa41e7b74c69acf27e9104f44cb956c9847870d864a24e988ff3a9b446e8",
        "inbound_event_id": "59feec35093a516eb72450330cdcaefed4a779b175fca223fc53d99f125ed18a",
        "tx_id": "b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa",
        "quantity": Decimal("1245.38419"),
        "time_diff_seconds": 201,
        "tronscan_url": (
            "https://tronscan.org/#/transaction/"
            "b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa"
        ),
    },
)


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


def raw_payload(event: dict[str, Any] | None) -> dict[str, Any]:
    data = payload(event)
    loaded = data.get("raw_row") or {}
    return loaded if isinstance(loaded, dict) else {}


def event_summary(event: dict[str, Any] | None) -> dict[str, str]:
    data = payload(event)
    raw = raw_payload(event)
    return {
        "event_id": str((event or {}).get("unique_event_id") or ""),
        "row_index": str((event or {}).get("row_index") if event else ""),
        "timestamp_utc": str(data.get("timestamp_utc") or ""),
        "source": str(data.get("source") or ""),
        "event_type": str(data.get("event_type") or ""),
        "side": str(data.get("side") or ""),
        "asset": str(data.get("asset") or ""),
        "quantity": str(data.get("quantity") or ""),
        "tx_id": str(data.get("tx_id") or ""),
        "network": str(raw.get("network") or ""),
        "address": str(raw.get("address") or ""),
        "raw_from": str(raw.get("info") or ""),
        "raw_to": str(raw.get("address") or ""),
        "raw_date": str(raw.get("date(UTC+0)") or raw.get("applyTime") or ""),
        "raw_complete_time": str(raw.get("completeTime") or ""),
        "raw_fee": str(raw.get("transactionFee") or raw.get("fee") or ""),
    }


def event_dt(event: dict[str, Any] | None) -> datetime | None:
    ts = str(payload(event).get("timestamp_utc") or "")
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def validate_transfer(row: dict[str, Any], outbound: dict[str, Any] | None, inbound: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    out = payload(outbound)
    inc = payload(inbound)
    if not outbound:
        errors.append("missing_outbound_event")
    if not inbound:
        errors.append("missing_inbound_event")
    if str(out.get("source") or "") != "binance_api" or str(out.get("event_type") or "") != "withdrawal":
        errors.append("outbound_not_binance_withdrawal")
    if str(inc.get("source") or "") != "pionex" or str(inc.get("event_type") or "") != "deposit":
        errors.append("inbound_not_pionex_deposit")
    if str(out.get("asset") or "").upper() != "USDT" or str(inc.get("asset") or "").upper() != "USDT":
        errors.append("asset_not_usdt")
    if str(out.get("tx_id") or "") != row["tx_id"] or str(inc.get("tx_id") or "") != row["tx_id"]:
        errors.append("tx_id_mismatch")
    if dec(out.get("quantity")) != row["quantity"] or dec(inc.get("quantity")) != row["quantity"]:
        errors.append("quantity_mismatch")
    out_dt = event_dt(outbound)
    in_dt = event_dt(inbound)
    if not out_dt or not in_dt:
        errors.append("missing_timestamp")
    elif out_dt > in_dt:
        errors.append("outbound_after_inbound")
    else:
        seconds = int((in_dt - out_dt).total_seconds())
        if seconds != row["time_diff_seconds"]:
            errors.append(f"time_diff_mismatch:{seconds}")
    return errors


def existing_state() -> dict[str, Any]:
    matches = STORE.list_transfer_matches()
    active = [match for match in matches if str(match.get("status") or "").lower() in {"matched", "approved"}]
    return {
        "pairs": {
            (str(match.get("outbound_event_id") or ""), str(match.get("inbound_event_id") or ""))
            for match in active
        },
        "outbound_ids": {str(match.get("outbound_event_id") or "") for match in active},
        "inbound_ids": {str(match.get("inbound_event_id") or "") for match in active},
    }


def build_report(apply: bool) -> dict[str, Any]:
    STORE.initialize()
    existing = existing_state()
    candidates = []
    created = []
    for row in TRANSFERS:
        outbound = STORE.get_raw_event(row["outbound_event_id"])
        inbound = STORE.get_raw_event(row["inbound_event_id"])
        validation_errors = validate_transfer(row, outbound, inbound)
        pair = (row["outbound_event_id"], row["inbound_event_id"])
        action = "create"
        if validation_errors:
            action = "blocked_validation_error"
        elif pair in existing["pairs"]:
            action = "skip_existing"
        elif row["outbound_event_id"] in existing["outbound_ids"] or row["inbound_event_id"] in existing["inbound_ids"]:
            action = "blocked_conflict"
        match_id = ""
        if apply and action == "create":
            match_id = STORE.create_transfer_match(
                outbound_event_id=row["outbound_event_id"],
                inbound_event_id=row["inbound_event_id"],
                confidence_score="0.9990",
                time_diff_seconds=int(row["time_diff_seconds"]),
                amount_diff="0",
                status="matched",
                method=METHOD,
                note=(
                    "TRC20-USDT transfer verified by identical tx_id in Binance withdrawal, "
                    "Pionex deposit and Tron transaction; preserves lot continuity only."
                ),
            )
            created.append({**row, "match_id": match_id})
            action = "created"
        candidates.append(
            {
                "label": row["label"],
                "tx_id": row["tx_id"],
                "quantity_usdt": plain(row["quantity"]),
                "time_diff_seconds": row["time_diff_seconds"],
                "tronscan_url": row["tronscan_url"],
                "outbound": event_summary(outbound),
                "inbound": event_summary(inbound),
                "validation_errors": validation_errors,
                "action": action,
                "match_id": match_id,
            }
        )
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "applied": apply,
        "method": METHOD,
        "candidate_count": len(candidates),
        "created_count": len(created),
        "candidates": candidates,
        "created": created,
        "interpretation": [
            "Die TX-ID beweist nur den Binance->Pionex-Transfer, nicht die urspruengliche Anschaffung der USDT.",
            "Der Match erzeugt keine neuen Anschaffungskosten und keinen neuen Preisanker.",
            "Der 2022-01-19-Transfer kommt nach dem Pionex-MXC-BUY um 12:45:42 UTC; dafuer bleibt vorheriger Pionex-Bestand oder ein fehlender Beleg erforderlich.",
        ],
    }


def render_doc(report: dict[str, Any]) -> str:
    lines = [
        "# USDT Binance -> Pionex Transfer-Match",
        "",
        f"Stand: {RUN_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Applied: `{report['applied']}`",
        f"- Methode: `{report['method']}`",
        f"- Kandidaten: `{report['candidate_count']}`",
        f"- Erstellt: `{report['created_count']}`",
        "",
        "## Bewertung",
        "",
    ]
    for line in report["interpretation"]:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "## Matches",
            "",
            "| Label | TXID | Menge USDT | Out UTC | In UTC | Delta Sekunden | Aktion | Match |",
            "| --- | --- | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in report["candidates"]:
        lines.append(
            "| {label} | `{tx_id}` | {quantity_usdt} | `{out}` | `{inc}` | {seconds} | `{action}` | `{match}` |".format(
                label=row["label"],
                tx_id=row["tx_id"],
                quantity_usdt=row["quantity_usdt"],
                out=row["outbound"]["timestamp_utc"],
                inc=row["inbound"]["timestamp_utc"],
                seconds=row["time_diff_seconds"],
                action=row["action"],
                match=row["match_id"],
            )
        )
    lines.extend(["", "## Onchain-Beleg", ""])
    for row in report["candidates"]:
        lines.extend(
            [
                f"### {row['label']}",
                "",
                f"- Tronscan: {row['tronscan_url']}",
                f"- TXID: `{row['tx_id']}`",
                f"- Betrag: `{row['quantity_usdt']} USDT`",
                f"- Binance Out: `{row['outbound']['timestamp_utc']}`",
                f"- Pionex In: `{row['inbound']['timestamp_utc']}`",
                f"- Binance Raw `completeTime`: `{row['outbound']['raw_complete_time']}`",
                f"- Pionex Raw `date(UTC+0)`: `{row['inbound']['raw_date']}`",
                f"- Binance Zieladresse / Pionex Deposit-Adresse: `{row['outbound']['address'] or row['inbound']['raw_to']}`",
                f"- Binance Hot-Wallet laut Binance-Rohfeld `info`: `{row['outbound']['raw_from']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Wichtig",
            "",
            "Diese Transfer-Matches koennen die belegte Lot-Kontinuitaet zwischen Binance und Pionex verbessern. "
            "Sie loesen aber nicht automatisch die offene Anschaffungskette, wenn die verbrauchten USDT schon "
            "vor dem Transfer auf Pionex vorhanden gewesen sein muessen oder wenn auf Binance fuer den Abgang "
            "selbst noch Anschaffungskosten fehlen.",
            "",
            f"JSON: `{OUT_JSON.relative_to(ROOT)}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Persist validated transfer matches.")
    args = parser.parse_args()
    report = build_report(apply=args.apply)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    OUT_MD.write_text(render_doc(report), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "doc": str(OUT_MD), "created_count": report["created_count"]}, indent=2))


if __name__ == "__main__":
    main()
