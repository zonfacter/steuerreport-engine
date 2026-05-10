#!/usr/bin/env python3
"""Match Blockpit reference rows against Bitget primary rows in the liquidation window."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

JSON_PATH = ROOT / "var" / "bitget_blockpit_reference_match_2026-05-08.json"
DOC_PATH = ROOT / "docs" / "61_BITGET_BLOCKPIT_REFERENCE_MATCH_2026-05-08.md"
START_DAY = "2025-02-20"
END_DAY = "2025-03-05"
TIME_TOLERANCE_SECONDS = 120
AMOUNT_TOLERANCE = Decimal("0.00000001")


def main() -> None:
    raw_events = STORE.list_raw_events()
    reviewed, _summary = apply_review_actions(raw_events)
    effective, override_count = apply_tax_event_overrides(reviewed)
    effective_event_ids = {str(event.get("unique_event_id") or "") for event in effective}

    raw_rows = collect_bitget_window(reviewed)
    effective_rows = collect_bitget_window(effective)
    primary = [row for row in raw_rows if row["source"] == "bitget_tax_api"]
    reference = [row for row in raw_rows if row["source"] == "blockpit"]
    matches, unmatched = match_rows(primary, reference)
    annotate_effective_status(matches, unmatched, effective_event_ids)
    effective_reference = [row for row in effective_rows if row["source"] == "blockpit"]
    effective_reference_ids = {row["event_id"] for row in effective_reference}
    effective_matched = [row for row in matches if row["reference_event_id"] in effective_reference_ids]
    effective_unmatched = [row for row in unmatched if row["event_id"] in effective_reference_ids]
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": f"Blockpit reference rows vs Bitget primary rows {START_DAY}..{END_DAY}",
        "view_note": (
            "Raw/reviewed counts are before tax_event_overrides so duplicate reference rows remain visible. "
            "Effective counts are after existing tax_event_overrides and represent rows still active for tax processing."
        ),
        "matching_rule": {
            "same_asset": True,
            "same_signed_balance_effect": True,
            "time_tolerance_seconds": TIME_TOLERANCE_SECONDS,
            "amount_tolerance": str(AMOUNT_TOLERANCE),
            "comment_id_base_match": True,
        },
        "primary_count": len(primary),
        "reference_count": len(reference),
        "matched_count": len(matches),
        "unmatched_count": len(unmatched),
        "override_count": override_count,
        "effective_primary_count": len([row for row in effective_rows if row["source"] == "bitget_tax_api"]),
        "effective_reference_count": len(effective_reference),
        "effective_matched_reference_count": len(effective_matched),
        "effective_unmatched_reference_count": len(effective_unmatched),
        "matched_basis_counts": dict(Counter(row["match_basis"] for row in matches)),
        "effective_unmatched_type_counts": dict(Counter(row["event_type"] for row in effective_unmatched)),
        "matches": matches,
        "unmatched_reference_rows": unmatched,
        "effective_matched_reference_rows": effective_matched,
        "effective_unmatched_reference_rows": effective_unmatched,
        "safe_exclusion_candidate_event_ids": [row["reference_event_id"] for row in effective_matched],
        "recommendation": (
            "Only effective matched Blockpit rows are current exclusion candidates. Raw matched rows that are no longer effective "
            "are already excluded or otherwise overridden. Effective unmatched rows must remain under review."
        ),
    }
    JSON_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    DOC_PATH.write_text(render(audit), encoding="utf-8")
    print(
        json.dumps(
            {
                "json": str(JSON_PATH),
                "doc": str(DOC_PATH),
                "raw_matched": len(matches),
                "raw_unmatched": len(unmatched),
                "effective_reference": len(effective_reference),
                "effective_matched": len(effective_matched),
                "effective_unmatched": len(effective_unmatched),
            },
            indent=2,
        )
    )


def collect_bitget_window(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if not (START_DAY <= ts[:10] <= END_DAY):
            continue
        text = " ".join([str(payload.get("source") or ""), str(payload.get("event_type") or ""), json.dumps(raw, ensure_ascii=False)]).lower()
        if "bitget" not in text:
            continue
        source = str(payload.get("source") or "")
        if source not in {"bitget_tax_api", "blockpit"}:
            continue
        row = normalize_row(event, payload, raw)
        if row:
            rows.append(row)
    rows.sort(key=lambda row: (row["timestamp_utc"], row["source"], row["event_id"]))
    return rows


def normalize_row(event: dict[str, Any], payload: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any] | None:
    ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    source = str(payload.get("source") or "")
    asset = str(payload.get("asset") or raw.get("coin") or raw.get("Outgoing Asset") or raw.get("Incoming Asset") or "").upper()
    event_type = str(payload.get("event_type") or "")
    if source == "bitget_tax_api":
        gross = dec(raw.get("amount") if "amount" in raw else signed_from_payload(payload))
        fee = dec(raw.get("fee"))
        effect = gross + fee
        business = str(raw.get("businessType") or raw.get("spotTaxType") or "")
        symbol = str(raw.get("symbol") or "")
        primary_id = str(raw.get("billId") or raw.get("id") or raw.get("bizOrderId") or "")
    else:
        qty = signed_from_payload(payload)
        effect = qty
        fee = Decimal("0")
        business = str(raw.get("Comment (optional)") or "")
        symbol = extract_symbol(business)
        primary_id = str(raw.get("Trx. ID (optional)") or "")
    return {
        "event_id": str(event.get("unique_event_id") or ""),
        "timestamp_utc": ts,
        "epoch_seconds": parse_epoch(ts),
        "source": source,
        "event_type": event_type,
        "business_type": business,
        "symbol": symbol,
        "asset": asset,
        "gross_amount": str(gross if source == "bitget_tax_api" else effect),
        "fee": str(fee),
        "balance_effect": str(effect),
        "match_amount": str(effect),
        "fee_match_amount": str(fee),
        "source_tx_id": primary_id,
        "source_tx_base": primary_id[:-4] if primary_id.endswith("-fee") else primary_id,
    }


def match_rows(primary: list[dict[str, Any]], reference: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matches: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    used_primary: set[str] = set()
    for ref in reference:
        candidates = []
        for prim in primary:
            if prim["event_id"] in used_primary:
                continue
            if prim["asset"] != ref["asset"]:
                continue
            amount_basis = amount_match_basis(prim, ref)
            if amount_basis is None:
                continue
            delta_seconds = abs(int(prim["epoch_seconds"]) - int(ref["epoch_seconds"]))
            base_match = bool(ref["source_tx_base"] and ref["source_tx_base"] == prim["source_tx_base"])
            if delta_seconds <= TIME_TOLERANCE_SECONDS or base_match:
                candidates.append((0 if base_match else 1, 0 if amount_basis == "balance_effect" else 1, delta_seconds, prim, amount_basis))
        if not candidates:
            unmatched.append(ref)
            continue
        candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]["event_id"]))
        _rank, _amount_rank, delta_seconds, prim, amount_basis = candidates[0]
        used_primary.add(prim["event_id"])
        matches.append(
            {
                "reference_event_id": ref["event_id"],
                "primary_event_id": prim["event_id"],
                "reference_timestamp_utc": ref["timestamp_utc"],
                "primary_timestamp_utc": prim["timestamp_utc"],
                "delta_seconds": delta_seconds,
                "asset": ref["asset"],
                "amount": ref["match_amount"],
                "reference_comment": ref["business_type"],
                "primary_business_type": prim["business_type"],
                "reference_tx_id": ref["source_tx_id"],
                "primary_tx_id": prim["source_tx_id"],
                "amount_basis": amount_basis,
                "match_basis": match_basis_label(ref, prim, amount_basis),
            }
        )
    return matches, unmatched


def amount_match_basis(prim: dict[str, Any], ref: dict[str, Any]) -> str | None:
    ref_amount = dec(ref["match_amount"])
    if abs(dec(prim["match_amount"]) - ref_amount) <= AMOUNT_TOLERANCE:
        return "balance_effect"
    if ref["event_type"] == "derivative fee" and dec(prim["fee_match_amount"]) != Decimal("0"):
        if abs(dec(prim["fee_match_amount"]) - ref_amount) <= AMOUNT_TOLERANCE:
            return "primary_fee_component"
    return None


def match_basis_label(ref: dict[str, Any], prim: dict[str, Any], amount_basis: str) -> str:
    id_basis = "tx_id_base" if ref["source_tx_base"] and ref["source_tx_base"] == prim["source_tx_base"] else "time_amount_asset"
    if amount_basis == "primary_fee_component":
        return f"{id_basis}_fee_component"
    return id_basis


def annotate_effective_status(
    matches: list[dict[str, Any]],
    unmatched: list[dict[str, Any]],
    effective_event_ids: set[str],
) -> None:
    for row in matches:
        row["reference_effective"] = row["reference_event_id"] in effective_event_ids
        row["primary_effective"] = row["primary_event_id"] in effective_event_ids
        row["candidate_status"] = "still_effective_candidate" if row["reference_effective"] else "already_excluded_or_overridden"
    for row in unmatched:
        row["reference_effective"] = row["event_id"] in effective_event_ids
        row["candidate_status"] = "still_effective_unmatched" if row["reference_effective"] else "already_excluded_or_overridden"


def render(audit: dict[str, Any]) -> str:
    lines = [
        "# Bitget Blockpit Reference Match - 2026-05-08",
        "",
        "## Summary",
        "",
        f"- JSON: `{JSON_PATH}`",
        f"- Sicht: `{audit['view_note']}`",
        f"- Tax-Overrides angewendet in effektiver Sicht: `{audit['override_count']}`",
        f"- Raw/reviewed Primary rows: `{audit['primary_count']}`",
        f"- Raw/reviewed Blockpit reference rows: `{audit['reference_count']}`",
        f"- Raw/reviewed matched: `{audit['matched_count']}`",
        f"- Raw/reviewed unmatched: `{audit['unmatched_count']}`",
        f"- Effective Primary rows: `{audit['effective_primary_count']}`",
        f"- Effective Blockpit reference rows: `{audit['effective_reference_count']}`",
        f"- Effective matched reference rows: `{audit['effective_matched_reference_count']}`",
        f"- Effective unmatched reference rows: `{audit['effective_unmatched_reference_count']}`",
        f"- Match basis counts: `{audit['matched_basis_counts']}`",
        f"- Effective unmatched type counts: `{audit['effective_unmatched_type_counts']}`",
        "",
        "## Effective Matched Reference Duplicates",
        "",
        "| Ref Zeit | Prim Zeit | Amount | Ref Comment | Prim Business | Basis | Ref Event | Prim Event |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    if not audit["effective_matched_reference_rows"]:
        lines.append("| - | - | - | - | - | - | - | - |")
    for row in audit["effective_matched_reference_rows"]:
        lines.append(
            f"| `{row['reference_timestamp_utc']}` | `{row['primary_timestamp_utc']}` | `{row['amount']}` | "
            f"`{row['reference_comment']}` | `{row['primary_business_type']}` | `{row['match_basis']}` | "
            f"`{row['reference_event_id'][:10]}...` | `{row['primary_event_id'][:10]}...` |"
        )
    lines += [
        "",
        "## Effective Unmatched Reference Rows",
        "",
        "Diese Zeilen sind nach aktuellen Overrides noch wirksam und konnten in diesem Matching nicht 1:1 gegen Bitget-Primary belegt werden.",
        "",
    ]
    if not audit["effective_unmatched_reference_rows"]:
        lines.append("- Keine.")
    else:
        for row in audit["effective_unmatched_reference_rows"]:
            lines.append(
                f"- `{row['timestamp_utc']}` `{row['event_type']}` `{row['asset']}` amount `{row['match_amount']}` comment `{row['business_type']}` event `{row['event_id']}`"
            )
    lines += [
        "",
        "## Raw/Reviewed Abgleich",
        "",
        f"- Raw/reviewed matched Blockpit rows: `{audit['matched_count']}`",
        f"- Davon nicht mehr effektiv: `{audit['matched_count'] - audit['effective_matched_reference_count']}`",
        f"- Raw/reviewed unmatched Blockpit rows: `{audit['unmatched_count']}`",
        f"- Davon nicht mehr effektiv: `{audit['unmatched_count'] - audit['effective_unmatched_reference_count']}`",
        "",
        "Der Raw/reviewed Abgleich bleibt im JSON erhalten, damit bereits ausgeschlossene Blockpit-Referenzen weiterhin nachvollziehbar sind.",
    ]
    lines += [
        "",
        "## Empfehlung",
        "",
        audit["recommendation"],
        "",
        "Dieses Matching-Script schreibt selbst keine Overrides. Die geprüften Kandidaten wurden separat über `scripts/apply_bitget_blockpit_reference_exclusions.py` als `reference_import_only` ausgeschlossen.",
        "",
    ]
    return "\n".join(lines)


def signed_from_payload(payload: dict[str, Any]) -> Decimal:
    qty = dec(payload.get("quantity"))
    side = str(payload.get("side") or "").lower()
    if side in {"out", "sell"}:
        return -abs(qty)
    return abs(qty)


def extract_symbol(text: str) -> str:
    start = text.find("(")
    end = text.find(")", start + 1)
    if start >= 0 and end > start:
        return text[start + 1 : end]
    return ""


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
