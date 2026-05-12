#!/usr/bin/env python3
"""Create a focused Bitget USDT strategy/internal transfer chain report."""

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

JSON_PATH = ROOT / "var" / "bitget_usdt_strategy_chain_2026-05-08.json"
DOC_PATH = ROOT / "docs" / "59_BITGET_USDT_STRATEGY_CHAIN_2026-05-08.md"


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
        text = " ".join([str(payload.get("source") or ""), str(payload.get("event_type") or ""), json.dumps(raw_row, ensure_ascii=False)]).lower()
        if "bitget" not in text:
            continue
        if str(payload.get("asset") or raw_row.get("coin") or "").upper() != "USDT":
            continue
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if not ts.startswith("2025"):
            continue
        event_type = str(payload.get("event_type") or "")
        business_type = str(raw_row.get("businessType") or raw_row.get("spotTaxType") or "")
        relevant = any(token in f"{event_type} {business_type}".lower() for token in ("deposit", "withdraw", "transfer", "trans_", "strategy", "risk_captital"))
        if not relevant:
            continue
        amount = dec(raw_row.get("amount") if "amount" in raw_row else payload.get("quantity"))
        fee = dec(raw_row.get("fee"))
        source = str(payload.get("source") or "")
        is_reference = source.lower() == "blockpit"
        rows.append(
            {
                "timestamp_utc": ts,
                "source": source,
                "event_type": event_type,
                "business_type": business_type,
                "balance_effect": str(amount + fee),
                "gross_amount": str(amount),
                "fee": str(fee),
                "reported_balance": str(raw_row.get("balance") or ""),
                "id": str(raw_row.get("billId") or raw_row.get("id") or raw_row.get("bizOrderId") or raw_row.get("orderId") or ""),
                "classification": classify(event_type, business_type, is_reference),
                "is_reference": is_reference,
            }
        )
    rows.sort(key=lambda row: (row["timestamp_utc"], row["source"], row["id"]))
    return rows


def build_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    primary = [row for row in rows if not row["is_reference"]]
    reference = [row for row in rows if row["is_reference"]]
    class_net: dict[str, Decimal] = {}
    running = Decimal("0")
    timeline = []
    for row in primary:
        effect = dec(row["balance_effect"])
        running += effect
        class_net[row["classification"]] = class_net.get(row["classification"], Decimal("0")) + effect
        timeline.append({**row, "running_primary_effect": str(running)})
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": "Bitget 2025 USDT deposits/transfers/strategy/internal chain from available records.",
        "row_count": len(rows),
        "primary_count": len(primary),
        "reference_count": len(reference),
        "classification_counts": dict(Counter(row["classification"] for row in rows).most_common()),
        "classification_net_primary": {key: str(value) for key, value in sorted(class_net.items())},
        "net_primary_effect": str(sum(dec(row["balance_effect"]) for row in primary)),
        "timeline": timeline,
        "reference_rows": reference,
        "interpretation": [
            "The 2025 USDT chain shows external deposits and internal transfers into exchange/strategy contexts.",
            "Strategy transfer pair on 2025-02-22 is nearly matched: -249.59902416 to strategy and +248.38877526 from strategy, net -1.21024890 USDT.",
            "Risk capital transfer on 2025-02-27 moves -222.10227813 USDT and coincides with derivative loss/liquidation area in the broader Bitget audit.",
            "This chain supports a reconstruction, but it is not a replacement for missing bot fill details.",
        ],
    }


def render(audit: dict[str, Any]) -> str:
    lines = [
        "# Bitget USDT Strategy Chain - 2026-05-08",
        "",
        "## Zweck",
        "",
        "Fokussierte USDT-Kette fuer Bitget 2025: Deposits, Withdrawals, interne Exchange-Transfers, Strategy-Transfers und Risk-Capital-Transfers.",
        "Es werden keine fehlenden Bot-Fills erzeugt.",
        "",
        "## Summary",
        "",
        f"- JSON: `{JSON_PATH}`",
        f"- Zeilen: `{audit['row_count']}`",
        f"- Primaer: `{audit['primary_count']}`",
        f"- Referenz: `{audit['reference_count']}`",
        f"- Klassen: `{json.dumps(audit['classification_counts'], ensure_ascii=False)}`",
        f"- Net Primary Effect: `{audit['net_primary_effect']} USDT`",
        f"- Net je Klasse: `{json.dumps(audit['classification_net_primary'], ensure_ascii=False)}`",
        "",
        "## Primaer-Timeline",
        "",
        "| Zeit | Typ | Business | Effekt USDT | Gemeldeter Balance | Running Effekt | ID |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in audit["timeline"]:
        lines.append(
            f"| `{row['timestamp_utc']}` | `{row['event_type']}` | `{row['business_type']}` | "
            f"`{row['balance_effect']}` | `{row['reported_balance']}` | `{row['running_primary_effect']}` | `{row['id']}` |"
        )
    lines += ["", "## Referenzzeilen", ""]
    if not audit["reference_rows"]:
        lines.append("- Keine.")
    else:
        for row in audit["reference_rows"]:
            lines.append(
                f"- `{row['timestamp_utc']}` `{row['source']}` `{row['event_type']}` effect `{row['balance_effect']}` id `{row['id']}`"
            )
    lines += ["", "## Interpretation", ""]
    lines += [f"- {item}" for item in audit["interpretation"]]
    lines.append("")
    return "\n".join(lines)


def classify(event_type: str, business_type: str, is_reference: bool) -> str:
    if is_reference:
        return "reference"
    text = f"{event_type} {business_type}".lower()
    if "trans_to_strategy" in text or "trans_from_strategy" in text:
        return "strategy_transfer"
    if "trans_to_exchange" in text or "trans_from_exchange" in text:
        return "internal_exchange_transfer"
    if "risk_captital" in text or "risk_capital" in text:
        return "risk_capital_transfer"
    if "deposit" in text:
        return "deposit_or_auto_in"
    if "withdraw" in text:
        return "withdraw_or_auto_out"
    if "transfer" in text:
        return "transfer"
    return "other"


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


if __name__ == "__main__":
    main()
