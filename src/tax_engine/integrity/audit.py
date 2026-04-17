from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any, Literal

from tax_engine.ingestion.models import AuditEvent


class AuditEventWriter:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = Lock()

    def write(
        self,
        *,
        trace_id: str,
        step: str,
        status: Literal["success", "error", "partial"],
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            trace_id=trace_id,
            step=step,
            status=status,
            details=details or {},
            created_at_utc=datetime.now(UTC),
        )
        with self._lock:
            self._events.append(event)
        return event

    def list_events(self, trace_id: str | None = None) -> list[AuditEvent]:
        with self._lock:
            if trace_id is None:
                return list(self._events)
            return [event for event in self._events if event.trace_id == trace_id]
