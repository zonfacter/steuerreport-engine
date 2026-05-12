#!/usr/bin/env python3
"""Audit Bitget derivative/liquidation window around 2025-02-27."""

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

JSON_PATH = ROOT / "var" / "bitget_derivative_liquidation_audit_2026-05-08.json"
DOC_PATH = ROOT / "docs" / "60_BITGET_DERIVATIVE_LIQUIDATION_AUDIT_2026-05-08.md"
START_DAY = "2025-02-20"
END_DAY = "2025-03-05"


def main() -> None:
    rows = collect_rows()
    audit = build_audit(rows)
    JSON_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    DOC_PATH.write_text(render(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "rows": len(rows)}, indent=2))


def collect_rows() -> list[dict[str, Any]]:
    raw = STORE.list_raw_events()
    reviewed, _summary = apply_review_actions(raw)
    effective, _override_count = apply_tax_event_overrides(reviewed)
    rows: list[dict[str, Any]] = []
    for event in effective:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if not (START_DAY <= ts[:10] <= END_DAY):
            continue
        text = " ".join([str(payload.get("source") or ""), str(payload.get("event_type") or ""), json.dumps(raw_row, ensure_ascii=False)]).lower()
        if "bitget" not in text:
            continue
        source = str(payload.get("source") or "")
        event_type = str(payload.get("event_type") or "")
        business_type = str(raw_row.get("businessType") or raw_row.get("spotTaxType") or "")
        symbol = str(raw_row.get("symbol") or "")
        gross = dec(raw_row.get("amount") if "amount" in raw_row else signed_from_payload(payload))
        fee = dec(raw_row.get("fee"))
        balance_effect = gross + fee
        rows.append(
            {
                "timestamp_utc": ts,
                "day": ts[:10],
                "source": source,
                "event_type": event_type,
                "business_type": business_type,
                "symbol": symbol,
                "asset": str(payload.get("asset") or raw_row.get("coin") or "").upper(),
                "side": str(payload.get("side") or ""),
                "gross_amount": str(gross),
                "fee": str(fee),
                "balance_effect": str(balance_effect),
                "reported_balance": str(raw_row.get("balance") or ""),
                "id": str(raw_row.get("billId") or raw_row.get("id") or raw_row.get("bizOrderId") or ""),
                "classification": classify(source, event_type, business_type),
                "is_reference": source.lower() == "blockpit",
            }
        )
    rows.sort(key=lambda row: (row["timestamp_utc"], row["source"], row["id"]))
    return rows


def build_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    primary = [row for row in rows if not row["is_reference"]]
    reference = [row for row in rows if row["is_reference"]]
    net_by_class = sum_by(primary, "classification")
    net_by_business = sum_by(primary, "business_type")
    net_by_symbol = sum_by(primary, "symbol")
    net_by_day = sum_by(primary, "day")
    fee_by_business: dict[str, Decimal] = defaultdict(Decimal)
    gross_by_business: dict[str, Decimal] = defaultdict(Decimal)
    for row in primary:
        fee_by_business[row["business_type"]] += dec(row["fee"])
        gross_by_business[row["business_type"]] += dec(row["gross_amount"])
    loss_rows = [row for row in primary if "loss" in row["event_type"].lower() or "burst" in row["business_type"].lower()]
    risk_rows = [row for row in primary if "risk_captital" in row["business_type"].lower() or "risk_capital" in row["business_type"].lower()]
    reference_fee_total = sum(dec(row["balance_effect"]) for row in reference if "fee" in row["event_type"].lower())
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": f"Bitget derivative/liquidation window {START_DAY}..{END_DAY}",
        "row_count": len(rows),
        "primary_count": len(primary),
        "reference_count": len(reference),
        "source_counts": dict(Counter(row["source"] for row in rows).most_common()),
        "event_type_counts": dict(Counter(row["event_type"] for row in rows).most_common()),
        "business_type_counts": dict(Counter(row["business_type"] for row in rows).most_common()),
        "net_primary_by_class": stringify(net_by_class),
        "net_primary_by_business_type": stringify(net_by_business),
        "gross_primary_by_business_type": stringify(gross_by_business),
        "fee_primary_by_business_type": stringify(fee_by_business),
        "net_primary_by_symbol": stringify(net_by_symbol),
        "net_primary_by_day": stringify(net_by_day),
        "loss_rows": loss_rows,
        "risk_capital_rows": risk_rows,
        "reference_fee_total_quantity": str(reference_fee_total),
        "timeline_focus": [
            row
            for row in primary
            if row["day"] in {"2025-02-22", "2025-02-27"} or row["classification"] in {"liquidation_loss", "risk_capital_transfer"}
        ][:120],
        "interpretation": [
            "Open-long/open-short rows have gross amount 0 and balance effect equals fee only; they are not leveraged notional movements.",
            "Close-long/close-short rows carry realized PnL amount plus fee and are balance-relevant settlement rows.",
            "The 2025-02-27 loss row is a Bitget primary liquidation/loss-style row: burst_long_loss_query on HNTUSDT.",
            "The 2025-02-27 risk_captital_user_transfer row moves remaining USDT after the loss area and should be documented as transfer/risk-capital movement, not a synthetic trade.",
            "Blockpit rows in this window are reference-only and must not be added on top of Bitget primary rows unless unmatched.",
        ],
    }


def render(audit: dict[str, Any]) -> str:
    lines = [
        "# Bitget Derivative Liquidation Audit - 2026-05-08",
        "",
        "## Scope",
        "",
        f"- Zeitraum: `{audit['scope']}`",
        f"- JSON: `{JSON_PATH}`",
        f"- Rows: `{audit['row_count']}`",
        f"- Primary: `{audit['primary_count']}`",
        f"- Reference: `{audit['reference_count']}`",
        f"- Sources: `{json.dumps(audit['source_counts'], ensure_ascii=False)}`",
        "",
        "## Primaer-Summen",
        "",
        f"- Net by class: `{json.dumps(audit['net_primary_by_class'], ensure_ascii=False)}`",
        f"- Net by symbol: `{json.dumps(audit['net_primary_by_symbol'], ensure_ascii=False)}`",
        f"- Net by day: `{json.dumps(audit['net_primary_by_day'], ensure_ascii=False)}`",
        f"- Gross by business: `{json.dumps(audit['gross_primary_by_business_type'], ensure_ascii=False)}`",
        f"- Fees by business: `{json.dumps(audit['fee_primary_by_business_type'], ensure_ascii=False)}`",
        f"- Blockpit reference fee quantity total: `{audit['reference_fee_total_quantity']}`",
        "",
        "## Loss / Risk Capital",
        "",
    ]
    for row in audit["loss_rows"]:
        lines.append(
            f"- LOSS `{row['timestamp_utc']}` `{row['symbol']}` gross `{row['gross_amount']}` fee `{row['fee']}` "
            f"effect `{row['balance_effect']}` balance `{row['reported_balance']}` id `{row['id']}`"
        )
    for row in audit["risk_capital_rows"]:
        lines.append(
            f"- RISK `{row['timestamp_utc']}` gross `{row['gross_amount']}` effect `{row['balance_effect']}` "
            f"balance `{row['reported_balance']}` id `{row['id']}`"
        )
    lines += ["", "## Focus Timeline", "", "| Zeit | Typ | Business | Symbol | Gross | Fee | Effect | Balance |", "|---|---|---|---|---:|---:|---:|---:|"]
    for row in audit["timeline_focus"][:80]:
        lines.append(
            f"| `{row['timestamp_utc']}` | `{row['event_type']}` | `{row['business_type']}` | `{row['symbol']}` | "
            f"`{row['gross_amount']}` | `{row['fee']}` | `{row['balance_effect']}` | `{row['reported_balance']}` |"
        )
    lines += ["", "## Interpretation", ""]
    lines += [f"- {item}" for item in audit["interpretation"]]
    lines.append("")
    return "\n".join(lines)


def classify(source: str, event_type: str, business_type: str) -> str:
    if source.lower() == "blockpit":
        return "reference"
    text = f"{event_type} {business_type}".lower()
    if "risk_captital" in text or "risk_capital" in text:
        return "risk_capital_transfer"
    if "burst" in text or "liquidation" in text or "loss" in text:
        return "liquidation_loss"
    if "open_long" in text or "open_short" in text:
        return "open_position_fee_only"
    if "close_long" in text or "close_short" in text:
        return "close_position_pnl_fee"
    if "contract_settle_fee" in text or "derivative fee" in text:
        return "funding_or_settlement_fee"
    if "strategy" in text:
        return "strategy_transfer"
    return "other"


def sum_by(rows: list[dict[str, Any]], key: str) -> dict[str, Decimal]:
    result: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        result[str(row.get(key) or "")] += dec(row["balance_effect"])
    return dict(result)


def stringify(values: dict[str, Decimal]) -> dict[str, str]:
    return {key: str(value) for key, value in sorted(values.items())}


def signed_from_payload(payload: dict[str, Any]) -> Decimal:
    qty = dec(payload.get("quantity"))
    side = str(payload.get("side") or "").lower()
    if side in {"out", "sell"}:
        return -abs(qty)
    return abs(qty)


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


if __name__ == "__main__":
    main()
