from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tax_engine.admin import put_admin_setting
from tax_engine.ingestion import write_audit
from tax_engine.ingestion.store import STORE
from tax_engine.queue import get_processing_job
from tax_engine.reconciliation import (
    AutoMatchRequest,
    ManualMatchRequest,
    auto_match_and_persist,
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
    note: str | None = Field(default=None, max_length=500)


class TaxEventOverrideDeleteRequest(BaseModel):
    source_event_id: str = Field(min_length=8, max_length=200)


router = APIRouter()


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")

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
    open_issues = [item for item in issues if str(item.get("status", "")).lower() in open_statuses]
    open_high_issues = [item for item in open_issues if str(item.get("severity", "")).lower() == "high"]
    unmatched_outbound = unmatched.get("unmatched_outbound_ids", [])
    unmatched_inbound = unmatched.get("unmatched_inbound_ids", [])

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
            "issues_high_open": len(open_high_issues),
            "unmatched_outbound": len(unmatched_outbound),
            "unmatched_inbound": len(unmatched_inbound),
            "unmatched_total": unmatched_total,
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


@router.post("/api/v1/tax/event-override/upsert", response_model=StandardResponse, tags=["tax"])
def tax_event_override_upsert(payload: TaxEventOverrideUpsertRequest) -> StandardResponse:
    trace_id = str(uuid4())
    category = _normalize_tax_event_category(payload.tax_category)
    if category is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_tax_category", "message": "tax_category muss PRIVATE_SO oder BUSINESS sein"}],
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
    entry = {
        "tax_category": category,
        "note": (payload.note or "").strip(),
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




def _build_issue_inbox() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    overrides = _load_issue_overrides()
    raw_events = STORE.list_raw_events()

    # 1) Missing price issues for trade-like events.
    for event in raw_events:
        event_id = str(event.get("unique_event_id", ""))
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if not _is_trade_like(payload):
            continue
        if _safe_decimal(payload.get("price_eur", payload.get("price", "0"))) > 0:
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

    issues.sort(key=lambda item: (item.get("status") != "open", item.get("severity"), item.get("created_hint_utc")))
    return issues


def _build_issue_row(
    issue_id: str,
    issue_type: str,
    severity: str,
    title: str,
    detail: str,
    source_event_id: str,
    payload: dict[str, Any],
    overrides: dict[str, dict[str, str]],
) -> dict[str, Any]:
    override = overrides.get(issue_id, {})
    return {
        "issue_id": issue_id,
        "type": issue_type,
        "severity": severity,
        "status": str(override.get("status", "open")),
        "title": title,
        "detail": detail,
        "source_event_id": source_event_id,
        "asset": str(payload.get("asset", "")),
        "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
        "source": str(payload.get("source", "")),
        "note": str(override.get("note", "")),
        "updated_at_utc": str(override.get("updated_at_utc", "")),
        "created_hint_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
    }


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
            "note": str(payload.get("note", "")),
            "updated_at_utc": str(payload.get("updated_at_utc", "")),
        }
    return result


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
