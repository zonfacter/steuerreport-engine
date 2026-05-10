#!/usr/bin/env python3
"""Audit raw-event timestamp variants for identical tx/asset/quantity rows."""

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

from tax_engine.api.dashboard import _payload_asset_canonical_symbol  # noqa: E402
from tax_engine.ingestion.store import STORE  # noqa: E402
from tax_engine.queue.service import apply_review_actions  # noqa: E402

CREATED_DATE = "2026-05-09"
OVERRIDE_KEY = "runtime.tax_event_overrides"
OUTPUT_JSON = ROOT / "var" / f"timestamp_variant_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"140_TIMESTAMP_VARIANT_AUDIT_{CREATED_DATE}.md"


def main() -> None:
    reviewed, _ = apply_review_actions(STORE.list_raw_events())
    overrides = load_overrides()
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in reviewed:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if not payload:
            continue
        tx_id = str(payload.get("tx_id") or "").strip()
        if not tx_id:
            continue
        qty = dec(payload.get("quantity"))
        if qty == 0:
            continue
        key = (
            tx_id,
            _payload_asset_canonical_symbol(payload),
            plain(abs(qty)),
            "in" if qty > 0 else "out",
        )
        grouped[key].append(slim(event, payload, overrides))

    variants = []
    for (tx_id, asset, quantity, direction), items in grouped.items():
        timestamps = {item["timestamp_utc"] for item in items if item["timestamp_utc"]}
        if len(items) < 2 or len(timestamps) < 2:
            continue
        parsed = [(item, parse_ts(item["timestamp_utc"])) for item in items]
        parsed = [(item, ts) for item, ts in parsed if ts is not None]
        if len(parsed) < 2:
            continue
        anchor, anchor_ts = min(parsed, key=lambda pair: (source_priority(pair[0]["source"]), pair[1], pair[0]["event_id"]))
        rows = []
        for item, ts in sorted(parsed, key=lambda pair: (pair[1], pair[0]["event_id"])):
            rows.append({**item, "normalized_timestamp_utc": anchor_ts.isoformat(), "timestamp_offset_seconds": int((ts - anchor_ts).total_seconds())})
        variants.append(
            {
                "tx_id": tx_id,
                "asset": asset,
                "quantity": quantity,
                "direction": direction,
                "anchor_event_id": anchor["event_id"],
                "normalized_timestamp_utc": anchor_ts.isoformat(),
                "row_count": len(rows),
                "offset_seconds": sorted({row["timestamp_offset_seconds"] for row in rows}),
                "sources": dict(Counter(row["source"] for row in rows)),
                "override_categories": dict(Counter(row["override_category"] for row in rows)),
                "rows": rows,
            }
        )

    variants.sort(key=lambda row: (row["normalized_timestamp_utc"], row["asset"], row["tx_id"]))
    audit = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "variant_group_count": len(variants),
        "row_count": sum(len(row["rows"]) for row in variants),
        "offset_counts": dict(Counter(str(offset) for row in variants for offset in row["offset_seconds"])),
        "variants": variants[:1000],
    }
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(DOC_PATH), "variant_groups": len(variants), "rows": audit["row_count"]}, ensure_ascii=False, indent=2))


def slim(event: dict[str, Any], payload: dict[str, Any], overrides: dict[str, dict[str, Any]]) -> dict[str, Any]:
    event_id = str(event.get("unique_event_id") or "")
    override = overrides.get(event_id, {})
    return {
        "event_id": event_id,
        "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
        "source": str(payload.get("source") or ""),
        "event_type": str(payload.get("event_type") or ""),
        "side": str(payload.get("side") or ""),
        "override_category": str(override.get("tax_category") or "ACTIVE"),
        "override_reason_code": str(override.get("reason_code") or ""),
    }


def load_overrides() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting(OVERRIDE_KEY)
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    return {str(key): value for key, value in raw.items() if isinstance(value, dict)} if isinstance(raw, dict) else {}


def parse_ts(value: str) -> datetime | None:
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


def source_priority(source: str) -> int:
    normalized = str(source or "").lower()
    if normalized in {"solana_rpc", "solscan", "solscan_wallet_discovery"} or normalized.startswith("helium_legacy"):
        return 0
    if normalized.endswith("_api"):
        return 1
    if normalized in {"binance", "bitget", "pionex"}:
        return 2
    return 3


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Timestamp Variant Audit - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Gruppen mit Zeitvarianten: `{audit['variant_group_count']}`",
        f"- Betroffene Rohdaten-Zeilen: `{audit['row_count']}`",
        f"- Offset-Verteilung Sekunden: `{audit['offset_counts']}`",
        "",
        "## Top Zeitvarianten",
        "",
    ]
    for variant in audit["variants"][:80]:
        lines.append(
            f"- `{variant['normalized_timestamp_utc']}` `{variant['asset']}` `{variant['quantity']}` "
            f"{variant['direction']} rows `{variant['row_count']}` offsets `{variant['offset_seconds']}` "
            f"sources `{variant['sources']}` overrides `{variant['override_categories']}` tx `{variant['tx_id']}`"
        )
    lines += [
        "",
        "## Bewertung",
        "",
        "- `normalized_timestamp_utc` ist die kanonische Vergleichszeit je identischer TX/Asset/Menge/Richtung.",
        "- `timestamp_utc` bleibt unverändert erhalten; Zeitvarianten werden nur für Matching, Plausibilität und Audit glattgezogen.",
        "- EXCLUDED-Zeilen bleiben hier sichtbar, obwohl sie nicht mehr in der Steuerberechnung wirken.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
