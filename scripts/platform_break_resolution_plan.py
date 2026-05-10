#!/usr/bin/env python3
"""Classify platform balance breaks into actionable resolution buckets."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CREATED_DATE = "2026-05-09"
SIM_JSON = ROOT / "var" / f"platform_balance_simulation_{CREATED_DATE}.json"
CANDIDATES_JSON = ROOT / "var" / f"platform_transfer_candidates_{CREATED_DATE}.json"
AI_JSON = ROOT / "var" / f"ai_platform_reconciliation_review_{CREATED_DATE}.json"
OUTPUT_JSON = ROOT / "var" / f"platform_break_resolution_plan_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"135_PLATFORM_BREAK_RESOLUTION_PLAN_{CREATED_DATE}.md"
DUST_LIMITS = {
    "USDT": Decimal("0.01"),
    "USDC": Decimal("0.01"),
    "BUSD": Decimal("1"),
    "BTC": Decimal("0.00001"),
    "HNT": Decimal("1"),
    "SOL": Decimal("0.01"),
}


def main() -> None:
    simulation = read_json(SIM_JSON)
    candidates = read_json(CANDIDATES_JSON)
    ai = read_json(AI_JSON)
    rows = classify_breaks(simulation.get("negative_assets") or [], candidates.get("negative_break_links") or [], ai.get("hypotheses") or [])
    audit = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "break_count": len(rows),
        "status_counts": count_by(rows, "resolution_status"),
        "priority_counts": count_by(rows, "priority"),
        "rows": rows,
    }
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(DOC_PATH), "breaks": len(rows), "status_counts": audit["status_counts"]}, ensure_ascii=False, indent=2))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def classify_breaks(break_assets: list[dict[str, Any]], break_links: list[dict[str, Any]], ai_hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    links_by_key = {(row.get("platform"), row.get("asset")): row for row in break_links}
    ai_by_key = {(row.get("platform"), row.get("asset")): row for row in ai_hypotheses}
    rows = []
    for item in break_assets:
        platform = str(item.get("platform") or "")
        asset = str(item.get("asset") or "")
        final_balance = dec(item.get("final_balance"))
        worst_balance = dec(item.get("worst_balance"))
        first = item.get("first_negative") or {}
        link = links_by_key.get((platform, asset), {})
        ai = ai_by_key.get((platform, asset), {})
        direct = int(link.get("direct_candidate_count") or 0)
        nearby = int(link.get("nearby_candidate_count") or 0)
        status, priority, action = classify(platform, asset, final_balance, worst_balance, direct, nearby, first)
        rows.append(
            {
                "platform": platform,
                "asset": asset,
                "resolution_status": status,
                "priority": priority,
                "final_balance": plain(final_balance),
                "worst_balance": plain(worst_balance),
                "first_negative_timestamp_utc": first.get("timestamp_utc", ""),
                "first_negative_ledger_id": first.get("ledger_id", ""),
                "first_negative_tx_id": first.get("tx_id", ""),
                "direct_candidate_count": direct,
                "nearby_candidate_count": nearby,
                "recommended_action": action,
                "ai_likely_cause": ai.get("likely_cause", ""),
                "ai_next_action": ai.get("next_action", ""),
            }
        )
    return sorted(rows, key=lambda row: (priority_rank(row["priority"]), status_rank(row["resolution_status"]), row["platform"], row["asset"]))


def classify(
    platform: str,
    asset: str,
    final_balance: Decimal,
    worst_balance: Decimal,
    direct: int,
    nearby: int,
    first: dict[str, Any],
) -> tuple[str, str, str]:
    abs_final = abs(final_balance)
    dust_limit = DUST_LIMITS.get(asset, Decimal("0.000001"))
    if abs_final <= dust_limit and abs(worst_balance) <= max(dust_limit, Decimal("1")):
        return (
            "dust_or_rounding_review",
            "low",
            "Als Dust/Rundung markieren, wenn TX-Beleg und finaler Kontostand plausibel sind.",
        )
    if direct > 0:
        return (
            "candidate_transfer_review",
            "high",
            "Direkten Transfer-Kandidaten pruefen; bei Beleggleichheit als internen Transfer verknuepfen.",
        )
    if nearby > 0:
        return (
            "nearby_transfer_context",
            "medium",
            "Nahe Transfer-Kandidaten pruefen; wahrscheinlich Plattform-/Fee- oder Doppelzeilen-Effekt.",
        )
    if platform == "pionex":
        return (
            "opening_balance_or_bot_history_needed",
            "high" if asset == "USDT" else "medium",
            "Pionex Start-/Bot-Historie oder Opening-Balance-Beleg beschaffen; ohne Beleg nicht finalisieren.",
        )
    if platform == "bitget":
        return (
            "bitget_history_needed",
            "high",
            "Bitget Export/API-Historie und Supportdaten abgleichen; Bot-/Margin-Kontext pruefen.",
        )
    if platform == "solana_wallet":
        return (
            "onchain_counterflow_needed",
            "high",
            "Solscan Detail fuer Bruch-TX und Gegenwallets pruefen; fehlende Token-Transfers oder Swap-Legs importieren.",
        )
    return (
        "source_gap_review",
        "medium",
        "Quellhistorie und Referenzexporte fuer diese Plattform/Asset-Kombination pruefen.",
    )


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        result[value] = result.get(value, 0) + 1
    return result


def priority_rank(value: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(str(value), 9)


def status_rank(value: str) -> int:
    order = {
        "candidate_transfer_review": 0,
        "opening_balance_or_bot_history_needed": 1,
        "bitget_history_needed": 2,
        "onchain_counterflow_needed": 3,
        "nearby_transfer_context": 4,
        "source_gap_review": 5,
        "dust_or_rounding_review": 6,
    }
    return order.get(str(value), 9)


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Platform Break Resolution Plan - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Bruchstellen: `{audit['break_count']}`",
        f"- Status: `{audit['status_counts']}`",
        f"- Prioritaeten: `{audit['priority_counts']}`",
        "",
        "## Arbeitsliste",
        "",
    ]
    for row in audit["rows"]:
        lines.append(
            f"- `{row['priority']}` `{row['resolution_status']}` `{row['platform']}` `{row['asset']}` "
            f"final `{row['final_balance']}` worst `{row['worst_balance']}` "
            f"direct `{row['direct_candidate_count']}` nearby `{row['nearby_candidate_count']}` "
            f"first `{row['first_negative_timestamp_utc']}`"
        )
        lines.append(f"  - Aktion: {row['recommended_action']}")
    lines += [
        "",
        "## Naechster Ablauf",
        "",
        "1. High ohne Kandidat zuerst klaeren: Pionex USDT Opening/Bot-Historie, Bitget BTC 2024, Solana JUP Onchain-Gegenfluss.",
        "2. Medium-Kontext pruefen: Binance SOL, Bitget HNT, Solana HNT.",
        "3. Low/Dust erst nach den grossen Luecken final markieren.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
