from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from tax_engine.admin.service import resolve_effective_runtime_config
from tax_engine.core.derivatives import process_derivatives_for_year
from tax_engine.core.processor import process_events_for_year
from tax_engine.core.tax_domains import build_tax_domain_summary
from tax_engine.fx import FallbackFxResolver
from tax_engine.ingestion.store import STORE
from tax_engine.integrations import filter_events_for_processing
from tax_engine.integrity import (
    config_fingerprint,
    data_fingerprint,
    report_integrity_id,
    ruleset_fingerprint,
)
from tax_engine.rulesets import build_default_registry

from .models import ProcessRunRequest


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
        category = str(payload.get("tax_category", "")).strip().upper()
        if category not in {"PRIVATE_SO", "BUSINESS", "EXCLUDED"}:
            continue
        result[event_id] = {
            "tax_category": category,
            "reason_code": str(payload.get("reason_code", "")).strip(),
            "reason_label": str(payload.get("reason_label", "")).strip(),
            "note": str(payload.get("note", "")).strip(),
            "updated_at_utc": str(payload.get("updated_at_utc", "")).strip(),
        }
    return result


def _load_review_actions() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting("runtime.review_actions")
    empty: dict[str, dict[str, Any]] = {"timezone_corrections": {}, "merges": {}, "splits": {}}
    if row is None:
        return empty
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return empty
    if not isinstance(raw, dict):
        return empty
    result: dict[str, dict[str, Any]] = {"timezone_corrections": {}, "merges": {}, "splits": {}}
    for section in result:
        value = raw.get(section, {})
        if isinstance(value, dict):
            result[section] = value
    return result


def apply_review_actions(raw_events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    actions = _load_review_actions()
    timezone_corrections = actions.get("timezone_corrections", {})
    if not timezone_corrections:
        return raw_events, {"timezone_correction_count": 0}

    transformed: list[dict[str, Any]] = []
    applied_timezone = 0
    for event in raw_events:
        event_id = str(event.get("unique_event_id", "")).strip()
        correction = timezone_corrections.get(event_id)
        if not isinstance(correction, dict):
            transformed.append(event)
            continue
        corrected_timestamp = str(correction.get("corrected_timestamp_utc", "")).strip()
        if not corrected_timestamp:
            transformed.append(event)
            continue
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        payload_copy = dict(payload)
        payload_copy["original_timestamp_utc"] = payload_copy.get("timestamp_utc", "")
        payload_copy["timestamp_utc"] = corrected_timestamp
        payload_copy["review_action"] = "timezone_correct"
        payload_copy["review_action_note"] = str(correction.get("note", "")).strip()
        payload_copy["review_action_updated_at_utc"] = str(correction.get("updated_at_utc", "")).strip()
        event_copy = dict(event)
        event_copy["payload"] = payload_copy
        transformed.append(event_copy)
        applied_timezone += 1

    return transformed, {"timezone_correction_count": applied_timezone}


def apply_tax_event_overrides(raw_events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    overrides = _load_tax_event_overrides()
    if not overrides:
        return raw_events, 0
    transformed: list[dict[str, Any]] = []
    applied = 0
    for event in raw_events:
        event_id = str(event.get("unique_event_id", "")).strip()
        override = overrides.get(event_id)
        if override is None:
            transformed.append(event)
            continue
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        payload_copy = dict(payload)
        category = override["tax_category"]
        if category == "EXCLUDED":
            applied += 1
            continue
        payload_copy["tax_category"] = "BUSINESS" if category == "BUSINESS" else "INCOME_SO"
        payload_copy["tax_override_note"] = override.get("note", "")
        payload_copy["tax_override_updated_at_utc"] = override.get("updated_at_utc") or datetime.now(UTC).isoformat()
        event_copy = dict(event)
        event_copy["payload"] = payload_copy
        transformed.append(event_copy)
        applied += 1
    return transformed, applied


def create_processing_job(payload: ProcessRunRequest) -> dict[str, Any]:
    registry = build_default_registry()
    ruleset, _warnings = registry.resolve_for_year(
        tax_year=payload.tax_year,
        ruleset_id=payload.ruleset_id,
        ruleset_version=payload.ruleset_version,
    )
    job_id = str(uuid4())
    cfg_hash = config_fingerprint(
        {
            "tax_year": payload.tax_year,
            "ruleset_id": ruleset.ruleset_id,
            "ruleset_version": ruleset.ruleset_version,
            "dry_run": payload.dry_run,
            "config": payload.config,
        }
    )
    STORE.create_processing_job(
        job_id=job_id,
        tax_year=payload.tax_year,
        ruleset_id=ruleset.ruleset_id,
        ruleset_version=ruleset.ruleset_version,
        config_hash=cfg_hash,
        config_json=json.dumps(payload.config, sort_keys=True, separators=(",", ":")),
        status="queued",
        progress=0,
    )
    job = STORE.get_processing_job(job_id)
    if job is None:
        raise RuntimeError("Job creation failed unexpectedly")
    return job


def get_processing_job(job_id: str) -> dict[str, Any] | None:
    return STORE.get_processing_job(job_id)


def run_next_queued_job(simulate_fail: bool = False) -> dict[str, Any] | None:
    claimed = STORE.claim_next_queued_job()
    if claimed is None:
        return None

    job_id = claimed["job_id"]
    try:
        STORE.update_processing_job_state(
            job_id=job_id,
            status="running",
            progress=35,
            current_step="load_events",
        )
        job_config = claimed.get("config", {}) if isinstance(claimed.get("config"), dict) else {}
        raw_events, integration_filter_summary = filter_events_for_processing(STORE.list_raw_events(), job_config)
        adjusted_events, review_action_summary = apply_review_actions(raw_events)
        effective_events, override_count = apply_tax_event_overrides(adjusted_events)
        fx_config = resolve_effective_runtime_config()
        runtime_fx = fx_config.get("runtime", {}).get("fx", {})
        fallback_rate = runtime_fx.get("usd_to_eur", 1.0)
        fx_resolver = FallbackFxResolver(fallback_rate=fallback_rate)
        effective_events, fx_summary = fx_resolver.enrich_events_with_fx(effective_events)
        STORE.upsert_setting(
            setting_key="runtime.fx.unresolved_events",
            value_json=json.dumps(fx_summary.get("unresolved_events", []), separators=(",", ":")),
            is_secret=False,
        )

        STORE.update_processing_job_state(
            job_id=job_id,
            status="running",
            progress=70,
            current_step="core_processing",
        )
        ruleset_id = str(claimed["ruleset_id"])
        ruleset_version = claimed.get("ruleset_version")
        if ruleset_version is not None and not str(ruleset_version).strip():
            ruleset_version = None

        processing_result = process_events_for_year(
            raw_events=effective_events,
            tax_year=claimed["tax_year"],
            ruleset_id=ruleset_id,
            ruleset_version=ruleset_version,
        )
        processing_result["integration_filter_summary"] = integration_filter_summary
        tax_lines = processing_result.pop("tax_lines")
        tax_lines = _attach_transfer_trace(tax_lines)
        derivative_result = process_derivatives_for_year(raw_events=effective_events, tax_year=claimed["tax_year"])
        derivative_lines = derivative_result.pop("lines")
        tax_domain_summary = build_tax_domain_summary(
            raw_events=effective_events,
            tax_lines=tax_lines,
            derivative_lines=derivative_lines,
            tax_year=claimed["tax_year"],
            ruleset_id=ruleset_id,
        )

        registry = build_default_registry()
        ruleset = registry.get(ruleset_id, ruleset_version)
        ruleset_hash = ruleset_fingerprint(ruleset)

        event_ids = [event.get("unique_event_id", "") for event in effective_events]
        data_hash = data_fingerprint([str(value) for value in event_ids])
        integrity_id = report_integrity_id(
            event_hashes=[str(event_id) for event_id in event_ids],
            ruleset_hash=ruleset_hash,
            config_hash=claimed["config_hash"],
        )
        STORE.insert_report_integrity(
            job_id=job_id,
            data_hash=data_hash,
            ruleset_id=ruleset_id,
            ruleset_version=ruleset.ruleset_version,
            ruleset_hash=ruleset_hash,
            config_hash=claimed["config_hash"],
            report_integrity_id=integrity_id,
            event_count=len(event_ids),
            run_started_at_utc=claimed["created_at_utc"],
        )

        if simulate_fail:
            raise RuntimeError("Simulated worker error")

        STORE.replace_tax_lines(job_id=job_id, tax_lines=tax_lines)
        STORE.replace_derivative_lines(job_id=job_id, derivative_lines=derivative_lines)
        processing_result["derivatives"] = derivative_result
        processing_result["tax_domain_summary"] = tax_domain_summary
        processing_result["tax_event_override_count"] = override_count
        processing_result["review_actions"] = review_action_summary
        processing_result["fx_enrichment"] = fx_summary
        processing_result["ruleset_id"] = ruleset_id
        processing_result["ruleset_version"] = ruleset.ruleset_version
        processing_result["report_integrity_id"] = integrity_id

        STORE.update_processing_job_state(
            job_id=job_id,
            status="completed",
            progress=100,
            current_step="completed",
            error_message=None,
            result_json=json.dumps(processing_result, sort_keys=True, separators=(",", ":")),
        )
    except Exception as exc:
        STORE.update_processing_job_state(
            job_id=job_id,
            status="failed",
            progress=70,
            current_step="failed",
            error_message=str(exc),
            result_json=None,
        )

    return STORE.get_processing_job(job_id)


def _attach_transfer_trace(tax_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transfer_chain_by_event_id: dict[str, str] = {}
    for match in STORE.list_transfer_matches():
        chain_id = str(match.get("match_id", ""))
        if not chain_id:
            continue
        transfer_chain_by_event_id[str(match.get("outbound_event_id", ""))] = chain_id
        transfer_chain_by_event_id[str(match.get("inbound_event_id", ""))] = chain_id

    enriched: list[dict[str, Any]] = []
    for line in tax_lines:
        row = dict(line)
        lot_source_event_id = str(row.get("lot_source_event_id", "")).strip()
        sell_source_event_id = str(row.get("source_event_id", "")).strip()
        row["transfer_chain_id"] = (
            transfer_chain_by_event_id.get(lot_source_event_id)
            or transfer_chain_by_event_id.get(sell_source_event_id)
            or str(row.get("transfer_chain_id", "")).strip()
        )
        enriched.append(row)
    return enriched
