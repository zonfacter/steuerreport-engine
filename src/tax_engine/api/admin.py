from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tax_engine.admin import (
    get_admin_settings_view,
    put_admin_setting,
    resolve_cex_credentials,
    resolve_effective_runtime_config,
)
from tax_engine.ingestion import write_audit
from tax_engine.ingestion.store import STORE


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


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

_SOLANA_BACKFILL_SERVICE = "steuerreport-solana-backfill.service"
_SOLANA_BACKFILL_LOG = Path("/var/log/steuerreport/solana-wallet-backfill.log")
_SOLANA_BACKFILL_CURSOR_KEY = "runtime.scan.cursor.wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB"
_SOLANA_BACKFILL_STATS_KEY = "runtime.scan.stats.wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB"


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


@router.get("/settings", response_model=StandardResponse)
def admin_settings_list() -> StandardResponse:
    trace_id = str(uuid4())
    data = get_admin_settings_view()
    write_audit(
        trace_id=trace_id,
        action="admin.settings.list",
        payload={"count": len(data.get("settings", []))},
    )
    return StandardResponse(trace_id=trace_id, status="success", data=data, errors=[], warnings=[])


@router.get("/runtime-config", response_model=StandardResponse)
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


@router.post("/settings", response_model=StandardResponse)
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


@router.get("/services/solana-backfill", response_model=StandardResponse)
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


@router.post("/services/solana-backfill/action", response_model=StandardResponse)
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

    log_tail = _tail_file(_SOLANA_BACKFILL_LOG, max_lines=40)
    scan_reached_start = bool(stats.get("reached_start", False)) if isinstance(stats, dict) else False
    if not scan_reached_start:
        scan_reached_start = any("signatures=0" in line for line in log_tail)
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
        "scan_reached_start": scan_reached_start,
        "import_coverage": _build_solana_import_coverage(),
        "log_path": str(_SOLANA_BACKFILL_LOG),
        "log_tail": log_tail,
    }


def _build_solana_import_coverage() -> dict[str, Any]:
    wallet_row = STORE.get_setting("runtime.solana.default_wallet")
    wallet = ""
    if wallet_row is not None:
        try:
            loaded = json.loads(str(wallet_row.get("value_json", '""')))
            wallet = str(loaded or "").strip()
        except json.JSONDecodeError:
            wallet = str(wallet_row.get("value_json", "")).strip().strip('"')

    events = STORE.list_raw_events()
    solana_events: list[dict[str, Any]] = []
    tx_ids: set[str] = set()
    source_files: set[str] = set()
    timestamps: list[str] = []
    for event in events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source", "")).lower()
        event_wallet = str(payload.get("wallet_address", "")).strip()
        if "solana" not in source and (not wallet or event_wallet != wallet):
            continue
        solana_events.append(event)
        source_files.add(str(event.get("source_file_id", "")))
        tx_id = str(payload.get("tx_id", "")).strip()
        if tx_id:
            tx_ids.add(tx_id)
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "").strip()
        if ts:
            timestamps.append(ts)

    timestamps.sort()
    return {
        "wallet_address": wallet,
        "raw_event_count": len(solana_events),
        "distinct_tx_id_count": len(tx_ids),
        "source_file_count": len([item for item in source_files if item]),
        "first_timestamp_utc": timestamps[0] if timestamps else "",
        "last_timestamp_utc": timestamps[-1] if timestamps else "",
        "completeness_note": "Coverage zeigt nur lokal importierte Solana-Events; Vollständigkeit hängt vom Backfill-Cursor und RPC-Ergebnis ab.",
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


@router.get("/token-aliases", response_model=StandardResponse)
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


@router.post("/token-aliases/upsert", response_model=StandardResponse)
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


@router.post("/token-aliases/delete", response_model=StandardResponse)
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


@router.get("/ignored-tokens", response_model=StandardResponse)
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


@router.post("/ignored-tokens/upsert", response_model=StandardResponse)
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


@router.post("/ignored-tokens/delete", response_model=StandardResponse)
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


@router.post("/cex-credentials/load", response_model=StandardResponse)
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
