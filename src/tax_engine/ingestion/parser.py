from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from dateutil import parser as date_parser

from tax_engine.ingestion.models import ColumnFormatDetection, ErrorDetail, ImportProfile, WarningDetail


NUMBER_PATTERN = re.compile(r"^[\s\+\-\(]?[\d\.,\s\u00A0]+(?:e[\+\-]?\d+)?\)?\s*$", re.IGNORECASE)
ISO_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?(?:Z|[\+\-]\d{2}:?\d{2})?$")


class CsvAdapter:
    source_name: str = "generic"
    required_columns: set[str] = set()
    dedupe_fields: tuple[str, ...] = tuple()

    def can_handle(self, headers: set[str]) -> bool:
        return self.required_columns.issubset(headers)


class BinanceCsvAdapter(CsvAdapter):
    source_name = "binance"
    required_columns = {"Date(UTC)", "Pair", "Side", "Price", "Executed"}
    dedupe_fields = ("Date(UTC)", "Pair", "Side", "Price", "Executed", "Fee", "OrderId")


class BitgetCsvAdapter(CsvAdapter):
    source_name = "bitget"
    required_columns = {"time", "symbol", "side", "price", "size"}
    dedupe_fields = ("time", "symbol", "side", "price", "size", "fee", "orderId")


ADAPTERS: tuple[CsvAdapter, ...] = (BinanceCsvAdapter(), BitgetCsvAdapter())


def detect_source_candidates(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    headers = set(rows[0].keys())
    return [adapter.source_name for adapter in ADAPTERS if adapter.can_handle(headers)]


def dedupe_payload_for_row(row: dict[str, Any], source_name: str | None = None) -> dict[str, Any]:
    adapter = next((item for item in ADAPTERS if item.source_name == source_name), None)
    if adapter is None:
        return {key: row[key] for key in sorted(row)}
    payload: dict[str, Any] = {}
    for field in adapter.dedupe_fields:
        if field in row:
            payload[field] = row[field]
    if not payload:
        return {key: row[key] for key in sorted(row)}
    return payload


def _clean_numeric_text(value: str) -> str:
    text = value.replace("\u00A0", " ").strip()
    if text.startswith("(") and text.endswith(")"):
        text = f"-{text[1:-1].strip()}"
    return text.replace(" ", "")


def detect_numeric_separators(value: str) -> tuple[str | None, str | None, bool]:
    text = _clean_numeric_text(value)
    if not NUMBER_PATTERN.match(text):
        return None, None, False
    lower_text = text.lower()
    if "e" in lower_text:
        prefix = lower_text.split("e", maxsplit=1)[0]
    else:
        prefix = lower_text

    comma_count = prefix.count(",")
    dot_count = prefix.count(".")

    if comma_count and dot_count:
        if prefix.rfind(",") > prefix.rfind("."):
            return ",", ".", False
        return ".", ",", False

    if comma_count:
        tail_len = len(prefix.split(",")[-1])
        ambiguous = comma_count == 1 and tail_len == 3
        return ",", None if comma_count == 1 else ",", ambiguous

    if dot_count:
        tail_len = len(prefix.split(".")[-1])
        ambiguous = dot_count == 1 and tail_len == 3
        return ".", None if dot_count == 1 else ".", ambiguous

    return ".", None, False


def parse_decimal(
    value: Any,
    *,
    decimal_separator: str | None,
    thousand_separator: str | None,
) -> tuple[Decimal | None, ErrorDetail | None, WarningDetail | None]:
    if isinstance(value, Decimal):
        return value, None, None
    if isinstance(value, (int, float)):
        return Decimal(str(value)), None, None
    if value is None:
        return None, None, None

    text = _clean_numeric_text(str(value))
    if text == "":
        return None, None, None
    if text.endswith("%"):
        return (
            None,
            ErrorDetail(
                code="number_format_error",
                message="Percent values require explicit profile conversion and cannot be auto-parsed.",
            ),
            None,
        )

    if "e" in text.lower():
        normalized_scientific = text.replace(",", ".")
        try:
            return Decimal(normalized_scientific), None, None
        except InvalidOperation:
            return None, ErrorDetail(code="number_format_error", message=f"Invalid numeric value '{value}'"), None

    detected_decimal, detected_thousand, ambiguous = detect_numeric_separators(text)
    use_decimal = decimal_separator or detected_decimal
    use_thousand = thousand_separator or detected_thousand

    if ambiguous and decimal_separator is None and thousand_separator is None:
        return (
            None,
            None,
            WarningDetail(
                code="number_format_error",
                message=f"Ambiguous number format for value '{value}'.",
                hint="Provide profile separators explicitly.",
            ),
        )

    normalized = text
    if use_thousand:
        normalized = normalized.replace(use_thousand, "")
    if use_decimal and use_decimal != ".":
        normalized = normalized.replace(use_decimal, ".")

    try:
        return Decimal(normalized), None, None
    except InvalidOperation:
        return None, ErrorDetail(code="number_format_error", message=f"Invalid numeric value '{value}'"), None


def parse_datetime_with_fallback(
    value: Any,
    *,
    profile: ImportProfile,
) -> tuple[str | None, ErrorDetail | None]:
    if value is None:
        return None, None

    text = str(value).strip()
    if text == "":
        return None, None

    if ISO_PATTERN.match(text):
        try:
            iso_input = text.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(iso_input)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC).isoformat(), None
        except ValueError:
            pass

    for pattern in profile.date_patterns:
        try:
            parsed = datetime.strptime(text, pattern)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC).isoformat(), None
        except ValueError:
            continue

    try:
        parsed = date_parser.parse(
            text,
            dayfirst=bool(profile.locale and profile.locale.lower().startswith("de")),
            fuzzy=False,
        )
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat(), None
    except (ValueError, OverflowError, TypeError):
        return (
            None,
            ErrorDetail(
                code="timezone_parse_error",
                message=f"Could not parse datetime value '{value}'",
            ),
        )


def detect_column_format(
    field: str,
    values: list[Any],
    source_candidates: list[str],
    profile: ImportProfile | None,
) -> ColumnFormatDetection:
    decimal_separator: str | None = None
    thousand_separator: str | None = None
    date_pattern: str | None = None

    for value in values:
        text = "" if value is None else str(value).strip()
        if not text:
            continue
        detected_decimal, detected_thousand, _ = detect_numeric_separators(text)
        if detected_decimal is not None:
            decimal_separator = detected_decimal
            thousand_separator = detected_thousand
            break

    if profile is not None and profile.date_patterns:
        for pattern in profile.date_patterns:
            try:
                if values and values[0] is not None:
                    datetime.strptime(str(values[0]).strip(), pattern)
                    date_pattern = pattern
                    break
            except ValueError:
                continue

    return ColumnFormatDetection(
        field=field,
        decimal_separator=decimal_separator,
        thousand_separator=thousand_separator,
        date_pattern=date_pattern,
        timezone_hint=profile.timezone_hint if profile else None,
        source_candidates=source_candidates,
    )
