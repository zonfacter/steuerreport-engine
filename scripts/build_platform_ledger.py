#!/usr/bin/env python3
"""Build a chronological platform ledger from effective tax events."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
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
    _year,
)

from tax_engine.integrations import effective_integration_mode  # noqa: E402

CREATED_DATE = "2026-05-09"
JSONL_PATH = ROOT / "var" / f"platform_ledger_{CREATED_DATE}.jsonl"
CSV_PATH = ROOT / "var" / f"platform_ledger_{CREATED_DATE}.csv"
SUMMARY_JSON = ROOT / "var" / f"platform_ledger_summary_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"130_PLATFORM_LEDGER_EXPORT_{CREATED_DATE}.md"

KNOWN_ADDRESS_PLATFORMS = {
    "TMHP82UVNVYQTQOXEP98GVCH5DQBZZYFCQ": "pionex",
    "138BCXPVFSQ7YYTFODURVWZTPMUR4WGYA7TED9Y41DJMF7RJA8Y": "binance",
    "WBRPOIEEZKYW6OBGAMNAC2ISKINS4HVWOAWQJBV2OB": "solana_wallet",
}


LEDGER_FIELDS = [
    "ledger_id",
    "timestamp_utc",
    "normalized_timestamp_utc",
    "timestamp_normalization_reason",
    "timestamp_normalization_anchor_ledger_id",
    "timestamp_offset_seconds",
    "year",
    "platform",
    "account_scope",
    "asset",
    "quantity_delta",
    "direction",
    "event_type",
    "source",
    "source_event_id",
    "tx_id",
    "counterparty_platform",
    "counterparty_address",
    "raw_integration",
    "raw_label",
    "raw_comment",
    "source_mode",
    "confidence",
    "review_status",
]


def main() -> None:
    events = _effective_events()
    event_by_id = {str(row.get("unique_event_id") or ""): row for row in events}
    token_aliases = _load_token_aliases()
    ignored_mints = set(_load_ignored_tokens().keys())
    movements = [
        movement
        for row in events
        for movement in _movements(row, token_aliases=token_aliases, ignored_mints=ignored_mints)
        if _year(movement["timestamp"]) >= 2020
    ]
    movements.sort(key=_movement_sort_key)
    rows = [build_ledger_row(index, movement, event_by_id.get(str(movement.get("event_id") or ""), {})) for index, movement in enumerate(movements, 1)]
    apply_timestamp_normalization(rows)

    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JSONL_PATH.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    summary = build_summary(rows)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(summary), encoding="utf-8")
    print(json.dumps({"jsonl": str(JSONL_PATH), "csv": str(CSV_PATH), "summary": str(SUMMARY_JSON), "doc": str(DOC_PATH)}, ensure_ascii=False, indent=2))


def build_ledger_row(index: int, movement: dict[str, Any], event: dict[str, Any]) -> dict[str, str]:
    payload = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    platform = infer_platform(movement, payload, raw)
    counterparty_address = infer_counterparty_address(payload, raw)
    counterparty_platform = infer_counterparty_platform(counterparty_address, payload, raw)
    delta = Decimal(str(movement.get("delta") or "0"))
    source_mode = effective_integration_mode(str(movement.get("source") or "unknown"))
    return {
        "ledger_id": f"pl-{index:08d}",
        "timestamp_utc": str(movement.get("timestamp") or ""),
        "normalized_timestamp_utc": str(movement.get("timestamp") or ""),
        "timestamp_normalization_reason": "",
        "timestamp_normalization_anchor_ledger_id": "",
        "timestamp_offset_seconds": "0",
        "year": str(movement.get("year") or ""),
        "platform": platform,
        "account_scope": infer_account_scope(platform, payload, raw),
        "asset": str(movement.get("asset") or "").upper(),
        "quantity_delta": _plain(delta),
        "direction": "in" if delta > 0 else "out" if delta < 0 else "neutral",
        "event_type": str(movement.get("event_type") or ""),
        "source": str(movement.get("source") or ""),
        "source_event_id": str(movement.get("event_id") or ""),
        "tx_id": str(movement.get("tx_id") or ""),
        "counterparty_platform": counterparty_platform,
        "counterparty_address": counterparty_address,
        "raw_integration": str(movement.get("raw_integration") or ""),
        "raw_label": str(movement.get("raw_label") or ""),
        "raw_comment": str(movement.get("raw_comment") or ""),
        "source_mode": source_mode,
        "confidence": platform_confidence(platform, movement, payload, raw),
        "review_status": "unreviewed",
    }


def apply_timestamp_normalization(rows: list[dict[str, str]]) -> None:
    """Mark duplicate-source time variants without overwriting the original timestamp."""
    by_key: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        tx_id = str(row.get("tx_id") or "").strip()
        if not tx_id:
            continue
        key = (
            tx_id,
            str(row.get("asset") or ""),
            str(abs(Decimal(str(row.get("quantity_delta") or "0")))),
            str(row.get("direction") or ""),
        )
        by_key.setdefault(key, []).append(row)

    for items in by_key.values():
        if len(items) < 2:
            continue
        parsed = [(row, parse_timestamp(row.get("timestamp_utc", ""))) for row in items]
        parsed = [(row, ts) for row, ts in parsed if ts is not None]
        if len(parsed) < 2:
            continue
        unique_timestamps = {ts for _, ts in parsed}
        if len(unique_timestamps) < 2:
            continue
        anchor_row, anchor_ts = min(parsed, key=lambda item: (source_priority(item[0]), item[1], item[0].get("ledger_id", "")))
        for row, ts in parsed:
            offset_seconds = int((ts - anchor_ts).total_seconds())
            if offset_seconds == 0:
                continue
            row["normalized_timestamp_utc"] = anchor_ts.isoformat()
            row["timestamp_normalization_reason"] = "duplicate_tx_asset_quantity_time_variant"
            row["timestamp_normalization_anchor_ledger_id"] = anchor_row.get("ledger_id", "")
            row["timestamp_offset_seconds"] = str(offset_seconds)


def parse_timestamp(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def source_priority(row: dict[str, str]) -> tuple[int, str]:
    source = str(row.get("source") or "").lower()
    if source in {"solana_rpc", "solscan", "solscan_wallet_discovery"} or "helium_legacy" in source:
        rank = 0
    elif source.endswith("_api") or source in {"binance_api", "bitget_api", "pionex_api"}:
        rank = 1
    elif source in {"binance", "bitget", "pionex"}:
        rank = 2
    else:
        rank = 3
    return (rank, str(row.get("timestamp_utc") or ""))


def infer_platform(movement: dict[str, Any], payload: dict[str, Any], raw: dict[str, Any]) -> str:
    source = str(movement.get("source") or payload.get("source") or "").lower().strip()
    integration = str(raw.get("Integration Name") or raw.get("Source Name") or raw.get("integration") or "").lower().strip()
    source_name = str(raw.get("Source Name") or "").lower().strip()
    if source in {"blockpit", "cointracking", "koinly"}:
        return f"{source}_reference"
    if "pionex" in source or "pionex" in integration or "pionex" in source_name:
        return "pionex"
    if source.startswith("binance") or "binance" in integration or "binance" in source_name:
        return "binance"
    if source.startswith("bitget") or "bitget" in integration or "bitget" in source_name:
        return "bitget"
    if source in {"solana_rpc", "solscan_wallet_discovery", "solscan"} or "solana" in integration:
        return "solana_wallet"
    if source.startswith("helium_legacy"):
        return "helium_legacy"
    if source.startswith("heliumtracker") or source.startswith("heliumgeek"):
        return "helium_mining"
    if source.startswith("coinbase"):
        return "coinbase"
    if source == "blockpit":
        return integration or "blockpit_reference"
    return source or "unknown"


def infer_account_scope(platform: str, payload: dict[str, Any], raw: dict[str, Any]) -> str:
    for key in ("account_type", "wallet_address", "owner", "Source Type", "Wallet", "Source Name"):
        value = payload.get(key)
        if value is None:
            value = raw.get(key)
        if value:
            return str(value)[:120]
    return platform


def infer_counterparty_address(payload: dict[str, Any], raw: dict[str, Any]) -> str:
    side = str(payload.get("side") or raw.get("side") or "").lower().strip()
    if side == "in":
        keys = (
            "from_address",
            "counterparty_address",
            "address",
            "Address",
            "SourceAddress",
            "From",
            "payer",
            "to_address",
            "Destination Address",
            "To",
            "payee",
        )
    elif side == "out":
        keys = (
            "to_address",
            "counterparty_address",
            "address",
            "Address",
            "Destination Address",
            "To",
            "payee",
            "from_address",
            "SourceAddress",
            "From",
            "payer",
        )
    else:
        keys = (
            "counterparty_address",
            "to_address",
            "from_address",
            "address",
            "Address",
            "SourceAddress",
            "Destination Address",
            "To",
            "From",
            "payee",
            "payer",
        )
    for key in keys:
        value = payload.get(key)
        if value is None:
            value = raw.get(key)
        if value:
            return str(value).strip()
    return ""


def infer_counterparty_platform(address: str, payload: dict[str, Any], raw: dict[str, Any]) -> str:
    normalized = "".join(ch for ch in str(address).upper() if ch.isalnum())
    if normalized in KNOWN_ADDRESS_PLATFORMS:
        return KNOWN_ADDRESS_PLATFORMS[normalized]
    network = str(payload.get("network") or raw.get("network") or raw.get("Network") or "").lower()
    if "trc20" in network or normalized.startswith("T"):
        return "tron"
    if len(normalized) > 30 and not normalized.startswith("0X"):
        return "chain_address"
    return ""


def platform_confidence(platform: str, movement: dict[str, Any], payload: dict[str, Any], raw: dict[str, Any]) -> str:
    source = str(movement.get("source") or "")
    if platform in source.lower():
        return "high"
    if raw.get("Integration Name") or raw.get("Source Name"):
        return "medium"
    if platform != "unknown":
        return "medium"
    return "low"


def build_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    platform_counts = Counter(row["platform"] for row in rows)
    asset_counts = Counter(row["asset"] for row in rows)
    source_counts = Counter(row["source"] for row in rows)
    mode_counts = Counter(row["source_mode"] for row in rows)
    active_rows = [row for row in rows if row.get("source_mode") == "active"]
    normalized_rows = [row for row in rows if row.get("timestamp_normalization_reason")]
    platform_asset: Counter[tuple[str, str]] = Counter((row["platform"], row["asset"]) for row in rows)
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "ledger_row_count": len(rows),
        "active_ledger_row_count": len(active_rows),
        "reference_ledger_row_count": sum(1 for row in rows if row.get("source_mode") == "reference"),
        "disabled_ledger_row_count": sum(1 for row in rows if row.get("source_mode") == "disabled"),
        "timestamp_normalized_row_count": len(normalized_rows),
        "platform_count": len(platform_counts),
        "asset_count": len(asset_counts),
        "source_count": len(source_counts),
        "files": {"jsonl": str(JSONL_PATH), "csv": str(CSV_PATH)},
        "top_platforms": [{"platform": key, "rows": count} for key, count in platform_counts.most_common(20)],
        "top_assets": [{"asset": key, "rows": count} for key, count in asset_counts.most_common(20)],
        "top_sources": [{"source": key, "rows": count} for key, count in source_counts.most_common(20)],
        "source_modes": [{"mode": key, "rows": count} for key, count in mode_counts.most_common()],
        "timestamp_normalization_examples": normalized_rows[:50],
        "top_platform_assets": [
            {"platform": key[0], "asset": key[1], "rows": count}
            for key, count in platform_asset.most_common(30)
        ],
    }


def render_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# Platform Ledger Export - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Ledger-Zeilen: `{summary['ledger_row_count']}`",
        f"- Aktive Ledger-Zeilen: `{summary['active_ledger_row_count']}`",
        f"- Referenz-Zeilen: `{summary['reference_ledger_row_count']}`",
        f"- Plattformen: `{summary['platform_count']}`",
        f"- Assets: `{summary['asset_count']}`",
        f"- Quellen: `{summary['source_count']}`",
        f"- Zeit-normalisierte Duplikatvarianten: `{summary['timestamp_normalized_row_count']}`",
        f"- JSONL: `{summary['files']['jsonl']}`",
        f"- CSV: `{summary['files']['csv']}`",
        "",
        "## Top Plattformen",
        "",
    ]
    lines.extend(f"- `{row['platform']}`: `{row['rows']}`" for row in summary["top_platforms"])
    lines += ["", "## Top Plattform/Asset-Kombinationen", ""]
    lines.extend(f"- `{row['platform']}` / `{row['asset']}`: `{row['rows']}`" for row in summary["top_platform_assets"][:20])
    lines += [
        "",
        "## Bewertung",
        "",
        "- Das Ledger ist eine deterministische Sicht auf effektive Events nach Review-Actions, Tax-Overrides, Token-Aliasen und Ignored-Tokens.",
        "- Plattformzuordnung ist bei nativen Quellen hoch, bei Blockpit-/Referenzzeilen anhand Integration Name mittel.",
        "- RAW-Daten wurden nicht veraendert.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
