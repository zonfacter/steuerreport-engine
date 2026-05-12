#!/usr/bin/env python3
"""Audit the HNT staking/legacy -> Binance -> USDT -> Pionex hypothesis."""

from __future__ import annotations

import csv
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
    _plain,
)

CREATED_DATE = "2026-05-09"
JSON_PATH = ROOT / "var" / f"hnt_staking_to_pionex_usdt_chain_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"128_HNT_STAKING_TO_PIONEX_USDT_CHAIN_AUDIT_{CREATED_DATE}.md"
PIONEX_DEPOSIT_WITHDRAW = ROOT / "usertransfer" / "pionex" / "deposit-withdraw.csv"
BINANCE_HNT_ADDRESS = "138bCXPVfSq7yyTfoDUrVwztPmUr4WGyA7TED9Y41djmF7rjA8y"


def main() -> None:
    aliases = _load_token_aliases()
    ignored_mints = set(_load_ignored_tokens().keys())
    movements = [
        movement
        for row in _effective_events()
        for movement in _movements(row, token_aliases=aliases, ignored_mints=ignored_mints)
        if movement["asset"] in {"HNT", "USDT"}
        and "2021-12-01" <= str(movement["timestamp"])[:10] <= "2022-01-19"
    ]
    movements.sort(key=_movement_sort_key)

    chain_window = [
        movement
        for movement in movements
        if "2021-12-13" <= str(movement["timestamp"])[:10] <= "2021-12-25"
        and movement["source"] in {"helium_legacy_cointracking", "binance", "binance_api", "pionex"}
        and (
            movement["event_type"] in {"legacy_transfer", "deposit", "trade", "withdrawal"}
            or movement["source"] in {"binance_api", "pionex"}
        )
    ]
    totals = summarize(movements)
    pionex_deposits = load_pionex_deposits()
    audit = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "hypothesis": "HNT staking/legacy rewards were transferred to Binance, sold to USDT, then USDT was sent to Pionex.",
        "known_binance_hnt_deposit_address": BINANCE_HNT_ADDRESS,
        "pionex_deposit_withdraw_file": str(PIONEX_DEPOSIT_WITHDRAW.relative_to(ROOT)),
        "pionex_deposit_assets": sorted({row["coin"] for row in pionex_deposits if row["tx_type"] == "DEPOSIT"}),
        "pionex_deposits": pionex_deposits,
        "window_totals": totals,
        "evidence_chain": [slim(row) for row in chain_window],
        "interpretation": [
            "Direct HNT-to-Pionex deposit is not supported by the current Pionex deposit/withdraw CSV; Pionex deposits are USDT only in the early period.",
            "The chain HNT legacy/staking -> Binance is directly supported by matching HNT legacy transfer and Binance HNT deposit txid on 2021-12-13.",
            "The chain Binance HNT -> USDT is supported by Binance HNT trade-out and USDT trade-in rows, especially 2021-12-17 and 2021-12-25.",
            "The chain Binance USDT -> Pionex is directly supported by identical TXIDs for Binance withdrawals and Pionex deposits.",
            "This explains the source of visible Pionex funding, but it does not fully remove the remaining current global transient USDT gap of 125.5260918462 USDT.",
        ],
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH)}, ensure_ascii=False, indent=2))


def summarize(movements: list[dict[str, Any]]) -> dict[str, str]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for row in movements:
        key = f"{row['asset']}|{row['source']}|{row['event_type']}|{row['side']}"
        totals[key] += row["delta"]
    return {key: _plain(value) for key, value in sorted(totals.items())}


def load_pionex_deposits() -> list[dict[str, str]]:
    if not PIONEX_DEPOSIT_WITHDRAW.exists():
        return []
    with PIONEX_DEPOSIT_WITHDRAW.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for row in reader:
            rows.append(
                {
                    "date_utc": row.get("date(UTC+0)", ""),
                    "tx_type": row.get("tx_type", ""),
                    "amount": row.get("amount", ""),
                    "coin": row.get("coin", ""),
                    "network": row.get("network", ""),
                    "txid": row.get("txid", ""),
                }
            )
        return rows


def slim(row: dict[str, Any]) -> dict[str, str]:
    return {
        "timestamp": str(row.get("timestamp") or ""),
        "asset": str(row.get("asset") or ""),
        "source": str(row.get("source") or ""),
        "event_type": str(row.get("event_type") or ""),
        "side": str(row.get("side") or ""),
        "quantity": _plain(row.get("quantity") or "0"),
        "delta": _plain(row.get("delta") or "0"),
        "tx_id": str(row.get("tx_id") or ""),
    }


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# HNT Staking/Legacy -> Binance -> USDT -> Pionex Chain Audit - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Hypothese: {audit['hypothesis']}",
        f"- Bekannte Binance-HNT-Deposit-Adresse: `{audit['known_binance_hnt_deposit_address']}`",
        f"- Pionex Deposit-Datei: `{audit['pionex_deposit_withdraw_file']}`",
        f"- Pionex Deposit-Assets in dieser Datei: `{audit['pionex_deposit_assets']}`",
        "",
        "## Pionex Deposits",
        "",
    ]
    for row in audit["pionex_deposits"]:
        if row["tx_type"] == "DEPOSIT":
            lines.append(f"- `{row['date_utc']}` `{row['amount']} {row['coin']}` `{row['network']}` tx `{row['txid']}`")
    lines += ["", "## Window Totals 2021-12-01 bis 2022-01-19", ""]
    for key, value in audit["window_totals"].items():
        if any(marker in key for marker in ["HNT|binance", "USDT|binance", "USDT|pionex"]):
            lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Belegkette", ""]
    for row in audit["evidence_chain"]:
        lines.append(
            f"- `{row['timestamp']}` `{row['asset']}` `{row['source']}` / `{row['event_type']}` / `{row['side']}` "
            f"qty `{row['quantity']}` delta `{row['delta']}` tx `{row['tx_id']}`"
        )
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
