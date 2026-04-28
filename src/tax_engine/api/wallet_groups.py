from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tax_engine.admin import put_admin_setting
from tax_engine.connectors import WalletGroupDeleteRequest, WalletGroupUpsertRequest
from tax_engine.ingestion import write_audit
from tax_engine.ingestion.store import STORE


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


router = APIRouter(prefix="/api/v1/wallet-groups", tags=["wallet-groups"])


def decimal_to_plain(value: Decimal) -> str:
    # Keine wissenschaftliche Notation in der UI (z. B. 1E+9).
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"-0", ""}:
        return "0"
    return text


def normalize_wallet_addresses(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item:
            continue
        if item not in normalized:
            normalized.append(item)
    return normalized


def load_wallet_groups() -> list[dict[str, Any]]:
    row = STORE.get_setting("runtime.wallet_groups")
    if row is None:
        return []
    try:
        raw = json.loads(str(row.get("value_json", "[]")))
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    groups: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        group_id = str(item.get("group_id") or "").strip()
        name = str(item.get("name") or "").strip()
        wallets_raw = item.get("wallet_addresses", [])
        if not isinstance(wallets_raw, list):
            wallets_raw = []
        wallets = normalize_wallet_addresses([str(v) for v in wallets_raw])
        if not group_id or not name:
            continue
        groups.append(
            {
                "group_id": group_id,
                "name": name,
                "wallet_addresses": wallets,
                "description": str(item.get("description") or "").strip(),
            }
        )
    return groups


def resolve_wallets_from_group(group_id: str | None, payload_wallets: list[str]) -> list[str]:
    wallets = normalize_wallet_addresses(payload_wallets)
    if wallets:
        return wallets
    if not group_id:
        return []
    groups = load_wallet_groups()
    for group in groups:
        if str(group.get("group_id", "")) == group_id:
            values = group.get("wallet_addresses", [])
            if isinstance(values, list):
                return normalize_wallet_addresses([str(v) for v in values])
    return []


def load_wallet_snapshots() -> list[dict[str, Any]]:
    row = STORE.get_setting("runtime.dashboard.wallet_snapshots")
    if row is None:
        return []
    try:
        raw = json.loads(str(row.get("value_json", "[]")))
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    points: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        scope = str(item.get("scope", "")).strip()
        entity_id = str(item.get("entity_id", "")).strip()
        ts = str(item.get("timestamp_utc", "")).strip()
        if scope not in {"wallet", "group"} or not entity_id or not ts:
            continue
        points.append(
            {
                "scope": scope,
                "entity_id": entity_id,
                "timestamp_utc": ts,
                "total_estimated_usd": str(item.get("total_estimated_usd", "")),
                "sol_balance": str(item.get("sol_balance", "")),
            }
        )
    points.sort(key=lambda p: str(p.get("timestamp_utc", "")))
    return points


def append_wallet_snapshot(scope: str, entity_id: str, total_estimated_usd: str, sol_balance: str) -> None:
    if scope not in {"wallet", "group"}:
        return
    eid = str(entity_id).strip()
    if not eid:
        return
    points = load_wallet_snapshots()
    points.append(
        {
            "scope": scope,
            "entity_id": eid,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "total_estimated_usd": str(total_estimated_usd or ""),
            "sol_balance": str(sol_balance or ""),
        }
    )
    # Ringpuffer: letzte 2000 Punkte behalten.
    if len(points) > 2000:
        points = points[-2000:]
    put_admin_setting("runtime.dashboard.wallet_snapshots", points, is_secret=False)


def filter_wallet_snapshots(scope: str, entity_id: str) -> list[dict[str, Any]]:
    points = load_wallet_snapshots()
    scoped = [point for point in points if str(point.get("scope")) == scope]
    eid = str(entity_id).strip()
    if not eid:
        return scoped[-300:]
    return [point for point in scoped if str(point.get("entity_id", "")) == eid][-300:]


@router.get("", response_model=StandardResponse)
def wallet_groups_list() -> StandardResponse:
    trace_id = str(uuid4())
    groups = load_wallet_groups()
    write_audit(
        trace_id=trace_id,
        action="wallet_groups.list",
        payload={"count": len(groups)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(groups), "groups": groups},
        errors=[],
        warnings=[],
    )


@router.post("/upsert", response_model=StandardResponse)
def wallet_groups_upsert(payload: WalletGroupUpsertRequest) -> StandardResponse:
    trace_id = str(uuid4())
    groups = load_wallet_groups()
    normalized_wallets = normalize_wallet_addresses(payload.wallet_addresses)
    if not normalized_wallets:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "wallet_addresses_empty", "message": "Mindestens eine Wallet-Adresse erforderlich."}],
            warnings=[],
        )

    group_id = (payload.group_id or "").strip() or str(uuid4())
    name = payload.name.strip()
    description = (payload.description or "").strip()
    updated = False
    for group in groups:
        if str(group.get("group_id", "")) == group_id:
            group["name"] = name
            group["wallet_addresses"] = normalized_wallets
            group["description"] = description
            updated = True
            break

    if not updated:
        groups.append(
            {
                "group_id": group_id,
                "name": name,
                "wallet_addresses": normalized_wallets,
                "description": description,
            }
        )

    put_admin_setting("runtime.wallet_groups", groups, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="wallet_groups.upsert",
        payload={"group_id": group_id, "wallet_count": len(normalized_wallets), "updated": updated},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"group_id": group_id, "updated": updated, "groups": groups},
        errors=[],
        warnings=[],
    )


@router.post("/delete", response_model=StandardResponse)
def wallet_groups_delete(payload: WalletGroupDeleteRequest) -> StandardResponse:
    trace_id = str(uuid4())
    groups = load_wallet_groups()
    remaining = [group for group in groups if str(group.get("group_id", "")) != payload.group_id]
    deleted = len(remaining) != len(groups)
    put_admin_setting("runtime.wallet_groups", remaining, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="wallet_groups.delete",
        payload={"group_id": payload.group_id, "deleted": deleted},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"deleted": deleted, "count": len(remaining), "groups": remaining},
        errors=[],
        warnings=[],
    )
