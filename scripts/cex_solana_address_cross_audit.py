#!/usr/bin/env python3
"""Cross-audit Solana transfer counterparties against known Binance/Bitget addresses."""

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

from tax_engine.connectors.token_metadata import resolve_token_metadata
from tax_engine.ingestion.store import STORE

CREATED_DATE = "2026-05-09"
JSON_PATH = ROOT / "var" / f"cex_solana_address_cross_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"93_CEX_SOLANA_ADDRESS_CROSS_AUDIT_{CREATED_DATE}.md"
SOL_MINTS = {
    "So11111111111111111111111111111111111111111".upper(): "SOL",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB".upper(): "USDT",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v".upper(): "USDC",
    "hntyVP6YFm1Hg25TN9WGLqM12b8TQmcknKrdu1oxWux".upper(): "HNT",
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN".upper(): "JUP",
}
ADDRESS_KEYS = (
    "address",
    "Address",
    "toAddress",
    "fromAddress",
    "SourceAddress",
    "destination",
    "recipient",
    "withdrawAddress",
)
TXID_KEYS = ("txId", "TXID", "txid", "hash", "transaction_id", "transactionId")
TRANSFER_EVENT_MARKERS = ("deposit", "withdraw", "withdrawal", "automatic_withdrawal")


def main() -> None:
    raw_events = STORE.list_raw_events()
    cex_events = collect_cex_events(raw_events)
    address_book = build_address_book(cex_events)
    solscan_transfers = load_solscan_transfers()
    solscan_matches = match_solscan_transfers(solscan_transfers, address_book, cex_events)
    rpc_counterparties = collect_solana_rpc_counterparties(raw_events)
    owner_matches = match_rpc_counterparties(rpc_counterparties, address_book)
    discovered_clusters = summarize_discovered_clusters(rpc_counterparties)

    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": "Solscan/Solana counterparties vs known Binance and Bitget transfer addresses",
        "source_counts": {
            "raw_event_count": len(raw_events),
            "cex_transfer_event_count": len(cex_events),
            "known_address_count": len(address_book),
            "solscan_account_transfer_count": len(solscan_transfers),
            "solana_rpc_counterparty_count": len(rpc_counterparties),
        },
        "address_book_summary": summarize_address_book(address_book),
        "cex_transfer_summary": summarize_cex_events(cex_events),
        "solscan_match_summary": summarize_solscan_matches(solscan_matches),
        "owner_match_summary": summarize_owner_matches(owner_matches),
        "top_discovered_owner_clusters": discovered_clusters[:30],
        "solscan_matches": solscan_matches[:1000],
        "owner_matches": owner_matches[:1000],
        "interpretation": build_interpretation(solscan_matches, owner_matches, discovered_clusters),
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": audit["source_counts"]}, indent=2, ensure_ascii=False))


def collect_cex_events(raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in raw_events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        source = str(payload.get("source") or "").lower()
        raw_source = str(raw.get("Source Name") or raw.get("Integration Name") or "").lower()
        exchange = classify_exchange(source, raw_source)
        if exchange not in {"binance", "bitget"}:
            continue
        event_type = str(payload.get("event_type") or "").lower()
        if not any(marker in event_type for marker in TRANSFER_EVENT_MARKERS):
            continue
        addresses = extract_addresses(raw)
        tx_ids = extract_txids(payload, raw)
        if not addresses and not tx_ids:
            continue
        rows.append(
            {
                "event_id": str(event.get("unique_event_id") or ""),
                "exchange": exchange,
                "source": source,
                "timestamp_utc": str(payload.get("timestamp_utc") or ""),
                "event_type": event_type,
                "side": str(payload.get("side") or "").lower(),
                "asset": str(payload.get("asset") or raw.get("coin") or "").upper(),
                "quantity": str(payload.get("quantity") or ""),
                "network": str(payload.get("network") or raw.get("network") or raw.get("Network") or raw.get("chain") or raw.get("chainName") or ""),
                "addresses": addresses,
                "tx_ids": tx_ids,
            }
        )
    return sorted(rows, key=lambda row: (row["timestamp_utc"], row["exchange"], row["event_id"]))


def classify_exchange(source: str, raw_source: str) -> str:
    text = f"{source} {raw_source}".lower()
    if "bitget" in text:
        return "bitget"
    if "binance" in text:
        return "binance"
    return ""


def extract_addresses(raw: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for key in ADDRESS_KEYS:
        value = str(raw.get(key) or "").strip()
        if not looks_like_address(value):
            continue
        dedupe = (key, value)
        if dedupe in seen:
            continue
        seen.add(dedupe)
        result.append({"field": key, "address": value})
    return result


def extract_txids(payload: dict[str, Any], raw: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for value in [payload.get("tx_id"), *(raw.get(key) for key in TXID_KEYS)]:
        text = str(value or "").strip()
        if len(text) >= 16 and text not in values:
            values.append(text)
    return values


def looks_like_address(value: str) -> bool:
    if not value or len(value) < 20:
        return False
    if any(char.isspace() for char in value):
        return False
    return True


def build_address_book(cex_events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    book: dict[str, dict[str, Any]] = {}
    for row in cex_events:
        for address_item in row["addresses"]:
            address = address_item["address"]
            entry = book.setdefault(
                address,
                {
                    "address": address,
                    "exchanges": set(),
                    "fields": Counter(),
                    "roles": Counter(),
                    "event_count": 0,
                    "first_seen_utc": "",
                    "last_seen_utc": "",
                    "sample_events": [],
                },
            )
            entry["exchanges"].add(row["exchange"])
            entry["fields"][address_item["field"]] += 1
            entry["roles"][address_role(row, address_item["field"])] += 1
            entry["event_count"] += 1
            ts = row["timestamp_utc"]
            entry["first_seen_utc"] = min(filter(None, [entry["first_seen_utc"], ts])) if entry["first_seen_utc"] else ts
            entry["last_seen_utc"] = max(entry["last_seen_utc"], ts)
            if len(entry["sample_events"]) < 5:
                entry["sample_events"].append(slim_cex_event(row))
    for entry in book.values():
        entry["exchanges"] = sorted(entry["exchanges"])
        entry["fields"] = dict(entry["fields"].most_common())
        entry["roles"] = dict(entry["roles"].most_common())
    return book


def address_role(row: dict[str, Any], field: str) -> str:
    event_type = str(row.get("event_type") or "").lower()
    side = str(row.get("side") or "").lower()
    normalized_field = str(field or "").lower()
    if normalized_field in {"fromaddress", "sourceaddress"}:
        return "cex_hot_or_source_address"
    if "deposit" in event_type and side == "in":
        return "cex_deposit_address"
    if "withdraw" in event_type and side == "out":
        return "user_or_external_destination_address"
    return "transfer_related_address"


def load_solscan_transfers() -> list[dict[str, Any]]:
    db_path = Path("/root/.local/share/steuerreport/steuerreport.db")
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT wallet_address, signature, block_time_utc, flow, activity_type, token_address,
                   token_decimals, amount, value_usd, from_address, to_address, raw_json
            FROM solscan_account_transfers
            ORDER BY block_time_utc ASC, signature ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def match_solscan_transfers(
    transfers: list[dict[str, Any]],
    address_book: dict[str, dict[str, Any]],
    cex_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cex_by_txid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in cex_events:
        for tx_id in row["tx_ids"]:
            cex_by_txid[tx_id].append(row)

    matches: list[dict[str, Any]] = []
    for transfer in transfers:
        counterparty = str(transfer.get("to_address") if transfer.get("flow") == "out" else transfer.get("from_address") or "").strip()
        signature = str(transfer.get("signature") or "").strip()
        address_entry = address_book.get(counterparty)
        signature_events = cex_by_txid.get(signature, [])
        if address_entry is None and not signature_events:
            continue
        matches.append(
            {
                "match_type": match_type(address_entry is not None, bool(signature_events)),
                "signature": signature,
                "timestamp_utc": str(transfer.get("block_time_utc") or ""),
                "flow": str(transfer.get("flow") or ""),
                "activity_type": str(transfer.get("activity_type") or ""),
                "token_address": str(transfer.get("token_address") or ""),
                "symbol": symbol_for_token(str(transfer.get("token_address") or "")),
                "amount_raw": str(transfer.get("amount") or ""),
                "amount_display": amount_display(transfer),
                "counterparty_address": counterparty,
                "known_address": address_entry,
                "known_address_roles": address_entry.get("roles", {}) if address_entry else {},
                "signature_cex_events": [slim_cex_event(row) for row in signature_events[:10]],
            }
        )
    return matches


def collect_solana_rpc_counterparties(raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for event in raw_events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if str(payload.get("source") or "") != "solana_rpc":
            continue
        if str(payload.get("event_type") or "").lower() != "token_transfer":
            continue
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        signature = str(payload.get("tx_id") or "")
        side = str(payload.get("side") or "").lower()
        instructions = parsed_instructions(raw)
        owner_by_account = destination_owner_index(instructions)
        transfers = transfer_checked_items(instructions)
        for transfer in transfers:
            mint = str(transfer.get("mint") or "").upper()
            asset = str(payload.get("asset") or "").upper()
            if mint and asset and mint != asset:
                # payload asset is sometimes already a symbol; keep only obvious mismatches out of strict matching.
                if symbol_for_token(mint) == asset:
                    pass
                else:
                    continue
            source_account = str(transfer.get("source") or "")
            destination_account = str(transfer.get("destination") or "")
            counterpart_account = destination_account if side == "out" else source_account
            owner = owner_by_account.get(counterpart_account, "")
            key = (signature, side, asset or mint, counterpart_account)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "event_id": str(event.get("unique_event_id") or ""),
                    "signature": signature,
                    "timestamp_utc": str(payload.get("timestamp_utc") or ""),
                    "side": side,
                    "asset": asset or mint,
                    "symbol": symbol_for_token(asset or mint),
                    "quantity": str(payload.get("quantity") or ""),
                    "wallet_address": str(payload.get("wallet_address") or ""),
                    "counterparty_token_account": counterpart_account,
                    "counterparty_owner": owner,
                    "mint": mint,
                }
            )
    return sorted(rows, key=lambda row: (row["timestamp_utc"], row["signature"], row["asset"]))


def parsed_instructions(raw: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    tx = raw.get("transaction") if isinstance(raw.get("transaction"), dict) else {}
    msg = tx.get("message") if isinstance(tx.get("message"), dict) else {}
    ins = msg.get("instructions")
    if isinstance(ins, list):
        result.extend(item for item in ins if isinstance(item, dict))
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    inner = meta.get("innerInstructions")
    if isinstance(inner, list):
        for group in inner:
            if not isinstance(group, dict):
                continue
            group_ins = group.get("instructions")
            if isinstance(group_ins, list):
                result.extend(item for item in group_ins if isinstance(item, dict))
    return result


def destination_owner_index(instructions: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for instruction in instructions:
        parsed = instruction.get("parsed") if isinstance(instruction.get("parsed"), dict) else {}
        info = parsed.get("info") if isinstance(parsed.get("info"), dict) else {}
        if str(parsed.get("type") or "") in {"initializeAccount3", "initializeAccount"}:
            account = str(info.get("account") or "")
            owner = str(info.get("owner") or "")
            if account and owner:
                result[account] = owner
    return result


def transfer_checked_items(instructions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for instruction in instructions:
        parsed = instruction.get("parsed") if isinstance(instruction.get("parsed"), dict) else {}
        if str(parsed.get("type") or "") not in {"transferChecked", "transfer"}:
            continue
        info = parsed.get("info") if isinstance(parsed.get("info"), dict) else {}
        result.append(info)
    return result


def match_rpc_counterparties(
    counterparties: list[dict[str, Any]],
    address_book: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for row in counterparties:
        token_account_entry = address_book.get(row["counterparty_token_account"])
        owner_entry = address_book.get(row["counterparty_owner"]) if row["counterparty_owner"] else None
        if token_account_entry is None and owner_entry is None:
            continue
        matches.append(
            {
                **row,
                "match_type": match_type(token_account_entry is not None, owner_entry is not None),
                "token_account_known_address": token_account_entry,
                "owner_known_address": owner_entry,
            }
        )
    return matches


def summarize_discovered_clusters(counterparties: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clusters: dict[str, dict[str, Any]] = {}
    for row in counterparties:
        key = row.get("counterparty_owner") or row.get("counterparty_token_account") or ""
        if not key:
            continue
        entry = clusters.setdefault(
            key,
            {
                "counterparty": key,
                "signature_count": 0,
                "transfer_count": 0,
                "first_timestamp_utc": "",
                "last_timestamp_utc": "",
                "asset_counts": Counter(),
                "asset_totals": defaultdict(Decimal),
                "sample_signatures": [],
            },
        )
        entry["transfer_count"] += 1
        sig = row["signature"]
        if sig not in entry["sample_signatures"] and len(entry["sample_signatures"]) < 10:
            entry["sample_signatures"].append(sig)
        ts = row["timestamp_utc"]
        entry["first_timestamp_utc"] = min(filter(None, [entry["first_timestamp_utc"], ts])) if entry["first_timestamp_utc"] else ts
        entry["last_timestamp_utc"] = max(entry["last_timestamp_utc"], ts)
        symbol = row.get("symbol") or row.get("asset") or "unknown"
        entry["asset_counts"][symbol] += 1
        entry["asset_totals"][symbol] += dec(row.get("quantity"))
    result: list[dict[str, Any]] = []
    for entry in clusters.values():
        result.append(
            {
                "counterparty": entry["counterparty"],
                "transfer_count": entry["transfer_count"],
                "first_timestamp_utc": entry["first_timestamp_utc"],
                "last_timestamp_utc": entry["last_timestamp_utc"],
                "asset_counts": dict(entry["asset_counts"].most_common()),
                "asset_totals": {asset: value.to_eng_string() for asset, value in sorted(entry["asset_totals"].items())},
                "sample_signatures": entry["sample_signatures"],
            }
        )
    result.sort(key=lambda row: (row["transfer_count"], row["last_timestamp_utc"]), reverse=True)
    return result


def summarize_address_book(address_book: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_exchange: Counter[str] = Counter()
    by_field: Counter[str] = Counter()
    by_role: Counter[str] = Counter()
    for entry in address_book.values():
        for exchange in entry["exchanges"]:
            by_exchange[exchange] += 1
        by_field.update(entry["fields"])
        by_role.update(entry["roles"])
    return {
        "by_exchange": dict(by_exchange.most_common()),
        "by_field": dict(by_field.most_common()),
        "by_role": dict(by_role.most_common()),
        "top_addresses": [
            {
                "address": entry["address"],
                "exchanges": entry["exchanges"],
                "event_count": entry["event_count"],
                "fields": entry["fields"],
                "roles": entry["roles"],
                "first_seen_utc": entry["first_seen_utc"],
                "last_seen_utc": entry["last_seen_utc"],
            }
            for entry in sorted(address_book.values(), key=lambda item: item["event_count"], reverse=True)[:30]
        ],
    }


def summarize_cex_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "by_exchange": dict(Counter(row["exchange"] for row in events).most_common()),
        "by_exchange_event_type": dict(Counter(f"{row['exchange']}:{row['event_type']}" for row in events).most_common()),
        "by_network": dict(Counter(str(row.get("network") or "unknown") for row in events).most_common(30)),
    }


def summarize_solscan_matches(matches: list[dict[str, Any]]) -> dict[str, Any]:
    role_counter: Counter[str] = Counter()
    cex_target_counter: Counter[str] = Counter()
    for row in matches:
        roles = row.get("known_address_roles") if isinstance(row.get("known_address_roles"), dict) else {}
        role_counter.update(roles)
        if any(role in roles for role in ("cex_deposit_address", "cex_hot_or_source_address")):
            cex_target_counter[row["counterparty_address"]] += 1
    return {
        "count": len(matches),
        "by_match_type": dict(Counter(row["match_type"] for row in matches).most_common()),
        "by_flow": dict(Counter(row["flow"] for row in matches).most_common()),
        "by_symbol": dict(Counter(row["symbol"] for row in matches).most_common(30)),
        "by_known_address_role": dict(role_counter.most_common()),
        "cex_target_counterparties": dict(cex_target_counter.most_common(30)),
        "top_counterparties": dict(Counter(row["counterparty_address"] for row in matches).most_common(30)),
    }


def summarize_owner_matches(matches: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(matches),
        "by_match_type": dict(Counter(row["match_type"] for row in matches).most_common()),
        "by_side": dict(Counter(row["side"] for row in matches).most_common()),
        "by_symbol": dict(Counter(row["symbol"] for row in matches).most_common(30)),
    }


def build_interpretation(
    solscan_matches: list[dict[str, Any]],
    owner_matches: list[dict[str, Any]],
    discovered_clusters: list[dict[str, Any]],
) -> list[str]:
    lines = [
        f"Direkte Solscan-zu-CEX-Matches gefunden: {len(solscan_matches)}.",
        f"Solana-RPC-Owner/Token-Account-Matches gegen bekannte CEX-Adressen gefunden: {len(owner_matches)}.",
        "Der Audit trennt direkte Adressmatches, Signaturmatches und Owner-Matches, weil Solana-Token-Accounts nicht immer die eigentliche Gegenpartei-Adresse sind.",
    ]
    if discovered_clusters:
        top = discovered_clusters[0]
        lines.append(
            f"Groesster wiederkehrender Solana-Counterparty-Cluster: {top['counterparty']} mit {top['transfer_count']} Transfers "
            f"von {top['first_timestamp_utc']} bis {top['last_timestamp_utc']}."
        )
    lines.append("Naechster Schritt: bekannte CEX-Adresscluster als Evidence-Layer markieren und nur sicher gematchte Blockpit-Referenzen als reference_import_only pruefen.")
    return lines


def slim_cex_event(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": row["event_id"],
        "exchange": row["exchange"],
        "source": row["source"],
        "timestamp_utc": row["timestamp_utc"],
        "event_type": row["event_type"],
        "side": row["side"],
        "asset": row["asset"],
        "quantity": row["quantity"],
        "network": row["network"],
        "tx_ids": row["tx_ids"][:3],
    }


def match_type(address_match: bool, signature_or_owner_match: bool) -> str:
    if address_match and signature_or_owner_match:
        return "address_and_signature_or_owner"
    if address_match:
        return "address"
    return "signature_or_owner"


def symbol_for_token(token_address: str) -> str:
    token = str(token_address or "").upper()
    if token in SOL_MINTS:
        return SOL_MINTS[token]
    meta = resolve_token_metadata(token)
    symbol = str(meta.get("symbol") or "").upper()
    return symbol if symbol and symbol != token else token


def amount_display(row: dict[str, Any]) -> str:
    raw = dec(row.get("amount"))
    decimals = row.get("token_decimals")
    try:
        exp = int(decimals)
    except (TypeError, ValueError):
        return raw.to_eng_string()
    if exp < 0 or exp > 18:
        return raw.to_eng_string()
    return (raw / (Decimal(10) ** exp)).to_eng_string()


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# CEX/Solana Address Cross Audit - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Abgleich bekannter Binance-/Bitget-Transferadressen gegen lokale Solscan-Transfers und Solana-RPC-Token-Transfer-Owner.",
        "",
        "## Summary",
        "",
    ]
    for key, value in audit["source_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## CEX-Transferquellen", ""]
    for key, value in audit["cex_transfer_summary"]["by_exchange_event_type"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Adressbuch", ""]
    lines.append(f"- Rollen: `{audit['address_book_summary']['by_role']}`")
    for row in audit["address_book_summary"]["top_addresses"][:20]:
        lines.append(
            f"- `{row['address']}` exchanges `{row['exchanges']}` events `{row['event_count']}` "
            f"roles `{row['roles']}` fields `{row['fields']}` period `{row['first_seen_utc']}`..`{row['last_seen_utc']}`"
        )
    lines += ["", "## Solscan Direct/Signature Matches", ""]
    s = audit["solscan_match_summary"]
    lines.append(f"- Count: `{s['count']}`")
    lines.append(f"- Match types: `{s['by_match_type']}`")
    lines.append(f"- Flow: `{s['by_flow']}`")
    lines.append(f"- Symbols: `{s['by_symbol']}`")
    lines.append(f"- Known address roles: `{s['by_known_address_role']}`")
    lines.append(f"- CEX target counterparties: `{s['cex_target_counterparties']}`")
    lines += ["", "## Solana RPC Owner Matches", ""]
    o = audit["owner_match_summary"]
    lines.append(f"- Count: `{o['count']}`")
    lines.append(f"- Match types: `{o['by_match_type']}`")
    lines.append(f"- Sides: `{o['by_side']}`")
    lines.append(f"- Symbols: `{o['by_symbol']}`")
    lines += ["", "## Top Discovered Counterparty Clusters", ""]
    for row in audit["top_discovered_owner_clusters"][:20]:
        lines.append(
            f"- `{row['counterparty']}` transfers `{row['transfer_count']}` period "
            f"`{row['first_timestamp_utc']}`..`{row['last_timestamp_utc']}` totals `{row['asset_totals']}`"
        )
    lines += ["", "## Bewertung", ""]
    for item in audit["interpretation"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
