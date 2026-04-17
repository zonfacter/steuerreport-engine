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
