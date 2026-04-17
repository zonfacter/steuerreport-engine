"""Minimal FastAPI bootstrap for Etappe 0."""

from fastapi import FastAPI

app = FastAPI(title="Steuerreport Engine API", version="0.1.0")


@app.get("/api/v1/health", tags=["system"])
def health() -> dict[str, object]:
    """Liveness endpoint using the standardized response envelope."""
    return {
        "status": "success",
        "trace_id": "bootstrap-trace-id",
        "data": {"service": "steuerreport-engine", "uptime_state": "ok"},
        "errors": [],
        "warnings": [],
    }
