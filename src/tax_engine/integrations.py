from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from tax_engine.ingestion.store import STORE

INTEGRATION_MODES = {"active", "reference", "disabled"}
REFERENCE_DEFAULT_SOURCES = {"blockpit", "cointracking", "koinly"}


def normalize_integration_id(value: Any) -> str:
    return str(value or "").strip().lower()


def integration_source_from_event(event: dict[str, Any]) -> str:
    payload = event.get("payload", {})
    if not isinstance(payload, dict):
        return "unknown"
    return normalize_integration_id(payload.get("source") or payload.get("source_name") or "unknown") or "unknown"


def infer_default_integration_mode(integration_id: str) -> str:
    source = normalize_integration_id(integration_id)
    if source in REFERENCE_DEFAULT_SOURCES:
        return "reference"
    return "active"


def load_integration_mode_overrides() -> dict[str, dict[str, str]]:
    row = STORE.get_setting("runtime.integration_modes")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for source_raw, payload in raw.items():
        source = normalize_integration_id(source_raw)
        if not source or not isinstance(payload, dict):
            continue
        mode = normalize_integration_mode(str(payload.get("mode", "")))
        if mode is None:
            continue
        result[source] = {
            "mode": mode,
            "note": str(payload.get("note", "")).strip(),
            "updated_at_utc": str(payload.get("updated_at_utc", "")).strip(),
        }
    return result


def normalize_integration_mode(value: str) -> str | None:
    mode = str(value or "").strip().lower()
    if mode in {"primary", "enabled"}:
        mode = "active"
    if mode in {"ref"}:
        mode = "reference"
    if mode in {"off", "ignore", "ignored"}:
        mode = "disabled"
    return mode if mode in INTEGRATION_MODES else None


def effective_integration_mode(integration_id: str, overrides: dict[str, dict[str, str]] | None = None) -> str:
    source = normalize_integration_id(integration_id)
    effective_overrides = load_integration_mode_overrides() if overrides is None else overrides
    override = effective_overrides.get(source)
    if override is not None:
        mode = normalize_integration_mode(override.get("mode", ""))
        if mode is not None:
            return mode
    return infer_default_integration_mode(source)


def upsert_integration_mode(integration_id: str, mode: str, note: str = "") -> dict[str, str]:
    source = normalize_integration_id(integration_id)
    normalized_mode = normalize_integration_mode(mode)
    if not source:
        raise ValueError("integration_id_missing")
    if normalized_mode is None:
        raise ValueError("invalid_integration_mode")
    overrides = load_integration_mode_overrides()
    entry = {
        "mode": normalized_mode,
        "note": str(note or "").strip(),
        "updated_at_utc": datetime.now(UTC).isoformat(),
    }
    overrides[source] = entry
    STORE.upsert_setting("runtime.integration_modes", json.dumps(overrides, sort_keys=True, separators=(",", ":")), False)
    return {"integration_id": source, **entry}


def active_sources_from_integrations(integration_rows: list[dict[str, Any]]) -> list[str]:
    overrides = load_integration_mode_overrides()
    sources = [
        normalize_integration_id(row.get("integration_id"))
        for row in integration_rows
        if effective_integration_mode(str(row.get("integration_id") or ""), overrides) == "active"
    ]
    return sorted({source for source in sources if source})


def filter_events_for_processing(raw_events: list[dict[str, Any]], config: dict[str, Any] | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cfg = config if isinstance(config, dict) else {}
    overrides = load_integration_mode_overrides()
    explicit_filters_raw = cfg.get("source_filters") or cfg.get("active_source_filters") or []
    explicit_filters = {
        normalize_integration_id(item)
        for item in explicit_filters_raw
        if normalize_integration_id(item)
    } if isinstance(explicit_filters_raw, list) else set()
    include_reference = bool(cfg.get("include_reference_sources", False))
    include_disabled = bool(cfg.get("include_disabled_sources", False))

    filtered: list[dict[str, Any]] = []
    excluded_by_mode = 0
    excluded_by_filter = 0
    included_sources: set[str] = set()
    excluded_sources: set[str] = set()

    for event in raw_events:
        source = integration_source_from_event(event)
        mode = effective_integration_mode(source, overrides)
        if explicit_filters and source not in explicit_filters:
            excluded_by_filter += 1
            excluded_sources.add(source)
            continue
        if mode == "disabled" and not include_disabled:
            excluded_by_mode += 1
            excluded_sources.add(source)
            continue
        if mode == "reference" and not include_reference and not explicit_filters:
            excluded_by_mode += 1
            excluded_sources.add(source)
            continue
        filtered.append(event)
        included_sources.add(source)

    return filtered, {
        "input_event_count": len(raw_events),
        "output_event_count": len(filtered),
        "excluded_by_mode": excluded_by_mode,
        "excluded_by_filter": excluded_by_filter,
        "included_sources": sorted(included_sources),
        "excluded_sources": sorted(excluded_sources),
        "explicit_source_filters": sorted(explicit_filters),
        "include_reference_sources": include_reference,
        "include_disabled_sources": include_disabled,
    }
