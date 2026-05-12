from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from .models import TaxRuleset


class TaxStatus(StrEnum):
    TAXABLE = "taxable"
    EXEMPT = "exempt"


@dataclass(frozen=True, slots=True)
class RuleContext:
    acquisition_date: date
    disposal_date: date
    amount: Decimal


class TaxStrategy(ABC):
    @property
    @abstractmethod
    def ruleset(self) -> TaxRuleset:
        raise NotImplementedError

    @abstractmethod
    def calculate_tax_status(self, context: RuleContext) -> TaxStatus:
        raise NotImplementedError

