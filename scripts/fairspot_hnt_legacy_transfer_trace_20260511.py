#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-05-11"
OUT_JSON = ROOT / "var" / "fairspot_hnt_legacy_transfer_trace_2026-05-11.json"
OUT_MD = ROOT / "docs" / "230_FAIRSPOT_HNT_LEGACY_TRANSFER_TRACE_2026-05-11.md"
FAIRSPOT_PAGE = "https://www.fairspot.host/hnt-export-mining-tax"
CSV_BASE = "https://fairspot.nyc3.digitaloceanspaces.com/accounting-csv/helium-{wallet}-all.csv"

MAIN_WALLET = "133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j"
STAKING_WALLET = "14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA"
STAKING_COUNTERPARTY = "14aDLshY7p2MJrCgbYrWFZZfjB1MBSqHboo2cJCPCVR9Meorh7w"

CRITICAL_TX_IDS = (
    "n7pUrLCjNgmbd95CzofzUJAzMz6zlAZJqRmzYk_um7M",
    "LFebJjnxaKi5MkKKVWmCjGsBKNHzKbR83wnkms_BQV4",
    "q4_AgR7s3njJdUfMZkdUiUt_zDIvnjA-kavtXKu5bHE",
    "48Jt0OydVHYIZrwqPX0348Rkwk5cy9yLjyxnQlv7TKo",
    "7ABuG00VMpdR9jG9BevdWXZWY7CuQ3ZhgHrov7XeRGE",
    "8FHBnG2SF9IoQ3J_d5c9KuAkFVs-_mwERFe_Ix4eJbA",
)


@dataclass(frozen=True)
class FairspotRow:
    wallet: str
    block: str
    date: str
    type: str
    transaction_hash: str
    hnt_amount: Decimal
    hnt_fee: Decimal
    usd_oracle_price: Decimal
    usd_amount: Decimal
    usd_fee: Decimal
    payer: str
    payee: str


def dec(value: object) -> Decimal:
    text = str(value or "0").strip().replace(",", ".")
    try:
        return Decimal(text) if text else Decimal("0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: object) -> str:
    value_dec = dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def fetch_csv(wallet: str) -> list[FairspotRow]:
    url = CSV_BASE.format(wallet=wallet)
    with urlopen(url, timeout=45) as response:
        text = response.read().decode("utf-8")
    rows: list[FairspotRow] = []
    for row in csv.DictReader(text.splitlines()):
        rows.append(
            FairspotRow(
                wallet=wallet,
                block=str(row.get("block") or ""),
                date=str(row.get("date") or ""),
                type=str(row.get("type") or ""),
                transaction_hash=str(row.get("transaction_hash") or ""),
                hnt_amount=dec(row.get("hnt_amount")),
                hnt_fee=dec(row.get("hnt_fee")),
                usd_oracle_price=dec(row.get("usd_oracle_price")),
                usd_amount=dec(row.get("usd_amount")),
                usd_fee=dec(row.get("usd_fee")),
                payer=str(row.get("payer") or ""),
                payee=str(row.get("payee") or ""),
            )
        )
    return rows


def serialize(row: FairspotRow) -> dict[str, str]:
    return {
        "wallet": row.wallet,
        "block": row.block,
        "date": row.date,
        "type": row.type,
        "transaction_hash": row.transaction_hash,
        "hnt_amount": plain(row.hnt_amount),
        "hnt_fee": plain(row.hnt_fee),
        "usd_oracle_price": plain(row.usd_oracle_price),
        "usd_amount": plain(row.usd_amount),
        "usd_fee": plain(row.usd_fee),
        "payer": row.payer,
        "payee": row.payee,
    }


def rows_for_tx(rows_by_wallet: dict[str, list[FairspotRow]], tx_ids: Iterable[str]) -> list[dict[str, str]]:
    wanted = set(tx_ids)
    output_by_key: dict[tuple[str, str, str, str, str, str], FairspotRow] = {}
    for rows in rows_by_wallet.values():
        for row in rows:
            key = (row.date, row.transaction_hash, row.type, plain(row.hnt_amount), row.payer, row.payee)
            if row.transaction_hash not in wanted:
                continue
            current = output_by_key.get(key)
            if current is None or row.hnt_fee > current.hnt_fee:
                output_by_key[key] = row
    output = [serialize(row) for row in output_by_key.values()]
    return sorted(output, key=lambda item: (item["date"], item["transaction_hash"]))


def staking_counterparty_rows(rows: list[FairspotRow]) -> list[FairspotRow]:
    return [
        row
        for row in rows
        if {row.payer, row.payee} == {STAKING_WALLET, STAKING_COUNTERPARTY}
    ]


def summarize_staking_counterparty(rows: list[FairspotRow]) -> dict[str, str | int]:
    sent = Decimal("0")
    sent_fee = Decimal("0")
    received = Decimal("0")
    for row in rows:
        if row.payer == STAKING_WALLET and row.payee == STAKING_COUNTERPARTY:
            sent += row.hnt_amount
            sent_fee += row.hnt_fee
        elif row.payee == STAKING_WALLET and row.payer == STAKING_COUNTERPARTY:
            received += row.hnt_amount
    return {
        "row_count": len(rows),
        "sent_to_counterparty_hnt": plain(sent),
        "sent_fees_hnt": plain(sent_fee),
        "received_from_counterparty_hnt": plain(received),
        "net_received_minus_sent_and_fees_hnt": plain(received - sent - sent_fee),
    }


def summarize_until(rows: list[FairspotRow], cutoff: str) -> dict[str, str | int]:
    scoped = [row for row in rows if row.date <= cutoff]
    return summarize_staking_counterparty(scoped)


def build_trace() -> dict[str, object]:
    rows_by_wallet = {
        MAIN_WALLET: fetch_csv(MAIN_WALLET),
        STAKING_WALLET: fetch_csv(STAKING_WALLET),
        STAKING_COUNTERPARTY: fetch_csv(STAKING_COUNTERPARTY),
    }
    staking_rows = staking_counterparty_rows(rows_by_wallet[STAKING_WALLET])
    counterparty_payments_before_return = [
        row
        for row in rows_by_wallet[STAKING_COUNTERPARTY]
        if row.date <= "2022-07-12 01:08:41"
        and row.type.startswith("payment")
        and (row.payee == STAKING_COUNTERPARTY or row.payer == STAKING_COUNTERPARTY)
    ]
    inbound_to_counterparty = [
        row for row in counterparty_payments_before_return if row.payee == STAKING_COUNTERPARTY
    ]
    unique_inbound_payers = sorted({row.payer for row in inbound_to_counterparty if row.payer})

    return {
        "run_date": RUN_DATE,
        "created_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "sources": {
            "fairspot_page": FAIRSPOT_PAGE,
            "csv_base": CSV_BASE,
        },
        "wallets": {
            "main_wallet": MAIN_WALLET,
            "staking_wallet": STAKING_WALLET,
            "staking_counterparty": STAKING_COUNTERPARTY,
        },
        "downloaded_row_counts": {wallet: len(rows) for wallet, rows in rows_by_wallet.items()},
        "critical_transactions": rows_for_tx(rows_by_wallet, CRITICAL_TX_IDS),
        "staking_counterparty_summary_all": summarize_staking_counterparty(staking_rows),
        "staking_counterparty_summary_until_2022_07_12_010841": summarize_until(staking_rows, "2022-07-12 01:08:41"),
        "staking_counterparty_rows": [serialize(row) for row in staking_rows],
        "counterparty_context": {
            "payment_rows_until_return": len(counterparty_payments_before_return),
            "inbound_payment_rows_until_return": len(inbound_to_counterparty),
            "unique_inbound_payer_count_until_return": len(unique_inbound_payers),
            "sample_inbound_payers_until_return": unique_inbound_payers[:40],
        },
        "interpretation": {
            "2021_08_17": (
                "Fairspot bestaetigt den Transfer 100 HNT von der Haupt-Wallet an die Staking-Wallet "
                "und den anschliessenden Weitertransfer an 14aDLshY. Es gibt daraus keinen neuen "
                "Binance-Bestand fuer die HNT-Verkaeufe am 2021-08-17."
            ),
            "2022_07_12": (
                "Fairspot bestaetigt drei Rueckfluesse von 14aDLshY an die Staking-Wallet ueber "
                "421.34562734 HNT und den anschliessenden Ruecktransfer von 421.30245111 HNT an "
                "die Haupt-Wallet. Bis zu diesem Zeitpunkt war netto mehr HNT an 14aDLshY gesendet "
                "als von dort zurueckgekommen."
            ),
            "tax_safety": (
                "Die Fairspot-Daten belegen die Wallet-Kette und enthalten Oracle-USD-Werte. "
                "Sie beweisen aber nicht allein, ob 14aDLshY als eigene Verwahrung, Staking-Pool "
                "oder fremde Gegenpartei zu behandeln ist."
            ),
        },
    }


def render_doc(trace: dict[str, object]) -> str:
    rows = trace["critical_transactions"]
    staking_rows = trace["staking_counterparty_rows"]
    summary_until = trace["staking_counterparty_summary_until_2022_07_12_010841"]
    summary_all = trace["staking_counterparty_summary_all"]
    context = trace["counterparty_context"]
    lines = [
        "# Fairspot HNT Legacy Transfer Trace",
        "",
        f"Stand: {RUN_DATE}",
        "",
        "## Ergebnis",
        "",
        "- Fairspot stellt fuer Legacy-Helium-Wallets statische CSVs bereit.",
        "- Die CSVs enthalten `payer`, `payee`, `transaction_hash`, HNT-Menge, HNT-Fee und Helium-Oracle-USD-Werte.",
        "- Die fehlende 2022-HNT-Kette laesst sich bis zur Counterparty-Wallet `14aDLshY...` nachvollziehen.",
        "- `14aDLshY...` wirkt in den Fairspot-Daten wie eine stark genutzte Sammel-/Pool-/Service-Wallet; das ist eine Dateninferenz, kein steuerliches Urteil.",
        "- Fuer `2021-08-17` ergibt sich kein zusaetzlicher Binance-Zufluss.",
        "",
        "## Quellen",
        "",
        f"- Fairspot-Seite: `{FAIRSPOT_PAGE}`",
        "- Fairspot-CSV-Pattern: `https://fairspot.nyc3.digitaloceanspaces.com/accounting-csv/helium-{wallet}-all.csv`",
        "",
        "## Wallets",
        "",
        f"- Haupt-Wallet: `{MAIN_WALLET}`",
        f"- Staking-Wallet: `{STAKING_WALLET}`",
        f"- Counterparty/Payout-Wallet: `{STAKING_COUNTERPARTY}`",
        "",
        "## Kritische Transaktionen",
        "",
        "| Datum | Tx | Typ | HNT | Fee HNT | USD | Payer | Payee |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['date']}` | `{row['transaction_hash']}` | `{row['type']}` | "
            f"{row['hnt_amount']} | {row['hnt_fee']} | {row['usd_amount']} | "
            f"`{row['payer']}` | `{row['payee']}` |"
        )
    lines.extend(
        [
            "",
            "## Staking-Counterparty-Saldo",
            "",
            "| Scope | Zeilen | An Counterparty HNT | Fees HNT | Von Counterparty HNT | Netto Rueckfluss minus Sendung/Fee HNT |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            "| Bis `2022-07-12 01:08:41` | {row_count} | {sent_to_counterparty_hnt} | {sent_fees_hnt} | {received_from_counterparty_hnt} | {net_received_minus_sent_and_fees_hnt} |".format(
                **summary_until
            ),
            "| Alle Fairspot-Zeilen | {row_count} | {sent_to_counterparty_hnt} | {sent_fees_hnt} | {received_from_counterparty_hnt} | {net_received_minus_sent_and_fees_hnt} |".format(
                **summary_all
            ),
            "",
            "## Alle direkten Staking-Wallet-/Counterparty-Zeilen",
            "",
            "| Datum | Richtung | Tx | HNT | Fee HNT | USD |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in staking_rows:
        direction = "out" if row["payer"] == STAKING_WALLET else "in"
        lines.append(
            f"| `{row['date']}` | `{direction}` | `{row['transaction_hash']}` | "
            f"{row['hnt_amount']} | {row['hnt_fee']} | {row['usd_amount']} |"
        )
    lines.extend(
        [
            "",
            "## Counterparty-Kontext",
            "",
            f"- Payment-Zeilen der Counterparty bis zum Rueckfluss: `{context['payment_rows_until_return']}`",
            f"- Eingehende Payment-Zeilen an die Counterparty bis zum Rueckfluss: `{context['inbound_payment_rows_until_return']}`",
            f"- Einzigartige Payer an die Counterparty bis zum Rueckfluss: `{context['unique_inbound_payer_count_until_return']}`",
            "- Diese Breite spricht gegen eine einfache zweite eigene Wallet und eher fuer Pool-/Service-/Sammelwallet-Kontext.",
            "",
            "## Bewertung",
            "",
            "- Die Fairspot-Daten belegen, dass der 2022-Binance-Deposit ueber `14eKed...` und `133rkwo...` aus einem Rueckfluss von `14aDLshY...` stammt.",
            "- Bis zum Rueckfluss am `2022-07-12` hatte `14eKed...` netto noch weniger von `14aDLshY...` zurueckerhalten als vorher an diese Wallet gesendet.",
            "- Daraus folgt technisch: Die 2022-HNT-Luecke ist wahrscheinlich kein komplett neuer unbelegter Zufluss, sondern eine nicht modellierte Staking-/Custody-Rueckgabe-Kette.",
            "- Nicht automatisch ableiten: Anschaffungskosten, steuerliche Reward-Aufteilung oder Eigentumsstatus von `14aDLshY...`.",
            "",
            "## Naechste sichere Aktion",
            "",
            "- Einen separaten Korrekturpfad fuer `14eKed...` <-> `14aDLshY...` als Staking-/Custody-Kette bauen.",
            "- Dabei zuerst nur Transfer-/Continuity-Belege persistieren, wenn die Chain-Regeln mehrere Outbounds gegen spaetere Rueckfluesse sauber tragen.",
            "- Falls die Rueckfluesse fachlich als Staking-Rewards statt Rueckgabe von Principal behandelt werden sollen, muss das als Review-Entscheidung mit Fairspot-Oracle-USD-Werten dokumentiert werden.",
            "",
            f"JSON: `{OUT_JSON.relative_to(ROOT)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    trace = build_trace()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(trace, indent=2, sort_keys=True), encoding="utf-8")
    OUT_MD.write_text(render_doc(trace), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "report": str(OUT_MD)}, indent=2))


if __name__ == "__main__":
    main()
