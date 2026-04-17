from __future__ import annotations

from decimal import Decimal
import json
from typing import Any

from tax_engine.ingestion.models import (
    ErrorDetail,
    NormalizePreviewData,
    NormalizePreviewRequest,
    NormalizedRow,
    WarningDetail,
)
from tax_engine.ingestion.parser import parse_datetime_with_fallback, parse_decimal


NUMERIC_LIKE_PATTERN = r"^[\s\+\-\(]?[\d\.,\s\u00A0]+(?:e[\+\-]?\d+)?\)?\s*$"


def _is_numeric_like(value: Any) -> bool:
    if isinstance(value, (int, float, Decimal)):
        return True
    if not isinstance(value, str):
        return False
    import re

    return bool(re.match(NUMERIC_LIKE_PATTERN, value, re.IGNORECASE))


def _decimal_to_str(value: Decimal) -> str:
    return format(value.normalize(), "f")


def normalize_preview(
    request: NormalizePreviewRequest,
) -> tuple[NormalizePreviewData, list[ErrorDetail], list[WarningDetail]]:
    normalized_rows: list[NormalizedRow] = []
    errors: list[ErrorDetail] = []
    warnings: list[WarningDetail] = []

    for row_index, row in enumerate(request.rows):
        normalized_values: dict[str, Any] = {}
        unresolved_fields: list[str] = []
        row_asset = str(row.get(request.asset_field, "")).strip()

        for field, value in row.items():
            if field in request.datetime_fields:
                parsed_datetime, error = parse_datetime_with_fallback(value, profile=request.profile)
                if error is not None:
                    error.field = field
                    errors.append(error)
                    unresolved_fields.append(field)
                    normalized_values[field] = value
                else:
                    normalized_values[field] = parsed_datetime
                continue

            should_parse_numeric = field in request.numeric_fields or _is_numeric_like(value)
            if should_parse_numeric:
                parsed_decimal, error, warning = parse_decimal(
                    value,
                    decimal_separator=request.profile.decimal_separator,
                    thousand_separator=request.profile.thousand_separator,
                )
                if error is not None:
                    error.field = field
                    errors.append(error)
                    unresolved_fields.append(field)
                    normalized_values[field] = value
                    continue
                if warning is not None:
                    warning.field = field
                    warnings.append(warning)
                    unresolved_fields.append(field)
                    normalized_values[field] = value
                    continue
                if parsed_decimal is None:
                    normalized_values[field] = value
                    continue

                factor_key = request.profile.subunit_field_map.get(field)
                if factor_key is not None:
                    factor = request.profile.subunit_factors.get(factor_key)
                    if factor is None:
                        errors.append(
                            ErrorDetail(
                                code="conversion_factor_missing",
                                message=f"Missing conversion factor for key '{factor_key}'.",
                                field=field,
                            )
                        )
                        unresolved_fields.append(field)
                        normalized_values[field] = value
                        continue
                    parsed_decimal = parsed_decimal * factor
                elif row_asset and row_asset in request.profile.subunit_factors:
                    parsed_decimal = parsed_decimal * request.profile.subunit_factors[row_asset]

                normalized_values[field] = _decimal_to_str(parsed_decimal)
                continue

            normalized_values[field] = value

        normalized_rows.append(
            NormalizedRow(
                index=row_index,
                values=json.loads(json.dumps(normalized_values, default=str)),
                unresolved_fields=sorted(set(unresolved_fields)),
            )
        )

    return NormalizePreviewData(row_count=len(request.rows), normalized_rows=normalized_rows), errors, warnings
