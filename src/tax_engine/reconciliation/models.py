from __future__ import annotations

from pydantic import BaseModel, Field


class AutoMatchRequest(BaseModel):
    time_window_seconds: int = Field(default=600, ge=1, le=86400)
    amount_tolerance_ratio: float = Field(default=0.02, ge=0.0, le=1.0)
    min_confidence: float = Field(default=0.75, ge=0.0, le=1.0)


class ManualMatchRequest(BaseModel):
    outbound_event_id: str = Field(min_length=1)
    inbound_event_id: str = Field(min_length=1)
    note: str | None = None

