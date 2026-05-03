from __future__ import annotations

from base64 import b64decode
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

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


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


class BulkFolderImportRequest(BaseModel):
    folder_path: str = Field(default="usertransfer", min_length=1, max_length=500)
    recursive: bool = Field(default=True)
    dry_run: bool = Field(default=False)
    max_files: int = Field(default=500, ge=1, le=5000)
    max_rows_per_file: int = Field(default=200000, ge=1, le=500000)


router = APIRouter(prefix="/api/v1/import", tags=["import"])

_BULK_IMPORT_EXTENSIONS = {".csv", ".txt", ".json", ".xls", ".xlsx"}


def detect_connector_from_filename(file_path: Path) -> str | None:
    name = file_path.name.lower()
    if name.startswith("heliumtracker-report-advanced"):
        return "heliumtracker"
    if "helium-staking wallet" in name and "raw" in name:
        return "helium_legacy_raw"
    if "helium" in name and "cointracking" in name:
        return "helium_legacy_cointracking"
    if "blockpit" in name:
        return "blockpit"
    if "binance" in name:
        return "binance"
    if "bitget" in name:
        return "bitget"
    if "coinbase" in name:
        return "coinbase"
    if "pionex" in name:
        return "pionex"
    if "heliumgeek" in name:
        return "heliumgeek"
    if name.startswith("wallet.") and "month" in name:
        return "heliumgeek"
    return None


def detect_connector_from_source_name(source_name: str) -> str:
    normalized = str(source_name or "").lower()
    if "heliumtracker-report-advanced" in normalized:
        return "heliumtracker"
    if "helium-staking wallet" in normalized and "raw" in normalized:
        return "helium_legacy_raw"
    if "helium_legacy_cointracking" in normalized or ("helium" in normalized and "cointracking" in normalized):
        return "helium_legacy_cointracking"
    for connector in ("binance", "bitget", "coinbase", "pionex", "blockpit", "heliumgeek", "heliumtracker", "solana"):
        if connector in normalized:
            return connector
    if normalized.startswith("wallet.") and "month" in normalized:
        return "heliumgeek"
    return "unknown"


def build_import_job_rows(
    *,
    status: str | None,
    integration: str | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    wanted_status = str(status or "").strip().lower()
    wanted_integration = str(integration or "").strip().lower()
    raw_rows = STORE.list_source_file_summaries(limit=5000)
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        declared = int(row.get("declared_row_count") or 0)
        imported = int(row.get("imported_event_count") or 0)
        duplicates = max(declared - imported, 0)
        warnings: list[dict[str, Any]] = []
        if declared == 0:
            row_status = "empty"
            status_reason = "Die Quelle enthielt keine importierbaren Zeilen."
            warnings.append({"code": "empty_import", "message": status_reason})
        elif imported == 0 and duplicates > 0:
            row_status = "duplicate"
            status_reason = "Alle Zeilen waren bereits als Events vorhanden."
            warnings.append({"code": "duplicate_import", "message": status_reason})
        elif imported < declared:
            row_status = "partial"
            status_reason = f"{imported} von {declared} Zeilen wurden importiert; {duplicates} Zeilen waren Duplikate oder nicht steuerwirksam."
            warnings.append({"code": "partial_import", "message": status_reason})
        else:
            row_status = "completed"
            status_reason = "Alle Zeilen wurden verarbeitet."

        source_name = str(row.get("source_name") or "")
        connector = detect_connector_from_source_name(source_name)
        is_bulk = source_name.startswith("bulk:")
        can_retry = row_status in {"empty", "partial"} or is_bulk
        retry_action = "retry_bulk" if is_bulk else "open_connector"
        severity = "ok" if row_status == "completed" else "info" if row_status == "duplicate" else "warning"
        if wanted_status and row_status != wanted_status:
            continue
        if wanted_integration and connector != wanted_integration:
            continue
        rows.append(
            {
                "job_id": row.get("source_file_id"),
                "source_file_id": row.get("source_file_id"),
                "connector": connector,
                "source_name": source_name,
                "started_at_utc": row.get("created_at_utc"),
                "finished_at_utc": row.get("created_at_utc"),
                "status": row_status,
                "status_reason": status_reason,
                "severity": severity,
                "rows": declared,
                "inserted_events": imported,
                "duplicates": duplicates,
                "can_retry": can_retry,
                "retry_action": retry_action,
                "warnings": warnings,
            }
        )
    return rows[offset : offset + limit]


@router.post("/detect-format", response_model=StandardResponse)
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


@router.post("/normalize-preview", response_model=StandardResponse)
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


@router.post("/confirm", response_model=StandardResponse)
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


@router.get("/sources-summary", response_model=StandardResponse)
def import_sources_summary(limit: int = 100) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = max(1, min(limit, 5000))
    rows = STORE.list_source_file_summaries(limit=safe_limit)
    write_audit(
        trace_id=trace_id,
        action="import.sources_summary",
        payload={"count": len(rows), "limit": safe_limit},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "rows": rows},
        errors=[],
        warnings=[],
    )


@router.get("/connectors", response_model=StandardResponse)
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


@router.post("/parse-preview", response_model=StandardResponse)
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


@router.post("/upload-preview", response_model=StandardResponse)
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
        for row in rows:
            row["__source_name"] = payload.filename
            row["__file_name"] = payload.filename
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


@router.post("/bulk-folder", response_model=StandardResponse)
def import_bulk_folder(payload: BulkFolderImportRequest) -> StandardResponse:
    trace_id = str(uuid4())
    folder = Path(payload.folder_path).expanduser()
    if not folder.is_absolute():
        folder = (Path.cwd() / folder).resolve()
    else:
        folder = folder.resolve()

    if not folder.exists() or not folder.is_dir():
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "folder_not_found", "message": str(folder)}],
            warnings=[],
        )

    file_iter = folder.rglob("*") if payload.recursive else folder.glob("*")
    candidate_files = [
        path
        for path in file_iter
        if path.is_file() and path.suffix.lower() in _BULK_IMPORT_EXTENSIONS
    ]
    candidate_files = sorted(candidate_files)[: payload.max_files]

    rows: list[dict[str, Any]] = []
    total_inserted = 0
    total_duplicates = 0
    total_normalized = 0
    total_failed = 0
    warnings: list[dict[str, str]] = []

    for file_path in candidate_files:
        connector_id = detect_connector_from_filename(file_path)
        if connector_id is None:
            warnings.append({"code": "connector_not_detected", "message": file_path.name})
            continue
        try:
            raw_rows, parse_warnings = parse_upload_file(file_path.name, file_path.read_bytes())
            for raw_row in raw_rows:
                raw_row["__source_name"] = file_path.name
                raw_row["__file_name"] = file_path.name
            normalized_rows, map_warnings, errors = normalize_connector_rows(
                connector_id=connector_id,
                rows=raw_rows,
                max_rows=payload.max_rows_per_file,
            )
            total_normalized += len(normalized_rows)
            if payload.dry_run:
                import_result = {"inserted_events": 0, "duplicate_events": 0}
            else:
                source_name = f"bulk:{connector_id}:{file_path.name}"
                import_result = confirm_import(source_name=source_name, rows=normalized_rows)
                total_inserted += int(import_result.get("inserted_events", 0))
                total_duplicates += int(import_result.get("duplicate_events", 0))

            rows.append(
                {
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "connector_id": connector_id,
                    "raw_rows": len(raw_rows),
                    "normalized_rows": len(normalized_rows),
                    "parse_warnings": len(parse_warnings),
                    "map_warnings": len(map_warnings),
                    "errors": len(errors),
                    "inserted_events": int(import_result.get("inserted_events", 0)),
                    "duplicate_events": int(import_result.get("duplicate_events", 0)),
                }
            )
        except Exception as exc:
            total_failed += 1
            rows.append(
                {
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "connector_id": connector_id or "",
                    "raw_rows": 0,
                    "normalized_rows": 0,
                    "parse_warnings": 0,
                    "map_warnings": 0,
                    "errors": 1,
                    "inserted_events": 0,
                    "duplicate_events": 0,
                    "error_message": str(exc),
                }
            )

    write_audit(
        trace_id=trace_id,
        action="import.bulk_folder",
        payload={
            "folder_path": str(folder),
            "recursive": payload.recursive,
            "dry_run": payload.dry_run,
            "scanned_files": len(candidate_files),
            "processed_files": len(rows),
            "failed_files": total_failed,
            "normalized_rows": total_normalized,
            "inserted_events": total_inserted,
            "duplicate_events": total_duplicates,
        },
    )

    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "folder_path": str(folder),
            "recursive": payload.recursive,
            "dry_run": payload.dry_run,
            "scanned_files": len(candidate_files),
            "processed_files": len(rows),
            "failed_files": total_failed,
            "normalized_rows": total_normalized,
            "inserted_events": total_inserted,
            "duplicate_events": total_duplicates,
            "rows": rows,
        },
        errors=[],
        warnings=warnings,
    )


@router.get("/jobs", response_model=StandardResponse)
def import_jobs(
    status: str | None = None,
    integration: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = max(1, min(int(limit), 5000))
    safe_offset = max(0, int(offset))
    rows = build_import_job_rows(
        status=status,
        integration=integration,
        limit=safe_limit,
        offset=safe_offset,
    )
    write_audit(
        trace_id=trace_id,
        action="import.jobs",
        payload={
            "status": status,
            "integration": integration,
            "count": len(rows),
            "limit": safe_limit,
            "offset": safe_offset,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "offset": safe_offset, "limit": safe_limit, "rows": rows},
        errors=[],
        warnings=[],
    )
