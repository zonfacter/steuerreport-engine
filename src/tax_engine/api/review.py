from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tax_engine.admin import put_admin_setting
from tax_engine.admin.service import resolve_effective_runtime_config
from tax_engine.ai import (
    OllamaReviewConfig,
    OllamaReviewError,
    OpenAICompatibleReviewConfig,
    analyze_issue_with_ollama,
    classify_issue_with_ollama,
    classify_issue_with_openai_compatible,
)
from tax_engine.api.dashboard import (
    _asset_canonical_symbol,
    _cached_asset_usd_price_on_or_before,
    _dashboard_event_quantity,
    _estimate_event_values,
    _load_fx_lookup,
    _load_ignored_tokens,
    _load_token_aliases,
    _normalize_mint,
    _payload_asset_canonical_symbol,
    _runtime_usd_to_eur_rate,
)
from tax_engine.ingestion import write_audit
from tax_engine.ingestion.store import STORE
from tax_engine.integrations import (
    effective_integration_mode,
    integration_source_from_event,
    load_integration_mode_overrides,
    upsert_integration_mode,
)
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides, get_processing_job
from tax_engine.reconciliation import (
    AutoMatchRequest,
    ManualMatchRequest,
    auto_match_and_persist,
    get_transfer_chain,
    list_transfer_ledger,
    list_unmatched_transfers,
    manual_match,
)


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


class IssueStatusUpdateRequest(BaseModel):
    issue_id: str = Field(min_length=3, max_length=200)
    status: str = Field(min_length=2, max_length=30)
    note: str | None = Field(default=None, max_length=500)


class TaxEventOverrideUpsertRequest(BaseModel):
    source_event_id: str = Field(min_length=8, max_length=200)
    tax_category: str = Field(min_length=3, max_length=30)
    reason_code: str | None = Field(default=None, min_length=3, max_length=80)
    note: str | None = Field(default=None, max_length=500)


class TaxEventOverrideDeleteRequest(BaseModel):
    source_event_id: str = Field(min_length=8, max_length=200)


class ReviewIgnoreRequest(BaseModel):
    source_event_id: str = Field(min_length=8, max_length=200)
    reason_code: str = Field(min_length=3, max_length=80)
    note: str = Field(min_length=3, max_length=500)


class ReviewCommentRequest(BaseModel):
    source_event_id: str = Field(min_length=8, max_length=200)
    comment: str = Field(min_length=3, max_length=1000)
    reason_code: str | None = Field(default=None, min_length=3, max_length=80)


class IntegrationConflictResolveRequest(BaseModel):
    conflict_ids: list[str] = Field(min_length=1, max_length=200)
    action: str = Field(min_length=3, max_length=40)
    reason_code: str = Field(min_length=3, max_length=80)
    note: str = Field(min_length=3, max_length=500)


class ReviewTimezoneCorrectRequest(BaseModel):
    source_event_id: str = Field(min_length=8, max_length=200)
    corrected_timestamp_utc: str = Field(min_length=10, max_length=40)
    reason_code: str = Field(default="timezone_wrong", min_length=3, max_length=80)
    note: str = Field(min_length=3, max_length=500)


class ReviewMergeRequest(BaseModel):
    source_event_ids: list[str] = Field(min_length=2, max_length=100)
    reason_code: str = Field(default="same_economic_event", min_length=3, max_length=80)
    note: str = Field(min_length=3, max_length=500)


class ReviewSplitRequest(BaseModel):
    source_event_id: str = Field(min_length=8, max_length=200)
    split_rows: list[dict[str, Any]] = Field(min_length=1, max_length=50)
    reason_code: str = Field(default="bundled_event_split", min_length=3, max_length=80)
    note: str = Field(min_length=3, max_length=500)


class AiReviewAnalyzeRequest(BaseModel):
    issue_id: str = Field(min_length=8, max_length=240)
    persist: bool = Field(default=True)
    window_days: int = Field(default=14, ge=0, le=365)
    limit: int = Field(default=200, ge=1, le=500)
    engine: str = Field(default="runtime", min_length=3, max_length=80)


class AiReviewApplySuggestionRequest(BaseModel):
    suggestion_id: str = Field(min_length=8, max_length=240)
    actions: list[str] = Field(default_factory=list, max_length=20)
    note: str | None = Field(default=None, max_length=500)


class BalanceAdjustmentCandidateUpsertRequest(BaseModel):
    candidate_id: str = Field(min_length=8, max_length=200)
    platform: str = Field(min_length=2, max_length=80)
    asset: str = Field(min_length=1, max_length=40)
    quantity_delta: str = Field(min_length=1, max_length=80)
    effective_timestamp_utc: str = Field(min_length=10, max_length=40)
    adjustment_type: str = Field(min_length=3, max_length=80)
    status: str = Field(default="needs_evidence", min_length=3, max_length=40)
    reason_code: str = Field(min_length=3, max_length=80)
    note: str = Field(min_length=3, max_length=2000)
    evidence: dict[str, Any] = Field(default_factory=dict)
    tax_effective: bool = Field(default=False)


class BalanceAdjustmentCandidateDeleteRequest(BaseModel):
    candidate_id: str = Field(min_length=8, max_length=200)


class BalanceAdjustmentCandidateDecisionRequest(BaseModel):
    candidate_id: str = Field(min_length=8, max_length=200)
    decision: str = Field(min_length=3, max_length=80)
    reviewer: str = Field(min_length=2, max_length=120)
    note: str = Field(min_length=10, max_length=2000)
    evidence: dict[str, Any] = Field(default_factory=dict)


router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PIONEX_EVIDENCE_CANDIDATE_ID = "pionex-usdt-opening-balance-2021-12-28"
PIONEX_EVIDENCE_PACKAGE_FILES = {
    "evidence_report": PROJECT_ROOT / "docs" / "172_PIONEX_EVIDENCE_REQUEST_PACKAGE_2026-05-09.md",
    "final_blocker_audit": PROJECT_ROOT / "docs" / "167_PIONEX_USDT_FINAL_BLOCKER_AUDIT_2026-05-09.md",
    "package_json": PROJECT_ROOT / "var" / "pionex_evidence_request_package_2026-05-09.json",
    "known_transfer_csv": PROJECT_ROOT / "var" / "pionex_usdt_known_transfers_for_support_2026-05-09.csv",
    "support_request_en": PROJECT_ROOT / "var" / "pionex_support_request_usdt_history_en_2026-05-09.txt",
    "support_request_de": PROJECT_ROOT / "var" / "pionex_support_request_usdt_history_de_2026-05-09.txt",
}
PIONEX_EVIDENCE_PACKAGE_ZIP = PROJECT_ROOT / "var" / "pionex_support_package_2026-05-09.zip"


EXCLUSION_REASON_CATALOG: dict[str, str] = {
    "duplicate_import": "Duplikat aus Mehrfachimport oder Referenzreport",
    "wrong_assignment": "Falsche automatische Zuordnung/Klassifizierung",
    "spam_or_dust": "Spam-/Dust-Token ohne belastbaren wirtschaftlichen Vorgang",
    "reference_import_only": "Nur Referenzimport, Primärdaten sind bereits vorhanden",
    "not_tax_relevant": "Nach manueller Prüfung nicht steuerrelevant",
}

BALANCE_ADJUSTMENT_DECISIONS: dict[str, str] = {
    "approve_non_tax_inventory_normalization": "Dokumentierte nicht steuerwirksame Bestandsnormalisierung fachlich freigegeben",
    "reject_candidate": "Kandidat fachlich abgelehnt",
    "request_more_evidence": "Weitere Primaerbelege erforderlich",
}

BALANCE_ADJUSTMENT_REQUIRED_EVIDENCE: dict[str, list[str]] = {
    "missing_pionex_bot_start_capital": [
        "Pionex Account/Bot-Historie vor dem ersten negativen USDT-Bruch",
        "Pionex Deposit-/Withdraw-Export mit Startbestand oder Bot-Startkapital",
        "Alternativ externer Absenderbeleg fuer die fehlenden 197.8470311162 USDT",
    ],
}
ZERO_COST_TAX_LINE_PROCEEDS_THRESHOLD_EUR = Decimal("1000")

REVIEW_ACTION_REASON_CATALOG: dict[str, str] = {
    "timezone_wrong": "Zeitzone/Zeitstempel manuell korrigiert",
    "source_timezone_cet": "Quelle nutzt CET/CEST statt UTC",
    "source_period_start": "Quelle datiert aggregierten Zeitraum auf Periodenbeginn",
    "same_economic_event": "Mehrere Rohereignisse gehoeren zu einem wirtschaftlichen Vorgang",
    "bundled_event_split": "Ein Rohereignis muss fachlich in mehrere Teilvorgaenge zerlegt werden",
    "reference_match": "Referenzreport bestaetigt Primaerereignis",
}


def _list_effective_review_events() -> tuple[list[dict[str, Any]], dict[str, int]]:
    events, review_summary = apply_review_actions(STORE.list_raw_events())
    events, override_count = apply_tax_event_overrides(events)
    if override_count:
        review_summary = {**review_summary, "tax_event_override_count": override_count}
    return events, review_summary

DAC8_CARF_CONTEXT: dict[str, Any] = {
    "version": "2026-05-04",
    "framework": ["DAC8", "OECD-CARF", "KStTG"],
    "sources": [
        {
            "name": "EU Commission DAC8",
            "url": "https://taxation-customs.ec.europa.eu/taxation/tax-transparency-cooperation/administrative-co-operation-and-mutual-assistance/directive-administrative-cooperation-dac/dac8_en",
            "source_type": "primary",
        },
        {
            "name": "Council Directive (EU) 2023/2226",
            "url": "https://eur-lex.europa.eu/eli/dir/2023/2226/oj/eng",
            "source_type": "primary",
        },
        {
            "name": "OECD Crypto-Asset Reporting Framework",
            "url": "https://www.oecd.org/en/publications/international-standards-for-automatic-exchange-of-information-in-tax-matters_896d79d1-en/full-report/component-5.html",
            "source_type": "primary",
        },
        {
            "name": "BMF DAC8-Umsetzungsgesetz",
            "url": "https://www.bundesfinanzministerium.de/Content/DE/Gesetzestexte/Gesetze_Gesetzesvorhaben/Abteilungen/Abteilung_IV/21_Legislaturperiode/2025-11-05-DAC8-G/0-Gesetz.html",
            "source_type": "primary_de",
        },
        {
            "name": "Kryptowerte-Steuertransparenz-Gesetz (KStTG), BGBl. 2025 I Nr. 352",
            "url": "https://www.buzer.de/KStTG.htm",
            "source_type": "consolidated_law_text",
        },
    ],
    "timeline": {
        "eu_transposition_deadline": "2025-12-31",
        "de_law_promulgated": "2025-12-23",
        "de_ksttg_effective_from": "2025-12-24",
        "dac8_applies_from": "2026-01-01",
        "first_reporting_year": 2026,
        "pre_existing_user_due_diligence_deadline": "2027-01-01",
        "first_reporting_exchange_year": 2027,
        "first_exchange_deadline_eu": "2027-09-30",
    },
    "reporting_scope": {
        "reporting_entities": [
            "Reporting Crypto-Asset Service Provider",
            "Kryptowerte-Dienstleister",
            "Kryptowerte-Betreiber",
        ],
        "reportable_assets_include": [
            "crypto-assets under MiCA-linked definitions",
            "decentralised crypto-assets",
            "stablecoins",
            "e-money tokens",
            "certain NFTs depending on design/use",
        ],
        "reportable_transaction_categories": [
            "acquisitions against fiat currency",
            "disposals against fiat currency",
            "acquisitions against other reportable crypto-assets",
            "disposals against other reportable crypto-assets",
            "reportable retail payment transactions",
            "transfers to the user",
            "transfers by the user",
            "transfers to distributed-ledger addresses not known as VASP/financial-institution addresses",
        ],
    },
    "engine_policy": {
        "reporting_data_is_reference_only": True,
        "no_tax_result_without_ruleset": True,
        "does_not_replace_fifo": True,
        "does_not_replace_holding_period_check": True,
        "does_not_replace_cost_basis_or_fee_treatment": True,
        "raw_events_must_not_be_overwritten": True,
        "provider_scope_requires_source": True,
    },
    "llm_guardrails": {
        "must_distinguish_collection_and_reporting": True,
        "must_use_first_exchange_deadline_eu_if_specific_date_needed": "2027-09-30",
        "must_not_claim_exchange_deadline_2027_12_31": True,
        "must_not_treat_carf_as_identical_to_crs": True,
        "must_not_infer_taxable_gain_from_reporting_data_alone": True,
    },
}


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


@router.get("/api/v1/regulatory/dac8-carf/context", response_model=StandardResponse, tags=["regulatory"])
def regulatory_dac8_carf_context() -> StandardResponse:
    trace_id = str(uuid4())
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"regulatory_context": DAC8_CARF_CONTEXT},
        errors=[],
        warnings=[],
    )

@router.post("/api/v1/reconcile/auto-match", response_model=StandardResponse, tags=["reconcile"])
def reconcile_auto_match(payload: AutoMatchRequest) -> StandardResponse:
    trace_id = str(uuid4())
    result = auto_match_and_persist(
        time_window_seconds=payload.time_window_seconds,
        amount_tolerance_ratio=payload.amount_tolerance_ratio,
        min_confidence=payload.min_confidence,
    )
    write_audit(
        trace_id=trace_id,
        action="reconcile.auto_match",
        payload={
            "persisted_match_count": result["persisted_match_count"],
            "unmatched_outbound_count": len(result["unmatched_outbound_ids"]),
            "unmatched_inbound_count": len(result["unmatched_inbound_ids"]),
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@router.get("/api/v1/review/unmatched", response_model=StandardResponse, tags=["reconcile"])
def review_unmatched(
    time_window_seconds: int = 600,
    amount_tolerance_ratio: float = 0.02,
    min_confidence: float = 0.75,
) -> StandardResponse:
    trace_id = str(uuid4())
    result = list_unmatched_transfers(
        time_window_seconds=time_window_seconds,
        amount_tolerance_ratio=amount_tolerance_ratio,
        min_confidence=min_confidence,
    )
    write_audit(
        trace_id=trace_id,
        action="review.unmatched",
        payload={
            "unmatched_outbound_count": len(result["unmatched_outbound_ids"]),
            "unmatched_inbound_count": len(result["unmatched_inbound_ids"]),
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@router.get("/api/v1/review/gates", response_model=StandardResponse, tags=["reconcile"])
def review_gates(
    job_id: str | None = None,
    time_window_seconds: int = 600,
    amount_tolerance_ratio: float = 0.02,
    min_confidence: float = 0.75,
) -> StandardResponse:
    trace_id = str(uuid4())
    issues = _build_issue_inbox()
    unmatched = list_unmatched_transfers(
        time_window_seconds=time_window_seconds,
        amount_tolerance_ratio=amount_tolerance_ratio,
        min_confidence=min_confidence,
    )

    open_statuses = {"open", "in_review"}
    open_issues_total = [item for item in issues if str(item.get("status", "")).lower() in open_statuses]
    open_issues = [item for item in open_issues_total if item.get("is_current_scope", True)]
    historical_open_issues = [item for item in open_issues_total if not item.get("is_current_scope", True)]
    open_high_issues = [item for item in open_issues if str(item.get("severity", "")).lower() == "high"]
    unmatched_outbound = unmatched.get("unmatched_outbound_ids", [])
    unmatched_inbound = unmatched.get("unmatched_inbound_ids", [])
    balance_candidates = _load_balance_adjustment_candidates()
    blocking_candidate_statuses = {"needs_evidence", "ready_for_explicit_review_decision"}
    blocking_balance_candidates = [
        item
        for item in balance_candidates.values()
        if str(item.get("status") or "").lower() in blocking_candidate_statuses
    ]

    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    unmatched_total = len(unmatched_outbound) + len(unmatched_inbound)
    if unmatched_total > 0:
        blockers.append(
            {
                "code": "unmatched_transfers_open",
                "message": f"{unmatched_total} unmatched Transfers offen.",
            }
        )
    if open_high_issues:
        blockers.append(
            {
                "code": "high_severity_issues_open",
                "message": f"{len(open_high_issues)} High-Severity Issues sind nicht gelöst.",
            }
        )
    if blocking_balance_candidates:
        labels = ", ".join(
            f"{item.get('platform', 'unknown')}/{item.get('asset', 'unknown')}:{item.get('status', 'unknown')}"
            for item in blocking_balance_candidates[:5]
        )
        blockers.append(
            {
                "code": "balance_adjustment_candidates_need_decision",
                "message": (
                    f"{len(blocking_balance_candidates)} Review-only Balance-Kandidat(en) brauchen "
                    f"Beleg oder explizite Entscheidung: {labels}."
                ),
            }
        )

    job_info: dict[str, Any] = {}
    if job_id:
        job = get_processing_job(job_id)
        if job is None:
            blockers.append({"code": "job_not_found", "message": f"Process Job nicht gefunden: {job_id}"})
        else:
            job_status = str(job.get("status", "unknown"))
            job_info = {
                "job_id": str(job.get("job_id", "")),
                "status": job_status,
                "progress": int(job.get("progress", 0) or 0),
                "tax_line_count": int(job.get("tax_line_count", 0) or 0),
                "derivative_line_count": int(job.get("derivative_line_count", 0) or 0),
            }
            if job_status != "completed":
                blockers.append(
                    {"code": "process_job_not_completed", "message": f"Process Job Status ist '{job_status}'."}
                )
            elif job_info["tax_line_count"] == 0 and job_info["derivative_line_count"] == 0:
                warnings.append(
                    {
                        "code": "process_job_empty",
                        "message": "Process Job ist abgeschlossen, enthält aber keine Tax/Derivative Lines.",
                    }
                )
    else:
        warnings.append({"code": "job_id_missing", "message": "Kein job_id angegeben; Process-Gate wurde nicht geprüft."})

    allow_export = len(blockers) == 0
    data = {
        "allow_export": allow_export,
        "blocking_reasons": blockers,
        "warning_reasons": warnings,
        "counts": {
            "issues_total": len(issues),
            "issues_open": len(open_issues),
            "issues_open_total": len(open_issues_total),
            "issues_historical_open": len(historical_open_issues),
            "issues_high_open": len(open_high_issues),
            "unmatched_outbound": len(unmatched_outbound),
            "unmatched_inbound": len(unmatched_inbound),
            "unmatched_total": unmatched_total,
            "balance_adjustment_candidates_open": len(blocking_balance_candidates),
        },
        "balance_adjustment_candidates": [
            _balance_candidate_gate_row(item) for item in blocking_balance_candidates[:20]
        ],
        "draft_export_policy": {
            "final_export_allowed": allow_export,
            "draft_export_allowed": True,
            "draft_label_required": not allow_export,
            "message": (
                "Finaler Export ist gesperrt; Entwurfsdateien duerfen nur mit offenem Pionex-Hinweis verwendet werden."
                if not allow_export
                else "Finaler Export ist freigegeben."
            ),
        },
        "job": job_info,
    }
    write_audit(
        trace_id=trace_id,
        action="review.gates",
        payload={
            "allow_export": allow_export,
            "issues_open": len(open_issues),
            "issues_high_open": len(open_high_issues),
            "unmatched_total": unmatched_total,
            "job_id": job_id or "",
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=[])


def _balance_candidate_gate_row(item: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(item.get("candidate_id") or "")
    platform = str(item.get("platform") or "")
    asset = str(item.get("asset") or "")
    reason_code = str(item.get("reason_code") or "")
    required_evidence = BALANCE_ADJUSTMENT_REQUIRED_EVIDENCE.get(
        reason_code,
        [
            "Primaerbeleg fuer Herkunft und Zeitpunkt der Bestandsdifferenz",
            "Nachvollziehbare Nicht-Steuerwirksamkeitsentscheidung im Review",
        ],
    )
    return {
        "candidate_id": candidate_id,
        "platform": platform,
        "asset": asset,
        "quantity_delta": str(item.get("quantity_delta") or ""),
        "effective_timestamp_utc": str(item.get("effective_timestamp_utc") or ""),
        "adjustment_type": str(item.get("adjustment_type") or ""),
        "status": str(item.get("status") or ""),
        "reason_code": reason_code,
        "note": str(item.get("note") or ""),
        "tax_effective": False,
        "review_decision": item.get("review_decision", {}),
        "required_evidence": required_evidence,
        "api_actions": {
            "provide_more_evidence": {
                "method": "POST",
                "path": "/api/v1/review/balance-adjustment-candidates/upsert",
                "candidate_id": candidate_id,
            },
            "evidence_package": {
                "method": "GET",
                "path": f"/api/v1/review/balance-adjustment-candidates/{candidate_id}/evidence-package",
                "candidate_id": candidate_id,
            },
            "approve_non_tax_inventory_normalization": {
                "method": "POST",
                "path": "/api/v1/review/balance-adjustment-candidates/decide",
                "body": {
                    "candidate_id": candidate_id,
                    "decision": "approve_non_tax_inventory_normalization",
                    "tax_effective": False,
                },
            },
            "reject_candidate": {
                "method": "POST",
                "path": "/api/v1/review/balance-adjustment-candidates/decide",
                "body": {
                    "candidate_id": candidate_id,
                    "decision": "reject_candidate",
                    "tax_effective": False,
                },
            },
        },
    }


def _balance_candidate_decision_preview(item: dict[str, Any]) -> dict[str, Any]:
    row = _balance_candidate_gate_row(item)
    candidate_id = row["candidate_id"]
    approval_payload = {
        "candidate_id": candidate_id,
        "decision": "approve_non_tax_inventory_normalization",
        "reviewer": "manual-review",
        "note": (
            "Explicit non-tax inventory normalization for Pionex/USDT opening context. "
            "Known Binance/TRON/Pionex exports prove only the visible deposits; remaining gap is treated as "
            "unsupported platform-local opening/bot-history context, not as a taxable inflow."
        ),
        "evidence": {
            "evidence_package": "docs/172_PIONEX_EVIDENCE_REQUEST_PACKAGE_2026-05-09.md",
            "final_blocker_audit": "docs/167_PIONEX_USDT_FINAL_BLOCKER_AUDIT_2026-05-09.md",
            "decision_dossier": "docs/157_PIONEX_OPENING_DECISION_DOSSIER_2026-05-09.md",
            "known_transfer_csv": "var/pionex_usdt_known_transfers_for_support_2026-05-09.csv",
        },
    }
    return {
        "candidate": row,
        "current_status": str(item.get("status") or ""),
        "current_gate_effect": {
            "blocks_final_export": str(item.get("status") or "") in {"needs_evidence", "ready_for_explicit_review_decision"},
            "tax_effective": False,
            "creates_import": False,
        },
        "available_decisions": [
            {
                "decision": "request_more_evidence",
                "resulting_status": "needs_evidence",
                "blocks_final_export": True,
                "tax_effective": False,
                "when_to_use": "Use while Pionex support evidence or written unavailability confirmation is still pending.",
            },
            {
                "decision": "approve_non_tax_inventory_normalization",
                "resulting_status": "approved_non_tax_inventory_normalization",
                "blocks_final_export": False,
                "tax_effective": False,
                "when_to_use": "Use only after explicit reviewer/user decision that no taxable inflow should be invented.",
            },
            {
                "decision": "reject_candidate",
                "resulting_status": "rejected",
                "blocks_final_export": False,
                "tax_effective": False,
                "when_to_use": "Use only if the candidate is proven wrong and should not block readiness.",
            },
        ],
        "approval_payload_template": approval_payload,
        "safety_notes": [
            "Preview is read-only and does not change the candidate.",
            "Approval does not create a tax-effective import or alter raw data.",
            "Approval should be backed by Pionex evidence, written non-availability confirmation, or explicit manual review acceptance.",
        ],
    }


def _relative_project_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _read_support_transfer_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _ensure_pionex_evidence_zip() -> dict[str, Any]:
    PIONEX_EVIDENCE_PACKAGE_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(PIONEX_EVIDENCE_PACKAGE_ZIP, "w", compression=ZIP_DEFLATED) as archive:
        for path in PIONEX_EVIDENCE_PACKAGE_FILES.values():
            if not path.exists():
                continue
            archive.write(path, arcname=f"pionex_evidence_package/{_relative_project_path(path)}")
    exists = PIONEX_EVIDENCE_PACKAGE_ZIP.exists()
    return {
        "path": _relative_project_path(PIONEX_EVIDENCE_PACKAGE_ZIP),
        "exists": exists,
        "size_bytes": PIONEX_EVIDENCE_PACKAGE_ZIP.stat().st_size if exists else 0,
    }


def _pionex_evidence_package(candidate_id: str) -> dict[str, Any]:
    files = []
    for key, path in PIONEX_EVIDENCE_PACKAGE_FILES.items():
        exists = path.exists()
        files.append(
            {
                "key": key,
                "path": _relative_project_path(path),
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else 0,
            }
        )
    transfer_rows = _read_support_transfer_rows(PIONEX_EVIDENCE_PACKAGE_FILES["known_transfer_csv"])
    return {
        "candidate_id": candidate_id,
        "package_type": "pionex_usdt_opening_balance_support_request",
        "zip_file": _ensure_pionex_evidence_zip(),
        "files": files,
        "support_request_en": _read_text_file(PIONEX_EVIDENCE_PACKAGE_FILES["support_request_en"]),
        "support_request_de": _read_text_file(PIONEX_EVIDENCE_PACKAGE_FILES["support_request_de"]),
        "known_transfer_count": len(transfer_rows),
        "known_transfers": transfer_rows,
        "usage_note": (
            "Dieses Paket ist ein Support-/Belegpaket fuer Pionex. Es ist keine steuerwirksame "
            "Buchung und ersetzt keine Review-Entscheidung."
        ),
    }


@router.post("/api/v1/reconcile/manual", response_model=StandardResponse, tags=["reconcile"])
def reconcile_manual(payload: ManualMatchRequest) -> StandardResponse:
    trace_id = str(uuid4())
    result = manual_match(
        outbound_event_id=payload.outbound_event_id,
        inbound_event_id=payload.inbound_event_id,
        note=payload.note,
    )
    if not result["ok"]:
        write_audit(
            trace_id=trace_id,
            action="reconcile.manual",
            payload={"ok": False, "error": result["error"]},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": result["error"], "message": "Manual match failed"}],
            warnings=[],
        )

    write_audit(
        trace_id=trace_id,
        action="reconcile.manual",
        payload={"ok": True, "match_id": result["match_id"]},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@router.get("/api/v1/reconcile/ledger", response_model=StandardResponse, tags=["reconcile"])
def reconcile_ledger(limit: int = 200, offset: int = 0) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = min(max(limit, 1), 1000)
    safe_offset = max(offset, 0)
    result = list_transfer_ledger(limit=safe_limit, offset=safe_offset)
    write_audit(
        trace_id=trace_id,
        action="reconcile.ledger",
        payload={"limit": safe_limit, "offset": safe_offset, "row_count": len(result.get("rows", []))},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@router.get("/api/v1/audit/transfer-chain/{transfer_chain_id}", response_model=StandardResponse, tags=["audit"])
def audit_transfer_chain(transfer_chain_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    result = get_transfer_chain(transfer_chain_id)
    if result is None:
        write_audit(
            trace_id=trace_id,
            action="audit.transfer_chain",
            payload={"transfer_chain_id": transfer_chain_id, "found": False},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "transfer_chain_not_found", "message": f"Transfer Chain nicht gefunden: {transfer_chain_id}"}],
            warnings=[],
        )
    write_audit(
        trace_id=trace_id,
        action="audit.transfer_chain",
        payload={"transfer_chain_id": transfer_chain_id, "row_count": result.get("row_count", 0)},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@router.get("/api/v1/issues/inbox", response_model=StandardResponse, tags=["issues"])
def issues_inbox() -> StandardResponse:
    trace_id = str(uuid4())
    issues = _build_issue_inbox()
    write_audit(
        trace_id=trace_id,
        action="issues.inbox",
        payload={"count": len(issues)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(issues), "issues": issues},
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/issues/update-status", response_model=StandardResponse, tags=["issues"])
def issues_update_status(payload: IssueStatusUpdateRequest) -> StandardResponse:
    trace_id = str(uuid4())
    status = _normalize_issue_status(payload.status)
    if status is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_issue_status", "message": "status muss open|in_review|resolved|wont_fix sein"}],
            warnings=[],
        )
    overrides = _load_issue_overrides()
    issue_id = payload.issue_id.strip()
    overrides[issue_id] = {
        "status": status,
        "note": (payload.note or "").strip(),
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    put_admin_setting("runtime.issue_status_overrides", overrides, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="issues.update_status",
        payload={"issue_id": issue_id, "status": status},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"issue_id": issue_id, "status": status, "saved": True},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/tax/event-overrides", response_model=StandardResponse, tags=["tax"])
def tax_event_overrides_list() -> StandardResponse:
    trace_id = str(uuid4())
    overrides = _load_tax_event_overrides()
    rows = [
        {"source_event_id": event_id, **payload}
        for event_id, payload in sorted(overrides.items(), key=lambda item: item[0])
    ]
    write_audit(
        trace_id=trace_id,
        action="tax.event_overrides.list",
        payload={"count": len(rows)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "rows": rows},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/review/balance-adjustment-candidates", response_model=StandardResponse, tags=["review"])
def balance_adjustment_candidates_list() -> StandardResponse:
    trace_id = str(uuid4())
    candidates = _load_balance_adjustment_candidates()
    rows = sorted(
        candidates.values(),
        key=lambda row: (str(row.get("effective_timestamp_utc") or ""), str(row.get("candidate_id") or "")),
    )
    write_audit(
        trace_id=trace_id,
        action="review.balance_adjustment_candidates.list",
        payload={"count": len(rows)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "count": len(rows),
            "rows": rows,
            "api": {
                "list": "GET /api/v1/review/balance-adjustment-candidates",
                "upsert": "POST /api/v1/review/balance-adjustment-candidates/upsert",
                "decide": "POST /api/v1/review/balance-adjustment-candidates/decide",
                "delete": "POST /api/v1/review/balance-adjustment-candidates/delete",
                "tax_effective_rule": "Candidates are not tax-effective unless explicitly converted into a reviewed adjustment/import.",
            },
        },
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/review/balance-adjustment-candidates/{candidate_id}/decision-preview", response_model=StandardResponse, tags=["review"])
def balance_adjustment_candidate_decision_preview(candidate_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    candidate_key = str(candidate_id or "").strip()
    candidates = _load_balance_adjustment_candidates()
    entry = candidates.get(candidate_key)
    if entry is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"candidate_id": candidate_key},
            errors=[{"code": "candidate_not_found", "message": "Balance-Adjustment-Kandidat nicht gefunden."}],
            warnings=[],
        )
    preview = _balance_candidate_decision_preview(entry)
    write_audit(
        trace_id=trace_id,
        action="review.balance_adjustment_candidate.decision_preview",
        payload={"candidate_id": candidate_key, "current_status": entry.get("status", "")},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=preview, errors=[], warnings=[])


@router.get("/api/v1/review/balance-adjustment-candidates/{candidate_id}/evidence-package", response_model=StandardResponse, tags=["review"])
def balance_adjustment_candidate_evidence_package(candidate_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    candidate_key = str(candidate_id or "").strip()
    candidates = _load_balance_adjustment_candidates()
    entry = candidates.get(candidate_key)
    if entry is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"candidate_id": candidate_key},
            errors=[{"code": "candidate_not_found", "message": "Balance-Adjustment-Kandidat nicht gefunden."}],
            warnings=[],
        )
    if candidate_key != PIONEX_EVIDENCE_CANDIDATE_ID:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"candidate_id": candidate_key},
            errors=[
                {
                    "code": "evidence_package_not_available",
                    "message": "Fuer diesen Kandidaten ist noch kein Belegpaket hinterlegt.",
                }
            ],
            warnings=[],
        )
    package = _pionex_evidence_package(candidate_key)
    package["candidate"] = _balance_candidate_gate_row(entry)
    write_audit(
        trace_id=trace_id,
        action="review.balance_adjustment_candidate.evidence_package",
        payload={
            "candidate_id": candidate_key,
            "zip_path": package.get("zip_file", {}).get("path", ""),
            "known_transfer_count": package.get("known_transfer_count", 0),
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=package, errors=[], warnings=[])


@router.post("/api/v1/review/balance-adjustment-candidates/upsert", response_model=StandardResponse, tags=["review"])
def balance_adjustment_candidate_upsert(payload: BalanceAdjustmentCandidateUpsertRequest) -> StandardResponse:
    trace_id = str(uuid4())
    candidate_id = payload.candidate_id.strip()
    quantity_delta = _safe_decimal(payload.quantity_delta)
    if quantity_delta == Decimal("0"):
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "quantity_delta_required", "message": "quantity_delta darf nicht 0 sein."}],
            warnings=[],
        )
    if payload.tax_effective:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[
                {
                    "code": "candidate_cannot_be_tax_effective",
                    "message": "Review-Kandidaten duerfen nicht direkt steuerwirksam gespeichert werden.",
                }
            ],
            warnings=[],
        )
    candidates = _load_balance_adjustment_candidates()
    entry = {
        "candidate_id": candidate_id,
        "platform": payload.platform.strip().lower(),
        "asset": payload.asset.strip().upper(),
        "quantity_delta": quantity_delta.to_eng_string(),
        "effective_timestamp_utc": payload.effective_timestamp_utc.strip(),
        "adjustment_type": payload.adjustment_type.strip(),
        "status": payload.status.strip(),
        "reason_code": payload.reason_code.strip(),
        "note": payload.note.strip(),
        "evidence": payload.evidence,
        "tax_effective": False,
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    candidates[candidate_id] = entry
    _save_balance_adjustment_candidates(candidates)
    write_audit(
        trace_id=trace_id,
        action="review.balance_adjustment_candidate.upsert",
        payload={"candidate_id": candidate_id, "platform": entry["platform"], "asset": entry["asset"]},
    )
    return StandardResponse(trace_id=trace_id, status="success", data={"saved": True, **entry}, errors=[], warnings=[])


@router.post("/api/v1/review/balance-adjustment-candidates/decide", response_model=StandardResponse, tags=["review"])
def balance_adjustment_candidate_decide(payload: BalanceAdjustmentCandidateDecisionRequest) -> StandardResponse:
    trace_id = str(uuid4())
    candidate_id = payload.candidate_id.strip()
    decision = payload.decision.strip()
    if decision not in BALANCE_ADJUSTMENT_DECISIONS:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"allowed_decisions": sorted(BALANCE_ADJUSTMENT_DECISIONS)},
            errors=[
                {
                    "code": "unsupported_balance_adjustment_decision",
                    "message": "Diese Kandidaten-Entscheidung wird nicht unterstuetzt.",
                }
            ],
            warnings=[],
        )
    candidates = _load_balance_adjustment_candidates()
    entry = candidates.get(candidate_id)
    if entry is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"candidate_id": candidate_id},
            errors=[{"code": "candidate_not_found", "message": "Balance-Adjustment-Kandidat nicht gefunden."}],
            warnings=[],
        )
    now = datetime.now(UTC).isoformat()
    decision_entry = {
        "decision": decision,
        "label": BALANCE_ADJUSTMENT_DECISIONS[decision],
        "reviewer": payload.reviewer.strip(),
        "note": payload.note.strip(),
        "evidence": payload.evidence,
        "decided_at_utc": now,
    }
    history_raw = entry.get("decision_history")
    history: list[Any] = history_raw if isinstance(history_raw, list) else []
    history = [item for item in history if isinstance(item, dict)]
    history.append(decision_entry)
    status_by_decision = {
        "approve_non_tax_inventory_normalization": "approved_non_tax_inventory_normalization",
        "reject_candidate": "rejected",
        "request_more_evidence": "needs_evidence",
    }
    entry["status"] = status_by_decision[decision]
    entry["review_decision"] = decision_entry
    entry["decision_history"] = history[-20:]
    entry["tax_effective"] = False
    entry["updated_at_utc"] = now
    candidates[candidate_id] = entry
    _save_balance_adjustment_candidates(candidates)
    write_audit(
        trace_id=trace_id,
        action="review.balance_adjustment_candidate.decide",
        payload={"candidate_id": candidate_id, "decision": decision, "status": entry["status"]},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"saved": True, **entry},
        errors=[],
        warnings=[
            {
                "code": "not_tax_effective",
                "message": "Die Entscheidung speichert keine steuerwirksame Buchung und erzeugt keinen Import.",
            }
        ],
    )


@router.post("/api/v1/review/balance-adjustment-candidates/delete", response_model=StandardResponse, tags=["review"])
def balance_adjustment_candidate_delete(payload: BalanceAdjustmentCandidateDeleteRequest) -> StandardResponse:
    trace_id = str(uuid4())
    candidate_id = payload.candidate_id.strip()
    candidates = _load_balance_adjustment_candidates()
    deleted = candidate_id in candidates
    if deleted:
        del candidates[candidate_id]
        _save_balance_adjustment_candidates(candidates)
    write_audit(
        trace_id=trace_id,
        action="review.balance_adjustment_candidate.delete",
        payload={"candidate_id": candidate_id, "deleted": deleted},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"candidate_id": candidate_id, "deleted": deleted},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/review/exclusion-reasons", response_model=StandardResponse, tags=["review"])
def review_exclusion_reasons() -> StandardResponse:
    trace_id = str(uuid4())
    write_audit(
        trace_id=trace_id,
        action="review.exclusion_reasons",
        payload={"count": len(EXCLUSION_REASON_CATALOG)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "count": len(EXCLUSION_REASON_CATALOG),
            "reasons": [
                {"reason_code": reason_code, "label": label}
                for reason_code, label in sorted(EXCLUSION_REASON_CATALOG.items(), key=lambda item: item[0])
            ],
        },
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/review/negative-balances", response_model=StandardResponse, tags=["review"])
def review_negative_balances(
    as_of: str | None = None,
    year: int | None = None,
    asset: str | None = None,
    limit: int = 100,
    include_events: int = 5,
) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = min(max(int(limit), 1), 500)
    safe_include_events = min(max(int(include_events), 0), 25)
    asset_filter = str(asset or "").upper().strip()
    checkpoints = _negative_balance_checkpoints(as_of=as_of, year=year)
    if not checkpoints:
        safe_year = _valid_negative_balance_year(year)
        if as_of is None and safe_year is not None:
            return StandardResponse(
                trace_id=trace_id,
                status="success",
                data={
                    "mode": "year",
                    "as_of": "",
                    "year": safe_year,
                    "asset": asset_filter,
                    "checkpoint_count": 0,
                    "count": 0,
                    "limit": safe_limit,
                    "include_events": safe_include_events,
                    "rows": [],
                    "api": _negative_balance_api_contract(),
                },
                errors=[],
                warnings=[],
            )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_negative_balance_scope", "message": "as_of muss YYYY-MM-DD sein oder year muss gesetzt sein."}],
            warnings=[],
        )

    events, review_summary = _list_effective_review_events()
    ignored_mints = set(_load_ignored_tokens().keys())
    fx_lookup = _load_fx_lookup()
    fx_rate_cache: dict[str, Decimal] = {}
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] = {}
    overrides = _load_issue_overrides()

    rows: list[dict[str, Any]] = []
    for checkpoint in checkpoints:
        rows.extend(
            _build_negative_balance_rows_for_date(
                events=events,
                as_of=checkpoint,
                ignored_mints=ignored_mints,
                fx_lookup=fx_lookup,
                fx_rate_cache=fx_rate_cache,
                asset_usd_price_cache=asset_usd_price_cache,
                overrides=overrides,
                asset_filter=asset_filter,
                include_events=safe_include_events,
            )
        )
    rows.sort(key=lambda item: (_safe_decimal(item.get("value_usd")).copy_abs(), str(item.get("date")), str(item.get("asset"))), reverse=True)
    rows = rows[:safe_limit]
    write_audit(
        trace_id=trace_id,
        action="review.negative_balances",
        payload={
            "as_of": as_of or "",
            "year": year,
            "asset": asset_filter,
            "checkpoint_count": len(checkpoints),
            "count": len(rows),
            "review_summary": review_summary,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "mode": "as_of" if as_of else "year",
            "as_of": checkpoints[0] if as_of else "",
            "year": year,
            "asset": asset_filter,
            "checkpoint_count": len(checkpoints),
            "count": len(rows),
            "limit": safe_limit,
            "include_events": safe_include_events,
            "rows": rows,
            "api": _negative_balance_api_contract(),
        },
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/review/issue-context/{issue_id}", response_model=StandardResponse, tags=["review"])
def review_issue_context(issue_id: str, window_days: int = 14, limit: int = 200) -> StandardResponse:
    trace_id = str(uuid4())
    safe_window_days = min(max(int(window_days), 0), 365)
    safe_limit = min(max(int(limit), 1), 500)
    zero_cost_parsed = _parse_zero_cost_tax_lot_issue_id(issue_id)
    if zero_cost_parsed is not None:
        year, asset, job_id = zero_cost_parsed
        context = _build_zero_cost_tax_lot_issue_context(
            issue_id=issue_id,
            year=year,
            asset=asset,
            job_id=job_id,
            limit=safe_limit,
        )
        if context is None:
            return StandardResponse(
                trace_id=trace_id,
                status="error",
                data={},
                errors=[{"code": "issue_not_found", "message": f"Zero-Cost-Issue nicht gefunden: {issue_id}"}],
                warnings=[],
            )
        write_audit(
            trace_id=trace_id,
            action="review.issue_context.zero_cost_tax_lots",
            payload={"issue_id": issue_id, "year": year, "asset": asset, "job_id": job_id},
        )
        return StandardResponse(trace_id=trace_id, status="success", data=context, errors=[], warnings=[])

    parsed = _parse_negative_balance_issue_id(issue_id)
    if parsed is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[
                {
                    "code": "unsupported_issue_context",
                    "message": (
                        "Aktuell wird Issue-Kontext fuer negative_balance:<YYYY-MM-DD>:<ASSET> "
                        "und zero_cost_tax_lots:<YEAR>:<ASSET>:<JOB_ID> unterstuetzt."
                    ),
                }
            ],
            warnings=[],
        )
    as_of, asset = parsed
    events, review_summary = apply_review_actions(STORE.list_raw_events())
    ignored_mints = set(_load_ignored_tokens().keys())
    fx_lookup = _load_fx_lookup()
    fx_rate_cache: dict[str, Decimal] = {}
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] = {}
    issue_rows = _build_negative_balance_rows_for_date(
        events=events,
        as_of=as_of,
        ignored_mints=ignored_mints,
        fx_lookup=fx_lookup,
        fx_rate_cache=fx_rate_cache,
        asset_usd_price_cache=asset_usd_price_cache,
        overrides=_load_issue_overrides(),
        asset_filter=asset,
        include_events=10,
    )
    issue = next((row for row in issue_rows if str(row.get("issue_id")) == issue_id), None)
    if issue is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "issue_not_found", "message": f"Issue nicht gefunden oder nicht mehr negativ: {issue_id}"}],
            warnings=[],
        )

    context = _build_negative_balance_issue_context(
        events=events,
        issue=issue,
        as_of=as_of,
        asset=asset,
        window_days=safe_window_days,
        limit=safe_limit,
    )
    write_audit(
        trace_id=trace_id,
        action="review.issue_context",
        payload={
            "issue_id": issue_id,
            "issue_type": "negative_balance",
            "asset": asset,
            "as_of": as_of,
            "window_days": safe_window_days,
            "review_summary": review_summary,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "issue_id": issue_id,
            "issue_type": "negative_balance",
            "issue": issue,
            "context": context,
            "api": {
                "negative_balances": "GET /api/v1/review/negative-balances",
                "transaction_search": "GET /api/v1/dashboard/transaction-search",
                "set_status": "POST /api/v1/issues/update-status",
                "comment_event": "POST /api/v1/review/comment",
                "ignore_event": "POST /api/v1/review/ignore",
                "merge_events": "POST /api/v1/review/merge",
                "split_event": "POST /api/v1/review/split",
                "tax_event_override": "POST /api/v1/tax/event-override/upsert",
            },
        },
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/ai/review/analyze", response_model=StandardResponse, tags=["ai"])
def ai_review_analyze(payload: AiReviewAnalyzeRequest) -> StandardResponse:
    trace_id = str(uuid4())
    context_response = review_issue_context(
        issue_id=payload.issue_id.strip(),
        window_days=payload.window_days,
        limit=payload.limit,
    )
    if context_response.status != "success":
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=context_response.errors,
            warnings=context_response.warnings,
        )
    selected_engine = _resolve_ai_review_engine(payload.engine)
    suggestion, engine_warnings = _build_ai_review_suggestion_for_engine(
        context_payload=context_response.data,
        engine=selected_engine,
    )
    saved = False
    if payload.persist:
        suggestions = _load_ai_review_suggestions()
        suggestions[suggestion["suggestion_id"]] = suggestion
        put_admin_setting("runtime.ai_review_suggestions", suggestions, is_secret=False)
        saved = True
    write_audit(
        trace_id=trace_id,
        action="ai.review.analyze",
        payload={
            "issue_id": payload.issue_id,
            "suggestion_id": suggestion["suggestion_id"],
            "engine": selected_engine,
            "persist": payload.persist,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"suggestion": suggestion, "saved": saved},
        errors=[],
        warnings=engine_warnings,
    )


def _resolve_ai_review_engine(engine: str) -> str:
    requested = str(engine or "runtime").strip().lower()
    if requested in {"runtime", "default", "configured"}:
        runtime = resolve_effective_runtime_config().get("runtime", {})
        ai_config = runtime.get("ai_review", {}) if isinstance(runtime, dict) else {}
        if isinstance(ai_config, dict):
            provider = str(ai_config.get("provider") or "").strip().lower()
            if provider:
                return provider
        return "deterministic-v1"
    return requested


@router.get("/api/v1/ai/review/suggestions", response_model=StandardResponse, tags=["ai"])
def ai_review_suggestions(issue_id: str | None = None, status: str | None = None, limit: int = 200) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = min(max(int(limit), 1), 500)
    issue_filter = str(issue_id or "").strip()
    status_filter = str(status or "").strip().lower()
    rows = list(_load_ai_review_suggestions().values())
    if issue_filter:
        rows = [row for row in rows if str(row.get("issue_id") or "") == issue_filter]
    if status_filter:
        rows = [row for row in rows if str(row.get("status") or "").lower() == status_filter]
    rows.sort(key=lambda row: str(row.get("created_at_utc") or ""), reverse=True)
    rows = rows[:safe_limit]
    write_audit(
        trace_id=trace_id,
        action="ai.review.suggestions",
        payload={"issue_id": issue_filter, "status": status_filter, "count": len(rows)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "limit": safe_limit, "rows": rows},
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/ai/review/apply-suggestion", response_model=StandardResponse, tags=["ai"])
def ai_review_apply_suggestion(payload: AiReviewApplySuggestionRequest) -> StandardResponse:
    trace_id = str(uuid4())
    suggestions = _load_ai_review_suggestions()
    suggestion_id = payload.suggestion_id.strip()
    suggestion = suggestions.get(suggestion_id)
    if suggestion is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "suggestion_not_found", "message": f"Suggestion nicht gefunden: {suggestion_id}"}],
            warnings=[],
        )
    requested = {str(action).strip() for action in payload.actions if str(action).strip()}
    if not requested:
        requested = {"set_status", "comment_last_event"}
    allowed = {"set_status", "comment_last_event"}
    unsupported = sorted(requested - allowed)
    if unsupported:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"allowed_actions": sorted(allowed), "unsupported_actions": unsupported},
            errors=[
                {
                    "code": "unsafe_ai_action_requires_manual_review",
                    "message": "Nur Status und Kommentar duerfen direkt aus KI-Suggestions angewendet werden.",
                }
            ],
            warnings=[],
        )

    applied: list[dict[str, Any]] = []
    if "set_status" in requested:
        issue_id = str(suggestion.get("issue_id") or "")
        note = str(payload.note or suggestion.get("summary") or "KI-Review-Vorschlag in Bearbeitung.").strip()
        status_response = issues_update_status(IssueStatusUpdateRequest(issue_id=issue_id, status="in_review", note=note[:500]))
        applied.append({"action": "set_status", "status": status_response.status, "errors": status_response.errors})
    if "comment_last_event" in requested:
        event_id = str((suggestion.get("primary_evidence_event_ids") or [""])[0])
        if event_id:
            comment = _ai_suggestion_comment_text(suggestion=suggestion, note=payload.note)
            comment_response = review_comment(
                ReviewCommentRequest(
                    source_event_id=event_id,
                    reason_code="negative_balance_review",
                    comment=comment[:1000],
                )
            )
            applied.append({"action": "comment_last_event", "status": comment_response.status, "errors": comment_response.errors})

    suggestion["status"] = "applied"
    suggestion["applied_at_utc"] = datetime.now(UTC).isoformat()
    suggestion["applied_actions"] = sorted(requested)
    suggestions[suggestion_id] = suggestion
    put_admin_setting("runtime.ai_review_suggestions", suggestions, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="ai.review.apply_suggestion",
        payload={"suggestion_id": suggestion_id, "actions": sorted(requested)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"suggestion_id": suggestion_id, "applied": applied, "suggestion": suggestion},
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/tax/event-override/upsert", response_model=StandardResponse, tags=["tax"])
def tax_event_override_upsert(payload: TaxEventOverrideUpsertRequest) -> StandardResponse:
    trace_id = str(uuid4())
    category = _normalize_tax_event_category(payload.tax_category)
    if category is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[
                {
                    "code": "invalid_tax_category",
                    "message": "tax_category muss PRIVATE_SO, BUSINESS oder EXCLUDED sein",
                }
            ],
            warnings=[],
        )

    event_id = payload.source_event_id.strip()
    raw_event = STORE.get_raw_event(event_id)
    if raw_event is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "source_event_not_found", "message": f"Event nicht gefunden: {event_id}"}],
            warnings=[],
        )

    overrides = _load_tax_event_overrides()
    reason_code = str(payload.reason_code or "").strip()
    note = (payload.note or "").strip()
    if category == "EXCLUDED":
        if reason_code not in EXCLUSION_REASON_CATALOG:
            return StandardResponse(
                trace_id=trace_id,
                status="error",
                data={"allowed_reason_codes": EXCLUSION_REASON_CATALOG},
                errors=[
                    {
                        "code": "invalid_exclusion_reason",
                        "message": "Ausschluss benötigt einen gültigen vorausgewählten reason_code.",
                    }
                ],
                warnings=[],
            )
        if not note:
            return StandardResponse(
                trace_id=trace_id,
                status="error",
                data={},
                errors=[
                    {
                        "code": "exclusion_note_required",
                        "message": "Ausschluss benötigt eine manuelle Begründung/Notiz.",
                    }
                ],
                warnings=[],
            )
    elif reason_code and reason_code not in EXCLUSION_REASON_CATALOG:
        reason_code = ""

    entry = {
        "tax_category": category,
        "reason_code": reason_code,
        "reason_label": EXCLUSION_REASON_CATALOG.get(reason_code, ""),
        "note": note,
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    overrides[event_id] = entry
    put_admin_setting("runtime.tax_event_overrides", overrides, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="tax.event_override.upsert",
        payload={"source_event_id": event_id, "tax_category": category},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"source_event_id": event_id, **entry, "saved": True},
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/review/ignore", response_model=StandardResponse, tags=["review"])
def review_ignore(payload: ReviewIgnoreRequest) -> StandardResponse:
    # Deutsche Kommentare: fachlicher Alias fuer den Roadmap-Review-Flow; Raw Events bleiben unveraendert.
    return tax_event_override_upsert(
        TaxEventOverrideUpsertRequest(
            source_event_id=payload.source_event_id,
            tax_category="EXCLUDED",
            reason_code=payload.reason_code,
            note=payload.note,
        )
    )


@router.post("/api/v1/tax/event-override/delete", response_model=StandardResponse, tags=["tax"])
def tax_event_override_delete(payload: TaxEventOverrideDeleteRequest) -> StandardResponse:
    trace_id = str(uuid4())
    event_id = payload.source_event_id.strip()
    overrides = _load_tax_event_overrides()
    deleted = event_id in overrides
    if deleted:
        del overrides[event_id]
        put_admin_setting("runtime.tax_event_overrides", overrides, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="tax.event_override.delete",
        payload={"source_event_id": event_id, "deleted": deleted},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"source_event_id": event_id, "deleted": deleted},
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/review/comment", response_model=StandardResponse, tags=["review"])
def review_comment(payload: ReviewCommentRequest) -> StandardResponse:
    trace_id = str(uuid4())
    event_id = payload.source_event_id.strip()
    raw_event = STORE.get_raw_event(event_id)
    if raw_event is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "source_event_not_found", "message": f"Event nicht gefunden: {event_id}"}],
            warnings=[],
        )
    comments = _load_event_comments()
    entry = {
        "source_event_id": event_id,
        "comment": payload.comment.strip(),
        "reason_code": str(payload.reason_code or "").strip(),
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    comments[event_id] = entry
    put_admin_setting("runtime.event_comments", comments, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="review.comment",
        payload={"source_event_id": event_id, "reason_code": entry["reason_code"]},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={**entry, "saved": True},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/review/comments", response_model=StandardResponse, tags=["review"])
def review_comments(source_event_id: str | None = None) -> StandardResponse:
    trace_id = str(uuid4())
    comments = _load_event_comments()
    event_id = str(source_event_id or "").strip()
    rows = [
        item
        for item in comments.values()
        if not event_id or str(item.get("source_event_id", "")).strip() == event_id
    ]
    rows.sort(key=lambda item: (str(item.get("updated_at_utc", "")), str(item.get("source_event_id", ""))))
    write_audit(
        trace_id=trace_id,
        action="review.comments",
        payload={"count": len(rows), "source_event_id": event_id},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "rows": rows},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/review/actions", response_model=StandardResponse, tags=["review"])
def review_actions(source_event_id: str | None = None) -> StandardResponse:
    trace_id = str(uuid4())
    event_id = str(source_event_id or "").strip()
    actions = _load_review_actions()
    timezone_rows = [
        {"action_type": "timezone_correct", **payload}
        for payload in actions.get("timezone_corrections", {}).values()
        if not event_id or str(payload.get("source_event_id", "")) == event_id
    ]
    merge_rows = [
        {"action_type": "merge", **payload}
        for payload in actions.get("merges", {}).values()
        if not event_id or event_id in {str(item) for item in payload.get("source_event_ids", [])}
    ]
    split_rows = [
        {"action_type": "split", **payload}
        for payload in actions.get("splits", {}).values()
        if not event_id or str(payload.get("source_event_id", "")) == event_id
    ]
    rows = [*timezone_rows, *merge_rows, *split_rows]
    rows.sort(key=lambda item: (str(item.get("updated_at_utc", "")), str(item.get("action_id", ""))))
    write_audit(
        trace_id=trace_id,
        action="review.actions",
        payload={"count": len(rows), "source_event_id": event_id},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "rows": rows, "reason_catalog": REVIEW_ACTION_REASON_CATALOG},
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/review/timezone-correct", response_model=StandardResponse, tags=["review"])
def review_timezone_correct(payload: ReviewTimezoneCorrectRequest) -> StandardResponse:
    trace_id = str(uuid4())
    event_id = payload.source_event_id.strip()
    raw_event = STORE.get_raw_event(event_id)
    if raw_event is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "source_event_not_found", "message": f"Event nicht gefunden: {event_id}"}],
            warnings=[],
        )
    corrected = _normalize_review_timestamp(payload.corrected_timestamp_utc)
    if corrected is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_corrected_timestamp", "message": "corrected_timestamp_utc muss ISO-8601 sein."}],
            warnings=[],
        )
    actions = _load_review_actions()
    entry = {
        "action_id": f"timezone:{event_id}",
        "source_event_id": event_id,
        "corrected_timestamp_utc": corrected,
        "reason_code": _normalize_review_reason(payload.reason_code, "timezone_wrong"),
        "reason_label": REVIEW_ACTION_REASON_CATALOG.get(_normalize_review_reason(payload.reason_code, "timezone_wrong"), ""),
        "note": payload.note.strip(),
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    actions["timezone_corrections"][event_id] = entry
    _save_review_actions(actions)
    write_audit(
        trace_id=trace_id,
        action="review.timezone_correct",
        payload={"source_event_id": event_id, "corrected_timestamp_utc": corrected},
    )
    return StandardResponse(trace_id=trace_id, status="success", data={**entry, "saved": True}, errors=[], warnings=[])


@router.post("/api/v1/review/merge", response_model=StandardResponse, tags=["review"])
def review_merge(payload: ReviewMergeRequest) -> StandardResponse:
    trace_id = str(uuid4())
    event_ids = sorted({str(item).strip() for item in payload.source_event_ids if str(item).strip()})
    if len(event_ids) < 2:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "merge_requires_two_events", "message": "Merge benoetigt mindestens zwei Event IDs."}],
            warnings=[],
        )
    missing = [event_id for event_id in event_ids if STORE.get_raw_event(event_id) is None]
    if missing:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"missing_event_ids": missing},
            errors=[{"code": "source_event_not_found", "message": "Mindestens ein Merge-Event wurde nicht gefunden."}],
            warnings=[],
        )
    actions = _load_review_actions()
    action_id = "merge:" + _stable_action_suffix(event_ids)
    entry = {
        "action_id": action_id,
        "source_event_ids": event_ids,
        "reason_code": _normalize_review_reason(payload.reason_code, "same_economic_event"),
        "reason_label": REVIEW_ACTION_REASON_CATALOG.get(_normalize_review_reason(payload.reason_code, "same_economic_event"), ""),
        "note": payload.note.strip(),
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    actions["merges"][action_id] = entry
    _save_review_actions(actions)
    write_audit(trace_id=trace_id, action="review.merge", payload={"action_id": action_id, "event_count": len(event_ids)})
    return StandardResponse(trace_id=trace_id, status="success", data={**entry, "saved": True}, errors=[], warnings=[])


@router.post("/api/v1/review/split", response_model=StandardResponse, tags=["review"])
def review_split(payload: ReviewSplitRequest) -> StandardResponse:
    trace_id = str(uuid4())
    event_id = payload.source_event_id.strip()
    if STORE.get_raw_event(event_id) is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "source_event_not_found", "message": f"Event nicht gefunden: {event_id}"}],
            warnings=[],
        )
    actions = _load_review_actions()
    entry = {
        "action_id": f"split:{event_id}",
        "source_event_id": event_id,
        "split_rows": payload.split_rows,
        "reason_code": _normalize_review_reason(payload.reason_code, "bundled_event_split"),
        "reason_label": REVIEW_ACTION_REASON_CATALOG.get(_normalize_review_reason(payload.reason_code, "bundled_event_split"), ""),
        "note": payload.note.strip(),
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    actions["splits"][event_id] = entry
    _save_review_actions(actions)
    write_audit(
        trace_id=trace_id,
        action="review.split",
        payload={"source_event_id": event_id, "split_row_count": len(payload.split_rows)},
    )
    return StandardResponse(trace_id=trace_id, status="success", data={**entry, "saved": True}, errors=[], warnings=[])


@router.get("/api/v1/review/integration-conflicts", response_model=StandardResponse, tags=["review"])
def review_integration_conflicts(limit: int = 200) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = min(max(int(limit), 1), 1000)
    conflicts = _build_integration_conflicts(limit=safe_limit)
    write_audit(
        trace_id=trace_id,
        action="review.integration_conflicts",
        payload={"count": len(conflicts), "limit": safe_limit},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(conflicts), "limit": safe_limit, "conflicts": conflicts},
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/review/integration-conflicts/resolve", response_model=StandardResponse, tags=["review"])
def review_integration_conflicts_resolve(payload: IntegrationConflictResolveRequest) -> StandardResponse:
    trace_id = str(uuid4())
    action = str(payload.action or "").strip().lower()
    allowed_actions = {"exclude_reference_events", "disable_reference_sources", "confirm_reference_only"}
    if action not in allowed_actions:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"allowed_actions": sorted(allowed_actions)},
            errors=[
                {
                    "code": "invalid_conflict_action",
                    "message": "Aktion muss exclude_reference_events|disable_reference_sources|confirm_reference_only sein.",
                }
            ],
            warnings=[],
        )
    if payload.reason_code not in EXCLUSION_REASON_CATALOG:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"allowed_reason_codes": EXCLUSION_REASON_CATALOG},
            errors=[
                {
                    "code": "invalid_exclusion_reason",
                    "message": "Massenentscheidung benötigt einen gültigen vorausgewählten reason_code.",
                }
            ],
            warnings=[],
        )
    conflict_ids = {str(item or "").strip() for item in payload.conflict_ids if str(item or "").strip()}
    if not conflict_ids:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "conflict_ids_required", "message": "Mindestens eine conflict_id ist erforderlich."}],
            warnings=[],
        )

    conflict_map = {str(item["conflict_id"]): item for item in _build_integration_conflicts(limit=1000)}
    selected = [conflict_map[item] for item in sorted(conflict_ids) if item in conflict_map]
    missing_ids = sorted(conflict_ids.difference(conflict_map.keys()))
    overrides = _load_tax_event_overrides()
    excluded_event_ids: list[str] = []
    disabled_sources: list[str] = []
    resolved_issue_ids: list[str] = []
    now = datetime.now(UTC).isoformat()

    for conflict in selected:
        resolved_issue_ids.append(f"integration_conflict:{conflict['conflict_id']}")
        if action == "exclude_reference_events":
            for event_id in conflict.get("reference_event_ids", []):
                event_id_str = str(event_id or "").strip()
                if not event_id_str:
                    continue
                overrides[event_id_str] = {
                    "tax_category": "EXCLUDED",
                    "reason_code": payload.reason_code,
                    "reason_label": EXCLUSION_REASON_CATALOG.get(payload.reason_code, ""),
                    "note": payload.note.strip(),
                    "updated_at_utc": now,
                }
                excluded_event_ids.append(event_id_str)
        elif action == "disable_reference_sources":
            for source in conflict.get("reference_sources", []):
                entry = upsert_integration_mode(
                    str(source),
                    "disabled",
                    f"Integration-Konfliktentscheidung: {payload.note.strip()}",
                )
                disabled_sources.append(entry["integration_id"])
        elif action == "confirm_reference_only":
            for source in conflict.get("reference_sources", []):
                entry = upsert_integration_mode(
                    str(source),
                    "reference",
                    f"Referenzimport bestätigt: {payload.note.strip()}",
                )
                disabled_sources.append(entry["integration_id"])

    if excluded_event_ids:
        put_admin_setting("runtime.tax_event_overrides", overrides, is_secret=False)
    if resolved_issue_ids:
        issue_overrides = _load_issue_overrides()
        for issue_id in resolved_issue_ids:
            issue_overrides[issue_id] = {"status": "resolved", "note": payload.note.strip(), "updated_at_utc": now}
        put_admin_setting("runtime.issue_status_overrides", issue_overrides, is_secret=False)

    result = {
        "action": action,
        "requested_count": len(conflict_ids),
        "resolved_count": len(selected),
        "missing_conflict_ids": missing_ids,
        "excluded_event_count": len(set(excluded_event_ids)),
        "excluded_event_ids": sorted(set(excluded_event_ids))[:200],
        "disabled_or_confirmed_sources": sorted(set(disabled_sources)),
        "resolved_issue_ids": resolved_issue_ids,
    }
    write_audit(
        trace_id=trace_id,
        action="review.integration_conflicts.resolve",
        payload=result,
    )
    return StandardResponse(
        trace_id=trace_id,
        status="partial" if missing_ids else "success",
        data=result,
        errors=[],
        warnings=(
            [{"code": "conflict_ids_not_found", "message": f"{len(missing_ids)} Konflikt-IDs wurden nicht gefunden."}]
            if missing_ids
            else []
        ),
    )




def _build_issue_inbox() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    overrides = _load_issue_overrides()
    closed_tax_years = _load_closed_tax_years()
    review_actions_payload = _load_review_actions()
    timezone_corrections = review_actions_payload.get("timezone_corrections", {})
    raw_events = STORE.list_raw_events()
    runtime_fx = _runtime_usd_to_eur_rate()
    fx_lookup = _load_fx_lookup()
    fx_rate_cache: dict[str, Decimal] = {}
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] = {}
    mode_overrides = load_integration_mode_overrides()

    # 1) Missing price issues for trade-like events.
    for event in raw_events:
        event_id = str(event.get("unique_event_id", ""))
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if not _is_trade_like(payload):
            continue
        integration_mode = effective_integration_mode(integration_source_from_event(event), mode_overrides)
        if integration_mode != "active":
            continue
        asset = str(payload.get("asset") or "").upper().strip()
        value = _estimate_event_values(
            payload=payload,
            asset=asset,
            quantity=_dashboard_event_quantity(payload),
            runtime_fx=runtime_fx,
            fx_rate_cache=fx_rate_cache,
            asset_usd_price_cache=asset_usd_price_cache,
            fx_lookup=fx_lookup,
        )
        if value["priced"]:
            continue
        source_name = str(payload.get("source", "")).strip().lower()
        severity = "medium" if source_name == "blockpit" else "high"
        issue_id = f"missing_price:{event_id}"
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="missing_price",
                severity=severity,
                title="Fehlender Preis für Trade-Event",
                detail=f"Event {event_id} hat Menge ohne Preis (EUR).",
                source_event_id=event_id,
                payload=payload,
                overrides=overrides,
            )
        )

    # 2) Timestamp timezone ambiguity issues.
    for event in raw_events:
        event_id = str(event.get("unique_event_id", ""))
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts_raw = payload.get("timestamp")
        if ts_raw is None:
            continue
        ts_text = str(ts_raw)
        if "Z" in ts_text or "+" in ts_text or ts_text.endswith("UTC"):
            continue
        if event_id in timezone_corrections:
            continue
        issue_id = f"timezone_ambiguous:{event_id}"
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="timezone_conflict",
                severity="medium",
                title="Zeitzone nicht eindeutig",
                detail=f"Event {event_id} enthält timestamp ohne TZ-Offset: {ts_text}",
                source_event_id=event_id,
                payload=payload,
                overrides=overrides,
            )
        )

    # 3) Unmatched transfers.
    unmatched = list_unmatched_transfers(time_window_seconds=600, amount_tolerance_ratio=0.02, min_confidence=0.75)
    for event_id in unmatched.get("unmatched_outbound_ids", []):
        payload = STORE.get_raw_event(str(event_id))
        issue_id = f"unmatched_transfer_out:{event_id}"
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="unmatched_transfer",
                severity="high",
                title="Unmatched Outbound Transfer",
                detail=f"Outbound Transfer {event_id} hat keine Gegenbuchung.",
                source_event_id=str(event_id),
                payload=(payload or {}).get("payload", {}) if isinstance(payload, dict) else {},
                overrides=overrides,
            )
        )
    for event_id in unmatched.get("unmatched_inbound_ids", []):
        payload = STORE.get_raw_event(str(event_id))
        issue_id = f"unmatched_transfer_in:{event_id}"
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="unmatched_transfer",
                severity="high",
                title="Unmatched Inbound Transfer",
                detail=f"Inbound Transfer {event_id} hat keine Outbound-Zuordnung.",
                source_event_id=str(event_id),
                payload=(payload or {}).get("payload", {}) if isinstance(payload, dict) else {},
                overrides=overrides,
            )
        )

    # 4) Fehlende FX-Kurse für USD->EUR-Konvertierung aus Worker-Enrichment.
    for item in _load_unresolved_fx_issues():
        event_id = str(item.get("source_event_id", ""))
        rate_date = str(item.get("rate_date", ""))
        reason = str(item.get("reason", ""))
        if not event_id:
            continue
        payload_row = STORE.get_raw_event(event_id)
        payload = (payload_row or {}).get("payload", {}) if isinstance(payload_row, dict) else {}
        issue_id = f"missing_fx_rate:{event_id}:{rate_date}"
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="missing_fx_rate",
                severity="high",
                title="Fehlender USD->EUR FX-Kurs",
                detail=f"Event {event_id} hat keinen FX-Kurs für {rate_date} ({reason}).",
                source_event_id=event_id,
                payload=payload if isinstance(payload, dict) else {},
                overrides=overrides,
            )
        )

    # 5) Starke Kandidaten fuer Doppelzaehlung zwischen Referenz- und Primaerquellen.
    for conflict in _build_integration_conflicts(limit=100):
        issue_id = f"integration_conflict:{conflict['conflict_id']}"
        if issue_id not in overrides:
            continue
        primary_ids = ", ".join(conflict.get("primary_event_ids", [])[:3])
        reference_ids = ", ".join(conflict.get("reference_event_ids", [])[:3])
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="integration_conflict",
                severity="medium",
                title="Referenzimport überschneidet sich mit Primärdaten",
                detail=(
                    f"{conflict['day']} {conflict['asset']} {conflict['quantity']} "
                    f"liegt in Primärquelle(n) {conflict['primary_sources']} und Referenzquelle(n) "
                    f"{conflict['reference_sources']} vor. Primary: {primary_ids}; Reference: {reference_ids}"
                ),
                source_event_id=str(conflict.get("reference_event_ids", [""])[0]),
                payload={
                    "asset": conflict["asset"],
                    "timestamp_utc": conflict["day"],
                    "source": ",".join(conflict.get("reference_sources", [])),
                },
                overrides=overrides,
            )
        )

    # 6) Material taxable disposals with zero cost basis in the latest completed runs.
    for item in _build_zero_cost_tax_line_issues():
        issue_id = str(item["issue_id"])
        payload = {
            "asset": item["asset"],
            "timestamp_utc": item["first_sell_timestamp_utc"],
            "source": "tax_lines",
            "tax_year": item["tax_year"],
        }
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="zero_cost_tax_lots",
                severity=str(item["severity"]),
                title="Steuerzeilen mit Cost Basis 0",
                detail=(
                    f"Tax Year {item['tax_year']} {item['asset']}: {item['row_count']} steuerpflichtige "
                    f"Zeile(n) mit Cost Basis 0 und {item['proceeds_eur']} EUR Erloes. "
                    "Anschaffungskostenkette pruefen oder explizit als Nullbasis bestaetigen."
                ),
                source_event_id=str(item["sample_source_event_ids"][0] if item["sample_source_event_ids"] else ""),
                payload=payload,
                overrides=overrides,
                closed_tax_years=closed_tax_years,
            )
        )

    issues.sort(key=lambda item: (item.get("status") != "open", item.get("severity"), item.get("created_hint_utc")))
    return issues


def _latest_completed_jobs_by_year() -> dict[int, dict[str, Any]]:
    rows = STORE.list_processing_jobs(status="completed", limit=5000)
    latest: dict[int, dict[str, Any]] = {}
    for row in rows:
        year = int(row.get("tax_year") or 0)
        if year <= 0:
            continue
        current = latest.get(year)
        if current is None or str(row.get("updated_at_utc") or "") > str(current.get("updated_at_utc") or ""):
            latest[year] = row
    return latest


def _build_zero_cost_tax_line_issues() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    latest_jobs = _latest_completed_jobs_by_year()
    for year, job in sorted(latest_jobs.items()):
        job_id = str(job.get("job_id") or "")
        grouped: dict[str, dict[str, Any]] = {}
        for line in STORE.get_tax_lines(job_id):
            if str(line.get("tax_status") or "").lower() != "taxable":
                continue
            proceeds = _safe_decimal(line.get("proceeds_eur"))
            cost_basis = _safe_decimal(line.get("cost_basis_eur"))
            if proceeds <= 0 or cost_basis != 0:
                continue
            asset = str(line.get("asset") or "").upper().strip()
            bucket = grouped.setdefault(
                asset,
                {
                    "tax_year": year,
                    "job_id": job_id,
                    "asset": asset,
                    "row_count": 0,
                    "proceeds_eur": Decimal("0"),
                    "qty": Decimal("0"),
                    "first_sell_timestamp_utc": str(line.get("sell_timestamp_utc") or ""),
                    "sample_source_event_ids": [],
                    "sample_lot_source_event_ids": [],
                },
            )
            bucket["row_count"] += 1
            bucket["proceeds_eur"] += proceeds
            bucket["qty"] += _safe_decimal(line.get("qty"))
            sell_ts = str(line.get("sell_timestamp_utc") or "")
            if sell_ts and (not bucket["first_sell_timestamp_utc"] or sell_ts < bucket["first_sell_timestamp_utc"]):
                bucket["first_sell_timestamp_utc"] = sell_ts
            source_event_id = str(line.get("source_event_id") or "")
            if source_event_id and source_event_id not in bucket["sample_source_event_ids"]:
                bucket["sample_source_event_ids"].append(source_event_id)
            lot_source_event_id = str(line.get("lot_source_event_id") or "")
            if lot_source_event_id and lot_source_event_id not in bucket["sample_lot_source_event_ids"]:
                bucket["sample_lot_source_event_ids"].append(lot_source_event_id)
        for asset, bucket in sorted(grouped.items()):
            proceeds = bucket["proceeds_eur"]
            if proceeds < ZERO_COST_TAX_LINE_PROCEEDS_THRESHOLD_EUR:
                continue
            severity = "high" if proceeds >= Decimal("5000") else "medium"
            issues.append(
                {
                    "issue_id": f"zero_cost_tax_lots:{year}:{asset}:{job_id}",
                    "severity": severity,
                    "tax_year": year,
                    "job_id": job_id,
                    "asset": asset,
                    "row_count": bucket["row_count"],
                    "qty": str(bucket["qty"].normalize()),
                    "proceeds_eur": str(proceeds.quantize(Decimal("0.01"))),
                    "first_sell_timestamp_utc": bucket["first_sell_timestamp_utc"],
                    "sample_source_event_ids": bucket["sample_source_event_ids"][:10],
                    "sample_lot_source_event_ids": bucket["sample_lot_source_event_ids"][:10],
                }
            )
    return issues


def _build_integration_conflicts(limit: int = 200) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str, str, str], dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: {"primary": [], "reference": []}
    )
    mode_overrides = load_integration_mode_overrides()
    for event in STORE.list_raw_events():
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        mode = effective_integration_mode(integration_source_from_event(event), mode_overrides)
        if mode not in {"active", "reference"}:
            continue
        key = _reference_conflict_key(payload)
        if key is None:
            continue
        bucket_key = key
        bucket_side = "reference" if mode == "reference" else "primary"
        buckets[bucket_key][bucket_side].append(event)

    rows: list[dict[str, Any]] = []
    for (day, asset, quantity, direction), grouped in buckets.items():
        primary = grouped["primary"]
        reference = grouped["reference"]
        if not primary or not reference:
            continue
        primary_sources = sorted({integration_source_from_event(event) for event in primary})
        reference_sources = sorted({integration_source_from_event(event) for event in reference})
        primary_ids = [str(event.get("unique_event_id", "")) for event in primary[:10]]
        reference_ids = [str(event.get("unique_event_id", "")) for event in reference[:10]]
        rows.append(
            {
                "conflict_id": f"{day}:{asset}:{quantity}:{direction}",
                "day": day,
                "asset": asset,
                "quantity": quantity,
                "direction": direction,
                "primary_sources": primary_sources,
                "reference_sources": reference_sources,
                "primary_event_count": len(primary),
                "reference_event_count": len(reference),
                "primary_event_ids": primary_ids,
                "reference_event_ids": reference_ids,
                "severity": "medium",
                "suggested_action": "Referenzquelle als reference belassen oder einzelne Events mit Pflichtgrund ausschliessen.",
            }
        )
    rows.sort(key=lambda item: (item["day"], item["asset"], item["quantity"]))
    return rows[:limit]


def _reference_conflict_key(payload: dict[str, Any]) -> tuple[str, str, str, str] | None:
    day = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")[:10]
    asset = str(payload.get("asset") or "").strip().upper()
    quantity = _event_quantity_for_conflict(payload)
    direction = _event_direction_for_conflict(payload)
    if len(day) != 10 or not asset or quantity <= 0 or not direction:
        return None
    return day, asset, _decimal_key(quantity), direction


def _event_quantity_for_conflict(payload: dict[str, Any]) -> Decimal:
    for key in ("quantity", "amount", "qty"):
        value = _safe_decimal(payload.get(key))
        if value != 0:
            return abs(value)
    return Decimal("0")


def _event_direction_for_conflict(payload: dict[str, Any]) -> str:
    side = str(payload.get("side", "")).lower().strip()
    event_type = str(payload.get("event_type", "")).lower().strip()
    if side in {"in", "buy"}:
        return "in"
    if side in {"out", "sell"}:
        return "out"
    if any(token in event_type for token in ("deposit", "reward", "income", "buy", "in")):
        return "in"
    if any(token in event_type for token in ("withdraw", "sell", "fee", "out")):
        return "out"
    return ""


def _decimal_key(value: Decimal) -> str:
    with localcontext() as ctx:
        ctx.prec = max(50, len(value.as_tuple().digits) + 18)
        normalized = value.quantize(Decimal("0.000000000000000001")).normalize()
    return format(normalized, "f")


def _build_issue_row(
    issue_id: str,
    issue_type: str,
    severity: str,
    title: str,
    detail: str,
    source_event_id: str,
    payload: dict[str, Any],
    overrides: dict[str, dict[str, str]],
    closed_tax_years: set[int] | None = None,
) -> dict[str, Any]:
    override = overrides.get(issue_id, {})
    note = str(override.get("note", ""))
    tax_year = _safe_int(payload.get("tax_year"))
    review_scope = "closed_tax_year" if tax_year in (closed_tax_years or set()) else "current"
    is_current_scope = review_scope == "current"
    return {
        "issue_id": issue_id,
        "type": issue_type,
        "severity": severity,
        "status": str(override.get("status", "open")),
        "title": title,
        "detail": detail,
        "source_event_id": source_event_id,
        "asset": str(payload.get("asset", "")),
        "tax_year": tax_year,
        "review_scope": review_scope,
        "is_current_scope": is_current_scope,
        "scope_note": (
            "Altjahr ist als abgeschlossen markiert; Issue bleibt sichtbar, zaehlt aber nicht als aktueller Export-Blocker."
            if not is_current_scope
            else ""
        ),
        "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
        "source": str(payload.get("source", "")),
        "note": note,
        "updated_at_utc": str(override.get("updated_at_utc", "")),
        "created_hint_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
        "api_actions": {
            "context": {
                "method": "GET",
                "path": f"/api/v1/review/issue-context/{issue_id}",
            },
            "set_status": {
                "method": "POST",
                "path": "/api/v1/issues/update-status",
                "body": {
                    "issue_id": issue_id,
                    "status": "in_review",
                    "note": note,
                },
            },
            "confirm_zero_basis": {
                "method": "POST",
                "path": "/api/v1/issues/update-status",
                "body": {
                    "issue_id": issue_id,
                    "status": "wont_fix",
                    "note": "Explizite Review-Entscheidung: Anschaffungskette nicht belegbar, Nullbasis bleibt im Steuerreport sichtbar dokumentiert.",
                },
            },
        },
    }


def _parse_zero_cost_tax_lot_issue_id(issue_id: str) -> tuple[int, str, str] | None:
    parts = str(issue_id or "").strip().split(":", 3)
    if len(parts) != 4 or parts[0] != "zero_cost_tax_lots":
        return None
    try:
        year = int(parts[1])
    except ValueError:
        return None
    asset = parts[2].upper().strip()
    job_id = parts[3].strip()
    if year <= 0 or not asset or not job_id:
        return None
    return year, asset, job_id


def _build_zero_cost_tax_lot_issue_context(
    issue_id: str,
    year: int,
    asset: str,
    job_id: str,
    limit: int,
) -> dict[str, Any] | None:
    job = get_processing_job(job_id)
    if job is None or int(job.get("tax_year") or 0) != year:
        return None
    rows: list[dict[str, Any]] = []
    row_count = 0
    total_qty = Decimal("0")
    total_proceeds = Decimal("0")
    for line in STORE.get_tax_lines(job_id):
        if str(line.get("tax_status") or "").lower() != "taxable":
            continue
        if str(line.get("asset") or "").upper().strip() != asset:
            continue
        proceeds = _safe_decimal(line.get("proceeds_eur"))
        cost_basis = _safe_decimal(line.get("cost_basis_eur"))
        if proceeds <= 0 or cost_basis != 0:
            continue
        qty = _safe_decimal(line.get("qty"))
        row_count += 1
        total_qty += qty
        total_proceeds += proceeds
        if len(rows) >= limit:
            continue
        rows.append(
            {
                "line_id": line.get("line_id"),
                "asset": str(line.get("asset") or ""),
                "qty": str(qty),
                "sell_timestamp_utc": str(line.get("sell_timestamp_utc") or ""),
                "buy_timestamp_utc": str(line.get("buy_timestamp_utc") or ""),
                "proceeds_eur": str(proceeds),
                "cost_basis_eur": str(cost_basis),
                "gain_loss_eur": str(_safe_decimal(line.get("gain_loss_eur"))),
                "source_event_id": str(line.get("source_event_id") or ""),
                "lot_source_event_id": str(line.get("lot_source_event_id") or ""),
                "transfer_chain_id": str(line.get("transfer_chain_id") or ""),
            }
        )
    if row_count == 0:
        return None
    overrides = _load_issue_overrides()
    status = str(overrides.get(issue_id, {}).get("status", "open"))
    note = str(overrides.get(issue_id, {}).get("note", ""))
    return {
        "issue_id": issue_id,
        "type": "zero_cost_tax_lots",
        "tax_year": year,
        "asset": asset,
        "job_id": job_id,
        "status": status,
        "note": note,
        "row_count": row_count,
        "returned_row_count": len(rows),
        "total_qty": str(total_qty),
        "total_proceeds_eur": str(total_proceeds),
        "tax_lines": rows,
        "decision_options": [
            {
                "status": "open",
                "meaning": "Weiter offen lassen, weil Primaerbeleg oder Anschaffungskette noch gesucht wird.",
            },
            {
                "status": "in_review",
                "meaning": "Fachlich in Pruefung; blockiert weiter die Review-Gates.",
            },
            {
                "status": "wont_fix",
                "meaning": "Explizite Nullbasis-Entscheidung; der Gewinn bleibt im Report sichtbar, aber das Issue blockiert nicht mehr.",
            },
        ],
        "api_actions": {
            "set_status": {
                "method": "POST",
                "path": "/api/v1/issues/update-status",
                "body": {"issue_id": issue_id, "status": "in_review", "note": note},
            },
            "confirm_zero_basis": {
                "method": "POST",
                "path": "/api/v1/issues/update-status",
                "body": {
                    "issue_id": issue_id,
                    "status": "wont_fix",
                    "note": "Explizite Review-Entscheidung: Anschaffungskette nicht belegbar, Nullbasis bleibt im Steuerreport sichtbar dokumentiert.",
                },
            },
        },
    }


def _negative_balance_checkpoints(as_of: str | None, year: int | None) -> list[str]:
    if as_of:
        day = str(as_of).strip()[:10]
        if len(day) == 10 and day[4] == "-" and day[7] == "-" and day.replace("-", "").isdigit():
            return [day]
        return []
    safe_year = _valid_negative_balance_year(year)
    if safe_year is None:
        if year is None:
            return [datetime.now(UTC).date().isoformat()]
        return []
    month_end_days: dict[str, str] = {}
    events, _summary = _list_effective_review_events()
    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if len(ts_raw) < 10 or ts_raw[:4] != str(safe_year):
            continue
        month_end_days[ts_raw[:7]] = ts_raw[:10]
    return [month_end_days[key] for key in sorted(month_end_days)]


def _valid_negative_balance_year(year: int | None) -> int | None:
    if year is None:
        return None
    try:
        safe_year = int(year)
    except (TypeError, ValueError):
        return None
    if safe_year < 2009 or safe_year > 2100:
        return None
    return safe_year


def _negative_balance_api_contract() -> dict[str, str]:
    return {
        "list": "GET /api/v1/review/negative-balances?as_of=YYYY-MM-DD&asset=ASSET",
        "set_status": "POST /api/v1/issues/update-status",
        "comment_event": "POST /api/v1/review/comment",
        "ignore_event": "POST /api/v1/review/ignore",
        "merge_events": "POST /api/v1/review/merge",
        "split_event": "POST /api/v1/review/split",
        "tax_event_override": "POST /api/v1/tax/event-override/upsert",
        "transaction_search": "GET /api/v1/dashboard/transaction-search",
    }


def _build_negative_balance_rows_for_date(
    events: list[dict[str, Any]],
    as_of: str,
    ignored_mints: set[str],
    fx_lookup: dict[tuple[str, str], list[tuple[str, Decimal]]],
    fx_rate_cache: dict[str, Decimal],
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal],
    overrides: dict[str, dict[str, str]],
    asset_filter: str,
    include_events: int,
) -> list[dict[str, Any]]:
    balances: dict[str, Decimal] = defaultdict(Decimal)
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"in": 0, "out": 0, "neutral": 0})
    source_breakdown: dict[str, dict[tuple[str, str, str], dict[str, Any]]] = defaultdict(dict)
    recent_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    first_negative_at: dict[str, str] = {}
    token_aliases = _load_token_aliases()
    canonical_asset_filter = _asset_canonical_symbol(asset_filter, token_aliases) if asset_filter else ""

    for row in sorted(events, key=lambda item: str((item.get("payload") or {}).get("timestamp_utc") or (item.get("payload") or {}).get("timestamp") or "")):
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if len(ts_raw) < 10 or ts_raw[:10] > as_of:
            continue
        raw_asset = str(payload.get("asset") or "").upper().strip()
        asset = _payload_asset_canonical_symbol(payload, token_aliases)
        if not asset or _normalize_mint(raw_asset) in ignored_mints or _normalize_mint(asset) in ignored_mints:
            continue
        if canonical_asset_filter and asset != canonical_asset_filter:
            continue
        qty = _dashboard_event_quantity(payload)
        side = str(payload.get("side") or "").lower().strip()
        if side in {"in", "buy"}:
            delta = abs(qty)
            counts[asset]["in"] += 1
        elif side in {"out", "sell"}:
            delta = -abs(qty)
            counts[asset]["out"] += 1
        else:
            delta = qty
            counts[asset]["neutral"] += 1
        before = balances[asset]
        after = before + delta
        balances[asset] = after
        if before >= 0 > after:
            first_negative_at.setdefault(asset, ts_raw)

        key = (
            str(payload.get("source") or "unknown").strip() or "unknown",
            str(payload.get("event_type") or "unknown").strip() or "unknown",
            side or "neutral",
        )
        bucket = source_breakdown[asset].setdefault(
            key,
            {"source": key[0], "event_type": key[1], "side": key[2], "event_count": 0, "net_quantity": Decimal("0")},
        )
        bucket["event_count"] = int(bucket["event_count"]) + 1
        bucket["net_quantity"] = _safe_decimal(bucket["net_quantity"]) + delta
        if include_events > 0:
            event_row = _negative_balance_event_row(row, payload, delta)
            recent_events[asset].append(event_row)
            if len(recent_events[asset]) > include_events:
                recent_events[asset] = recent_events[asset][-include_events:]

    rows: list[dict[str, Any]] = []
    for asset, balance in balances.items():
        if balance >= 0:
            continue
        price_usd = _cached_asset_usd_price_on_or_before(
            asset,
            as_of,
            asset_usd_price_cache=asset_usd_price_cache,
            fx_lookup=fx_lookup,
        )
        value_usd = balance * price_usd if price_usd > 0 else Decimal("0")
        issue_id = f"negative_balance:{as_of}:{asset}"
        override = overrides.get(issue_id, {})
        breakdown_rows = [
            {
                "source": str(item["source"]),
                "event_type": str(item["event_type"]),
                "side": str(item["side"]),
                "event_count": int(item["event_count"]),
                "net_quantity": _decimal_to_plain_review(_safe_decimal(item["net_quantity"])),
            }
            for item in source_breakdown[asset].values()
        ]
        breakdown_rows.sort(key=lambda item: _safe_decimal(item["net_quantity"]).copy_abs(), reverse=True)
        last_event = recent_events[asset][-1] if recent_events[asset] else {}
        rows.append(
            {
                "issue_id": issue_id,
                "type": "negative_balance",
                "severity": _negative_balance_severity(balance=balance, value_usd=value_usd, price_usd=price_usd),
                "status": str(override.get("status", "open")),
                "note": str(override.get("note", "")),
                "updated_at_utc": str(override.get("updated_at_utc", "")),
                "date": as_of,
                "asset": asset,
                "balance": _decimal_to_plain_review(balance),
                "price_usd": _decimal_to_plain_review(price_usd),
                "value_usd": _decimal_to_plain_review(value_usd),
                "priced": price_usd > 0,
                "first_negative_at_utc": first_negative_at.get(asset, ""),
                "event_counts": counts[asset],
                "source_breakdown": breakdown_rows[:20],
                "last_event": last_event,
                "recent_events": recent_events[asset],
                "api_actions": {
                    "set_status": {
                        "method": "POST",
                        "path": "/api/v1/issues/update-status",
                        "body": {"issue_id": issue_id, "status": "in_review", "note": "Negativbestand wird fachlich geprüft."},
                    },
                    "comment_last_event": {
                        "method": "POST",
                        "path": "/api/v1/review/comment",
                        "body": {
                            "source_event_id": str(last_event.get("source_event_id", "")),
                            "reason_code": "negative_balance_review",
                            "comment": "Prüfung wegen negativem Bestand zum Stichtag.",
                        },
                    },
                    "transaction_search": {
                        "method": "GET",
                        "path": f"/api/v1/dashboard/transaction-search?asset={asset}&limit=100",
                    },
                },
                "suggested_checks": [
                    "Fehlenden Zufluss vor diesem Abgang importieren oder Quelle aktivieren.",
                    "Doppelte Out-Legs, Auto-Balancing-Outs oder Referenzdaten gegen Primärdaten prüfen.",
                    "Bei Swaps prüfen, ob In- und Out-Leg demselben wirtschaftlichen Vorgang zugeordnet sind.",
                ],
            }
        )
    return rows


def _negative_balance_event_row(row: dict[str, Any], payload: dict[str, Any], delta: Decimal) -> dict[str, Any]:
    return {
        "source_event_id": str(row.get("unique_event_id") or ""),
        "source_file_id": str(row.get("source_file_id") or ""),
        "row_index": int(row.get("row_index") or 0),
        "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
        "source": str(payload.get("source") or ""),
        "event_type": str(payload.get("event_type") or ""),
        "asset": str(payload.get("asset") or "").upper().strip(),
        "canonical_asset": _payload_asset_canonical_symbol(payload),
        "side": str(payload.get("side") or ""),
        "quantity": _decimal_to_plain_review(_dashboard_event_quantity(payload)),
        "delta": _decimal_to_plain_review(delta),
        "tx_id": str(payload.get("tx_id") or payload.get("transaction_hash") or payload.get("signature") or ""),
        "wallet_address": str(payload.get("wallet_address") or ""),
        "counterparty_wallet": str(payload.get("counterparty_wallet") or ""),
    }


def _parse_negative_balance_issue_id(issue_id: str) -> tuple[str, str] | None:
    parts = str(issue_id or "").split(":", 2)
    if len(parts) != 3 or parts[0] != "negative_balance":
        return None
    day = parts[1].strip()
    asset = parts[2].upper().strip()
    if len(day) != 10 or day[4] != "-" or day[7] != "-" or not day.replace("-", "").isdigit() or not asset:
        return None
    return day, asset


def _build_negative_balance_issue_context(
    events: list[dict[str, Any]],
    issue: dict[str, Any],
    as_of: str,
    asset: str,
    window_days: int,
    limit: int,
) -> dict[str, Any]:
    asset_events: list[dict[str, Any]] = []
    related_tx_ids = {
        str(event.get("tx_id") or "").strip()
        for event in [issue.get("last_event", {}), *(issue.get("recent_events") or [])]
        if isinstance(event, dict) and str(event.get("tx_id") or "").strip()
    }
    same_tx_events: list[dict[str, Any]] = []
    yearly_totals: dict[str, dict[str, Any]] = {}
    running = Decimal("0")
    first_event = ""
    last_event = ""
    first_negative_at = str(issue.get("first_negative_at_utc") or "")
    first_negative_dt = _parse_review_datetime(first_negative_at)
    window_start = first_negative_dt - timedelta(days=window_days) if first_negative_dt is not None else None
    window_end = first_negative_dt + timedelta(days=window_days) if first_negative_dt is not None else None
    token_aliases = _load_token_aliases()
    canonical_asset = _asset_canonical_symbol(asset, token_aliases)

    for row in sorted(events, key=lambda item: str((item.get("payload") or {}).get("timestamp_utc") or (item.get("payload") or {}).get("timestamp") or "")):
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if len(ts_raw) >= 10:
            if not first_event:
                first_event = ts_raw
            last_event = ts_raw
        tx_id = str(payload.get("tx_id") or payload.get("transaction_hash") or payload.get("signature") or "").strip()
        event_asset = _payload_asset_canonical_symbol(payload, token_aliases)
        if tx_id and tx_id in related_tx_ids:
            same_tx_events.append(_negative_balance_event_row(row, payload, _event_delta(payload)))
        if event_asset != canonical_asset:
            continue
        delta = _event_delta(payload)
        running += delta
        if len(ts_raw) >= 4:
            year_bucket = yearly_totals.setdefault(
                ts_raw[:4],
                {"year": ts_raw[:4], "in_quantity": Decimal("0"), "out_quantity": Decimal("0"), "net_quantity": Decimal("0"), "event_count": 0},
            )
            year_bucket["event_count"] = int(year_bucket["event_count"]) + 1
            year_bucket["net_quantity"] = _safe_decimal(year_bucket["net_quantity"]) + delta
            if delta >= 0:
                year_bucket["in_quantity"] = _safe_decimal(year_bucket["in_quantity"]) + delta
            else:
                year_bucket["out_quantity"] = _safe_decimal(year_bucket["out_quantity"]) + delta.copy_abs()
        if len(ts_raw) < 10 or ts_raw[:10] > as_of:
            continue
        ts = _parse_review_datetime(ts_raw)
        in_window = (
            window_start is None
            or window_end is None
            or ts is None
            or (window_start <= ts <= window_end)
        )
        row_payload = _negative_balance_event_row(row, payload, delta)
        row_payload["running_balance_after"] = _decimal_to_plain_review(running)
        if in_window or len(asset_events) < limit:
            asset_events.append(row_payload)

    asset_events = asset_events[-limit:]
    return {
        "scope": {"as_of": as_of, "asset": asset, "window_days": window_days, "limit": limit},
        "global_event_range": {"first_timestamp_utc": first_event, "last_timestamp_utc": last_event},
        "asset_yearly_totals": [
            {
                "year": item["year"],
                "event_count": int(item["event_count"]),
                "in_quantity": _decimal_to_plain_review(_safe_decimal(item["in_quantity"])),
                "out_quantity": _decimal_to_plain_review(_safe_decimal(item["out_quantity"])),
                "net_quantity": _decimal_to_plain_review(_safe_decimal(item["net_quantity"])),
            }
            for item in sorted(yearly_totals.values(), key=lambda value: str(value["year"]))
        ],
        "context_events": asset_events,
        "same_transaction_events": same_tx_events[:limit],
        "regulatory_context": DAC8_CARF_CONTEXT,
        "analysis_contract": {
            "llm_should_return": [
                "priority",
                "probable_cause",
                "confidence",
                "evidence_event_ids",
                "missing_data_questions",
                "recommended_api_actions",
                "risk_note",
            ],
            "allowed_action_policy": "Vorschlaege duerfen gespeichert werden; steuerlich wirksame Merge/Split/Override-Aktionen bleiben bestaetigungspflichtig.",
            "regulatory_policy": "DAC8/CARF/KStTG-Daten duerfen nur als Referenz-/Plausibilitaetsdaten genutzt werden; keine automatische Steuerberechnung und kein Ersetzen von FIFO, Haltefrist, Anschaffungskosten oder Gebuehrenbehandlung.",
        },
    }


def _event_delta(payload: dict[str, Any]) -> Decimal:
    qty = _dashboard_event_quantity(payload)
    side = str(payload.get("side") or "").lower().strip()
    if side in {"in", "buy"}:
        return abs(qty)
    if side in {"out", "sell"}:
        return -abs(qty)
    return qty


def _parse_review_datetime(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _build_ai_review_suggestion(context_payload: dict[str, Any], engine: str) -> dict[str, Any]:
    issue = context_payload.get("issue", {})
    context = context_payload.get("context", {})
    issue_id = str(context_payload.get("issue_id") or issue.get("issue_id") or "")
    asset = str(issue.get("asset") or "").upper().strip()
    balance = _safe_decimal(issue.get("balance"))
    value_usd = _safe_decimal(issue.get("value_usd"))
    context_events = [item for item in context.get("context_events", []) if isinstance(item, dict)]
    out_count = sum(1 for item in context_events if _safe_decimal(item.get("delta")) < 0)
    in_count = sum(1 for item in context_events if _safe_decimal(item.get("delta")) > 0)
    same_tx_events = [item for item in context.get("same_transaction_events", []) if isinstance(item, dict)]
    yearly_totals = [item for item in context.get("asset_yearly_totals", []) if isinstance(item, dict)]
    as_of = str((context.get("scope") or {}).get("as_of") or issue.get("date") or "")
    year_total = next((item for item in yearly_totals if str(item.get("year") or "") == as_of[:4]), {})
    year_net = _safe_decimal(year_total.get("net_quantity")) if year_total else Decimal("0")
    priority = _ai_priority_for_issue(issue)
    confidence = "medium"
    probable_cause = (
        f"Stichtagsnegativbestand fuer {asset}: bis {as_of} liegen mehr Abgaenge als Zugaenge vor."
    )
    if str(issue.get("source_breakdown") or "").lower().find("blockpit") >= 0:
        probable_cause += " Blockpit-Legs dominieren den Befund; Primaer-/Referenzquellen und fehlende Zufluesse pruefen."
    if year_net > 0 and balance < 0:
        probable_cause += " Der Jahresnettosaldo ist spaeter positiv, daher ist der Zeitpunktbezug entscheidend."
        confidence = "medium"
    if same_tx_events:
        probable_cause += " Gleiche Transaktions-Events sind vorhanden und sollten als Swap-/Gegenleg-Kontext geprueft werden."
    evidence_ids = [
        str(item.get("source_event_id") or "")
        for item in [issue.get("last_event", {}), *context_events[-5:]]
        if isinstance(item, dict) and str(item.get("source_event_id") or "")
    ]
    evidence_ids = list(dict.fromkeys(evidence_ids))[:10]
    suggested_status_note = (
        f"KI/ML-Vorschlag: {asset}-Negativbestand {as_of} priorisiert; "
        "fehlende Zufluesse, Referenzquellen und Swap-/Gegenlegs pruefen."
    )
    suggestion_id = f"ai_suggestion:{issue_id}:{_stable_suggestion_suffix(issue_id, probable_cause)}"
    return {
        "suggestion_id": suggestion_id,
        "issue_id": issue_id,
        "issue_type": str(context_payload.get("issue_type") or issue.get("type") or ""),
        "engine": str(engine or "deterministic-v1"),
        "status": "open",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "priority": priority,
        "confidence": confidence,
        "summary": suggested_status_note,
        "probable_cause": probable_cause,
        "primary_evidence_event_ids": evidence_ids,
        "observations": {
            "asset": asset,
            "as_of": as_of,
            "balance": _decimal_to_plain_review(balance),
            "value_usd": _decimal_to_plain_review(value_usd),
            "context_event_count": len(context_events),
            "context_in_count": in_count,
            "context_out_count": out_count,
            "same_transaction_event_count": len(same_tx_events),
            "asset_yearly_totals": yearly_totals,
        },
        "missing_data_questions": [
            f"Gibt es vor {as_of} nicht importierte {asset}-Zufluesse aus Wallet, Exchange oder Referenzquelle?",
            "Sind betroffene Referenzdaten als reference statt active konfiguriert?",
            "Gehoeren nahe In-/Out-Legs zu einem gemeinsamen Swap oder internen Transfer?",
        ],
        "recommended_api_actions": [
            {
                "action": "set_status",
                "method": "POST",
                "path": "/api/v1/issues/update-status",
                "body": {"issue_id": issue_id, "status": "in_review", "note": suggested_status_note},
                "auto_apply_safe": True,
            },
            {
                "action": "comment_last_event",
                "method": "POST",
                "path": "/api/v1/review/comment",
                "body": {
                    "source_event_id": evidence_ids[0] if evidence_ids else "",
                    "reason_code": "negative_balance_review",
                    "comment": suggested_status_note,
                },
                "auto_apply_safe": True,
            },
            {
                "action": "search_asset",
                "method": "GET",
                "path": f"/api/v1/dashboard/transaction-search?asset={asset}&year={as_of[:4]}&limit=500",
                "auto_apply_safe": False,
            },
        ],
        "risk_note": (
            "Keine automatische Merge/Split/Ignore- oder Tax-Override-Aktion. "
            "Diese Vorschlaege bleiben bestaetigungspflichtig, weil sie steuerlich wirksam sein koennen."
        ),
    }


def _build_ai_review_suggestion_for_engine(
    context_payload: dict[str, Any],
    engine: str,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    normalized_engine = str(engine or "deterministic-v1").strip().lower()
    warnings: list[dict[str, str]] = []
    if normalized_engine in {"ollama", "ollama-v1"}:
        try:
            suggestion = _build_ollama_review_suggestion(context_payload=context_payload, engine=normalized_engine)
            return suggestion, warnings
        except OllamaReviewError as exc:
            warnings.append(
                {
                    "code": "ollama_review_fallback",
                    "message": f"Ollama-Analyse nicht verfuegbar, deterministic-v1 genutzt: {exc}",
                }
            )
    if normalized_engine in {"ollama-classifier", "ollama-classification", "classifier"}:
        try:
            suggestion = _build_ollama_classification_review_suggestion(
                context_payload=context_payload,
                engine=normalized_engine,
            )
            return suggestion, warnings
        except OllamaReviewError as exc:
            warnings.append(
                {
                    "code": "ollama_classification_fallback",
                    "message": f"Ollama-Klassifizierung nicht verfuegbar, deterministic-v1 genutzt: {exc}",
                }
            )
    if normalized_engine in {"llama-cpp-classifier", "llamacpp-classifier", "llama.cpp-classifier"}:
        try:
            suggestion = _build_llama_cpp_classification_review_suggestion(
                context_payload=context_payload,
                engine=normalized_engine,
            )
            return suggestion, warnings
        except OllamaReviewError as exc:
            warnings.append(
                {
                    "code": "llama_cpp_classification_fallback",
                    "message": f"llama.cpp-Klassifizierung nicht verfuegbar, deterministic-v1 genutzt: {exc}",
                }
            )
    return _build_ai_review_suggestion(context_payload=context_payload, engine="deterministic-v1"), warnings


def _build_ollama_review_suggestion(context_payload: dict[str, Any], engine: str) -> dict[str, Any]:
    runtime = resolve_effective_runtime_config().get("runtime", {})
    ai_config = runtime.get("ai_review", {}) if isinstance(runtime, dict) else {}
    if not isinstance(ai_config, dict):
        ai_config = {}
    config = OllamaReviewConfig(
        base_url=str(ai_config.get("ollama_base_url") or "http://127.0.0.1:11434"),
        model=str(ai_config.get("ollama_model") or "qwen2.5:14b"),
        timeout_seconds=float(ai_config.get("ollama_timeout_seconds") or 120.0),
        temperature=float(ai_config.get("ollama_temperature") or 0.1),
        num_ctx=int(ai_config.get("ollama_num_ctx") or 4096),
    )
    ollama = analyze_issue_with_ollama(context_payload=context_payload, config=config)
    guardrail_violation = _ollama_regulatory_guardrail_violation(ollama)
    if guardrail_violation:
        raise OllamaReviewError(f"ollama_regulatory_guardrail:{guardrail_violation}")
    deterministic = _build_ai_review_suggestion(context_payload=context_payload, engine=engine)
    deterministic["engine"] = f"{engine}:{config.model}"
    deterministic["priority"] = str(ollama.get("priority") or deterministic["priority"])
    deterministic["confidence"] = str(ollama.get("confidence") or deterministic["confidence"])
    if str(ollama.get("probable_cause") or "").strip():
        deterministic["probable_cause"] = str(ollama["probable_cause"]).strip()
    if str(ollama.get("risk_note") or "").strip():
        deterministic["risk_note"] = str(ollama["risk_note"]).strip()
    evidence = [str(item).strip() for item in ollama.get("evidence_event_ids", []) if str(item).strip()]
    if evidence:
        deterministic["primary_evidence_event_ids"] = evidence[:10]
    questions = [str(item).strip() for item in ollama.get("missing_data_questions", []) if str(item).strip()]
    if questions:
        deterministic["missing_data_questions"] = questions[:20]
    actions = _validated_ollama_actions(
        ollama_actions=ollama.get("recommended_api_actions", []),
        fallback_actions=deterministic["recommended_api_actions"],
        issue_id=str(deterministic.get("issue_id") or ""),
    )
    deterministic["recommended_api_actions"] = actions
    deterministic["summary"] = f"Ollama-Vorschlag: {deterministic['probable_cause'][:420]}"
    deterministic["suggestion_id"] = (
        f"ai_suggestion:{deterministic['issue_id']}:{_stable_suggestion_suffix(str(deterministic['issue_id']), deterministic['probable_cause'])}"
    )
    return deterministic


def _build_ollama_classification_review_suggestion(context_payload: dict[str, Any], engine: str) -> dict[str, Any]:
    runtime = resolve_effective_runtime_config().get("runtime", {})
    ai_config = runtime.get("ai_review", {}) if isinstance(runtime, dict) else {}
    if not isinstance(ai_config, dict):
        ai_config = {}
    config = OllamaReviewConfig(
        base_url=str(ai_config.get("ollama_base_url") or "http://127.0.0.1:11434"),
        model=str(ai_config.get("ollama_model") or "qwen2.5:14b"),
        timeout_seconds=float(ai_config.get("ollama_timeout_seconds") or 120.0),
        temperature=float(ai_config.get("ollama_temperature") or 0.1),
        num_ctx=int(ai_config.get("ollama_num_ctx") or 4096),
    )
    classification = classify_issue_with_ollama(context_payload=context_payload, config=config)
    guardrail_violation = _ollama_regulatory_guardrail_violation(
        {
            "probable_cause": classification.get("rationale", ""),
            "risk_note": "",
            "missing_data_questions": classification.get("missing_data_questions", []),
        }
    )
    if guardrail_violation:
        raise OllamaReviewError(f"ollama_regulatory_guardrail:{guardrail_violation}")

    return _build_classification_review_suggestion(
        context_payload=context_payload,
        engine=f"{engine}:{config.model}",
        classification=classification,
    )


def _build_classification_review_suggestion(
    context_payload: dict[str, Any],
    engine: str,
    classification: dict[str, Any],
) -> dict[str, Any]:
    deterministic = _build_ai_review_suggestion(context_payload=context_payload, engine=engine)
    category = str(classification.get("cause_category") or "unknown")
    confidence = str(classification.get("confidence") or deterministic["confidence"])
    rationale = str(classification.get("rationale") or "").strip()
    deterministic["engine"] = engine
    deterministic["confidence"] = confidence
    deterministic["classification"] = {
        "cause_category": category,
        "confidence": confidence,
        "rationale": rationale,
    }
    if rationale:
        deterministic["probable_cause"] = (
            f"{_classification_label(category)}: {rationale} "
            f"Konservative Basispruefung: {deterministic['probable_cause']}"
        )[:1200]
        deterministic["summary"] = f"KI-Klassifizierung: {_classification_label(category)}"
    valid_event_ids = _context_source_event_ids(context_payload)
    evidence = [
        str(item).strip()
        for item in classification.get("evidence_event_ids", [])
        if str(item).strip() and str(item).strip() in valid_event_ids
    ]
    if evidence:
        deterministic["primary_evidence_event_ids"] = evidence[:10]
    questions = [str(item).strip() for item in classification.get("missing_data_questions", []) if str(item).strip()]
    if questions:
        deterministic["missing_data_questions"] = questions[:10] + [
            item for item in deterministic["missing_data_questions"] if item not in questions
        ]
        deterministic["missing_data_questions"] = deterministic["missing_data_questions"][:20]
    deterministic["suggestion_id"] = (
        f"ai_suggestion:{deterministic['issue_id']}:{_stable_suggestion_suffix(str(deterministic['issue_id']), deterministic['probable_cause'])}"
    )
    return deterministic


def _build_llama_cpp_classification_review_suggestion(
    context_payload: dict[str, Any],
    engine: str,
) -> dict[str, Any]:
    runtime = resolve_effective_runtime_config().get("runtime", {})
    ai_config = runtime.get("ai_review", {}) if isinstance(runtime, dict) else {}
    if not isinstance(ai_config, dict):
        ai_config = {}
    config = OpenAICompatibleReviewConfig(
        base_url=str(ai_config.get("llama_cpp_base_url") or "http://127.0.0.1:11435"),
        model=str(ai_config.get("llama_cpp_model") or "qwen3-coder-30b-a3b-llamacpp"),
        timeout_seconds=float(ai_config.get("llama_cpp_timeout_seconds") or 180.0),
        temperature=float(ai_config.get("llama_cpp_temperature") or 0.1),
        max_tokens=int(ai_config.get("llama_cpp_max_tokens") or 384),
    )
    classification = classify_issue_with_openai_compatible(context_payload=context_payload, config=config)
    guardrail_violation = _ollama_regulatory_guardrail_violation(
        {
            "probable_cause": classification.get("rationale", ""),
            "risk_note": "",
            "missing_data_questions": classification.get("missing_data_questions", []),
        }
    )
    if guardrail_violation:
        raise OllamaReviewError(f"llama_cpp_regulatory_guardrail:{guardrail_violation}")
    deterministic = _build_classification_review_suggestion(
        context_payload=context_payload,
        engine=f"{engine}:{config.model}",
        classification=classification,
    )
    return deterministic


def _context_source_event_ids(context_payload: dict[str, Any]) -> set[str]:
    issue = context_payload.get("issue", {})
    context = context_payload.get("context", {})
    rows: list[Any] = []
    if isinstance(issue, dict):
        rows.append(issue.get("last_event", {}))
        rows.extend(list(issue.get("recent_events", [])) if isinstance(issue.get("recent_events"), list) else [])
    if isinstance(context, dict):
        rows.extend(list(context.get("context_events", [])) if isinstance(context.get("context_events"), list) else [])
        rows.extend(
            list(context.get("same_transaction_events", []))
            if isinstance(context.get("same_transaction_events"), list)
            else []
        )
    return {
        str(item.get("source_event_id") or "").strip()
        for item in rows
        if isinstance(item, dict) and str(item.get("source_event_id") or "").strip()
    }


def _classification_label(category: str) -> str:
    labels = {
        "missing_inflow": "fehlender Zufluss",
        "duplicate_reference": "moegliches Referenzduplikat",
        "swap_counterleg": "Swap-/Gegenleg-Kontext",
        "derivative_or_fee_context": "Derivate-/Gebuehren-Kontext",
        "timing_boundary": "Stichtags-/Timing-Kontext",
        "provider_scope_unclear": "unklarer Provider-/Quellen-Scope",
        "unknown": "unklare Ursache",
    }
    return labels.get(str(category or "unknown"), "unklare Ursache")


def _ollama_regulatory_guardrail_violation(ollama: dict[str, Any]) -> str:
    text_parts = [
        str(ollama.get("probable_cause") or ""),
        str(ollama.get("risk_note") or ""),
        " ".join(str(item) for item in ollama.get("missing_data_questions", []) if str(item).strip())
        if isinstance(ollama.get("missing_data_questions"), list)
        else "",
    ]
    text = " ".join(text_parts).lower()
    blocked_fragments = {
        "regulatory violation": "regulatory_violation_claim",
        "tax evasion": "tax_evasion_claim",
        "fraud": "fraud_claim",
        "violation of dac8": "dac8_violation_claim",
        "violation of carf": "carf_violation_claim",
        "violation of ksttg": "ksttg_violation_claim",
        "regulatory requirement to report this loss": "loss_reporting_requirement_claim",
        "compliance with dac8": "dac8_compliance_claim",
        "compliance with carf": "carf_compliance_claim",
        "compliance with ksttg": "ksttg_compliance_claim",
    }
    for fragment, code in blocked_fragments.items():
        if fragment in text:
            return code
    return ""


def _validated_ollama_actions(
    ollama_actions: Any,
    fallback_actions: list[dict[str, Any]],
    issue_id: str,
) -> list[dict[str, Any]]:
    allowed_paths = {
        "/api/v1/issues/update-status",
        "/api/v1/review/comment",
        "/api/v1/dashboard/transaction-search",
        "/api/v1/review/integration-conflicts",
        "/api/v1/review/negative-balances",
        "/api/v1/review/issue-context",
    }
    result: list[dict[str, Any]] = []
    if isinstance(ollama_actions, list):
        for action in ollama_actions:
            if not isinstance(action, dict):
                continue
            path = str(action.get("path") or "").strip()
            if not any(path.startswith(allowed) for allowed in allowed_paths):
                continue
            action_name = str(action.get("action") or "").strip()
            auto_apply_safe = bool(action.get("auto_apply_safe")) and action_name in {"set_status", "comment_last_event"}
            body_raw = action.get("body")
            body: dict[str, Any] = body_raw if isinstance(body_raw, dict) else {}
            if action_name == "set_status":
                body = {**body, "issue_id": issue_id, "status": "in_review"}
            result.append(
                {
                    "action": action_name,
                    "method": str(action.get("method") or "GET").strip().upper(),
                    "path": path,
                    "body": body,
                    "auto_apply_safe": auto_apply_safe,
                }
            )
    safe_actions = {str(item.get("action") or "") for item in result if item.get("auto_apply_safe")}
    for fallback in fallback_actions:
        if bool(fallback.get("auto_apply_safe")) and str(fallback.get("action") or "") not in safe_actions:
            result.insert(0, fallback)
    return result[:20] if result else fallback_actions


def _ai_priority_for_issue(issue: dict[str, Any]) -> str:
    severity = str(issue.get("severity") or "").lower()
    value_abs = _safe_decimal(issue.get("value_usd")).copy_abs()
    if severity == "high" or value_abs >= Decimal("1000"):
        return "high"
    if severity == "medium" or value_abs >= Decimal("100"):
        return "medium"
    return "low"


def _stable_suggestion_suffix(issue_id: str, text: str) -> str:
    import hashlib

    digest = hashlib.sha256(f"{issue_id}|{text}".encode()).hexdigest()
    return digest[:12]


def _load_ai_review_suggestions() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting("runtime.ai_review_suggestions")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for suggestion_id_raw, payload in raw.items():
        suggestion_id = str(suggestion_id_raw).strip()
        if not suggestion_id or not isinstance(payload, dict):
            continue
        item = dict(payload)
        item["suggestion_id"] = str(item.get("suggestion_id") or suggestion_id)
        item["issue_id"] = str(item.get("issue_id") or "")
        item["status"] = str(item.get("status") or "open")
        result[suggestion_id] = item
    return result


def _ai_suggestion_comment_text(suggestion: dict[str, Any], note: str | None) -> str:
    lines = [
        str(suggestion.get("summary") or "KI/ML-Review-Vorschlag"),
        f"Confidence: {suggestion.get('confidence', '')}; Priority: {suggestion.get('priority', '')}",
        str(suggestion.get("probable_cause") or ""),
    ]
    if note:
        lines.append(f"Manuelle Notiz: {note}")
    return "\n".join([line for line in lines if line]).strip()


def _negative_balance_severity(balance: Decimal, value_usd: Decimal, price_usd: Decimal) -> str:
    if price_usd <= 0:
        return "medium" if balance.copy_abs() >= Decimal("1") else "low"
    value_abs = value_usd.copy_abs()
    if value_abs >= Decimal("1000"):
        return "high"
    if value_abs >= Decimal("100"):
        return "medium"
    return "low"


def _decimal_to_plain_review(value: Decimal) -> str:
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def _is_trade_like(payload: dict[str, Any]) -> bool:
    side = str(payload.get("side", "")).lower().strip()
    event_type = str(payload.get("event_type", "")).lower().strip()
    if side in {"buy", "sell"}:
        return True
    if event_type in {"trade", "swap_out_aggregated", "swap_in_aggregated"}:
        return True
    return False


def _normalize_tax_event_category(value: str) -> str | None:
    raw = str(value or "").strip().upper()
    if raw in {"PRIVATE_SO", "PRIVATE", "SO", "INCOME_SO"}:
        return "PRIVATE_SO"
    if raw in {"BUSINESS", "GEWERBE", "ANLAGE_G", "EUER"}:
        return "BUSINESS"
    if raw in {"EXCLUDED", "EXCLUDE", "IGNORE", "IGNORED", "AUSSCHLUSS"}:
        return "EXCLUDED"
    return None


def _load_tax_event_overrides() -> dict[str, dict[str, str]]:
    row = STORE.get_setting("runtime.tax_event_overrides")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for event_id_raw, payload in raw.items():
        event_id = str(event_id_raw).strip()
        if not event_id or not isinstance(payload, dict):
            continue
        category = _normalize_tax_event_category(str(payload.get("tax_category", "")))
        if category is None:
            continue
        result[event_id] = {
            "tax_category": category,
            "reason_code": str(payload.get("reason_code", "")),
            "reason_label": str(payload.get("reason_label", "")),
            "note": str(payload.get("note", "")),
            "updated_at_utc": str(payload.get("updated_at_utc", "")),
        }
    return result


def _load_event_comments() -> dict[str, dict[str, str]]:
    row = STORE.get_setting("runtime.event_comments")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for event_id_raw, payload in raw.items():
        event_id = str(event_id_raw).strip()
        if not event_id or not isinstance(payload, dict):
            continue
        comment = str(payload.get("comment", "")).strip()
        if not comment:
            continue
        result[event_id] = {
            "source_event_id": event_id,
            "comment": comment,
            "reason_code": str(payload.get("reason_code", "")).strip(),
            "updated_at_utc": str(payload.get("updated_at_utc", "")).strip(),
        }
    return result


def _load_review_actions() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting("runtime.review_actions")
    empty: dict[str, dict[str, Any]] = {"timezone_corrections": {}, "merges": {}, "splits": {}}
    if row is None:
        return empty
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return empty
    if not isinstance(raw, dict):
        return empty
    result: dict[str, dict[str, Any]] = {"timezone_corrections": {}, "merges": {}, "splits": {}}
    for section in result:
        section_payload = raw.get(section, {})
        if isinstance(section_payload, dict):
            result[section] = section_payload
    return result


def _load_balance_adjustment_candidates() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting("runtime.balance_adjustment_candidates")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for candidate_id_raw, payload in raw.items():
        candidate_id = str(candidate_id_raw).strip()
        if not candidate_id or not isinstance(payload, dict):
            continue
        entry = dict(payload)
        entry["candidate_id"] = candidate_id
        entry["tax_effective"] = False
        result[candidate_id] = entry
    return result


def _save_balance_adjustment_candidates(candidates: dict[str, dict[str, Any]]) -> None:
    normalized: dict[str, dict[str, Any]] = {}
    for candidate_id_raw, payload in candidates.items():
        candidate_id = str(candidate_id_raw).strip()
        if not candidate_id or not isinstance(payload, dict):
            continue
        entry = dict(payload)
        entry["candidate_id"] = candidate_id
        entry["tax_effective"] = False
        normalized[candidate_id] = entry
    put_admin_setting("runtime.balance_adjustment_candidates", normalized, is_secret=False)


def _save_review_actions(actions: dict[str, dict[str, Any]]) -> None:
    normalized = {
        "timezone_corrections": actions.get("timezone_corrections", {}),
        "merges": actions.get("merges", {}),
        "splits": actions.get("splits", {}),
    }
    put_admin_setting("runtime.review_actions", normalized, is_secret=False)


def _normalize_review_timestamp(value: str) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        normalized = raw.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat()


def _normalize_review_reason(value: str, fallback: str) -> str:
    reason = str(value or "").strip()
    if reason in REVIEW_ACTION_REASON_CATALOG:
        return reason
    return fallback


def _stable_action_suffix(values: list[str]) -> str:
    import hashlib

    joined = "|".join(values)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def _load_issue_overrides() -> dict[str, dict[str, str]]:
    row = STORE.get_setting("runtime.issue_status_overrides")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for issue_id_raw, payload in raw.items():
        issue_id = str(issue_id_raw).strip()
        if not issue_id or not isinstance(payload, dict):
            continue
        status = _normalize_issue_status(str(payload.get("status", "")))
        if status is None:
            continue
        result[issue_id] = {
            "status": status,
            "note": str(payload.get("note", "")),
            "updated_at_utc": str(payload.get("updated_at_utc", "")),
        }
    return result


def _safe_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _load_closed_tax_years() -> set[int]:
    row = STORE.get_setting("runtime.review.closed_tax_years")
    if row is None:
        return set()
    try:
        raw = json.loads(str(row.get("value_json", "[]")))
    except Exception:
        return set()
    values = raw.get("years", []) if isinstance(raw, dict) else raw
    if not isinstance(values, list):
        return set()
    years: set[int] = set()
    for value in values:
        year = _safe_int(value)
        if year is not None:
            years.add(year)
    return years


def _load_unresolved_fx_issues() -> list[dict[str, str]]:
    row = STORE.get_setting("runtime.fx.unresolved_events")
    if row is None:
        return []
    try:
        raw = json.loads(str(row.get("value_json", "[]")))
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    result: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        event_id = str(item.get("source_event_id", "")).strip()
        rate_date = str(item.get("rate_date", "")).strip()
        reason = str(item.get("reason", "")).strip()
        if not event_id:
            continue
        result.append(
            {
                "source_event_id": event_id,
                "rate_date": rate_date,
                "reason": reason or "unknown",
            }
        )
    return result


def _normalize_issue_status(value: str) -> str | None:
    raw = str(value or "").strip().lower()
    if raw == "won_t_fix":
        raw = "wont_fix"
    if raw in {"open", "in_review", "resolved", "wont_fix"}:
        return raw
    return None
