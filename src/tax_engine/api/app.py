from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from tax_engine.ingestion import (
    ConfirmImportRequest,
    DetectFormatRequest,
    NormalizePreviewRequest,
    confirm_import,
    detect_format,
    normalize_preview,
    write_audit,
)
from tax_engine.queue import (
    ProcessRunRequest,
    WorkerRunNextRequest,
    create_processing_job,
    get_processing_job,
    run_next_queued_job,
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
