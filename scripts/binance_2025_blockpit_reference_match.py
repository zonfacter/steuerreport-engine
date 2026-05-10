#!/usr/bin/env python3
"""Match Binance 2025 Blockpit reference rows against Binance primary rows."""

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

from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

JSON_PATH = ROOT / "var" / "binance_2025_blockpit_reference_match_2026-05-08.json"
DOC_PATH = ROOT / "docs" / "62_BINANCE_2025_BLOCKPIT_REFERENCE_MATCH_2026-05-08.md"
YEAR = "2025"
AMOUNT_TOLERANCE = Decimal("0.00000001")
TIME_TOLERANCE_SECONDS = 120


def main() -> None:
    raw_events = STORE.list_raw_events()
    reviewed, _summary = apply_review_actions(raw_events)
    effective, override_count = apply_tax_event_overrides(reviewed)
    rows = collect_rows(effective)
    primary = [row for row in rows if row["source"] in {"binance", "binance_api"}]
    reference = [row for row in rows if row["source"] == "blockpit"]
    direct_matches, group_matches, unmatched = match_reference(primary, reference)
    safe_ids = sorted({event_id for match in direct_matches + group_matches for event_id in match["reference_event_ids"]})
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": "Binance 2025 Blockpit reference rows vs Binance primary rows",
        "override_count": override_count,
        "primary_count": len(primary),
        "reference_count": len(reference),
        "direct_match_count": len(direct_matches),
        "group_match_count": len(group_matches),
        "safe_exclusion_candidate_count": len(safe_ids),
        "unmatched_count": len(unmatched),
        "reference_type_counts": dict(Counter(row["event_type"] for row in reference)),
        "unmatched_type_counts": dict(Counter(row["event_type"] for row in unmatched)),
        "direct_matches": direct_matches,
        "group_matches": group_matches,
        "unmatched_reference_rows": unmatched,
        "safe_exclusion_candidate_event_ids": safe_ids,
        "recommendation": (
            "Matched Blockpit Binance rows are reference duplicates and can be excluded with reason reference_import_only. "
            "Unmatched Earn Reward rows should remain as reference evidence until Binance Earn primary export/API is available."
        ),
    }
    JSON_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    DOC_PATH.write_text(render(audit), encoding="utf-8")
    print(
        json.dumps(
            {
                "json": str(JSON_PATH),
                "doc": str(DOC_PATH),
                "primary": len(primary),
                "reference": len(reference),
                "direct_matches": len(direct_matches),
                "group_matches": len(group_matches),
                "safe_candidates": len(safe_ids),
                "unmatched": len(unmatched),
            },
            indent=2,
        )
    )


def collect_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if not ts.startswith(YEAR):
            continue
        source = str(payload.get("source") or "")
        if source == "blockpit":
            if str(raw.get("Integration Name") or raw.get("Source Name") or "").lower() != "binance":
                continue
        elif source not in {"binance", "binance_api"}:
            continue
        row = normalize_row(event, payload, raw)
        if row:
            rows.append(row)
    rows.sort(key=lambda row: (row["timestamp_utc"], row["source"], row["event_id"]))
    return rows


def normalize_row(event: dict[str, Any], payload: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    source = str(payload.get("source") or "")
    side = str(payload.get("side") or "").lower()
    qty = dec(payload.get("quantity"))
    amount = -abs(qty) if side in {"out", "sell"} else abs(qty)
    source_tx_id = str(payload.get("tx_id") or raw.get("Transaction ID") or raw.get("Trx. ID (optional)") or raw.get("txId") or "")
    if source == "blockpit":
        source_tx_id = str(raw.get("Trx. ID (optional)") or "")
    return {
        "event_id": str(event.get("unique_event_id") or ""),
        "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
        "epoch_seconds": parse_epoch(str(payload.get("timestamp_utc") or payload.get("timestamp") or "")),
        "source": source,
        "event_type": str(payload.get("event_type") or ""),
        "asset": str(payload.get("asset") or raw.get("Incoming Asset") or raw.get("Outgoing Asset") or "").upper(),
        "side": side,
        "amount": str(amount),
        "fee_amount": str(fee_amount(payload)),
        "source_tx_id": source_tx_id,
        "normalized_tx_id": normalize_tx_id(source_tx_id),
        "comment": str(raw.get("Comment (optional)") or raw.get("Method") or ""),
    }


def match_reference(primary: list[dict[str, Any]], reference: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    primary_by_key = defaultdict(list)
    for row in primary:
        if row["normalized_tx_id"]:
            primary_by_key[(row["normalized_tx_id"], row["asset"])].append(row)

    used_refs: set[str] = set()
    direct_matches: list[dict[str, Any]] = []
    for ref in reference:
        candidates = primary_by_key.get((ref["normalized_tx_id"], ref["asset"]), [])
        for prim in candidates:
            if abs(dec(ref["amount"]) - dec(prim["amount"])) <= AMOUNT_TOLERANCE:
                direct_matches.append(match_payload([ref], prim, "tx_id_asset_amount"))
                used_refs.add(ref["event_id"])
                break

    for ref in reference:
        if ref["event_id"] in used_refs or ref["event_type"] != "fee":
            continue
        candidates = [
            prim
            for prim in primary
            if prim["asset"] == ref["asset"]
            and abs(dec(prim["fee_amount"]) - dec(ref["amount"])) <= AMOUNT_TOLERANCE
            and abs(int(prim["epoch_seconds"]) - int(ref["epoch_seconds"])) <= TIME_TOLERANCE_SECONDS
        ]
        if not candidates:
            continue
        candidates.sort(key=lambda prim: (abs(int(prim["epoch_seconds"]) - int(ref["epoch_seconds"])), prim["event_id"]))
        direct_matches.append(match_payload([ref], candidates[0], "time_asset_primary_fee_component"))
        used_refs.add(ref["event_id"])

    group_matches: list[dict[str, Any]] = []
    refs_by_tx_asset = defaultdict(list)
    for ref in reference:
        if ref["event_id"] not in used_refs and ref["normalized_tx_id"]:
            refs_by_tx_asset[(ref["normalized_tx_id"], ref["asset"])].append(ref)
    for key, refs in refs_by_tx_asset.items():
        candidates = primary_by_key.get(key, [])
        if not candidates:
            continue
        group_amount = sum(dec(ref["amount"]) for ref in refs)
        for prim in candidates:
            if abs(group_amount - dec(prim["amount"])) <= AMOUNT_TOLERANCE:
                group_matches.append(match_payload(refs, prim, "tx_id_asset_group_net_amount"))
                used_refs.update(ref["event_id"] for ref in refs)
                break

    unmatched = [ref for ref in reference if ref["event_id"] not in used_refs]
    return direct_matches, group_matches, unmatched


def match_payload(refs: list[dict[str, Any]], prim: dict[str, Any], basis: str) -> dict[str, Any]:
    return {
        "reference_event_ids": [ref["event_id"] for ref in refs],
        "primary_event_id": prim["event_id"],
        "timestamp_utc": refs[0]["timestamp_utc"],
        "primary_timestamp_utc": prim["timestamp_utc"],
        "asset": prim["asset"],
        "reference_net_amount": str(sum(dec(ref["amount"]) for ref in refs)),
        "primary_amount": prim["amount"],
        "source_tx_id": refs[0]["source_tx_id"],
        "primary_tx_id": prim["source_tx_id"],
        "reference_event_types": [ref["event_type"] for ref in refs],
        "basis": basis,
    }


def render(audit: dict[str, Any]) -> str:
    lines = [
        "# Binance 2025 Blockpit Reference Match - 2026-05-08",
        "",
        "## Summary",
        "",
        f"- JSON: `{JSON_PATH}`",
        f"- Primary rows: `{audit['primary_count']}`",
        f"- Blockpit reference rows: `{audit['reference_count']}`",
        f"- Direct matches: `{audit['direct_match_count']}`",
        f"- Group matches: `{audit['group_match_count']}`",
        f"- Safe exclusion candidate events: `{audit['safe_exclusion_candidate_count']}`",
        f"- Unmatched reference rows: `{audit['unmatched_count']}`",
        f"- Reference type counts: `{audit['reference_type_counts']}`",
        f"- Unmatched type counts: `{audit['unmatched_type_counts']}`",
        "",
        "## Safe Match Groups",
        "",
    ]
    for match in audit["direct_matches"] + audit["group_matches"]:
        lines.append(
            f"- `{match['timestamp_utc']}` `{match['asset']}` ref `{match['reference_net_amount']}` "
            f"primary `{match['primary_amount']}` basis `{match['basis']}` ref_events `{len(match['reference_event_ids'])}` tx `{match['source_tx_id']}`"
        )
    lines += ["", "## Unmatched Reference Rows", ""]
    for row in audit["unmatched_reference_rows"]:
        lines.append(
            f"- `{row['timestamp_utc']}` `{row['event_type']}` `{row['asset']}` amount `{row['amount']}` comment `{row['comment']}` event `{row['event_id']}`"
        )
    lines += ["", "## Empfehlung", "", audit["recommendation"], ""]
    lines += [
        "Dieses Matching-Script schreibt selbst keine Overrides. Die geprüften Kandidaten wurden separat über `scripts/apply_binance_2025_blockpit_reference_exclusions.py` als `reference_import_only` ausgeschlossen.",
        "",
    ]
    return "\n".join(lines)


def normalize_tx_id(value: str) -> str:
    text = str(value or "").strip()
    if text.isdigit():
        return text.lstrip("0") or "0"
    return text


def fee_amount(payload: dict[str, Any]) -> Decimal:
    fee = dec(payload.get("fee"))
    if fee == Decimal("0"):
        return Decimal("0")
    asset = str(payload.get("asset") or "").upper()
    fee_asset = str(payload.get("fee_asset") or "").upper()
    if fee_asset and fee_asset != asset:
        return Decimal("0")
    return -abs(fee)


def parse_epoch(ts: str) -> int:
    try:
        return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


if __name__ == "__main__":
    main()
