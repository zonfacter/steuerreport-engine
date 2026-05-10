#!/usr/bin/env python3
"""Reconstruct Bitget balances from available records without inventing missing bot trades."""

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

JSON_PATH = ROOT / "var" / "bitget_reconstruction_audit_2026-05-08.json"
DOC_PATH = ROOT / "docs" / "58_BITGET_RECONSTRUCTION_AUDIT_2026-05-08.md"

REFERENCE_SOURCES = {"blockpit", "wiso", "cointracking", "cointracker"}
DERIVATIVE_TYPES = ("derivative", "funding", "liquidation", "pnl", "profit", "loss")
TRANSFER_TYPES = ("deposit", "withdraw", "transfer", "automatic_deposit", "automatic_withdrawal")


def main() -> None:
    events = load_bitget_events()
    rows = [normalize_event(event) for event in events]
    rows = [row for row in rows if row]
    rows.sort(key=lambda row: (row["timestamp_utc"], row["event_id"]))
    audit = build_audit(rows)
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    DOC_PATH.write_text(render_markdown(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "rows": len(rows)}, indent=2))


def load_bitget_events() -> list[dict[str, Any]]:
    raw = STORE.list_raw_events()
    reviewed, _summary = apply_review_actions(raw)
    effective, _override_count = apply_tax_event_overrides(reviewed)
    rows = []
    for event in effective:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        text = " ".join(
            [
                str(payload.get("source") or ""),
                str(payload.get("event_type") or ""),
                json.dumps(raw_row, ensure_ascii=False)[:3000],
            ]
        ).lower()
        if "bitget" in text:
            rows.append(event)
    return rows


def normalize_event(event: dict[str, Any]) -> dict[str, Any] | None:
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    if len(ts) < 10:
        return None
    source = str(payload.get("source") or "unknown")
    event_type = str(payload.get("event_type") or "unknown")
    asset = str(payload.get("asset") or raw.get("coin") or "unknown").upper()
    side = str(payload.get("side") or "").lower()
    gross_amount = signed_quantity(payload, raw, side)
    fee_amount = first_decimal(raw, "fee", "Fee", default=Decimal("0")) or Decimal("0")
    balance_effect = gross_amount + fee_amount
    balance = first_decimal(raw, "balance", "Balance", default=None)
    business_type = str(raw.get("businessType") or raw.get("spotTaxType") or raw.get("type") or "")
    classification = classify(source, event_type, business_type)
    return {
        "event_id": str(event.get("unique_event_id") or ""),
        "timestamp_utc": ts,
        "day": ts[:10],
        "year": int(ts[:4]) if ts[:4].isdigit() else None,
        "source": source,
        "event_type": event_type,
        "business_type": business_type,
        "classification": classification,
        "asset": asset,
        "side": side,
        "gross_amount": str(gross_amount),
        "fee_amount": str(fee_amount),
        "signed_amount": str(balance_effect),
        "balance_reported": str(balance) if balance is not None else "",
        "tx_id": str(payload.get("tx_id") or raw.get("id") or raw.get("billId") or raw.get("orderId") or raw.get("bizOrderId") or ""),
        "is_reference": is_reference(source),
        "has_onchain_signature": has_onchain_signature(raw),
        "raw_hint": {
            key: raw.get(key)
            for key in (
                "amount",
                "fee",
                "balance",
                "coin",
                "businessType",
                "spotTaxType",
                "orderId",
                "tradeId",
                "fromAddress",
                "toAddress",
            )
            if key in raw
        },
    }


def build_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_asset[row["asset"]].append(row)

    asset_reports = []
    for asset, asset_rows in sorted(by_asset.items()):
        primary_rows = [row for row in asset_rows if not row["is_reference"]]
        reference_rows = [row for row in asset_rows if row["is_reference"]]
        class_net: dict[str, Decimal] = defaultdict(Decimal)
        source_counts: Counter[str] = Counter()
        type_counts: Counter[str] = Counter()
        reported_balance_points = []
        balance_breaks = []
        reconstructed = Decimal("0")
        last_reported: Decimal | None = None
        first_ts = asset_rows[0]["timestamp_utc"]
        last_ts = asset_rows[-1]["timestamp_utc"]

        for row in primary_rows:
            amount = dec(row["signed_amount"])
            reconstructed += amount
            class_net[row["classification"]] += amount
            source_counts[row["source"]] += 1
            type_counts[row["event_type"]] += 1
            if row["balance_reported"] != "":
                reported = dec(row["balance_reported"])
                reported_balance_points.append(
                    {
                        "timestamp_utc": row["timestamp_utc"],
                        "event_type": row["event_type"],
                        "business_type": row["business_type"],
                        "amount": row["signed_amount"],
                        "reported_balance": row["balance_reported"],
                        "reconstructed_from_zero": str(reconstructed),
                        "delta_reported_minus_reconstructed": str(reported - reconstructed),
                    }
                )
                if last_reported is not None:
                    expected = last_reported + amount
                    diff = reported - expected
                    if abs(diff) > Decimal("0.000001"):
                        balance_breaks.append(
                            {
                                "timestamp_utc": row["timestamp_utc"],
                                "event_type": row["event_type"],
                                "business_type": row["business_type"],
                                "amount": row["signed_amount"],
                                "previous_reported_balance": str(last_reported),
                                "expected_reported_balance": str(expected),
                                "actual_reported_balance": row["balance_reported"],
                                "difference": str(diff),
                            }
                        )
                last_reported = reported

        asset_reports.append(
            {
                "asset": asset,
                "event_count": len(asset_rows),
                "primary_event_count": len(primary_rows),
                "reference_event_count": len(reference_rows),
                "first_event_utc": first_ts,
                "last_event_utc": last_ts,
                "net_primary_from_available_events": str(sum(dec(row["signed_amount"]) for row in primary_rows)),
                "latest_reported_balance": str(last_reported) if last_reported is not None else "",
                "balance_break_count": len(balance_breaks),
                "balance_breaks_top": balance_breaks[:12],
                "classification_net": {key: str(value) for key, value in sorted(class_net.items())},
                "source_counts": dict(source_counts.most_common()),
                "event_type_counts": dict(type_counts.most_common(20)),
                "onchain_signature_count": sum(1 for row in primary_rows if row["has_onchain_signature"]),
                "reported_balance_sample": reported_balance_points[:8],
            }
        )

    overall = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": "Bitget reconstruction from available primary/reference records. Missing bot trades are not generated.",
        "row_count": len(rows),
        "source_counts": dict(Counter(row["source"] for row in rows).most_common()),
        "classification_counts": dict(Counter(row["classification"] for row in rows).most_common()),
        "asset_reports": sorted(asset_reports, key=lambda row: row["event_count"], reverse=True),
        "limits": [
            "Reported balance fields are platform snapshots per Bitget account area and can reset across Spot/Futures/Strategy contexts.",
            "Reference rows are not used as primary reconstruction truth.",
            "Public market data can validate price plausibility only.",
            "No missing bot fills are generated by this audit.",
        ],
        "next_actions": [
            "Create a focused Bitget 2025 USDT strategy-transfer chain report.",
            "Match every external Bitget withdrawal/deposit with on-chain or counter-platform evidence where tx/hash/address exists.",
            "After Bitget support response, replace unavailable_source_possible with either imported primary data or documented unavailable_source.",
        ],
    }
    return overall


def render_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Bitget Reconstruction Audit - 2026-05-08",
        "",
        "## Zweck",
        "",
        "Dieser Bericht rekonstruiert Bitget nur aus vorhandenen Primaer-/Referenzevents.",
        "Fehlende Bot-Trades werden nicht erzeugt. Referenzdaten bleiben getrennt.",
        "",
        "## Gesamtbild",
        "",
        f"- JSON: `{JSON_PATH}`",
        f"- Events: `{audit['row_count']}`",
        f"- Quellen: `{json.dumps(audit['source_counts'], ensure_ascii=False)}`",
        f"- Klassen: `{json.dumps(audit['classification_counts'], ensure_ascii=False)}`",
        "",
        "## Asset-Summary",
        "",
        "| Asset | Events | Primaer | Referenz | Zeitraum | Net Primaer | Letzter gemeldeter Balance | Balance-Brueche | On-Chain-Signaturen |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in audit["asset_reports"]:
        period = f"{row['first_event_utc'][:10]}..{row['last_event_utc'][:10]}"
        lines.append(
            f"| `{row['asset']}` | {row['event_count']} | {row['primary_event_count']} | {row['reference_event_count']} | "
            f"{period} | `{row['net_primary_from_available_events']}` | `{row['latest_reported_balance']}` | "
            f"{row['balance_break_count']} | {row['onchain_signature_count']} |"
        )
    lines += ["", "## Auffaellige Balance-Brueche", ""]
    for row in audit["asset_reports"]:
        if not row["balance_breaks_top"]:
            continue
        lines.append(f"### {row['asset']}")
        for item in row["balance_breaks_top"][:6]:
            lines.append(
                f"- `{item['timestamp_utc']}` `{item['event_type']}` `{item['business_type']}` "
                f"amount `{item['amount']}` expected `{item['expected_reported_balance']}` "
                f"actual `{item['actual_reported_balance']}` diff `{item['difference']}`"
            )
        lines.append("")
    lines += ["## Bewertung", ""]
    lines += [f"- {item}" for item in audit["limits"]]
    lines += ["", "## Naechste Schritte", ""]
    lines += [f"- {item}" for item in audit["next_actions"]]
    lines.append("")
    return "\n".join(lines)


def classify(source: str, event_type: str, business_type: str) -> str:
    text = f"{source} {event_type} {business_type}".lower()
    if any(marker in text for marker in REFERENCE_SOURCES):
        return "reference"
    if "trans_to_strategy" in text or "trans_from_strategy" in text or "strategy" in text:
        return "strategy_transfer"
    if "trans_to_exchange" in text or "trans_from_exchange" in text:
        return "internal_exchange_transfer"
    if any(token in text for token in ("deposit", "withdraw")):
        return "external_transfer_or_auto_account_move"
    if any(token in text for token in DERIVATIVE_TYPES):
        return "derivative_pnl_fee_or_position"
    if "trade" in text or "buy" in text or "sell" in text:
        return "trade_or_conversion"
    if "fee" in text:
        return "fee"
    if "transfer" in text:
        return "transfer"
    return "other"


def signed_quantity(payload: dict[str, Any], raw: dict[str, Any], side: str) -> Decimal:
    raw_amount = first_decimal(raw, "amount", "Amount", default=None)
    if raw_amount is not None:
        return raw_amount
    quantity = first_decimal(payload, "quantity", "amount", default=Decimal("0")) or Decimal("0")
    if side in {"out", "sell"}:
        return -abs(quantity)
    if side in {"in", "buy"}:
        return abs(quantity)
    return quantity


def first_decimal(mapping: dict[str, Any], *keys: str, default: Decimal | None = Decimal("0")) -> Decimal | None:
    for key in keys:
        if key not in mapping:
            continue
        try:
            return Decimal(str(mapping.get(key) or "0"))
        except (InvalidOperation, ValueError):
            continue
    return default


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def is_reference(source: str) -> bool:
    return source.lower() in REFERENCE_SOURCES


def has_onchain_signature(raw: dict[str, Any]) -> bool:
    for key in ("tradeId", "signature", "txHash", "tx_hash"):
        value = raw.get(key)
        if isinstance(value, str) and 80 <= len(value.strip()) <= 100:
            return True
    return False


if __name__ == "__main__":
    main()
