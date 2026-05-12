#!/usr/bin/env python3
"""Build a decision dossier for the remaining Pionex USDT opening blocker."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE  # noqa: E402

CREATED_DATE = "2026-05-09"
CANDIDATE_ID = "pionex-usdt-opening-balance-2021-12-28"
GAP_JSON = ROOT / "var" / f"pionex_usdt_platform_gap_current_{CREATED_DATE}.json"
READINESS_JSON = ROOT / "var" / f"tax_report_readiness_status_{CREATED_DATE}.json"
TRANSIENT_JSON = ROOT / "var" / f"transient_balance_undercoverage_audit_{CREATED_DATE}.json"
OUTPUT_JSON = ROOT / "var" / f"pionex_opening_decision_dossier_{CREATED_DATE}.json"
OUTPUT_MD = ROOT / "docs" / f"157_PIONEX_OPENING_DECISION_DOSSIER_{CREATED_DATE}.md"
LLM_URL = "http://192.168.2.203:11435/v1/chat/completions"
LLM_MODEL = "qwen3.6-35b-a3b-iq4xs"


def main() -> None:
    gap = load_json(GAP_JSON)
    readiness = load_json(READINESS_JSON)
    transient = load_json(TRANSIENT_JSON)
    candidate = load_candidate(CANDIDATE_ID)
    dossier = build_dossier(gap, readiness, transient, candidate)
    dossier["local_ai_review"] = run_local_ai_review(dossier)
    OUTPUT_JSON.write_text(json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(render_doc(dossier), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(OUTPUT_MD), "decision_status": dossier["recommended_candidate_update"]["status"], "ai_status": dossier["local_ai_review"]["status"]}, ensure_ascii=False, indent=2))


def build_dossier(
    gap: dict[str, Any],
    readiness: dict[str, Any],
    transient: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    visible_deposits = gap.get("deposits_until_worst") if isinstance(gap.get("deposits_until_worst"), list) else []
    visible_deposit_sum = sum(dec(row.get("quantity_delta")) for row in visible_deposits)
    required_opening = dec(gap.get("required_opening_to_avoid_negative"))
    uncovered_after_visible_deposits = required_opening - visible_deposit_sum
    if uncovered_after_visible_deposits < 0:
        uncovered_after_visible_deposits = Decimal("0")
    open_transient = [
        row
        for row in transient.get("asset_reports", [])
        if str(row.get("asset") or "").upper() == "USDT"
    ]
    evidence = {
        "current_gap_report": str(GAP_JSON.relative_to(ROOT)),
        "current_readiness_report": str((ROOT / "docs" / f"126_TAX_REPORT_READINESS_STATUS_{CREATED_DATE}.md").relative_to(ROOT)),
        "transient_report": str((ROOT / "docs" / f"119_TRANSIENT_BALANCE_UNDERCOVERAGE_AUDIT_{CREATED_DATE}.md").relative_to(ROOT)),
        "reconstruction_report": "docs/84_PIONEX_OPENING_RECONSTRUCTION_AUDIT_2026-05-08.md",
        "opening_evidence_refresh": "docs/78_PIONEX_OPENING_EVIDENCE_REFRESH_2026-05-08.md",
        "current_final_clean_balance_audit": "docs/156_CHRONOLOGICAL_BALANCE_BREAK_AUDIT_AFTER_BINANCE_SOURCE_CHAIN_RECONSTRUCTION_2026-05-09.md",
        "first_negative": gap.get("first_negative") or {},
        "worst_balance": gap.get("worst_balance") or {},
        "visible_deposits_until_worst": visible_deposits,
        "visible_deposit_sum_until_worst_usdt": plain(visible_deposit_sum),
        "required_opening_to_avoid_negative_usdt": plain(required_opening),
        "uncovered_by_visible_deposits_until_worst_usdt": plain(uncovered_after_visible_deposits),
        "pionex_event_count": gap.get("event_count"),
        "pionex_final_usdt_balance": gap.get("final_balance"),
        "negative_segment_count": gap.get("negative_segment_count"),
        "yearly_net": gap.get("yearly_net") or {},
        "readiness_status": readiness.get("status"),
        "global_negative_final_assets": readiness.get("negative_final_assets") or [],
        "global_usdt_transient": open_transient[0] if open_transient else {},
        "candidate_before": candidate,
    }
    assessment = [
        "Global final balances are clean; the remaining blocker is platform-local Pionex USDT chronology.",
        "The Pionex export stream is internally consistent and close to later API current balances, but it lacks a primary pre-bot account snapshot.",
        "Visible Pionex deposits until the worst point do not explain the bot capital requirement.",
        "A tax report can be drafted, but final clean status needs either external Pionex evidence or an explicit non-tax inventory-normalization decision.",
    ]
    recommended_update = {
        "candidate_id": CANDIDATE_ID,
        "platform": "pionex",
        "asset": "USDT",
        "quantity_delta": plain(required_opening),
        "effective_timestamp_utc": str((gap.get("first_negative") or {}).get("normalized_timestamp_utc") or "2021-12-28T00:49:12+00:00").replace("12+00:00", "11+00:00"),
        "adjustment_type": "opening_balance_candidate",
        "status": "ready_for_explicit_review_decision",
        "reason_code": "missing_pionex_bot_start_capital",
        "note": (
            "Decision-ready Pionex USDT opening candidate. Current platform ledger requires "
            f"{plain(required_opening)} USDT to avoid negative bot chronology; visible deposits until worst sum "
            f"{plain(visible_deposit_sum)} USDT. Candidate remains non-tax-effective and must not be booked "
            "without explicit review approval or primary Pionex evidence."
        ),
        "evidence": evidence,
        "tax_effective": False,
    }
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "decision_state": "explicit_user_or_reviewer_decision_required",
        "evidence": evidence,
        "assessment": assessment,
        "decision_options": [
            {
                "option": "strict_evidence_required",
                "effect": "Status remains blocked until Pionex support/export/snapshot evidence is available.",
                "tax_report_effect": "Draft only; do not mark final clean.",
            },
            {
                "option": "approve_non_tax_inventory_normalization",
                "effect": "A reviewed non-tax opening inventory adjustment can be imported later to make chronology non-negative.",
                "tax_report_effect": "Can mark the Pionex chronology as reviewer-approved, but documentation must disclose missing primary snapshot.",
            },
        ],
        "recommended_candidate_update": recommended_update,
        "api": {
            "list": "GET /api/v1/review/balance-adjustment-candidates",
            "upsert": "POST /api/v1/review/balance-adjustment-candidates/upsert",
            "candidate_rule": "Review candidates remain tax_effective=false; a separate reviewed adjustment/import is required after explicit approval.",
        },
    }


def run_local_ai_review(dossier: dict[str, Any]) -> dict[str, Any]:
    prompt = {
        "task": "Review the Pionex USDT opening decision. Do not invent evidence. Return concise JSON.",
        "facts": {
            "required_opening_usdt": dossier["evidence"]["required_opening_to_avoid_negative_usdt"],
            "visible_deposit_sum_until_worst_usdt": dossier["evidence"]["visible_deposit_sum_until_worst_usdt"],
            "readiness_status": dossier["evidence"]["readiness_status"],
            "negative_final_assets": dossier["evidence"]["global_negative_final_assets"],
            "first_negative": dossier["evidence"]["first_negative"],
            "worst_balance": dossier["evidence"]["worst_balance"],
        },
        "questions": [
            "Is it safe to auto-book this as tax-effective income?",
            "What is the correct next decision state?",
            "Which missing evidence would improve confidence?",
        ],
    }
    body = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "/no_think\nYou are a German crypto tax data reconciliation reviewer. Output only visible JSON, no reasoning."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0,
        "max_tokens": 700,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    try:
        request = urllib.request.Request(
            LLM_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"status": "error", "error": str(exc)}
    choice = (raw.get("choices") or [{}])[0]
    message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
    content = str(message.get("content") or "").strip()
    return {
        "status": "success" if content else "empty_content",
        "model": raw.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "usage": raw.get("usage") or {},
        "reasoning_content_present": bool(message.get("reasoning_content")),
        "content": content,
    }


def load_candidate(candidate_id: str) -> dict[str, Any]:
    row = STORE.get_setting("runtime.balance_adjustment_candidates")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    candidate = raw.get(candidate_id)
    return candidate if isinstance(candidate, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def render_doc(dossier: dict[str, Any]) -> str:
    evidence = dossier["evidence"]
    ai = dossier["local_ai_review"]
    update = dossier["recommended_candidate_update"]
    lines = [
        "# Pionex Opening Decision Dossier - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Kandidat: `{dossier['candidate_id']}`",
        f"- Entscheidungsstand: `{dossier['decision_state']}`",
        f"- Empfohlener Kandidatenstatus: `{update['status']}`",
        f"- Steuerwirksam: `{update['tax_effective']}`",
        f"- Benoetigtes Opening: `{evidence['required_opening_to_avoid_negative_usdt']} USDT`",
        f"- Sichtbare Deposits bis Worst: `{evidence['visible_deposit_sum_until_worst_usdt']} USDT`",
        f"- Nicht durch sichtbare Deposits gedeckt: `{evidence['uncovered_by_visible_deposits_until_worst_usdt']} USDT`",
        f"- Readiness: `{evidence['readiness_status']}`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {item}" for item in dossier["assessment"])
    lines += [
        "",
        "## Entscheidungsoptionen",
        "",
    ]
    for item in dossier["decision_options"]:
        lines.append(f"- `{item['option']}`: {item['effect']} {item['tax_report_effect']}")
    lines += [
        "",
        "## KI-Gegenpruefung",
        "",
        f"- Status: `{ai.get('status')}`",
        f"- Modell: `{ai.get('model')}`",
        f"- Usage: `{ai.get('usage')}`",
        f"- Reasoning-Content vorhanden: `{ai.get('reasoning_content_present')}`",
        "",
        "```json",
        ai.get("content") or "{}",
        "```",
        "",
        "## API-Payload",
        "",
        "```json",
        json.dumps(update, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Referenzen",
        "",
        f"- Pionex Gap: `{evidence['current_gap_report']}`",
        f"- Readiness: `{evidence['current_readiness_report']}`",
        f"- Transient: `{evidence['transient_report']}`",
        f"- Rekonstruktion: `{evidence['reconstruction_report']}`",
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
