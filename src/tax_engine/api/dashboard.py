from __future__ import annotations

import json
import subprocess
from bisect import bisect_right
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
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
from tax_engine.fx.service import FallbackFxResolver
from tax_engine.ingestion import write_audit
from tax_engine.ingestion.store import STORE
from tax_engine.integrations import (
    active_sources_from_integrations,
    effective_integration_mode,
    filter_events_for_processing,
    infer_default_integration_mode,
    load_integration_mode_overrides,
    normalize_integration_mode,
    upsert_integration_mode,
)
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides
from tax_engine.queue.service import (
    attach_cached_usd_prices_to_reward_events,
    attach_cached_usd_prices_to_swap_in_events,
    attach_reference_usd_value_anchors,
    drop_exact_pionex_duplicate_events,
    drop_solscan_duplicates_when_solana_rpc_is_active,
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

ROOT_DIR = Path(__file__).resolve().parents[3]
PLATFORM_LEDGER_DATE = "2026-05-09"
_STABLE_ASSET_SYMBOLS = {"USD", "USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD"}
_FxLookup = dict[tuple[str, str], list[tuple[str, Decimal]]]
AI_READONLY_QUEUE_DIR = ROOT_DIR / "var" / "ai_readonly_queue"


def _list_effective_raw_events() -> list[dict[str, Any]]:
    events, _summary = apply_review_actions(STORE.list_raw_events())
    events, _override_count = apply_tax_event_overrides(events)
    return events


def _list_processing_effective_raw_events() -> list[dict[str, Any]]:
    raw_events = STORE.list_raw_events()
    events, _integration_filter_summary = filter_events_for_processing(raw_events, {"include_reference_sources": False})
    events, _pionex_duplicate_summary = drop_exact_pionex_duplicate_events(events)
    events, _solscan_duplicate_summary = drop_solscan_duplicates_when_solana_rpc_is_active(events)
    events, _valuation_anchor_summary = attach_reference_usd_value_anchors(events, raw_events)
    events, _reward_price_summary = attach_cached_usd_prices_to_reward_events(events)
    events, _swap_price_summary = attach_cached_usd_prices_to_swap_in_events(events)
    events, _review_action_summary = apply_review_actions(events)
    events, _override_count = apply_tax_event_overrides(events)
    events, _fx_summary = FallbackFxResolver(fallback_rate="1").enrich_events_with_fx(events)
    return events


def _read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _read_jsonl_tail(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    for line in lines[-max(limit, 0) :]:
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _tail_text(path: Path, max_lines: int) -> list[str]:
    if not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-max(max_lines, 0) :]
    except Exception:
        return []


def _count_json_files(path: Path) -> int:
    try:
        return len(list(path.glob("*.json")))
    except Exception:
        return 0


def _list_queue_tasks(path: Path, limit: int = 20) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        files = sorted(path.glob("*.json"), key=lambda item: item.name)
    except Exception:
        return rows
    for item in files[:limit]:
        payload = _read_json_file(item)
        rows.append(
            {
                "task_id": payload.get("task_id") or item.stem,
                "title": payload.get("title") or payload.get("task_id") or item.stem,
                "path": str(item),
                "created_at_utc": payload.get("created_at_utc", ""),
                "last_error": payload.get("last_error", ""),
            }
        )
    return rows


def _systemd_service_status(service_name: str) -> dict[str, Any]:
    result: dict[str, Any] = {"service": service_name, "active_state": "unknown", "sub_state": "", "main_pid": ""}
    try:
        completed = subprocess.run(
            ["systemctl", "show", service_name, "--property=ActiveState,SubState,MainPID,ExecMainStatus"],
            text=True,
            capture_output=True,
            timeout=3,
            check=False,
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    if completed.returncode != 0:
        result["error"] = (completed.stderr or completed.stdout or "").strip()[:500]
        return result
    for line in completed.stdout.splitlines():
        key, _, value = line.partition("=")
        if key == "ActiveState":
            result["active_state"] = value
        elif key == "SubState":
            result["sub_state"] = value
        elif key == "MainPID":
            result["main_pid"] = value
        elif key == "ExecMainStatus":
            result["exec_main_status"] = value
    return result


@router.get("/api/v1/ai-readonly-queue/status", response_model=StandardResponse, tags=["dashboard"])
def ai_readonly_queue_status() -> StandardResponse:
    trace_id = str(uuid4())
    status_path = AI_READONLY_QUEUE_DIR / "status.json"
    results_path = AI_READONLY_QUEUE_DIR / "results.jsonl"
    log_path = AI_READONLY_QUEUE_DIR / "runner.log"
    systemd_log_path = AI_READONLY_QUEUE_DIR / "systemd.log"
    status_file = _read_json_file(status_path)
    counts = {
        "pending": _count_json_files(AI_READONLY_QUEUE_DIR / "pending"),
        "running": _count_json_files(AI_READONLY_QUEUE_DIR / "running"),
        "done": _count_json_files(AI_READONLY_QUEUE_DIR / "done"),
        "failed": _count_json_files(AI_READONLY_QUEUE_DIR / "failed"),
    }
    recent_results = _read_jsonl_tail(results_path, 10)
    warnings: list[dict[str, str]] = []
    if not AI_READONLY_QUEUE_DIR.exists():
        warnings.append({"code": "ai_queue_missing", "message": "AI readonly queue directory does not exist."})
    service = _systemd_service_status("steuerreport-ai-readonly-queue.service")
    data = {
        "queue_dir": str(AI_READONLY_QUEUE_DIR),
        "status_path": str(status_path),
        "results_jsonl": str(results_path),
        "runner_log": str(log_path),
        "systemd_log": str(systemd_log_path),
        "service": service,
        "status_file": status_file,
        "counts": counts,
        "current_task": status_file.get("current_task", ""),
        "updated_at_utc": status_file.get("updated_at_utc", ""),
        "started_at_utc": status_file.get("started_at_utc", ""),
        "pending_tasks": _list_queue_tasks(AI_READONLY_QUEUE_DIR / "pending", 20),
        "running_tasks": _list_queue_tasks(AI_READONLY_QUEUE_DIR / "running", 10),
        "failed_tasks": _list_queue_tasks(AI_READONLY_QUEUE_DIR / "failed", 10),
        "recent_results": recent_results,
        "log_tail": _tail_text(log_path, 30),
    }
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=warnings)


def _platform_residual_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("platform") or "").lower(), str(row.get("asset") or "").upper())


def _split_platform_resolution_rows(
    rows: list[dict[str, Any]],
    residual_review: dict[str, Any],
) -> dict[str, Any]:
    residuals = residual_review.get("residuals") or []
    documented_index = {
        _platform_residual_key(item): item
        for item in residuals
        if isinstance(item, dict)
        and str(item.get("review_classification") or "").startswith("documented_")
    }
    active_rows: list[dict[str, Any]] = []
    documented_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        residual = documented_index.get(_platform_residual_key(row))
        if residual:
            merged = dict(row)
            merged["review_classification"] = residual.get("review_classification", "")
            merged["review_reason"] = residual.get("reason", "")
            merged["review_recommendation"] = residual.get("recommendation", "")
            merged["supporting_report"] = residual.get("supporting_report", "")
            documented_rows.append(merged)
        else:
            active_rows.append(row)
    return {
        "active_rows": active_rows,
        "documented_rows": documented_rows,
        "active_count": len(active_rows),
        "documented_count": len(documented_rows),
    }


@router.get("/api/v1/platform-ledger/status", response_model=StandardResponse, tags=["dashboard"])
def platform_ledger_status() -> StandardResponse:
    trace_id = str(uuid4())
    summary = _read_json_file(ROOT_DIR / "var" / f"platform_ledger_summary_{PLATFORM_LEDGER_DATE}.json")
    transfers = _read_json_file(ROOT_DIR / "var" / f"platform_transfer_groups_{PLATFORM_LEDGER_DATE}.json")
    transfer_candidates = _read_json_file(ROOT_DIR / "var" / f"platform_transfer_candidates_{PLATFORM_LEDGER_DATE}.json")
    break_resolution = _read_json_file(ROOT_DIR / "var" / f"platform_break_resolution_plan_{PLATFORM_LEDGER_DATE}.json")
    simulation = _read_json_file(ROOT_DIR / "var" / f"platform_balance_simulation_{PLATFORM_LEDGER_DATE}.json")
    ai_review = _read_json_file(ROOT_DIR / "var" / f"ai_platform_reconciliation_review_{PLATFORM_LEDGER_DATE}.json")
    residual_review = _read_json_file(ROOT_DIR / "var" / f"platform_residual_review_audit_{PLATFORM_LEDGER_DATE}.json")
    split_resolution = _split_platform_resolution_rows(break_resolution.get("rows") or [], residual_review)
    files = {
        "ledger_jsonl": str(ROOT_DIR / "var" / f"platform_ledger_{PLATFORM_LEDGER_DATE}.jsonl"),
        "ledger_csv": str(ROOT_DIR / "var" / f"platform_ledger_{PLATFORM_LEDGER_DATE}.csv"),
        "summary_doc": str(ROOT_DIR / "docs" / f"130_PLATFORM_LEDGER_EXPORT_{PLATFORM_LEDGER_DATE}.md"),
        "transfers_doc": str(ROOT_DIR / "docs" / f"131_PLATFORM_TRANSFER_GROUPS_{PLATFORM_LEDGER_DATE}.md"),
        "simulation_doc": str(ROOT_DIR / "docs" / f"132_PLATFORM_BALANCE_SIMULATION_{PLATFORM_LEDGER_DATE}.md"),
        "ai_doc": str(ROOT_DIR / "docs" / f"133_AI_PLATFORM_RECONCILIATION_REVIEW_{PLATFORM_LEDGER_DATE}.md"),
        "transfer_candidates_doc": str(ROOT_DIR / "docs" / f"134_PLATFORM_TRANSFER_CANDIDATES_{PLATFORM_LEDGER_DATE}.md"),
        "break_resolution_doc": str(ROOT_DIR / "docs" / f"135_PLATFORM_BREAK_RESOLUTION_PLAN_{PLATFORM_LEDGER_DATE}.md"),
        "residual_review_doc": str(ROOT_DIR / "docs" / f"166_PLATFORM_RESIDUAL_REVIEW_AUDIT_{PLATFORM_LEDGER_DATE}.md"),
    }
    warnings = []
    if not summary:
        warnings.append({"code": "platform_ledger_missing", "message": "Platform ledger summary not found. Run scripts/build_platform_ledger.py."})
    if not simulation:
        warnings.append({"code": "platform_simulation_missing", "message": "Platform balance simulation not found. Run scripts/simulate_platform_balances.py."})
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "generated_for": PLATFORM_LEDGER_DATE,
            "files": files,
            "summary": summary,
            "transfers": {
                "generated_at_utc": transfers.get("generated_at_utc", ""),
                "ledger_rows": transfers.get("ledger_rows", 0),
                "transfer_group_count": transfers.get("transfer_group_count", 0),
                "matched_ledger_row_count": transfers.get("matched_ledger_row_count", 0),
                "unmatched_transfer_like_count": transfers.get("unmatched_transfer_like_count", 0),
                "groups": (transfers.get("groups") or [])[:50],
                "unmatched_transfer_like": (transfers.get("unmatched_transfer_like") or [])[:100],
            },
            "simulation": {
                "generated_at_utc": simulation.get("generated_at_utc", ""),
                "ledger_rows": simulation.get("ledger_rows", 0),
                "platform_asset_count": simulation.get("platform_asset_count", 0),
                "negative_platform_asset_count": simulation.get("negative_platform_asset_count", 0),
                "negative_assets": (simulation.get("negative_assets") or [])[:80],
                "first_timeline_breaks": (simulation.get("first_timeline_breaks") or [])[:120],
            },
            "transfer_candidates": {
                "generated_at_utc": transfer_candidates.get("generated_at_utc", ""),
                "transfer_like_rows": transfer_candidates.get("transfer_like_rows", 0),
                "candidate_count": transfer_candidates.get("candidate_count", 0),
                "confidence_counts": transfer_candidates.get("confidence_counts", {}),
                "match_type_counts": transfer_candidates.get("match_type_counts", {}),
                "break_link_count": transfer_candidates.get("break_link_count", 0),
                "candidates": (transfer_candidates.get("candidates") or [])[:120],
                "negative_break_links": (transfer_candidates.get("negative_break_links") or [])[:80],
            },
            "break_resolution": {
                "generated_at_utc": break_resolution.get("generated_at_utc", ""),
                "break_count": break_resolution.get("break_count", 0),
                "status_counts": break_resolution.get("status_counts", {}),
                "priority_counts": break_resolution.get("priority_counts", {}),
                "active_blocker_count": split_resolution["active_count"],
                "documented_residual_count": split_resolution["documented_count"],
                "active_rows": split_resolution["active_rows"][:80],
                "documented_rows": split_resolution["documented_rows"][:80],
                "rows": (break_resolution.get("rows") or [])[:80],
            },
            "residual_review": {
                "generated_at_utc": residual_review.get("generated_at_utc", ""),
                "residual_count": residual_review.get("residual_count", 0),
                "status_counts": residual_review.get("status_counts", {}),
                "decision": residual_review.get("decision", {}),
                "residuals": (residual_review.get("residuals") or [])[:80],
            },
            "ai_review": {
                "generated_at_utc": ai_review.get("generated_at_utc", ""),
                "status": ai_review.get("status", "missing" if not ai_review else ""),
                "model": ai_review.get("model", ""),
                "base_url": ai_review.get("base_url", ""),
                "hypotheses": (ai_review.get("hypotheses") or [])[:30],
                "error": ai_review.get("error", ""),
            },
        },
        warnings=warnings,
    )

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
    events = _list_effective_raw_events()

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
    token_aliases = _load_token_aliases()
    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source") or "unknown")
        event_type = str(payload.get("event_type") or "unknown")
        by_source[source] = by_source.get(source, 0) + 1
        by_event_type[event_type] = by_event_type.get(event_type, 0) + 1

        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if _counts_dashboard_activity(payload):
            day = ts_raw[:10] if len(ts_raw) >= 10 else "unknown"
            by_day[day] = by_day.get(day, 0) + 1
            year = _extract_year(ts_raw)
            if year is not None:
                by_year[year] = by_year.get(year, 0) + 1
        else:
            year = _extract_year(ts_raw)

        side = str(payload.get("side") or "").lower()
        raw_asset = str(payload.get("asset") or "").upper()
        if _normalize_mint(raw_asset) in ignored_mints:
            continue
        asset = _asset_canonical_symbol(raw_asset, token_aliases)
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
    events = _list_effective_raw_events()
    by_source: dict[str, int] = {}
    by_event_type: dict[str, int] = {}
    by_day: dict[str, int] = {}
    by_year: dict[int, int] = {}
    asset_balances: dict[str, Decimal] = {}
    reward_events = 0
    mining_events = 0
    ignored_mints = set(_load_ignored_tokens().keys())
    token_aliases = _load_token_aliases()

    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source") or "unknown")
        event_type = str(payload.get("event_type") or "unknown")
        by_source[source] = by_source.get(source, 0) + 1
        by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if _counts_dashboard_activity(payload):
            day = ts_raw[:10] if len(ts_raw) >= 10 else "unknown"
            by_day[day] = by_day.get(day, 0) + 1
            year = _extract_year(ts_raw)
            if year is not None:
                by_year[year] = by_year.get(year, 0) + 1
        else:
            year = _extract_year(ts_raw)
        raw_asset = str(payload.get("asset") or "").upper()
        asset = _asset_canonical_symbol(raw_asset, token_aliases)
        if asset and _normalize_mint(raw_asset) not in ignored_mints:
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


@router.get("/api/v1/dashboard/yearly-activity", response_model=StandardResponse, tags=["dashboard"])
def dashboard_yearly_activity(year: int | None = None) -> StandardResponse:
    trace_id = str(uuid4())
    events = _list_effective_raw_events()
    activity = _build_yearly_asset_activity(events, year=year)
    write_audit(
        trace_id=trace_id,
        action="dashboard.yearly_activity",
        payload={
            "event_count": len(events),
            "year": year,
            "row_count": len(activity.get("rows", [])),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "year": year,
            "yearly_asset_activity": activity,
        },
        errors=[],
        warnings=[],
    )


@router.get("/api/v1/dashboard/portfolio-history", response_model=StandardResponse, tags=["dashboard"])
def dashboard_portfolio_history(
    window_days: int = 3650,
    year: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    interval: str = "auto",
    max_points: int = 240,
) -> StandardResponse:
    trace_id = str(uuid4())
    events = _list_effective_raw_events()
    runtime_fx = _runtime_usd_to_eur_rate()
    ignored_mints = set(_load_ignored_tokens().keys())
    safe_max_points = min(max(int(max_points), 20), 2000)
    interval_normalized = _normalize_portfolio_history_interval(interval)
    mark_from = f"{year}-01-01" if year is not None else None
    mark_to = f"{year}-12-31" if year is not None else None
    if window_days > 0:
        cutoff = (datetime.now(UTC) - timedelta(days=window_days)).date().isoformat()
        mark_from = max(mark_from, cutoff) if mark_from else cutoff
    if from_date:
        mark_from = max(mark_from, str(from_date)[:10]) if mark_from else str(from_date)[:10]
    if to_date:
        mark_to = min(mark_to, str(to_date)[:10]) if mark_to else str(to_date)[:10]
    points = _build_portfolio_value_history(
        events,
        ignored_mints,
        runtime_fx,
        fx_rate_cache={},
        asset_usd_price_cache={},
        fx_lookup=_load_fx_lookup(),
        interval=interval_normalized,
        max_points=safe_max_points,
        mark_from=mark_from,
        mark_to=mark_to,
    )
    if year is not None:
        points = [point for point in points if int(point.get("year") or 0) == year]
    if from_date:
        points = [point for point in points if str(point.get("date") or "") >= str(from_date)[:10]]
    if to_date:
        points = [point for point in points if str(point.get("date") or "") <= str(to_date)[:10]]
    if window_days > 0:
        cutoff_ts = datetime.now(UTC) - timedelta(days=window_days)
        filtered_points: list[dict[str, Any]] = []
        for point in points:
            ts = _parse_iso_timestamp(f"{point.get('date', '')}T00:00:00+00:00")
            if ts is None or ts < cutoff_ts:
                continue
            filtered_points.append(point)
        points = filtered_points

    values = [_safe_decimal(point.get("value_usd", "0")) for point in points]
    start_value = values[0] if values else Decimal("0")
    end_value = values[-1] if values else Decimal("0")
    pnl_abs_total = end_value - start_value
    pnl_pct_total = (pnl_abs_total / start_value * Decimal("100")) if start_value > 0 else Decimal("0")
    write_audit(
        trace_id=trace_id,
        action="dashboard.portfolio_history",
        payload={
            "event_count": len(events),
            "window_days": window_days,
            "year": year,
            "from_date": from_date,
            "to_date": to_date,
            "interval": interval_normalized,
            "max_points": safe_max_points,
            "point_count": len(points),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "window_days": window_days,
            "year": year,
            "from_date": from_date,
            "to_date": to_date,
            "interval": interval_normalized,
            "max_points": safe_max_points,
            "event_count": len(events),
            "portfolio_value_history": points,
            "summary": {
                "start_value_usd": _decimal_to_plain(start_value),
                "end_value_usd": _decimal_to_plain(end_value),
                "pnl_abs_usd": _decimal_to_plain(pnl_abs_total),
                "pnl_pct": _decimal_to_plain(pnl_pct_total) if start_value > 0 else "",
            },
        },
        errors=[],
        warnings=[],
    )


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
    for row in _list_effective_raw_events():
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
    events = _list_effective_raw_events()
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
    overview = _build_helium_legacy_transfer_overview(_list_effective_raw_events())
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
    year: int | None = None,
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
    if year is not None:
        points = [
            point
            for point in points
            if _extract_year(str(point.get("timestamp_utc") or "")) == year
        ]
    elif window_days > 0:
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
            "year": year,
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
    year: int | None = None,
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
    all_events = _list_effective_raw_events()
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
    if year is not None:
        points = [point for point in points if int(point.get("year") or 0) == year]
    elif window_days > 0:
        cutoff = datetime.now(UTC) - timedelta(days=window_days)
        filtered_points: list[dict[str, Any]] = []
        for point in points:
            ts = _parse_iso_timestamp(f"{point.get('date', '')}T00:00:00+00:00")
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
        "year": year,
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
        payload={"group_id": group_id, "source_filter_count": len(source_filters), "event_count": len(events), "year": year},
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
def portfolio_lot_aging(as_of_utc: str | None = None, asset: str | None = None, domain: str | None = None) -> StandardResponse:
    trace_id = str(uuid4())
    as_of = _parse_iso_timestamp(as_of_utc or "") or datetime.now(UTC)
    snapshot = build_open_lot_aging_snapshot(
        raw_events=_list_processing_effective_raw_events(),
        as_of=as_of,
        transfer_matches=STORE.list_transfer_matches(),
    )
    asset_filter = str(asset or "").strip().upper()
    domain_filter = str(domain or "").strip().lower()
    if asset_filter:
        snapshot["assets"] = [item for item in snapshot.get("assets", []) if str(item.get("asset", "")).upper() == asset_filter]
        snapshot["lot_rows"] = [item for item in snapshot.get("lot_rows", []) if str(item.get("asset", "")).upper() == asset_filter]
        snapshot["private_assets"] = [item for item in snapshot.get("private_assets", []) if str(item.get("asset", "")).upper() == asset_filter]
        snapshot["private_lot_rows"] = [
            item for item in snapshot.get("private_lot_rows", []) if str(item.get("asset", "")).upper() == asset_filter
        ]
    if domain_filter in {"business", "private"}:
        snapshot["lot_rows"] = [item for item in snapshot.get("lot_rows", []) if str(item.get("domain", "")).lower() == domain_filter]
        snapshot["assets"] = _summarize_lot_aging_rows(snapshot["lot_rows"])
        snapshot["asset_count"] = len(snapshot["assets"])
        snapshot["lot_count"] = len(snapshot["lot_rows"])
    snapshot["private_asset_count"] = len(snapshot.get("private_assets", []))
    snapshot["private_lot_count"] = len(snapshot.get("private_lot_rows", []))
    write_audit(
        trace_id=trace_id,
        action="portfolio.lot_aging",
        payload={
            "as_of_utc": as_of.isoformat(),
            "asset_filter": asset_filter,
            "domain_filter": domain_filter,
            "lot_count": snapshot.get("lot_count", 0),
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=snapshot, errors=[], warnings=[])


def _summarize_lot_aging_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        asset = str(row.get("asset") or "").upper().strip()
        if not asset:
            continue
        item = grouped.setdefault(
            asset,
            {
                "asset": asset,
                "total_qty": Decimal("0"),
                "qty_exempt": Decimal("0"),
                "qty_taxable": Decimal("0"),
                "lot_count": 0,
                "oldest_hold_days": 0,
                "qty_business": Decimal("0"),
                "qty_private": Decimal("0"),
            },
        )
        qty = _safe_decimal(row.get("qty"))
        item["total_qty"] += qty
        if str(row.get("tax_status") or "").lower() == "exempt":
            item["qty_exempt"] += qty
        else:
            item["qty_taxable"] += qty
        if str(row.get("domain") or "").lower() == "business":
            item["qty_business"] += qty
        else:
            item["qty_private"] += qty
        item["lot_count"] += 1
        item["oldest_hold_days"] = max(int(item["oldest_hold_days"]), int(_safe_decimal(row.get("hold_days"))))
    result = []
    for item in grouped.values():
        result.append(
            {
                "asset": item["asset"],
                "total_qty": item["total_qty"].to_eng_string(),
                "qty_exempt": item["qty_exempt"].to_eng_string(),
                "qty_taxable": item["qty_taxable"].to_eng_string(),
                "lot_count": item["lot_count"],
                "oldest_hold_days": item["oldest_hold_days"],
                "qty_business": item["qty_business"].to_eng_string(),
                "qty_private": item["qty_private"].to_eng_string(),
            }
        )
    return sorted(result, key=lambda item: str(item["asset"]))


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
    if eur <= 0 and asset_symbol == "EUR":
        eur = qty_abs
    if eur <= 0 and quote_symbol == "EUR" and price > 0 and qty_abs > 0:
        eur = price * qty_abs
    if usd <= 0 and _is_stable_asset_symbol(asset_symbol):
        usd = qty_abs
    if usd <= 0 and _is_stable_asset_symbol(quote_symbol) and price > 0 and qty_abs > 0:
        usd = price * qty_abs
    if usd <= 0 and eur <= 0:
        raw_usd, raw_eur = _raw_market_total_event_values(
            payload=payload,
            rate_date=event_date,
            fx_rate=fx_rate,
            asset_usd_price_cache=asset_usd_price_cache,
            fx_lookup=fx_lookup,
        )
        usd = raw_usd
        eur = raw_eur
    if usd <= 0 and eur <= 0:
        raw_usd, raw_eur = _raw_blockpit_counterparty_event_values(
            payload=payload,
            asset=asset,
            rate_date=event_date,
            fx_rate=fx_rate,
            asset_usd_price_cache=asset_usd_price_cache,
            fx_lookup=fx_lookup,
        )
        usd = raw_usd
        eur = raw_eur
    if usd <= 0 and eur <= 0:
        raw_usd = _raw_indexed_transfer_usd_value(payload=payload)
        if raw_usd > 0:
            usd = raw_usd
    if usd <= 0 and qty_abs > 0:
        usd = _counterparty_swap_usd_value(
            payload=payload,
            asset=asset,
            rate_date=event_date,
            asset_usd_price_cache=asset_usd_price_cache,
            fx_lookup=fx_lookup,
        )
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


def _raw_indexed_transfer_usd_value(*, payload: dict[str, Any]) -> Decimal:
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0")
    for key in ("value_usd_sum", "value_usd", "amount_usd", "usd_value"):
        value = _safe_decimal(raw_row.get(key))
        if value > 0:
            return value
    raw_transfers = raw_row.get("raw_transfers")
    if not isinstance(raw_transfers, list):
        return Decimal("0")
    asset_address = str(payload.get("asset_address") or raw_row.get("token_address") or "").strip().lower()
    side = str(payload.get("side") or "").strip().lower()
    best = Decimal("0")
    for item in raw_transfers:
        if not isinstance(item, dict):
            continue
        if side and str(item.get("flow") or "").strip().lower() != side:
            continue
        if asset_address and str(item.get("token_address") or "").strip().lower() != asset_address:
            continue
        value = _safe_decimal(item.get("value_usd"))
        if value > best:
            best = value
    return best


def _raw_market_total_event_values(
    *,
    payload: dict[str, Any],
    rate_date: str,
    fx_rate: Decimal,
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] | None = None,
    fx_lookup: _FxLookup | None = None,
) -> tuple[Decimal, Decimal]:
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0"), Decimal("0")
    source = str(payload.get("source") or "").lower().strip()
    if source not in {"binance", "binance_api"}:
        return Decimal("0"), Decimal("0")
    market = _raw_lookup(raw_row, "market")
    quote_asset = _split_market_quote_asset(market)
    total = _safe_decimal(_raw_lookup(raw_row, "total"))
    if not quote_asset or total <= 0:
        return Decimal("0"), Decimal("0")
    if quote_asset == "EUR":
        eur = total
        usd = eur / fx_rate if fx_rate > 0 else Decimal("0")
        return usd, eur
    if _is_stable_asset_symbol(quote_asset):
        return total, Decimal("0")
    quote_price = _cached_asset_usd_price(
        asset=quote_asset,
        rate_date=rate_date,
        asset_usd_price_cache=asset_usd_price_cache,
        fx_lookup=fx_lookup,
    )
    if quote_price <= 0:
        quote_price = _cached_asset_usd_price_on_or_before(
            asset=quote_asset,
            rate_date=rate_date,
            asset_usd_price_cache=asset_usd_price_cache,
            fx_lookup=fx_lookup,
        )
    return (total * quote_price, Decimal("0")) if quote_price > 0 else (Decimal("0"), Decimal("0"))


def _raw_blockpit_counterparty_event_values(
    *,
    payload: dict[str, Any],
    asset: str,
    rate_date: str,
    fx_rate: Decimal,
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] | None = None,
    fx_lookup: _FxLookup | None = None,
) -> tuple[Decimal, Decimal]:
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0"), Decimal("0")
    source = str(payload.get("source") or "").lower().strip()
    if source != "blockpit":
        return Decimal("0"), Decimal("0")
    current_asset = _asset_display_symbol(asset)
    incoming_asset = _asset_display_symbol(_raw_lookup(raw_row, "Incoming Asset"))
    outgoing_asset = _asset_display_symbol(_raw_lookup(raw_row, "Outgoing Asset"))
    incoming_amount = abs(_safe_decimal(_raw_lookup(raw_row, "Incoming Amount")))
    outgoing_amount = abs(_safe_decimal(_raw_lookup(raw_row, "Outgoing Amount")))
    fee_asset = _asset_display_symbol(_raw_lookup(raw_row, "Fee Asset"))
    fee_amount = abs(_safe_decimal(_raw_lookup(raw_row, "Fee Amount")))

    candidates: list[tuple[str, Decimal]] = []
    if incoming_asset and incoming_amount > 0 and incoming_asset != current_asset:
        candidates.append((incoming_asset, incoming_amount))
    if outgoing_asset and outgoing_amount > 0 and outgoing_asset != current_asset:
        candidates.append((outgoing_asset, outgoing_amount))
    if fee_asset and fee_amount > 0 and fee_asset != current_asset:
        candidates.append((fee_asset, fee_amount))

    for counter_asset, counter_amount in candidates:
        if counter_asset == "EUR":
            eur = counter_amount
            usd = eur / fx_rate if fx_rate > 0 else Decimal("0")
            return usd, eur
        if counter_asset == "USD" or _is_stable_asset_symbol(counter_asset):
            return counter_amount, Decimal("0")

    for counter_asset, counter_amount in candidates:
        price = _cached_asset_usd_price(
            asset=counter_asset,
            rate_date=rate_date,
            asset_usd_price_cache=asset_usd_price_cache,
            fx_lookup=fx_lookup,
        )
        if price <= 0:
            price = _cached_asset_usd_price_on_or_before(
                asset=counter_asset,
                rate_date=rate_date,
                asset_usd_price_cache=asset_usd_price_cache,
                fx_lookup=fx_lookup,
            )
        if price > 0:
            return counter_amount * price, Decimal("0")

    return Decimal("0"), Decimal("0")


def _raw_lookup(raw_row: dict[str, Any], key: str) -> Any:
    normalized = key.lower().replace(" ", "_")
    for raw_key, value in raw_row.items():
        candidate = str(raw_key).lower().replace(" ", "_")
        if candidate == normalized:
            return value
    return ""


def _split_market_quote_asset(market: Any) -> str:
    value = str(market or "").upper().strip().replace("-", "").replace("_", "").replace("/", "")
    if not value:
        return ""
    for quote in (
        "BUSD",
        "USDT",
        "USDC",
        "FDUSD",
        "TUSD",
        "DAI",
        "EUR",
        "USD",
        "BTC",
        "ETH",
        "BNB",
    ):
        if value.endswith(quote) and len(value) > len(quote):
            return quote
    return ""


def _counterparty_swap_usd_value(
    payload: dict[str, Any],
    *,
    asset: str,
    rate_date: str,
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] | None = None,
    fx_lookup: _FxLookup | None = None,
) -> Decimal:
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0")
    if not raw_row.get("jupiter_aggregated"):
        return Decimal("0")
    current_asset = str(asset or "").upper().strip()
    from_asset = str(raw_row.get("from_asset") or "").upper().strip()
    to_asset = str(raw_row.get("to_asset") or "").upper().strip()
    from_qty = _safe_decimal(raw_row.get("from_quantity"))
    to_qty = _safe_decimal(raw_row.get("to_quantity"))
    if not current_asset or len(rate_date) < 10:
        return Decimal("0")
    counter_asset = ""
    counter_qty = Decimal("0")
    if current_asset == from_asset and to_asset and to_qty > 0:
        counter_asset = to_asset
        counter_qty = to_qty
    elif current_asset == to_asset and from_asset and from_qty > 0:
        counter_asset = from_asset
        counter_qty = from_qty
    if not counter_asset or counter_qty <= 0:
        return Decimal("0")
    counter_symbol = _asset_display_symbol(counter_asset)
    if _is_stable_asset_symbol(counter_symbol) or _is_stable_asset_symbol(counter_asset):
        return counter_qty
    counter_price = _cached_asset_usd_price(
        asset=counter_asset,
        rate_date=rate_date,
        asset_usd_price_cache=asset_usd_price_cache,
        fx_lookup=fx_lookup,
    )
    if counter_price <= 0:
        counter_price = _cached_asset_usd_price_on_or_before(
            asset=counter_asset,
            rate_date=rate_date,
            asset_usd_price_cache=asset_usd_price_cache,
            fx_lookup=fx_lookup,
        )
    return counter_qty * counter_price if counter_price > 0 else Decimal("0")


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
    qty = _safe_decimal(payload.get("quantity"))
    return qty if qty > 0 else _safe_decimal(payload.get("amount"))


def _heliumgeek_display_quantity(payload: dict[str, Any]) -> Decimal:
    if str(payload.get("source", "")).lower().strip() != "heliumgeek":
        return Decimal("0")
    asset = str(payload.get("asset") or "").upper().strip()
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0")
    token_fields = (
        ("HNT Token", "HNT Tokens"),
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
    interval: str = "auto",
    max_points: int = 240,
    mark_from: str | None = None,
    mark_to: str | None = None,
) -> list[dict[str, Any]]:
    timeline: list[tuple[str, dict[str, Any]]] = []
    token_aliases = _load_token_aliases()
    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if len(ts_raw) < 10:
            continue
        if not _portfolio_history_counts_event(payload):
            continue
        raw_asset = str(payload.get("asset") or "").upper().strip()
        if not raw_asset or _normalize_mint(raw_asset) in ignored_mints:
            continue
        timeline.append((ts_raw, payload))
    timeline.sort(key=lambda item: item[0])

    points: list[dict[str, Any]] = []
    running_balances: dict[str, Decimal] = {}
    day_payloads: dict[str, list[dict[str, Any]]] = {}
    for ts_raw, payload in timeline:
        day_payloads.setdefault(ts_raw[:10], []).append(payload)
    mark_days = _portfolio_history_mark_days(
        sorted(day_payloads.keys()),
        interval=interval,
        max_points=max_points,
        mark_from=mark_from,
        mark_to=mark_to,
    )

    for day, payloads in sorted(day_payloads.items(), key=lambda item: item[0]):
        for payload in payloads:
            if not _portfolio_history_counts_event(payload):
                continue
            asset = _asset_canonical_symbol(str(payload.get("asset") or "").upper().strip(), token_aliases)
            qty = _dashboard_event_quantity(payload)
            side = str(payload.get("side") or "").lower().strip()
            if side == "in":
                running_balances[asset] = running_balances.get(asset, Decimal("0")) + abs(qty)
            elif side == "out":
                running_balances[asset] = running_balances.get(asset, Decimal("0")) - abs(qty)
            else:
                running_balances[asset] = running_balances.get(asset, Decimal("0")) + qty
        if day not in mark_days:
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
    return points


def _normalize_portfolio_history_interval(value: str) -> str:
    normalized = str(value or "auto").strip().lower()
    if normalized in {"event", "events", "raw"}:
        return "event"
    if normalized in {"day", "daily", "1d"}:
        return "day"
    if normalized in {"week", "weekly", "1w"}:
        return "week"
    if normalized in {"month", "monthly", "1mo"}:
        return "month"
    if normalized in {"quarter", "quarterly", "3mo"}:
        return "quarter"
    return "auto"


def _portfolio_history_mark_days(
    days: list[str],
    interval: str,
    max_points: int,
    mark_from: str | None = None,
    mark_to: str | None = None,
) -> set[str]:
    if not days:
        return set()
    safe_max_points = min(max(int(max_points), 20), 2000)
    normalized = _normalize_portfolio_history_interval(interval)
    eligible_days = [
        day for day in days
        if (not mark_from or day >= str(mark_from)[:10]) and (not mark_to or day <= str(mark_to)[:10])
    ]
    if not eligible_days:
        return set()
    if normalized == "auto":
        start_ts = _parse_iso_timestamp(f"{eligible_days[0]}T00:00:00+00:00")
        end_ts = _parse_iso_timestamp(f"{eligible_days[-1]}T00:00:00+00:00")
        span_days = max(1, ((end_ts - start_ts).days + 1) if start_ts is not None and end_ts is not None else len(eligible_days))
        target_days_per_point = max(1, span_days // safe_max_points)
        if target_days_per_point <= 1:
            normalized = "day"
        elif target_days_per_point <= 7:
            normalized = "week"
        elif target_days_per_point <= 31:
            normalized = "month"
        else:
            normalized = "quarter"
    if normalized == "event":
        selected = set(eligible_days)
    else:
        selected_by_bucket: dict[str, str] = {}
        for day in eligible_days:
            selected_by_bucket[_portfolio_history_bucket_key(day, normalized)] = day
        selected = set(selected_by_bucket.values())
    if len(selected) <= safe_max_points:
        return selected
    ordered = sorted(selected)
    stride = max(1, len(ordered) // safe_max_points)
    downsampled = set(ordered[::stride])
    downsampled.add(ordered[-1])
    return downsampled


def _portfolio_history_bucket_key(day: str, interval: str) -> str:
    if interval == "day":
        return day
    parsed = _parse_iso_timestamp(f"{day}T00:00:00+00:00")
    if parsed is None:
        return day
    if interval == "week":
        iso_year, iso_week, _weekday = parsed.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if interval == "quarter":
        quarter = ((parsed.month - 1) // 3) + 1
        return f"{parsed.year}-Q{quarter}"
    return day[:7]


def _portfolio_history_counts_event(payload: dict[str, Any]) -> bool:
    event_type = str(payload.get("event_type") or "").lower().strip()
    text = " ".join(
        str(payload.get(key) or "").lower()
        for key in ("event_type", "type", "source", "tag", "defi_label")
    )
    if any(token in text for token in ("derivative", "future", "futures", "perp", "margin", "liquidation")):
        return False
    if event_type in {"balance_snapshot", "account_snapshot"}:
        return False
    return True


def _build_yearly_asset_activity(events: list[dict[str, Any]], year: int | None = None) -> dict[str, Any]:
    yearly_asset_buckets: dict[tuple[int, str, str], dict[str, Any]] = {}
    yearly_deduped_values: dict[int, dict[str, Any]] = {}
    yearly_event_buckets: dict[tuple[int, str], dict[str, Any]] = {}
    yearly_source_buckets: dict[tuple[int, str], dict[str, Any]] = {}
    runtime_fx = _runtime_usd_to_eur_rate()
    fx_rate_cache: dict[str, Decimal] = {}
    asset_usd_price_cache: dict[tuple[str, str, str], Decimal] = {}
    fx_lookup = _load_fx_lookup()
    ignored_mints = set(_load_ignored_tokens().keys())
    token_aliases = _load_token_aliases()

    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        event_year = _extract_year(ts_raw)
        if event_year is None or (year is not None and event_year != year):
            continue

        raw_asset = str(payload.get("asset") or "").upper().strip()
        if not raw_asset or _normalize_mint(raw_asset) in ignored_mints:
            continue
        asset = _asset_canonical_symbol(raw_asset, token_aliases)

        qty = _dashboard_event_quantity(payload)
        side = str(payload.get("side") or "").lower()
        source = str(payload.get("source") or "unknown").strip() or "unknown"
        event_type = str(payload.get("event_type") or "unknown")
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
            year=event_year,
            payload=payload,
            value=value,
            value_counts=value_counts,
        )
        _accumulate_yearly_source_breakdown(
            yearly_source_buckets=yearly_source_buckets,
            year=event_year,
            payload=payload,
            value=value,
            value_counts=value_counts,
        )
        bucket_key = (event_year, asset, source)
        bucket = yearly_asset_buckets.setdefault(
            bucket_key,
            {
                "year": event_year,
                "asset": asset,
                "source": source,
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
                year=event_year,
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

    return _format_yearly_asset_activity(
        yearly_asset_buckets,
        yearly_deduped_values,
        yearly_event_buckets,
        yearly_source_buckets,
    )


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


def _solana_tx_failed(payload: dict[str, Any]) -> bool:
    if str(payload.get("source") or "").lower().strip() != "solana_rpc":
        return False
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return False
    meta = raw_row.get("meta")
    if not isinstance(meta, dict):
        return False
    status = meta.get("status")
    if isinstance(status, dict) and status.get("Err") is not None:
        return True
    return meta.get("err") is not None


def _is_failed_zero_solana_noise(payload: dict[str, Any]) -> bool:
    event_type = str(payload.get("event_type") or "").lower().strip()
    if event_type not in {"sol_transfer", "solana_tx"}:
        return False
    return _solana_tx_failed(payload) and _dashboard_event_quantity(payload) == Decimal("0")


def _counts_dashboard_activity(payload: dict[str, Any]) -> bool:
    return not _is_failed_zero_solana_noise(payload)


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


def _asset_canonical_symbol(asset: str, token_aliases: dict[str, dict[str, str]] | None = None) -> str:
    normalized = _normalize_mint(asset)
    if not normalized:
        return ""
    if token_aliases:
        alias = token_aliases.get(normalized)
        if alias is not None:
            symbol = str(alias.get("symbol") or "").upper().strip()
            if symbol:
                return symbol
    meta = resolve_token_metadata(normalized)
    if bool(meta.get("is_known")) and meta.get("symbol"):
        return str(meta["symbol"]).upper().strip()
    return normalized


def _payload_asset_canonical_symbol(
    payload: dict[str, Any],
    token_aliases: dict[str, dict[str, str]] | None = None,
) -> str:
    raw_asset = _normalize_mint(str(payload.get("asset") or payload.get("symbol") or ""))
    base_asset = _normalize_mint(str(payload.get("base_asset") or ""))
    quote_asset = _normalize_mint(str(payload.get("quote_asset") or ""))
    source = str(payload.get("source") or "").lower().strip()
    event_type = str(payload.get("event_type") or "").lower().strip()
    side = str(payload.get("side") or "").lower().strip()
    if base_asset and quote_asset and raw_asset:
        pair_symbols = {
            f"{base_asset}{quote_asset}",
            f"{base_asset}-{quote_asset}",
            f"{base_asset}/{quote_asset}",
            f"{base_asset}_{quote_asset}",
        }
        if raw_asset in pair_symbols or (
            source.endswith("_api") and event_type in {"trade", "spot_trade", "order"} and side in {"buy", "sell"}
        ):
            return _asset_canonical_symbol(base_asset, token_aliases)
    return _asset_canonical_symbol(raw_asset or base_asset, token_aliases)


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
