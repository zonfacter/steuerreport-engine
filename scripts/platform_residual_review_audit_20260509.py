#!/usr/bin/env python3
"""Document non-critical platform residuals after the major source gaps are closed."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CREATED_DATE = "2026-05-09"
PLAN_JSON = ROOT / "var" / f"platform_break_resolution_plan_{CREATED_DATE}.json"
LEDGER_JSONL = ROOT / "var" / f"platform_ledger_{CREATED_DATE}.jsonl"
BALANCE_JSON = ROOT / "var" / "chronological_balance_break_audit_after_binance_btc_vet_win_reconstruction_2026-05-09.json"
HNT_JSON = ROOT / "var" / f"hnt_platform_context_audit_{CREATED_DATE}.json"
BINANCE_HNT_JSON = ROOT / "var" / f"binance_hnt_residual_audit_{CREATED_DATE}.json"
OUTPUT_JSON = ROOT / "var" / f"platform_residual_review_audit_{CREATED_DATE}.json"
OUTPUT_MD = ROOT / "docs" / f"166_PLATFORM_RESIDUAL_REVIEW_AUDIT_{CREATED_DATE}.md"


MATERIALITY = {
    "USDT": Decimal("0.01"),
    "USDC": Decimal("0.01"),
    "HNT": Decimal("2"),
}


def main() -> None:
    plan = load_json(PLAN_JSON)
    ledger = load_jsonl(LEDGER_JSONL)
    balance = load_json(BALANCE_JSON)
    hnt = load_json(HNT_JSON)
    binance_hnt = load_json(BINANCE_HNT_JSON)
    residuals = []
    for row in plan.get("rows", []):
        platform = str(row.get("platform") or "")
        asset = str(row.get("asset") or "")
        if platform == "pionex" and asset == "USDT":
            continue
        residuals.append(classify_residual(row, ledger, balance, hnt, binance_hnt))
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "hard_blocker": {
            "platform": "pionex",
            "asset": "USDT",
            "status": "opening_balance_or_bot_history_needed",
            "report": "docs/157_PIONEX_OPENING_DECISION_DOSSIER_2026-05-09.md",
        },
        "residual_count": len(residuals),
        "status_counts": count_by(residuals, "review_classification"),
        "residuals": residuals,
        "global_balance_context": {
            "negative_final_assets": balance.get("negative_final_assets", 0),
            "asset_reports_checked": len(balance.get("asset_reports", [])),
            "btc_report": find_asset(balance, "BTC"),
            "hnt_report": find_asset(balance, "HNT"),
            "usdt_report": find_asset(balance, "USDT"),
        },
        "decision": {
            "can_auto_import": False,
            "can_treat_as_documented_residuals": all(
                item["review_classification"] in {"documented_rounding_dust", "documented_platform_context_residual"}
                for item in residuals
            ),
            "tax_effective_adjustment_recommended": False,
            "note": "No automatic tax-effective adjustment is recommended for these platform-local residuals.",
        },
    }
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(
        json.dumps(
            {"json": str(OUTPUT_JSON), "doc": str(OUTPUT_MD), "residual_count": len(residuals), "status_counts": audit["status_counts"]},
            ensure_ascii=False,
            indent=2,
        )
    )


def classify_residual(
    row: dict[str, Any],
    ledger: list[dict[str, Any]],
    balance: dict[str, Any],
    hnt: dict[str, Any],
    binance_hnt: dict[str, Any],
) -> dict[str, Any]:
    platform = str(row.get("platform") or "")
    asset = str(row.get("asset") or "")
    worst = abs(dec(row.get("worst_balance")))
    threshold = MATERIALITY.get(asset, Decimal("0.000001"))
    first = str(row.get("first_negative_timestamp_utc") or "")
    events = context_events(ledger, platform, asset, first, limit=14)
    global_asset = find_asset(balance, asset)
    classification = "needs_more_context"
    reason = "Residual exceeds configured dust threshold or lacks supporting context."
    if worst <= threshold:
        classification = "documented_rounding_dust"
        reason = f"Worst platform-local residual {plain(worst)} {asset} is within materiality threshold {plain(threshold)} {asset}."
    if platform == "pionex" and asset == "HNT" and worst <= threshold:
        classification = "documented_rounding_dust"
        reason = "Small Pionex HNT bot residual; should be decided together with Pionex opening review, not booked as a separate taxable inflow."
    if platform == "binance" and asset == "HNT":
        classification = "documented_platform_context_residual"
        reason = str((binance_hnt.get("decision") or {}).get("reason") or "")
    return {
        "platform": platform,
        "asset": asset,
        "priority": row.get("priority"),
        "resolution_status": row.get("resolution_status"),
        "review_classification": classification,
        "final_balance": row.get("final_balance"),
        "worst_balance": row.get("worst_balance"),
        "materiality_threshold": plain(threshold),
        "first_negative_timestamp_utc": first,
        "first_negative_tx_id": row.get("first_negative_tx_id"),
        "global_final_balance": global_asset.get("final_balance"),
        "global_first_negative": global_asset.get("first_negative"),
        "supporting_report": supporting_report(platform, asset),
        "reason": reason,
        "recommendation": recommendation(classification, platform, asset),
        "context_events": events,
        "hnt_platform_context": hnt.get("global_hnt") if asset == "HNT" else {},
    }


def supporting_report(platform: str, asset: str) -> str:
    if platform == "binance" and asset == "HNT":
        return "docs/163_BINANCE_HNT_RESIDUAL_AUDIT_2026-05-09.md"
    if platform == "pionex" and asset == "HNT":
        return "docs/158_HNT_PLATFORM_CONTEXT_AUDIT_2026-05-09.md"
    if platform == "solana_wallet":
        return "docs/135_PLATFORM_BREAK_RESOLUTION_PLAN_2026-05-09.md"
    return ""


def recommendation(classification: str, platform: str, asset: str) -> str:
    if classification == "documented_rounding_dust":
        return "Document as non-material platform-local dust/rounding; do not import a tax-effective adjustment."
    if classification == "documented_platform_context_residual":
        return "Keep as documented platform-context residual; do not book a global asset inflow unless a primary source appears."
    return f"Continue source search for {platform}/{asset} before marking final."


def context_events(ledger: list[dict[str, Any]], platform: str, asset: str, timestamp: str, *, limit: int) -> list[dict[str, str]]:
    rows = [row for row in ledger if str(row.get("platform") or "") == platform and str(row.get("asset") or "") == asset]
    if not rows:
        return []
    selected_index = 0
    if timestamp:
        for index, row in enumerate(rows):
            if str(row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or "") >= timestamp:
                selected_index = index
                break
    start = max(0, selected_index - limit // 2)
    end = min(len(rows), selected_index + limit // 2 + 1)
    return [
        {
            "ledger_id": str(row.get("ledger_id") or ""),
            "timestamp_utc": str(row.get("normalized_timestamp_utc") or row.get("timestamp_utc") or ""),
            "event_type": str(row.get("event_type") or ""),
            "source": str(row.get("source") or ""),
            "quantity_delta": str(row.get("quantity_delta") or ""),
            "tx_id": str(row.get("tx_id") or ""),
        }
        for row in rows[start:end]
    ]


def find_asset(balance: dict[str, Any], asset: str) -> dict[str, Any]:
    for row in balance.get("asset_reports", []):
        if str(row.get("asset") or "").upper() == asset.upper():
            return {
                "asset": row.get("asset"),
                "final_balance": row.get("final_balance"),
                "first_negative": row.get("first_negative"),
                "worst_balance": row.get("worst_balance"),
            }
    return {}


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items()))


def load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Platform Residual Review Audit - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Residuals ohne Pionex-USDT-Hardblocker: `{audit['residual_count']}`",
        f"- Klassifikation: `{audit['status_counts']}`",
        f"- Automatisch importieren: `{audit['decision']['can_auto_import']}`",
        f"- Steuerwirksames Adjustment empfohlen: `{audit['decision']['tax_effective_adjustment_recommended']}`",
        "",
        "## Harter Blocker",
        "",
        "- `pionex / USDT`: Opening-/Bot-Startbestand bleibt entscheidungspflichtig; siehe `docs/157_PIONEX_OPENING_DECISION_DOSSIER_2026-05-09.md`.",
        "",
        "## Residuals",
        "",
    ]
    for row in audit["residuals"]:
        lines.append(
            f"- `{row['review_classification']}` `{row['platform']}` `{row['asset']}` "
            f"final `{row['final_balance']}` worst `{row['worst_balance']}` threshold `{row['materiality_threshold']}`"
        )
        lines.append(f"  - Grund: {row['reason']}")
        lines.append(f"  - Empfehlung: {row['recommendation']}")
        if row.get("supporting_report"):
            lines.append(f"  - Report: `{row['supporting_report']}`")
    lines += [
        "",
        "## Bewertung",
        "",
        "- Diese Residuals sind plattformlokale Rest-/Rundungs- oder Kontextfaelle.",
        "- Sie werden nicht als neue steuerwirksame Zufluesse importiert.",
        "- Final sauber bleibt weiterhin von Pionex-USDT und den Coverage-Entscheidungen abhaengig.",
        "",
    ]
    return "\n".join(lines)


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def plain(value: Decimal) -> str:
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


if __name__ == "__main__":
    main()
