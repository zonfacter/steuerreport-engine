from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import AuditEntry


@dataclass(slots=True)
class InMemoryImportStore:
    source_files: dict[str, dict[str, Any]] = field(default_factory=dict)
    raw_events: dict[str, dict[str, Any]] = field(default_factory=dict)
    audit_trail: list[AuditEntry] = field(default_factory=list)

    def write_audit(self, entry: AuditEntry) -> None:
        self.audit_trail.append(entry)


STORE = InMemoryImportStore()

