from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from tax_engine.api.import_router import router as import_router


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict = Field(default_factory=dict)
    errors: list = Field(default_factory=list)
    warnings: list = Field(default_factory=list)


app = FastAPI(
    title="Steuerreport Engine API",
    version="0.1.0",
    description="Modulare, auditierbare Steuer-Engine API",
)

app.include_router(import_router)


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
