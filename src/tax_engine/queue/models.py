from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProcessRunRequest(BaseModel):
    tax_year: int = Field(ge=2020, le=2100)
    ruleset_id: str = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = Field(default=False)

