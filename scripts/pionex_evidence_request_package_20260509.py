from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-05-09"
FINAL_AUDIT = ROOT / "var" / f"pionex_usdt_final_blocker_audit_{RUN_DATE}.json"
OUT_JSON = ROOT / "var" / f"pionex_evidence_request_package_{RUN_DATE}.json"
OUT_CSV = ROOT / "var" / f"pionex_usdt_known_transfers_for_support_{RUN_DATE}.csv"
OUT_EN = ROOT / "var" / f"pionex_support_request_usdt_history_en_{RUN_DATE}.txt"
OUT_DE = ROOT / "var" / f"pionex_support_request_usdt_history_de_{RUN_DATE}.txt"
OUT_DOC = ROOT / "docs" / f"172_PIONEX_EVIDENCE_REQUEST_PACKAGE_{RUN_DATE}.md"


def _read_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected object JSON: {path}")
    return raw


def _write_transfer_csv(transfers: list[dict[str, Any]]) -> None:
    headers = ["timestamp_utc", "direction", "amount_usdt", "from_address", "to_address", "tx_id"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for row in transfers:
            writer.writerow({key: row.get(key, "") for key in headers})


def _support_text_en(payload: dict[str, Any]) -> str:
    gap = payload["pionex_gap"]
    address = payload["pionex_tron_address"]
    return f"""Subject: Request for complete historical Pionex USDT account / bot history and opening balance evidence

Dear Pionex Support Team,

I am preparing a tax documentation package and need a complete historical export for my Pionex account.

Please provide all available records for the period from 2021-12-01 to 2022-02-28, especially:

- Spot trade history
- Bot/grid trading history including bot start capital, bot creation time, bot closing time and all generated trades
- Account balance snapshots or opening balances before 2021-12-28
- Deposit and withdrawal history
- Internal transfers or balance movements that are not visible as external blockchain deposits

The relevant USDT deposit address known from my records is:
{address}

The problem I need to document:
- First negative reconstructed Pionex USDT timestamp: {gap['first_negative_timestamp_utc']}
- Worst reconstructed Pionex USDT timestamp: {gap['worst_timestamp_utc']}
- Required opening/start balance to avoid negative Pionex USDT chronology: {gap['required_opening_usdt']} USDT
- Visible deposits until the worst timestamp: {gap['visible_deposit_sum_until_worst_usdt']} USDT
- Remaining unexplained amount: {gap['uncovered_until_worst_usdt']} USDT

Known TRC20/Binance deposits are attached/listed separately. They explain the visible deposits, but not the remaining opening/start balance gap.

Please provide the export in CSV or Excel format if possible. If some historical bot details are no longer available, please provide a written confirmation stating which records are unavailable and why.

Reason for request: tax documentation and audit trail.

Kind regards
"""


def _support_text_de(payload: dict[str, Any]) -> str:
    gap = payload["pionex_gap"]
    address = payload["pionex_tron_address"]
    return f"""Betreff: Anfrage vollstaendige historische Pionex USDT Konto-/Bot-Historie und Startbestand

Sehr geehrtes Pionex Support-Team,

ich erstelle eine Steuerdokumentation und benoetige einen vollstaendigen historischen Export fuer mein Pionex-Konto.

Bitte stellen Sie mir fuer den Zeitraum 01.12.2021 bis 28.02.2022 alle verfuegbaren Datensaetze bereit, insbesondere:

- Spot-Trade-Historie
- Bot-/Grid-Trading-Historie inklusive Bot-Startkapital, Bot-Startzeit, Bot-Endzeit und aller erzeugten Trades
- Konto-Snapshots oder Opening Balances vor dem 28.12.2021
- Deposit-/Withdraw-Historie
- Interne Transfers oder Bestandsbewegungen, die nicht als externe Blockchain-Deposits sichtbar sind

Die aus meinen Unterlagen bekannte USDT-Deposit-Adresse lautet:
{address}

Der zu belegende Sachverhalt:
- Erster negativer rekonstruierter Pionex-USDT-Zeitpunkt: {gap['first_negative_timestamp_utc']}
- Schlechtester rekonstruierter Pionex-USDT-Zeitpunkt: {gap['worst_timestamp_utc']}
- Benoetigter Opening-/Startbestand zur Vermeidung negativer Chronologie: {gap['required_opening_usdt']} USDT
- Sichtbare Deposits bis zum schlechtesten Zeitpunkt: {gap['visible_deposit_sum_until_worst_usdt']} USDT
- Offener, nicht erklaerter Betrag: {gap['uncovered_until_worst_usdt']} USDT

Die bekannten TRC20-/Binance-Deposits sind separat aufgefuehrt. Sie erklaeren die sichtbaren Einzahlungen, aber nicht die verbleibende Startbestands-/Bot-Kapital-Luecke.

Bitte stellen Sie die Daten nach Moeglichkeit als CSV oder Excel bereit. Falls historische Bot-Details nicht mehr verfuegbar sind, bitte ich um eine schriftliche Bestaetigung, welche Daten nicht verfuegbar sind und warum.

Grund der Anfrage: Steuerdokumentation und Pruefpfad.

Mit freundlichen Gruessen
"""


def _write_doc(package: dict[str, Any]) -> None:
    gap = package["pionex_gap"]
    lines = [
        "# Pionex Evidence Request Package - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        "- Zweck: Beleganforderung fuer den einzigen verbleibenden harten Readiness-Blocker.",
        "- Kandidat: `pionex-usdt-opening-balance-2021-12-28`",
        "- Status: `needs_evidence`",
        "- Steuerwirksame automatische Buchung: `False`",
        "",
        "## Offene Luecke",
        "",
        f"- Erste negative Pionex-USDT-Chronologie: `{gap['first_negative_timestamp_utc']}`",
        f"- Schlechtester Zeitpunkt: `{gap['worst_timestamp_utc']}`",
        f"- Benoetigter Opening-/Startbestand: `{gap['required_opening_usdt']} USDT`",
        f"- Sichtbare Deposits bis Worst: `{gap['visible_deposit_sum_until_worst_usdt']} USDT`",
        f"- Nicht belegter Rest: `{gap['uncovered_until_worst_usdt']} USDT`",
        "",
        "## Erzeugte Dateien",
        "",
        f"- JSON-Paket: `{OUT_JSON.relative_to(ROOT)}`",
        f"- Transfer-CSV: `{OUT_CSV.relative_to(ROOT)}`",
        f"- Supporttext Englisch: `{OUT_EN.relative_to(ROOT)}`",
        f"- Supporttext Deutsch: `{OUT_DE.relative_to(ROOT)}`",
        "",
        "## Bekannte Transfers",
        "",
        "| Zeit UTC | Richtung | Betrag USDT | Von | An | TX |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in package["known_transfers"]:
        lines.append(
            f"| {row.get('timestamp_utc', '')} | {row.get('direction', '')} | {row.get('amount_usdt', '')} | "
            f"`{row.get('from_address', '')}` | `{row.get('to_address', '')}` | `{row.get('tx_id', '')}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Die bekannten TRC20-/Binance-Transfers belegen die sichtbaren Pionex-Deposits.",
            "- Der offene Rest ist ein Pionex-interner Startbestand-/Bot-Historiennachweis, kein belegter steuerpflichtiger Zufluss.",
            "- Ohne weiteren Primaerbeleg bleibt der finale Export gesperrt; Entwurfsreports sind bereits als `ENTWURF - NICHT FINAL` markiert.",
            "",
        ]
    )
    OUT_DOC.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    audit = _read_json(FINAL_AUDIT)
    transfers = audit.get("tron_summary", {}).get("transfers", [])
    if not isinstance(transfers, list):
        transfers = []
    package = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "candidate_id": "pionex-usdt-opening-balance-2021-12-28",
        "status": "needs_evidence",
        "tax_effective": False,
        "pionex_tron_address": audit.get("pionex_tron_address", ""),
        "pionex_gap": audit.get("pionex_gap", {}),
        "known_transfers": transfers,
        "requested_evidence": [
            "Pionex spot trade history 2021-12-01 to 2022-02-28",
            "Pionex bot/grid history with bot start capital and generated trades",
            "Account balance snapshots or opening balances before 2021-12-28",
            "Internal transfers or balance movements not visible as blockchain deposits",
            "Written confirmation if older bot records are unavailable",
        ],
        "output_files": {
            "doc": str(OUT_DOC.relative_to(ROOT)),
            "json": str(OUT_JSON.relative_to(ROOT)),
            "transfer_csv": str(OUT_CSV.relative_to(ROOT)),
            "support_text_en": str(OUT_EN.relative_to(ROOT)),
            "support_text_de": str(OUT_DE.relative_to(ROOT)),
        },
    }
    OUT_JSON.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_transfer_csv(transfers)
    OUT_EN.write_text(_support_text_en(package), encoding="utf-8")
    OUT_DE.write_text(_support_text_de(package), encoding="utf-8")
    _write_doc(package)
    print(json.dumps(package["output_files"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
