from __future__ import annotations

import json
import subprocess
from base64 import b64decode
from collections import deque
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tax_engine.admin import (
    get_admin_settings_view,
    put_admin_setting,
    resolve_cex_credentials,
    resolve_effective_runtime_config,
)
from tax_engine.api.reporting import (
    _PDF_ROWS_PER_FILE,
)
from tax_engine.api.reporting import (
    build_csv_from_rows as _build_csv_from_rows,
)
from tax_engine.api.reporting import (
    build_export_rows as _build_export_rows,
)
from tax_engine.api.reporting import (
    build_pdf_from_rows as _build_pdf_from_rows,
)
from tax_engine.api.reporting import (
    build_report_file_index as _build_report_file_index,
)
from tax_engine.api.rulesets import (
    RulesetUpsertRequest,
    _format_ruleset_row,
    _to_iso_date,
    ruleset_get,
    ruleset_list,
    ruleset_upsert,
)
from tax_engine.api.rulesets import (
    router as rulesets_router,
)
from tax_engine.connectors import (
    CexBalancesPreviewRequest,
    CexImportConfirmRequest,
    CexTransactionsPreviewRequest,
    CexVerifyRequest,
    DashboardRoleOverrideRequest,
    SolanaBalanceSnapshotRequest,
    SolanaFullHistoryImportRequest,
    SolanaGroupBalanceSnapshotRequest,
    SolanaGroupImportConfirmRequest,
    SolanaImportConfirmRequest,
    SolanaRpcProbeRequest,
    SolanaWalletPreviewRequest,
    WalletGroupDeleteRequest,
    WalletGroupUpsertRequest,
    fetch_cex_balance_preview,
    fetch_cex_transactions_preview,
    fetch_solana_wallet_balances,
    fetch_solana_wallet_full_history,
    fetch_solana_wallet_preview,
    mask_api_key,
    probe_solana_rpc_endpoints,
    verify_cex_credentials,
)
from tax_engine.connectors.token_metadata import resolve_token_metadata
from tax_engine.core.derivatives import process_derivatives_for_year
from tax_engine.core.processor import build_open_lot_aging_snapshot, process_events_for_year
from tax_engine.core.tax_domains import build_tax_domain_summary
from tax_engine.ingestion import (
    ConfirmImportRequest,
    ConnectorParseRequest,
    DetectFormatRequest,
    NormalizePreviewRequest,
    UploadPreviewRequest,
    confirm_import,
    detect_format,
    list_connectors,
    normalize_connector_rows,
    normalize_preview,
    parse_upload_file,
    write_audit,
)
from tax_engine.ingestion.store import STORE
from tax_engine.queue import (
    ProcessRunRequest,
    WorkerRunNextRequest,
    create_processing_job,
    get_processing_job,
    run_next_queued_job,
)
from tax_engine.reconciliation import (
    AutoMatchRequest,
    ManualMatchRequest,
    auto_match_and_persist,
    list_transfer_ledger,
    list_unmatched_transfers,
    manual_match,
)
from tax_engine.rulesets import build_default_registry

__all__ = [
    "RulesetUpsertRequest",
    "_format_ruleset_row",
    "_to_iso_date",
    "ruleset_get",
    "ruleset_list",
    "ruleset_upsert",
]


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


class AdminSettingsPutRequest(BaseModel):
    setting_key: str = Field(min_length=3, max_length=200)
    value: Any
    is_secret: bool = Field(default=False)


class AdminServiceActionRequest(BaseModel):
    action: str = Field(pattern="^(start|stop|restart)$")


class TokenAliasUpsertRequest(BaseModel):
    mint: str = Field(min_length=8, max_length=120)
    symbol: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=120)
    notes: str | None = Field(default=None, max_length=300)


class TokenAliasDeleteRequest(BaseModel):
    mint: str = Field(min_length=8, max_length=120)


class IgnoredTokenUpsertRequest(BaseModel):
    mint: str = Field(min_length=8, max_length=120)
    reason: str = Field(min_length=3, max_length=300)


class IgnoredTokenDeleteRequest(BaseModel):
    mint: str = Field(min_length=8, max_length=120)


class CexCredentialsLoadRequest(BaseModel):
    connector_id: str = Field(min_length=1, max_length=40)


class CexFullHistoryImportRequest(BaseModel):
    connector_id: str = Field(min_length=1, max_length=40)
    api_key: str = Field(min_length=1)
    api_secret: str = Field(min_length=1)
    passphrase: str | None = Field(default=None)
    timeout_seconds: int = Field(default=20, ge=3, le=90)
    start_time_ms: int | None = Field(default=None, ge=0)
    end_time_ms: int | None = Field(default=None, ge=0)
    window_days: int = Field(default=30, ge=1, le=120)
    max_rows_per_call: int = Field(default=1000, ge=50, le=5000)


class BulkFolderImportRequest(BaseModel):
    folder_path: str = Field(default="usertransfer", min_length=1, max_length=500)
    recursive: bool = Field(default=True)
    dry_run: bool = Field(default=False)
    max_files: int = Field(default=500, ge=1, le=5000)
    max_rows_per_file: int = Field(default=200000, ge=1, le=500000)


class ReportSnapshotCreateRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)


class IssueStatusUpdateRequest(BaseModel):
    issue_id: str = Field(min_length=3, max_length=200)
    status: str = Field(min_length=2, max_length=30)
    note: str | None = Field(default=None, max_length=500)


class ProcessCompareRulesetsRequest(BaseModel):
    job_id: str = Field(min_length=1, max_length=200)
    compare_ruleset_id: str = Field(min_length=1, max_length=80)
    compare_ruleset_version: str | None = Field(default=None, min_length=1, max_length=20)


class TaxEventOverrideUpsertRequest(BaseModel):
    source_event_id: str = Field(min_length=8, max_length=200)
    tax_category: str = Field(min_length=3, max_length=30)
    note: str | None = Field(default=None, max_length=500)


class TaxEventOverrideDeleteRequest(BaseModel):
    source_event_id: str = Field(min_length=8, max_length=200)


app = FastAPI(
    title="Steuerreport Engine API",
    version="0.1.0",
    description="Modulare, auditierbare Steuer-Engine API",
)
app.include_router(rulesets_router)


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    trace_id = str(uuid4())
    return JSONResponse(
        status_code=422,
        content={
            "trace_id": trace_id,
            "status": "error",
            "data": {},
            "errors": [
                {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "detail": str(exc),
                    "path": str(request.url),
                }
            ],
            "warnings": [],
        },
    )


@app.exception_handler(HTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    _ = request
    trace_id = str(uuid4())
    status_code = int(exc.status_code)
    payload = {
        "trace_id": trace_id,
        "status": "error",
        "data": {},
        "errors": [
            {
                "code": "http_error",
                "message": str(exc.detail),
                "status_code": status_code,
            }
        ],
        "warnings": [],
    }
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    trace_id = str(uuid4())
    return JSONResponse(
        status_code=500,
        content={
            "trace_id": trace_id,
            "status": "error",
            "data": {},
            "errors": [
                {
                    "code": "internal_error",
                    "message": str(exc),
                }
            ],
            "warnings": [],
        },
    )

_UI_STATIC_DIR = Path(__file__).resolve().parents[1] / "ui" / "static"
app.mount("/ui/static", StaticFiles(directory=str(_UI_STATIC_DIR)), name="ui-static")

_BULK_IMPORT_EXTENSIONS = {".csv", ".txt", ".json", ".xls", ".xlsx"}


def _detect_connector_from_filename(file_path: Path) -> str | None:
    name = file_path.name.lower()
    if "blockpit" in name:
        return "blockpit"
    if "binance" in name:
        return "binance"
    if "bitget" in name:
        return "bitget"
    if "coinbase" in name:
        return "coinbase"
    if "pionex" in name:
        return "pionex"
    if "heliumgeek" in name:
        return "heliumgeek"
    if name.startswith("wallet.") and "month" in name:
        return "heliumgeek"
    return None


def _detect_connector_from_source_name(source_name: str) -> str:
    normalized = str(source_name or "").lower()
    for connector in ("binance", "bitget", "coinbase", "pionex", "blockpit", "heliumgeek", "solana"):
        if connector in normalized:
            return connector
    if normalized.startswith("wallet.") and "month" in normalized:
        return "heliumgeek"
    return "unknown"


def _build_import_job_rows(
    *,
    status: str | None,
    integration: str | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    wanted_status = str(status or "").strip().lower()
    wanted_integration = str(integration or "").strip().lower()
    raw_rows = STORE.list_source_file_summaries(limit=5000)
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        declared = int(row.get("declared_row_count") or 0)
        imported = int(row.get("imported_event_count") or 0)
        duplicates = max(declared - imported, 0)
        if declared == 0:
            row_status = "empty"
        elif imported == 0 and duplicates > 0:
            row_status = "duplicate"
        elif imported < declared:
            row_status = "partial"
        else:
            row_status = "completed"

        connector = _detect_connector_from_source_name(str(row.get("source_name") or ""))
        if wanted_status and row_status != wanted_status:
            continue
        if wanted_integration and connector != wanted_integration:
            continue
        rows.append(
            {
                "job_id": row.get("source_file_id"),
                "source_file_id": row.get("source_file_id"),
                "connector": connector,
                "source_name": row.get("source_name"),
                "started_at_utc": row.get("created_at_utc"),
                "finished_at_utc": row.get("created_at_utc"),
                "status": row_status,
                "rows": declared,
                "inserted_events": imported,
                "duplicates": duplicates,
                "warnings": [],
            }
        )
    return rows[offset : offset + limit]


@app.get("/", include_in_schema=False)
def web_root() -> RedirectResponse:
    return RedirectResponse(url="/app", status_code=307)


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


@app.get("/app", include_in_schema=False)
def web_app() -> FileResponse:
    return FileResponse(_UI_STATIC_DIR / "index.html")


@app.get("/api/v1/admin/settings", response_model=StandardResponse, tags=["admin"])
def admin_settings_list() -> StandardResponse:
    trace_id = str(uuid4())
    data = get_admin_settings_view()
    write_audit(
        trace_id=trace_id,
        action="admin.settings.list",
        payload={"count": len(data.get("settings", []))},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=[])


@app.get("/api/v1/admin/runtime-config", response_model=StandardResponse, tags=["admin"])
def admin_runtime_config() -> StandardResponse:
    trace_id = str(uuid4())
    data = resolve_effective_runtime_config()
    write_audit(
        trace_id=trace_id,
        action="admin.runtime_config.get",
        payload={
            "alchemy_configured": data.get("credentials", {}).get("alchemy_configured", False),
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=[])


@app.post("/api/v1/admin/settings", response_model=StandardResponse, tags=["admin"])
def admin_settings_put(payload: AdminSettingsPutRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        put_admin_setting(
            setting_key=payload.setting_key.strip(),
            value=payload.value,
            is_secret=payload.is_secret,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="admin.settings.put",
            payload={
                "setting_key": payload.setting_key,
                "is_secret": payload.is_secret,
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "admin_setting_write_failed", "message": str(exc)}],
            warnings=[],
        )

    write_audit(
        trace_id=trace_id,
        action="admin.settings.put",
        payload={
            "setting_key": payload.setting_key,
            "is_secret": payload.is_secret,
            "ok": True,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"setting_key": payload.setting_key, "saved": True},
        errors=[],
        warnings=[],
    )


_SOLANA_BACKFILL_SERVICE = "steuerreport-solana-backfill.service"
_SOLANA_BACKFILL_LOG = Path("/var/log/steuerreport/solana-wallet-backfill.log")
_SOLANA_BACKFILL_CURSOR_KEY = "runtime.scan.cursor.wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB"
_SOLANA_BACKFILL_STATS_KEY = "runtime.scan.stats.wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB"


@app.get("/api/v1/admin/services/solana-backfill", response_model=StandardResponse, tags=["admin"])
def admin_solana_backfill_status() -> StandardResponse:
    trace_id = str(uuid4())
    data = _build_solana_backfill_status()
    write_audit(
        trace_id=trace_id,
        action="admin.services.solana_backfill.status",
        payload={
            "active_state": data.get("active_state"),
            "sub_state": data.get("sub_state"),
            "enabled": data.get("enabled"),
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=[])


@app.post("/api/v1/admin/services/solana-backfill/action", response_model=StandardResponse, tags=["admin"])
def admin_solana_backfill_action(payload: AdminServiceActionRequest) -> StandardResponse:
    trace_id = str(uuid4())
    result = _run_systemctl([payload.action, _SOLANA_BACKFILL_SERVICE])
    data = _build_solana_backfill_status()
    data["command"] = {
        "action": payload.action,
        "returncode": result.returncode,
        "stderr": result.stderr[-2000:],
    }
    ok = result.returncode == 0
    write_audit(
        trace_id=trace_id,
        action="admin.services.solana_backfill.action",
        payload={
            "requested_action": payload.action,
            "returncode": result.returncode,
            "ok": ok,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success" if ok else "error",
        data=data,
        errors=[] if ok else [{"code": "service_action_failed", "message": result.stderr[-500:] or "systemctl failed"}],
        warnings=[],
    )


def _run_systemctl(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["systemctl", *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )


def _build_solana_backfill_status() -> dict[str, Any]:
    show = _run_systemctl(
        [
            "show",
            _SOLANA_BACKFILL_SERVICE,
            "--property=ActiveState,SubState,LoadState,MainPID,ExecMainStatus,RestartUSec,Result",
        ]
    )
    properties: dict[str, str] = {}
    for line in show.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        properties[key] = value

    enabled = _run_systemctl(["is-enabled", _SOLANA_BACKFILL_SERVICE])
    cursor_row = STORE.get_setting(_SOLANA_BACKFILL_CURSOR_KEY)
    stats_row = STORE.get_setting(_SOLANA_BACKFILL_STATS_KEY)
    stats: Any = None
    if stats_row is not None:
        try:
            stats = json.loads(str(stats_row.get("value_json", "{}")))
        except json.JSONDecodeError:
            stats = stats_row.get("value_json")
    cursor: Any = None
    if cursor_row is not None:
        try:
            cursor = json.loads(str(cursor_row.get("value_json", '""')))
        except json.JSONDecodeError:
            cursor = cursor_row.get("value_json")

    return {
        "service_name": _SOLANA_BACKFILL_SERVICE,
        "enabled": enabled.stdout.strip() == "enabled",
        "enabled_state": enabled.stdout.strip() or "unknown",
        "load_state": properties.get("LoadState", "unknown"),
        "active_state": properties.get("ActiveState", "unknown"),
        "sub_state": properties.get("SubState", "unknown"),
        "main_pid": int(properties.get("MainPID", "0") or "0"),
        "exec_main_status": properties.get("ExecMainStatus", ""),
        "result": properties.get("Result", ""),
        "cursor_set": bool(cursor),
        "last_before_signature": cursor,
        "stats": stats,
        "log_path": str(_SOLANA_BACKFILL_LOG),
        "log_tail": _tail_file(_SOLANA_BACKFILL_LOG, max_lines=40),
    }


def _tail_file(path: Path, max_lines: int) -> list[str]:
    if not path.exists():
        return []
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(max(0, size - 20000))
        data = handle.read().decode("utf-8", errors="replace")
    return data.splitlines()[-max_lines:]


@app.get("/api/v1/admin/token-aliases", response_model=StandardResponse, tags=["admin"])
def admin_token_aliases_list() -> StandardResponse:
    trace_id = str(uuid4())
    aliases = _load_token_aliases()
    items = [
        {"mint": mint, **value}
        for mint, value in sorted(aliases.items(), key=lambda item: item[0])
    ]
    write_audit(trace_id=trace_id, action="admin.token_aliases.list", payload={"count": len(items)})
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(items), "aliases": items},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/admin/token-aliases/upsert", response_model=StandardResponse, tags=["admin"])
def admin_token_aliases_upsert(payload: TokenAliasUpsertRequest) -> StandardResponse:
    trace_id = str(uuid4())
    mint = _normalize_mint(payload.mint)
    aliases = _load_token_aliases()
    aliases[mint] = {
        "symbol": payload.symbol.strip().upper(),
        "name": payload.name.strip(),
        "notes": (payload.notes or "").strip(),
    }
    put_admin_setting("runtime.token_aliases", aliases, is_secret=False)
    write_audit(trace_id=trace_id, action="admin.token_aliases.upsert", payload={"mint": mint})
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"mint": mint, "saved": True},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/admin/token-aliases/delete", response_model=StandardResponse, tags=["admin"])
def admin_token_aliases_delete(payload: TokenAliasDeleteRequest) -> StandardResponse:
    trace_id = str(uuid4())
    mint = _normalize_mint(payload.mint)
    aliases = _load_token_aliases()
    deleted = mint in aliases
    if deleted:
        del aliases[mint]
        put_admin_setting("runtime.token_aliases", aliases, is_secret=False)
    write_audit(trace_id=trace_id, action="admin.token_aliases.delete", payload={"mint": mint, "deleted": deleted})
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"mint": mint, "deleted": deleted},
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/admin/ignored-tokens", response_model=StandardResponse, tags=["admin"])
def admin_ignored_tokens_list() -> StandardResponse:
    trace_id = str(uuid4())
    ignored = _load_ignored_tokens()
    items = [
        {"mint": mint, **value}
        for mint, value in sorted(ignored.items(), key=lambda item: item[0])
    ]
    write_audit(trace_id=trace_id, action="admin.ignored_tokens.list", payload={"count": len(items)})
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(items), "ignored_tokens": items},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/admin/ignored-tokens/upsert", response_model=StandardResponse, tags=["admin"])
def admin_ignored_tokens_upsert(payload: IgnoredTokenUpsertRequest) -> StandardResponse:
    trace_id = str(uuid4())
    mint = _normalize_mint(payload.mint)
    ignored = _load_ignored_tokens()
    ignored[mint] = {
        "reason": payload.reason.strip(),
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    put_admin_setting("runtime.ignored_tokens", ignored, is_secret=False)
    write_audit(trace_id=trace_id, action="admin.ignored_tokens.upsert", payload={"mint": mint})
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"mint": mint, "saved": True},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/admin/ignored-tokens/delete", response_model=StandardResponse, tags=["admin"])
def admin_ignored_tokens_delete(payload: IgnoredTokenDeleteRequest) -> StandardResponse:
    trace_id = str(uuid4())
    mint = _normalize_mint(payload.mint)
    ignored = _load_ignored_tokens()
    deleted = mint in ignored
    if deleted:
        del ignored[mint]
        put_admin_setting("runtime.ignored_tokens", ignored, is_secret=False)
    write_audit(trace_id=trace_id, action="admin.ignored_tokens.delete", payload={"mint": mint, "deleted": deleted})
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"mint": mint, "deleted": deleted},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/admin/cex-credentials/load", response_model=StandardResponse, tags=["admin"])
def admin_cex_credentials_load(payload: CexCredentialsLoadRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        creds = resolve_cex_credentials(payload.connector_id)
    except Exception as exc:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "cex_credentials_load_failed", "message": str(exc)}],
            warnings=[],
        )
    write_audit(
        trace_id=trace_id,
        action="admin.cex_credentials.load",
        payload={"connector_id": creds["connector_id"]},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=creds, errors=[], warnings=[])


@app.post("/api/v1/dashboard/role-override", response_model=StandardResponse, tags=["dashboard"])
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


@app.get("/api/v1/dashboard/overview", response_model=StandardResponse, tags=["dashboard"])
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
            value = _estimate_event_values(payload=payload, asset=asset, quantity=qty, runtime_fx=runtime_fx)
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
        "portfolio_value_history": _build_portfolio_value_history(events, ignored_mints, runtime_fx),
        "yearly_asset_activity": yearly_asset_activity,
        "asset_balances": balances,
        "wallet_groups": _load_wallet_groups(),
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


@app.get("/api/v1/portfolio/integrations", response_model=StandardResponse, tags=["dashboard"])
def portfolio_integrations() -> StandardResponse:
    trace_id = str(uuid4())
    events = STORE.list_raw_events()
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
        rows.append(
            {
                "integration_id": str(bucket["integration_id"]),
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
        data={"count": len(rows), "event_count_total": len(events), "rows": rows},
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/dashboard/wallet-snapshots", response_model=StandardResponse, tags=["dashboard"])
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


@app.get("/api/v1/portfolio/lot-aging", response_model=StandardResponse, tags=["dashboard"])
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


@app.get("/api/v1/wallet-groups", response_model=StandardResponse, tags=["wallet-groups"])
def wallet_groups_list() -> StandardResponse:
    trace_id = str(uuid4())
    groups = _load_wallet_groups()
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


@app.post("/api/v1/wallet-groups/upsert", response_model=StandardResponse, tags=["wallet-groups"])
def wallet_groups_upsert(payload: WalletGroupUpsertRequest) -> StandardResponse:
    trace_id = str(uuid4())
    groups = _load_wallet_groups()
    normalized_wallets = _normalize_wallet_addresses(payload.wallet_addresses)
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


@app.post("/api/v1/wallet-groups/delete", response_model=StandardResponse, tags=["wallet-groups"])
def wallet_groups_delete(payload: WalletGroupDeleteRequest) -> StandardResponse:
    trace_id = str(uuid4())
    groups = _load_wallet_groups()
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


@app.post("/api/v1/import/detect-format", response_model=StandardResponse, tags=["import"])
def import_detect_format(payload: DetectFormatRequest) -> StandardResponse:
    trace_id = str(uuid4())
    result = detect_format(payload.rows)
    write_audit(
        trace_id=trace_id,
        action="import.detect_format",
        payload={
            "source_name": payload.source_name,
            "row_count": len(payload.rows),
            "detected_locale": result["detected_locale"],
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@app.post("/api/v1/import/normalize-preview", response_model=StandardResponse, tags=["import"])
def import_normalize_preview(payload: NormalizePreviewRequest) -> StandardResponse:
    trace_id = str(uuid4())
    normalized_rows, warnings, errors = normalize_preview(
        rows=payload.rows,
        locale_hint=payload.locale_hint,
        numeric_fields=payload.numeric_fields,
        datetime_fields=payload.datetime_fields,
        subunit_fields=payload.subunit_fields,
    )
    status = "success" if not errors else "partial"
    write_audit(
        trace_id=trace_id,
        action="import.normalize_preview",
        payload={
            "source_name": payload.source_name,
            "row_count": len(payload.rows),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status=status,
        data={"normalized_rows": normalized_rows},
        errors=errors,
        warnings=warnings,
    )


@app.post("/api/v1/import/confirm", response_model=StandardResponse, tags=["import"])
def import_confirm(payload: ConfirmImportRequest) -> StandardResponse:
    trace_id = str(uuid4())
    result = confirm_import(source_name=payload.source_name, rows=payload.rows)
    write_audit(
        trace_id=trace_id,
        action="import.confirm",
        payload={
            "source_name": payload.source_name,
            "source_file_id": result["source_file_id"],
            "inserted_events": result["inserted_events"],
            "duplicate_events": result["duplicate_events"],
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@app.get("/api/v1/import/sources-summary", response_model=StandardResponse, tags=["import"])
def import_sources_summary(limit: int = 100) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = max(1, min(limit, 5000))
    rows = STORE.list_source_file_summaries(limit=safe_limit)
    write_audit(
        trace_id=trace_id,
        action="import.sources_summary",
        payload={"count": len(rows), "limit": safe_limit},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "rows": rows},
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/import/connectors", response_model=StandardResponse, tags=["import"])
def import_connectors() -> StandardResponse:
    trace_id = str(uuid4())
    connectors = list_connectors()
    write_audit(
        trace_id=trace_id,
        action="import.connectors",
        payload={"count": len(connectors)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"connectors": connectors, "count": len(connectors)},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/import/parse-preview", response_model=StandardResponse, tags=["import"])
def import_parse_preview(payload: ConnectorParseRequest) -> StandardResponse:
    trace_id = str(uuid4())
    normalized_rows, warnings, errors = normalize_connector_rows(
        connector_id=payload.connector_id,
        rows=payload.rows,
        max_rows=payload.max_rows,
    )
    status = "success" if not errors else "partial"
    write_audit(
        trace_id=trace_id,
        action="import.parse_preview",
        payload={
            "connector_id": payload.connector_id,
            "input_rows": len(payload.rows),
            "normalized_rows": len(normalized_rows),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status=status,
        data={
            "connector_id": payload.connector_id,
            "normalized_rows": normalized_rows,
            "count": len(normalized_rows),
        },
        errors=errors,
        warnings=warnings,
    )


@app.post("/api/v1/import/upload-preview", response_model=StandardResponse, tags=["import"])
def import_upload_preview(payload: UploadPreviewRequest) -> StandardResponse:
    trace_id = str(uuid4())
    if not payload.filename:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "missing_filename", "message": "Filename missing"}],
            warnings=[],
        )

    try:
        content = b64decode(payload.file_content_base64, validate=True)
    except Exception:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_base64", "message": "Dateiinhalt ist kein valides Base64"}],
            warnings=[],
        )

    try:
        rows, file_warnings = parse_upload_file(payload.filename, content)
    except ValueError as exc:
        write_audit(
            trace_id=trace_id,
            action="import.upload_preview",
            payload={
                "connector_id": payload.connector_id,
                "filename": payload.filename,
                "parse_error": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": str(exc), "message": "Upload konnte nicht geparst werden"}],
            warnings=[],
        )

    normalized_rows, map_warnings, errors = normalize_connector_rows(
        connector_id=payload.connector_id,
        rows=rows,
        max_rows=payload.max_rows,
    )
    warnings = [*file_warnings, *map_warnings]
    status = "success" if not errors else "partial"

    write_audit(
        trace_id=trace_id,
        action="import.upload_preview",
        payload={
            "connector_id": payload.connector_id,
            "filename": payload.filename,
            "input_rows": len(rows),
            "normalized_rows": len(normalized_rows),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
        },
    )

    return StandardResponse(
        trace_id=trace_id,
        status=status,
        data={
            "connector_id": payload.connector_id,
            "filename": payload.filename,
            "input_rows": len(rows),
            "count": len(normalized_rows),
            "normalized_rows": normalized_rows,
        },
        errors=errors,
        warnings=warnings,
    )


@app.post("/api/v1/import/bulk-folder", response_model=StandardResponse, tags=["import"])
def import_bulk_folder(payload: BulkFolderImportRequest) -> StandardResponse:
    trace_id = str(uuid4())
    folder = Path(payload.folder_path).expanduser()
    if not folder.is_absolute():
        folder = (Path.cwd() / folder).resolve()
    else:
        folder = folder.resolve()

    if not folder.exists() or not folder.is_dir():
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "folder_not_found", "message": str(folder)}],
            warnings=[],
        )

    file_iter = folder.rglob("*") if payload.recursive else folder.glob("*")
    candidate_files = [
        path
        for path in file_iter
        if path.is_file() and path.suffix.lower() in _BULK_IMPORT_EXTENSIONS
    ]
    candidate_files = sorted(candidate_files)[: payload.max_files]

    rows: list[dict[str, Any]] = []
    total_inserted = 0
    total_duplicates = 0
    total_normalized = 0
    total_failed = 0
    warnings: list[dict[str, str]] = []

    for file_path in candidate_files:
        connector_id = _detect_connector_from_filename(file_path)
        if connector_id is None:
            warnings.append(
                {"code": "connector_not_detected", "message": file_path.name}
            )
            continue
        try:
            raw_rows, parse_warnings = parse_upload_file(file_path.name, file_path.read_bytes())
            normalized_rows, map_warnings, errors = normalize_connector_rows(
                connector_id=connector_id,
                rows=raw_rows,
                max_rows=payload.max_rows_per_file,
            )
            total_normalized += len(normalized_rows)
            if payload.dry_run:
                import_result = {"inserted_events": 0, "duplicate_events": 0}
            else:
                source_name = f"bulk:{connector_id}:{file_path.name}"
                import_result = confirm_import(source_name=source_name, rows=normalized_rows)
                total_inserted += int(import_result.get("inserted_events", 0))
                total_duplicates += int(import_result.get("duplicate_events", 0))

            rows.append(
                {
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "connector_id": connector_id,
                    "raw_rows": len(raw_rows),
                    "normalized_rows": len(normalized_rows),
                    "parse_warnings": len(parse_warnings),
                    "map_warnings": len(map_warnings),
                    "errors": len(errors),
                    "inserted_events": int(import_result.get("inserted_events", 0)),
                    "duplicate_events": int(import_result.get("duplicate_events", 0)),
                }
            )
        except Exception as exc:
            total_failed += 1
            rows.append(
                {
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "connector_id": connector_id or "",
                    "raw_rows": 0,
                    "normalized_rows": 0,
                    "parse_warnings": 0,
                    "map_warnings": 0,
                    "errors": 1,
                    "inserted_events": 0,
                    "duplicate_events": 0,
                    "error_message": str(exc),
                }
            )

    write_audit(
        trace_id=trace_id,
        action="import.bulk_folder",
        payload={
            "folder_path": str(folder),
            "recursive": payload.recursive,
            "dry_run": payload.dry_run,
            "scanned_files": len(candidate_files),
            "processed_files": len(rows),
            "failed_files": total_failed,
            "normalized_rows": total_normalized,
            "inserted_events": total_inserted,
            "duplicate_events": total_duplicates,
        },
    )

    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "folder_path": str(folder),
            "recursive": payload.recursive,
            "dry_run": payload.dry_run,
            "scanned_files": len(candidate_files),
            "processed_files": len(rows),
            "failed_files": total_failed,
            "normalized_rows": total_normalized,
            "inserted_events": total_inserted,
            "duplicate_events": total_duplicates,
            "rows": rows,
        },
        errors=[],
        warnings=warnings,
    )


@app.post("/api/v1/connectors/cex/verify", response_model=StandardResponse, tags=["connectors"])
def connectors_cex_verify(payload: CexVerifyRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        result = verify_cex_credentials(
            connector_id=payload.connector_id,
            api_key=payload.api_key,
            api_secret=payload.api_secret,
            passphrase=payload.passphrase,
            timeout_seconds=payload.timeout_seconds,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="connectors.cex.verify",
            payload={
                "connector_id": payload.connector_id,
                "api_key_masked": mask_api_key(payload.api_key),
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_error", "message": str(exc)}],
            warnings=[],
        )

    status = "success" if result.get("ok") else "partial"
    write_audit(
        trace_id=trace_id,
        action="connectors.cex.verify",
        payload={
            "connector_id": payload.connector_id,
            "api_key_masked": mask_api_key(payload.api_key),
            "ok": bool(result.get("ok")),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status=status,
        data=result,
        errors=[],
        warnings=[],
    )


@app.post(
    "/api/v1/connectors/cex/balances-preview",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_cex_balances_preview(payload: CexBalancesPreviewRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        result = fetch_cex_balance_preview(
            connector_id=payload.connector_id,
            api_key=payload.api_key,
            api_secret=payload.api_secret,
            passphrase=payload.passphrase,
            timeout_seconds=payload.timeout_seconds,
            max_rows=payload.max_rows,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="connectors.cex.balances_preview",
            payload={
                "connector_id": payload.connector_id,
                "api_key_masked": mask_api_key(payload.api_key),
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_error", "message": str(exc)}],
            warnings=[],
        )

    write_audit(
        trace_id=trace_id,
        action="connectors.cex.balances_preview",
        payload={
            "connector_id": payload.connector_id,
            "api_key_masked": mask_api_key(payload.api_key),
            "ok": True,
            "rows": result.get("count", 0),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data=result,
        errors=[],
        warnings=[],
    )


@app.post(
    "/api/v1/connectors/cex/transactions-preview",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_cex_transactions_preview(payload: CexTransactionsPreviewRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        result = fetch_cex_transactions_preview(
            connector_id=payload.connector_id,
            api_key=payload.api_key,
            api_secret=payload.api_secret,
            passphrase=payload.passphrase,
            timeout_seconds=payload.timeout_seconds,
            max_rows=payload.max_rows,
            start_time_ms=payload.start_time_ms,
            end_time_ms=payload.end_time_ms,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="connectors.cex.transactions_preview",
            payload={
                "connector_id": payload.connector_id,
                "api_key_masked": mask_api_key(payload.api_key),
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_error", "message": str(exc)}],
            warnings=[],
        )

    write_audit(
        trace_id=trace_id,
        action="connectors.cex.transactions_preview",
        payload={
            "connector_id": payload.connector_id,
            "api_key_masked": mask_api_key(payload.api_key),
            "ok": True,
            "rows": result.get("count", 0),
        },
    )
    warnings = result.get("warnings", [])
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data=result,
        errors=[],
        warnings=warnings if isinstance(warnings, list) else [],
    )


@app.post("/api/v1/connectors/cex/import-confirm", response_model=StandardResponse, tags=["connectors"])
def connectors_cex_import_confirm(payload: CexImportConfirmRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        preview = fetch_cex_transactions_preview(
            connector_id=payload.connector_id,
            api_key=payload.api_key,
            api_secret=payload.api_secret,
            passphrase=payload.passphrase,
            timeout_seconds=payload.timeout_seconds,
            max_rows=payload.max_rows,
            start_time_ms=payload.start_time_ms,
            end_time_ms=payload.end_time_ms,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="connectors.cex.import_confirm",
            payload={
                "connector_id": payload.connector_id,
                "api_key_masked": mask_api_key(payload.api_key),
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_error", "message": str(exc)}],
            warnings=[],
        )

    rows = preview.get("rows", [])
    if not isinstance(rows, list):
        rows = []

    source_name = payload.source_name or f"{payload.connector_id.lower()}_api_import"
    import_result = confirm_import(source_name=source_name, rows=rows)
    warnings = preview.get("warnings", [])

    write_audit(
        trace_id=trace_id,
        action="connectors.cex.import_confirm",
        payload={
            "connector_id": payload.connector_id,
            "api_key_masked": mask_api_key(payload.api_key),
            "source_name": source_name,
            "fetched_rows": len(rows),
            "inserted_events": import_result["inserted_events"],
            "duplicate_events": import_result["duplicate_events"],
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "connector_id": payload.connector_id,
            "source_name": source_name,
            "fetched_rows": len(rows),
            "preview_count": preview.get("count", len(rows)),
            "import_result": import_result,
        },
        errors=[],
        warnings=warnings if isinstance(warnings, list) else [],
    )


@app.post("/api/v1/connectors/cex/import-full-history", response_model=StandardResponse, tags=["connectors"])
def connectors_cex_import_full_history(payload: CexFullHistoryImportRequest) -> StandardResponse:
    trace_id = str(uuid4())
    connector = payload.connector_id.strip().lower()
    if connector != "binance":
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_not_supported_full_history", "message": "Aktuell nur Binance unterstützt"}],
            warnings=[],
        )

    now_utc = datetime.now(UTC)
    start_ms = payload.start_time_ms or int(datetime(2020, 1, 1, tzinfo=UTC).timestamp() * 1000)
    end_ms = payload.end_time_ms or int(now_utc.timestamp() * 1000)
    if start_ms >= end_ms:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_time_window", "message": "start_time_ms muss kleiner als end_time_ms sein"}],
            warnings=[],
        )

    window_ms = int(payload.window_days * 24 * 60 * 60 * 1000)
    min_window_ms = 6 * 60 * 60 * 1000
    max_split_depth = 6
    total_fetched_rows = 0
    total_inserted = 0
    total_duplicates = 0
    windows_processed = 0
    failed_windows = 0
    warnings: list[dict[str, str]] = []

    pending_windows: deque[tuple[int, int, int]] = deque()
    current_start = start_ms
    while current_start <= end_ms:
        current_end = min(current_start + window_ms - 1, end_ms)
        pending_windows.append((current_start, current_end, 0))
        current_start = current_end + 1

    while pending_windows:
        current_start, current_end, split_depth = pending_windows.popleft()
        windows_processed += 1
        try:
            preview = fetch_cex_transactions_preview(
                connector_id=connector,
                api_key=payload.api_key,
                api_secret=payload.api_secret,
                passphrase=payload.passphrase,
                timeout_seconds=payload.timeout_seconds,
                max_rows=payload.max_rows_per_call,
                start_time_ms=current_start,
                end_time_ms=current_end,
            )
            rows = preview.get("rows", [])
            if not isinstance(rows, list):
                rows = []
            source_name = f"{connector}_api_full_{current_start}_{current_end}"
            import_result = confirm_import(source_name=source_name, rows=rows)
            total_fetched_rows += len(rows)
            total_inserted += int(import_result.get("inserted_events", 0))
            total_duplicates += int(import_result.get("duplicate_events", 0))
            raw_warnings = preview.get("warnings", [])
            if isinstance(raw_warnings, list):
                for item in raw_warnings:
                    if isinstance(item, dict):
                        warnings.append(
                            {
                                "code": str(item.get("code", "connector_warning")),
                                "message": str(item.get("message", f"{current_start}-{current_end}")),
                            }
                        )
        except Exception as exc:
            duration = current_end - current_start + 1
            can_split = duration > min_window_ms and split_depth < max_split_depth
            if can_split:
                midpoint = current_start + (duration // 2)
                left_end = max(current_start, midpoint - 1)
                right_start = midpoint
                pending_windows.appendleft((right_start, current_end, split_depth + 1))
                pending_windows.appendleft((current_start, left_end, split_depth + 1))
                warnings.append(
                    {
                        "code": "window_retry_split",
                        "message": f"{current_start}-{current_end}: {exc}. Split depth {split_depth + 1}.",
                    }
                )
            else:
                failed_windows += 1
                warnings.append(
                    {
                        "code": "window_fetch_failed",
                        "message": f"{current_start}-{current_end}: {exc}",
                    }
                )

    write_audit(
        trace_id=trace_id,
        action="connectors.cex.import_full_history",
        payload={
            "connector_id": connector,
            "windows_processed": windows_processed,
            "failed_windows": failed_windows,
            "total_fetched_rows": total_fetched_rows,
            "total_inserted_events": total_inserted,
            "total_duplicate_events": total_duplicates,
        },
    )
    response_status = "partial" if failed_windows > 0 else "success"
    return StandardResponse(
        trace_id=trace_id,
        status=response_status,
        data={
            "connector_id": connector,
            "start_time_ms": start_ms,
            "end_time_ms": end_ms,
            "window_days": payload.window_days,
            "windows_processed": windows_processed,
            "failed_windows": failed_windows,
            "total_fetched_rows": total_fetched_rows,
            "total_inserted_events": total_inserted,
            "total_duplicate_events": total_duplicates,
        },
        errors=[],
        warnings=warnings,
    )


@app.post(
    "/api/v1/connectors/solana/rpc-probe",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_solana_rpc_probe(payload: SolanaRpcProbeRequest) -> StandardResponse:
    trace_id = str(uuid4())
    result = probe_solana_rpc_endpoints(
        rpc_url=payload.rpc_url,
        rpc_fallback_urls=payload.rpc_fallback_urls,
        timeout_seconds=payload.timeout_seconds,
    )
    write_audit(
        trace_id=trace_id,
        action="connectors.solana.rpc_probe",
        payload={
            "rpc_url": payload.rpc_url,
            "rpc_fallback_count": len(payload.rpc_fallback_urls),
            "ok_count": result.get("ok_count", 0),
            "probe_count": result.get("probe_count", 0),
        },
    )
    warnings: list[dict[str, str]] = []
    if result.get("ok_count", 0) == 0:
        warnings.append({"code": "no_working_rpc_endpoint", "message": "No endpoint responded successfully"})
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data=result,
        errors=[],
        warnings=warnings,
    )


@app.post(
    "/api/v1/connectors/solana/balance-snapshot",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_solana_balance_snapshot(payload: SolanaBalanceSnapshotRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        result = fetch_solana_wallet_balances(
            wallet_address=payload.wallet_address,
            rpc_url=payload.rpc_url,
            rpc_fallback_urls=payload.rpc_fallback_urls,
            timeout_seconds=payload.timeout_seconds,
            max_tokens=payload.max_tokens,
            include_prices=payload.include_prices,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="connectors.solana.balance_snapshot",
            payload={
                "wallet_address": payload.wallet_address,
                "rpc_url": payload.rpc_url,
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_error", "message": str(exc)}],
            warnings=[],
        )

    token_rows = result.get("tokens", [])
    if isinstance(token_rows, list):
        result["tokens"] = _decorate_token_rows(token_rows)

    write_audit(
        trace_id=trace_id,
        action="connectors.solana.balance_snapshot",
        payload={
            "wallet_address": payload.wallet_address,
            "rpc_url": payload.rpc_url,
            "token_count": result.get("token_count", 0),
            "ok": True,
        },
    )
    _append_wallet_snapshot(
        scope="wallet",
        entity_id=payload.wallet_address,
        total_estimated_usd=str(result.get("total_estimated_usd", "")),
        sol_balance=str(result.get("sol_balance", "")),
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@app.post(
    "/api/v1/connectors/solana/group-balance-snapshot",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_solana_group_balance_snapshot(payload: SolanaGroupBalanceSnapshotRequest) -> StandardResponse:
    trace_id = str(uuid4())
    wallets = _resolve_wallets_from_group(payload.group_id, payload.wallet_addresses)
    if not wallets:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "wallets_empty", "message": "Keine Wallets für Gruppenabfrage vorhanden."}],
            warnings=[],
        )

    wallet_results: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    total_sol_balance = Decimal("0")
    total_estimated_usd = Decimal("0")
    token_map: dict[str, dict[str, Decimal]] = {}

    for wallet in wallets:
        try:
            result = fetch_solana_wallet_balances(
                wallet_address=wallet,
                rpc_url=payload.rpc_url,
                rpc_fallback_urls=payload.rpc_fallback_urls,
                timeout_seconds=payload.timeout_seconds,
                max_tokens=payload.max_tokens,
                include_prices=payload.include_prices,
            )
            wallet_results.append(result)
            total_sol_balance += _safe_decimal(result.get("sol_balance", "0"))
            total_estimated_usd += _safe_decimal(result.get("total_estimated_usd", "0"))
            for token in result.get("tokens", []):
                if not isinstance(token, dict):
                    continue
                asset = str(token.get("asset") or "").upper()
                if not asset:
                    continue
                entry = token_map.setdefault(asset, {"quantity": Decimal("0"), "usd_value": Decimal("0")})
                entry["quantity"] += _safe_decimal(token.get("quantity", "0"))
                entry["usd_value"] += _safe_decimal(token.get("usd_value", "0"))
        except Exception as exc:
            warnings.append({"code": "wallet_balance_failed", "message": f"{wallet}: {exc}"})

    grouped_tokens: list[dict[str, str]] = []
    ignored_tokens = _load_ignored_tokens()
    for asset, values in sorted(token_map.items(), key=lambda item: abs(item[1]["quantity"]), reverse=True):
        meta = _resolve_token_display(asset)
        ignored_meta = ignored_tokens.get(_normalize_mint(asset))
        grouped_tokens.append(
            {
                "asset": asset,
                "symbol": str(meta["symbol"]),
                "name": str(meta["name"]),
                "quantity": _decimal_to_plain(values["quantity"]),
                "usd_value": values["usd_value"].normalize().to_eng_string() if values["usd_value"] > 0 else "",
                "ignored": "true" if ignored_meta is not None else "false",
                "ignored_reason": str(ignored_meta.get("reason", "")) if ignored_meta is not None else "",
                "spam_candidate": "true"
                if _is_spam_candidate(asset=asset, qty=values["quantity"], known=meta["is_known"])
                else "false",
            }
        )

    data = {
        "group_id": payload.group_id,
        "wallet_count": len(wallets),
        "wallets": wallets,
        "total_sol_balance": total_sol_balance.normalize().to_eng_string(),
        "total_estimated_usd": total_estimated_usd.normalize().to_eng_string()
        if total_estimated_usd > 0
        else "",
        "token_count": len(grouped_tokens),
        "tokens": grouped_tokens[: payload.max_tokens],
        "wallet_results": wallet_results,
    }
    write_audit(
        trace_id=trace_id,
        action="connectors.solana.group_balance_snapshot",
        payload={"group_id": payload.group_id, "wallet_count": len(wallets), "warnings": len(warnings)},
    )
    _append_wallet_snapshot(
        scope="group",
        entity_id=(payload.group_id or ",".join(wallets)),
        total_estimated_usd=str(data.get("total_estimated_usd", "")),
        sol_balance=str(data.get("total_sol_balance", "")),
    )
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=warnings)


@app.post(
    "/api/v1/connectors/solana/wallet-preview",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_solana_wallet_preview(payload: SolanaWalletPreviewRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        result = fetch_solana_wallet_preview(
            wallet_address=payload.wallet_address,
            rpc_url=payload.rpc_url,
            rpc_fallback_urls=payload.rpc_fallback_urls,
            before_signature=payload.before_signature,
            timeout_seconds=payload.timeout_seconds,
            max_signatures=payload.max_signatures,
            max_transactions=payload.max_transactions,
            aggregate_jupiter=payload.aggregate_jupiter,
            jupiter_window_seconds=payload.jupiter_window_seconds,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="connectors.solana.wallet_preview",
            payload={
                "wallet_address": payload.wallet_address,
                "rpc_url": payload.rpc_url,
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_error", "message": str(exc)}],
            warnings=[],
        )

    write_audit(
        trace_id=trace_id,
        action="connectors.solana.wallet_preview",
        payload={
            "wallet_address": payload.wallet_address,
            "rpc_url": payload.rpc_url,
            "rpc_fallback_count": len(payload.rpc_fallback_urls),
            "before_signature": payload.before_signature,
            "ok": True,
            "rows": result.get("count", 0),
            "aggregate_jupiter": payload.aggregate_jupiter,
            "jupiter_window_seconds": payload.jupiter_window_seconds,
        },
    )
    warnings = result.get("warnings", [])
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data=result,
        errors=[],
        warnings=warnings if isinstance(warnings, list) else [],
    )


@app.post(
    "/api/v1/connectors/solana/import-confirm",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_solana_import_confirm(payload: SolanaImportConfirmRequest) -> StandardResponse:
    trace_id = str(uuid4())
    try:
        preview = fetch_solana_wallet_preview(
            wallet_address=payload.wallet_address,
            rpc_url=payload.rpc_url,
            rpc_fallback_urls=payload.rpc_fallback_urls,
            before_signature=payload.before_signature,
            timeout_seconds=payload.timeout_seconds,
            max_signatures=payload.max_signatures,
            max_transactions=payload.max_transactions,
            aggregate_jupiter=payload.aggregate_jupiter,
            jupiter_window_seconds=payload.jupiter_window_seconds,
        )
    except Exception as exc:
        write_audit(
            trace_id=trace_id,
            action="connectors.solana.import_confirm",
            payload={
                "wallet_address": payload.wallet_address,
                "rpc_url": payload.rpc_url,
                "ok": False,
                "exception": str(exc),
            },
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "connector_error", "message": str(exc)}],
            warnings=[],
        )

    rows = preview.get("rows", [])
    if not isinstance(rows, list):
        rows = []

    source_name = payload.source_name or "solana_wallet_api_import"
    import_result = confirm_import(source_name=source_name, rows=rows)
    warnings = preview.get("warnings", [])
    write_audit(
        trace_id=trace_id,
        action="connectors.solana.import_confirm",
        payload={
            "wallet_address": payload.wallet_address,
            "rpc_url": payload.rpc_url,
            "rpc_fallback_count": len(payload.rpc_fallback_urls),
            "before_signature": payload.before_signature,
            "source_name": source_name,
            "fetched_rows": len(rows),
            "inserted_events": import_result["inserted_events"],
            "duplicate_events": import_result["duplicate_events"],
            "aggregate_jupiter": payload.aggregate_jupiter,
            "jupiter_window_seconds": payload.jupiter_window_seconds,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "wallet_address": payload.wallet_address,
            "rpc_url": payload.rpc_url,
            "source_name": source_name,
            "signature_count": preview.get("signature_count", 0),
            "first_signature": preview.get("first_signature"),
            "last_signature": preview.get("last_signature"),
            "fetched_rows": len(rows),
            "preview_count": preview.get("count", len(rows)),
            "import_result": import_result,
        },
        errors=[],
        warnings=warnings if isinstance(warnings, list) else [],
    )


@app.post(
    "/api/v1/connectors/solana/import-full-history",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_solana_import_full_history(payload: SolanaFullHistoryImportRequest) -> StandardResponse:
    trace_id = str(uuid4())
    start_ms = payload.start_time_ms if payload.start_time_ms is not None else int(
        datetime(2020, 1, 1, tzinfo=UTC).timestamp() * 1000
    )
    end_ms = payload.end_time_ms if payload.end_time_ms is not None else int(datetime.now(UTC).timestamp() * 1000)
    if start_ms >= end_ms:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_time_window", "message": "start_time_ms muss kleiner als end_time_ms sein"}],
            warnings=[],
        )

    cursor: str | None = payload.before_signature
    calls = 0
    total_scanned_signatures = 0
    total_fetched_rows = 0
    total_inserted_events = 0
    total_duplicate_events = 0
    failed_calls = 0
    warnings: list[dict[str, str]] = []
    reached_start = False
    seen_before_signatures: set[str] = set()

    base_source_name = (payload.source_name or f"solana_wallet_{payload.wallet_address}_full").strip()
    max_per_call = max(1, int(payload.max_signatures_per_call))
    remaining_total = int(payload.max_signatures_total)

    while total_scanned_signatures < remaining_total:
        calls += 1
        per_call_limit = min(max_per_call, remaining_total - total_scanned_signatures)
        try:
            preview = fetch_solana_wallet_full_history(
                wallet_address=payload.wallet_address,
                rpc_url=payload.rpc_url,
                rpc_fallback_urls=payload.rpc_fallback_urls,
                timeout_seconds=payload.timeout_seconds,
                start_time_ms=start_ms,
                end_time_ms=end_ms,
                before_signature=cursor,
                max_signatures_per_call=per_call_limit,
                max_signatures_total=per_call_limit,
                aggregate_jupiter=payload.aggregate_jupiter,
                jupiter_window_seconds=payload.jupiter_window_seconds,
            )
        except Exception as exc:
            failed_calls += 1
            warnings.append(
                {"code": "full_history_fetch_failed", "message": f"call={calls}: {exc}"}
            )
            break

        chunk_rows = preview.get("rows", [])
        if not isinstance(chunk_rows, list):
            chunk_rows = []

        scanned_this_call = int(preview.get("signature_scanned_count", 0))
        total_scanned_signatures += scanned_this_call
        total_fetched_rows += len(chunk_rows)
        import_result = confirm_import(
            source_name=f"{base_source_name}_chunk_{calls:03d}",
            rows=chunk_rows,
        )
        total_inserted_events += int(import_result.get("inserted_events", 0))
        total_duplicate_events += int(import_result.get("duplicate_events", 0))
        raw_warnings = preview.get("warnings", [])
        if isinstance(raw_warnings, list):
            for item in raw_warnings:
                if isinstance(item, dict):
                    warnings.append(
                        {
                            "code": str(item.get("code", "connector_warning")),
                            "message": str(item.get("message", item.get("signature", ""))),
                        }
                    )
        reached_start = bool(preview.get("reached_start", False))
        if reached_start:
            break

        next_cursor = preview.get("next_before_signature")
        if not isinstance(next_cursor, str) or not next_cursor:
            break
        if next_cursor in seen_before_signatures:
            warnings.append(
                {"code": "cursor_repeated", "message": f"Cursor wiederholt: {next_cursor}"}
            )
            break
        seen_before_signatures.add(next_cursor)
        cursor = next_cursor

        if calls >= 10000:
            warnings.append(
                {"code": "cursor_safety_limit", "message": "Sicherheitssperre erreicht (maximal 10000 Seiten)."}
            )
            break

    write_audit(
        trace_id=trace_id,
        action="connectors.solana.import_full_history",
        payload={
            "wallet_address": payload.wallet_address,
            "source_name": base_source_name,
            "calls": calls,
            "wallet_address_length": len(payload.wallet_address),
            "start_time_ms": start_ms,
            "end_time_ms": end_ms,
            "rpc_fallback_count": len(payload.rpc_fallback_urls),
            "before_signature": payload.before_signature,
            "max_signatures_per_call": max_per_call,
            "max_signatures_total": remaining_total,
            "scanned_signatures": total_scanned_signatures,
            "fetched_rows": total_fetched_rows,
            "inserted_events": total_inserted_events,
            "duplicate_events": total_duplicate_events,
            "reached_start": reached_start,
            "failed_calls": failed_calls,
        },
    )

    status = "partial" if failed_calls > 0 else "success"
    return StandardResponse(
        trace_id=trace_id,
        status=status,
        data={
            "wallet_address": payload.wallet_address,
            "source_name": base_source_name,
            "start_time_ms": start_ms,
            "end_time_ms": end_ms,
            "calls": calls,
            "chunks_processed": calls,
            "scanned_signatures": total_scanned_signatures,
            "total_fetched_rows": total_fetched_rows,
            "total_inserted_events": total_inserted_events,
            "total_duplicate_events": total_duplicate_events,
            "reached_start": reached_start,
            "next_before_signature": cursor,
            "last_before_signature": cursor,
            "failed_calls": failed_calls,
        },
        errors=[],
        warnings=warnings,
    )


@app.post(
    "/api/v1/connectors/solana/group-import-confirm",
    response_model=StandardResponse,
    tags=["connectors"],
)
def connectors_solana_group_import_confirm(payload: SolanaGroupImportConfirmRequest) -> StandardResponse:
    trace_id = str(uuid4())
    wallets = _resolve_wallets_from_group(payload.group_id, payload.wallet_addresses)
    if not wallets:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "wallets_empty", "message": "Keine Wallets für Gruppenimport vorhanden."}],
            warnings=[],
        )

    all_rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    wallet_results: list[dict[str, Any]] = []

    for wallet in wallets:
        try:
            preview = fetch_solana_wallet_preview(
                wallet_address=wallet,
                rpc_url=payload.rpc_url,
                rpc_fallback_urls=payload.rpc_fallback_urls,
                before_signature=None,
                timeout_seconds=payload.timeout_seconds,
                max_signatures=payload.max_signatures,
                max_transactions=payload.max_transactions,
                aggregate_jupiter=payload.aggregate_jupiter,
                jupiter_window_seconds=payload.jupiter_window_seconds,
            )
            rows = preview.get("rows", [])
            if isinstance(rows, list):
                all_rows.extend(rows)
            wallet_results.append(
                {
                    "wallet_address": wallet,
                    "signature_count": preview.get("signature_count", 0),
                    "row_count": len(rows) if isinstance(rows, list) else 0,
                    "last_signature": preview.get("last_signature"),
                }
            )
            raw_warnings = preview.get("warnings", [])
            if isinstance(raw_warnings, list):
                warnings.extend(raw_warnings)
        except Exception as exc:
            warnings.append({"code": "wallet_import_failed", "message": f"{wallet}: {exc}"})

    source_name = (payload.source_name or "").strip() or f"solana_group_{payload.group_id or 'manual'}_import"
    import_result = confirm_import(source_name=source_name, rows=all_rows)
    write_audit(
        trace_id=trace_id,
        action="connectors.solana.group_import_confirm",
        payload={
            "group_id": payload.group_id,
            "wallet_count": len(wallets),
            "fetched_rows": len(all_rows),
            "inserted_events": import_result["inserted_events"],
            "duplicate_events": import_result["duplicate_events"],
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "group_id": payload.group_id,
            "wallet_count": len(wallets),
            "wallet_results": wallet_results,
            "fetched_rows": len(all_rows),
            "source_name": source_name,
            "import_result": import_result,
        },
        errors=[],
        warnings=warnings,
    )


@app.post("/api/v1/process/run", response_model=StandardResponse, tags=["process"])
def process_run(payload: ProcessRunRequest) -> StandardResponse:
    trace_id = str(uuid4())
    registry = build_default_registry()
    try:
        resolved_ruleset, ruleset_warnings = registry.resolve_for_year(
            tax_year=payload.tax_year,
            ruleset_id=payload.ruleset_id,
            ruleset_version=payload.ruleset_version,
        )
    except ValueError as exc:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "ruleset_not_resolvable", "message": str(exc)}],
            warnings=[],
        )
    job = create_processing_job(payload)
    warnings: list[dict[str, str]] = list(ruleset_warnings)
    if resolved_ruleset.ruleset_id != payload.ruleset_id or (
        payload.ruleset_version is not None and resolved_ruleset.ruleset_version != payload.ruleset_version
    ):
        warnings.append(
            {
                "code": "ruleset_resolved",
                "message": (
                    f"Ruleset-Eingabe wurde auf {resolved_ruleset.ruleset_id} "
                    f"v{resolved_ruleset.ruleset_version} normalisiert."
                ),
            }
        )
    events = STORE.list_raw_events()
    year_count = 0
    for row in events:
        item = row.get("payload", {})
        if not isinstance(item, dict):
            continue
        ts_raw = str(item.get("timestamp_utc") or item.get("timestamp") or "")
        year = _extract_year(ts_raw)
        if year == payload.tax_year:
            year_count += 1
    if year_count == 0:
        warnings.append(
            {
                "code": "tax_year_no_events",
                "message": (
                    f"Keine Events mit Jahr {payload.tax_year} gefunden. "
                    "Bitte Tax Year oder Importdaten prüfen."
                ),
            }
        )
    write_audit(
        trace_id=trace_id,
        action="process.run",
        payload={
            "job_id": job["job_id"],
            "tax_year": payload.tax_year,
            "ruleset_id": payload.ruleset_id,
            "resolved_ruleset_id": job.get("ruleset_id"),
            "resolved_ruleset_version": job.get("ruleset_version"),
            "dry_run": payload.dry_run,
            "tax_year_event_count": year_count,
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=job, errors=[], warnings=warnings)


@app.get("/api/v1/process/status/{job_id}", response_model=StandardResponse, tags=["process"])
def process_status(job_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(job_id)
    if job is None:
        write_audit(
            trace_id=trace_id,
            action="process.status",
            payload={"job_id": job_id, "found": False},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )

    write_audit(
        trace_id=trace_id,
        action="process.status",
        payload={"job_id": job_id, "found": True, "status": job["status"]},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=job, errors=[], warnings=[])


@app.get("/api/v1/process/latest", response_model=StandardResponse, tags=["process"])
def process_latest() -> StandardResponse:
    trace_id = str(uuid4())
    job = STORE.get_latest_processing_job()
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="success",
            data={"job": None},
            errors=[],
            warnings=[{"code": "no_processing_jobs", "message": "Noch kein Processing-Job vorhanden."}],
        )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"job": job},
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/process/jobs", response_model=StandardResponse, tags=["process"])
def process_jobs(status: str | None = None, limit: int = 50, offset: int = 0) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = max(1, min(int(limit), 5000))
    safe_offset = max(0, int(offset))
    rows = STORE.list_processing_jobs(status=status, limit=safe_limit, offset=safe_offset)
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "offset": safe_offset, "limit": safe_limit, "rows": rows},
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/import/jobs", response_model=StandardResponse, tags=["import"])
def import_jobs(
    status: str | None = None,
    integration: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = max(1, min(int(limit), 5000))
    safe_offset = max(0, int(offset))
    rows = _build_import_job_rows(
        status=status,
        integration=integration,
        limit=safe_limit,
        offset=safe_offset,
    )
    write_audit(
        trace_id=trace_id,
        action="import.jobs",
        payload={
            "status": status,
            "integration": integration,
            "count": len(rows),
            "limit": safe_limit,
            "offset": safe_offset,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "offset": safe_offset, "limit": safe_limit, "rows": rows},
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/report/export", response_model=None)
def report_export(
    job_id: str,
    scope: str = "all",
    fmt: str = "json",
    part: int = 1,
) -> StandardResponse | StreamingResponse:
    trace_id = str(uuid4())
    scope_normalized = str(scope or "all").strip().lower()
    fmt_normalized = str(fmt or "json").strip().lower()
    include_derivatives = scope_normalized in {"all", "derivatives"}
    include_tax = scope_normalized in {"all", "tax"}

    if scope_normalized not in {"all", "tax", "derivatives"}:
        write_audit(
            trace_id=trace_id,
            action="report.export",
            payload={"job_id": job_id, "scope": scope_normalized, "format": fmt_normalized, "error": "invalid_scope"},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_scope", "message": "scope muss all|tax|derivatives sein."}],
            warnings=[],
        )

    if fmt_normalized not in {"json", "csv", "pdf"}:
        write_audit(
            trace_id=trace_id,
            action="report.export",
            payload={"job_id": job_id, "scope": scope_normalized, "format": fmt_normalized, "error": "invalid_format"},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_format", "message": "fmt muss json|csv|pdf sein."}],
            warnings=[],
        )

    job = get_processing_job(job_id)
    if job is None:
        write_audit(
            trace_id=trace_id,
            action="report.export",
            payload={"job_id": job_id, "found": False},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )

    tax_lines = STORE.get_tax_lines(job_id) if include_tax else []
    derivative_lines = STORE.get_derivative_lines(job_id) if include_derivatives else []
    integrity = STORE.get_report_integrity(job_id)
    export_rows = _build_export_rows(
        job,
        tax_lines,
        derivative_lines,
        include_derivatives=include_derivatives,
        integrity=integrity,
    )
    total_parts = max(1, (len(export_rows) + _PDF_ROWS_PER_FILE - 1) // _PDF_ROWS_PER_FILE)
    safe_part = max(1, int(part))
    if fmt_normalized == "pdf" and safe_part > total_parts:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={"job_id": job_id, "scope": scope_normalized, "part_count": total_parts},
            errors=[{"code": "report_part_not_found", "message": f"PDF-Teil {safe_part} existiert nicht."}],
            warnings=[],
        )
    write_audit(
        trace_id=trace_id,
        action="report.export",
        payload={
            "job_id": job_id,
            "scope": scope_normalized,
            "format": fmt_normalized,
            "part": safe_part,
            "tax_lines": len(tax_lines),
            "derivative_lines": len(derivative_lines),
        },
    )

    if fmt_normalized == "csv":
        csv_content = _build_csv_from_rows(export_rows)
        filename = f"steuerreport_{job_id}.csv"
        headers = {
            "Content-Disposition": f'attachment; filename=\"{filename}\"',
        }
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv; charset=utf-8",
            headers=headers,
        )

    if fmt_normalized == "pdf":
        start = (safe_part - 1) * _PDF_ROWS_PER_FILE
        selected_rows = export_rows[start : start + _PDF_ROWS_PER_FILE]
        pdf_content = _build_pdf_from_rows(
            job=job,
            rows=selected_rows,
            integrity=integrity,
            scope=scope_normalized,
            part=safe_part,
            part_count=total_parts,
        )
        filename = f"steuerreport_{job_id}_{scope_normalized}_teil_{safe_part}_von_{total_parts}.pdf"
        headers = {
            "Content-Disposition": f'attachment; filename=\"{filename}\"',
        }
        return StreamingResponse(
            iter([pdf_content]),
            media_type="application/pdf",
            headers=headers,
        )

    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "job_id": job_id,
            "scope": scope_normalized,
            "part_count": total_parts,
            "job": {
                "tax_year": job.get("tax_year"),
                "ruleset_id": job.get("ruleset_id"),
                "ruleset_version": job.get("ruleset_version"),
            },
            "integrity": integrity,
            "rows": export_rows,
        },
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/report/files/{run_id}", response_model=StandardResponse, tags=["report"])
def report_files(run_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(run_id)
    if job is None:
        write_audit(
            trace_id=trace_id,
            action="report.files",
            payload={"run_id": run_id, "found": False},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Run not found: {run_id}"}],
            warnings=[],
        )

    tax_lines = STORE.get_tax_lines(run_id)
    derivative_lines = STORE.get_derivative_lines(run_id)
    files = _build_report_file_index(
        job=job,
        tax_line_count=len(tax_lines),
        derivative_line_count=len(derivative_lines),
    )
    write_audit(
        trace_id=trace_id,
        action="report.files",
        payload={
            "run_id": run_id,
            "file_count": len(files),
            "tax_line_count": len(tax_lines),
            "derivative_line_count": len(derivative_lines),
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "run_id": run_id,
            "status": job.get("status"),
            "tax_year": job.get("tax_year"),
            "ruleset_id": job.get("ruleset_id"),
            "ruleset_version": job.get("ruleset_version"),
            "tax_line_count": len(tax_lines),
            "derivative_line_count": len(derivative_lines),
            "files": files,
        },
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/compliance/classification/{run_id}", response_model=StandardResponse, tags=["compliance"])
def compliance_classification(run_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    run = get_processing_job(run_id)
    if run is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "run_not_found", "message": f"Lauf nicht gefunden: {run_id}"}],
            warnings=[],
        )

    tax_year = int(run["tax_year"])
    events = STORE.list_raw_events()
    year_events: list[dict[str, Any]] = []
    for row in events:
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if _extract_year(ts_raw) == tax_year:
            year_events.append(payload)

    ruleset_id = str(run.get("ruleset_id", "DE-2026-v1.0"))
    run_ruleset_version = str(run.get("ruleset_version") or "").strip()
    ruleset_version = run_ruleset_version if run_ruleset_version else None
    registry = build_default_registry()
    try:
        ruleset = registry.get(ruleset_id, ruleset_version)
    except Exception:
        ruleset = registry.get("DE-2026-v1.0", "1.0")

    trading_like = 0
    transfer_like = 0
    reward_events = 0
    mining_events = 0
    reward_value = Decimal("0")
    trading_days: set[str] = set()

    def _is_reward_like(payload: dict[str, Any]) -> bool:
        text = " ".join(
            str(payload.get(key, "")).lower()
            for key in ("event_type", "type", "label", "comment", "description", "source", "tag")
        )
        event_type = str(payload.get("event_type", "")).lower().strip()
        return event_type in {
            "mining_reward",
            "staking_reward",
            "asset_dividend",
            "interest",
            "reward_claim",
            "reward",
        } or any(token in text for token in ("reward", "staking", "mining", "claim", "dividend", "interest"))

    def _is_mining_like(payload: dict[str, Any]) -> bool:
        text = " ".join(
            str(payload.get(key, "")).lower()
            for key in ("event_type", "type", "source", "comment", "description", "tag")
        )
        source = str(payload.get("source", "")).lower().strip()
        asset = str(payload.get("asset", "")).lower().strip()
        return (
            "mining" in text
            or source == "heliumgeek"
            or asset in {"hnt", "iot", "mobile", "myst"}
            or any(token in text for token in ("hotspot", "solana", "vehnt"))
        )

    for payload in year_events:
        event_type = str(payload.get("event_type", "")).lower().strip()
        side = str(payload.get("side", "")).lower().strip()
        if event_type in {"buy", "sell", "trade", "swap"} or side in {"buy", "sell"}:
            trading_like += 1
        if event_type in {"transfer_in", "transfer_out", "airdrop", "fee", "staking"} or side in {"in", "out"}:
            transfer_like += 1
        if _is_reward_like(payload):
            reward_events += 1
            reward_value += abs(_safe_decimal(payload.get("value_eur")))
        if _is_mining_like(payload):
            mining_events += 1

        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        day = ts_raw[:10] if len(ts_raw) >= 10 else ""
        if day:
            if event_type in {"buy", "sell", "trade", "swap"} or side in {"buy", "sell"}:
                trading_days.add(day)

    active_days = max(len(trading_days), 1)
    avg_trades_per_day = (Decimal(trading_like) / Decimal(active_days)) if active_days else Decimal("0")
    threshold_services = ruleset.other_services_exemption_limit if ruleset is not None else Decimal("256")

    high_frequency = trading_like >= 15000 or avg_trades_per_day >= Decimal("10")
    medium_frequency = trading_like >= 2000 or avg_trades_per_day >= Decimal("3")
    mining_exceeded = reward_events > 0 and reward_value >= threshold_services
    is_business = high_frequency or (mining_exceeded and mining_events > 0)
    level = "red" if high_frequency else ("yellow" if (medium_frequency or mining_exceeded) else "green")
    reasons: list[dict[str, Any]] = []
    if high_frequency:
        reasons.append(
            {
                "code": "high_frequency",
                "message": (
                    f"{trading_like} Trading-Events im Jahr {tax_year} "
                    f"({avg_trades_per_day:.2f}/Tag) deuten auf gewerbsmäßige Nutzung."
                ),
            }
        )
    if mining_exceeded:
        reasons.append(
            {
                "code": "mining_threshold",
                "message": (
                    f"Mining/Staking-Einnahmen {reward_value.to_eng_string()} EUR "
                    f"überschreiten die §22-Freigrenze {threshold_services.to_eng_string()} EUR."
                ),
            }
        )

    warnings: list[dict[str, str]] = []
    if level != "green":
        warnings.append(
            {
                "code": "commercial_risk",
                "message": "Prüfe den Status mit Steuerberater und ggf. Anlage G / Gewerbe-EÜR.",
            }
        )

    write_audit(
        trace_id=trace_id,
        action="compliance.classification",
        payload={
            "run_id": run_id,
            "level": level,
            "is_business": is_business,
            "trading_events": trading_like,
            "reward_events": reward_events,
            "mining_events": mining_events,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "run_id": run_id,
            "tax_year": tax_year,
            "is_commercial": is_business,
            "classification_level": level,
            "signals": {
                "trading_events": trading_like,
                "transfer_events": transfer_like,
                "reward_events": reward_events,
                "mining_events": mining_events,
                "active_trading_days": len(trading_days),
                "avg_trades_per_active_day": str(avg_trades_per_day),
                "reward_value_eur": reward_value.to_eng_string(),
            },
            "ruleset": {
                "ruleset_id": ruleset.ruleset_id,
                "ruleset_version": ruleset.ruleset_version,
                "jurisdiction": ruleset.jurisdiction,
                "exemption_limit_so": ruleset.exemption_limit_so.to_eng_string(),
                "other_services_exemption_limit": ruleset.other_services_exemption_limit.to_eng_string(),
                "holding_period_months": ruleset.holding_period_months,
            },
            "reasons": reasons,
        },
        errors=[],
        warnings=warnings,
    )


@app.get("/api/v1/integrity/report/{run_id}", response_model=StandardResponse, tags=["integrity"])
def integrity_report(run_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    info = STORE.get_report_integrity(run_id)
    if info is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "report_integrity_not_found", "message": f"No integration data for run {run_id}"}],
            warnings=[],
        )
    return StandardResponse(trace_id=trace_id, status="success", data=info, errors=[], warnings=[])


@app.post(
    "/api/v1/snapshots/create/{run_id}",
    response_model=StandardResponse,
    tags=["integrity"],
)
def create_snapshot(run_id: str, payload: ReportSnapshotCreateRequest) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(run_id)
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Run not found: {run_id}"}],
            warnings=[],
        )
    result_summary = job.get("result_summary")
    if result_summary is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "result_summary_missing", "message": "Run has no persisted result_summary"}],
            warnings=[],
        )
    snapshot_id = STORE.create_report_snapshot(
        job_id=run_id,
        payload_json=json.dumps(result_summary, sort_keys=True, separators=(",", ":")),
        summary_json=json.dumps(result_summary.get("tax_domain_summary", {}), sort_keys=True, separators=(",", ":")),
        notes=payload.notes,
    )
    snapshot = STORE.get_report_snapshot(snapshot_id)
    if snapshot is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "snapshot_creation_failed", "message": "Snapshot konnte nicht gespeichert werden"}],
            warnings=[],
        )
    return StandardResponse(trace_id=trace_id, status="success", data=snapshot, errors=[], warnings=[])


@app.get("/api/v1/snapshots/{snapshot_id}", response_model=StandardResponse, tags=["integrity"])
def get_snapshot(snapshot_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    snapshot = STORE.get_report_snapshot(snapshot_id)
    if snapshot is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "snapshot_not_found", "message": f"Snapshot not found: {snapshot_id}"}],
            warnings=[],
        )
    try:
        payload = json.loads(snapshot.get("payload_json", "{}"))
    except Exception:
        payload = {}
    try:
        summary = json.loads(snapshot.get("summary_json", "{}"))
    except Exception:
        summary = {}
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "snapshot_id": snapshot["snapshot_id"],
            "job_id": snapshot["job_id"],
            "created_at_utc": snapshot["created_at_utc"],
            "notes": snapshot.get("notes"),
            "payload": payload,
            "summary": summary,
        },
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/integrity/event/{unique_event_id}", response_model=StandardResponse, tags=["integrity"])
def integrity_event(unique_event_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    raw_event = STORE.get_raw_event(unique_event_id)
    if raw_event is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "event_not_found", "message": f"Raw event not found: {unique_event_id}"}],
            warnings=[],
        )
    jobs = STORE.list_jobs_using_event(unique_event_id=unique_event_id)
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"event": raw_event, "jobs": jobs},
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/process/compare-rulesets", response_model=StandardResponse, tags=["process"])
def process_compare_rulesets(
    job_id: str,
    compare_ruleset_id: str,
    compare_ruleset_version: str | None = None,
) -> StandardResponse:
    return _process_compare_rulesets_impl(
        job_id=job_id,
        compare_ruleset_id=compare_ruleset_id,
        compare_ruleset_version=compare_ruleset_version,
    )


@app.post("/api/v1/process/compare-rulesets", response_model=StandardResponse, tags=["process"])
def process_compare_rulesets_post(payload: ProcessCompareRulesetsRequest) -> StandardResponse:
    return _process_compare_rulesets_impl(
        job_id=payload.job_id,
        compare_ruleset_id=payload.compare_ruleset_id,
        compare_ruleset_version=payload.compare_ruleset_version,
    )


def _process_compare_rulesets_impl(
    job_id: str,
    compare_ruleset_id: str,
    compare_ruleset_version: str | None = None,
) -> StandardResponse:
    trace_id = str(uuid4())
    base_job = get_processing_job(job_id)
    if base_job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Run not found: {job_id}"},
            ],
            warnings=[],
        )

    raw_events = STORE.list_raw_events()
    if not raw_events:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "no_raw_events", "message": "No raw events available for comparison"}],
            warnings=[],
        )

    tax_year = int(base_job["tax_year"])
    try:
        compare_result = process_events_for_year(
            raw_events=raw_events,
            tax_year=tax_year,
            ruleset_id=compare_ruleset_id,
            ruleset_version=compare_ruleset_version,
        )
        derivative_result = process_derivatives_for_year(raw_events=raw_events, tax_year=tax_year)
        compare_summary = build_tax_domain_summary(
            raw_events=raw_events,
            tax_lines=compare_result.get("tax_lines", []),
            derivative_lines=derivative_result.get("lines", []),
            tax_year=tax_year,
            ruleset_id=compare_ruleset_id,
        )
    except Exception as exc:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "compare_failed", "message": str(exc)}],
            warnings=[],
        )

    base_summary = {}
    base_tax_summary = {}
    if base_job.get("result_summary") is not None:
        base_summary = base_job["result_summary"]
        base_tax_summary = base_summary.get("tax_domain_summary", {})
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "job_id": job_id,
            "tax_year": tax_year,
            "compare_ruleset_id": compare_ruleset_id,
            "compare_ruleset_version": compare_ruleset_version,
            "base": {
                "ruleset_id": base_job.get("ruleset_id"),
                "ruleset_version": base_job.get("ruleset_version"),
                "result_summary": base_summary,
                "tax_domain_summary": base_tax_summary,
            },
            "comparison": {
                "ruleset_id": compare_ruleset_id,
                "ruleset_version": compare_ruleset_version,
                "result_summary": compare_result,
                "tax_domain_summary": compare_summary,
            },
        },
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/process/tax-lines/{job_id}", response_model=StandardResponse, tags=["process"])
def process_tax_lines(job_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(job_id)
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )
    lines = STORE.get_tax_lines(job_id)
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"job_id": job_id, "count": len(lines), "lines": lines},
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/process/tax-domain-summary/{job_id}", response_model=StandardResponse, tags=["process"])
def process_tax_domain_summary(job_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(job_id)
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )
    result_summary = job.get("result_summary")
    if not isinstance(result_summary, dict):
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "result_not_available", "message": "Job result summary not available"}],
            warnings=[],
        )
    tax_domain_summary = result_summary.get("tax_domain_summary")
    if not isinstance(tax_domain_summary, dict):
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "tax_domain_summary_missing", "message": "No tax domain summary in result"}],
            warnings=[],
        )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"job_id": job_id, "tax_domain_summary": tax_domain_summary},
        errors=[],
        warnings=[],
    )


@app.get(
    "/api/v1/audit/tax-line/{job_id}/{line_no}",
    response_model=StandardResponse,
    tags=["audit"],
)
def audit_tax_line(job_id: str, line_no: int) -> StandardResponse:
    trace_id = str(uuid4())
    if line_no <= 0:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_line_no", "message": "line_no muss > 0 sein"}],
            warnings=[],
        )

    job = get_processing_job(job_id)
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )

    tax_line = STORE.get_tax_line(job_id=job_id, line_no=line_no)
    if tax_line is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "tax_line_not_found", "message": f"Tax line not found: {job_id}#{line_no}"}],
            warnings=[],
        )

    source_event = STORE.get_raw_event(tax_line["source_event_id"])
    calculation_trace = {
        "formula": "gain_loss_eur = proceeds_eur - cost_basis_eur",
        "cost_basis_eur": tax_line["cost_basis_eur"],
        "proceeds_eur": tax_line["proceeds_eur"],
        "gain_loss_eur": tax_line["gain_loss_eur"],
        "holding_period_days": tax_line["hold_days"],
        "tax_status": tax_line["tax_status"],
    }
    write_audit(
        trace_id=trace_id,
        action="audit.tax_line",
        payload={
            "job_id": job_id,
            "line_no": line_no,
            "source_event_found": source_event is not None,
        },
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={
            "job_id": job_id,
            "line_no": line_no,
            "tax_year": job["tax_year"],
            "ruleset_id": job["ruleset_id"],
            "tax_line": tax_line,
            "source_event": source_event,
            "calculation_trace": calculation_trace,
        },
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/process/derivative-lines/{job_id}", response_model=StandardResponse, tags=["process"])
def process_derivative_lines(job_id: str) -> StandardResponse:
    trace_id = str(uuid4())
    job = get_processing_job(job_id)
    if job is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "job_not_found", "message": f"Job not found: {job_id}"}],
            warnings=[],
        )
    lines = STORE.get_derivative_lines(job_id)
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"job_id": job_id, "count": len(lines), "lines": lines},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/process/worker/run-next", response_model=StandardResponse, tags=["process"])
def process_worker_run_next(payload: WorkerRunNextRequest) -> StandardResponse:
    trace_id = str(uuid4())
    processed = run_next_queued_job(simulate_fail=payload.simulate_fail)
    if processed is None:
        write_audit(
            trace_id=trace_id,
            action="process.worker.run_next",
            payload={"processed_job": False},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="success",
            data={},
            errors=[],
            warnings=[{"code": "no_queued_job", "message": "No queued job available"}],
        )

    write_audit(
        trace_id=trace_id,
        action="process.worker.run_next",
        payload={
            "processed_job": True,
            "job_id": processed["job_id"],
            "status": processed["status"],
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=processed, errors=[], warnings=[])


@app.post("/api/v1/reconcile/auto-match", response_model=StandardResponse, tags=["reconcile"])
def reconcile_auto_match(payload: AutoMatchRequest) -> StandardResponse:
    trace_id = str(uuid4())
    result = auto_match_and_persist(
        time_window_seconds=payload.time_window_seconds,
        amount_tolerance_ratio=payload.amount_tolerance_ratio,
        min_confidence=payload.min_confidence,
    )
    write_audit(
        trace_id=trace_id,
        action="reconcile.auto_match",
        payload={
            "persisted_match_count": result["persisted_match_count"],
            "unmatched_outbound_count": len(result["unmatched_outbound_ids"]),
            "unmatched_inbound_count": len(result["unmatched_inbound_ids"]),
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@app.get("/api/v1/review/unmatched", response_model=StandardResponse, tags=["reconcile"])
def review_unmatched(
    time_window_seconds: int = 600,
    amount_tolerance_ratio: float = 0.02,
    min_confidence: float = 0.75,
) -> StandardResponse:
    trace_id = str(uuid4())
    result = list_unmatched_transfers(
        time_window_seconds=time_window_seconds,
        amount_tolerance_ratio=amount_tolerance_ratio,
        min_confidence=min_confidence,
    )
    write_audit(
        trace_id=trace_id,
        action="review.unmatched",
        payload={
            "unmatched_outbound_count": len(result["unmatched_outbound_ids"]),
            "unmatched_inbound_count": len(result["unmatched_inbound_ids"]),
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@app.get("/api/v1/review/gates", response_model=StandardResponse, tags=["reconcile"])
def review_gates(
    job_id: str | None = None,
    time_window_seconds: int = 600,
    amount_tolerance_ratio: float = 0.02,
    min_confidence: float = 0.75,
) -> StandardResponse:
    trace_id = str(uuid4())
    issues = _build_issue_inbox()
    unmatched = list_unmatched_transfers(
        time_window_seconds=time_window_seconds,
        amount_tolerance_ratio=amount_tolerance_ratio,
        min_confidence=min_confidence,
    )

    open_statuses = {"open", "in_review"}
    open_issues = [item for item in issues if str(item.get("status", "")).lower() in open_statuses]
    open_high_issues = [item for item in open_issues if str(item.get("severity", "")).lower() == "high"]
    unmatched_outbound = unmatched.get("unmatched_outbound_ids", [])
    unmatched_inbound = unmatched.get("unmatched_inbound_ids", [])

    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    unmatched_total = len(unmatched_outbound) + len(unmatched_inbound)
    if unmatched_total > 0:
        blockers.append(
            {
                "code": "unmatched_transfers_open",
                "message": f"{unmatched_total} unmatched Transfers offen.",
            }
        )
    if open_high_issues:
        blockers.append(
            {
                "code": "high_severity_issues_open",
                "message": f"{len(open_high_issues)} High-Severity Issues sind nicht gelöst.",
            }
        )

    job_info: dict[str, Any] = {}
    if job_id:
        job = get_processing_job(job_id)
        if job is None:
            blockers.append({"code": "job_not_found", "message": f"Process Job nicht gefunden: {job_id}"})
        else:
            job_status = str(job.get("status", "unknown"))
            job_info = {
                "job_id": str(job.get("job_id", "")),
                "status": job_status,
                "progress": int(job.get("progress", 0) or 0),
                "tax_line_count": int(job.get("tax_line_count", 0) or 0),
                "derivative_line_count": int(job.get("derivative_line_count", 0) or 0),
            }
            if job_status != "completed":
                blockers.append(
                    {"code": "process_job_not_completed", "message": f"Process Job Status ist '{job_status}'."}
                )
            elif job_info["tax_line_count"] == 0 and job_info["derivative_line_count"] == 0:
                warnings.append(
                    {
                        "code": "process_job_empty",
                        "message": "Process Job ist abgeschlossen, enthält aber keine Tax/Derivative Lines.",
                    }
                )
    else:
        warnings.append({"code": "job_id_missing", "message": "Kein job_id angegeben; Process-Gate wurde nicht geprüft."})

    allow_export = len(blockers) == 0
    data = {
        "allow_export": allow_export,
        "blocking_reasons": blockers,
        "warning_reasons": warnings,
        "counts": {
            "issues_total": len(issues),
            "issues_open": len(open_issues),
            "issues_high_open": len(open_high_issues),
            "unmatched_outbound": len(unmatched_outbound),
            "unmatched_inbound": len(unmatched_inbound),
            "unmatched_total": unmatched_total,
        },
        "job": job_info,
    }
    write_audit(
        trace_id=trace_id,
        action="review.gates",
        payload={
            "allow_export": allow_export,
            "issues_open": len(open_issues),
            "issues_high_open": len(open_high_issues),
            "unmatched_total": unmatched_total,
            "job_id": job_id or "",
        },
    )
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=[])


@app.post("/api/v1/reconcile/manual", response_model=StandardResponse, tags=["reconcile"])
def reconcile_manual(payload: ManualMatchRequest) -> StandardResponse:
    trace_id = str(uuid4())
    result = manual_match(
        outbound_event_id=payload.outbound_event_id,
        inbound_event_id=payload.inbound_event_id,
        note=payload.note,
    )
    if not result["ok"]:
        write_audit(
            trace_id=trace_id,
            action="reconcile.manual",
            payload={"ok": False, "error": result["error"]},
        )
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": result["error"], "message": "Manual match failed"}],
            warnings=[],
        )

    write_audit(
        trace_id=trace_id,
        action="reconcile.manual",
        payload={"ok": True, "match_id": result["match_id"]},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@app.get("/api/v1/reconcile/ledger", response_model=StandardResponse, tags=["reconcile"])
def reconcile_ledger(limit: int = 200, offset: int = 0) -> StandardResponse:
    trace_id = str(uuid4())
    safe_limit = min(max(limit, 1), 1000)
    safe_offset = max(offset, 0)
    result = list_transfer_ledger(limit=safe_limit, offset=safe_offset)
    write_audit(
        trace_id=trace_id,
        action="reconcile.ledger",
        payload={"limit": safe_limit, "offset": safe_offset, "row_count": len(result.get("rows", []))},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=result, errors=[], warnings=[])


@app.get("/api/v1/issues/inbox", response_model=StandardResponse, tags=["issues"])
def issues_inbox() -> StandardResponse:
    trace_id = str(uuid4())
    issues = _build_issue_inbox()
    write_audit(
        trace_id=trace_id,
        action="issues.inbox",
        payload={"count": len(issues)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(issues), "issues": issues},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/issues/update-status", response_model=StandardResponse, tags=["issues"])
def issues_update_status(payload: IssueStatusUpdateRequest) -> StandardResponse:
    trace_id = str(uuid4())
    status = _normalize_issue_status(payload.status)
    if status is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_issue_status", "message": "status muss open|in_review|resolved|wont_fix sein"}],
            warnings=[],
        )
    overrides = _load_issue_overrides()
    issue_id = payload.issue_id.strip()
    overrides[issue_id] = {
        "status": status,
        "note": (payload.note or "").strip(),
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    put_admin_setting("runtime.issue_status_overrides", overrides, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="issues.update_status",
        payload={"issue_id": issue_id, "status": status},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"issue_id": issue_id, "status": status, "saved": True},
        errors=[],
        warnings=[],
    )


@app.get("/api/v1/tax/event-overrides", response_model=StandardResponse, tags=["tax"])
def tax_event_overrides_list() -> StandardResponse:
    trace_id = str(uuid4())
    overrides = _load_tax_event_overrides()
    rows = [
        {"source_event_id": event_id, **payload}
        for event_id, payload in sorted(overrides.items(), key=lambda item: item[0])
    ]
    write_audit(
        trace_id=trace_id,
        action="tax.event_overrides.list",
        payload={"count": len(rows)},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"count": len(rows), "rows": rows},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/tax/event-override/upsert", response_model=StandardResponse, tags=["tax"])
def tax_event_override_upsert(payload: TaxEventOverrideUpsertRequest) -> StandardResponse:
    trace_id = str(uuid4())
    category = _normalize_tax_event_category(payload.tax_category)
    if category is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "invalid_tax_category", "message": "tax_category muss PRIVATE_SO oder BUSINESS sein"}],
            warnings=[],
        )

    event_id = payload.source_event_id.strip()
    raw_event = STORE.get_raw_event(event_id)
    if raw_event is None:
        return StandardResponse(
            trace_id=trace_id,
            status="error",
            data={},
            errors=[{"code": "source_event_not_found", "message": f"Event nicht gefunden: {event_id}"}],
            warnings=[],
        )

    overrides = _load_tax_event_overrides()
    entry = {
        "tax_category": category,
        "note": (payload.note or "").strip(),
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    overrides[event_id] = entry
    put_admin_setting("runtime.tax_event_overrides", overrides, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="tax.event_override.upsert",
        payload={"source_event_id": event_id, "tax_category": category},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"source_event_id": event_id, **entry, "saved": True},
        errors=[],
        warnings=[],
    )


@app.post("/api/v1/tax/event-override/delete", response_model=StandardResponse, tags=["tax"])
def tax_event_override_delete(payload: TaxEventOverrideDeleteRequest) -> StandardResponse:
    trace_id = str(uuid4())
    event_id = payload.source_event_id.strip()
    overrides = _load_tax_event_overrides()
    deleted = event_id in overrides
    if deleted:
        del overrides[event_id]
        put_admin_setting("runtime.tax_event_overrides", overrides, is_secret=False)
    write_audit(
        trace_id=trace_id,
        action="tax.event_override.delete",
        payload={"source_event_id": event_id, "deleted": deleted},
    )
    return StandardResponse(
        trace_id=trace_id,
        status="success",
        data={"source_event_id": event_id, "deleted": deleted},
        errors=[],
        warnings=[],
    )


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


def _estimate_event_values(payload: dict[str, Any], asset: str, quantity: Decimal, runtime_fx: Decimal) -> dict[str, Any]:
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
        fx_rate = _usd_to_eur_rate_for_date(event_date, runtime_fx)

    eur = eur_direct
    usd = usd_direct
    if eur <= 0 and price_eur > 0 and qty_abs > 0:
        eur = price_eur * qty_abs
    if usd <= 0 and price_usd > 0 and qty_abs > 0:
        usd = price_usd * qty_abs
    if usd <= 0 and asset in {"USD", "USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD"}:
        usd = qty_abs
    if usd <= 0 and quote_asset in {"USD", "USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD"} and price > 0 and qty_abs > 0:
        usd = price * qty_abs
    if usd <= 0 and qty_abs > 0:
        cached = _cached_asset_usd_price(asset=asset, rate_date=event_date)
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


def _usd_to_eur_rate_for_date(rate_date: str, fallback_rate: Decimal) -> Decimal:
    if len(rate_date) >= 10:
        row = STORE.get_fx_rate_on_or_before(rate_date=rate_date[:10], base_ccy="USD", quote_ccy="EUR")
        if row:
            rate = _safe_decimal(row.get("rate"))
            if rate > 0:
                return rate
    return fallback_rate if fallback_rate > 0 else Decimal("1")


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


def _cached_asset_usd_price(asset: str, rate_date: str) -> Decimal:
    if not asset or len(rate_date) < 10:
        return Decimal("0")
    candidates = [asset.upper()]
    meta = _resolve_token_display(asset)
    symbol = str(meta.get("symbol") or "").upper().strip()
    if symbol and symbol not in candidates:
        candidates.append(symbol)
    for candidate in candidates:
        row = STORE.get_fx_rate(rate_date=rate_date, base_ccy=candidate, quote_ccy="USD")
        if row:
            rate = _safe_decimal(row.get("rate"))
            if rate > 0:
                return rate
    return Decimal("0")


def _cached_asset_usd_price_on_or_before(asset: str, rate_date: str) -> Decimal:
    if not asset or len(rate_date) < 10:
        return Decimal("0")
    normalized = asset.upper()
    if normalized in {"USD", "USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD"}:
        return Decimal("1")
    candidates = [normalized]
    meta = _resolve_token_display(normalized)
    symbol = str(meta.get("symbol") or "").upper().strip()
    if symbol and symbol not in candidates:
        candidates.append(symbol)
    for candidate in candidates:
        row = STORE.get_fx_rate_on_or_before(rate_date=rate_date, base_ccy=candidate, quote_ccy="USD")
        if row:
            rate = _safe_decimal(row.get("rate"))
            if rate > 0:
                return rate
    return Decimal("0")


def _build_portfolio_value_history(events: list[dict[str, Any]], ignored_mints: set[str], runtime_fx: Decimal) -> list[dict[str, Any]]:
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
            price = _cached_asset_usd_price_on_or_before(balance_asset, day)
            if price > 0:
                value_usd += balance_qty * price
                priced_assets += 1
            else:
                unpriced_assets += 1
        fx_rate = _usd_to_eur_rate_for_date(day, runtime_fx)
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
                "priced_coverage_ratio": _decimal_to_plain(
                    Decimal(int(bucket["priced_events"])) / Decimal(int(bucket["events"])) if int(bucket["events"]) > 0 else Decimal("0")
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
            }
        )
    rows.sort(key=lambda item: (int(item["year"]), -int(item["events"]), str(item["source"])))
    return rows


def _decimal_to_plain(value: Decimal) -> str:
    # Keine wissenschaftliche Notation in der UI (z. B. 1E+9).
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"-0", ""}:
        return "0"
    return text


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


def _normalize_wallet_addresses(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item:
            continue
        if item not in normalized:
            normalized.append(item)
    return normalized


def _load_wallet_groups() -> list[dict[str, Any]]:
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
        wallets = _normalize_wallet_addresses([str(v) for v in wallets_raw])
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


def _resolve_wallets_from_group(group_id: str | None, payload_wallets: list[str]) -> list[str]:
    wallets = _normalize_wallet_addresses(payload_wallets)
    if wallets:
        return wallets
    if not group_id:
        return []
    groups = _load_wallet_groups()
    for group in groups:
        if str(group.get("group_id", "")) == group_id:
            values = group.get("wallet_addresses", [])
            if isinstance(values, list):
                return _normalize_wallet_addresses([str(v) for v in values])
    return []


def _load_wallet_snapshots() -> list[dict[str, Any]]:
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


def _append_wallet_snapshot(scope: str, entity_id: str, total_estimated_usd: str, sol_balance: str) -> None:
    if scope not in {"wallet", "group"}:
        return
    eid = str(entity_id).strip()
    if not eid:
        return
    points = _load_wallet_snapshots()
    points.append(
        {
            "scope": scope,
            "entity_id": eid,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "total_estimated_usd": str(total_estimated_usd or ""),
            "sol_balance": str(sol_balance or ""),
        }
    )
    # Ringpuffer: letzte 2000 Punkte behalten
    if len(points) > 2000:
        points = points[-2000:]
    put_admin_setting("runtime.dashboard.wallet_snapshots", points, is_secret=False)


def _filter_wallet_snapshots(scope: str, entity_id: str) -> list[dict[str, Any]]:
    points = _load_wallet_snapshots()
    scoped = [point for point in points if str(point.get("scope")) == scope]
    eid = str(entity_id).strip()
    if not eid:
        return scoped[-300:]
    return [point for point in scoped if str(point.get("entity_id", "")) == eid][-300:]


def _normalize_mint(value: str) -> str:
    return str(value or "").strip().upper()


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


def _build_issue_inbox() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    overrides = _load_issue_overrides()
    raw_events = STORE.list_raw_events()

    # 1) Missing price issues for trade-like events.
    for event in raw_events:
        event_id = str(event.get("unique_event_id", ""))
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if not _is_trade_like(payload):
            continue
        if _safe_decimal(payload.get("price_eur", payload.get("price", "0"))) > 0:
            continue
        source_name = str(payload.get("source", "")).strip().lower()
        severity = "medium" if source_name == "blockpit" else "high"
        issue_id = f"missing_price:{event_id}"
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="missing_price",
                severity=severity,
                title="Fehlender Preis für Trade-Event",
                detail=f"Event {event_id} hat Menge ohne Preis (EUR).",
                source_event_id=event_id,
                payload=payload,
                overrides=overrides,
            )
        )

    # 2) Timestamp timezone ambiguity issues.
    for event in raw_events:
        event_id = str(event.get("unique_event_id", ""))
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts_raw = payload.get("timestamp")
        if ts_raw is None:
            continue
        ts_text = str(ts_raw)
        if "Z" in ts_text or "+" in ts_text or ts_text.endswith("UTC"):
            continue
        issue_id = f"timezone_ambiguous:{event_id}"
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="timezone_conflict",
                severity="medium",
                title="Zeitzone nicht eindeutig",
                detail=f"Event {event_id} enthält timestamp ohne TZ-Offset: {ts_text}",
                source_event_id=event_id,
                payload=payload,
                overrides=overrides,
            )
        )

    # 3) Unmatched transfers.
    unmatched = list_unmatched_transfers(time_window_seconds=600, amount_tolerance_ratio=0.02, min_confidence=0.75)
    for event_id in unmatched.get("unmatched_outbound_ids", []):
        payload = STORE.get_raw_event(str(event_id))
        issue_id = f"unmatched_transfer_out:{event_id}"
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="unmatched_transfer",
                severity="high",
                title="Unmatched Outbound Transfer",
                detail=f"Outbound Transfer {event_id} hat keine Gegenbuchung.",
                source_event_id=str(event_id),
                payload=(payload or {}).get("payload", {}) if isinstance(payload, dict) else {},
                overrides=overrides,
            )
        )
    for event_id in unmatched.get("unmatched_inbound_ids", []):
        payload = STORE.get_raw_event(str(event_id))
        issue_id = f"unmatched_transfer_in:{event_id}"
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="unmatched_transfer",
                severity="high",
                title="Unmatched Inbound Transfer",
                detail=f"Inbound Transfer {event_id} hat keine Outbound-Zuordnung.",
                source_event_id=str(event_id),
                payload=(payload or {}).get("payload", {}) if isinstance(payload, dict) else {},
                overrides=overrides,
            )
        )

    # 4) Fehlende FX-Kurse für USD->EUR-Konvertierung aus Worker-Enrichment.
    for item in _load_unresolved_fx_issues():
        event_id = str(item.get("source_event_id", ""))
        rate_date = str(item.get("rate_date", ""))
        reason = str(item.get("reason", ""))
        if not event_id:
            continue
        payload_row = STORE.get_raw_event(event_id)
        payload = (payload_row or {}).get("payload", {}) if isinstance(payload_row, dict) else {}
        issue_id = f"missing_fx_rate:{event_id}:{rate_date}"
        issues.append(
            _build_issue_row(
                issue_id=issue_id,
                issue_type="missing_fx_rate",
                severity="high",
                title="Fehlender USD->EUR FX-Kurs",
                detail=f"Event {event_id} hat keinen FX-Kurs für {rate_date} ({reason}).",
                source_event_id=event_id,
                payload=payload if isinstance(payload, dict) else {},
                overrides=overrides,
            )
        )

    issues.sort(key=lambda item: (item.get("status") != "open", item.get("severity"), item.get("created_hint_utc")))
    return issues


def _build_issue_row(
    issue_id: str,
    issue_type: str,
    severity: str,
    title: str,
    detail: str,
    source_event_id: str,
    payload: dict[str, Any],
    overrides: dict[str, dict[str, str]],
) -> dict[str, Any]:
    override = overrides.get(issue_id, {})
    return {
        "issue_id": issue_id,
        "type": issue_type,
        "severity": severity,
        "status": str(override.get("status", "open")),
        "title": title,
        "detail": detail,
        "source_event_id": source_event_id,
        "asset": str(payload.get("asset", "")),
        "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
        "source": str(payload.get("source", "")),
        "note": str(override.get("note", "")),
        "updated_at_utc": str(override.get("updated_at_utc", "")),
        "created_hint_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
    }


def _is_trade_like(payload: dict[str, Any]) -> bool:
    side = str(payload.get("side", "")).lower().strip()
    event_type = str(payload.get("event_type", "")).lower().strip()
    if side in {"buy", "sell"}:
        return True
    if event_type in {"trade", "swap_out_aggregated", "swap_in_aggregated"}:
        return True
    return False


def _normalize_tax_event_category(value: str) -> str | None:
    raw = str(value or "").strip().upper()
    if raw in {"PRIVATE_SO", "PRIVATE", "SO", "INCOME_SO"}:
        return "PRIVATE_SO"
    if raw in {"BUSINESS", "GEWERBE", "ANLAGE_G", "EUER"}:
        return "BUSINESS"
    return None


def _load_tax_event_overrides() -> dict[str, dict[str, str]]:
    row = STORE.get_setting("runtime.tax_event_overrides")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for event_id_raw, payload in raw.items():
        event_id = str(event_id_raw).strip()
        if not event_id or not isinstance(payload, dict):
            continue
        category = _normalize_tax_event_category(str(payload.get("tax_category", "")))
        if category is None:
            continue
        result[event_id] = {
            "tax_category": category,
            "note": str(payload.get("note", "")),
            "updated_at_utc": str(payload.get("updated_at_utc", "")),
        }
    return result


def _load_issue_overrides() -> dict[str, dict[str, str]]:
    row = STORE.get_setting("runtime.issue_status_overrides")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for issue_id_raw, payload in raw.items():
        issue_id = str(issue_id_raw).strip()
        if not issue_id or not isinstance(payload, dict):
            continue
        status = _normalize_issue_status(str(payload.get("status", "")))
        if status is None:
            continue
        result[issue_id] = {
            "status": status,
            "note": str(payload.get("note", "")),
            "updated_at_utc": str(payload.get("updated_at_utc", "")),
        }
    return result


def _load_unresolved_fx_issues() -> list[dict[str, str]]:
    row = STORE.get_setting("runtime.fx.unresolved_events")
    if row is None:
        return []
    try:
        raw = json.loads(str(row.get("value_json", "[]")))
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    result: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        event_id = str(item.get("source_event_id", "")).strip()
        rate_date = str(item.get("rate_date", "")).strip()
        reason = str(item.get("reason", "")).strip()
        if not event_id:
            continue
        result.append(
            {
                "source_event_id": event_id,
                "rate_date": rate_date,
                "reason": reason or "unknown",
            }
        )
    return result


def _normalize_issue_status(value: str) -> str | None:
    raw = str(value or "").strip().lower()
    if raw == "won_t_fix":
        raw = "wont_fix"
    if raw in {"open", "in_review", "resolved", "wont_fix"}:
        return raw
    return None
