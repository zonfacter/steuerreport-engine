from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from dateutil import parser as date_parser

SUBUNIT_FACTORS: dict[str, Decimal] = {
    "lamports": Decimal("0.000000001"),
    "satoshis": Decimal("0.00000001"),
    "wei": Decimal("0.000000000000000001"),
}

_NUMBER_RE = re.compile(r"^[\s\-\+\(\)\d\.,eE]+$")


def detect_number_locale(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None
    if "," in text and "." in text:
        return "comma_decimal" if text.rfind(",") > text.rfind(".") else "dot_decimal"
    if "," in text and "." not in text:
        if re.match(r"^\d{1,3}(,\d{3})+$", text):
            return "ambiguous"
        return "comma_decimal"
    if "." in text and "," not in text:
        return "dot_decimal"
    return None


def parse_decimal_value(value: Any, locale_hint: str | None = None) -> tuple[Decimal | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, Decimal):
        return value, None
    if isinstance(value, int):
        return Decimal(value), None
    if isinstance(value, float):
        return Decimal(str(value)), None

    text = str(value).strip()
    if not text:
        return None, None
    if not _NUMBER_RE.match(text):
        return None, "invalid_numeric_token"

    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()

    locale = locale_hint or detect_number_locale(text)
    if locale == "ambiguous":
        return None, "ambiguous_number_format"

    normalized = text.replace(" ", "")
    if locale == "comma_decimal":
        normalized = normalized.replace(".", "")
        normalized = normalized.replace(",", ".")
    else:
        normalized = normalized.replace(",", "")

    try:
        parsed = Decimal(normalized)
    except InvalidOperation:
        return None, "invalid_numeric_token"

    if negative:
        parsed = -parsed
    return parsed, None


def parse_datetime_value(value: Any, timezone: str = "UTC") -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None, None
        dayfirst = False
        yearfirst = False
        # Deutsche Formate wie 12.05.2021 als dd.mm.yyyy behandeln.
        if re.match(r"^\d{1,2}\.\d{1,2}\.\d{2,4}([ T].*)?$", text):
            dayfirst = True
        # Binance-Sonderfall: yy-mm-dd HH:MM:SS (z. B. 25-06-12 10:51:05 => 2025-06-12).
        elif re.match(r"^\d{2}-\d{2}-\d{2}([ T]\d{1,2}:\d{2}(:\d{2})?)?$", text):
            yearfirst = True
            dayfirst = False
        # ISO-nahe Formate mit Jahr vorne.
        elif re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", text):
            yearfirst = True
        try:
            dt = date_parser.parse(text, dayfirst=dayfirst, yearfirst=yearfirst)
        except (ValueError, TypeError, OverflowError):
            return None, "invalid_datetime"

    if dt.tzinfo is None:
        # Wir normalisieren naive Zeitstempel explizit auf UTC.
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat(), None


def convert_subunit(value: Decimal, subunit: str) -> tuple[Decimal | None, str | None]:
    factor = SUBUNIT_FACTORS.get(subunit.lower())
    if factor is None:
        return None, "unknown_subunit"
    return value * factor, None


def detect_fields(rows: Iterable[dict[str, Any]]) -> tuple[list[str], list[str]]:
    numeric_fields: set[str] = set()
    datetime_fields: set[str] = set()

    for row in rows:
        for key, value in row.items():
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                continue
            if _NUMBER_RE.match(text):
                numeric_fields.add(key)
                continue
            parsed_dt, dt_error = parse_datetime_value(value)
            if parsed_dt is not None and dt_error is None:
                datetime_fields.add(key)

    return sorted(numeric_fields), sorted(datetime_fields)
