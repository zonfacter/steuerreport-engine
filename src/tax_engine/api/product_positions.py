from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tax_engine.ingestion import write_audit
from tax_engine.ingestion.store import STORE


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


router = APIRouter(prefix="/api/v1/product-positions", tags=["product-positions"])


@router.get("/events", response_model=StandardResponse)
def product_position_events(
    platform: str | None = None,
    asset: str | None = None,
    tax_treatment: str | None = None,
    limit: int = 10000,
) -> StandardResponse:
    trace_id = str(uuid4())
    rows = STORE.list_product_position_events(
        platform=platform,
        asset=asset,
        tax_treatment=tax_treatment,
        limit=limit,
    )
    write_audit(
        trace_id=trace_id,
        action="product_positions.events",
        payload={
            "platform": platform or "",
            "asset": asset or "",
            "tax_treatment": tax_treatment or "",
            "count": len(rows),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "rows": rows},
        errors=[],
        warnings=[],
    )


@router.get("/summary", response_model=StandardResponse)
def product_position_summary(platform: str | None = None, asset: str | None = None) -> StandardResponse:
    trace_id = str(uuid4())
    rows = STORE.list_product_position_events(platform=platform, asset=asset, limit=100000)
    by_asset: dict[str, dict[str, Any]] = {}
    by_treatment: dict[str, int] = defaultdict(int)
    for row in rows:
        asset_key = str(row.get("asset") or "").upper()
        if not asset_key:
            continue
        treatment = str(row.get("tax_treatment") or "")
        event_type = str(row.get("event_type") or "")
        qty = _dec(row.get("quantity"))
        item = by_asset.setdefault(
            asset_key,
            {
                "asset": asset_key,
                "event_count": 0,
                "principal_movement_abs_qty": Decimal("0"),
                "reward_income_candidate_qty": Decimal("0"),
                "event_type_counts": defaultdict(int),
            },
        )
        item["event_count"] += 1
        item["event_type_counts"][event_type] += 1
        if treatment == "reward_income_candidate":
            item["reward_income_candidate_qty"] += qty
        else:
            item["principal_movement_abs_qty"] += qty
        by_treatment[treatment] += 1

    assets = []
    for item in by_asset.values():
        assets.append(
            {
                "asset": item["asset"],
                "event_count": item["event_count"],
                "principal_movement_abs_qty": item["principal_movement_abs_qty"].to_eng_string(),
                "reward_income_candidate_qty": item["reward_income_candidate_qty"].to_eng_string(),
                "event_type_counts": dict(sorted(item["event_type_counts"].items())),
            }
        )
    assets.sort(key=lambda item: str(item["asset"]))
    write_audit(
        trace_id=trace_id,
        action="product_positions.summary",
        payload={"platform": platform or "", "asset": asset or "", "count": len(rows)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "event_count": len(rows),
            "tax_treatment_counts": dict(sorted(by_treatment.items())),
            "assets": assets,
        },
        errors=[],
        warnings=[],
    )


def _dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")
