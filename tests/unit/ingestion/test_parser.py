from decimal import Decimal

from tax_engine.ingestion.models import ImportProfile
from tax_engine.ingestion.parser import (
    detect_source_candidates,
    parse_datetime_with_fallback,
    parse_decimal,
)


def test_parse_decimal_supported_formats() -> None:
    samples = {
        "1234.56": Decimal("1234.56"),
        "1234,56": Decimal("1234.56"),
        "1,234.56": Decimal("1234.56"),
        "1.234,56": Decimal("1234.56"),
        "1 234,56": Decimal("1234.56"),
        "(1,234.50)": Decimal("-1234.50"),
        "1.23e-8": Decimal("0.0000000123"),
    }

    for value, expected in samples.items():
        parsed, error, warning = parse_decimal(value, decimal_separator=None, thousand_separator=None)
        assert error is None
        assert warning is None
        assert parsed == expected


def test_parse_decimal_ambiguous_number_is_warning() -> None:
    parsed, error, warning = parse_decimal("1,234", decimal_separator=None, thousand_separator=None)

    assert parsed is None
    assert error is None
    assert warning is not None
    assert warning.code == "number_format_error"


def test_parse_datetime_fallback_with_iso_and_locale_pattern() -> None:
    profile = ImportProfile(
        profile_id="de_profile",
        profile_version="1.0.0",
        locale="de_DE",
        date_patterns=["%d.%m.%Y %H:%M:%S"],
    )

    parsed_iso, iso_error = parse_datetime_with_fallback("2026-01-02T13:30:00Z", profile=profile)
    parsed_locale, locale_error = parse_datetime_with_fallback("02.01.2026 13:30:00", profile=profile)

    assert iso_error is None
    assert locale_error is None
    assert parsed_iso is not None and parsed_iso.endswith("+00:00")
    assert parsed_locale is not None and parsed_locale.endswith("+00:00")


def test_detect_source_candidates_binance_and_bitget() -> None:
    binance_rows = [{"Date(UTC)": "2026-01-01", "Pair": "BTCUSDT", "Side": "BUY", "Price": "1", "Executed": "1"}]
    bitget_rows = [{"time": "2026-01-01", "symbol": "BTCUSDT", "side": "buy", "price": "1", "size": "1"}]

    assert detect_source_candidates(binance_rows) == ["binance"]
    assert detect_source_candidates(bitget_rows) == ["bitget"]
