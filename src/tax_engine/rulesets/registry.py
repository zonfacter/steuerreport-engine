from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from tax_engine.ingestion.store import STORE

from .de_standard import DEStandardRule
from .models import MiningTaxCategory, TaxRuleset
from .strategy import TaxStrategy


def _ruleset_key(ruleset_id: str, ruleset_version: str) -> str:
    return f"{ruleset_id}::{ruleset_version}"


@dataclass(slots=True)
class RulesetRegistry:
    _rulesets: dict[str, TaxRuleset] = field(default_factory=dict)

    def _register(self, ruleset: TaxRuleset) -> None:
        self._rulesets[_ruleset_key(ruleset.ruleset_id, ruleset.ruleset_version)] = ruleset

    def register(self, ruleset: TaxRuleset) -> None:
        self._register(ruleset)

    def get(self, ruleset_id: str, ruleset_version: str | None = None) -> TaxRuleset:
        if ruleset_id in {"", None}:
            raise ValueError("Unknown ruleset_id: <empty>")

        if ruleset_version is not None:
            key = _ruleset_key(ruleset_id, ruleset_version)
            if key in self._rulesets:
                return self._rulesets[key]
            catalog_row = STORE.get_ruleset(ruleset_id=ruleset_id, ruleset_version=ruleset_version)
            if catalog_row is not None:
                return TaxRuleset.from_dict(catalog_row)
            raise ValueError(f"Unknown ruleset: {ruleset_id} v{ruleset_version}")

        direct_key = _ruleset_key(ruleset_id, "")
        direct_key_match = self._rulesets.get(direct_key)
        if direct_key_match is not None:
            return direct_key_match

        mem_matches = [ruleset for ruleset in self._rulesets.values() if ruleset.ruleset_id == ruleset_id]
        if not mem_matches:
            catalog_rows = STORE.list_rulesets(include_pending=True)
            mem_matches = [TaxRuleset.from_dict(row) for row in catalog_rows if str(row.get("ruleset_id", "")) == ruleset_id]
        if len(mem_matches) == 1:
            return mem_matches[0]
        if len(mem_matches) == 0:
            raise ValueError(f"Unknown ruleset_id: {ruleset_id}")
        raise ValueError(
            f"Ambiguous ruleset_id '{ruleset_id}' without version. "
            f"Available: {', '.join(sorted(item.ruleset_version for item in mem_matches))}"
        )

    def select_for_date(self, jurisdiction: str, value: date) -> TaxRuleset:
        annual_id = f"{jurisdiction}-{value.year}-v1.0"
        annual_matches = [
            ruleset
            for ruleset in self.list_rulesets(include_pending=True)
            if ruleset.ruleset_id == annual_id and ruleset.covers(value)
        ]
        if len(annual_matches) == 1:
            return annual_matches[0]

        matches = [
            ruleset
            for ruleset in self.list_rulesets(include_pending=False)
            if ruleset.jurisdiction == jurisdiction and ruleset.covers(value)
        ]
        if len(matches) == 1:
            return matches[0]

        id_matches = [
            ruleset
            for ruleset in self.list_rulesets(include_pending=False)
            if ruleset.ruleset_id == jurisdiction and ruleset.covers(value)
        ]
        if len(id_matches) == 1:
            return id_matches[0]
        if not matches and not id_matches:
            raise ValueError(
                f"Expected exactly one ruleset for jurisdiction={jurisdiction} and date={value}"
            )
        raise ValueError(
            f"Expected exactly one ruleset for jurisdiction={jurisdiction} and date={value}"
        )

    def resolve_for_year(
        self,
        tax_year: int,
        ruleset_id: str,
        ruleset_version: str | None = None,
    ) -> tuple[TaxRuleset, list[dict[str, str]]]:
        warnings: list[dict[str, str]] = []
        normalized_id = str(ruleset_id or "").strip()
        normalized_version = str(ruleset_version or "").strip() or None

        try:
            ruleset = self.get(normalized_id, normalized_version)
            if ruleset.covers(date(tax_year, 12, 31)):
                return ruleset, warnings
            warnings.append(
                {
                    "code": "ruleset_year_mismatch",
                    "message": (
                        f"Ruleset {ruleset.ruleset_id} v{ruleset.ruleset_version} deckt "
                        f"das Steuerjahr {tax_year} nicht vollständig ab; es wurde ein Jahres-Ruleset gesucht."
                    ),
                }
            )
        except ValueError:
            pass

        jurisdiction = _infer_jurisdiction(normalized_id)
        requested_year = _infer_year(normalized_id, normalized_version) or tax_year
        try:
            ruleset = self.select_for_date(jurisdiction, date(requested_year, 12, 31))
            if requested_year != tax_year:
                warnings.append(
                    {
                        "code": "ruleset_year_from_request",
                        "message": (
                            f"Ruleset-Eingabe verweist auf {requested_year}; Steuerlauf nutzt "
                            f"{ruleset.ruleset_id} für {requested_year}."
                        ),
                    }
                )
            return ruleset, warnings
        except ValueError:
            pass

        available = [
            item
            for item in self.list_rulesets(include_pending=True)
            if item.jurisdiction == jurisdiction
        ]
        if not available:
            raise ValueError(f"No rulesets available for jurisdiction={jurisdiction}")

        target = date(tax_year, 12, 31)
        nearest = min(available, key=lambda item: min(abs((item.valid_from - target).days), abs((item.valid_to - target).days)))
        warnings.append(
            {
                "code": "ruleset_nearest_fallback",
                "message": (
                    f"Kein bestätigtes Ruleset für {jurisdiction}-{tax_year} gefunden. "
                    f"Fallback auf {nearest.ruleset_id} v{nearest.ruleset_version}."
                ),
            }
        )
        return nearest, warnings

    def build_strategy(self, ruleset_id: str, ruleset_version: str | None = None) -> TaxStrategy:
        ruleset = self.get(ruleset_id, ruleset_version)
        if ruleset.jurisdiction == "DE":
            return DEStandardRule(ruleset)
        raise ValueError(f"No strategy registered for jurisdiction={ruleset.jurisdiction}")

    def list_rulesets(self, include_pending: bool = True) -> list[TaxRuleset]:
        deltas = STORE.list_rulesets(include_pending=include_pending)
        existing_keys = {_ruleset_key(item.ruleset_id, item.ruleset_version) for item in self._rulesets.values()}
        result: list[TaxRuleset] = list(self._rulesets.values())
        for entry in deltas:
            key = _ruleset_key(str(entry["ruleset_id"]), str(entry["ruleset_version"]))
            if key in existing_keys:
                continue
            result.append(TaxRuleset.from_dict(entry))
        result.sort(key=lambda value: (value.jurisdiction, value.valid_from, value.ruleset_id, value.ruleset_version))
        return result


def build_default_registry() -> RulesetRegistry:
    registry = RulesetRegistry()
    for year in range(2020, 2027):
        registry.register(
            TaxRuleset(
                ruleset_id=f"DE-{year}-v1.0",
                ruleset_version="1.0",
                jurisdiction="DE",
                valid_from=date(year, 1, 1),
                valid_to=date(year, 12, 31),
                exemption_limit_so=Decimal("1000.00") if year >= 2024 else Decimal("600.00"),
                other_services_exemption_limit=Decimal("256.00"),
                holding_period_months=12,
                staking_extension=False,
                mining_tax_category=MiningTaxCategory.INCOME,
            )
        )
    return registry


def _infer_jurisdiction(ruleset_id: str) -> str:
    prefix = str(ruleset_id or "").strip().upper().split("-", maxsplit=1)[0]
    return prefix if prefix else "DE"


def _infer_year(ruleset_id: str, ruleset_version: str | None) -> int | None:
    for value in (ruleset_id, ruleset_version or ""):
        match = re.search(r"(20\d{2}|21\d{2})", str(value))
        if match:
            return int(match.group(1))
    return None
