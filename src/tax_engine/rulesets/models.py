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
    other_services_exemption_limit: Decimal
    holding_period_months: int
    staking_extension: bool
    mining_tax_category: MiningTaxCategory

    def covers(self, value: date) -> bool:
        return self.valid_from <= value <= self.valid_to

    def to_dict(self) -> dict[str, object]:
        return {
            "ruleset_id": self.ruleset_id,
            "ruleset_version": self.ruleset_version,
            "jurisdiction": self.jurisdiction,
            "valid_from": self.valid_from.isoformat(),
            "valid_to": self.valid_to.isoformat(),
            "exemption_limit_so": self.exemption_limit_so.to_eng_string(),
            "other_services_exemption_limit": self.other_services_exemption_limit.to_eng_string(),
            "holding_period_months": self.holding_period_months,
            "staking_extension": self.staking_extension,
            "mining_tax_category": self.mining_tax_category.value,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> TaxRuleset:
        try:
            ruleset_id = str(payload["ruleset_id"])
            ruleset_version = str(payload["ruleset_version"])
            jurisdiction = str(payload["jurisdiction"])
            valid_from = date.fromisoformat(str(payload["valid_from"]))
            valid_to = date.fromisoformat(str(payload["valid_to"]))
            exemption_limit_so = Decimal(str(payload["exemption_limit_so"]))
            other_services_exemption_limit = Decimal(str(payload.get("other_services_exemption_limit", "256.00")))
            holding_period_months = int(str(payload["holding_period_months"]))
            staking_extension = bool(payload["staking_extension"])
            category_raw = str(payload["mining_tax_category"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid ruleset payload: {exc}") from exc

        category = MiningTaxCategory(category_raw)
        return cls(
            ruleset_id=ruleset_id,
            ruleset_version=ruleset_version,
            jurisdiction=jurisdiction,
            valid_from=valid_from,
            valid_to=valid_to,
            exemption_limit_so=exemption_limit_so,
            other_services_exemption_limit=other_services_exemption_limit,
            holding_period_months=holding_period_months,
            staking_extension=staking_extension,
            mining_tax_category=category,
        )
