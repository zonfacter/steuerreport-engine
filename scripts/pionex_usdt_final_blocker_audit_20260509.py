from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-05-09"
PIONEX_ADDRESS = "TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dec(value: Any) -> Decimal:
    return Decimal(str(value or "0"))


def _plain(value: Decimal) -> str:
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_doc(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = [
        f"# Pionex USDT Final Blocker Audit - {RUN_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Status: `{payload['status']}`",
        f"- Pionex-Adresse: `{payload['pionex_tron_address']}`",
        f"- Bekannte TRC20-USDT-Eingaenge auf diese Adresse: `{payload['tron_summary']['incoming_count']}`",
        f"- Bekannte TRC20-USDT-Eingaenge bis Worst: `{payload['tron_summary']['incoming_until_worst_usdt']} USDT`",
        f"- Benoetigtes Opening zur negativen Chronologievermeidung: `{payload['pionex_gap']['required_opening_usdt']} USDT`",
        f"- Nicht durch sichtbare Deposits gedeckt: `{payload['pionex_gap']['uncovered_until_worst_usdt']} USDT`",
        f"- Binance-Withdrawals zur Pionex-Adresse: `{payload['binance_summary']['withdrawal_count']}` / `{payload['binance_summary']['withdrawal_sum_usdt']} USDT`",
        f"- Steuerwirksamer Auto-Import empfohlen: `{payload['decision']['tax_effective_auto_import_recommended']}`",
        "",
        "## Onchain-Befund",
        "",
        "- Die Pionex-TRON-Adresse ist eine Durchgangsadresse: jeder sichtbare Eingang wurde kurz danach an eine Pionex-Sweep-Adresse weitergeleitet.",
        "- Vor dem Worst-Zeitpunkt am `2022-01-19T12:56:19+00:00` gibt es auf der bekannten Adresse nur zwei USDT-Eingaenge.",
        "- Es gibt keinen Onchain-Beleg fuer einen weiteren USDT-Eingang auf diese bekannte Adresse vor dem Worst-Zeitpunkt.",
        "",
        "## Bekannte TRC20-Transfers",
        "",
        "| Zeit UTC | Richtung | Betrag USDT | Von | An | TX |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in payload["tron_summary"]["transfers"]:
        lines.append(
            "| {timestamp_utc} | {direction} | {amount_usdt} | `{from_address}` | `{to_address}` | `{tx_id}` |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Bewertung",
            "",
            "- Die sichtbaren Binance- und TRON-Daten belegen die bekannten Pionex-Deposits, erklaeren aber nicht das fehlende Start-/Botkapital.",
            "- Der Restblocker ist damit kein globaler USDT-Endbestandsfehler, sondern ein Pionex-plattformlokaler Startbestand-/Bot-Historien-Nachweis.",
            "- Ohne Primaerbeleg sollte keine steuerwirksame Einnahme oder Anschaffung erfunden werden.",
            "- Fuer einen final sauberen Report bleiben zwei belastbare Wege: Pionex-Support/Snapshot/Bot-Historie nachreichen oder explizit als nicht steuerwirksame Inventar-Normalisierung freigeben.",
            "",
            "## Empfohlene naechste API-Entscheidung",
            "",
            "```json",
            json.dumps(payload["decision"]["review_decision_payload"], indent=2, ensure_ascii=False),
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    tron = _read_json(ROOT / "var" / "tron_pionex_deposit_address_usdt_summary_2026-05-08.json")
    binance = _read_json(ROOT / "var" / "binance_withdraw_address_summary_2026-05-08.json")
    dossier = _read_json(ROOT / "var" / f"pionex_opening_decision_dossier_{RUN_DATE}.json")
    evidence = dossier["evidence"]
    worst_ts = str(evidence["worst_balance"]["timestamp_utc"])

    transfers = []
    incoming_until_worst = Decimal("0")
    incoming_count = 0
    for row in tron.get("transfers", []):
        if row.get("symbol") != "USDT":
            continue
        amount = _dec(row.get("amount"))
        direction = str(row.get("direction") or "")
        if direction == "in":
            incoming_count += 1
            if str(row.get("timestamp_utc") or "") <= worst_ts:
                incoming_until_worst += amount
        transfers.append(
            {
                "timestamp_utc": row.get("timestamp_utc", ""),
                "direction": direction,
                "amount_usdt": _plain(amount),
                "from_address": row.get("from", ""),
                "to_address": row.get("to", ""),
                "tx_id": row.get("tx_id", ""),
            }
        )

    binance_pionex = next((item for item in binance if item.get("address") == PIONEX_ADDRESS), {})
    withdrawal_sum = _dec((binance_pionex.get("assets") or {}).get("USDT"))

    required_opening = _dec(evidence.get("required_opening_to_avoid_negative_usdt"))
    visible_until_worst = _dec(evidence.get("visible_deposit_sum_until_worst_usdt"))
    uncovered = _dec(evidence.get("uncovered_by_visible_deposits_until_worst_usdt"))
    status = "hard_blocker_primary_evidence_or_explicit_non_tax_decision_required"

    payload: dict[str, Any] = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "pionex_tron_address": PIONEX_ADDRESS,
        "source_files": {
            "tron_usdt_summary": "var/tron_pionex_deposit_address_usdt_summary_2026-05-08.json",
            "binance_withdraw_summary": "var/binance_withdraw_address_summary_2026-05-08.json",
            "decision_dossier": f"var/pionex_opening_decision_dossier_{RUN_DATE}.json",
        },
        "pionex_gap": {
            "first_negative_timestamp_utc": evidence["first_negative"]["timestamp_utc"],
            "worst_timestamp_utc": worst_ts,
            "required_opening_usdt": _plain(required_opening),
            "visible_deposit_sum_until_worst_usdt": _plain(visible_until_worst),
            "uncovered_until_worst_usdt": _plain(uncovered),
        },
        "tron_summary": {
            "incoming_count": incoming_count,
            "transfer_count": len(transfers),
            "incoming_until_worst_usdt": _plain(incoming_until_worst),
            "address_first_timestamp_utc": tron.get("first_timestamp_utc", ""),
            "address_last_timestamp_utc": tron.get("last_timestamp_utc", ""),
            "transfers": transfers,
        },
        "binance_summary": {
            "withdrawal_count": binance_pionex.get("count", 0),
            "withdrawal_sum_usdt": _plain(withdrawal_sum),
            "samples": binance_pionex.get("samples", []),
        },
        "decision": {
            "tax_effective_auto_import_recommended": False,
            "can_mark_final_clean_without_decision": False,
            "review_decision_payload": {
                "candidate_id": "pionex-usdt-opening-balance-2021-12-28",
                "decision": "request_more_evidence",
                "reviewer": "codex",
                "note": (
                    "Known Binance/TRON/Pionex exports prove only 1445.38419 USDT deposits before the "
                    "2022-01-19 worst point. Missing 197.8470311162 USDT remains unsupported by primary "
                    "Pionex bot/start-balance evidence; keep as non-tax review blocker."
                ),
                "evidence": {
                    "final_blocker_audit": f"docs/167_PIONEX_USDT_FINAL_BLOCKER_AUDIT_{RUN_DATE}.md",
                    "decision_dossier": f"docs/157_PIONEX_OPENING_DECISION_DOSSIER_{RUN_DATE}.md",
                    "tron_summary": "var/tron_pionex_deposit_address_usdt_summary_2026-05-08.json",
                    "binance_withdraw_summary": "var/binance_withdraw_address_summary_2026-05-08.json",
                },
            },
        },
    }

    json_path = ROOT / "var" / f"pionex_usdt_final_blocker_audit_{RUN_DATE}.json"
    doc_path = ROOT / "docs" / f"167_PIONEX_USDT_FINAL_BLOCKER_AUDIT_{RUN_DATE}.md"
    _write_json(json_path, payload)
    _write_doc(doc_path, payload)
    print(json.dumps({"json": str(json_path), "doc": str(doc_path), "status": status}, indent=2))


if __name__ == "__main__":
    main()
