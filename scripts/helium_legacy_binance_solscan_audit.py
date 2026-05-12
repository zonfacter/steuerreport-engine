#!/usr/bin/env python3
"""Audit Helium legacy, Binance HNT, and Solana/Solscan coverage."""

from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.api.dashboard import _payload_asset_canonical_symbol
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

CREATED_DATE = "2026-05-09"
JSON_PATH = ROOT / "var" / f"helium_legacy_binance_solscan_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"95_HELIUM_LEGACY_BINANCE_SOLSCAN_AUDIT_{CREATED_DATE}.md"
BALANCE_JSON = ROOT / "var" / "chronological_balance_break_audit_current_2026-05-09_after_heliumgeek_quantity_fix.json"
DB_PATH = Path("/root/.local/share/steuerreport/steuerreport.db")
HELIUM_ASSETS = {"HNT", "IOT", "MOBILE"}
BINANCE_HNT_DEPOSIT_ADDRESS = "138bCXPVfSq7yyTfoDUrVwztPmUr4WGyA7TED9Y41djmF7rjA8y"


def main() -> None:
    raw_events = STORE.list_raw_events()
    reviewed, review_summary = apply_review_actions(raw_events)
    effective_events, override_count = apply_tax_event_overrides(reviewed)

    helium_events = [event for event in effective_events if is_helium_related(event)]
    binance_hnt = [event for event in effective_events if is_binance_hnt(event)]
    binance_deposits = [event for event in binance_hnt if is_deposit_like(event)]
    binance_withdrawals = [event for event in binance_hnt if is_withdrawal_like(event)]
    binance_trades = [event for event in binance_hnt if is_trade_like(event)]
    legacy_events = [event for event in effective_events if is_legacy_helium_hnt(event)]
    solana_helium = [event for event in effective_events if is_solana_helium(event)]
    solscan_rows = load_solscan_helium_rows()

    legacy_by_base_tx = index_by_base_tx(legacy_events)
    deposit_matches = match_binance_deposits(binance_deposits, legacy_by_base_tx)
    legacy_raw_flow_summary = summarize_legacy_raw_flows(effective_events)
    heliumgeek_quantity_issues = summarize_heliumgeek_quantity_issues(effective_events)

    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "review_summary": review_summary,
        "tax_event_override_count": override_count,
        "scope": "Helium legacy L1, Binance HNT, Solana/Solscan post-migration evidence",
        "source_year_counts": summarize_source_year_counts(helium_events),
        "binance_hnt_summary": summarize_binance_hnt(binance_deposits, binance_withdrawals, binance_trades),
        "binance_hnt_deposit_legacy_matches": summarize_deposit_matches(deposit_matches),
        "unmatched_binance_hnt_deposits": [slim_event(item["deposit"]) for item in deposit_matches if not item["matched_legacy_events"]][:50],
        "legacy_raw_flow_summary": legacy_raw_flow_summary,
        "heliumgeek_quantity_issue_summary": heliumgeek_quantity_issues,
        "solana_post_migration_summary": summarize_solana_post_migration(solana_helium, solscan_rows),
        "balance_status": load_balance_status(),
        "interpretation": build_interpretation(deposit_matches, heliumgeek_quantity_issues),
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": compact_summary(audit)}, ensure_ascii=False, indent=2))


def is_helium_related(event: dict[str, Any]) -> bool:
    payload = payload_of(event)
    source = str(payload.get("source") or "").lower()
    asset = canonical_asset(payload)
    return asset in HELIUM_ASSETS or source.startswith("helium") or "helium" in source


def is_binance_hnt(event: dict[str, Any]) -> bool:
    payload = payload_of(event)
    source = str(payload.get("source") or "").lower()
    return source.startswith("binance") and canonical_asset(payload) == "HNT"


def is_legacy_helium_hnt(event: dict[str, Any]) -> bool:
    payload = payload_of(event)
    source = str(payload.get("source") or "").lower()
    return source.startswith("helium_legacy") and canonical_asset(payload) == "HNT"


def is_solana_helium(event: dict[str, Any]) -> bool:
    payload = payload_of(event)
    source = str(payload.get("source") or "").lower()
    return source in {"solana_rpc", "solscan_wallet_discovery"} and canonical_asset(payload) in HELIUM_ASSETS


def is_deposit_like(event: dict[str, Any]) -> bool:
    payload = payload_of(event)
    raw = raw_of(payload)
    event_type = str(payload.get("event_type") or "").lower()
    side = str(payload.get("side") or "").lower()
    return side == "in" and ("deposit" in event_type or str(raw.get("Status") or raw.get("status") or "").lower() in {"completed", "1"})


def is_withdrawal_like(event: dict[str, Any]) -> bool:
    payload = payload_of(event)
    event_type = str(payload.get("event_type") or "").lower()
    side = str(payload.get("side") or "").lower()
    return side == "out" and "withdraw" in event_type


def is_trade_like(event: dict[str, Any]) -> bool:
    payload = payload_of(event)
    event_type = str(payload.get("event_type") or "").lower()
    raw = raw_of(payload)
    return "trade" in event_type or str(raw.get("Operation") or raw.get("type") or "").lower() in {"buy", "sell", "trade"}


def index_by_base_tx(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        tx_id = base_tx(str(payload_of(event).get("tx_id") or ""))
        if tx_id:
            result[tx_id].append(event)
    return result


def match_binance_deposits(deposits: list[dict[str, Any]], legacy_by_base_tx: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for deposit in sorted(deposits, key=lambda event: (str(payload_of(event).get("timestamp_utc") or ""), str(event.get("unique_event_id") or ""))):
        tx_id = base_tx(str(payload_of(deposit).get("tx_id") or ""))
        rows.append({"deposit": deposit, "base_tx": tx_id, "matched_legacy_events": legacy_by_base_tx.get(tx_id, [])})
    return rows


def summarize_source_year_counts(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_source: Counter[str] = Counter()
    by_year: Counter[str] = Counter()
    by_source_year: Counter[str] = Counter()
    by_asset: Counter[str] = Counter()
    for event in events:
        payload = payload_of(event)
        source = str(payload.get("source") or "unknown")
        year = str(payload.get("timestamp_utc") or "unknown")[:4]
        asset = canonical_asset(payload) or "unknown"
        by_source[source] += 1
        by_year[year] += 1
        by_source_year[f"{source}:{year}"] += 1
        by_asset[asset] += 1
    return {
        "event_count": len(events),
        "by_source": dict(by_source.most_common()),
        "by_year": dict(by_year.most_common()),
        "by_asset": dict(by_asset.most_common()),
        "by_source_year_top": dict(by_source_year.most_common(40)),
    }


def summarize_binance_hnt(deposits: list[dict[str, Any]], withdrawals: list[dict[str, Any]], trades: list[dict[str, Any]]) -> dict[str, Any]:
    unique_deposits = unique_by_tx(deposits)
    return {
        "deposit_row_count": len(deposits),
        "unique_deposit_tx_count": len(unique_deposits),
        "deposit_total_hnt_rows": sum_qty(deposits),
        "deposit_total_hnt_unique_tx": sum_qty(unique_deposits),
        "deposit_address_counts": dict(address_counts(deposits).most_common()),
        "withdrawal_count": len(withdrawals),
        "withdrawal_total_hnt": sum_qty(withdrawals),
        "trade_leg_count": len(trades),
        "trade_net_hnt": signed_sum(trades),
        "first_deposit_utc": first_ts(deposits),
        "last_deposit_utc": last_ts(deposits),
        "known_binance_hnt_deposit_address": BINANCE_HNT_DEPOSIT_ADDRESS,
    }


def summarize_deposit_matches(matches: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [item for item in matches if item["matched_legacy_events"]]
    unmatched = [item for item in matches if not item["matched_legacy_events"]]
    unique_matches = unique_match_by_tx(matches)
    unique_matched = [item for item in unique_matches if item["matched_legacy_events"]]
    unique_unmatched = [item for item in unique_matches if not item["matched_legacy_events"]]
    matched_qty = sum(qty(payload_of(item["deposit"])) for item in matched)
    unmatched_qty = sum(qty(payload_of(item["deposit"])) for item in unmatched)
    unique_matched_qty = sum(qty(payload_of(item["deposit"])) for item in unique_matched)
    unique_unmatched_qty = sum(qty(payload_of(item["deposit"])) for item in unique_unmatched)
    return {
        "binance_hnt_deposit_row_count": len(matches),
        "matched_by_legacy_tx_id_row_count": len(matched),
        "unmatched_by_legacy_tx_id_row_count": len(unmatched),
        "matched_deposit_total_hnt_rows": plain(matched_qty),
        "unmatched_deposit_total_hnt_rows": plain(unmatched_qty),
        "unique_deposit_tx_count": len(unique_matches),
        "unique_matched_by_legacy_tx_id_count": len(unique_matched),
        "unique_unmatched_by_legacy_tx_id_count": len(unique_unmatched),
        "unique_matched_deposit_total_hnt": plain(unique_matched_qty),
        "unique_unmatched_deposit_total_hnt": plain(unique_unmatched_qty),
        "matched_examples": [
            {
                "deposit": slim_event(item["deposit"]),
                "legacy_matches": [slim_event(event) for event in item["matched_legacy_events"][:5]],
            }
            for item in matched[:10]
        ],
    }


def summarize_legacy_raw_flows(events: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    wallet_counter: Counter[str] = Counter()
    known_binance_hits = []
    for event in events:
        payload = payload_of(event)
        if str(payload.get("source") or "") != "helium_legacy_raw":
            continue
        raw = raw_of(payload)
        payer = str(raw.get("payer") or "")
        payee = str(raw.get("payee") or "")
        wallet_counter[payer] += 1
        wallet_counter[payee] += 1
        row = {
            "timestamp_utc": str(payload.get("timestamp_utc") or ""),
            "tx_id": str(payload.get("tx_id") or ""),
            "side": str(payload.get("side") or ""),
            "quantity": str(payload.get("quantity") or ""),
            "payer": payer,
            "payee": payee,
            "fee_hnt": str(raw.get("hnt_fee") or ""),
        }
        rows.append(row)
        if BINANCE_HNT_DEPOSIT_ADDRESS in {payer, payee}:
            known_binance_hits.append(row)
    return {
        "legacy_raw_transfer_count": len(rows),
        "known_wallets_top": dict(wallet_counter.most_common(20)),
        "known_binance_deposit_address_hits": known_binance_hits,
        "sample_transfers": rows[:20],
    }


def summarize_heliumgeek_quantity_issues(events: list[dict[str, Any]]) -> dict[str, Any]:
    issue_rows = []
    asset_totals_payload: defaultdict[str, Decimal] = defaultdict(Decimal)
    asset_totals_display: defaultdict[str, Decimal] = defaultdict(Decimal)
    for event in events:
        payload = payload_of(event)
        if str(payload.get("source") or "").lower() != "heliumgeek":
            continue
        asset = canonical_asset(payload)
        if asset not in HELIUM_ASSETS:
            continue
        raw = raw_of(payload)
        display = heliumgeek_display_quantity(raw, asset)
        payload_qty = qty(payload)
        asset_totals_payload[asset] += payload_qty
        asset_totals_display[asset] += display
        if display and payload_qty >= display * Decimal("100000"):
            issue_rows.append(
                {
                    "timestamp_utc": str(payload.get("timestamp_utc") or ""),
                    "asset": asset,
                    "payload_quantity": plain(payload_qty),
                    "display_quantity_from_raw": plain(display),
                    "ratio": plain(payload_qty / display),
                    "tx_id": str(payload.get("tx_id") or ""),
                }
            )
    return {
        "issue_count": len(issue_rows),
        "payload_totals": {asset: plain(value) for asset, value in sorted(asset_totals_payload.items())},
        "display_totals_from_raw": {asset: plain(value) for asset, value in sorted(asset_totals_display.items())},
        "sample_issues": issue_rows[:20],
        "interpretation": "HeliumGeek payload.quantity appears to be stored in raw subunits for affected rows; raw display token columns contain human token amounts. Dashboard/core logic and the updated balance audit use the display columns.",
    }


def summarize_solana_post_migration(events: list[dict[str, Any]], solscan_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "effective_solana_helium_event_count": len(events),
        "effective_solana_helium_by_source": dict(Counter(str(payload_of(event).get("source") or "unknown") for event in events).most_common()),
        "effective_solana_helium_by_asset": dict(Counter(canonical_asset(payload_of(event)) or "unknown" for event in events).most_common()),
        "effective_solana_helium_first_utc": first_ts(events),
        "effective_solana_helium_last_utc": last_ts(events),
        "cached_solscan_helium_transfer_count": len(solscan_rows),
        "cached_solscan_by_symbol": dict(Counter(str(row.get("symbol") or "unknown") for row in solscan_rows).most_common()),
        "cached_solscan_first_utc": min((str(row.get("block_time_utc") or "") for row in solscan_rows), default=""),
        "cached_solscan_last_utc": max((str(row.get("block_time_utc") or "") for row in solscan_rows), default=""),
    }


def load_solscan_helium_rows() -> list[dict[str, Any]]:
    if not DB_PATH.exists():
        return []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT signature, block_time_utc, flow, token_address, amount,
                   token_decimals, from_address, to_address
            FROM solscan_account_transfers
            ORDER BY block_time_utc ASC, signature ASC
            """
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        token_address = str(item.get("token_address") or "")
        symbol = solscan_symbol(token_address)
        if symbol not in HELIUM_ASSETS:
            continue
        item["symbol"] = symbol
        result.append(item)
    return result


def solscan_symbol(token_address: str) -> str:
    mapping = {
        "hntyVP6YFm1Hg25TN9WGLqM12b8TQmcknKrdu1oxWux": "HNT",
        "iotEVVZLEsS5eYBX9HGENZ8RduwvBwtKBbGVbfc5Kxs": "IOT",
        "mb1eu7Tz9gcdV2dD5kG1Y6dQNhRbRTEZ2p7mL8K9dY": "MOBILE",
    }
    return mapping.get(token_address, "")


def load_balance_status() -> dict[str, Any]:
    if not BALANCE_JSON.exists():
        return {"available": False}
    data = json.loads(BALANCE_JSON.read_text(encoding="utf-8"))
    wanted = {}
    for row in data.get("asset_reports", []):
        asset = str(row.get("asset") or "")
        if asset in {"HNT", "IOT", "MOBILE", "SOL", "USDT"}:
            wanted[asset] = {
                "final_balance": row.get("final_balance"),
                "first_negative": row.get("first_negative"),
                "worst_balance": row.get("worst_balance"),
                "yearly_net": row.get("yearly_net"),
                "source_net_top": row.get("source_net_top", [])[:10],
            }
    return {"available": True, "negative_final_assets": data.get("negative_final_assets"), "assets": wanted}


def build_interpretation(matches: list[dict[str, Any]], heliumgeek_issues: dict[str, Any]) -> list[str]:
    match_summary = summarize_deposit_matches(matches)
    lines = [
        "Binance-HNT ist als CEX-Seite stark belegt: Deposits, Deposit-Adresse, Trades und API/CSV-Duplikate liegen lokal vor.",
        f"Von {match_summary['unique_deposit_tx_count']} eindeutigen Binance-HNT-Deposit-Transaktionen wurden {match_summary['unique_matched_by_legacy_tx_id_count']} per gleicher Legacy-Transaktions-ID in Helium-Legacy-Quellen gefunden.",
        "Nicht gematchte Binance-HNT-Deposits sind kein Binance-Problem, sondern ein Legacy-L1-Evidence-Gap: Binance kennt den Eingang, aber die lokale Legacy-Quelle enthaelt nicht jeden passenden On-Chain-Transfer.",
        "Solana/Solscan deckt die Post-Migration-Phase ab; das ersetzt nicht die alte Helium-L1-Historie vor Migration.",
    ]
    if int(heliumgeek_issues.get("issue_count") or 0) > 0:
        lines.append("HeliumGeek-Miningdaten haben ein Rohdaten-Einheitenproblem: payload.quantity ist bei betroffenen rows um Faktor 1e6 zu hoch. Die Dashboard-/Core-Logik und die aktualisierte Bestandsbruch-Auswertung verwenden die Display-Tokenmengen aus raw_row.")
    return lines


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Helium Legacy / Binance / Solscan Audit - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Gezielte Pruefung, ob Binance ausserhalb der alten Helium-Blockchain sauber belegt ist, und wo Helium-Legacy/Solscan/Blockpit als Evidenzquellen stehen.",
        "",
        "## Gesamtabdeckung",
        "",
        f"- Helium-bezogene Effective Events: `{audit['source_year_counts']['event_count']}`",
        f"- Quellen: `{audit['source_year_counts']['by_source']}`",
        f"- Jahre: `{audit['source_year_counts']['by_year']}`",
        f"- Assets: `{audit['source_year_counts']['by_asset']}`",
        "",
        "## Binance HNT",
        "",
    ]
    b = audit["binance_hnt_summary"]
    lines += [
        f"- HNT-Deposit-Zeilen: `{b['deposit_row_count']}` total rows `{b['deposit_total_hnt_rows']}` HNT",
        f"- Eindeutige HNT-Deposit-TXIDs: `{b['unique_deposit_tx_count']}` total unique `{b['deposit_total_hnt_unique_tx']}` HNT",
        f"- Deposit-Zeitraum: `{b['first_deposit_utc']}` bis `{b['last_deposit_utc']}`",
        f"- Deposit-Adressen: `{b['deposit_address_counts']}`",
        f"- HNT-Withdrawals: `{b['withdrawal_count']}` total `{b['withdrawal_total_hnt']}` HNT",
        f"- HNT-Trade-Legs: `{b['trade_leg_count']}` net `{b['trade_net_hnt']}` HNT",
        "",
        "## Binance Deposits vs Helium Legacy TXID",
        "",
    ]
    m = audit["binance_hnt_deposit_legacy_matches"]
    lines += [
        f"- Binance-HNT-Deposit-Zeilen: `{m['binance_hnt_deposit_row_count']}`",
        f"- Eindeutige Deposit-TXIDs: `{m['unique_deposit_tx_count']}`",
        f"- Eindeutig per Legacy-TXID gematcht: `{m['unique_matched_by_legacy_tx_id_count']}`",
        f"- Eindeutig nicht per Legacy-TXID gematcht: `{m['unique_unmatched_by_legacy_tx_id_count']}`",
        f"- Gematchte eindeutige Menge: `{m['unique_matched_deposit_total_hnt']}` HNT",
        f"- Nicht gematchte eindeutige Menge: `{m['unique_unmatched_deposit_total_hnt']}` HNT",
        "",
        "## Helium Legacy Raw",
        "",
    ]
    legacy_summary = audit["legacy_raw_flow_summary"]
    lines += [
        f"- Legacy-Raw-Transfers: `{legacy_summary['legacy_raw_transfer_count']}`",
        f"- Wallets top: `{legacy_summary['known_wallets_top']}`",
        f"- Treffer direkte Binance-HNT-Deposit-Adresse: `{len(legacy_summary['known_binance_deposit_address_hits'])}`",
        "",
        "## HeliumGeek Einheitenpruefung",
        "",
    ]
    h = audit["heliumgeek_quantity_issue_summary"]
    lines += [
        f"- Auffaellige Rows: `{h['issue_count']}`",
        f"- Payload-Totals: `{h['payload_totals']}`",
        f"- Raw-Display-Totals: `{h['display_totals_from_raw']}`",
        f"- Bewertung: {h['interpretation']}",
        "",
        "## Solana / Solscan nach Migration",
        "",
    ]
    s = audit["solana_post_migration_summary"]
    lines += [
        f"- Effective Solana-Helium Events: `{s['effective_solana_helium_event_count']}`",
        f"- Effective nach Quelle: `{s['effective_solana_helium_by_source']}`",
        f"- Effective nach Asset: `{s['effective_solana_helium_by_asset']}`",
        f"- Cached Solscan Helium Transfers: `{s['cached_solscan_helium_transfer_count']}`",
        f"- Cached Solscan nach Symbol: `{s['cached_solscan_by_symbol']}`",
        "",
        "## Balance Status",
        "",
    ]
    balance = audit["balance_status"]
    lines.append(f"- Negative Endbestaende gesamt: `{balance.get('negative_final_assets')}`")
    for asset, row in balance.get("assets", {}).items():
        first_negative = row.get("first_negative")
        lines.append(f"- `{asset}` final `{row.get('final_balance')}`, erster negativer Bruch: `{first_negative}`")
    lines += [
        "",
        "## Bewertung",
        "",
        *[f"- {line}" for line in audit["interpretation"]],
        "",
        "## Ergebnis",
        "",
        "Nein, die harte Aussage `alles komplett sauber ausser Helium-Blockchain` waere noch zu stark. Die Binance-Seite ist fuer HNT gut belegt; die offene Stelle ist die vollstaendige unabhaengige Legacy-L1-Gegenpruefung und das HeliumGeek-Einheitenproblem. Solscan deckt erst die Solana-Phase nach Migration ab.",
    ]
    return "\n".join(lines) + "\n"


def compact_summary(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "helium_effective_events": audit["source_year_counts"]["event_count"],
        "binance_hnt_deposit_rows": audit["binance_hnt_summary"]["deposit_row_count"],
        "binance_hnt_unique_deposit_txs": audit["binance_hnt_summary"]["unique_deposit_tx_count"],
        "binance_hnt_deposit_legacy_matches": audit["binance_hnt_deposit_legacy_matches"],
        "heliumgeek_issue_count": audit["heliumgeek_quantity_issue_summary"]["issue_count"],
        "solscan_helium_transfers": audit["solana_post_migration_summary"]["cached_solscan_helium_transfer_count"],
    }


def payload_of(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def raw_of(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("raw_row")
    return raw if isinstance(raw, dict) else {}


def canonical_asset(payload: dict[str, Any]) -> str:
    return str(_payload_asset_canonical_symbol(payload) or payload.get("asset") or "").upper().strip()


def qty(payload: dict[str, Any]) -> Decimal:
    for key in ("quantity", "qty", "amount", "size"):
        value = dec(payload.get(key))
        if value != 0:
            return abs(value)
    return Decimal("0")


def signed_qty(payload: dict[str, Any]) -> Decimal:
    value = qty(payload)
    side = str(payload.get("side") or "").lower()
    if side in {"out", "sell", "sell_base", "buy_quote", "fee"}:
        return -value
    return value


def sum_qty(events: list[dict[str, Any]]) -> str:
    return plain(sum(qty(payload_of(event)) for event in events))


def signed_sum(events: list[dict[str, Any]]) -> str:
    return plain(sum(signed_qty(payload_of(event)) for event in events))


def address_counts(events: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for event in events:
        raw = raw_of(payload_of(event))
        address = str(raw.get("Address") or raw.get("address") or "")
        if address:
            counter[address] += 1
    return counter


def unique_by_tx(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for event in sorted(events, key=lambda row: (str(payload_of(row).get("timestamp_utc") or ""), str(row.get("unique_event_id") or ""))):
        tx_id = base_tx(str(payload_of(event).get("tx_id") or ""))
        key = tx_id or str(event.get("unique_event_id") or "")
        if key in seen:
            continue
        seen.add(key)
        result.append(event)
    return result


def unique_match_by_tx(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in matches:
        key = item.get("base_tx") or str(item["deposit"].get("unique_event_id") or "")
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def first_ts(events: list[dict[str, Any]]) -> str:
    return min((str(payload_of(event).get("timestamp_utc") or "") for event in events), default="")


def last_ts(events: list[dict[str, Any]]) -> str:
    return max((str(payload_of(event).get("timestamp_utc") or "") for event in events), default="")


def slim_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = payload_of(event)
    raw = raw_of(payload)
    return {
        "event_id": str(event.get("unique_event_id") or ""),
        "timestamp_utc": str(payload.get("timestamp_utc") or ""),
        "source": str(payload.get("source") or ""),
        "event_type": str(payload.get("event_type") or ""),
        "side": str(payload.get("side") or ""),
        "asset": canonical_asset(payload),
        "quantity": str(payload.get("quantity") or ""),
        "tx_id": str(payload.get("tx_id") or ""),
        "address": str(raw.get("Address") or raw.get("address") or ""),
        "payer": str(raw.get("payer") or ""),
        "payee": str(raw.get("payee") or ""),
    }


def heliumgeek_display_quantity(raw: dict[str, Any], asset: str) -> Decimal:
    mapping = {
        "HNT": ("HNT Token", "HNT Tokens"),
        "IOT": ("IOT Token", "IOT Tokens"),
        "MOBILE": ("MOBILE Token", "MOBILE Tokens"),
    }
    token_key, amount_key = mapping.get(asset, ("", ""))
    if token_key and str(raw.get(token_key) or "").upper().strip() == asset:
        return abs(dec(raw.get(amount_key)))
    return Decimal("0")


def base_tx(value: str) -> str:
    value = value.strip()
    if "+" in value:
        value = value.split("+", 1)[0]
    return value


def dec(value: Any) -> Decimal:
    try:
        text = str(value or "").strip().replace(",", ".")
        return Decimal(text) if text else Decimal("0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Decimal) -> str:
    return value.normalize().to_eng_string() if value else "0"


if __name__ == "__main__":
    main()
