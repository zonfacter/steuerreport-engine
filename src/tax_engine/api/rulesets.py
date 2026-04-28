from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tax_engine.ingestion import write_audit
from tax_engine.ingestion.store import STORE
from tax_engine.integrity import ruleset_fingerprint
from tax_engine.rulesets import TaxRuleset, build_default_registry


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


class RulesetUpsertRequest(BaseModel):
    ruleset_id: str = Field(min_length=1, max_length=80)
    ruleset_version: str = Field(min_length=1, max_length=20)
    jurisdiction: str = Field(min_length=2, max_length=10)
    valid_from: str = Field(min_length=10, max_length=10)
    valid_to: str = Field(min_length=10, max_length=10)
    exemption_limit_so: str = Field(min_length=1, max_length=60)
    other_services_exemption_limit: str = Field(default="256.00", min_length=1, max_length=60)
    holding_period_months: int = Field(ge=0, le=120)
    staking_extension: bool = Field(default=False)
    mining_tax_category: str = Field(min_length=1, max_length=30)
    status: str = Field(default="draft", max_length=30)
    source_hash: str = Field(default="manual", max_length=128)
    approved_by: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=500)


router = APIRouter(prefix="/api/v1/rulesets", tags=["rulesets"])


def _to_iso_date(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise ValueError("invalid_date") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.date().isoformat()


def _format_ruleset_row(row: dict[str, Any], include_status: bool = False) -> dict[str, Any]:
    payload = dict(row)
    if include_status:
        return payload
    payload.pop("status", None)
    payload.pop("source_hash", None)
    payload.pop("approved_by", None)
    payload.pop("notes", None)
    payload.pop("created_at_utc", None)
    return payload


@router.get("", response_model=StandardResponse)
def ruleset_list(include_pending: bool = True) -> StandardResponse:
    trace_id = str(uuid4())
    registry = build_default_registry()
    entries = registry.list_rulesets(include_pending=include_pending)
    catalog_rows = STORE.list_rulesets(include_pending=include_pending)
    catalog_index = {
        f"{str(row['ruleset_id'])}::{str(row['ruleset_version'])}": row for row in catalog_rows
    }
    merged: list[dict[str, Any]] = []
    for entry in entries:
        key = f"{entry.ruleset_id}::{entry.ruleset_version}"
        row = dict(entry.to_dict())
        overlay = catalog_index.get(key)
        if overlay is not None:
            row.update(_format_ruleset_row(overlay, include_status=True))
        merged.append(row)
    for _key, row in catalog_index.items():
        if any(
            item["ruleset_id"] == row["ruleset_id"] and item["ruleset_version"] == row["ruleset_version"]
            for item in merged
        ):
            continue
        merged.append(_format_ruleset_row(row, include_status=True))

    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(merged), "rulesets": merged},
        errors=[],
        warnings=[],
    )


@router.post("", response_model=StandardResponse)
def ruleset_upsert(payload: RulesetUpsertRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        _to_iso_date(payload.valid_from)
        _to_iso_date(payload.valid_to)
    except ValueError:
        write_audit(
            trace_id=trace_id,
            action="rulesets.upsert",
            payload={"ok": False, "reason": "invalid_dates", "ruleset_id": payload.ruleset_id},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_ruleset_dates", "message": "valid_from / valid_to must be ISO-8601 dates"}],
            warnings=[],
        )

    normalized = payload.model_dump()
    if payload.source_hash == "manual":
        ruleset_obj = TaxRuleset.from_dict(
            {
                "ruleset_id": payload.ruleset_id,
                "ruleset_version": payload.ruleset_version,
                "jurisdiction": payload.jurisdiction,
                "valid_from": payload.valid_from,
                "valid_to": payload.valid_to,
                "exemption_limit_so": payload.exemption_limit_so,
                "other_services_exemption_limit": payload.other_services_exemption_limit,
                "holding_period_months": payload.holding_period_months,
                "staking_extension": payload.staking_extension,
                "mining_tax_category": payload.mining_tax_category,
            }
        )
        normalized["source_hash"] = ruleset_fingerprint(ruleset_obj)[:128]
    else:
        normalized["source_hash"] = payload.source_hash.strip()
    if payload.approved_by is not None:
        normalized["approved_by"] = payload.approved_by.strip()
    if payload.notes is not None:
        normalized["notes"] = payload.notes.strip()

    STORE.upsert_ruleset_catalog(payload=normalized)
    write_audit(
        trace_id=trace_id,
        action="rulesets.upsert",
        payload={
            "ruleset_id": payload.ruleset_id,
            "ruleset_version": payload.ruleset_version,
            "status": payload.status,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "ruleset_id": payload.ruleset_id,
            "ruleset_version": payload.ruleset_version,
            "status": payload.status,
            "saved": True,
        },
        errors=[],
        warnings=[],
    )


@router.get("/{ruleset_id}/{ruleset_version}", response_model=StandardResponse)
def ruleset_get(ruleset_id: str, ruleset_version: str) -> StandardResponse:
    trace_id = str(uuid4())
    registry = build_default_registry()
    try:
        ruleset = registry.get(ruleset_id, ruleset_version)
        data: dict[str, Any] = ruleset.to_dict()
        data["status"] = "builtin"
        data["source_hash"] = "builtin"
    except Exception:
        row = STORE.get_ruleset(ruleset_id=ruleset_id, ruleset_version=ruleset_version)
        if row is None:
            return StandardResponse(
                trace_id=trace_id,
                status="error",
                data={},
                errors=[{"code": "ruleset_not_found", "message": f"Ruleset {ruleset_id} v{ruleset_version} not found"}],
                warnings=[],
            )
        data = _format_ruleset_row(row, include_status=True)

    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=[])
