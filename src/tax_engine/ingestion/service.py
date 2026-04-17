from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from tax_engine.integrity import canonical_json, event_fingerprint

from .models import AuditEntry
from .parser import (
    convert_subunit,
    detect_fields,
    detect_number_locale,
    parse_datetime_value,
    parse_decimal_value,
)
from .store import STORE


def detect_format(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows_list = list(rows)
    numeric_fields, datetime_fields = detect_fields(rows_list)

    locale_votes: dict[str, int] = {"comma_decimal": 0, "dot_decimal": 0, "ambiguous": 0}
    for row in rows_list:
        for value in row.values():
            if value is None:
                continue
            locale = detect_number_locale(str(value))
            if locale in locale_votes:
                locale_votes[locale] += 1

    detected_locale = "dot_decimal"
    if locale_votes["comma_decimal"] > locale_votes["dot_decimal"]:
        detected_locale = "comma_decimal"

    return {
        "detected_locale": detected_locale,
        "locale_votes": locale_votes,
        "numeric_fields": numeric_fields,
        "datetime_fields": datetime_fields,
    }


def normalize_preview(
    rows: list[dict[str, Any]],
    locale_hint: str | None,
    numeric_fields: list[str] | None,
    datetime_fields: list[str] | None,
    subunit_fields: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    resolved_numeric_fields: list[str]
    resolved_datetime_fields: list[str]

    if numeric_fields is None or datetime_fields is None:
        auto_numeric, auto_datetime = detect_fields(rows)
        resolved_numeric_fields = numeric_fields if numeric_fields is not None else auto_numeric
        resolved_datetime_fields = datetime_fields if datetime_fields is not None else auto_datetime
    else:
        resolved_numeric_fields = numeric_fields
        resolved_datetime_fields = datetime_fields

    normalized_rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for idx, row in enumerate(rows):
        normalized_row: dict[str, Any] = {}
        for key, value in row.items():
            if key in resolved_numeric_fields:
                parsed, parse_error = parse_decimal_value(value, locale_hint=locale_hint)
                if parse_error:
                    warnings.append({"row": str(idx), "field": key, "code": parse_error})
                    normalized_row[key] = value
                    continue
                if parsed is None:
                    normalized_row[key] = value
                    continue

                unit = subunit_fields.get(key)
                if unit:
                    converted, conversion_error = convert_subunit(parsed, unit)
                    if conversion_error:
                        errors.append({"row": str(idx), "field": key, "code": conversion_error})
                        normalized_row[key] = value
                        continue
                    if converted is None:
                        errors.append({"row": str(idx), "field": key, "code": "conversion_result_missing"})
                        normalized_row[key] = value
                        continue
                    parsed = converted
                normalized_row[key] = parsed.to_eng_string()
                continue

            if key in resolved_datetime_fields:
                parsed_dt, dt_error = parse_datetime_value(value)
                if dt_error:
                    warnings.append({"row": str(idx), "field": key, "code": dt_error})
                    normalized_row[key] = value
                    continue
                normalized_row[key] = parsed_dt
                continue

            normalized_row[key] = value
        normalized_rows.append(normalized_row)

    return normalized_rows, warnings, errors


def confirm_import(source_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_payload = {"source_name": source_name, "rows": rows}
    source_file_id = event_fingerprint(source_payload)
    created_source = False
    if source_file_id not in STORE.source_files:
        STORE.source_files[source_file_id] = {
            "source_file_id": source_file_id,
            "source_name": source_name,
            "source_hash": source_file_id,
            "row_count": len(rows),
        }
        created_source = True

    inserted_events = 0
    duplicate_events = 0
    event_ids: list[str] = []

    for idx, row in enumerate(rows):
        unique_event_id = event_fingerprint(
            {
                "source_file_id": source_file_id,
                "row_index": idx,
                "row_payload": row,
            }
        )
        event_ids.append(unique_event_id)
        if unique_event_id in STORE.raw_events:
            duplicate_events += 1
            continue
        STORE.raw_events[unique_event_id] = {
            "unique_event_id": unique_event_id,
            "source_file_id": source_file_id,
            "row_index": idx,
            "payload": canonical_json(row),
        }
        inserted_events += 1

    return {
        "source_file_id": source_file_id,
        "source_created": created_source,
        "inserted_events": inserted_events,
        "duplicate_events": duplicate_events,
        "event_ids": event_ids,
    }


def write_audit(trace_id: str, action: str, payload: dict[str, Any]) -> None:
    STORE.write_audit(AuditEntry.create(trace_id=trace_id, action=action, payload=payload))
