from __future__ import annotations

import json
from bisect import bisect_right
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tax_engine.admin import put_admin_setting, resolve_effective_runtime_config
from tax_engine.api.wallet_groups import (
    decimal_to_plain as _decimal_to_plain,
)
from tax_engine.api.wallet_groups import (
    filter_wallet_snapshots as _filter_wallet_snapshots,
)
from tax_engine.api.wallet_groups import (
    load_wallet_groups as _load_wallet_groups,
)
from tax_engine.api.wallet_groups import (
    normalize_source_filters as _normalize_source_filters,
)
from tax_engine.connectors import DashboardRoleOverrideRequest
from tax_engine.connectors.token_metadata import resolve_token_metadata
from tax_engine.core.processor import build_open_lot_aging_snapshot
from tax_engine.ingestion import write_audit
from tax_engine.ingestion.store import STORE
from tax_engine.integrations import (
    active_sources_from_integrations,
    effective_integration_mode,
    infer_default_integration_mode,
    load_integration_mode_overrides,
    normalize_integration_mode,
    upsert_integration_mode,
)


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


class IntegrationModeUpdateRequest(BaseModel):
    integration_id: str = Field(min_length=1, max_length=120)
    mode: str = Field(min_length=3, max_length=30)
    note: str | None = Field(default=None, max_length=500)


router = APIRouter()

_STABLE_ASSET_SYMBOLS = {"USD", "USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD"}
_FxLookup = dict[tuple[str, str], list[tuple[str, Decimal]]]

@router.post("/api/v1/dashboard/role-override", response_model=StandardResponse, tags=["dashboard"])
def dashboard_role_override(payload: DashboardRoleOverrideRequest) -> StandardResponse:
    trace_id = str(uuid4())
    put_admin_setting("runtime.dashboard.role_override", payload.mode, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="dashboard.role_override",
        payload={"mode": payload.mode},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"mode": payload.mode, "saved": True},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/dashboard/overview", response_model=StandardResponse, tags=["dashboard"])
def dashboard_overview() -> StandardResponse:
    trace_id = str(uuid4())
    events = STORE.list_raw_events()

    by_source: dict[str, int] = {}
    by_event_type: dict[str, int] = {}
    by_day: dict[str, int] = {}
    by_year: dict[int, int] = {}
    asset_balances: dict[str, Decimal] = {}
    yearly_asset_buckets: dict[tuple[int, str, str], dict[str, Any]] = {}
    yearly_deduped_values: dict[int, dict[str, Any]] = {}
    yearly_event_buckets: dict[tuple[int, str], dict[str, Any]] = {}
    yearly_source_buckets: dict[tuple[int, str], dict[str, Any]] = {}
    runtime_fx = _runtime_usd_to_eur_rate()
    fx_rate_cache: dict[str, Decimal] = {}
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] = {}
    fx_lookup = _load_fx_lookup()

    reward_events = 0
    mining_events = 0
    ignored_tokens = _load_ignored_tokens()
    ignored_mints = set(ignored_tokens.keys())
    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source") or "unknown")
        event_type = str(payload.get("event_type") or "unknown")
        by_source[source] = by_source.get(source, 0) + 1
        by_event_type[event_type] = by_event_type.get(event_type, 0) + 1

        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        day = ts_raw[:10] if len(ts_raw) >= 10 else "unknown"
        by_day[day] = by_day.get(day, 0) + 1
        year = _extract_year(ts_raw)
        if year is not None:
            by_year[year] = by_year.get(year, 0) + 1

        side = str(payload.get("side") or "").lower()
        asset = str(payload.get("asset") or "").upper()
        if _normalize_mint(asset) in ignored_mints:
            continue
        qty = _dashboard_event_quantity(payload)
        if year is not None and asset:
            value = _estimate_event_values(
                payload=payload,
                asset=asset,
                quantity=qty,
                runtime_fx=runtime_fx,
                fx_rate_cache=fx_rate_cache,
                asset_usd_price_cache=asset_usd_price_cache,
                fx_lookup=fx_lookup,
            )
            value_counts = _is_dashboard_value_event(payload)
            _accumulate_yearly_event_breakdown(
                yearly_event_buckets=yearly_event_buckets,
                year=year,
                payload=payload,
                value=value,
                value_counts=value_counts,
            )
            _accumulate_yearly_source_breakdown(
                yearly_source_buckets=yearly_source_buckets,
                year=year,
                payload=payload,
                value=value,
                value_counts=value_counts,
            )
            source_key = source or "unknown"
            bucket_key = (year, asset, source_key)
            bucket = yearly_asset_buckets.setdefault(
                bucket_key,
                {
                    "year": year,
                    "asset": asset,
                    "source": source_key,
                    "events": 0,
                    "quantity_in": Decimal("0"),
                    "quantity_out": Decimal("0"),
                    "quantity_net": Decimal("0"),
                    "quantity_abs": Decimal("0"),
                    "value_usd": Decimal("0"),
                    "value_eur": Decimal("0"),
                    "trading_value_usd": Decimal("0"),
                    "trading_value_eur": Decimal("0"),
                    "priced_events": 0,
                    "unpriced_events": 0,
                    "valuation_required_events": 0,
                },
            )
            bucket["events"] += 1
            bucket["quantity_abs"] += abs(qty)
            if side == "in":
                bucket["quantity_in"] += abs(qty)
                bucket["quantity_net"] += abs(qty)
            elif side == "out":
                bucket["quantity_out"] += abs(qty)
                bucket["quantity_net"] -= abs(qty)
            else:
                bucket["quantity_net"] += qty
            if value_counts:
                bucket["value_usd"] += value["usd_abs"]
                bucket["value_eur"] += value["eur_abs"]
                _accumulate_yearly_deduped_value(
                    yearly_deduped_values=yearly_deduped_values,
                    year=year,
                    payload=payload,
                    value=value,
                    event_type=event_type,
                )
            if _is_trading_volume_event(event_type):
                bucket["trading_value_usd"] += value["usd_abs"]
                bucket["trading_value_eur"] += value["eur_abs"]
            if _requires_dashboard_valuation(payload):
                bucket["valuation_required_events"] += 1
                if value["priced"]:
                    bucket["priced_events"] += 1
                else:
                    bucket["unpriced_events"] += 1
        if asset and qty != Decimal("0"):
            sign = Decimal("0")
            if side == "in":
                sign = Decimal("1")
            elif side == "out":
                sign = Decimal("-1")
            asset_balances[asset] = asset_balances.get(asset, Decimal("0")) + (sign * qty)

        lowered = event_type.lower()
        if any(tag in lowered for tag in ("reward", "claim", "staking", "income")):
            reward_events += 1
        if "mining" in lowered:
            mining_events += 1

    sorted_days = sorted(by_day.items(), key=lambda item: item[0])
    activity_history = [{"day": day, "count": count} for day, count in sorted_days if day != "unknown"]
    activity_years = [
        {"year": year, "count": count}
        for year, count in sorted(by_year.items(), key=lambda item: item[0])
    ]
    yearly_asset_activity = _format_yearly_asset_activity(
        yearly_asset_buckets,
        yearly_deduped_values,
        yearly_event_buckets,
        yearly_source_buckets,
    )
    top_balances = sorted(asset_balances.items(), key=lambda item: abs(item[1]), reverse=True)[:20]
    balances: list[dict[str, str]] = []
    for asset, qty in top_balances:
        meta = _resolve_token_display(asset)
        spam_candidate = _is_spam_candidate(asset=asset, qty=qty, known=meta["is_known"])
        balances.append(
            {
                "asset": asset,
                "symbol": str(meta["symbol"]),
                "name": str(meta["name"]),
                "display_source": str(meta["display_source"]),
                "quantity": _decimal_to_plain(qty),
                "quantity_abs": _decimal_to_plain(abs(qty)),
                "flow_direction": "net_in" if qty > 0 else ("net_out" if qty < 0 else "flat"),
                "spam_candidate": "true" if spam_candidate else "false",
            }
        )

    override_mode = _load_dashboard_role_override()
    auto_business = (reward_events > 0 and len(events) >= 500) or mining_events > 0
    detected_mode = "business" if auto_business else "private"
    effective_mode = detected_mode if override_mode == "auto" else override_mode

    role_detection = {
        "is_commercial": effective_mode == "business",
        "detected_mode": detected_mode,
        "override_mode": override_mode,
        "effective_mode": effective_mode,
        "signals": {
            "has_reward_events": reward_events > 0,
            "reward_events": reward_events,
            "mining_events": mining_events,
            "high_activity": len(events) >= 500,
            "event_count": len(events),
        },
    }

    wallet_groups = _load_wallet_groups()
    data = {
        "summary": {
            "total_events": len(events),
            "unique_sources": len(by_source),
            "unique_event_types": len(by_event_type),
            "unique_assets": len({item["asset"] for item in balances}),
            "suggested_tax_year": max(by_year.keys()) if by_year else None,
        },
        "role_detection": role_detection,
        "by_source": by_source,
        "by_event_type": by_event_type,
        "activity_history": activity_history,
        "activity_years": activity_years,
        "portfolio_value_history": _build_portfolio_value_history(
            events,
            ignored_mints,
            runtime_fx,
            fx_rate_cache=fx_rate_cache,
            asset_usd_price_cache=asset_usd_price_cache,
            fx_lookup=fx_lookup,
        ),
        "yearly_asset_activity": yearly_asset_activity,
        "asset_balances": balances,
        "wallet_groups": _decorate_wallet_groups_with_sources(wallet_groups, by_source),
    }
    write_audit(
        trace_id=trace_id,
        action="dashboard.overview",
        payload={
            "total_events": len(events),
            "effective_mode": effective_mode,
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=[])


@router.get("/api/v1/dashboard/shell", response_model=StandardResponse, tags=["dashboard"])
def dashboard_shell() -> StandardResponse:
    trace_id = str(uuid4())
    events = STORE.list_raw_events()
    by_source: dict[str, int] = {}
    by_event_type: dict[str, int] = {}
    by_day: dict[str, int] = {}
    by_year: dict[int, int] = {}
    asset_balances: dict[str, Decimal] = {}
    reward_events = 0
    mining_events = 0
    ignored_mints = set(_load_ignored_tokens().keys())

    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source") or "unknown")
        event_type = str(payload.get("event_type") or "unknown")
        by_source[source] = by_source.get(source, 0) + 1
        by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        day = ts_raw[:10] if len(ts_raw) >= 10 else "unknown"
        by_day[day] = by_day.get(day, 0) + 1
        year = _extract_year(ts_raw)
        if year is not None:
            by_year[year] = by_year.get(year, 0) + 1
        asset = str(payload.get("asset") or "").upper()
        if asset and _normalize_mint(asset) not in ignored_mints:
            qty = _dashboard_event_quantity(payload)
            side = str(payload.get("side") or "").lower()
            sign = Decimal("1") if side == "in" else Decimal("-1") if side == "out" else Decimal("0")
            if sign != 0:
                asset_balances[asset] = asset_balances.get(asset, Decimal("0")) + (sign * qty)
        lowered = event_type.lower()
        if any(tag in lowered for tag in ("reward", "claim", "staking", "income")):
            reward_events += 1
        if "mining" in lowered:
            mining_events += 1

    balances: list[dict[str, str]] = []
    for asset, qty in sorted(asset_balances.items(), key=lambda item: abs(item[1]), reverse=True)[:20]:
        meta = _resolve_token_display(asset)
        balances.append(
            {
                "asset": asset,
                "symbol": str(meta["symbol"]),
                "name": str(meta["name"]),
                "display_source": str(meta["display_source"]),
                "quantity": _decimal_to_plain(qty),
                "quantity_abs": _decimal_to_plain(abs(qty)),
                "flow_direction": "net_in" if qty > 0 else ("net_out" if qty < 0 else "flat"),
                "spam_candidate": "true" if _is_spam_candidate(asset=asset, qty=qty, known=meta["is_known"]) else "false",
            }
        )

    override_mode = _load_dashboard_role_override()
    auto_business = (reward_events > 0 and len(events) >= 500) or mining_events > 0
    detected_mode = "business" if auto_business else "private"
    effective_mode = detected_mode if override_mode == "auto" else override_mode
    activity_history = [{"day": day, "count": count} for day, count in sorted(by_day.items()) if day != "unknown"]
    activity_years = [{"year": year, "count": count} for year, count in sorted(by_year.items())]
    data = {
        "summary": {
            "total_events": len(events),
            "unique_sources": len(by_source),
            "unique_event_types": len(by_event_type),
            "unique_assets": len({item["asset"] for item in balances}),
            "suggested_tax_year": max(by_year.keys()) if by_year else None,
            "is_partial": True,
        },
        "role_detection": {
            "is_commercial": effective_mode == "business",
            "detected_mode": detected_mode,
            "override_mode": override_mode,
            "effective_mode": effective_mode,
            "signals": {
                "has_reward_events": reward_events > 0,
                "reward_events": reward_events,
                "mining_events": mining_events,
                "high_activity": len(events) >= 500,
                "event_count": len(events),
            },
        },
        "by_source": by_source,
        "by_event_type": by_event_type,
        "activity_history": activity_history,
        "activity_years": activity_years,
        "portfolio_value_history": [],
        "yearly_asset_activity": {},
        "asset_balances": balances,
        "wallet_groups": _decorate_wallet_groups_with_sources(_load_wallet_groups(), by_source),
    }
    write_audit(trace_id=trace_id, action="dashboard.shell", payload={"total_events": len(events)})
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=[])


def _decorate_wallet_groups_with_sources(groups: list[dict[str, Any]], by_source: dict[str, int]) -> list[dict[str, Any]]:
    available_sources = set(by_source.keys())
    decorated: list[dict[str, Any]] = []
    for group in groups:
        item = dict(group)
        source_filters = _normalize_source_filters([str(v) for v in item.get("source_filters", [])])
        item["source_filters"] = source_filters
        item["source_event_count"] = (
            sum(int(by_source.get(source, 0)) for source in source_filters)
            if source_filters
            else sum(int(value) for value in by_source.values())
        )
        item["source_filters_missing"] = sorted([source for source in source_filters if source not in available_sources])
        decorated.append(item)
    return decorated


@router.get("/api/v1/dashboard/transaction-search", response_model=StandardResponse, tags=["dashboard"])
def dashboard_transaction_search(
    q: str | None = None,
    year: int | None = None,
    source: str | None = None,
    asset: str | None = None,
    wallet: str | None = None,
    event_type: str | None = None,
    tx_id: str | None = None,
    limit: int = 100,
) -> StandardResponse:
    trace_id = str(uuid4())
    runtime_fx = _runtime_usd_to_eur_rate()
    rows: list[dict[str, Any]] = []
    safe_limit = min(max(int(limit), 1), 500)
    for row in STORE.list_raw_events():
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if not _transaction_matches_filters(
            payload=payload,
            query=q,
            year=year,
            source=source,
            asset=asset,
            wallet=wallet,
            event_type=event_type,
            tx_id=tx_id,
        ):
            continue
        rows.append(_format_transaction_search_row(row=row, payload=payload, runtime_fx=runtime_fx))
        if len(rows) >= safe_limit:
            break
    write_audit(
        trace_id=trace_id,
        action="dashboard.transaction_search",
        payload={
            "q": q or "",
            "year": year,
            "source": source or "",
            "asset": asset or "",
            "wallet": _mask_identifier(wallet or ""),
            "event_type": event_type or "",
            "tx_id": _mask_identifier(tx_id or ""),
            "limit": safe_limit,
            "returned": len(rows),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"rows": rows, "count": len(rows), "limit": safe_limit},
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/portfolio/integrations", response_model=StandardResponse, tags=["dashboard"])
def portfolio_integrations() -> StandardResponse:
    trace_id = str(uuid4())
    events = STORE.list_raw_events()
    mode_overrides = load_integration_mode_overrides()
    buckets: dict[str, dict[str, Any]] = {}
    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source") or payload.get("source_name") or "unknown").strip() or "unknown"
        bucket = buckets.get(source)
        if bucket is None:
            bucket = {
                "integration_id": source,
                "event_count": 0,
                "assets": set(),
                "source_file_ids": set(),
                "first_timestamp_utc": "",
                "last_timestamp_utc": "",
            }
            buckets[source] = bucket

        bucket["event_count"] += 1
        asset = str(payload.get("asset") or "").strip().upper()
        if asset:
            bucket["assets"].add(asset)
        source_file_id = str(row.get("source_file_id") or "").strip()
        if source_file_id:
            bucket["source_file_ids"].add(source_file_id)
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "").strip()
        if ts:
            current_first = str(bucket.get("first_timestamp_utc") or "")
            current_last = str(bucket.get("last_timestamp_utc") or "")
            if not current_first or ts < current_first:
                bucket["first_timestamp_utc"] = ts
            if not current_last or ts > current_last:
                bucket["last_timestamp_utc"] = ts

    rows: list[dict[str, Any]] = []
    for bucket in buckets.values():
        integration_id = str(bucket["integration_id"])
        default_mode = infer_default_integration_mode(integration_id)
        mode = effective_integration_mode(integration_id, mode_overrides)
        override = mode_overrides.get(integration_id, {})
        rows.append(
            {
                "integration_id": integration_id,
                "mode": mode,
                "default_mode": default_mode,
                "mode_overridden": mode != default_mode,
                "mode_note": str(override.get("note", "")),
                "mode_updated_at_utc": str(override.get("updated_at_utc", "")),
                "event_count": int(bucket["event_count"]),
                "asset_count": len(bucket["assets"]),
                "source_file_count": len(bucket["source_file_ids"]),
                "assets_preview": sorted(list(bucket["assets"]))[:10],
                "first_timestamp_utc": str(bucket["first_timestamp_utc"]),
                "last_timestamp_utc": str(bucket["last_timestamp_utc"]),
            }
        )
    rows.sort(key=lambda item: int(item.get("event_count", 0)), reverse=True)

    write_audit(
        trace_id=trace_id,
        action="portfolio.integrations",
        payload={"count": len(rows), "event_count_total": len(events)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "count": len(rows),
            "event_count_total": len(events),
            "active_sources": active_sources_from_integrations(rows),
            "mode_catalog": [
                {"mode": "active", "label": "Aktiv fuer Steuerlauf"},
                {"mode": "reference", "label": "Nur Referenz/Kontrolle"},
                {"mode": "disabled", "label": "Deaktiviert"},
            ],
            "rows": rows,
        },
        errors=[],
        warnings=[],
    )


@router.post("/api/v1/portfolio/integrations/mode", response_model=StandardResponse, tags=["dashboard"])
def portfolio_integration_mode_update(payload: IntegrationModeUpdateRequest) -> StandardResponse:
    trace_id = str(uuid4())
    mode = normalize_integration_mode(payload.mode)
    if mode is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_integration_mode", "message": "mode muss active|reference|disabled sein."}],
            warnings=[],
        )
    try:
        entry = upsert_integration_mode(payload.integration_id, mode, payload.note or "")
    except ValueError as exc:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": str(exc), "message": "Integration-Modus konnte nicht gespeichert werden."}],
            warnings=[],
        )
    write_audit(
        trace_id=trace_id,
        action="portfolio.integration_mode.update",
        payload={"integration_id": entry["integration_id"], "mode": entry["mode"]},
    )
    return StandardResponse(trace_id=trace_id, status="success", data={**entry, "saved": True}, errors=[], warnings=[])


@router.get("/api/v1/portfolio/helium-legacy-transfers", response_model=StandardResponse, tags=["dashboard"])
def portfolio_helium_legacy_transfers() -> StandardResponse:
    trace_id = str(uuid4())
    overview = _build_helium_legacy_transfer_overview(STORE.list_raw_events())
    write_audit(
        trace_id=trace_id,
        action="portfolio.helium_legacy_transfers",
        payload={
            "transfer_count": overview["summary"]["transfer_count"],
            "counterparty_count": overview["summary"]["counterparty_count"],
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data=overview,
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/dashboard/wallet-snapshots", response_model=StandardResponse, tags=["dashboard"])
def dashboard_wallet_snapshots(
    scope: str = "wallet",
    entity_id: str = "",
    window_days: int = 365,
) -> StandardResponse:
    trace_id = str(uuid4())
    if scope not in {"wallet", "group"}:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_scope", "message": "scope muss wallet oder group sein"}],
            warnings=[],
        )
    points = _filter_wallet_snapshots(scope=scope, entity_id=entity_id.strip())
    if window_days > 0:
        cutoff = datetime.now(UTC) - timedelta(days=window_days)
        filtered: list[dict[str, Any]] = []
        for point in points:
            ts = _parse_iso_timestamp(str(point.get("timestamp_utc", "")))
            if ts is None or ts < cutoff:
                continue
            filtered.append(point)
        points = filtered

    perf_points: list[dict[str, str]] = []
    start_value = Decimal("0")
    end_value = Decimal("0")
    if points:
        start_value = _safe_decimal(points[0].get("total_estimated_usd", "0"))
        end_value = _safe_decimal(points[-1].get("total_estimated_usd", "0"))
        for point in points:
            value = _safe_decimal(point.get("total_estimated_usd", "0"))
            pnl_abs = value - start_value
            pnl_pct = (pnl_abs / start_value * Decimal("100")) if start_value > 0 else Decimal("0")
            perf_points.append(
                {
                    "timestamp_utc": str(point.get("timestamp_utc", "")),
                    "value_usd": value.normalize().to_eng_string() if value != 0 else "0",
                    "pnl_abs_usd": pnl_abs.normalize().to_eng_string() if pnl_abs != 0 else "0",
                    "pnl_pct": pnl_pct.normalize().to_eng_string() if start_value > 0 else "",
                }
            )

    pnl_abs_total = end_value - start_value
    pnl_pct_total = (pnl_abs_total / start_value * Decimal("100")) if start_value > 0 else Decimal("0")
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "scope": scope,
            "entity_id": entity_id.strip(),
            "window_days": window_days,
            "count": len(points),
            "points": points,
            "performance_points": perf_points,
            "summary": {
                "start_value_usd": start_value.normalize().to_eng_string() if start_value != 0 else "0",
                "end_value_usd": end_value.normalize().to_eng_string() if end_value != 0 else "0",
                "pnl_abs_usd": pnl_abs_total.normalize().to_eng_string() if pnl_abs_total != 0 else "0",
                "pnl_pct": pnl_pct_total.normalize().to_eng_string() if start_value > 0 else "",
            },
        },
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/dashboard/portfolio-set-history", response_model=StandardResponse, tags=["dashboard"])
def dashboard_portfolio_set_history(
    group_id: str,
    window_days: int = 365,
) -> StandardResponse:
    trace_id = str(uuid4())
    group = next((item for item in _load_wallet_groups() if str(item.get("group_id")) == str(group_id)), None)
    if group is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "group_not_found", "message": f"Wallet-Gruppe nicht gefunden: {group_id}"}],
            warnings=[],
        )

    source_filters = _normalize_source_filters([str(v) for v in group.get("source_filters", [])])
    all_events = STORE.list_raw_events()
    events: list[dict[str, Any]] = []
    if source_filters:
        wanted = set(source_filters)
        for row in all_events:
            payload = row.get("payload", {})
            if not isinstance(payload, dict):
                continue
            source = str(payload.get("source") or payload.get("source_name") or "unknown").strip() or "unknown"
            if source in wanted:
                events.append(row)
    else:
        events = all_events

    runtime_fx = _runtime_usd_to_eur_rate()
    ignored_mints = set(_load_ignored_tokens().keys())
    points = _build_portfolio_value_history(
        events,
        ignored_mints,
        runtime_fx,
        fx_rate_cache={},
        asset_usd_price_cache={},
        fx_lookup=_load_fx_lookup(),
    )
    if window_days > 0:
        cutoff = datetime.now(UTC) - timedelta(days=window_days)
        filtered_points: list[dict[str, Any]] = []
        for point in points:
            ts = _parse_iso_timestamp(f"{point.get('month', '')}-01T00:00:00+00:00")
            if ts is None or ts < cutoff:
                continue
            filtered_points.append(point)
        points = filtered_points

    values = [_safe_decimal(point.get("value_usd", "0")) for point in points]
    start_value = values[0] if values else Decimal("0")
    end_value = values[-1] if values else Decimal("0")
    pnl_abs_total = end_value - start_value
    pnl_pct_total = (pnl_abs_total / start_value * Decimal("100")) if start_value > 0 else Decimal("0")
    data = {
        "group": _decorate_wallet_groups_with_sources([group], _source_counts_for_events(all_events))[0],
        "source_filters": source_filters,
        "event_count": len(events),
        "window_days": window_days,
        "points": points,
        "summary": {
            "start_value_usd": start_value.normalize().to_eng_string() if start_value != 0 else "0",
            "end_value_usd": end_value.normalize().to_eng_string() if end_value != 0 else "0",
            "pnl_abs_usd": pnl_abs_total.normalize().to_eng_string() if pnl_abs_total != 0 else "0",
            "pnl_pct": pnl_pct_total.normalize().to_eng_string() if start_value > 0 else "",
        },
    }
    write_audit(
        trace_id=trace_id,
        action="dashboard.portfolio_set_history",
        payload={"group_id": group_id, "source_filter_count": len(source_filters), "event_count": len(events)},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=[])


def _source_counts_for_events(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source") or payload.get("source_name") or "unknown").strip() or "unknown"
        counts[source] = counts.get(source, 0) + 1
    return counts


@router.get("/api/v1/portfolio/lot-aging", response_model=StandardResponse, tags=["dashboard"])
def portfolio_lot_aging(as_of_utc: str | None = None, asset: str | None = None) -> StandardResponse:
    trace_id = str(uuid4())
    as_of = _parse_iso_timestamp(as_of_utc or "") or datetime.now(UTC)
    snapshot = build_open_lot_aging_snapshot(raw_events=STORE.list_raw_events(), as_of=as_of)
    asset_filter = str(asset or "").strip().upper()
    if asset_filter:
        snapshot["assets"] = [item for item in snapshot.get("assets", []) if str(item.get("asset", "")).upper() == asset_filter]
        snapshot["lot_rows"] = [item for item in snapshot.get("lot_rows", []) if str(item.get("asset", "")).upper() == asset_filter]
        snapshot["asset_count"] = len(snapshot["assets"])
        snapshot["lot_count"] = len(snapshot["lot_rows"])
    write_audit(
        trace_id=trace_id,
        action="portfolio.lot_aging",
        payload={"as_of_utc": as_of.isoformat(), "asset_filter": asset_filter, "lot_count": snapshot.get("lot_count", 0)},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=snapshot, errors=[], warnings=[])


def _build_helium_legacy_transfer_overview(events: list[dict[str, Any]]) -> dict[str, Any]:
    origin_wallets: set[str] = set()
    counterparties: dict[str, dict[str, Any]] = {}
    transfers: list[dict[str, Any]] = []
    sent_hnt = Decimal("0")
    received_hnt = Decimal("0")
    fees_hnt = Decimal("0")
    first_ts = ""
    last_ts = ""

    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if str(payload.get("source") or "") != "helium_legacy_cointracking":
            continue
        if str(payload.get("event_type") or "").lower() != "legacy_transfer":
            continue

        asset = str(payload.get("asset") or "").upper()
        if asset != "HNT":
            continue
        side = str(payload.get("side") or "").lower().strip()
        qty = _safe_decimal(payload.get("quantity"))
        fee = _safe_decimal(payload.get("fee"))
        timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        tx_id = str(payload.get("tx_id") or "")
        wallet = str(payload.get("wallet_address") or "")
        from_wallet = str(payload.get("from_wallet") or "")
        to_wallet = str(payload.get("to_wallet") or "")
        counterparty = str(payload.get("counterparty_wallet") or "")
        comment = str(payload.get("raw_comment") or "")

        if wallet:
            origin_wallets.add(wallet)
        if timestamp:
            if not first_ts or timestamp < first_ts:
                first_ts = timestamp
            if not last_ts or timestamp > last_ts:
                last_ts = timestamp
        if side == "out":
            sent_hnt += abs(qty)
            fees_hnt += abs(fee)
            direction = "out"
        elif side == "in":
            received_hnt += abs(qty)
            direction = "in"
        else:
            direction = "unknown"

        counterparty_key = counterparty or ("unknown_to" if direction == "out" else "unknown_from")
        bucket = counterparties.setdefault(
            counterparty_key,
            {
                "counterparty_wallet": counterparty_key,
                "sent_hnt": Decimal("0"),
                "received_hnt": Decimal("0"),
                "fees_hnt": Decimal("0"),
                "outbound_count": 0,
                "inbound_count": 0,
                "first_timestamp_utc": "",
                "last_timestamp_utc": "",
                "sample_tx_ids": [],
                "sample_comments": [],
            },
        )
        if direction == "out":
            bucket["sent_hnt"] += abs(qty)
            bucket["fees_hnt"] += abs(fee)
            bucket["outbound_count"] += 1
        elif direction == "in":
            bucket["received_hnt"] += abs(qty)
            bucket["inbound_count"] += 1
        if timestamp:
            if not bucket["first_timestamp_utc"] or timestamp < bucket["first_timestamp_utc"]:
                bucket["first_timestamp_utc"] = timestamp
            if not bucket["last_timestamp_utc"] or timestamp > bucket["last_timestamp_utc"]:
                bucket["last_timestamp_utc"] = timestamp
        if tx_id and len(bucket["sample_tx_ids"]) < 5:
            bucket["sample_tx_ids"].append(tx_id)
        if comment and len(bucket["sample_comments"]) < 3:
            bucket["sample_comments"].append(comment)

        transfers.append(
            {
                "timestamp_utc": timestamp,
                "direction": direction,
                "asset": asset,
                "quantity_hnt": _decimal_to_plain(abs(qty)),
                "fee_hnt": _decimal_to_plain(abs(fee)),
                "wallet_address": wallet,
                "from_wallet": from_wallet,
                "to_wallet": to_wallet,
                "counterparty_wallet": counterparty,
                "tx_id": tx_id,
                "comment": comment,
            }
        )

    counterparty_rows: list[dict[str, Any]] = []
    for bucket in counterparties.values():
        net_hnt = _safe_decimal(bucket["received_hnt"]) - _safe_decimal(bucket["sent_hnt"]) - _safe_decimal(bucket["fees_hnt"])
        counterparty_rows.append(
            {
                "counterparty_wallet": str(bucket["counterparty_wallet"]),
                "sent_hnt": _decimal_to_plain(bucket["sent_hnt"]),
                "received_hnt": _decimal_to_plain(bucket["received_hnt"]),
                "fees_hnt": _decimal_to_plain(bucket["fees_hnt"]),
                "net_hnt": _decimal_to_plain(net_hnt),
                "outbound_count": int(bucket["outbound_count"]),
                "inbound_count": int(bucket["inbound_count"]),
                "first_timestamp_utc": str(bucket["first_timestamp_utc"]),
                "last_timestamp_utc": str(bucket["last_timestamp_utc"]),
                "sample_tx_ids": list(bucket["sample_tx_ids"]),
                "sample_comments": list(bucket["sample_comments"]),
            }
        )
    counterparty_rows.sort(
        key=lambda item: (
            -abs(_safe_decimal(item["sent_hnt"]) + _safe_decimal(item["received_hnt"])),
            str(item["counterparty_wallet"]),
        )
    )
    transfers.sort(key=lambda item: str(item.get("timestamp_utc") or ""))

    return {
        "summary": {
            "origin_wallets": sorted(origin_wallets),
            "transfer_count": len(transfers),
            "counterparty_count": len(counterparty_rows),
            "outbound_count": sum(int(item["outbound_count"]) for item in counterparty_rows),
            "inbound_count": sum(int(item["inbound_count"]) for item in counterparty_rows),
            "sent_hnt": _decimal_to_plain(sent_hnt),
            "received_hnt": _decimal_to_plain(received_hnt),
            "fees_hnt": _decimal_to_plain(fees_hnt),
            "net_hnt": _decimal_to_plain(received_hnt - sent_hnt - fees_hnt),
            "first_timestamp_utc": first_ts,
            "last_timestamp_utc": last_ts,
        },
        "counterparties": counterparty_rows,
        "transfers": transfers,
    }


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _runtime_usd_to_eur_rate() -> Decimal:
    runtime = resolve_effective_runtime_config()
    raw_rate = runtime.get("runtime", {}).get("fx", {}).get("usd_to_eur")
    rate = _safe_decimal(raw_rate)
    return rate if rate > 0 else Decimal("1")


def _load_fx_lookup() -> _FxLookup:
    lookup: _FxLookup = {}
    for row in STORE.list_fx_rates():
        rate = _safe_decimal(row.get("rate"))
        if rate <= 0:
            continue
        key = (str(row.get("base_ccy") or "").upper(), str(row.get("quote_ccy") or "").upper())
        lookup.setdefault(key, []).append((str(row.get("rate_date") or ""), rate))
    return lookup


def _lookup_fx_rate(
    lookup: _FxLookup | None,
    *,
    rate_date: str,
    base_ccy: str,
    quote_ccy: str,
    on_or_before: bool,
) -> Decimal:
    if lookup is None or len(rate_date) < 10:
        return Decimal("0")
    rows = lookup.get((base_ccy.upper(), quote_ccy.upper()), [])
    if not rows:
        return Decimal("0")
    needle = rate_date[:10]
    if not on_or_before:
        idx = bisect_right(rows, (needle, Decimal("Infinity"))) - 1
        if idx >= 0 and rows[idx][0] == needle:
            return rows[idx][1]
        return Decimal("0")
    idx = bisect_right(rows, (needle, Decimal("Infinity"))) - 1
    return rows[idx][1] if idx >= 0 else Decimal("0")


def _estimate_event_values(
    payload: dict[str, Any],
    asset: str,
    quantity: Decimal,
    runtime_fx: Decimal,
    fx_rate_cache: dict[str, Decimal] | None = None,
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] | None = None,
    fx_lookup: _FxLookup | None = None,
) -> dict[str, Any]:
    eur_direct = _first_positive_decimal(
        payload,
        (
            "value_eur",
            "amount_eur",
            "income_eur",
            "proceeds_eur",
            "raw_value_eur",
            "raw_amount_eur",
            "raw_income_eur",
            "raw_proceeds_eur",
        ),
    )
    usd_direct = _first_positive_decimal(
        payload,
        (
            "value_usd",
            "amount_usd",
            "income_usd",
            "proceeds_usd",
            "raw_value_usd",
            "raw_amount_usd",
            "raw_income_usd",
            "raw_proceeds_usd",
            "usd_amount",
            "raw_usd_amount",
        ),
    )
    price_eur = _first_positive_decimal(payload, ("price_eur", "execution_price_eur"))
    price_usd = _first_positive_decimal(payload, ("price_usd", "usd_price", "execution_price_usd", "raw_usd_price"))
    price = _safe_decimal(payload.get("price"))
    quote_asset = _event_quote_asset(payload)
    qty_abs = abs(quantity)
    event_date = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")[:10]
    fx_rate = _safe_decimal(payload.get("fx_rate_usd_eur"))
    if fx_rate <= 0:
        fx_rate = _usd_to_eur_rate_for_date(
            event_date,
            runtime_fx,
            fx_rate_cache=fx_rate_cache,
            fx_lookup=fx_lookup,
        )

    eur = eur_direct
    usd = usd_direct
    if eur <= 0 and price_eur > 0 and qty_abs > 0:
        eur = price_eur * qty_abs
    if usd <= 0 and price_usd > 0 and qty_abs > 0:
        usd = price_usd * qty_abs
    asset_symbol = _asset_display_symbol(asset)
    quote_symbol = _asset_display_symbol(quote_asset) if quote_asset else quote_asset
    if usd <= 0 and _is_stable_asset_symbol(asset_symbol):
        usd = qty_abs
    if usd <= 0 and _is_stable_asset_symbol(quote_symbol) and price > 0 and qty_abs > 0:
        usd = price * qty_abs
    if usd <= 0 and qty_abs > 0:
        cached = _cached_asset_usd_price(
            asset=asset,
            rate_date=event_date,
            asset_usd_price_cache=asset_usd_price_cache,
            fx_lookup=fx_lookup,
        )
        if cached <= 0:
            cached = _cached_asset_usd_price_on_or_before(
                asset=asset,
                rate_date=event_date,
                asset_usd_price_cache=asset_usd_price_cache,
                fx_lookup=fx_lookup,
            )
        if cached > 0:
            usd = cached * qty_abs
    if eur <= 0 and usd > 0 and fx_rate > 0:
        eur = usd * fx_rate
    if usd <= 0 and eur > 0 and fx_rate > 0:
        usd = eur / fx_rate

    return {
        "usd_abs": abs(usd),
        "eur_abs": abs(eur),
        "priced": usd > 0 or eur > 0,
    }


def _usd_to_eur_rate_for_date(
    rate_date: str,
    fallback_rate: Decimal,
    fx_rate_cache: dict[str, Decimal] | None = None,
    fx_lookup: _FxLookup | None = None,
) -> Decimal:
    if len(rate_date) >= 10:
        key = rate_date[:10]
        if fx_rate_cache is not None and key in fx_rate_cache:
            return fx_rate_cache[key]
        lookup_rate = _lookup_fx_rate(fx_lookup, rate_date=key, base_ccy="USD", quote_ccy="EUR", on_or_before=True)
        if lookup_rate > 0:
            if fx_rate_cache is not None:
                fx_rate_cache[key] = lookup_rate
            return lookup_rate
        row = STORE.get_fx_rate_on_or_before(rate_date=rate_date[:10], base_ccy="USD", quote_ccy="EUR")
        if row:
            rate = _safe_decimal(row.get("rate"))
            if rate > 0:
                if fx_rate_cache is not None:
                    fx_rate_cache[key] = rate
                return rate
    fallback = fallback_rate if fallback_rate > 0 else Decimal("1")
    if len(rate_date) >= 10 and fx_rate_cache is not None:
        fx_rate_cache[rate_date[:10]] = fallback
    return fallback


def _dashboard_event_quantity(payload: dict[str, Any]) -> Decimal:
    normalized_helium_qty = _heliumgeek_display_quantity(payload)
    if normalized_helium_qty > 0:
        return normalized_helium_qty
    return _safe_decimal(payload.get("quantity"))


def _heliumgeek_display_quantity(payload: dict[str, Any]) -> Decimal:
    if str(payload.get("source", "")).lower().strip() != "heliumgeek":
        return Decimal("0")
    asset = str(payload.get("asset") or "").upper().strip()
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0")
    token_fields = (
        ("IOT Token", "IOT Tokens"),
        ("MOBILE Token", "MOBILE Tokens"),
    )
    for token_field, amount_field in token_fields:
        if str(raw_row.get(token_field, "")).upper().strip() == asset:
            return abs(_safe_decimal(raw_row.get(amount_field)))
    return Decimal("0")


def _cached_asset_usd_price(
    asset: str,
    rate_date: str,
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] | None = None,
    fx_lookup: _FxLookup | None = None,
) -> Decimal:
    if not asset or len(rate_date) < 10:
        return Decimal("0")
    cache_key = ("exact", asset.upper(), rate_date[:10])
    if asset_usd_price_cache is not None and cache_key in asset_usd_price_cache:
        return asset_usd_price_cache[cache_key]
    candidates = [asset.upper()]
    meta = _resolve_token_display(asset)
    symbol = str(meta.get("symbol") or "").upper().strip()
    if _is_stable_asset_symbol(symbol) or _is_stable_asset_symbol(candidates[0]):
        if asset_usd_price_cache is not None:
            asset_usd_price_cache[cache_key] = Decimal("1")
        return Decimal("1")
    if symbol and symbol not in candidates:
        candidates.append(symbol)
    for candidate in candidates:
        lookup_rate = _lookup_fx_rate(fx_lookup, rate_date=rate_date[:10], base_ccy=candidate, quote_ccy="USD", on_or_before=False)
        if lookup_rate > 0:
            if asset_usd_price_cache is not None:
                asset_usd_price_cache[cache_key] = lookup_rate
            return lookup_rate
        row = STORE.get_fx_rate(rate_date=rate_date, base_ccy=candidate, quote_ccy="USD")
        if row:
            rate = _safe_decimal(row.get("rate"))
            if rate > 0:
                if asset_usd_price_cache is not None:
                    asset_usd_price_cache[cache_key] = rate
                return rate
    if asset_usd_price_cache is not None:
        asset_usd_price_cache[cache_key] = Decimal("0")
    return Decimal("0")


def _cached_asset_usd_price_on_or_before(
    asset: str,
    rate_date: str,
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] | None = None,
    fx_lookup: _FxLookup | None = None,
) -> Decimal:
    if not asset or len(rate_date) < 10:
        return Decimal("0")
    normalized = asset.upper()
    cache_key = ("on_or_before", normalized, rate_date[:10])
    if asset_usd_price_cache is not None and cache_key in asset_usd_price_cache:
        return asset_usd_price_cache[cache_key]
    candidates = [normalized]
    meta = _resolve_token_display(normalized)
    symbol = str(meta.get("symbol") or "").upper().strip()
    if _is_stable_asset_symbol(normalized) or _is_stable_asset_symbol(symbol):
        if asset_usd_price_cache is not None:
            asset_usd_price_cache[cache_key] = Decimal("1")
        return Decimal("1")
    if symbol and symbol not in candidates:
        candidates.append(symbol)
    for candidate in candidates:
        lookup_rate = _lookup_fx_rate(fx_lookup, rate_date=rate_date[:10], base_ccy=candidate, quote_ccy="USD", on_or_before=True)
        if lookup_rate > 0:
            if asset_usd_price_cache is not None:
                asset_usd_price_cache[cache_key] = lookup_rate
            return lookup_rate
        row = STORE.get_fx_rate_on_or_before(rate_date=rate_date, base_ccy=candidate, quote_ccy="USD")
        if row:
            rate = _safe_decimal(row.get("rate"))
            if rate > 0:
                if asset_usd_price_cache is not None:
                    asset_usd_price_cache[cache_key] = rate
                return rate
    if asset_usd_price_cache is not None:
        asset_usd_price_cache[cache_key] = Decimal("0")
    return Decimal("0")


def _build_portfolio_value_history(
    events: list[dict[str, Any]],
    ignored_mints: set[str],
    runtime_fx: Decimal,
    fx_rate_cache: dict[str, Decimal] | None = None,
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] | None = None,
    fx_lookup: _FxLookup | None = None,
) -> list[dict[str, Any]]:
    timeline: list[tuple[str, dict[str, Any]]] = []
    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if len(ts_raw) < 10:
            continue
        asset = str(payload.get("asset") or "").upper().strip()
        if not asset or _normalize_mint(asset) in ignored_mints:
            continue
        timeline.append((ts_raw, payload))
    timeline.sort(key=lambda item: item[0])

    month_end_days: dict[str, str] = {}
    for ts_raw, _payload in timeline:
        day = ts_raw[:10]
        month_end_days[day[:7]] = day

    points: list[dict[str, Any]] = []
    running_balances: dict[str, Decimal] = {}
    month_marks = set(month_end_days.values())
    day_payloads: dict[str, list[dict[str, Any]]] = {}
    for ts_raw, payload in timeline:
        day_payloads.setdefault(ts_raw[:10], []).append(payload)

    for day, payloads in sorted(day_payloads.items(), key=lambda item: item[0]):
        for payload in payloads:
            asset = str(payload.get("asset") or "").upper().strip()
            qty = _dashboard_event_quantity(payload)
            side = str(payload.get("side") or "").lower().strip()
            if side == "in":
                running_balances[asset] = running_balances.get(asset, Decimal("0")) + abs(qty)
            elif side == "out":
                running_balances[asset] = running_balances.get(asset, Decimal("0")) - abs(qty)
            else:
                running_balances[asset] = running_balances.get(asset, Decimal("0")) + qty
        if day not in month_marks:
            continue
        value_usd = Decimal("0")
        priced_assets = 0
        unpriced_assets = 0
        for balance_asset, balance_qty in running_balances.items():
            if balance_qty == 0:
                continue
            price = _cached_asset_usd_price_on_or_before(
                balance_asset,
                day,
                asset_usd_price_cache=asset_usd_price_cache,
                fx_lookup=fx_lookup,
            )
            if price > 0:
                value_usd += balance_qty * price
                priced_assets += 1
            else:
                unpriced_assets += 1
        fx_rate = _usd_to_eur_rate_for_date(day, runtime_fx, fx_rate_cache=fx_rate_cache, fx_lookup=fx_lookup)
        value_eur = value_usd * fx_rate if fx_rate > 0 else value_usd
        points.append(
            {
                "date": day,
                "year": int(day[:4]),
                "value_usd": _decimal_to_plain(value_usd),
                "value_eur": _decimal_to_plain(value_eur),
                "priced_assets": priced_assets,
                "unpriced_assets": unpriced_assets,
            }
        )
        month_marks.remove(day)
    return points


def _first_positive_decimal(payload: dict[str, Any], keys: tuple[str, ...]) -> Decimal:
    lookup = {str(key).lower(): value for key, value in payload.items()}
    raw_row = payload.get("raw_row")
    if isinstance(raw_row, dict):
        lookup.update({str(key).lower().replace(" ", "_"): value for key, value in raw_row.items()})
        lookup.update({str(key).lower(): value for key, value in raw_row.items()})
    for key in keys:
        value = lookup.get(key.lower())
        parsed = _safe_decimal(value)
        if parsed > 0:
            return parsed
    return Decimal("0")


def _event_quote_asset(payload: dict[str, Any]) -> str:
    lookup = {str(key).lower(): value for key, value in payload.items()}
    raw_row = payload.get("raw_row")
    if isinstance(raw_row, dict):
        lookup.update({str(key).lower().replace(" ", "_"): value for key, value in raw_row.items()})
        lookup.update({str(key).lower(): value for key, value in raw_row.items()})
    for key in ("quote_asset", "quote", "quoteasset", "quote_asset_symbol", "currency", "market"):
        raw = str(lookup.get(key, "") or "").upper().strip()
        if raw:
            if raw.endswith("USDT"):
                return "USDT"
            if raw.endswith("USDC"):
                return "USDC"
            return raw
    return ""


def _is_trading_volume_event(event_type: str) -> bool:
    normalized = event_type.lower().strip()
    return any(token in normalized for token in ("trade", "swap", "buy", "sell", "fill", "convert"))


def _requires_dashboard_valuation(payload: dict[str, Any]) -> bool:
    return _is_dashboard_value_event(payload) or _is_trading_volume_event(str(payload.get("event_type") or ""))


def _is_dashboard_value_event(payload: dict[str, Any]) -> bool:
    event_type = str(payload.get("event_type") or "").lower().strip()
    if _is_trading_volume_event(event_type):
        return True
    if any(token in event_type for token in ("reward", "interest", "staking", "mining", "income", "airdrop")):
        return True
    if event_type in {"deposit", "withdrawal", "token_transfer", "sol_transfer", "fee", ""}:
        return False
    defi_label = str(payload.get("defi_label") or "").lower().strip()
    if defi_label == "swap":
        return True
    return False


def _dashboard_event_category(payload: dict[str, Any]) -> str:
    event_type = str(payload.get("event_type") or "").lower().strip()
    if "derivative" in event_type:
        return "derivate"
    if event_type in {"deposit", "withdrawal", "token_transfer", "sol_transfer"}:
        return "transfer"
    if "auto-balancing" in event_type or "non-taxable" in event_type:
        return "abgleich"
    if "fee" in event_type:
        return "gebuehr"
    if any(token in event_type for token in ("reward", "interest", "staking", "mining", "income", "airdrop", "bounty")):
        return "reward_einkunft"
    if _is_trading_volume_event(event_type):
        return "trade_swap"
    if not event_type or event_type == "unknown":
        return "unbekannt"
    return event_type.replace("_", " ")


def _accumulate_yearly_event_breakdown(
    yearly_event_buckets: dict[tuple[int, str], dict[str, Any]],
    year: int,
    payload: dict[str, Any],
    value: dict[str, Any],
    value_counts: bool,
) -> None:
    category = _dashboard_event_category(payload)
    key = (year, category)
    bucket = yearly_event_buckets.setdefault(
        key,
        {
            "year": year,
            "category": category,
            "events": 0,
            "value_usd": Decimal("0"),
            "value_eur": Decimal("0"),
            "trading_value_usd": Decimal("0"),
            "trading_value_eur": Decimal("0"),
            "priced_events": 0,
            "unpriced_events": 0,
            "valuation_required_events": 0,
            "deduped_values": {},
        },
    )
    bucket["events"] += 1
    if value_counts:
        bucket["value_usd"] += _safe_decimal(value.get("usd_abs"))
        bucket["value_eur"] += _safe_decimal(value.get("eur_abs"))
    if _is_trading_volume_event(str(payload.get("event_type") or "")):
        bucket["trading_value_usd"] += _safe_decimal(value.get("usd_abs"))
        bucket["trading_value_eur"] += _safe_decimal(value.get("eur_abs"))
    if value_counts or _is_trading_volume_event(str(payload.get("event_type") or "")):
        _accumulate_deduped_bucket_value(bucket, payload, year, value)
    if _requires_dashboard_valuation(payload):
        bucket["valuation_required_events"] += 1
        if value.get("priced"):
            bucket["priced_events"] += 1
        else:
            bucket["unpriced_events"] += 1


def _accumulate_yearly_source_breakdown(
    yearly_source_buckets: dict[tuple[int, str], dict[str, Any]],
    year: int,
    payload: dict[str, Any],
    value: dict[str, Any],
    value_counts: bool,
) -> None:
    source = str(payload.get("source") or "unknown").strip() or "unknown"
    key = (year, source)
    bucket = yearly_source_buckets.setdefault(
        key,
        {
            "year": year,
            "source": source,
            "events": 0,
            "value_usd": Decimal("0"),
            "value_eur": Decimal("0"),
            "trading_value_usd": Decimal("0"),
            "trading_value_eur": Decimal("0"),
            "priced_events": 0,
            "unpriced_events": 0,
            "valuation_required_events": 0,
            "deduped_values": {},
        },
    )
    bucket["events"] += 1
    if value_counts:
        bucket["value_usd"] += _safe_decimal(value.get("usd_abs"))
        bucket["value_eur"] += _safe_decimal(value.get("eur_abs"))
    if _is_trading_volume_event(str(payload.get("event_type") or "")):
        bucket["trading_value_usd"] += _safe_decimal(value.get("usd_abs"))
        bucket["trading_value_eur"] += _safe_decimal(value.get("eur_abs"))
    if value_counts or _is_trading_volume_event(str(payload.get("event_type") or "")):
        _accumulate_deduped_bucket_value(bucket, payload, year, value)
    if _requires_dashboard_valuation(payload):
        bucket["valuation_required_events"] += 1
        if value.get("priced"):
            bucket["priced_events"] += 1
        else:
            bucket["unpriced_events"] += 1


def _accumulate_yearly_deduped_value(
    yearly_deduped_values: dict[int, dict[str, Any]],
    year: int,
    payload: dict[str, Any],
    value: dict[str, Any],
    event_type: str,
) -> None:
    tx_key = _dashboard_economic_tx_key(payload, year)
    bucket = yearly_deduped_values.setdefault(year, {})
    current = bucket.get(tx_key)
    usd = _safe_decimal(value.get("usd_abs"))
    eur = _safe_decimal(value.get("eur_abs"))
    trading = _is_trading_volume_event(event_type)
    if current is None:
        bucket[tx_key] = {
            "usd": usd,
            "eur": eur,
            "trading_usd": usd if trading else Decimal("0"),
            "trading_eur": eur if trading else Decimal("0"),
        }
        return
    if usd > current["usd"]:
        current["usd"] = usd
    if eur > current["eur"]:
        current["eur"] = eur
    if trading and usd > current["trading_usd"]:
        current["trading_usd"] = usd
    if trading and eur > current["trading_eur"]:
        current["trading_eur"] = eur


def _accumulate_deduped_bucket_value(bucket: dict[str, Any], payload: dict[str, Any], year: int, value: dict[str, Any]) -> None:
    deduped_values = bucket.setdefault("deduped_values", {})
    if not isinstance(deduped_values, dict):
        return
    tx_key = _dashboard_economic_tx_key(payload, year)
    usd = _safe_decimal(value.get("usd_abs"))
    eur = _safe_decimal(value.get("eur_abs"))
    trading = _is_trading_volume_event(str(payload.get("event_type") or ""))
    current = deduped_values.get(tx_key)
    if current is None:
        deduped_values[tx_key] = {
            "usd": usd,
            "eur": eur,
            "trading_usd": usd if trading else Decimal("0"),
            "trading_eur": eur if trading else Decimal("0"),
        }
        return
    if usd > current["usd"]:
        current["usd"] = usd
    if eur > current["eur"]:
        current["eur"] = eur
    if trading and usd > current["trading_usd"]:
        current["trading_usd"] = usd
    if trading and eur > current["trading_eur"]:
        current["trading_eur"] = eur


def _deduped_bucket_totals(bucket: dict[str, Any]) -> dict[str, Decimal]:
    deduped_values = bucket.get("deduped_values")
    if not isinstance(deduped_values, dict) or not deduped_values:
        return {
            "value_usd": _safe_decimal(bucket.get("value_usd")),
            "value_eur": _safe_decimal(bucket.get("value_eur")),
            "trading_value_usd": _safe_decimal(bucket.get("trading_value_usd")),
            "trading_value_eur": _safe_decimal(bucket.get("trading_value_eur")),
        }
    return {
        "value_usd": sum((_safe_decimal(item.get("usd")) for item in deduped_values.values()), Decimal("0")),
        "value_eur": sum((_safe_decimal(item.get("eur")) for item in deduped_values.values()), Decimal("0")),
        "trading_value_usd": sum((_safe_decimal(item.get("trading_usd")) for item in deduped_values.values()), Decimal("0")),
        "trading_value_eur": sum((_safe_decimal(item.get("trading_eur")) for item in deduped_values.values()), Decimal("0")),
    }


def _dashboard_economic_tx_key(payload: dict[str, Any], year: int) -> str:
    raw_row = payload.get("raw_row")
    if isinstance(raw_row, dict):
        for key in ("Trx. ID (optional)", "TXID", "transaction_hash", "Order No.", "Trade ID"):
            raw = str(raw_row.get(key) or "").strip()
            if raw:
                return f"{year}:{raw}"
    for key in ("tx_id", "signature", "transaction_hash", "order_id", "trade_id"):
        raw = str(payload.get(key) or "").strip()
        if raw:
            if raw.startswith("blockpit-") and raw.rsplit(":", 1)[-1] in {"in", "out", "fee"}:
                raw = raw.rsplit(":", 1)[0]
            return f"{year}:{raw}"
    timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "").strip()
    source = str(payload.get("source") or "").strip()
    event_type = str(payload.get("event_type") or "").strip()
    return f"{year}:{source}:{event_type}:{timestamp}:{payload.get('asset')}:{payload.get('quantity')}"


def _format_yearly_asset_activity(
    buckets: dict[tuple[int, str, str], dict[str, Any]],
    yearly_deduped_values: dict[int, dict[str, Any]] | None = None,
    yearly_event_buckets: dict[tuple[int, str], dict[str, Any]] | None = None,
    yearly_source_buckets: dict[tuple[int, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    totals: dict[int, dict[str, Any]] = {}
    for (_, asset, source), bucket in buckets.items():
        year = int(bucket["year"])
        meta = _resolve_token_display(asset)
        rows.append(
            {
                "year": year,
                "asset": asset,
                "source": source,
                "symbol": str(meta["symbol"]),
                "name": str(meta["name"]),
                "events": int(bucket["events"]),
                "quantity_in": _decimal_to_plain(bucket["quantity_in"]),
                "quantity_out": _decimal_to_plain(bucket["quantity_out"]),
                "quantity_net": _decimal_to_plain(bucket["quantity_net"]),
                "quantity_abs": _decimal_to_plain(bucket["quantity_abs"]),
                "value_usd": _decimal_to_plain(bucket["value_usd"]),
                "value_eur": _decimal_to_plain(bucket["value_eur"]),
                "avg_usd_to_eur": _decimal_to_plain(
                    bucket["value_eur"] / bucket["value_usd"] if bucket["value_usd"] > 0 else Decimal("0")
                ),
                "trading_value_usd": _decimal_to_plain(bucket["trading_value_usd"]),
                "trading_value_eur": _decimal_to_plain(bucket["trading_value_eur"]),
                "priced_events": int(bucket["priced_events"]),
                "unpriced_events": int(bucket["unpriced_events"]),
                "valuation_required_events": int(bucket["valuation_required_events"]),
                "priced_coverage_ratio": _decimal_to_plain(
                    Decimal(int(bucket["priced_events"])) / Decimal(int(bucket["valuation_required_events"]))
                    if int(bucket["valuation_required_events"]) > 0
                    else Decimal("0")
                ),
            }
        )
        total = totals.setdefault(
            year,
            {
                "year": year,
                "events": 0,
                "value_usd": Decimal("0"),
                "value_eur": Decimal("0"),
                "trading_value_usd": Decimal("0"),
                "trading_value_eur": Decimal("0"),
                "quantity_abs": Decimal("0"),
            },
        )
        total["events"] += int(bucket["events"])
        total["value_usd"] += bucket["value_usd"]
        total["value_eur"] += bucket["value_eur"]
        total["trading_value_usd"] += bucket["trading_value_usd"]
        total["trading_value_eur"] += bucket["trading_value_eur"]
        total["quantity_abs"] += bucket["quantity_abs"]

    if yearly_deduped_values:
        for year, tx_values in yearly_deduped_values.items():
            total = totals.setdefault(
                year,
                {
                    "year": year,
                    "events": 0,
                    "value_usd": Decimal("0"),
                    "value_eur": Decimal("0"),
                    "trading_value_usd": Decimal("0"),
                    "trading_value_eur": Decimal("0"),
                    "quantity_abs": Decimal("0"),
                },
            )
            total["value_usd"] = sum((_safe_decimal(item.get("usd")) for item in tx_values.values()), Decimal("0"))
            total["value_eur"] = sum((_safe_decimal(item.get("eur")) for item in tx_values.values()), Decimal("0"))
            total["trading_value_usd"] = sum((_safe_decimal(item.get("trading_usd")) for item in tx_values.values()), Decimal("0"))
            total["trading_value_eur"] = sum((_safe_decimal(item.get("trading_eur")) for item in tx_values.values()), Decimal("0"))

    rows.sort(key=lambda item: (int(item["year"]), -_safe_decimal(item["value_eur"]), -int(item["events"])))
    yearly_totals = [
        {
            "year": year,
            "events": total["events"],
            "value_usd": _decimal_to_plain(total["value_usd"]),
            "value_eur": _decimal_to_plain(total["value_eur"]),
            "avg_usd_to_eur": _decimal_to_plain(
                total["value_eur"] / total["value_usd"] if total["value_usd"] > 0 else Decimal("0")
            ),
            "trading_value_usd": _decimal_to_plain(total["trading_value_usd"]),
            "trading_value_eur": _decimal_to_plain(total["trading_value_eur"]),
            "quantity_abs": _decimal_to_plain(total["quantity_abs"]),
        }
        for year, total in sorted(totals.items(), key=lambda item: item[0])
    ]
    return {
        "years": sorted(totals.keys()),
        "rows": rows,
        "totals_by_year": yearly_totals,
        "event_breakdown": _format_yearly_event_breakdown(yearly_event_buckets or {}),
        "source_breakdown": _format_yearly_source_breakdown(yearly_source_buckets or {}),
    }


def _format_yearly_event_breakdown(buckets: dict[tuple[int, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (_, category), bucket in buckets.items():
        deduped = _deduped_bucket_totals(bucket)
        rows.append(
            {
                "year": int(bucket["year"]),
                "category": category,
                "events": int(bucket["events"]),
                "value_usd": _decimal_to_plain(deduped["value_usd"]),
                "value_eur": _decimal_to_plain(deduped["value_eur"]),
                "avg_usd_to_eur": _decimal_to_plain(
                    deduped["value_eur"] / deduped["value_usd"] if deduped["value_usd"] > 0 else Decimal("0")
                ),
                "trading_value_usd": _decimal_to_plain(deduped["trading_value_usd"]),
                "trading_value_eur": _decimal_to_plain(deduped["trading_value_eur"]),
                "priced_events": int(bucket["priced_events"]),
                "unpriced_events": int(bucket["unpriced_events"]),
                "valuation_required_events": int(bucket["valuation_required_events"]),
            }
        )
    rows.sort(key=lambda item: (int(item["year"]), -int(item["events"]), str(item["category"])))
    return rows


def _format_yearly_source_breakdown(buckets: dict[tuple[int, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (_, source), bucket in buckets.items():
        deduped = _deduped_bucket_totals(bucket)
        rows.append(
            {
                "year": int(bucket["year"]),
                "source": source,
                "events": int(bucket["events"]),
                "value_usd": _decimal_to_plain(deduped["value_usd"]),
                "value_eur": _decimal_to_plain(deduped["value_eur"]),
                "avg_usd_to_eur": _decimal_to_plain(
                    deduped["value_eur"] / deduped["value_usd"] if deduped["value_usd"] > 0 else Decimal("0")
                ),
                "trading_value_usd": _decimal_to_plain(deduped["trading_value_usd"]),
                "trading_value_eur": _decimal_to_plain(deduped["trading_value_eur"]),
                "priced_events": int(bucket["priced_events"]),
                "unpriced_events": int(bucket["unpriced_events"]),
                "valuation_required_events": int(bucket["valuation_required_events"]),
            }
        )
    rows.sort(key=lambda item: (int(item["year"]), -int(item["events"]), str(item["source"])))
    return rows


def _transaction_matches_filters(
    payload: dict[str, Any],
    query: str | None,
    year: int | None,
    source: str | None,
    asset: str | None,
    wallet: str | None,
    event_type: str | None,
    tx_id: str | None,
) -> bool:
    if year is not None and _extract_year(str(payload.get("timestamp_utc") or payload.get("timestamp") or "")) != int(year):
        return False
    if source and str(source).lower().strip() not in str(payload.get("source") or "").lower():
        return False
    if asset:
        needle = str(asset).lower().strip()
        meta = _resolve_token_display(str(payload.get("asset") or ""))
        haystack = f"{payload.get('asset', '')} {meta.get('symbol', '')} {meta.get('name', '')}".lower()
        if needle not in haystack:
            return False
    if event_type and str(event_type).lower().strip() not in str(payload.get("event_type") or "").lower():
        return False
    if tx_id:
        needle = str(tx_id).lower().strip()
        haystack = f"{payload.get('tx_id', '')} {payload.get('signature', '')}".lower()
        if needle not in haystack:
            return False
    if wallet:
        needle = str(wallet).lower().strip()
        if not any(needle in str(value).lower() for value in _wallet_identifiers(payload)):
            return False
    if query:
        needle = str(query).lower().strip()
        if needle and needle not in _transaction_search_text(payload).lower():
            return False
    return True


def _format_transaction_search_row(row: dict[str, Any], payload: dict[str, Any], runtime_fx: Decimal) -> dict[str, Any]:
    asset = str(payload.get("asset") or "").upper()
    meta = _resolve_token_display(asset)
    qty = _dashboard_event_quantity(payload)
    value = _estimate_event_values(payload=payload, asset=asset, quantity=qty, runtime_fx=runtime_fx)
    raw_row = payload.get("raw_row")
    return {
        "unique_event_id": str(row.get("unique_event_id") or ""),
        "source_file_id": str(row.get("source_file_id") or ""),
        "row_index": int(row.get("row_index") or 0),
        "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
        "year": _extract_year(str(payload.get("timestamp_utc") or payload.get("timestamp") or "")),
        "source": str(payload.get("source") or "unknown"),
        "event_type": str(payload.get("event_type") or "unknown"),
        "category": _dashboard_event_category(payload),
        "asset": asset,
        "symbol": str(meta.get("symbol") or asset),
        "name": str(meta.get("name") or ""),
        "quantity": _decimal_to_plain(qty),
        "side": str(payload.get("side") or ""),
        "wallet_address": str(payload.get("wallet_address") or ""),
        "from_wallet": str(payload.get("from_wallet") or ""),
        "to_wallet": str(payload.get("to_wallet") or ""),
        "counterparty_wallet": str(payload.get("counterparty_wallet") or ""),
        "address": str(payload.get("address") or ""),
        "tx_id": str(payload.get("tx_id") or payload.get("signature") or ""),
        "fee": str(payload.get("fee") or ""),
        "fee_asset": str(payload.get("fee_asset") or ""),
        "value_usd": _decimal_to_plain(value["usd_abs"]),
        "value_eur": _decimal_to_plain(value["eur_abs"]),
        "priced": bool(value["priced"]),
        "defi_label": str(payload.get("defi_label") or ""),
        "tax_category": str(payload.get("tax_category") or ""),
        "raw_summary": _summarize_raw_row(raw_row),
    }


def _transaction_search_text(payload: dict[str, Any]) -> str:
    meta = _resolve_token_display(str(payload.get("asset") or ""))
    parts = [
        payload.get("source"),
        payload.get("event_type"),
        payload.get("asset"),
        meta.get("symbol"),
        meta.get("name"),
        payload.get("tx_id"),
        payload.get("signature"),
        payload.get("wallet_address"),
        payload.get("from_wallet"),
        payload.get("to_wallet"),
        payload.get("counterparty_wallet"),
        payload.get("address"),
        payload.get("gateway_address"),
        payload.get("gateway_name"),
        payload.get("tax_category"),
        payload.get("raw_comment"),
    ]
    raw_row = payload.get("raw_row")
    if isinstance(raw_row, dict):
        parts.extend(str(value) for value in raw_row.values())
    return " ".join(str(part or "") for part in parts)


def _wallet_identifiers(payload: dict[str, Any]) -> list[str]:
    values = [
        payload.get("wallet_address"),
        payload.get("from_wallet"),
        payload.get("to_wallet"),
        payload.get("counterparty_wallet"),
        payload.get("address"),
        payload.get("gateway_address"),
    ]
    raw_row = payload.get("raw_row")
    if isinstance(raw_row, dict):
        for key, value in raw_row.items():
            lowered = str(key).lower()
            if "wallet" in lowered or "address" in lowered or "account" in lowered:
                values.append(value)
    return [str(value) for value in values if value]


def _summarize_raw_row(raw_row: Any) -> dict[str, str]:
    if not isinstance(raw_row, dict):
        return {}
    summary: dict[str, str] = {}
    for key, value in raw_row.items():
        if value in (None, "", [], {}):
            continue
        summary[str(key)] = str(value)
        if len(summary) >= 12:
            break
    return summary


def _mask_identifier(value: str) -> str:
    raw = str(value or "").strip()
    if len(raw) <= 12:
        return raw
    return f"{raw[:6]}...{raw[-4:]}"


def _extract_year(ts_raw: str) -> int | None:
    value = str(ts_raw).strip()
    if len(value) < 4:
        return None
    candidate = value[:4]
    if not candidate.isdigit():
        return None
    year = int(candidate)
    if year < 2009 or year > 2100:
        return None
    return year


def _normalize_mint(value: str) -> str:
    return str(value or "").strip().upper()


def _asset_display_symbol(asset: str) -> str:
    normalized = _normalize_mint(asset)
    if not normalized:
        return ""
    return str(_resolve_token_display(normalized).get("symbol") or normalized).upper().strip()


def _is_stable_asset_symbol(symbol: str) -> bool:
    return str(symbol or "").upper().strip() in _STABLE_ASSET_SYMBOLS


def _load_token_aliases() -> dict[str, dict[str, str]]:
    row = STORE.get_setting("runtime.token_aliases")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    aliases: dict[str, dict[str, str]] = {}
    for mint_raw, payload in raw.items():
        mint = _normalize_mint(str(mint_raw))
        if not mint or not isinstance(payload, dict):
            continue
        symbol = str(payload.get("symbol", "")).strip().upper()
        name = str(payload.get("name", "")).strip()
        notes = str(payload.get("notes", "")).strip()
        if not symbol or not name:
            continue
        aliases[mint] = {"symbol": symbol, "name": name, "notes": notes}
    return aliases


def _load_ignored_tokens() -> dict[str, dict[str, str]]:
    row = STORE.get_setting("runtime.ignored_tokens")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    ignored: dict[str, dict[str, str]] = {}
    for mint_raw, payload in raw.items():
        mint = _normalize_mint(str(mint_raw))
        if not mint or not isinstance(payload, dict):
            continue
        reason = str(payload.get("reason", "")).strip()
        updated_at_utc = str(payload.get("updated_at_utc", "")).strip()
        if not reason:
            continue
        ignored[mint] = {"reason": reason, "updated_at_utc": updated_at_utc}
    return ignored


def _is_ignored_token(asset: str) -> bool:
    mint = _normalize_mint(asset)
    if not mint:
        return False
    ignored = _load_ignored_tokens()
    return mint in ignored


def _resolve_token_display(asset: str) -> dict[str, Any]:
    mint = _normalize_mint(asset)
    aliases = _load_token_aliases()
    aliased = aliases.get(mint)
    if aliased is not None:
        return {
            "asset": mint,
            "symbol": aliased["symbol"],
            "name": aliased["name"],
            "is_known": True,
            "display_source": "alias",
        }
    meta = resolve_token_metadata(mint)
    return {
        "asset": mint,
        "symbol": str(meta.get("symbol", mint)),
        "name": str(meta.get("name", "Unbekanntes Token")),
        "is_known": bool(meta.get("is_known", False)),
        "display_source": "known" if bool(meta.get("is_known", False)) else "unknown",
    }


def _is_spam_candidate(asset: str, qty: Decimal, known: bool) -> bool:
    if known:
        return False
    abs_qty = abs(qty)
    # Heuristik: unbekannt + extrem klein oder extrem groß => Spam/Dust-Kandidat.
    if abs_qty == 0:
        return False
    if abs_qty < Decimal("0.01"):
        return True
    if abs_qty > Decimal("1000000"):
        return True
    return False


def _decorate_token_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decorated: list[dict[str, Any]] = []
    ignored_tokens = _load_ignored_tokens()
    for row in rows:
        if not isinstance(row, dict):
            continue
        asset = str(row.get("asset") or "")
        qty = _safe_decimal(row.get("quantity", "0"))
        meta = _resolve_token_display(asset)
        item = dict(row)
        item["symbol"] = str(meta["symbol"])
        item["name"] = str(meta["name"])
        item["display_source"] = str(meta["display_source"])
        ignored_meta = ignored_tokens.get(_normalize_mint(asset))
        item["ignored"] = "true" if ignored_meta is not None else "false"
        item["ignored_reason"] = str(ignored_meta.get("reason", "")) if ignored_meta is not None else ""
        item["spam_candidate"] = "true" if _is_spam_candidate(asset=asset, qty=qty, known=bool(meta["is_known"])) else "false"
        item["quantity"] = _decimal_to_plain(qty)
        decorated.append(item)
    return decorated


def _parse_iso_timestamp(value: str) -> datetime | None:
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _load_dashboard_role_override() -> str:
    row = STORE.get_setting("runtime.dashboard.role_override")
    if row is None:
        return "auto"
    try:
        value = row.get("value_json", "\"auto\"")
        mode = str(json.loads(str(value)))
    except Exception:
        return "auto"
    if mode not in {"auto", "private", "business"}:
        return "auto"
    return mode
