from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from tax_engine.rulesets import RuleContext, TaxStatus, build_default_registry


def test_select_for_date_returns_de_2026_ruleset() -> None:
    registry = build_default_registry()

    ruleset = registry.select_for_date("DE", date(2026, 5, 1))

    assert ruleset.ruleset_id == "DE-2026-v1.0"
    assert ruleset.exemption_limit_so == Decimal("1000.00")
    assert ruleset.other_services_exemption_limit == Decimal("256.00")


def test_default_registry_covers_de_years_2020_to_2026() -> None:
    registry = build_default_registry()

    for year in range(2020, 2027):
        ruleset = registry.select_for_date("DE", date(year, 12, 31))
        assert ruleset.ruleset_id == f"DE-{year}-v1.0"
        assert ruleset.ruleset_version == "1.0"


def test_resolve_for_year_accepts_ui_style_de_version_alias() -> None:
    registry = build_default_registry()

    ruleset, warnings = registry.resolve_for_year(
        tax_year=2026,
        ruleset_id="DE",
        ruleset_version="2026-v1",
    )

    assert ruleset.ruleset_id == "DE-2026-v1.0"
    assert ruleset.ruleset_version == "1.0"
    assert warnings == []


def test_resolve_for_year_uses_nearest_fallback_for_missing_future_year() -> None:
    registry = build_default_registry()

    ruleset, warnings = registry.resolve_for_year(
        tax_year=2027,
        ruleset_id="DE",
        ruleset_version=None,
    )

    assert ruleset.ruleset_id == "DE-2026-v1.0"
    assert warnings[0]["code"] == "ruleset_nearest_fallback"


def test_select_for_date_raises_on_missing_ruleset() -> None:
    registry = build_default_registry()

    with pytest.raises(ValueError):
        _ = registry.select_for_date("DE", date(2027, 1, 1))


def test_de_strategy_marks_holding_period_as_exempt() -> None:
    registry = build_default_registry()
    strategy = registry.build_strategy("DE-2026-v1.0")

    status = strategy.calculate_tax_status(
        RuleContext(
            acquisition_date=date(2025, 1, 1),
            disposal_date=date(2026, 1, 1),
            amount=Decimal("1.0"),
        )
    )

    assert status == TaxStatus.EXEMPT


def test_de_strategy_marks_short_holding_period_as_taxable() -> None:
    registry = build_default_registry()
    strategy = registry.build_strategy("DE-2026-v1.0")

    status = strategy.calculate_tax_status(
        RuleContext(
            acquisition_date=date(2026, 2, 1),
            disposal_date=date(2026, 12, 31),
            amount=Decimal("1.0"),
        )
    )

    assert status == TaxStatus.TAXABLE
