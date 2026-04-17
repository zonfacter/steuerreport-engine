from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter

from tax_engine.ingestion.models import (
    ConfirmImportData,
    ConfirmImportRequest,
    DetectFormatData,
    DetectFormatRequest,
    ErrorDetail,
    NormalizePreviewRequest,
    PersistedRawEvent,
    PersistedSourceFile,
)
from tax_engine.ingestion.normalizer import normalize_preview
from tax_engine.ingestion.parser import detect_column_format, detect_source_candidates, dedupe_payload_for_row
from tax_engine.integrity.audit import AuditEventWriter
from tax_engine.integrity.fingerprint import unique_event_id


router = APIRouter(prefix="/api/v1/import", tags=["import"])

_AUDIT_WRITER = AuditEventWriter()
_PERSISTED_SOURCE_FILES: list[PersistedSourceFile] = []
_PERSISTED_RAW_EVENTS: dict[str, PersistedRawEvent] = {}


def _response(
    *,
    trace_id: str,
    status: str,
    data: Any,
    errors: list[ErrorDetail] | list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "status": status,
        "data": data,
        "errors": [error.model_dump() if isinstance(error, ErrorDetail) else error for error in errors],
        "warnings": warnings,
    }


@router.post("/detect-format")
def detect_format(request: DetectFormatRequest) -> dict[str, Any]:
    trace_id = str(uuid4())
    source_candidates = detect_source_candidates(request.rows)

    if not request.rows:
        _AUDIT_WRITER.write(trace_id=trace_id, step="import.detect_format", status="partial", details={"row_count": 0})
        return _response(
            trace_id=trace_id,
            status="partial",
            data=DetectFormatData(row_count=0, column_detections=[]).model_dump(),
            errors=[],
            warnings=[{"code": "schema_mismatch", "message": "No rows supplied for format detection."}],
        )

    keys = sorted({key for row in request.rows for key in row.keys()})
    detections = [
        detect_column_format(
            field=field,
            values=[row.get(field) for row in request.rows],
            source_candidates=source_candidates,
            profile=request.profile,
        ).model_dump()
        for field in keys
    ]

    _AUDIT_WRITER.write(
        trace_id=trace_id,
        step="import.detect_format",
        status="success",
        details={"row_count": len(request.rows), "source_candidates": source_candidates},
    )

    return _response(
        trace_id=trace_id,
        status="success",
        data=DetectFormatData(row_count=len(request.rows), column_detections=detections).model_dump(),
        errors=[],
        warnings=[],
    )


@router.post("/normalize-preview")
def normalize_preview_endpoint(request: NormalizePreviewRequest) -> dict[str, Any]:
    trace_id = str(uuid4())
    data, errors, warnings = normalize_preview(request)

    status = "success"
    if errors and data.normalized_rows:
        status = "partial"
    elif errors:
        status = "error"
    elif warnings:
        status = "partial"

    _AUDIT_WRITER.write(
        trace_id=trace_id,
        step="import.normalize_preview",
        status=status,
        details={
            "row_count": len(request.rows),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "profile_id": request.profile.profile_id,
            "profile_version": request.profile.profile_version,
        },
    )

    return _response(
        trace_id=trace_id,
        status=status,
        data=data.model_dump(),
        errors=errors,
        warnings=[warning.model_dump() for warning in warnings],
    )


@router.post("/confirm")
def confirm_import(request: ConfirmImportRequest) -> dict[str, Any]:
    trace_id = str(uuid4())
    now = datetime.now(UTC)

    persisted_files: list[PersistedSourceFile] = []
    for source_file in request.source_files:
        persisted = PersistedSourceFile(
            source_name=source_file.source_name,
            file_name=source_file.file_name,
            file_hash=source_file.file_hash,
            imported_at_utc=now,
        )
        _PERSISTED_SOURCE_FILES.append(persisted)
        persisted_files.append(persisted)

    duplicate_event_ids: list[str] = []
    persisted_events: list[PersistedRawEvent] = []
    schema_errors: list[ErrorDetail] = []
    source_name = request.source_files[0].source_name if request.source_files else None

    for row in request.raw_events:
        if not isinstance(row, dict):
            schema_errors.append(
                ErrorDetail(
                    code="schema_mismatch",
                    message="raw_events entries must be objects.",
                    field="raw_events",
                )
            )
            continue

        dedupe_payload = dedupe_payload_for_row(row, source_name=source_name)
        event_id = unique_event_id(dedupe_payload)

        if event_id in _PERSISTED_RAW_EVENTS:
            duplicate_event_ids.append(event_id)
            continue

        persisted_event = PersistedRawEvent(
            unique_event_id=event_id,
            raw_event=row,
            source_name=source_name,
            profile_id=request.profile.profile_id,
            profile_version=request.profile.profile_version,
            imported_at_utc=now,
        )
        _PERSISTED_RAW_EVENTS[event_id] = persisted_event
        persisted_events.append(persisted_event)

    status = "success"
    warnings: list[dict[str, Any]] = []
    if schema_errors and persisted_events:
        status = "partial"
    elif schema_errors:
        status = "error"

    if duplicate_event_ids:
        warnings.append(
            {
                "code": "duplicate_event",
                "message": "Duplicate events skipped based on deterministic unique_event_id.",
                "hint": f"duplicates={len(duplicate_event_ids)}",
            }
        )
        if status == "success":
            status = "partial"

    _AUDIT_WRITER.write(
        trace_id=trace_id,
        step="import.confirm",
        status=status,
        details={
            "persisted_source_files": len(persisted_files),
            "persisted_raw_events": len(persisted_events),
            "duplicate_raw_events": len(duplicate_event_ids),
            "profile_id": request.profile.profile_id,
            "profile_version": request.profile.profile_version,
        },
    )

    return _response(
        trace_id=trace_id,
        status=status,
        data=ConfirmImportData(
            persisted_source_files=persisted_files,
            persisted_raw_events=persisted_events,
            duplicate_event_ids=duplicate_event_ids,
        ).model_dump(),
        errors=schema_errors,
        warnings=warnings,
    )
