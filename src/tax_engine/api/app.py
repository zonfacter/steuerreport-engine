from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tax_engine.api.admin import (
    AdminServiceActionRequest,
    AdminSettingsPutRequest,
    CexCredentialsLoadRequest,
    IgnoredTokenDeleteRequest,
    IgnoredTokenUpsertRequest,
    TokenAliasDeleteRequest,
    TokenAliasUpsertRequest,
    _build_solana_backfill_status,
    _run_systemctl,
    _tail_file,
    admin_cex_credentials_load,
    admin_ignored_tokens_delete,
    admin_ignored_tokens_list,
    admin_ignored_tokens_upsert,
    admin_runtime_config,
    admin_settings_list,
    admin_settings_put,
    admin_solana_backfill_action,
    admin_solana_backfill_status,
    admin_token_aliases_delete,
    admin_token_aliases_list,
    admin_token_aliases_upsert,
)
from tax_engine.api.admin import (
    router as admin_router,
)
from tax_engine.api.connectors import (
    CexFullHistoryImportRequest,
    connectors_cex_balances_preview,
    connectors_cex_import_confirm,
    connectors_cex_import_full_history,
    connectors_cex_transactions_preview,
    connectors_cex_verify,
    connectors_solana_balance_snapshot,
    connectors_solana_group_balance_snapshot,
    connectors_solana_group_import_confirm,
    connectors_solana_import_confirm,
    connectors_solana_import_full_history,
    connectors_solana_rpc_probe,
    connectors_solana_wallet_preview,
)
from tax_engine.api.connectors import (
    router as connectors_router,
)
from tax_engine.api.dashboard import (
    DashboardRoleOverrideRequest,
    _accumulate_deduped_bucket_value,
    _accumulate_yearly_deduped_value,
    _accumulate_yearly_event_breakdown,
    _accumulate_yearly_source_breakdown,
    _build_portfolio_value_history,
    _cached_asset_usd_price,
    _cached_asset_usd_price_on_or_before,
    _dashboard_economic_tx_key,
    _dashboard_event_category,
    _dashboard_event_quantity,
    _decimal_to_plain,
    _decorate_token_rows,
    _deduped_bucket_totals,
    _estimate_event_values,
    _event_quote_asset,
    _extract_year,
    _first_positive_decimal,
    _format_yearly_asset_activity,
    _format_yearly_event_breakdown,
    _format_yearly_source_breakdown,
    _heliumgeek_display_quantity,
    _is_dashboard_value_event,
    _is_ignored_token,
    _is_spam_candidate,
    _is_trading_volume_event,
    _load_dashboard_role_override,
    _load_ignored_tokens,
    _load_token_aliases,
    _normalize_mint,
    _parse_iso_timestamp,
    _resolve_token_display,
    _runtime_usd_to_eur_rate,
    _safe_decimal,
    _usd_to_eur_rate_for_date,
    dashboard_overview,
    dashboard_role_override,
    dashboard_wallet_snapshots,
    portfolio_helium_legacy_transfers,
    portfolio_integrations,
    portfolio_lot_aging,
)
from tax_engine.api.dashboard import (
    router as dashboard_router,
)
from tax_engine.api.imports import (
    BulkFolderImportRequest,
    import_bulk_folder,
    import_confirm,
    import_connectors,
    import_detect_format,
    import_jobs,
    import_normalize_preview,
    import_parse_preview,
    import_sources_summary,
    import_upload_preview,
)
from tax_engine.api.imports import (
    build_import_job_rows as _build_import_job_rows,
)
from tax_engine.api.imports import (
    detect_connector_from_filename as _detect_connector_from_filename,
)
from tax_engine.api.imports import (
    detect_connector_from_source_name as _detect_connector_from_source_name,
)
from tax_engine.api.imports import (
    router as imports_router,
)
from tax_engine.api.processing import (
    ProcessCompareRulesetsRequest,
    ProcessPreflightRequest,
    ReportSnapshotCreateRequest,
    audit_tax_line,
    compliance_classification,
    create_snapshot,
    get_snapshot,
    integrity_event,
    integrity_report,
    process_compare_rulesets,
    process_compare_rulesets_post,
    process_derivative_lines,
    process_jobs,
    process_latest,
    process_options,
    process_preflight,
    process_run,
    process_status,
    process_tax_domain_summary,
    process_tax_lines,
    process_worker_run_next,
    report_export,
    report_files,
)
from tax_engine.api.processing import (
    router as processing_router,
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
from tax_engine.api.review import (
    IssueStatusUpdateRequest,
    TaxEventOverrideDeleteRequest,
    TaxEventOverrideUpsertRequest,
    _build_issue_inbox,
    _load_issue_overrides,
    _load_tax_event_overrides,
    _load_unresolved_fx_issues,
    issues_inbox,
    issues_update_status,
    reconcile_auto_match,
    reconcile_ledger,
    reconcile_manual,
    review_gates,
    review_unmatched,
    tax_event_override_delete,
    tax_event_override_upsert,
    tax_event_overrides_list,
)
from tax_engine.api.review import (
    router as review_router,
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
from tax_engine.api.wallet_groups import (
    append_wallet_snapshot as _append_wallet_snapshot,
)
from tax_engine.api.wallet_groups import (
    load_wallet_snapshots as _load_wallet_snapshots,
)
from tax_engine.api.wallet_groups import (
    normalize_wallet_addresses as _normalize_wallet_addresses,
)
from tax_engine.api.wallet_groups import (
    resolve_wallets_from_group as _resolve_wallets_from_group,
)
from tax_engine.api.wallet_groups import (
    router as wallet_groups_router,
)
from tax_engine.api.wallet_groups import (
    wallet_groups_delete,
    wallet_groups_list,
    wallet_groups_upsert,
)

__all__ = [
    "AdminServiceActionRequest",
    "AdminSettingsPutRequest",
    "BulkFolderImportRequest",
    "CexFullHistoryImportRequest",
    "CexCredentialsLoadRequest",
    "DashboardRoleOverrideRequest",
    "IgnoredTokenDeleteRequest",
    "IgnoredTokenUpsertRequest",
    "IssueStatusUpdateRequest",
    "ProcessCompareRulesetsRequest",
    "ProcessPreflightRequest",
    "ReportSnapshotCreateRequest",
    "RulesetUpsertRequest",
    "TaxEventOverrideDeleteRequest",
    "TaxEventOverrideUpsertRequest",
    "TokenAliasDeleteRequest",
    "TokenAliasUpsertRequest",
    "_accumulate_deduped_bucket_value",
    "_accumulate_yearly_deduped_value",
    "_accumulate_yearly_event_breakdown",
    "_accumulate_yearly_source_breakdown",
    "_build_solana_backfill_status",
    "_append_wallet_snapshot",
    "_build_csv_from_rows",
    "_build_export_rows",
    "_build_import_job_rows",
    "_build_issue_inbox",
    "_build_portfolio_value_history",
    "_build_pdf_from_rows",
    "_build_report_file_index",
    "_cached_asset_usd_price",
    "_cached_asset_usd_price_on_or_before",
    "_dashboard_economic_tx_key",
    "_dashboard_event_category",
    "_dashboard_event_quantity",
    "_detect_connector_from_filename",
    "_detect_connector_from_source_name",
    "_decimal_to_plain",
    "_decorate_token_rows",
    "_deduped_bucket_totals",
    "_estimate_event_values",
    "_event_quote_asset",
    "_extract_year",
    "_first_positive_decimal",
    "_format_ruleset_row",
    "_format_yearly_asset_activity",
    "_format_yearly_event_breakdown",
    "_format_yearly_source_breakdown",
    "_heliumgeek_display_quantity",
    "_is_dashboard_value_event",
    "_is_ignored_token",
    "_is_spam_candidate",
    "_is_trading_volume_event",
    "_load_dashboard_role_override",
    "_load_ignored_tokens",
    "_load_token_aliases",
    "_load_wallet_snapshots",
    "_load_issue_overrides",
    "_load_tax_event_overrides",
    "_load_unresolved_fx_issues",
    "_normalize_mint",
    "_normalize_wallet_addresses",
    "_parse_iso_timestamp",
    "_resolve_wallets_from_group",
    "_resolve_token_display",
    "_runtime_usd_to_eur_rate",
    "_safe_decimal",
    "_run_systemctl",
    "_tail_file",
    "_to_iso_date",
    "_usd_to_eur_rate_for_date",
    "admin_cex_credentials_load",
    "admin_ignored_tokens_delete",
    "admin_ignored_tokens_list",
    "admin_ignored_tokens_upsert",
    "admin_runtime_config",
    "admin_settings_list",
    "admin_settings_put",
    "admin_solana_backfill_action",
    "admin_solana_backfill_status",
    "admin_token_aliases_delete",
    "admin_token_aliases_list",
    "admin_token_aliases_upsert",
    "audit_tax_line",
    "compliance_classification",
    "connectors_cex_balances_preview",
    "connectors_cex_import_confirm",
    "connectors_cex_import_full_history",
    "connectors_cex_transactions_preview",
    "connectors_cex_verify",
    "connectors_solana_balance_snapshot",
    "connectors_solana_group_balance_snapshot",
    "connectors_solana_group_import_confirm",
    "connectors_solana_import_confirm",
    "connectors_solana_import_full_history",
    "connectors_solana_rpc_probe",
    "connectors_solana_wallet_preview",
    "create_snapshot",
    "dashboard_overview",
    "dashboard_role_override",
    "dashboard_wallet_snapshots",
    "get_snapshot",
    "import_bulk_folder",
    "import_confirm",
    "import_connectors",
    "import_detect_format",
    "import_jobs",
    "import_normalize_preview",
    "import_parse_preview",
    "import_sources_summary",
    "import_upload_preview",
    "integrity_event",
    "integrity_report",
    "issues_inbox",
    "issues_update_status",
    "portfolio_integrations",
    "portfolio_helium_legacy_transfers",
    "portfolio_lot_aging",
    "process_compare_rulesets",
    "process_compare_rulesets_post",
    "process_derivative_lines",
    "process_jobs",
    "process_latest",
    "process_options",
    "process_preflight",
    "process_run",
    "process_status",
    "process_tax_domain_summary",
    "process_tax_lines",
    "process_worker_run_next",
    "reconcile_auto_match",
    "reconcile_ledger",
    "reconcile_manual",
    "report_export",
    "report_files",
    "review_gates",
    "review_unmatched",
    "ruleset_get",
    "ruleset_list",
    "ruleset_upsert",
    "wallet_groups_delete",
    "wallet_groups_list",
    "wallet_groups_upsert",
    "tax_event_override_delete",
    "tax_event_override_upsert",
    "tax_event_overrides_list",
]


class StandardResponse(BaseModel):
    trace_id: str = Field(description="Request trace identifier")
    status: str = Field(description="Response status")
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)


app = FastAPI(
    title="Steuerreport Engine API",
    version="0.1.0",
    description="Modulare, auditierbare Steuer-Engine API",
)
app.include_router(admin_router)
app.include_router(connectors_router)
app.include_router(dashboard_router)
app.include_router(imports_router)
app.include_router(processing_router)
app.include_router(review_router)
app.include_router(rulesets_router)
app.include_router(wallet_groups_router)


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
