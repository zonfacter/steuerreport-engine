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


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_timestamp(value: Any) -> str:
    raw = _clean_text(value)
    if not raw:
        return ""
    parsed, _ = parse_datetime_value(raw)
    return parsed or raw


def _normalize_decimal(value: Any) -> str:
    raw = _clean_text(value)
    if not raw:
        return ""
    parsed, parse_error = parse_decimal_value(raw)
    if parse_error or parsed is None:
        return raw
    return parsed.to_eng_string()


def _extract_first(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return value
    return None


def _build_event_identity(row: dict[str, Any]) -> dict[str, str]:
    # Deutsche Kommentare: Identity-Keys müssen dateiübergreifend stabil sein, damit Duplikate
    # aus überlappenden CSV/API-Imports nicht erneut persistiert werden.
    raw_row = row.get("raw_row")
    raw_map = raw_row if isinstance(raw_row, dict) else {}

    merged: dict[str, Any] = {}
    merged.update(raw_map)
    merged.update(row)

    connector_event_id = _extract_first(
        merged,
        (
            "tx_id",
            "transaction_id",
            "transactionId",
            "tranId",
            "id",
            "order_id",
            "orderId",
            "trade_id",
            "tradeId",
            "signature",
            "hash",
        ),
    )

    identity = {
        "identity_version": "v2",
        "source": _clean_text(_extract_first(merged, ("source", "connector_id", "exchange", "platform"))).lower(),
        "event_id": _clean_text(connector_event_id),
        "timestamp_utc": _normalize_timestamp(_extract_first(merged, ("timestamp_utc", "timestamp", "time", "date"))),
        "event_type": _clean_text(_extract_first(merged, ("event_type", "type", "operation"))).lower(),
        "side": _clean_text(_extract_first(merged, ("side", "direction"))).lower(),
        "asset": _clean_text(_extract_first(merged, ("asset", "coin", "currency", "symbol"))).upper(),
        "quantity": _normalize_decimal(_extract_first(merged, ("quantity", "amount", "qty", "size"))),
        "price": _normalize_decimal(_extract_first(merged, ("price", "rate", "execution_price"))),
        "fee": _normalize_decimal(_extract_first(merged, ("fee", "commission", "transaction_fee"))),
        "fee_asset": _clean_text(_extract_first(merged, ("fee_asset", "fee coin", "commissionAsset", "fee_currency"))).upper(),
        "wallet_address": _clean_text(_extract_first(merged, ("wallet_address", "address", "from_address", "to_address"))),
        "network": _clean_text(_extract_first(merged, ("network", "chain", "blockchain"))).lower(),
    }
    return identity


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
    created_source = STORE.upsert_source_file(
        source_file_id=source_file_id,
        source_name=source_name,
        source_hash=source_file_id,
        row_count=len(rows),
    )

    inserted_events = 0
    duplicate_events = 0
    event_ids: list[str] = []

    for idx, row in enumerate(rows):
        unique_event_id = event_fingerprint(_build_event_identity(row))
        event_ids.append(unique_event_id)
        inserted = STORE.insert_raw_event(
            unique_event_id=unique_event_id,
            source_file_id=source_file_id,
            row_index=idx,
            payload_json=canonical_json(row),
        )
        if inserted:
            inserted_events += 1
        else:
            duplicate_events += 1

    return {
        "source_file_id": source_file_id,
        "source_created": created_source,
        "inserted_events": inserted_events,
        "duplicate_events": duplicate_events,
        "event_ids": event_ids,
    }


def write_audit(trace_id: str, action: str, payload: dict[str, Any]) -> None:
    entry = AuditEntry.create(trace_id=trace_id, action=action, payload=payload)
    STORE.write_audit(
        trace_id=entry.trace_id,
        action=entry.action,
        event_time_utc=entry.event_time_utc,
        payload_json=canonical_json(entry.payload),
    )
