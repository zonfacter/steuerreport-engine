from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class MiningTaxCategory(StrEnum):
    INCOME = "INCOME"
    BUSINESS = "BUSINESS"


@dataclass(frozen=True, slots=True)
class TaxRuleset:
    ruleset_id: str
    ruleset_version: str
    jurisdiction: str
    valid_from: date
    valid_to: date
    exemption_limit_so: Decimal
    holding_period_months: int
    staking_extension: bool
    mining_tax_category: MiningTaxCategory

    def covers(self, value: date) -> bool:
        return self.valid_from <= value <= self.valid_to

