#!/usr/bin/env python3
"""Audit Solana transfers to the target owner derived from a known Blockpit/Solana signature."""

from __future__ import annotations

import json
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
SEED_SIGNATURE = "61gUSpVfrTHWVQj9j2Yqv9RvAYkuJ8tGhUAMqNeWnZgD9gjJfeFdis8W83UMMw4KS6j7Epvo6WNoQx89oPRWC9Nb"
JSON_PATH = ROOT / "var" / f"bitget_solana_target_address_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"92_BITGET_SOLANA_TARGET_ADDRESS_AUDIT_{CREATED_DATE}.md"
MINT_SYMBOLS = {
    "ES9VMFRZACERMJFRF4H2FYD4KCONKY11MCCE8BENWNYB": "USDT",
    "EPJFWDd5AUFQSSQEM2QN1XZYBAPC8G4WEGGKZWYTDT1V".upper(): "USDC",
}


def main() -> None:
    raw_events = STORE.list_raw_events()
    seed_events = find_events_by_signature(raw_events, SEED_SIGNATURE)
    if not seed_events:
        raise SystemExit(f"Seed signature not found: {SEED_SIGNATURE}")
    seed_detail = derive_target_from_seed(seed_events)
    target_owner = seed_detail.get("target_owner", "")
    target_token_account = seed_detail.get("target_token_account", "")
    if not target_owner:
        raise SystemExit("Could not derive target owner from seed signature.")

    owner_matches = collect_owner_matches(raw_events, target_owner=target_owner, target_token_account=target_token_account)
    signature_groups = group_signature_matches(owner_matches)
    summary = summarize(signature_groups)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "seed_signature": SEED_SIGNATURE,
        "seed_detail": seed_detail,
        "summary": summary,
        "signature_groups": signature_groups,
        "interpretation": build_interpretation(seed_detail, summary),
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": summary}, indent=2, ensure_ascii=False))


def find_events_by_signature(events: list[dict[str, Any]], signature: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        if str(payload.get("tx_id") or "") == signature or signature in json.dumps(raw, ensure_ascii=False):
            found.append(event)
    return found


def derive_target_from_seed(events: list[dict[str, Any]]) -> dict[str, Any]:
    candidates: list[dict[str, str]] = []
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        for instruction in all_instructions(raw):
            parsed = instruction.get("parsed") if isinstance(instruction, dict) else None
            info = parsed.get("info") if isinstance(parsed, dict) else None
            if not isinstance(info, dict):
                continue
            if parsed.get("type") == "initializeAccount3":
                candidates.append(
                    {
                        "target_token_account": str(info.get("account") or ""),
                        "target_owner": str(info.get("owner") or ""),
                        "mint": str(info.get("mint") or ""),
                        "basis": "initializeAccount3",
                    }
                )
            if parsed.get("type") == "transferChecked":
                candidates.append(
                    {
                        "target_token_account": str(info.get("destination") or ""),
                        "target_owner": "",
                        "mint": str(info.get("mint") or ""),
                        "amount": str((info.get("tokenAmount") or {}).get("uiAmountString") or ""),
                        "basis": "transferChecked",
                    }
                )
    owner_by_account = {
        item["target_token_account"]: item["target_owner"]
        for item in candidates
        if item.get("basis") == "initializeAccount3" and item.get("target_token_account") and item.get("target_owner")
    }
    for item in candidates:
        if item.get("basis") == "transferChecked" and item.get("target_token_account") in owner_by_account:
            item["target_owner"] = owner_by_account[item["target_token_account"]]
            item["symbol"] = symbol_for_mint(item.get("mint", ""))
            return item
    for item in candidates:
        if item.get("target_owner"):
            item["symbol"] = symbol_for_mint(item.get("mint", ""))
            return item
    return {"candidates": candidates}


def all_instructions(raw: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    tx = raw.get("transaction") if isinstance(raw.get("transaction"), dict) else {}
    message = tx.get("message") if isinstance(tx.get("message"), dict) else {}
    instructions = message.get("instructions")
    if isinstance(instructions, list):
        result.extend(item for item in instructions if isinstance(item, dict))
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    inner = meta.get("innerInstructions")
    if isinstance(inner, list):
        for group in inner:
            if not isinstance(group, dict):
                continue
            inner_instructions = group.get("instructions")
            if isinstance(inner_instructions, list):
                result.extend(item for item in inner_instructions if isinstance(item, dict))
    return result


def collect_owner_matches(
    events: list[dict[str, Any]],
    *,
    target_owner: str,
    target_token_account: str,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        if str(payload.get("source") or "") != "solana_rpc":
            continue
        text = json.dumps(raw, ensure_ascii=False)
        if target_owner not in text and target_token_account not in text:
            continue
        side = str(payload.get("side") or "").lower()
        event_type = str(payload.get("event_type") or "").lower()
        if side != "out" or event_type != "token_transfer":
            continue
        mint = str(payload.get("asset") or "").upper()
        matches.append(
            {
                "event_id": str(event.get("unique_event_id") or ""),
                "timestamp_utc": str(payload.get("timestamp_utc") or ""),
                "tx_id": str(payload.get("tx_id") or ""),
                "asset": mint,
                "symbol": symbol_for_mint(mint),
                "quantity": str(payload.get("quantity") or ""),
                "side": side,
                "event_type": event_type,
                "wallet_address": str(payload.get("wallet_address") or ""),
                "target_owner_found": target_owner in text,
                "target_token_account_found": target_token_account in text if target_token_account else False,
            }
        )
    return sorted(matches, key=lambda row: (row["timestamp_utc"], row["tx_id"], row["asset"]))


def group_signature_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in matches:
        tx_id = row["tx_id"]
        group = grouped.setdefault(
            tx_id,
            {
                "tx_id": tx_id,
                "timestamp_utc": row["timestamp_utc"],
                "wallet_address": row["wallet_address"],
                "token_transfers": [],
            },
        )
        group["token_transfers"].append(row)
    return sorted(grouped.values(), key=lambda row: row["timestamp_utc"])


def summarize(groups: list[dict[str, Any]]) -> dict[str, Any]:
    asset_totals: defaultdict[str, Decimal] = defaultdict(Decimal)
    asset_counts: Counter[str] = Counter()
    for group in groups:
        for row in group.get("token_transfers", []):
            symbol = str(row.get("symbol") or row.get("asset") or "unknown")
            asset_totals[symbol] += dec(row.get("quantity"))
            asset_counts[symbol] += 1
    return {
        "matching_signatures": len(groups),
        "token_transfer_rows": sum(len(group.get("token_transfers", [])) for group in groups),
        "first_timestamp_utc": groups[0]["timestamp_utc"] if groups else "",
        "last_timestamp_utc": groups[-1]["timestamp_utc"] if groups else "",
        "asset_counts": dict(asset_counts.most_common()),
        "asset_totals": {asset: total.to_eng_string() for asset, total in sorted(asset_totals.items())},
    }


def build_interpretation(seed_detail: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    return [
        f"Die Seed-Signatur liefert als Ziel-Owner `{seed_detail.get('target_owner')}` und Token-Account `{seed_detail.get('target_token_account')}`.",
        f"Lokal wurden `{summary['matching_signatures']}` Signaturen mit ausgehenden Token-Transfers zu diesem Owner gefunden.",
        "Diese Adresse ist ein belastbarer Suchanker fuer fruehere Solana-Abfluesse Richtung Bitget/Blockpit-Zieladresse, ersetzt aber keinen CEX-internen Trade-/PnL-Export.",
        "Naechster Schritt: diese On-Chain-Outflows gegen Bitget-Deposits, Blockpit-Solana-Zeilen und spaetere Bitget-Trading-/Derivate-Referenzen clustern.",
    ]


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Bitget/Solana Target Address Audit - 2026-05-09",
        "",
        "## Seed",
        "",
        f"- Signatur: `{audit['seed_signature']}`",
        f"- Ziel-Token-Account: `{audit['seed_detail'].get('target_token_account', '')}`",
        f"- Ziel-Owner: `{audit['seed_detail'].get('target_owner', '')}`",
        f"- Mint/Symbol: `{audit['seed_detail'].get('mint', '')}` / `{audit['seed_detail'].get('symbol', '')}`",
        f"- Seed-Betrag: `{audit['seed_detail'].get('amount', '')}`",
        "",
        "## Zusammenfassung",
        "",
        f"- Matching-Signaturen: `{audit['summary']['matching_signatures']}`",
        f"- Token-Transfer-Zeilen: `{audit['summary']['token_transfer_rows']}`",
        f"- Zeitraum: `{audit['summary']['first_timestamp_utc']}` bis `{audit['summary']['last_timestamp_utc']}`",
        f"- Asset-Totals: `{audit['summary']['asset_totals']}`",
        "",
        "## Treffer",
        "",
    ]
    for group in audit["signature_groups"]:
        transfers = ", ".join(
            f"{row['quantity']} {row['symbol']}" for row in group.get("token_transfers", [])
        )
        lines.append(f"- `{group['timestamp_utc']}` `{transfers}` tx `{group['tx_id']}`")
    lines += ["", "## Bewertung", ""]
    for item in audit["interpretation"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def symbol_for_mint(value: str) -> str:
    mint = str(value or "").upper()
    if mint in MINT_SYMBOLS:
        return MINT_SYMBOLS[mint]
    meta = resolve_token_metadata(mint)
    symbol = str(meta.get("symbol") or "").upper()
    return symbol if symbol and symbol != mint else mint


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


if __name__ == "__main__":
    main()
