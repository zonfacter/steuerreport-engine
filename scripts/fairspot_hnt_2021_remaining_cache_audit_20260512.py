#!/usr/bin/env python3
"""Audit cached Fairspot wallet exports for remaining 2021 HNT zero-cost rows."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-05-12"
DEFAULT_DB = Path("/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite")
DEFAULT_CACHE_DIR = Path("/root/.local/share/steuerreport/fairspot_wallet_exports")
OUT_JSON = ROOT / "var" / "fairspot_hnt_2021_remaining_cache_audit_2026-05-12.json"
OUT_MD = ROOT / "docs" / "236_FAIRSPOT_HNT_2021_REMAINING_CACHE_AUDIT_2026-05-12.md"

MAIN_WALLET = "133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j"
STAKING_WALLET = "14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA"
BINANCE_WALLET = "138bCXPVfSq7yyTfoDUrVwztPmUr4WGyA7TED9Y41djmF7rjA8y"
ROUNDTRIP_WALLET = "14o7quYAMQZFE8UCNPN89yK9fwtxMW8wvht8MQZkSiSgizeqSme"
SERVICE_LIKE_INBOUND_WALLET = "14YeKFGXE23yAdACj6hu5NWEcYzzKxptYbm5jHgzw9A1P1UQfMv"

CUTOFFS = (
    ("2021-08-17 16:10:05", "Vor Binance-HNT-Verkauf ohne Lot-Quelle"),
    ("2021-08-20 08:01:13", "Nach Legacy-Outflow zum Binance-Deposit dd5353..."),
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


def dec(value: Any) -> Decimal:
    text = str(value or "0").strip().replace(",", ".")
    try:
        return Decimal(text) if text else Decimal("0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Any) -> str:
    value_dec = dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def load_wallet(cache_dir: Path, wallet: str) -> list[FairspotRow]:
    path = cache_dir / f"helium-{wallet}-all.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing cached Fairspot CSV: {path}")
    rows: list[FairspotRow] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
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


def wallet_balance_until(rows: list[FairspotRow], wallet: str, cutoff: str) -> dict[str, Any]:
    scoped = [row for row in rows if row.date <= cutoff]
    rewards = Decimal("0")
    payment_in = Decimal("0")
    payment_out = Decimal("0")
    fees = Decimal("0")
    type_counts: Counter[str] = Counter()
    for row in scoped:
        type_counts[row.type] += 1
        if row.type.startswith("rewards"):
            rewards += row.hnt_amount
        if row.payee == wallet:
            payment_in += row.hnt_amount
        if row.payer == wallet:
            payment_out += row.hnt_amount
            fees += row.hnt_fee
    balance = rewards + payment_in - payment_out - fees
    return {
        "wallet": wallet,
        "cutoff": cutoff,
        "row_count": len(scoped),
        "type_counts": dict(sorted(type_counts.items())),
        "reward_hnt": plain(rewards),
        "payment_in_hnt": plain(payment_in),
        "payment_out_hnt": plain(payment_out),
        "fee_hnt": plain(fees),
        "balance_hnt": plain(balance),
    }


def direct_payments(rows: list[FairspotRow], from_wallet: str, to_wallet: str, cutoff: str) -> list[dict[str, str]]:
    return [
        serialize(row)
        for row in rows
        if row.date <= cutoff
        and row.type.startswith("payment")
        and row.payer == from_wallet
        and row.payee == to_wallet
    ]


def window_payments(rows: list[FairspotRow], start: str, end: str) -> list[dict[str, str]]:
    output = [
        serialize(row)
        for row in rows
        if start <= row.date <= end and row.type.startswith("payment") and (row.payer == MAIN_WALLET or row.payee == MAIN_WALLET)
    ]
    return sorted(output, key=lambda item: (item["date"], item["transaction_hash"]))


def counterparty_context(rows: list[FairspotRow], wallet: str, cutoff: str) -> dict[str, Any]:
    scoped = [row for row in rows if row.date <= cutoff and row.type.startswith("payment")]
    inbound = [row for row in scoped if row.payee == wallet]
    outbound = [row for row in scoped if row.payer == wallet]
    balance = sum((row.hnt_amount for row in inbound), Decimal("0")) - sum(
        (row.hnt_amount + row.hnt_fee for row in outbound), Decimal("0")
    )
    return {
        "wallet": wallet,
        "cutoff": cutoff,
        "payment_rows": len(scoped),
        "inbound_rows": len(inbound),
        "outbound_rows": len(outbound),
        "unique_inbound_payers": len({row.payer for row in inbound if row.payer}),
        "unique_outbound_payees": len({row.payee for row in outbound if row.payee}),
        "in_hnt": plain(sum((row.hnt_amount for row in inbound), Decimal("0"))),
        "out_hnt": plain(sum((row.hnt_amount for row in outbound), Decimal("0"))),
        "fee_hnt": plain(sum((row.hnt_fee for row in outbound), Decimal("0"))),
        "payment_balance_hnt": plain(balance),
        "latest_payments": [serialize(row) for row in sorted(scoped, key=lambda item: item.date)[-5:]],
    }


def rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def remaining_hnt_lines(db_path: Path) -> list[dict[str, str]]:
    uri = f"file:{db_path}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        result = rows(
            conn,
            """
            SELECT tax_year, line_no, asset, qty, buy_timestamp_utc, sell_timestamp_utc,
                   cost_basis_eur, proceeds_eur, gain_loss_eur, source_event_id,
                   lot_source_event_id, transfer_chain_id
            FROM ai_open_zero_cost_tax_lines
            WHERE asset = 'HNT'
              AND tax_year = 2021
              AND CAST(proceeds_eur AS REAL) >= 50
            ORDER BY line_no
            """,
        )
    finally:
        conn.close()
    return [{key: str(value or "") for key, value in row.items()} for row in result]


def build_audit(cache_dir: Path = DEFAULT_CACHE_DIR, db_path: Path = DEFAULT_DB) -> dict[str, Any]:
    main_rows = load_wallet(cache_dir, MAIN_WALLET)
    staking_rows = load_wallet(cache_dir, STAKING_WALLET)
    roundtrip_rows = load_wallet(cache_dir, ROUNDTRIP_WALLET)
    service_like_rows = load_wallet(cache_dir, SERVICE_LIKE_INBOUND_WALLET)

    balances = []
    for cutoff, label in CUTOFFS:
        balances.append({"label": label, **wallet_balance_until(main_rows, MAIN_WALLET, cutoff)})
        balances.append({"label": label, **wallet_balance_until(staking_rows, STAKING_WALLET, cutoff)})

    binance_transfers_before_sale = direct_payments(main_rows, MAIN_WALLET, BINANCE_WALLET, "2021-08-17 16:10:05")
    august_window = window_payments(main_rows, "2021-08-01 00:00:00", "2021-08-20 23:59:59")

    audit = {
        "run_date": RUN_DATE,
        "created_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "cache_dir": str(cache_dir),
        "db_path": str(db_path),
        "wallets": {
            "main_wallet": MAIN_WALLET,
            "staking_wallet": STAKING_WALLET,
            "binance_wallet": BINANCE_WALLET,
            "roundtrip_wallet": ROUNDTRIP_WALLET,
            "service_like_inbound_wallet": SERVICE_LIKE_INBOUND_WALLET,
        },
        "remaining_hnt_lines": remaining_hnt_lines(db_path),
        "fairspot_balances": balances,
        "binance_transfers_before_2021_08_17_sale": binance_transfers_before_sale,
        "main_wallet_august_payment_window": august_window,
        "roundtrip_wallet_context": counterparty_context(roundtrip_rows, ROUNDTRIP_WALLET, "2021-07-08 18:30:29"),
        "service_like_inbound_wallet_context": counterparty_context(
            service_like_rows, SERVICE_LIKE_INBOUND_WALLET, "2021-06-22 08:58:58"
        ),
        "interpretation": {
            "line_1285": (
                "Fairspot zeigt vor dem Binance-Verkauf am 2021-08-17 nur einen Restbestand von "
                "20.0447256801337252586127 HNT in der Haupt-Wallet. Die offenen 22.7759533567933520993873 HNT "
                "liegen auf Binance; ohne zusaetzlichen Binance-Deposit nach 2021-08-10 bleibt die Lot-Herkunft offen."
            ),
            "dd5353_lines": (
                "Der 2021-08-20-Abgang von 18.30256046 HNT an die Binance-Adresse ist in Fairspot vorhanden. "
                "Die Fairspot-Hauptwallet enthaelt vor diesem Abgang genug Bestand, aber ein Teil dieses Bestands "
                "haengt an inbound Transfers von Gegenwallets. Die Rueckkehr von 14o7... ist als Roundtrip belegnah; "
                "14Ye... wirkt wegen tausender Gegenparteien service-/poolartig und ist kein automatischer Cost-Basis-Fix."
            ),
            "tax_safety": (
                "Aus Fairspot-Rewards und Transfers wird hier keine steuerwirksame Anschaffungskostenkorrektur geschrieben. "
                "Der Bericht grenzt nur belegte Walletbewegungen und verbleibende Belegluecken ein."
            ),
        },
    }
    return audit


def render_table(headers: list[str], rows_: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(str(value) for value in row) + " |" for row in rows_],
    ]


def short_wallet(wallet: str) -> str:
    return f"{wallet[:8]}..." if wallet else ""


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Fairspot HNT 2021 Restzeilen Cache-Audit",
        "",
        f"Stand: {RUN_DATE}",
        "",
        "## Ergebnis",
        "",
        "- Der Fairspot-Cache wurde inklusive `rewards_v1`, `payment_v1`, `payment_v2` und Fees ausgewertet.",
        "- Vor dem Binance-HNT-Verkauf am `2021-08-17` zeigt Fairspot fuer die Haupt-Wallet nur `20.0447256801337252586127 HNT` Restbestand.",
        "- Vor dem `2021-08-20`-Abgang an die Binance-Adresse ist Fairspot-seitig genug Hauptwallet-Bestand sichtbar; ein Teil stammt aber aus Gegenwallet-Inbounds und ist nicht automatisch als bewertete Cost-Basis verwendbar.",
        "- Es wurde kein automatischer Preis-, FX- oder Cost-Basis-Fix abgeleitet.",
        "",
        "## Verbleibende 2021-HNT-Zero-Cost-Zeilen",
        "",
    ]
    remaining_rows = [
        [
            row["line_no"],
            row["qty"],
            row["sell_timestamp_utc"],
            row["proceeds_eur"],
            row["source_event_id"][:12] + "...",
            (row["lot_source_event_id"][:12] + "...") if row["lot_source_event_id"] else "",
        ]
        for row in audit["remaining_hnt_lines"]
    ]
    lines.extend(render_table(["Line", "HNT", "Sale-Zeit", "Erloes EUR", "Source", "Lot-Source"], remaining_rows))

    lines.extend(["", "## Fairspot-Bestandsschnitte", ""])
    balance_rows = [
        [
            item["label"],
            short_wallet(item["wallet"]),
            item["row_count"],
            item["reward_hnt"],
            item["payment_in_hnt"],
            item["payment_out_hnt"],
            item["fee_hnt"],
            item["balance_hnt"],
        ]
        for item in audit["fairspot_balances"]
    ]
    lines.extend(
        render_table(
            ["Kontext", "Wallet", "Zeilen", "Rewards HNT", "In HNT", "Out HNT", "Fees HNT", "Saldo HNT"],
            balance_rows,
        )
    )

    lines.extend(["", "## Direkte Binance-Abgaenge vor 2021-08-17", ""])
    transfer_rows = [
        [row["date"], row["transaction_hash"], row["hnt_amount"], row["hnt_fee"]]
        for row in audit["binance_transfers_before_2021_08_17_sale"]
    ]
    lines.extend(render_table(["Zeit", "Tx", "HNT", "Fee HNT"], transfer_rows))

    lines.extend(["", "## Hauptwallet-Zahlungen 2021-08-01 bis 2021-08-20", ""])
    window_rows = [
        [
            row["date"],
            row["transaction_hash"],
            row["hnt_amount"],
            row["hnt_fee"],
            short_wallet(row["payer"]),
            short_wallet(row["payee"]),
        ]
        for row in audit["main_wallet_august_payment_window"]
    ]
    lines.extend(render_table(["Zeit", "Tx", "HNT", "Fee HNT", "Von", "An"], window_rows))

    lines.extend(["", "## Gegenwallet-Kontext", ""])
    cp_rows = []
    for key, label in (
        ("roundtrip_wallet_context", "14o7... Roundtrip"),
        ("service_like_inbound_wallet_context", "14Ye... Service-/Pool-Indiz"),
    ):
        item = audit[key]
        cp_rows.append(
            [
                label,
                item["payment_rows"],
                item["inbound_rows"],
                item["outbound_rows"],
                item["unique_inbound_payers"],
                item["unique_outbound_payees"],
                item["in_hnt"],
                item["out_hnt"],
                item["payment_balance_hnt"],
            ]
        )
    lines.extend(
        render_table(
            [
                "Wallet-Kontext",
                "Zahlungen",
                "Inbound",
                "Outbound",
                "Unique In",
                "Unique Out",
                "In HNT",
                "Out HNT",
                "Saldo HNT",
            ],
            cp_rows,
        )
    )

    lines.extend(
        [
            "",
            "## Einordnung",
            "",
            "- Line `1285` bleibt offen: Fairspot belegt keinen zusaetzlichen Binance-HNT-Zufluss zwischen den bekannten Deposits am `2021-08-10` und dem Verkauf am `2021-08-17`.",
            "- Lines `1347` und `1517` bleiben fachlich eingegrenzt: der `dd5353...`-Deposit ist als Legacy-Abgang belegt, aber die vorgelagerte Bewertbarkeit haengt an der korrekten Behandlung der Gegenwallet-Inbounds.",
            "- `14o7...` ist ein belegnaher Roundtrip: `100 HNT` gingen von der Hauptwallet dorthin, `99.75 HNT` kamen zurueck.",
            "- `14Ye...` ist kein sauberer Eigenwallet-Nachweis: vor dem Transfer an die Hauptwallet hat diese Wallet tausende Zahlungsgegenparteien.",
            "- Naechster sicherer Schritt ist daher kein Auto-Fix, sondern ein separater Review-/Importpfad nur fuer belegbare eigene Roundtrips oder nachgelieferte Primaerbelege.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    audit = build_audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "doc": str(OUT_MD)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
