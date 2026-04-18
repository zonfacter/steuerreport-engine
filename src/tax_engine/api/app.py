from __future__ import annotations

from base64 import b64decode
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tax_engine.connectors import (
    CexBalancesPreviewRequest,
    CexTransactionsPreviewRequest,
    CexVerifyRequest,
    fetch_cex_balance_preview,
    fetch_cex_transactions_preview,
    mask_api_key,
    verify_cex_credentials,
)
from tax_engine.ingestion import (
    ConfirmImportRequest,
    ConnectorParseRequest,
    DetectFormatRequest,
    NormalizePreviewRequest,
    UploadPreviewRequest,
    confirm_import,
    detect_format,
    list_connectors,
    normalize_connector_rows,
    normalize_preview,
    parse_upload_file,
    write_audit,
)
from tax_engine.ingestion.store import STORE
from tax_engine.queue import (
    ProcessRunRequest,
    WorkerRunNextRequest,
    create_processing_job,
    get_processing_job,
    run_next_queued_job,
)
from tax_engine.reconciliation import (
    AutoMatchRequest,
    ManualMatchRequest,
    auto_match_and_persist,
    list_unmatched_transfers,
    manual_match,
)


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


app = FastAPI(
    title="Steuerreport Engine API",
    version="0.1.0",
    description="Modulare, auditierbare Steuer-Engine API",
)

_UI_STATIC_DIR = Path(__file__).resolve().parents[1] / "ui" / "static"
app.mount("/ui/static", StaticFiles(directory=str(_UI_STATIC_DIR)), name="ui-static")


@app.get("/api/v1/health", response_model=StandardResponse, tags=["system"])
def health() -> StandardResponse:
    return StandardResponse(
        trace_id=str(uuid4()),
        status="success",
        data={
            "service": "steuerreport-engine",
            "uptime_state": "ok",
            "timestamp_utc": datetime.now(UTC).isoformat(),
        },
        errors=[],
        warnings=[],
    )


@app.get("/app", include_in_schema=False)
def web_app() -> FileResponse:
    return FileResponse(_UI_STATIC_DIR / "index.html")


@app.post("/api/v1/import/detect-format", response_model=StandardResponse, tags=["import"])
def import_detect_format(payload: DetectFormatRequest) -> StandardResponse:
    trace_id = str(uuid4())
    result = detect_format(payload.rows)
    write_audit(
        trace_id=trace_id,
        action="import.detect_format",
        payload={
            "source_name": payload.source_name,
            "row_count": len(payload.rows),
            "detected_locale": result["detected_locale"],
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@app.post("/api/v1/import/normalize-preview", response_model=StandardResponse, tags=["import"])
def import_normalize_preview(payload: NormalizePreviewRequest) -> StandardResponse:
    trace_id = str(uuid4())
    normalized_rows, warnings, errors = normalize_preview(
        rows=payload.rows,
        locale_hint=payload.locale_hint,
        numeric_fields=payload.numeric_fields,
        datetime_fields=payload.datetime_fields,
        subunit_fields=payload.subunit_fields,
    )
    status = "success" if not errors else "partial"
    write_audit(
        trace_id=trace_id,
        action="import.normalize_preview",
        payload={
            "source_name": payload.source_name,
            "row_count": len(payload.rows),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status=status,
        data={"normalized_rows": normalized_rows},
        errors=errors,
        warnings=warnings,
    )


@app.post("/api/v1/import/confirm", response_model=StandardResponse, tags=["import"])
def import_confirm(payload: ConfirmImportRequest) -> StandardResponse:
    trace_id = str(uuid4())
    result = confirm_import(source_name=payload.source_name, rows=payload.rows)
    write_audit(
        trace_id=trace_id,
        action="import.confirm",
        payload={
            "source_name": payload.source_name,
            "source_file_id": result["source_file_id"],
            "inserted_events": result["inserted_events"],
            "duplicate_events": result["duplicate_events"],
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@app.get("/api/v1/import/connectors", response_model=StandardResponse, tags=["import"])
def import_connectors() -> StandardResponse:
    trace_id = str(uuid4())
    connectors = list_connectors()
    write_audit(
        trace_id=trace_id,
        action="import.connectors",
        payload={"count": len(connectors)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"connectors": connectors, "count": len(connectors)},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/import/parse-preview", response_model=StandardResponse, tags=["import"])
def import_parse_preview(payload: ConnectorParseRequest) -> StandardResponse:
    trace_id = str(uuid4())
    normalized_rows, warnings, errors = normalize_connector_rows(
        connector_id=payload.connector_id,
        rows=payload.rows,
        max_rows=payload.max_rows,
    )
    status = "success" if not errors else "partial"
    write_audit(
        trace_id=trace_id,
        action="import.parse_preview",
        payload={
            "connector_id": payload.connector_id,
            "input_rows": len(payload.rows),
            "normalized_rows": len(normalized_rows),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status=status,
        data={
            "connector_id": payload.connector_id,
            "normalized_rows": normalized_rows,
            "count": len(normalized_rows),
        },
        errors=errors,
        warnings=warnings,
    )


@app.post("/api/v1/import/upload-preview", response_model=StandardResponse, tags=["import"])
def import_upload_preview(payload: UploadPreviewRequest) -> StandardResponse:
    trace_id = str(uuid4())
    if not payload.filename:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "missing_filename", "message": "Filename missing"}],
            warnings=[],
        )

    try:
        content = b64decode(payload.file_content_base64, validate=True)
    except Exception:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_base64", "message": "Dateiinhalt ist kein valides Base64"}],
            warnings=[],
        )

    try:
        rows, file_warnings = parse_upload_file(payload.filename, content)
    except ValueError as exc:
        write_audit(
            trace_id=trace_id,
            action="import.upload_preview",
            payload={
                "connector_id": payload.connector_id,
                "filename": payload.filename,
                "parse_error": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": str(exc), "message": "Upload konnte nicht geparst werden"}],
            warnings=[],
        )

    normalized_rows, map_warnings, errors = normalize_connector_rows(
        connector_id=payload.connector_id,
        rows=rows,
        max_rows=payload.max_rows,
    )
    warnings = [*file_warnings, *map_warnings]
    status = "success" if not errors else "partial"

    write_audit(
        trace_id=trace_id,
        action="import.upload_preview",
        payload={
            "connector_id": payload.connector_id,
            "filename": payload.filename,
            "input_rows": len(rows),
            "normalized_rows": len(normalized_rows),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
        },
    )

    return StandardResponse(
        trace_id=trace_id,
        status=status,
        data={
            "connector_id": payload.connector_id,
            "filename": payload.filename,
            "input_rows": len(rows),
            "count": len(normalized_rows),
            "normalized_rows": normalized_rows,
        },
        errors=errors,
        warnings=warnings,
    )


@app.post("/api/v1/connectors/cex/verify", response_model=StandardResponse, tags=["connectors"])
def connectors_cex_verify(payload: CexVerifyRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        result = verify_cex_credentials(
            connector_id=payload.connector_id,
            api_key=payload.api_key,
            api_secret=payload.api_secret,
            passphrase=payload.passphrase,
            timeout_seconds=payload.timeout_seconds,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="connectors.cex.verify",
            payload={
                "connector_id": payload.connector_id,
                "api_key_masked": mask_api_key(payload.api_key),
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_error", "message": str(exc)}],
            warnings=[],
        )

    status = "success" if result.get("ok") else "partial"
    write_audit(
        trace_id=trace_id,
        action="connectors.cex.verify",
        payload={
            "connector_id": payload.connector_id,
            "api_key_masked": mask_api_key(payload.api_key),
            "ok": bool(result.get("ok")),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status=status,
        data=result,
        errors=[],
        warnings=[],
    )


@app.post(
    "/api/v1/connectors/cex/balances-preview",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_cex_balances_preview(payload: CexBalancesPreviewRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        result = fetch_cex_balance_preview(
            connector_id=payload.connector_id,
            api_key=payload.api_key,
            api_secret=payload.api_secret,
            passphrase=payload.passphrase,
            timeout_seconds=payload.timeout_seconds,
            max_rows=payload.max_rows,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="connectors.cex.balances_preview",
            payload={
                "connector_id": payload.connector_id,
                "api_key_masked": mask_api_key(payload.api_key),
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_error", "message": str(exc)}],
            warnings=[],
        )

    write_audit(
        trace_id=trace_id,
        action="connectors.cex.balances_preview",
        payload={
            "connector_id": payload.connector_id,
            "api_key_masked": mask_api_key(payload.api_key),
            "ok": True,
            "rows": result.get("count", 0),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data=result,
        errors=[],
        warnings=[],
    )


@app.post(
    "/api/v1/connectors/cex/transactions-preview",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_cex_transactions_preview(payload: CexTransactionsPreviewRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        result = fetch_cex_transactions_preview(
            connector_id=payload.connector_id,
            api_key=payload.api_key,
            api_secret=payload.api_secret,
            passphrase=payload.passphrase,
            timeout_seconds=payload.timeout_seconds,
            max_rows=payload.max_rows,
            start_time_ms=payload.start_time_ms,
            end_time_ms=payload.end_time_ms,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="connectors.cex.transactions_preview",
            payload={
                "connector_id": payload.connector_id,
                "api_key_masked": mask_api_key(payload.api_key),
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_error", "message": str(exc)}],
            warnings=[],
        )

    write_audit(
        trace_id=trace_id,
        action="connectors.cex.transactions_preview",
        payload={
            "connector_id": payload.connector_id,
            "api_key_masked": mask_api_key(payload.api_key),
            "ok": True,
            "rows": result.get("count", 0),
        },
    )
    warnings = result.get("warnings", [])
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data=result,
        errors=[],
        warnings=warnings if isinstance(warnings, list) else [],
    )


@app.post("/api/v1/process/run", response_model=StandardResponse, tags=["process"])
def process_run(payload: ProcessRunRequest) -> StandardResponse:
    trace_id = str(uuid4())
    job = create_processing_job(payload)
    write_audit(
        trace_id=trace_id,
        action="process.run",
        payload={
            "job_id": job["job_id"],
            "tax_year": payload.tax_year,
            "ruleset_id": payload.ruleset_id,
            "dry_run": payload.dry_run,
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=job, errors=[], warnings=[])


@app.get("/api/v1/process/status/{job_id}", response_model=StandardResponse, tags=["process"])
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


@app.get("/api/v1/process/tax-lines/{job_id}", response_model=StandardResponse, tags=["process"])
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


@app.get("/api/v1/process/derivative-lines/{job_id}", response_model=StandardResponse, tags=["process"])
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


@app.post("/api/v1/process/worker/run-next", response_model=StandardResponse, tags=["process"])
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


@app.post("/api/v1/reconcile/auto-match", response_model=StandardResponse, tags=["reconcile"])
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


@app.get("/api/v1/review/unmatched", response_model=StandardResponse, tags=["reconcile"])
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


@app.post("/api/v1/reconcile/manual", response_model=StandardResponse, tags=["reconcile"])
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
