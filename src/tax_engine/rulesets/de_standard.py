from __future__ import annotations

import calendar
from datetime import date

from .models import TaxRuleset
from .strategy import RuleContext, TaxStatus, TaxStrategy


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    max_day = calendar.monthrange(year, month)[1]
    day = min(value.day, max_day)
    return date(year, month, day)


class DEStandardRule(TaxStrategy):
    def __init__(self, ruleset: TaxRuleset) -> None:
        self._ruleset = ruleset

    @property
    def ruleset(self) -> TaxRuleset:
        return self._ruleset

    def calculate_tax_status(self, context: RuleContext) -> TaxStatus:
        threshold_date = _add_months(
            context.acquisition_date,
            self._ruleset.holding_period_months,
        )
        if context.disposal_date >= threshold_date:
            return TaxStatus.EXEMPT
        return TaxStatus.TAXABLE

