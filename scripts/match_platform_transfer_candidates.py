#!/usr/bin/env python3
"""Find amount/time/address transfer candidates across platform ledger rows."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CREATED_DATE = "2026-05-09"
LEDGER_JSONL = ROOT / "var" / f"platform_ledger_{CREATED_DATE}.jsonl"
TRANSFER_GROUPS_JSON = ROOT / "var" / f"platform_transfer_groups_{CREATED_DATE}.json"
SIM_JSON = ROOT / "var" / f"platform_balance_simulation_{CREATED_DATE}.json"
OUTPUT_JSON = ROOT / "var" / f"platform_transfer_candidates_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"134_PLATFORM_TRANSFER_CANDIDATES_{CREATED_DATE}.md"
TRANSFER_TYPES = {"deposit", "withdrawal", "transfer", "legacy_transfer", "token_transfer", "fiat_deposit", "fiat_withdrawal"}
WINDOWS = (timedelta(hours=6), timedelta(days=3), timedelta(days=14), timedelta(days=45))


def main() -> None:
    rows = load_active_ledger()
    exact_groups = read_json(TRANSFER_GROUPS_JSON)
    simulation = read_json(SIM_JSON)
    exact_matched_ids = {ledger_id for group in exact_groups.get("groups", []) for ledger_id in group.get("ledger_ids", [])}
    transfer_like = [row for row in rows if is_transfer_like(row) and row["ledger_id"] not in exact_matched_ids]
    candidates = dedupe_candidates(find_candidates(transfer_like))
    break_links = link_negative_breaks(simulation.get("first_timeline_breaks") or [], candidates)
    audit = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "transfer_like_rows": len(transfer_like),
        "candidate_count": len(candidates),
        "confidence_counts": dict(Counter(row["confidence"] for row in candidates)),
        "match_type_counts": dict(Counter(row["match_type"] for row in candidates)),
        "break_link_count": len(break_links),
        "candidates": candidates[:1000],
        "negative_break_links": break_links,
    }
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(DOC_PATH), "candidates": len(candidates), "break_links": len(break_links)}, ensure_ascii=False, indent=2))


def load_active_ledger() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with LEDGER_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("source_mode") or "active").lower() != "active":
                continue
            row["_dt"] = parse_ts(str(row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or ""))
            row["_qty"] = Decimal(str(row.get("quantity_delta") or "0"))
            rows.append(row)
    rows.sort(key=lambda row: (row["_dt"], row.get("ledger_id", "")))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def is_transfer_like(row: dict[str, Any]) -> bool:
    event_type = str(row.get("event_type") or "").lower()
    return event_type in TRANSFER_TYPES or bool(row.get("counterparty_address"))


def find_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_asset[str(row.get("asset") or "")].append(row)
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for asset_rows in by_asset.values():
        ins = [row for row in asset_rows if row["_qty"] > 0]
        outs = [row for row in asset_rows if row["_qty"] < 0]
        for out in outs:
            out_qty = abs(out["_qty"])
            best_for_out: list[dict[str, Any]] = []
            for inn in ins:
                if out.get("platform") == inn.get("platform"):
                    continue
                delta_seconds = abs((inn["_dt"] - out["_dt"]).total_seconds())
                if delta_seconds > WINDOWS[-1].total_seconds():
                    continue
                in_qty = inn["_qty"]
                qty_diff = abs(in_qty - out_qty)
                tolerance = max(Decimal("0.000001"), out_qty * Decimal("0.002"))
                if qty_diff > tolerance:
                    continue
                key = tuple(sorted((str(out["ledger_id"]), str(inn["ledger_id"]))))
                if key in seen:
                    continue
                candidate = build_candidate(out, inn, qty_diff, delta_seconds)
                best_for_out.append(candidate)
            best_for_out.sort(key=lambda row: (confidence_rank(row["confidence"]), Decimal(row["quantity_diff"]), row["time_delta_seconds"]))
            for candidate in best_for_out[:3]:
                seen.add(tuple(sorted((candidate["from_ledger_id"], candidate["to_ledger_id"]))))
                candidates.append(candidate)
    return sorted(candidates, key=lambda row: (confidence_rank(row["confidence"]), row["first_timestamp_utc"], row["asset"], row["quantity_diff"]))


def dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_out: dict[str, dict[str, Any]] = {}
    best_by_fingerprint: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    for candidate in sorted(candidates, key=candidate_sort_key):
        out_id = str(candidate["from_ledger_id"])
        if out_id not in best_by_out:
            best_by_out[out_id] = candidate
        fingerprint = (
            str(candidate["asset"]),
            str(candidate["from_platform"]),
            str(candidate["to_platform"]),
            str(candidate["quantity_out"]),
            str(candidate["from_tx_id"]),
            str(candidate["to_tx_id"]),
        )
        current = best_by_fingerprint.get(fingerprint)
        if current is None or candidate_sort_key(candidate) < candidate_sort_key(current):
            best_by_fingerprint[fingerprint] = candidate
    keep_ids = {id(row) for row in best_by_out.values()} | {id(row) for row in best_by_fingerprint.values()}
    return sorted([row for row in candidates if id(row) in keep_ids], key=candidate_sort_key)


def candidate_sort_key(row: dict[str, Any]) -> tuple[int, Decimal, int, str]:
    return (
        confidence_rank(str(row.get("confidence", ""))),
        Decimal(str(row.get("quantity_diff") or "0")),
        int(row.get("time_delta_seconds") or 0),
        str(row.get("candidate_id") or ""),
    )


def build_candidate(out: dict[str, Any], inn: dict[str, Any], qty_diff: Decimal, delta_seconds: float) -> dict[str, Any]:
    direct_address = addresses_match(out, inn)
    if direct_address:
        match_type = "address_amount_time"
    elif delta_seconds <= WINDOWS[0].total_seconds():
        match_type = "same_asset_amount_6h"
    elif delta_seconds <= WINDOWS[1].total_seconds():
        match_type = "same_asset_amount_3d"
    elif delta_seconds <= WINDOWS[2].total_seconds():
        match_type = "same_asset_amount_14d"
    else:
        match_type = "same_asset_amount_45d"
    confidence = infer_confidence(match_type, qty_diff, abs(out["_qty"]), delta_seconds)
    return {
        "candidate_id": f"cand:{out['ledger_id']}:{inn['ledger_id']}",
        "match_type": match_type,
        "confidence": confidence,
        "asset": out.get("asset", ""),
        "quantity_out": plain(abs(out["_qty"])),
        "quantity_in": plain(inn["_qty"]),
        "quantity_diff": plain(qty_diff),
        "time_delta_seconds": int(delta_seconds),
        "first_timestamp_utc": min(str(out.get("timestamp_utc") or ""), str(inn.get("timestamp_utc") or "")),
        "first_normalized_timestamp_utc": min(effective_timestamp(out), effective_timestamp(inn)),
        "from_ledger_id": out.get("ledger_id", ""),
        "from_platform": out.get("platform", ""),
        "from_timestamp_utc": out.get("timestamp_utc", ""),
        "from_normalized_timestamp_utc": effective_timestamp(out),
        "from_event_type": out.get("event_type", ""),
        "from_tx_id": out.get("tx_id", ""),
        "from_counterparty_address": out.get("counterparty_address", ""),
        "to_ledger_id": inn.get("ledger_id", ""),
        "to_platform": inn.get("platform", ""),
        "to_timestamp_utc": inn.get("timestamp_utc", ""),
        "to_normalized_timestamp_utc": effective_timestamp(inn),
        "to_event_type": inn.get("event_type", ""),
        "to_tx_id": inn.get("tx_id", ""),
        "to_counterparty_address": inn.get("counterparty_address", ""),
    }


def addresses_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_addr = normalize_address(str(left.get("counterparty_address") or ""))
    right_addr = normalize_address(str(right.get("counterparty_address") or ""))
    if left_addr and right_addr and left_addr == right_addr:
        return True
    for row, other in ((left, right), (right, left)):
        addr = normalize_address(str(row.get("counterparty_address") or ""))
        platform = normalize_address(str(other.get("account_scope") or other.get("platform") or ""))
        if addr and platform and addr == platform:
            return True
    return False


def infer_confidence(match_type: str, qty_diff: Decimal, qty: Decimal, delta_seconds: float) -> str:
    rel = Decimal("0") if qty == 0 else qty_diff / qty
    if match_type == "address_amount_time" and rel <= Decimal("0.0001"):
        return "high"
    if delta_seconds <= WINDOWS[0].total_seconds() and rel <= Decimal("0.0001"):
        return "high"
    if delta_seconds <= WINDOWS[1].total_seconds() and rel <= Decimal("0.001"):
        return "medium"
    return "low"


def link_negative_breaks(breaks: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_ledger: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_ledger[candidate["from_ledger_id"]].append(candidate)
        by_ledger[candidate["to_ledger_id"]].append(candidate)
    links = []
    for item in breaks:
        ledger_id = str(item.get("ledger_id") or "")
        direct = by_ledger.get(ledger_id, [])
        nearby = [
            candidate
            for candidate in candidates
            if candidate["asset"] == item.get("asset")
            and (candidate["from_platform"] == item.get("platform") or candidate["to_platform"] == item.get("platform"))
        ][:10]
        links.append(
            {
                "break_ledger_id": ledger_id,
                "timestamp_utc": item.get("timestamp_utc", ""),
                "normalized_timestamp_utc": item.get("normalized_timestamp_utc", item.get("timestamp_utc", "")),
                "platform": item.get("platform", ""),
                "asset": item.get("asset", ""),
                "balance_after": item.get("balance_after", ""),
                "direct_candidate_count": len(direct),
                "nearby_candidate_count": len(nearby),
                "direct_candidates": direct[:5],
                "nearby_candidates": nearby[:5],
            }
        )
    return links


def parse_ts(raw: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def effective_timestamp(row: dict[str, Any]) -> str:
    return str(row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or "")


def normalize_address(value: str) -> str:
    return "".join(ch for ch in value.upper() if ch.isalnum())


def confidence_rank(value: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(str(value), 9)


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Platform Transfer Candidates - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Transfer-like Zeilen ohne exakte TXID-Gruppe: `{audit['transfer_like_rows']}`",
        f"- Amount/Time/Address-Kandidaten: `{audit['candidate_count']}`",
        f"- Bruchstellen mit Kandidatenlink-Analyse: `{audit['break_link_count']}`",
        f"- Confidence: `{audit['confidence_counts']}`",
        f"- Match-Typen: `{audit['match_type_counts']}`",
        "",
        "## Top Kandidaten",
        "",
    ]
    if not audit["candidates"]:
        lines.append("- Keine Kandidaten gefunden.")
    for row in audit["candidates"][:80]:
        lines.append(
            f"- `{row['confidence']}` `{row['asset']}` `{row['quantity_out']}` "
            f"{row['from_platform']} -> {row['to_platform']} "
            f"diff `{row['quantity_diff']}` dt `{row['time_delta_seconds']}s` "
            f"from `{row['from_timestamp_utc']}` to `{row['to_timestamp_utc']}`"
        )
    lines += ["", "## Bruchstellen-Bezug", ""]
    for row in audit["negative_break_links"]:
        lines.append(
            f"- `{row['timestamp_utc']}` `{row['platform']}` `{row['asset']}` saldo `{row['balance_after']}` "
            f"direct `{row['direct_candidate_count']}` nearby `{row['nearby_candidate_count']}`"
        )
    lines += [
        "",
        "## Bewertung",
        "",
        "- High/Medium Kandidaten sind nur Match-Vorschlaege. Steuerlich wirksam werden sie erst nach Beleg-/API-Abgleich oder expliziter Review-Entscheidung.",
        "- Kandidaten mit gleichem Asset und sehr kurzer Zeitdifferenz sind besonders relevant fuer CEX-zu-Wallet-Transfers ohne identische TXID.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
