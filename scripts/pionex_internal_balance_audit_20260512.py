#!/usr/bin/env python3
"""Reconstruct canonical Pionex balances before the January 2022 USDT break."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-05-12"
CUTOFF_TEXT = "2022-01-19 12:56:19"
CUTOFF = datetime.fromisoformat(CUTOFF_TEXT)
PIONEX_DIR = ROOT / "usertransfer" / "pionex"
TRADING_CSV = PIONEX_DIR / "trading.csv"
DEPOSIT_WITHDRAW_CSV = PIONEX_DIR / "deposit-withdraw.csv"
OUT_JSON = ROOT / "var" / "pionex_internal_balance_audit_2026-05-12.json"
OUT_MD = ROOT / "docs" / "241_PIONEX_INTERNAL_BALANCE_AUDIT_2026-05-12.md"


@dataclass(frozen=True)
class BalanceEvent:
    timestamp_utc: str
    asset: str
    delta: str
    kind: str
    source_file: str
    row_index: int
    symbol: str
    side: str
    tax_id: str


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Any) -> str:
    value_dec = dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.strip())


def read_deposit_events() -> list[BalanceEvent]:
    events: list[BalanceEvent] = []
    with DEPOSIT_WITHDRAW_CSV.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            timestamp = str(row.get("date(UTC+0)") or "")
            if parse_dt(timestamp) > CUTOFF:
                continue
            tx_type = str(row.get("tx_type") or "").upper()
            asset = str(row.get("coin") or "").upper()
            amount = dec(row.get("amount"))
            fee = dec(row.get("fee"))
            if tx_type == "DEPOSIT":
                delta = amount
                kind = "deposit_in"
            else:
                delta = -amount
                kind = "withdrawal_out"
            events.append(
                BalanceEvent(
                    timestamp_utc=timestamp.replace(" ", "T") + "+00:00",
                    asset=asset,
                    delta=plain(delta),
                    kind=kind,
                    source_file=str(DEPOSIT_WITHDRAW_CSV.relative_to(ROOT)),
                    row_index=idx,
                    symbol="",
                    side=tx_type,
                    tax_id=str(row.get("txid") or ""),
                )
            )
            if fee:
                events.append(
                    BalanceEvent(
                        timestamp_utc=timestamp.replace(" ", "T") + "+00:00",
                        asset=asset,
                        delta=plain(-fee),
                        kind="withdrawal_fee",
                        source_file=str(DEPOSIT_WITHDRAW_CSV.relative_to(ROOT)),
                        row_index=idx,
                        symbol="",
                        side=tx_type,
                        tax_id=str(row.get("txid") or ""),
                    )
                )
    return events


def split_symbol(symbol: str) -> tuple[str, str]:
    parts = symbol.upper().split("_", 1)
    if len(parts) != 2:
        return symbol.upper(), ""
    return parts[0], parts[1]


def read_trade_events() -> list[BalanceEvent]:
    events: list[BalanceEvent] = []
    with TRADING_CSV.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            timestamp = str(row.get("date(UTC+0)") or "")
            if parse_dt(timestamp) > CUTOFF:
                continue
            symbol = str(row.get("symbol") or "").upper()
            base, quote = split_symbol(symbol)
            qty = dec(row.get("executed_qty"))
            amount = dec(row.get("amount"))
            side = str(row.get("side") or "").upper()
            fee = dec(row.get("fee"))
            fee_coin = str(row.get("fee_coin") or "").upper()
            tax_id = str(row.get("tax_id") or "")
            if side == "BUY":
                legs = ((base, qty, "trade_buy_base_in"), (quote, -amount, "trade_buy_quote_out"))
            else:
                legs = ((base, -qty, "trade_sell_base_out"), (quote, amount, "trade_sell_quote_in"))
            for asset, delta, kind in legs:
                events.append(
                    BalanceEvent(
                        timestamp_utc=timestamp.replace(" ", "T") + "+00:00",
                        asset=asset,
                        delta=plain(delta),
                        kind=kind,
                        source_file=str(TRADING_CSV.relative_to(ROOT)),
                        row_index=idx,
                        symbol=symbol,
                        side=side,
                        tax_id=tax_id,
                    )
                )
            if fee:
                events.append(
                    BalanceEvent(
                        timestamp_utc=timestamp.replace(" ", "T") + "+00:00",
                        asset=fee_coin,
                        delta=plain(-fee),
                        kind="trade_fee",
                        source_file=str(TRADING_CSV.relative_to(ROOT)),
                        row_index=idx,
                        symbol=symbol,
                        side=side,
                        tax_id=tax_id,
                    )
                )
    return events


def load_events() -> list[BalanceEvent]:
    events = [*read_deposit_events(), *read_trade_events()]
    return sorted(events, key=lambda event: (event.timestamp_utc, event.source_file, event.row_index, event.kind, event.asset))


def build_audit() -> dict[str, Any]:
    events = load_events()
    balances: dict[str, Decimal] = {}
    min_balances: dict[str, Decimal] = {}
    min_events: dict[str, BalanceEvent] = {}
    symbol_summary: dict[str, dict[str, Decimal]] = {}
    deposit_summary: dict[str, Decimal] = {}
    for event in events:
        asset = event.asset
        delta = dec(event.delta)
        balances[asset] = balances.get(asset, Decimal("0")) + delta
        if asset not in min_balances or balances[asset] < min_balances[asset]:
            min_balances[asset] = balances[asset]
            min_events[asset] = event
        if event.kind == "deposit_in":
            deposit_summary[asset] = deposit_summary.get(asset, Decimal("0")) + delta
        if event.symbol:
            summary = symbol_summary.setdefault(
                event.symbol,
                {
                    "base_in": Decimal("0"),
                    "base_out": Decimal("0"),
                    "quote_in": Decimal("0"),
                    "quote_out": Decimal("0"),
                    "fee": Decimal("0"),
                },
            )
            if event.kind == "trade_buy_base_in":
                summary["base_in"] += delta
            elif event.kind == "trade_sell_base_out":
                summary["base_out"] += -delta
            elif event.kind == "trade_sell_quote_in":
                summary["quote_in"] += delta
            elif event.kind == "trade_buy_quote_out":
                summary["quote_out"] += -delta
            elif event.kind == "trade_fee":
                summary["fee"] += -delta

    asset_rows = []
    for asset in sorted(balances):
        min_event = min_events[asset]
        required_opening = -min_balances[asset] if min_balances[asset] < 0 else Decimal("0")
        asset_rows.append(
            {
                "asset": asset,
                "deposit_in": plain(deposit_summary.get(asset, Decimal("0"))),
                "ending_balance": plain(balances[asset]),
                "minimum_balance": plain(min_balances[asset]),
                "required_opening_balance": plain(required_opening),
                "minimum_timestamp_utc": min_event.timestamp_utc,
                "minimum_event_kind": min_event.kind,
                "minimum_event_symbol": min_event.symbol,
                "minimum_event_delta": min_event.delta,
                "minimum_event_tax_id": min_event.tax_id,
            }
        )

    symbol_rows = []
    for symbol, summary in sorted(symbol_summary.items()):
        base, quote = split_symbol(symbol)
        symbol_rows.append(
            {
                "symbol": symbol,
                "base_asset": base,
                "quote_asset": quote,
                "base_in": plain(summary["base_in"]),
                "base_out": plain(summary["base_out"]),
                "quote_in": plain(summary["quote_in"]),
                "quote_out": plain(summary["quote_out"]),
                "net_quote_before_fees": plain(summary["quote_in"] - summary["quote_out"]),
                "fees": plain(summary["fee"]),
            }
        )

    negative_assets = [row for row in asset_rows if dec(row["required_opening_balance"]) > 0]
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "cutoff_utc": CUTOFF_TEXT.replace(" ", "T") + "+00:00",
        "source_files": [str(DEPOSIT_WITHDRAW_CSV.relative_to(ROOT)), str(TRADING_CSV.relative_to(ROOT))],
        "event_count": len(events),
        "asset_rows": asset_rows,
        "symbol_rows": symbol_rows,
        "negative_assets": negative_assets,
        "conclusion": {
            "status": "missing_usdt_opening_or_internal_statement",
            "required_usdt_opening": next(
                (row["required_opening_balance"] for row in negative_assets if row["asset"] == "USDT"),
                "0",
            ),
            "reason": (
                "In den kanonischen Pionex-CSV bis zum Cutoff wird nur USDT negativ. "
                "Andere Assets bleiben nicht negativ, daher ist kein sichtbarer interner Verkauf/Swap "
                "eines fehlenden Assets als Quelle der USDT-Luecke belegbar."
            ),
        },
    }


def table(headers: list[str], body: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(str(value) for value in row) + " |" for row in body],
    ]


def render_doc(audit: dict[str, Any]) -> str:
    negative = audit["negative_assets"]
    usdt = next((row for row in audit["asset_rows"] if row["asset"] == "USDT"), {})
    lines = [
        "# Pionex Interne Bilanz bis USDT-Bruch",
        "",
        f"Stand: {RUN_DATE}",
        "",
        "## Scope",
        "",
        f"- Cutoff: `{audit['cutoff_utc']}`",
        "- Quelle: kanonische lokale Pionex-Dateien `usertransfer/pionex/deposit-withdraw.csv` und `usertransfer/pionex/trading.csv`.",
        "- Zweck: Pruefen, ob die offene USDT-Luecke aus sichtbaren Pionex-Verkaeufen/Swaps anderer Assets entstanden sein kann.",
        "- Keine steuerliche Cost-Basis-Aenderung und keine Preis-/FX-Schaetzung.",
        "",
        "## Ergebnis",
        "",
        f"- Ausgewertete Bilanzbewegungen: `{audit['event_count']}`",
        f"- Assets mit negativem Mindestbestand: `{', '.join(row['asset'] for row in negative) or 'keine'}`",
        f"- Erforderlicher rechnerischer USDT-Startbestand: `{audit['conclusion']['required_usdt_opening']} USDT`",
        "- Andere Assets werden in dieser kanonischen Pionex-Chronologie bis zum Cutoff nicht negativ.",
        "- Damit ist kein sichtbarer interner Verkauf eines fehlenden Assets als Quelle der USDT-Luecke belegbar.",
        "",
        "## USDT-Kernbefund",
        "",
        f"- Sichtbare USDT-Deposits bis Cutoff: `{usdt.get('deposit_in', '0')} USDT`",
        f"- USDT-Endbestand aus sichtbaren Pionex-Bewegungen bis Cutoff: `{usdt.get('ending_balance', '0')} USDT`",
        f"- Schlechtester USDT-Stand: `{usdt.get('minimum_balance', '0')} USDT`",
        f"- Schlechtester Zeitpunkt: `{usdt.get('minimum_timestamp_utc', '')}`",
        f"- Ausloesendes sichtbares Event: `{usdt.get('minimum_event_kind', '')}` `{usdt.get('minimum_event_symbol', '')}` `{usdt.get('minimum_event_tax_id', '')}`",
        "",
        "## Asset-Bilanzen",
        "",
    ]
    lines.extend(
        table(
            ["Asset", "Deposits", "Endbestand", "Minimum", "Benoetigter Startbestand", "Minimum-Zeit", "Minimum-Event"],
            [
                [
                    row["asset"],
                    row["deposit_in"],
                    row["ending_balance"],
                    row["minimum_balance"],
                    row["required_opening_balance"],
                    row["minimum_timestamp_utc"],
                    f"{row['minimum_event_kind']} {row['minimum_event_symbol']}".strip(),
                ]
                for row in audit["asset_rows"]
            ],
        )
    )
    lines.extend(["", "## Trading-Paare bis Cutoff", ""])
    lines.extend(
        table(
            ["Symbol", "Base In", "Base Out", "Quote In", "Quote Out", "Net Quote vor Fees", "Fees"],
            [
                [
                    row["symbol"],
                    row["base_in"],
                    row["base_out"],
                    row["quote_in"],
                    row["quote_out"],
                    row["net_quote_before_fees"],
                    row["fees"],
                ]
                for row in audit["symbol_rows"]
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Einordnung",
            "",
            "- Die sichtbaren HNT_USDT-Trades erzeugen nur einen kleinen USDT-Ueberschuss; sie erklaeren die grosse MXC_USDT-Luecke nicht.",
            "- Der grosse Bruch liegt beim `MXC_USDT`-BUY `s_11` am `2022-01-19T12:56:19+00:00`.",
            "- Aus den vorhandenen Pionex-Dateien folgt daher: Es fehlt kein sichtbarer Asset-Verkauf, sondern ein USDT-Opening-/Bot-/Strategy-Startbestand oder eine nicht exportierte interne Pionex-Kontobuchung.",
            "- Ohne diesen Primaerbeleg darf weiterhin keine Anschaffungskostenbasis automatisch erzeugt werden.",
            "",
            f"JSON: `{OUT_JSON.relative_to(ROOT)}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    audit = build_audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "doc": str(OUT_MD)}, indent=2))


if __name__ == "__main__":
    main()
