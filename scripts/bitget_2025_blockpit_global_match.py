#!/usr/bin/env python3
"""Match Bitget 2025 Blockpit reference rows against Bitget API primary rows."""

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

CREATED_DATE = "2026-05-09"
JSON_PATH = ROOT / "var" / f"bitget_2025_blockpit_global_match_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"90_BITGET_2025_BLOCKPIT_GLOBAL_MATCH_{CREATED_DATE}.md"
TIME_TOLERANCE_SECONDS = 300
AMOUNT_TOLERANCE = Decimal("0.00000001")
PRIMARY_SOURCES = {"bitget_api", "bitget_tax_api", "bitget_account_bills_api"}


def main() -> None:
    raw_events = STORE.list_raw_events()
    reviewed, review_summary = apply_review_actions(raw_events)
    effective, override_count = apply_tax_event_overrides(reviewed)
    effective_ids = {str(event.get("unique_event_id") or "") for event in effective}

    rows = collect_rows(reviewed)
    primary = [row for row in rows if row["kind"] == "primary"]
    reference = [row for row in rows if row["kind"] == "reference"]
    matches, unmatched = match_rows(primary, reference)
    for row in matches:
        row["reference_effective"] = row["reference_event_id"] in effective_ids
        row["primary_effective"] = row["primary_event_id"] in effective_ids
    for row in unmatched:
        row["reference_effective"] = row["event_id"] in effective_ids

    effective_matches = [row for row in matches if row["reference_effective"]]
    effective_unmatched = [row for row in unmatched if row["reference_effective"]]
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": "Bitget 2025 Blockpit reference rows vs Bitget API primary rows",
        "view_note": (
            "Raw/reviewed view is used for matching so reference rows remain visible. "
            "effective_* marks rows after review actions and tax_event_overrides, but before integration-mode filtering."
        ),
        "matching_rule": {
            "year": "2025",
            "same_asset": True,
            "same_signed_balance_effect": True,
            "time_tolerance_seconds": TIME_TOLERANCE_SECONDS,
            "amount_tolerance": str(AMOUNT_TOLERANCE),
            "tx_id_base_match": True,
            "primary_sources": sorted(PRIMARY_SOURCES),
        },
        "review_summary": review_summary,
        "override_count": override_count,
        "primary_count": len(primary),
        "reference_count": len(reference),
        "matched_count": len(matches),
        "unmatched_count": len(unmatched),
        "effective_matched_reference_count": len(effective_matches),
        "effective_unmatched_reference_count": len(effective_unmatched),
        "primary_source_counts": top_counts(Counter(row["source"] for row in primary), 20),
        "reference_label_counts": top_counts(Counter(row["raw_label"] for row in reference), 30),
        "matched_label_counts": top_counts(Counter(row["reference_event_type"] for row in matches), 30),
        "unmatched_label_counts": top_counts(Counter(row["event_type"] for row in unmatched), 30),
        "effective_unmatched_label_counts": top_counts(Counter(row["event_type"] for row in effective_unmatched), 30),
        "effective_unmatched_month_counts": top_counts(Counter(row["timestamp_utc"][:7] for row in effective_unmatched), 30),
        "effective_unmatched_asset_counts": top_counts(Counter(row["asset"] for row in effective_unmatched), 30),
        "match_basis_counts": top_counts(Counter(row["match_basis"] for row in matches), 20),
        "matches_sample": matches[:200],
        "effective_unmatched_reference_rows": effective_unmatched[:1000],
        "recommendation": build_recommendation(effective_matches, effective_unmatched),
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(
        json.dumps(
            {
                "json": str(JSON_PATH),
                "doc": str(DOC_PATH),
                "primary_count": audit["primary_count"],
                "reference_count": audit["reference_count"],
                "matched_count": audit["matched_count"],
                "effective_unmatched_reference_count": audit["effective_unmatched_reference_count"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def collect_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if ts[:4] != "2025":
            continue
        source = str(payload.get("source") or "").strip().lower()
        is_primary = source in PRIMARY_SOURCES
        raw_source = str(raw.get("Source Name") or raw.get("Integration Name") or "").strip().lower()
        is_reference = source == "blockpit" and raw_source == "bitget"
        if not is_primary and not is_reference:
            continue
        row = normalize_row(event, payload, raw, "primary" if is_primary else "reference")
        if row is not None:
            rows.append(row)
    rows.sort(key=lambda row: (row["timestamp_utc"], row["kind"], row["event_id"]))
    return rows


def normalize_row(event: dict[str, Any], payload: dict[str, Any], raw: dict[str, Any], kind: str) -> dict[str, Any] | None:
    ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    event_id = str(event.get("unique_event_id") or "")
    source = str(payload.get("source") or "").strip().lower()
    event_type = str(payload.get("event_type") or "").strip().lower()
    asset = str(payload.get("asset") or raw.get("coin") or raw.get("Outgoing Asset") or raw.get("Incoming Asset") or "").upper()
    if not ts or not event_id or not asset:
        return None
    amount = signed_from_payload(payload)
    tx_id = source_tx_id(payload, raw)
    return {
        "event_id": event_id,
        "kind": kind,
        "source": source,
        "timestamp_utc": ts,
        "epoch_seconds": parse_epoch(ts),
        "asset": asset,
        "event_type": event_type,
        "raw_label": str(raw.get("Label") or raw.get("businessType") or raw.get("spotTaxType") or event_type).strip().lower(),
        "balance_effect": str(amount),
        "tx_id": tx_id,
        "tx_base": normalize_tx_base(tx_id),
        "raw_comment": str(raw.get("Comment (optional)") or raw.get("businessType") or raw.get("spotTaxType") or ""),
    }


def match_rows(primary: list[dict[str, Any]], reference: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    primary_by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in primary:
        primary_by_asset[row["asset"]].append(row)
    matches: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    used_primary: set[str] = set()
    for ref in reference:
        candidates: list[tuple[int, int, str, dict[str, Any], str]] = []
        ref_amount = dec(ref["balance_effect"])
        for prim in primary_by_asset.get(ref["asset"], []):
            if prim["event_id"] in used_primary:
                continue
            if abs(dec(prim["balance_effect"]) - ref_amount) > AMOUNT_TOLERANCE:
                continue
            delta_seconds = abs(int(prim["epoch_seconds"]) - int(ref["epoch_seconds"]))
            tx_match = bool(ref["tx_base"] and ref["tx_base"] == prim["tx_base"])
            if not tx_match and delta_seconds > TIME_TOLERANCE_SECONDS:
                continue
            basis = "tx_id_base_amount_asset" if tx_match else "time_amount_asset"
            candidates.append((0 if tx_match else 1, delta_seconds, prim["event_id"], prim, basis))
        if not candidates:
            unmatched.append(ref)
            continue
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        _rank, delta_seconds, _id, prim, basis = candidates[0]
        used_primary.add(prim["event_id"])
        matches.append(
            {
                "reference_event_id": ref["event_id"],
                "primary_event_id": prim["event_id"],
                "reference_timestamp_utc": ref["timestamp_utc"],
                "primary_timestamp_utc": prim["timestamp_utc"],
                "delta_seconds": delta_seconds,
                "asset": ref["asset"],
                "amount": ref["balance_effect"],
                "reference_event_type": ref["event_type"],
                "primary_event_type": prim["event_type"],
                "reference_comment": ref["raw_comment"],
                "primary_comment": prim["raw_comment"],
                "reference_tx_id": ref["tx_id"],
                "primary_tx_id": prim["tx_id"],
                "match_basis": basis,
            }
        )
    return matches, unmatched


def build_recommendation(effective_matches: list[dict[str, Any]], effective_unmatched: list[dict[str, Any]]) -> str:
    if not effective_unmatched:
        return (
            "Alle aktuell effektiven Bitget-Blockpit-Referenzzeilen aus 2025 konnten gegen Bitget-API-Primary gematcht werden. "
            "Ausschluss als reference_import_only waere nach Review moeglich."
        )
    return (
        f"{len(effective_unmatched)} aktuell effektive Bitget-Blockpit-Referenzzeilen 2025 bleiben ohne 1:1-API-Match. "
        "Sie duerfen nicht automatisch als Primary behandelt werden; sie sind aber gute Suchanker fuer Bitget-Supportexport, "
        "On-Chain-Transfers, PnL-/Funding-Summen und lokale KI-Priorisierung."
    )


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Bitget 2025 Blockpit Global Match - 2026-05-09",
        "",
        "## Summary",
        "",
        f"- JSON: `{JSON_PATH}`",
        f"- Scope: `{audit['scope']}`",
        f"- Sicht: `{audit['view_note']}`",
        f"- Primary-Zeilen: `{audit['primary_count']}`",
        f"- Blockpit-Referenzzeilen: `{audit['reference_count']}`",
        f"- Matches: `{audit['matched_count']}`",
        f"- Unmatched: `{audit['unmatched_count']}`",
        f"- Effektive matched Referenzen: `{audit['effective_matched_reference_count']}`",
        f"- Effektive unmatched Referenzen: `{audit['effective_unmatched_reference_count']}`",
        f"- Match-Basis: `{audit['match_basis_counts']}`",
        "",
        "## Effektive unmatched Referenzen nach Typ",
        "",
    ]
    for key, value in audit["effective_unmatched_label_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    if not audit["effective_unmatched_label_counts"]:
        lines.append("- Keine.")
    lines += ["", "## Effektive unmatched Referenzen nach Monat", ""]
    for key, value in audit["effective_unmatched_month_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    if not audit["effective_unmatched_month_counts"]:
        lines.append("- Keine.")
    lines += ["", "## Effektive unmatched Referenzen nach Asset", ""]
    for key, value in audit["effective_unmatched_asset_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    if not audit["effective_unmatched_asset_counts"]:
        lines.append("- Keine.")
    lines += ["", "## Erste offene Referenzzeilen", ""]
    for row in audit["effective_unmatched_reference_rows"][:80]:
        lines.append(
            f"- `{row['timestamp_utc']}` `{row['event_type']}` `{row['asset']}` `{row['balance_effect']}` "
            f"comment `{row['raw_comment']}` event `{row['event_id']}`"
        )
    if not audit["effective_unmatched_reference_rows"]:
        lines.append("- Keine.")
    lines += ["", "## Bewertung", "", audit["recommendation"], ""]
    return "\n".join(lines)


def signed_from_payload(payload: dict[str, Any]) -> Decimal:
    qty = dec(payload.get("quantity"))
    side = str(payload.get("side") or "").lower()
    if side in {"out", "sell"}:
        return -abs(qty)
    return abs(qty)


def source_tx_id(payload: dict[str, Any], raw: dict[str, Any]) -> str:
    for key in ("tx_id", "billId", "id", "bizOrderId", "orderId", "tradeId", "Trx. ID (optional)"):
        value = payload.get(key) if key in payload else raw.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def normalize_tx_base(value: str) -> str:
    text = str(value or "").strip()
    for suffix in (":out", ":in", ":fee", "-fee"):
        if text.endswith(suffix):
            return text[: -len(suffix)]
    return text


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


def top_counts(counter: Counter[str], limit: int) -> dict[str, int]:
    return {key: int(value) for key, value in counter.most_common(limit)}


if __name__ == "__main__":
    main()
