from __future__ import annotations

import json
from collections import deque
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tax_engine.api.wallet_groups import (
    append_wallet_snapshot as _append_wallet_snapshot,
)
from tax_engine.api.wallet_groups import (
    decimal_to_plain as _decimal_to_plain,
)
from tax_engine.api.wallet_groups import (
    resolve_wallets_from_group as _resolve_wallets_from_group,
)
from tax_engine.connectors import (
    CexBalancesPreviewRequest,
    CexImportConfirmRequest,
    CexTransactionsPreviewRequest,
    CexVerifyRequest,
    SolanaBalanceSnapshotRequest,
    SolanaFullHistoryImportRequest,
    SolanaGroupBalanceSnapshotRequest,
    SolanaGroupImportConfirmRequest,
    SolanaImportConfirmRequest,
    SolanaRpcProbeRequest,
    SolanaWalletPreviewRequest,
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
from tax_engine.ingestion import confirm_import, write_audit
from tax_engine.ingestion.store import STORE


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


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


router = APIRouter(prefix="/api/v1/connectors", tags=["connectors"])


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


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
        item["spam_candidate"] = (
            "true" if _is_spam_candidate(asset=asset, qty=qty, known=bool(meta["is_known"])) else "false"
        )
        item["quantity"] = _decimal_to_plain(qty)
        decorated.append(item)
    return decorated


@router.post("/cex/verify", response_model=StandardResponse, tags=["connectors"])
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


@router.post(
    "/cex/balances-preview",
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


@router.post(
    "/cex/transactions-preview",
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


@router.post("/cex/import-confirm", response_model=StandardResponse, tags=["connectors"])
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


@router.post("/cex/import-full-history", response_model=StandardResponse, tags=["connectors"])
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


@router.post(
    "/solana/rpc-probe",
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


@router.post(
    "/solana/balance-snapshot",
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


@router.post(
    "/solana/group-balance-snapshot",
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


@router.post(
    "/solana/wallet-preview",
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


@router.post(
    "/solana/import-confirm",
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


@router.post(
    "/solana/import-full-history",
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


@router.post(
    "/solana/group-import-confirm",
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

