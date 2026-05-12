#!/usr/bin/env python3
"""Build a concise readiness status for producing tax reports."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

BALANCE_JSON = ROOT / "var" / "chronological_balance_break_audit_after_binance_btc_vet_win_reconstruction_2026-05-09.json"
TRANSIENT_JSON = ROOT / "var" / "transient_balance_undercoverage_audit_2026-05-09.json"
CEX_JSON = ROOT / "var" / "cex_compliance_coverage_2026-05-08.json"
AI_JSON = ROOT / "var" / "ai_cex_compliance_review_2026-05-08.json"
JUPITER_2025_COVERAGE_JSON = ROOT / "var" / "jupiter_2025_solscan_coverage_audit_2026-05-08.json"
OUTPUT_JSON = ROOT / "var" / "tax_report_readiness_status_2026-05-09.json"
OUTPUT_DOC = ROOT / "docs" / "126_TAX_REPORT_READINESS_STATUS_2026-05-09.md"


def main() -> None:
    raw_events = STORE.list_raw_events()
    reviewed, review_summary = apply_review_actions(raw_events)
    effective, override_count = apply_tax_event_overrides(reviewed)
    balance = _load_json(BALANCE_JSON)
    transient = _load_json(TRANSIENT_JSON)
    cex = _load_json(CEX_JSON)
    ai = _load_json(AI_JSON)
    candidates = _load_candidates()

    negative_assets = [
        {
            "asset": row.get("asset"),
            "final_balance": row.get("final_balance"),
            "first_negative": row.get("first_negative"),
        }
        for row in balance.get("asset_reports", [])
        if _is_negative(row.get("final_balance"))
    ]
    blocking_candidates = [
        row
        for row in candidates.values()
        if row.get("tax_effective") is False
        and str(row.get("status") or "")
        in {
            "needs_evidence",
            "needs_review",
            "needs_evidence_or_explicit_review_decision",
            "ready_for_explicit_review_decision",
        }
    ]
    open_transient_assets = [
        {"asset": row.get("asset"), "worst_balance": (row.get("worst_balance") or {}).get("balance_after")}
        for row in transient.get("asset_reports", [])
        if _is_negative((row.get("worst_balance") or {}).get("balance_after"))
    ]
    coverage_evidence = _coverage_evidence()
    coverage_blockers = _coverage_blockers(cex, coverage_evidence)
    status = _overall_status(negative_assets, blocking_candidates, coverage_blockers)

    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "raw_event_count": len(raw_events),
        "effective_event_count": len(effective),
        "review_action_summary": review_summary,
        "override_count": override_count,
        "negative_final_assets": negative_assets,
        "open_transient_assets": open_transient_assets,
        "balance_audit": str(BALANCE_JSON),
        "transient_audit": str(TRANSIENT_JSON),
        "coverage_report": str(ROOT / "docs" / "54_CEX_COMPLIANCE_COVERAGE_2026-05-08.md"),
        "ai_review_report": str(ROOT / "docs" / "55_AI_CEX_COMPLIANCE_REVIEW_2026-05-08.md"),
        "ai_review_status": ai.get("status"),
        "ai_usage": ai.get("usage"),
        "open_review_candidates": sorted(blocking_candidates, key=lambda row: str(row.get("candidate_id") or "")),
        "coverage_blockers": coverage_blockers,
        "coverage_evidence": coverage_evidence,
        "decision": _decision(status, negative_assets, open_transient_assets, blocking_candidates, coverage_blockers),
    }
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_DOC.write_text(_render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(OUTPUT_DOC), "status": status}, indent=2, ensure_ascii=False))


def _coverage_evidence() -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    jupiter_2025 = _load_json(JUPITER_2025_COVERAGE_JSON)
    if jupiter_2025.get("coverage_decision") == "no_2025_solscan_import_needed":
        evidence["jupiter:2025"] = {
            "status": "covered_by_solscan_true_missing_audit",
            "report": str(ROOT / "docs" / "80_JUPITER_2025_SOLSCAN_COVERAGE_AUDIT_2026-05-08.md"),
            "note": "True-Missing-Preview enthaelt 0 Zeilen fuer 2025; alte Preview-Signaturen sind lokal vorhanden.",
        }
    candidates = _load_candidates()
    pionex_opening = candidates.get("pionex-usdt-opening-balance-2021-12-28")
    if _is_approved_non_tax_inventory_normalization(pionex_opening):
        decision = pionex_opening.get("review_decision") if isinstance(pionex_opening, dict) else {}
        decided_at = str(decision.get("decided_at_utc") or "") if isinstance(decision, dict) else ""
        for year in ("2021", "2022"):
            evidence[f"pionex:{year}"] = {
                "status": "approved_non_tax_inventory_normalization",
                "report": str(ROOT / "docs" / "157_PIONEX_OPENING_DECISION_DOSSIER_2026-05-09.md"),
                "note": f"Explizite Review-Entscheidung fuer Pionex Opening-Kandidat; tax_effective=false; decided_at={decided_at}",
            }
    return evidence


def _coverage_blockers(cex: dict[str, Any], evidence: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    matrix = cex.get("matrix") if isinstance(cex.get("matrix"), dict) else {}
    blockers: list[dict[str, Any]] = []
    for platform, years in matrix.items():
        if not isinstance(years, dict):
            continue
        for year, cell in years.items():
            if not isinstance(cell, dict):
                continue
            statuses = [str(item) for item in cell.get("statuses", [])]
            reasons = [str(item) for item in cell.get("reasons", [])]
            evidence_key = f"{platform}:{year}"
            if evidence_key in evidence and statuses == ["partial", "manual_review"]:
                continue
            if evidence_key in evidence and "opening_balance_required" in statuses:
                continue
            is_blocker = (
                "opening_balance_required" in statuses
                or "support_required" in statuses
                or ("manual_review" in statuses and platform in {"bitget", "jupiter"})
            )
            if is_blocker:
                blockers.append(
                    {
                        "platform": platform,
                        "year": str(year),
                        "statuses": statuses,
                        "effective_event_count": cell.get("effective_event_count"),
                        "primary_event_count": cell.get("primary_event_count"),
                        "reference_event_count": cell.get("reference_event_count"),
                        "period": _period(cell),
                        "reasons": reasons,
                    }
                )
    return sorted(blockers, key=lambda row: (row["platform"], row["year"]))


def _overall_status(negative_assets: list[dict[str, Any]], candidates: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> str:
    if negative_assets:
        return "blocked_by_active_source_balance_gaps"
    if any(row.get("platform") == "pionex" and row.get("asset") == "USDT" for row in candidates):
        return "blocked_by_pionex_opening_evidence"
    if any(row.get("platform") == "pionex" and "opening_balance_required" in row.get("statuses", []) for row in blockers):
        return "blocked_by_pionex_opening_evidence"
    if any(row.get("platform") == "bitget" and row.get("year") == "2025" for row in blockers):
        return "blocked_by_bitget_2025_support"
    return "ready_with_documented_residual_risk"


def _is_approved_non_tax_inventory_normalization(row: Any) -> bool:
    if not isinstance(row, dict):
        return False
    decision = row.get("review_decision") if isinstance(row.get("review_decision"), dict) else {}
    return (
        str(row.get("status") or "") == "approved_non_tax_inventory_normalization"
        and str(decision.get("decision") or "") == "approve_non_tax_inventory_normalization"
        and row.get("tax_effective") is False
    )


def _decision(
    status: str,
    negative_assets: list[dict[str, Any]],
    transient_assets: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "can_generate_draft_report": True,
        "can_mark_final_clean_report": status == "ready_with_documented_residual_risk",
        "must_not_auto_book": [
            "Pionex opening balance candidate",
            "Bitget missing bot/trade details",
        ],
        "next_human_decisions": [
            "Pionex: provide account/bot start evidence or explicitly approve documented non-tax inventory normalization.",
            "Bitget 2025: wait for support export or approve documented reconstruction limits.",
        ],
        "negative_asset_count": len(negative_assets),
        "open_transient_asset_count": len(transient_assets),
        "review_candidate_count": len(candidates),
        "coverage_blocker_count": len(blockers),
    }


def _render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Tax Report Readiness Status - 2026-05-09",
        "",
        "## Summary",
        "",
        f"- Status: `{audit['status']}`",
        f"- RAW-Events: `{audit['raw_event_count']}`",
        f"- Effektive Events: `{audit['effective_event_count']}`",
        f"- Override-Count: `{audit['override_count']}`",
        f"- Balance-Audit: `{audit['balance_audit']}`",
        f"- Transient-Audit: `{audit['transient_audit']}`",
        f"- CEX-Coverage: `{audit['coverage_report']}`",
        f"- KI-Review: `{audit['ai_review_report']}`",
        "",
        "## Entscheidung",
        "",
        f"- Draft-Report erzeugbar: `{audit['decision']['can_generate_draft_report']}`",
        f"- Als final sauber markierbar: `{audit['decision']['can_mark_final_clean_report']}`",
        "",
        "Ein Entwurf ist technisch erzeugbar. Als final sauber sollte der Report erst gelten, wenn aktive Quellen keine materiellen Negativbestaende mehr zeigen und Pionex-Opening/USDT-Rest sowie Bitget-2025 fachlich entschieden bzw. durch Supportdaten belegt sind.",
        "",
        "## Negative Endbestaende",
        "",
    ]
    if audit["negative_final_assets"]:
        for row in audit["negative_final_assets"]:
            lines.append(f"- `{row['asset']}`: `{row['final_balance']}`")
    else:
        lines.append("- Keine negativen Endbestaende im aktuellen Audit.")
    lines += ["", "## Offene transiente Crypto-Unterdeckungen", ""]
    if audit["open_transient_assets"]:
        for row in audit["open_transient_assets"]:
            lines.append(f"- `{row['asset']}`: worst `{row['worst_balance']}`")
    else:
        lines.append("- Keine offenen transienten Crypto-Unterdeckungen im aktuellen Audit.")
    lines += ["", "## Offene Review-Kandidaten", ""]
    for row in audit["open_review_candidates"]:
        lines.append(
            f"- `{row.get('candidate_id')}`: `{row.get('asset')}` `{row.get('quantity_delta')}`, "
            f"status `{row.get('status')}`, tax_effective `{row.get('tax_effective')}`"
        )
    lines += ["", "## Coverage-Blocker", ""]
    for row in audit["coverage_blockers"]:
        lines.append(
            f"- `{row['platform']}` `{row['year']}`: `{', '.join(row['statuses'])}`, "
            f"Events `{row.get('effective_event_count')}`, Zeitraum `{row.get('period')}`"
        )
    if audit.get("coverage_evidence"):
        lines += ["", "## Erledigte Coverage-Pruefungen", ""]
        for key, row in sorted(audit["coverage_evidence"].items()):
            lines.append(f"- `{key}`: `{row.get('status')}`, Report `{row.get('report')}`")
    lines += ["", "## Naechste menschliche Entscheidungen", ""]
    for item in audit["decision"]["next_human_decisions"]:
        lines.append(f"- {item}")
    lines += ["", "## Nicht automatisch buchen", ""]
    for item in audit["decision"]["must_not_auto_book"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _load_candidates() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting("runtime.balance_adjustment_candidates")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items() if isinstance(value, dict)}


def _period(cell: dict[str, Any]) -> str:
    first = str(cell.get("first_event_utc") or "")
    last = str(cell.get("last_event_utc") or "")
    if first and last:
        return f"{first}..{last}"
    return "-"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _is_negative(value: Any) -> bool:
    try:
        return Decimal(str(value)) < 0
    except (InvalidOperation, ValueError):
        return False


if __name__ == "__main__":
    main()
