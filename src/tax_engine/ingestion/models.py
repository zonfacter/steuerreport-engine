from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None
    hint: str | None = None


class WarningDetail(BaseModel):
    code: str
    message: str
    field: str | None = None
    hint: str | None = None


class ImportProfile(BaseModel):
    profile_id: str
    profile_version: str
    locale: str | None = None
    decimal_separator: str | None = None
    thousand_separator: str | None = None
    date_patterns: list[str] = Field(default_factory=list)
    timezone_hint: str | None = None
    subunit_factors: dict[str, Decimal] = Field(default_factory=dict)
    subunit_field_map: dict[str, str] = Field(default_factory=dict)


class DetectFormatRequest(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    profile: ImportProfile | None = None


class ColumnFormatDetection(BaseModel):
    field: str
    decimal_separator: str | None = None
    thousand_separator: str | None = None
    date_pattern: str | None = None
    timezone_hint: str | None = None
    source_candidates: list[str] = Field(default_factory=list)


class DetectFormatData(BaseModel):
    row_count: int
    column_detections: list[ColumnFormatDetection] = Field(default_factory=list)


class NormalizePreviewRequest(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    profile: ImportProfile
    numeric_fields: list[str] = Field(default_factory=list)
    datetime_fields: list[str] = Field(default_factory=list)
    asset_field: str = "asset"


class NormalizedRow(BaseModel):
    index: int
    values: dict[str, Any]
    unresolved_fields: list[str] = Field(default_factory=list)


class NormalizePreviewData(BaseModel):
    row_count: int
    normalized_rows: list[NormalizedRow] = Field(default_factory=list)


class SourceFileInput(BaseModel):
    source_name: str
    file_name: str
    file_hash: str


class ConfirmImportRequest(BaseModel):
    source_files: list[SourceFileInput] = Field(default_factory=list)
    raw_events: list[dict[str, Any]] = Field(default_factory=list)
    profile: ImportProfile


class PersistedSourceFile(BaseModel):
    source_name: str
    file_name: str
    file_hash: str
    imported_at_utc: datetime


class PersistedRawEvent(BaseModel):
    unique_event_id: str
    raw_event: dict[str, Any]
    source_name: str | None = None
    profile_id: str
    profile_version: str
    imported_at_utc: datetime


class ConfirmImportData(BaseModel):
    persisted_source_files: list[PersistedSourceFile] = Field(default_factory=list)
    persisted_raw_events: list[PersistedRawEvent] = Field(default_factory=list)
    duplicate_event_ids: list[str] = Field(default_factory=list)


class AuditEvent(BaseModel):
    trace_id: str
    step: str
    status: Literal["success", "error", "partial"]
    details: dict[str, Any] = Field(default_factory=dict)
    created_at_utc: datetime
