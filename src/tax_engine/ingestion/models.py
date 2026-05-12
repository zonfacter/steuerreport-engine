from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class DetectFormatRequest(BaseModel):
    source_name: str = Field(min_length=1)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class NormalizePreviewRequest(BaseModel):
    source_name: str = Field(min_length=1)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    locale_hint: str | None = Field(default=None)
    numeric_fields: list[str] | None = Field(default=None)
    datetime_fields: list[str] | None = Field(default=None)
    subunit_fields: dict[str, str] = Field(default_factory=dict)
    timezone: str = Field(default="UTC")


class ConfirmImportRequest(BaseModel):
    source_name: str = Field(min_length=1)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    locale_hint: str | None = Field(default=None)
    subunit_fields: dict[str, str] = Field(default_factory=dict)


class ConnectorParseRequest(BaseModel):
    connector_id: str = Field(min_length=1)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    max_rows: int = Field(default=5000, ge=1, le=50000)


class UploadPreviewRequest(BaseModel):
    connector_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    file_content_base64: str = Field(min_length=1)
    max_rows: int = Field(default=5000, ge=1, le=50000)


class AuditEntry(BaseModel):
    trace_id: str
    action: str
    event_time_utc: str
    payload: dict[str, Any]

    @classmethod
    def create(cls, trace_id: str, action: str, payload: dict[str, Any]) -> AuditEntry:
        return cls(
            trace_id=trace_id,
            action=action,
            event_time_utc=datetime.now(UTC).isoformat(),
            payload=payload,
        )
