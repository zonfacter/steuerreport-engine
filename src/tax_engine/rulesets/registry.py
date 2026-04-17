from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from .de_standard import DEStandardRule
from .models import MiningTaxCategory, TaxRuleset
from .strategy import TaxStrategy


@dataclass(slots=True)
class RulesetRegistry:
    _rulesets: dict[str, TaxRuleset] = field(default_factory=dict)

    def register(self, ruleset: TaxRuleset) -> None:
        self._rulesets[ruleset.ruleset_id] = ruleset

    def get(self, ruleset_id: str) -> TaxRuleset:
        try:
            return self._rulesets[ruleset_id]
        except KeyError as exc:
            raise ValueError(f"Unknown ruleset_id: {ruleset_id}") from exc

    def select_for_date(self, jurisdiction: str, value: date) -> TaxRuleset:
        matches = [
            ruleset
            for ruleset in self._rulesets.values()
            if ruleset.jurisdiction == jurisdiction and ruleset.covers(value)
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected exactly one ruleset for jurisdiction={jurisdiction} and date={value}"
            )
        return matches[0]

    def build_strategy(self, ruleset_id: str) -> TaxStrategy:
        ruleset = self.get(ruleset_id)
        if ruleset.jurisdiction == "DE":
            return DEStandardRule(ruleset)
        raise ValueError(
            f"No strategy registered for jurisdiction={ruleset.jurisdiction}"
        )


def build_default_registry() -> RulesetRegistry:
    registry = RulesetRegistry()
    registry.register(
        TaxRuleset(
            ruleset_id="DE-2026-v1.0",
            ruleset_version="1.0",
            jurisdiction="DE",
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 12, 31),
            exemption_limit_so=Decimal("1000.00"),
            holding_period_months=12,
            staking_extension=False,
            mining_tax_category=MiningTaxCategory.INCOME,
        )
    )
    return registry

