from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from tax_engine.api.reporting import (
    _PDF_ROWS_PER_FILE,
)
from tax_engine.api.reporting import (
    build_csv_from_rows as _build_csv_from_rows,
)
from tax_engine.api.reporting import (
    build_export_rows as _build_export_rows,
)
from tax_engine.api.reporting import (
    build_pdf_from_rows as _build_pdf_from_rows,
)
from tax_engine.api.reporting import (
    build_report_file_index as _build_report_file_index,
)
from tax_engine.api.review import _build_issue_inbox
from tax_engine.core.derivatives import process_derivatives_for_year
from tax_engine.core.processor import process_events_for_year
from tax_engine.core.tax_domains import build_tax_domain_summary
from tax_engine.ingestion import write_audit
from tax_engine.ingestion.store import STORE
from tax_engine.queue import (
    ProcessRunRequest,
    WorkerRunNextRequest,
    apply_tax_event_overrides,
    create_processing_job,
    get_processing_job,
    run_next_queued_job,
)
from tax_engine.reconciliation import list_unmatched_transfers
from tax_engine.rulesets import build_default_registry


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class ReportSnapshotCreateRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)


class ProcessCompareRulesetsRequest(BaseModel):
    job_id: str = Field(min_length=1, max_length=200)
    compare_ruleset_id: str = Field(min_length=1, max_length=80)
    compare_ruleset_version: str | None = Field(default=None, min_length=1, max_length=20)


class ProcessPreflightRequest(BaseModel):
    tax_year: int = Field(ge=2020, le=2100)
    ruleset_id: str = Field(min_length=1, max_length=80)
    ruleset_version: str | None = Field(default=None, min_length=1, max_length=20)
    config: dict[str, Any] = Field(default_factory=dict)
    time_window_seconds: int = Field(default=600, ge=1, le=86400)
    amount_tolerance_ratio: float = Field(default=0.02, ge=0, le=1)
    min_confidence: float = Field(default=0.75, ge=0, le=1)


router = APIRouter()


def _extract_year(ts_raw: str) -> int | None:
    value = str(ts_raw).strip()
    if len(value) < 4:
        return None
    candidate = value[:4]
    if not candidate.isdigit():
        return None
    year = int(candidate)
    if year < 2009 or year > 2100:
        return None
    return year


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _preflight_needs_valuation(payload: dict[str, Any]) -> bool:
    event_type = str(payload.get("event_type") or "").lower()
    side = str(payload.get("side") or "").lower()
    if any(token in event_type for token in ("transfer", "deposit", "withdraw", "fee")):
        return False
    if side not in {"buy", "sell", "in", "out"}:
        return False
    if any(token in event_type for token in ("reward", "mining", "staking", "income", "claim", "airdrop")):
        return True
    if any(token in event_type for token in ("trade", "swap", "buy", "sell", "convert")):
        return True
    return str(payload.get("price") or payload.get("price_eur") or payload.get("value_usd") or payload.get("value_eur") or "").strip() != ""


def _preflight_has_valuation(payload: dict[str, Any]) -> bool:
    for key in ("price_eur", "value_eur", "amount_eur", "income_eur", "proceeds_eur", "cost_basis_eur"):
        if _safe_decimal(payload.get(key)) > 0:
            return True
    if _safe_decimal(payload.get("value_usd")) > 0 or _safe_decimal(payload.get("amount_usd")) > 0:
        return True
    if _safe_decimal(payload.get("price_usd")) > 0:
        return True
    quote = str(payload.get("quote_asset") or payload.get("fee_asset") or "").upper()
    if quote in {"USDT", "USDC", "BUSD", "FDUSD", "DAI", "USD"} and _safe_decimal(payload.get("price")) > 0:
        return True
    return False


def _preflight_action(
    label: str,
    target_step: str,
    target_review_tab: str | None = None,
    target_element_id: str | None = None,
    issue_search: str | None = None,
    issue_status: str | None = None,
    transfer_status: str | None = None,
) -> dict[str, str]:
    action: dict[str, str] = {
        "label": label,
        "target_step": target_step,
    }
    if target_review_tab:
        action["target_review_tab"] = target_review_tab
    if target_element_id:
        action["target_element_id"] = target_element_id
    if issue_search is not None:
        action["issue_search"] = issue_search
    if issue_status is not None:
        action["issue_status"] = issue_status
    if transfer_status is not None:
        action["transfer_status"] = transfer_status
    return action


@router.get("/api/v1/process/options", response_model=StandardResponse, tags=["process"])
def process_options() -> StandardResponse:
    trace_id = str(uuid4())
    registry = build_default_registry()
    rulesets = [item.to_dict() for item in registry.list_rulesets(include_pending=True)]
    years = sorted(
        {
            year
            for item in registry.list_rulesets(include_pending=True)
            for year in range(item.valid_from.year, item.valid_to.year + 1)
            if 2020 <= year <= 2100
        }
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "tax_years": years,
            "default_tax_year": max(years) if years else 2026,
            "rulesets": rulesets,
            "tax_methods": [
                {
                    "id": "fifo",
                    "label": "FIFO",
                    "description": "First-in-first-out als Projektstandard fuer deutsche Krypto-Berechnung.",
                    "default": True,
                }
            ],
            "depot_modes": [
                {"id": "global", "label": "Global FIFO", "default": True},
                {"id": "depot_separated", "label": "Depot-getrennte FIFO-Pools", "default": False},
            ],
            "validation_flags": [
                {"id": "short_sell_guard", "label": "Short-Sell Guard", "default": True},
                {"id": "transfer_check", "label": "Transfercheck", "default": True},
                {"id": "holding_period_check", "label": "Haltefristpruefung", "default": True},
            ],
            "profiles": [
                {"id": "de_private_standard", "label": "DE Privat Standard", "tax_method": "fifo", "depot_mode": "global"},
                {
                    "id": "de_trading_derivatives",
                    "label": "DE Trading + Derivate",
                    "tax_method": "fifo",
                    "depot_mode": "global",
                },
                {
                    "id": "de_mining_staking",
                    "label": "DE Mining/Staking",
                    "tax_method": "fifo",
                    "depot_mode": "depot_separated",
                },
            ],
        },
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/process/preflight", response_model=StandardResponse, tags=["process"])
def process_preflight(payload: ProcessPreflightRequest) -> StandardResponse:
    trace_id = str(uuid4())
    registry = build_default_registry()
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    try:
        resolved_ruleset, ruleset_warnings = registry.resolve_for_year(
            tax_year=payload.tax_year,
            ruleset_id=payload.ruleset_id,
            ruleset_version=payload.ruleset_version,
        )
        warnings.extend(ruleset_warnings)
    except ValueError as exc:
        resolved_ruleset = None
        blockers.append(
            {
                "code": "ruleset_not_resolvable",
                "message": str(exc),
                "action": _preflight_action(
                    "Ruleset-Auswahl prüfen",
                    target_step="3",
                    target_element_id="rulesetId",
                ),
            }
        )

    raw_events = STORE.list_raw_events()
    year_events = []
    unresolved_valuation_events = 0
    unclassified_events = 0
    for row in raw_events:
        item = row.get("payload", {})
        if not isinstance(item, dict):
            continue
        ts_raw = str(item.get("timestamp_utc") or item.get("timestamp") or "")
        if _extract_year(ts_raw) != payload.tax_year:
            continue
        year_events.append(row)
        event_type = str(item.get("event_type") or "").strip().lower()
        if not event_type or event_type == "unknown":
            unclassified_events += 1
        if _preflight_needs_valuation(item) and not _preflight_has_valuation(item):
            unresolved_valuation_events += 1

    if not raw_events:
        blockers.append(
            {
                "code": "no_import_data",
                "message": "Keine Importdaten vorhanden.",
                "action": _preflight_action(
                    "Importe öffnen",
                    target_step="1",
                    target_element_id="integrationHub",
                ),
            }
        )
    elif not year_events:
        blockers.append(
            {
                "code": "tax_year_no_events",
                "message": f"Keine Events fuer Steuerjahr {payload.tax_year} vorhanden.",
                "action": _preflight_action(
                    "Import-Zeitraum prüfen",
                    target_step="1",
                    target_element_id="importActivity",
                ),
            }
        )

    issues = _build_issue_inbox()
    open_high_issues = [
        item
        for item in issues
        if str(item.get("status", "")).lower() in {"open", "in_review"}
        and str(item.get("severity", "")).lower() == "high"
    ]
    if open_high_issues:
        blockers.append(
            {
                "code": "high_severity_issues_open",
                "message": f"{len(open_high_issues)} High-Severity Issues sind offen.",
                "action": _preflight_action(
                    "High-Issues bearbeiten",
                    target_step="4",
                    target_review_tab="transfers",
                    target_element_id="issuesTable",
                    issue_search="high",
                    issue_status="",
                ),
            }
        )

    unmatched = list_unmatched_transfers(
        time_window_seconds=payload.time_window_seconds,
        amount_tolerance_ratio=payload.amount_tolerance_ratio,
        min_confidence=payload.min_confidence,
    )
    unmatched_total = len(unmatched.get("unmatched_outbound_ids", [])) + len(unmatched.get("unmatched_inbound_ids", []))
    if unmatched_total > 0:
        blockers.append(
            {
                "code": "unmatched_transfers_open",
                "message": f"{unmatched_total} unmatched Transfers sind offen.",
                "action": _preflight_action(
                    "Transfers abgleichen",
                    target_step="4",
                    target_review_tab="transfers",
                    target_element_id="reviewTransferTable",
                    transfer_status="unmatched",
                ),
            }
        )

    if unresolved_valuation_events > 0:
        warnings.append(
            {
                "code": "valuation_coverage_incomplete",
                "message": f"{unresolved_valuation_events} Events im Steuerjahr haben keine klare Bewertung.",
                "action": _preflight_action(
                    "Bewertungs-Issues prüfen",
                    target_step="4",
                    target_review_tab="transfers",
                    target_element_id="issuesTable",
                    issue_search="valuation",
                    issue_status="",
                ),
            }
        )
    if unclassified_events > 0:
        warnings.append(
            {
                "code": "unclassified_events_present",
                "message": f"{unclassified_events} Events im Steuerjahr sind unklassifiziert.",
                "action": _preflight_action(
                    "Klassifizierung prüfen",
                    target_step="4",
                    target_review_tab="transfers",
                    target_element_id="issuesTable",
                    issue_search="unknown",
                    issue_status="",
                ),
            }
        )

    allow_run = len(blockers) == 0
    data = {
        "allow_run": allow_run,
        "tax_year": payload.tax_year,
        "ruleset": resolved_ruleset.to_dict() if resolved_ruleset is not None else None,
        "counts": {
            "raw_events_total": len(raw_events),
            "tax_year_events": len(year_events),
            "issues_total": len(issues),
            "high_severity_open": len(open_high_issues),
            "unmatched_transfers": unmatched_total,
            "unresolved_valuation_events": unresolved_valuation_events,
            "unclassified_events": unclassified_events,
        },
        "blockers": blockers,
        "warnings": warnings,
    }
    write_audit(
        trace_id=trace_id,
        action="process.preflight",
        payload={
            "tax_year": payload.tax_year,
            "allow_run": allow_run,
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=warnings)


@router.post("/api/v1/process/run", response_model=StandardResponse, tags=["process"])
def process_run(payload: ProcessRunRequest) -> StandardResponse:
    trace_id = str(uuid4())
    registry = build_default_registry()
    try:
        resolved_ruleset, ruleset_warnings = registry.resolve_for_year(
            tax_year=payload.tax_year,
            ruleset_id=payload.ruleset_id,
            ruleset_version=payload.ruleset_version,
        )
    except ValueError as exc:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "ruleset_not_resolvable", "message": str(exc)}],
            warnings=[],
        )
    job = create_processing_job(payload)
    warnings: list[dict[str, str]] = list(ruleset_warnings)
    if resolved_ruleset.ruleset_id != payload.ruleset_id or (
        payload.ruleset_version is not None and resolved_ruleset.ruleset_version != payload.ruleset_version
    ):
        warnings.append(
            {
                "code": "ruleset_resolved",
                "message": (
                    f"Ruleset-Eingabe wurde auf {resolved_ruleset.ruleset_id} "
                    f"v{resolved_ruleset.ruleset_version} normalisiert."
                ),
            }
        )
    events = STORE.list_raw_events()
    year_count = 0
    for row in events:
        item = row.get("payload", {})
        if not isinstance(item, dict):
            continue
        ts_raw = str(item.get("timestamp_utc") or item.get("timestamp") or "")
        year = _extract_year(ts_raw)
        if year == payload.tax_year:
            year_count += 1
    if year_count == 0:
        warnings.append(
            {
                "code": "tax_year_no_events",
                "message": (
                    f"Keine Events mit Jahr {payload.tax_year} gefunden. "
                    "Bitte Tax Year oder Importdaten prüfen."
                ),
            }
        )
    write_audit(
        trace_id=trace_id,
        action="process.run",
        payload={
            "job_id": job["job_id"],
            "tax_year": payload.tax_year,
            "ruleset_id": payload.ruleset_id,
            "resolved_ruleset_id": job.get("ruleset_id"),
            "resolved_ruleset_version": job.get("ruleset_version"),
            "dry_run": payload.dry_run,
            "tax_year_event_count": year_count,
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=job, errors=[], warnings=warnings)


@router.get("/api/v1/process/status/{job_id}", response_model=StandardResponse, tags=["process"])
def process_status(job_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(job_id)
    if job is None:
        write_audit(
            trace_id=trace_id,
            action="process.status",
            payload={"job_id": job_id, "found": False},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )

    write_audit(
        trace_id=trace_id,
        action="process.status",
        payload={"job_id": job_id, "found": True, "status": job["status"]},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=job, errors=[], warnings=[])


@router.get("/api/v1/process/latest", response_model=StandardResponse, tags=["process"])
def process_latest() -> StandardResponse:
    trace_id = str(uuid4())
    job = STORE.get_latest_processing_job()
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="success",
            data={"job": None},
            errors=[],
            warnings=[{"code": "no_processing_jobs", "message": "Noch kein Processing-Job vorhanden."}],
        )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"job": job},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/process/jobs", response_model=StandardResponse, tags=["process"])
def process_jobs(status: str | None = None, limit: int = 50, offset: int = 0) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = max(1, min(int(limit), 5000))
    safe_offset = max(0, int(offset))
    rows = STORE.list_processing_jobs(status=status, limit=safe_limit, offset=safe_offset)
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "offset": safe_offset, "limit": safe_limit, "rows": rows},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/report/export", response_model=None)
def report_export(
    job_id: str,
    scope: str = "all",
    fmt: str = "json",
    part: int = 1,
) -> StandardResponse | StreamingResponse:
    trace_id = str(uuid4())
    scope_normalized = str(scope or "all").strip().lower()
    fmt_normalized = str(fmt or "json").strip().lower()
    include_derivatives = scope_normalized in {"all", "derivatives"}
    include_tax = scope_normalized in {"all", "tax"}

    if scope_normalized not in {"all", "tax", "derivatives"}:
        write_audit(
            trace_id=trace_id,
            action="report.export",
            payload={"job_id": job_id, "scope": scope_normalized, "format": fmt_normalized, "error": "invalid_scope"},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_scope", "message": "scope muss all|tax|derivatives sein."}],
            warnings=[],
        )

    if fmt_normalized not in {"json", "csv", "pdf"}:
        write_audit(
            trace_id=trace_id,
            action="report.export",
            payload={"job_id": job_id, "scope": scope_normalized, "format": fmt_normalized, "error": "invalid_format"},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_format", "message": "fmt muss json|csv|pdf sein."}],
            warnings=[],
        )

    job = get_processing_job(job_id)
    if job is None:
        write_audit(
            trace_id=trace_id,
            action="report.export",
            payload={"job_id": job_id, "found": False},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )

    tax_lines = STORE.get_tax_lines(job_id) if include_tax else []
    derivative_lines = STORE.get_derivative_lines(job_id) if include_derivatives else []
    integrity = STORE.get_report_integrity(job_id)
    export_rows = _build_export_rows(
        job,
        tax_lines,
        derivative_lines,
        include_derivatives=include_derivatives,
        integrity=integrity,
    )
    total_parts = max(1, (len(export_rows) + _PDF_ROWS_PER_FILE - 1) // _PDF_ROWS_PER_FILE)
    safe_part = max(1, int(part))
    if fmt_normalized == "pdf" and safe_part > total_parts:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"job_id": job_id, "scope": scope_normalized, "part_count": total_parts},
            errors=[{"code": "report_part_not_found", "message": f"PDF-Teil {safe_part} existiert nicht."}],
            warnings=[],
        )
    write_audit(
        trace_id=trace_id,
        action="report.export",
        payload={
            "job_id": job_id,
            "scope": scope_normalized,
            "format": fmt_normalized,
            "part": safe_part,
            "tax_lines": len(tax_lines),
            "derivative_lines": len(derivative_lines),
        },
    )

    if fmt_normalized == "csv":
        csv_content = _build_csv_from_rows(export_rows)
        filename = f"steuerreport_{job_id}.csv"
        headers = {
            "Content-Disposition": f'attachment; filename=\"{filename}\"',
        }
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv; charset=utf-8",
            headers=headers,
        )

    if fmt_normalized == "pdf":
        start = (safe_part - 1) * _PDF_ROWS_PER_FILE
        selected_rows = export_rows[start : start + _PDF_ROWS_PER_FILE]
        pdf_content = _build_pdf_from_rows(
            job=job,
            rows=selected_rows,
            integrity=integrity,
            scope=scope_normalized,
            part=safe_part,
            part_count=total_parts,
        )
        filename = f"steuerreport_{job_id}_{scope_normalized}_teil_{safe_part}_von_{total_parts}.pdf"
        headers = {
            "Content-Disposition": f'attachment; filename=\"{filename}\"',
        }
        return StreamingResponse(
            iter([pdf_content]),
            media_type="application/pdf",
            headers=headers,
        )

    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "job_id": job_id,
            "scope": scope_normalized,
            "part_count": total_parts,
            "job": {
                "tax_year": job.get("tax_year"),
                "ruleset_id": job.get("ruleset_id"),
                "ruleset_version": job.get("ruleset_version"),
            },
            "integrity": integrity,
            "rows": export_rows,
        },
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/report/files/{run_id}", response_model=StandardResponse, tags=["report"])
def report_files(run_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(run_id)
    if job is None:
        write_audit(
            trace_id=trace_id,
            action="report.files",
            payload={"run_id": run_id, "found": False},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Run not found: {run_id}"}],
            warnings=[],
        )

    tax_lines = STORE.get_tax_lines(run_id)
    derivative_lines = STORE.get_derivative_lines(run_id)
    files = _build_report_file_index(
        job=job,
        tax_line_count=len(tax_lines),
        derivative_line_count=len(derivative_lines),
    )
    write_audit(
        trace_id=trace_id,
        action="report.files",
        payload={
            "run_id": run_id,
            "file_count": len(files),
            "tax_line_count": len(tax_lines),
            "derivative_line_count": len(derivative_lines),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "run_id": run_id,
            "status": job.get("status"),
            "tax_year": job.get("tax_year"),
            "ruleset_id": job.get("ruleset_id"),
            "ruleset_version": job.get("ruleset_version"),
            "tax_line_count": len(tax_lines),
            "derivative_line_count": len(derivative_lines),
            "files": files,
        },
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/compliance/classification/{run_id}", response_model=StandardResponse, tags=["compliance"])
def compliance_classification(run_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    run = get_processing_job(run_id)
    if run is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "run_not_found", "message": f"Lauf nicht gefunden: {run_id}"}],
            warnings=[],
        )

    tax_year = int(run["tax_year"])
    events = STORE.list_raw_events()
    year_events: list[dict[str, Any]] = []
    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if _extract_year(ts_raw) == tax_year:
            year_events.append(payload)

    ruleset_id = str(run.get("ruleset_id", "DE-2026-v1.0"))
    run_ruleset_version = str(run.get("ruleset_version") or "").strip()
    ruleset_version = run_ruleset_version if run_ruleset_version else None
    registry = build_default_registry()
    try:
        ruleset = registry.get(ruleset_id, ruleset_version)
    except Exception:
        ruleset = registry.get("DE-2026-v1.0", "1.0")

    trading_like = 0
    transfer_like = 0
    reward_events = 0
    mining_events = 0
    reward_value = Decimal("0")
    trading_days: set[str] = set()

    def _is_reward_like(payload: dict[str, Any]) -> bool:
        text = " ".join(
            str(payload.get(key, "")).lower()
            for key in ("event_type", "type", "label", "comment", "description", "source", "tag")
        )
        event_type = str(payload.get("event_type", "")).lower().strip()
        return event_type in {
            "mining_reward",
            "staking_reward",
            "asset_dividend",
            "interest",
            "reward_claim",
            "reward",
        } or any(token in text for token in ("reward", "staking", "mining", "claim", "dividend", "interest"))

    def _is_mining_like(payload: dict[str, Any]) -> bool:
        text = " ".join(
            str(payload.get(key, "")).lower()
            for key in ("event_type", "type", "source", "comment", "description", "tag")
        )
        source = str(payload.get("source", "")).lower().strip()
        asset = str(payload.get("asset", "")).lower().strip()
        return (
            "mining" in text
            or source == "heliumgeek"
            or asset in {"hnt", "iot", "mobile", "myst"}
            or any(token in text for token in ("hotspot", "solana", "vehnt"))
        )

    for payload in year_events:
        event_type = str(payload.get("event_type", "")).lower().strip()
        side = str(payload.get("side", "")).lower().strip()
        if event_type in {"buy", "sell", "trade", "swap"} or side in {"buy", "sell"}:
            trading_like += 1
        if event_type in {"transfer_in", "transfer_out", "airdrop", "fee", "staking"} or side in {"in", "out"}:
            transfer_like += 1
        if _is_reward_like(payload):
            reward_events += 1
            reward_value += abs(_safe_decimal(payload.get("value_eur")))
        if _is_mining_like(payload):
            mining_events += 1

        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        day = ts_raw[:10] if len(ts_raw) >= 10 else ""
        if day:
            if event_type in {"buy", "sell", "trade", "swap"} or side in {"buy", "sell"}:
                trading_days.add(day)

    active_days = max(len(trading_days), 1)
    avg_trades_per_day = (Decimal(trading_like) / Decimal(active_days)) if active_days else Decimal("0")
    threshold_services = ruleset.other_services_exemption_limit if ruleset is not None else Decimal("256")

    high_frequency = trading_like >= 15000 or avg_trades_per_day >= Decimal("10")
    medium_frequency = trading_like >= 2000 or avg_trades_per_day >= Decimal("3")
    mining_exceeded = reward_events > 0 and reward_value >= threshold_services
    is_business = high_frequency or (mining_exceeded and mining_events > 0)
    level = "red" if high_frequency else ("yellow" if (medium_frequency or mining_exceeded) else "green")
    reasons: list[dict[str, Any]] = []
    if high_frequency:
        reasons.append(
            {
                "code": "high_frequency",
                "message": (
                    f"{trading_like} Trading-Events im Jahr {tax_year} "
                    f"({avg_trades_per_day:.2f}/Tag) deuten auf gewerbsmäßige Nutzung."
                ),
            }
        )
    if mining_exceeded:
        reasons.append(
            {
                "code": "mining_threshold",
                "message": (
                    f"Mining/Staking-Einnahmen {reward_value.to_eng_string()} EUR "
                    f"überschreiten die §22-Freigrenze {threshold_services.to_eng_string()} EUR."
                ),
            }
        )

    warnings: list[dict[str, str]] = []
    if level != "green":
        warnings.append(
            {
                "code": "commercial_risk",
                "message": "Prüfe den Status mit Steuerberater und ggf. Anlage G / Gewerbe-EÜR.",
            }
        )

    write_audit(
        trace_id=trace_id,
        action="compliance.classification",
        payload={
            "run_id": run_id,
            "level": level,
            "is_business": is_business,
            "trading_events": trading_like,
            "reward_events": reward_events,
            "mining_events": mining_events,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "run_id": run_id,
            "tax_year": tax_year,
            "is_commercial": is_business,
            "classification_level": level,
            "signals": {
                "trading_events": trading_like,
                "transfer_events": transfer_like,
                "reward_events": reward_events,
                "mining_events": mining_events,
                "active_trading_days": len(trading_days),
                "avg_trades_per_active_day": str(avg_trades_per_day),
                "reward_value_eur": reward_value.to_eng_string(),
            },
            "ruleset": {
                "ruleset_id": ruleset.ruleset_id,
                "ruleset_version": ruleset.ruleset_version,
                "jurisdiction": ruleset.jurisdiction,
                "exemption_limit_so": ruleset.exemption_limit_so.to_eng_string(),
                "other_services_exemption_limit": ruleset.other_services_exemption_limit.to_eng_string(),
                "holding_period_months": ruleset.holding_period_months,
            },
            "reasons": reasons,
        },
        errors=[],
        warnings=warnings,
    )


@router.get("/api/v1/integrity/report/{run_id}", response_model=StandardResponse, tags=["integrity"])
def integrity_report(run_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    info = STORE.get_report_integrity(run_id)
    if info is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "report_integrity_not_found", "message": f"No integration data for run {run_id}"}],
            warnings=[],
        )
    return StandardResponse(trace_id=trace_id, status="success", data=info, errors=[], warnings=[])


@router.post(
    "/api/v1/snapshots/create/{run_id}",
    response_model=StandardResponse,
    tags=["integrity"],
)
def create_snapshot(run_id: str, payload: ReportSnapshotCreateRequest) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(run_id)
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Run not found: {run_id}"}],
            warnings=[],
        )
    result_summary = job.get("result_summary")
    if result_summary is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "result_summary_missing", "message": "Run has no persisted result_summary"}],
            warnings=[],
        )
    snapshot_id = STORE.create_report_snapshot(
        job_id=run_id,
        payload_json=json.dumps(result_summary, sort_keys=True, separators=(",", ":")),
        summary_json=json.dumps(result_summary.get("tax_domain_summary", {}), sort_keys=True, separators=(",", ":")),
        notes=payload.notes,
    )
    snapshot = STORE.get_report_snapshot(snapshot_id)
    if snapshot is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "snapshot_creation_failed", "message": "Snapshot konnte nicht gespeichert werden"}],
            warnings=[],
        )
    return StandardResponse(trace_id=trace_id, status="success", data=snapshot, errors=[], warnings=[])


@router.get("/api/v1/snapshots/{snapshot_id}", response_model=StandardResponse, tags=["integrity"])
def get_snapshot(snapshot_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    snapshot = STORE.get_report_snapshot(snapshot_id)
    if snapshot is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "snapshot_not_found", "message": f"Snapshot not found: {snapshot_id}"}],
            warnings=[],
        )
    try:
        payload = json.loads(snapshot.get("payload_json", "{}"))
    except Exception:
        payload = {}
    try:
        summary = json.loads(snapshot.get("summary_json", "{}"))
    except Exception:
        summary = {}
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "snapshot_id": snapshot["snapshot_id"],
            "job_id": snapshot["job_id"],
            "created_at_utc": snapshot["created_at_utc"],
            "notes": snapshot.get("notes"),
            "payload": payload,
            "summary": summary,
        },
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/integrity/event/{unique_event_id}", response_model=StandardResponse, tags=["integrity"])
def integrity_event(unique_event_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    raw_event = STORE.get_raw_event(unique_event_id)
    if raw_event is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "event_not_found", "message": f"Raw event not found: {unique_event_id}"}],
            warnings=[],
        )
    jobs = STORE.list_jobs_using_event(unique_event_id=unique_event_id)
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"event": raw_event, "jobs": jobs},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/process/compare-rulesets", response_model=StandardResponse, tags=["process"])
def process_compare_rulesets(
    job_id: str,
    compare_ruleset_id: str,
    compare_ruleset_version: str | None = None,
) -> StandardResponse:
    return _process_compare_rulesets_impl(
        job_id=job_id,
        compare_ruleset_id=compare_ruleset_id,
        compare_ruleset_version=compare_ruleset_version,
    )


@router.post("/api/v1/process/compare-rulesets", response_model=StandardResponse, tags=["process"])
def process_compare_rulesets_post(payload: ProcessCompareRulesetsRequest) -> StandardResponse:
    return _process_compare_rulesets_impl(
        job_id=payload.job_id,
        compare_ruleset_id=payload.compare_ruleset_id,
        compare_ruleset_version=payload.compare_ruleset_version,
    )


def _process_compare_rulesets_impl(
    job_id: str,
    compare_ruleset_id: str,
    compare_ruleset_version: str | None = None,
) -> StandardResponse:
    trace_id = str(uuid4())
    base_job = get_processing_job(job_id)
    if base_job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Run not found: {job_id}"},
            ],
            warnings=[],
        )

    raw_events = STORE.list_raw_events()
    effective_events, override_count = apply_tax_event_overrides(raw_events)
    if not effective_events:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "no_effective_events", "message": "No effective events available for comparison"}],
            warnings=[],
        )

    tax_year = int(base_job["tax_year"])
    try:
        compare_result = process_events_for_year(
            raw_events=effective_events,
            tax_year=tax_year,
            ruleset_id=compare_ruleset_id,
            ruleset_version=compare_ruleset_version,
        )
        derivative_result = process_derivatives_for_year(raw_events=effective_events, tax_year=tax_year)
        compare_summary = build_tax_domain_summary(
            raw_events=effective_events,
            tax_lines=compare_result.get("tax_lines", []),
            derivative_lines=derivative_result.get("lines", []),
            tax_year=tax_year,
            ruleset_id=compare_ruleset_id,
        )
    except Exception as exc:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "compare_failed", "message": str(exc)}],
            warnings=[],
        )

    base_summary = {}
    base_tax_summary = {}
    if base_job.get("result_summary") is not None:
        base_summary = base_job["result_summary"]
        base_tax_summary = base_summary.get("tax_domain_summary", {})
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "job_id": job_id,
            "tax_year": tax_year,
            "compare_ruleset_id": compare_ruleset_id,
            "compare_ruleset_version": compare_ruleset_version,
            "base": {
                "ruleset_id": base_job.get("ruleset_id"),
                "ruleset_version": base_job.get("ruleset_version"),
                "result_summary": base_summary,
                "tax_domain_summary": base_tax_summary,
            },
            "comparison": {
                "ruleset_id": compare_ruleset_id,
                "ruleset_version": compare_ruleset_version,
                "result_summary": compare_result,
                "tax_domain_summary": compare_summary,
                "tax_event_override_count": override_count,
            },
        },
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/process/tax-lines/{job_id}", response_model=StandardResponse, tags=["process"])
def process_tax_lines(job_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(job_id)
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )
    lines = STORE.get_tax_lines(job_id)
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"job_id": job_id, "count": len(lines), "lines": lines},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/process/tax-domain-summary/{job_id}", response_model=StandardResponse, tags=["process"])
def process_tax_domain_summary(job_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(job_id)
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )
    result_summary = job.get("result_summary")
    if not isinstance(result_summary, dict):
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "result_not_available", "message": "Job result summary not available"}],
            warnings=[],
        )
    tax_domain_summary = result_summary.get("tax_domain_summary")
    if not isinstance(tax_domain_summary, dict):
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "tax_domain_summary_missing", "message": "No tax domain summary in result"}],
            warnings=[],
        )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"job_id": job_id, "tax_domain_summary": tax_domain_summary},
        errors=[],
        warnings=[],
    )


@router.get(
    "/api/v1/audit/tax-line/{job_id}/{line_no}",
    response_model=StandardResponse,
    tags=["audit"],
)
def audit_tax_line(job_id: str, line_no: int) -> StandardResponse:
    trace_id = str(uuid4())
    if line_no <= 0:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_line_no", "message": "line_no muss > 0 sein"}],
            warnings=[],
        )

    job = get_processing_job(job_id)
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )

    tax_line = STORE.get_tax_line(job_id=job_id, line_no=line_no)
    if tax_line is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "tax_line_not_found", "message": f"Tax line not found: {job_id}#{line_no}"}],
            warnings=[],
        )

    source_event = STORE.get_raw_event(tax_line["source_event_id"])
    calculation_trace = {
        "formula": "gain_loss_eur = proceeds_eur - cost_basis_eur",
        "cost_basis_eur": tax_line["cost_basis_eur"],
        "proceeds_eur": tax_line["proceeds_eur"],
        "gain_loss_eur": tax_line["gain_loss_eur"],
        "holding_period_days": tax_line["hold_days"],
        "tax_status": tax_line["tax_status"],
    }
    write_audit(
        trace_id=trace_id,
        action="audit.tax_line",
        payload={
            "job_id": job_id,
            "line_no": line_no,
            "source_event_found": source_event is not None,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "job_id": job_id,
            "line_no": line_no,
            "tax_year": job["tax_year"],
            "ruleset_id": job["ruleset_id"],
            "tax_line": tax_line,
            "source_event": source_event,
            "calculation_trace": calculation_trace,
        },
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/process/derivative-lines/{job_id}", response_model=StandardResponse, tags=["process"])
def process_derivative_lines(job_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(job_id)
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )
    lines = STORE.get_derivative_lines(job_id)
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"job_id": job_id, "count": len(lines), "lines": lines},
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/process/worker/run-next", response_model=StandardResponse, tags=["process"])
def process_worker_run_next(payload: WorkerRunNextRequest) -> StandardResponse:
    trace_id = str(uuid4())
    processed = run_next_queued_job(simulate_fail=payload.simulate_fail)
    if processed is None:
        write_audit(
            trace_id=trace_id,
            action="process.worker.run_next",
            payload={"processed_job": False},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="success",
            data={},
            errors=[],
            warnings=[{"code": "no_queued_job", "message": "No queued job available"}],
        )

    write_audit(
        trace_id=trace_id,
        action="process.worker.run_next",
        payload={
            "processed_job": True,
            "job_id": processed["job_id"],
            "status": processed["status"],
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=processed, errors=[], warnings=[])
