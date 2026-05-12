from __future__ import annotations

from decimal import Decimal

from tax_engine.ingestion.parser import convert_subunit, parse_decimal_value


def test_parse_decimal_handles_parentheses_negative() -> None:
    value, error = parse_decimal_value("(1,234.50)")
    assert error is None
    assert value == Decimal("-1234.50")


def test_parse_decimal_handles_scientific_notation() -> None:
    value, error = parse_decimal_value("1.23e-8")
    assert error is None
    assert value == Decimal("1.23E-8")


def test_parse_decimal_detects_ambiguous_number() -> None:
    value, error = parse_decimal_value("1,234")
    assert value is None
    assert error == "ambiguous_number_format"


def test_convert_subunit_lamports_to_sol() -> None:
    value, error = convert_subunit(Decimal("1000000000"), "lamports")
    assert error is None
    assert value == Decimal("1.000000000")

