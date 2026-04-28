from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from tax_engine.rulesets import MiningTaxCategory, build_default_registry


def _parse_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _event_timestamp(payload: dict[str, Any]) -> datetime | None:
    for key in ("timestamp_utc", "timestamp", "datetime", "date", "time"):
        raw = payload.get(key)
        if raw is None:
            continue
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            continue
    return None


def _to_text(payload: dict[str, Any]) -> str:
    return " ".join(
        str(payload.get(key, "")).lower()
        for key in ("event_type", "type", "label", "comment", "defi_label", "source", "tag")
    )


def _value_eur(payload: dict[str, Any]) -> Decimal:
    # Deutsche Kommentare: Erst direkte EUR-Felder prüfen, dann Fallback qty * price.
    for key in ("value_eur", "amount_eur", "income_eur", "proceeds_eur", "pnl_eur"):
        if key in payload:
            value = _parse_decimal(payload.get(key))
            if value != Decimal("0"):
                return value

    qty = Decimal("0")
    for key in ("quantity", "qty", "amount", "size"):
        if key in payload:
            qty = abs(_parse_decimal(payload.get(key)))
            break
    if qty == Decimal("0"):
        return Decimal("0")

    for key in ("price_eur", "unit_price_eur", "price"):
        if key in payload:
            price = _parse_decimal(payload.get(key))
            if price != Decimal("0"):
                return qty * price
    return Decimal("0")


def _fee_eur(payload: dict[str, Any]) -> Decimal:
    for key in ("fee_eur", "fee", "commission_eur"):
        if key in payload:
            value = abs(_parse_decimal(payload.get(key)))
            if value != Decimal("0"):
                return value
    return Decimal("0")


def _is_reward_like(payload: dict[str, Any]) -> bool:
    text = _to_text(payload)
    event_type = str(payload.get("event_type", "")).lower().strip()
    if event_type in {"mining_reward", "asset_dividend", "interest", "staking_reward", "reward_claim"}:
        return True
    return any(token in text for token in ("reward", "staking", "mining", "claim", "dividend", "interest"))


def _is_mining_like(payload: dict[str, Any]) -> bool:
    text = _to_text(payload)
    event_type = str(payload.get("event_type", "")).lower().strip()
    if event_type == "mining_reward":
        return True
    if str(payload.get("source", "")).lower().strip() == "heliumgeek":
        return True
    return any(token in text for token in ("mining", "hotspot", "helium", "iot", "mobile", "myst"))


def _is_data_credit_usage(payload: dict[str, Any]) -> bool:
    asset = str(payload.get("asset", "")).upper().strip()
    event_type = str(payload.get("event_type", "")).lower().strip()
    text = _to_text(payload)
    if asset in {"DC", "DATA_CREDIT", "DATA CREDITS"}:
        return True
    if "data_credit" in event_type or "data credit" in text:
        return True
    return False


def _is_business_override(payload: dict[str, Any]) -> bool:
    # Deutsche Kommentare: Manuelle Tax-Overrides aus Import/Review haben Vorrang.
    raw = str(payload.get("tax_category", payload.get("tax_domain", ""))).strip().upper()
    return raw in {"BUSINESS", "EUER", "ANLAGE_G", "GEWERBE"}


def build_tax_domain_summary(
    *,
    raw_events: list[dict[str, Any]],
    tax_lines: list[dict[str, Any]],
    derivative_lines: list[dict[str, Any]],
    tax_year: int,
    ruleset_id: str,
) -> dict[str, Any]:
    registry = build_default_registry()
    ruleset = registry.get(ruleset_id)

    so_services_income = Decimal("0")
    business_income = Decimal("0")
    business_expenses = Decimal("0")
    unresolved_valuation_events = 0
    reward_event_count = 0
    mining_event_count = 0
    data_credit_event_count = 0

    for event in raw_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ts = _event_timestamp(payload)
        if ts is None or ts.year != tax_year:
            continue

        if _is_data_credit_usage(payload):
            data_credit_event_count += 1
            value = _value_eur(payload)
            fee = _fee_eur(payload)
            expense = abs(value) if value != Decimal("0") else fee
            business_expenses += expense
            if expense == Decimal("0"):
                unresolved_valuation_events += 1
            continue

        if _is_reward_like(payload):
            reward_event_count += 1
            is_mining = _is_mining_like(payload)
            if is_mining:
                mining_event_count += 1
            value = _value_eur(payload)
            if value == Decimal("0"):
                unresolved_valuation_events += 1
            is_business = _is_business_override(payload)
            if not is_business and is_mining and ruleset.mining_tax_category == MiningTaxCategory.BUSINESS:
                is_business = True
            if is_business:
                business_income += value
            else:
                so_services_income += value

    taxable_private_gain = Decimal("0")
    taxable_private_loss = Decimal("0")
    exempt_private_gain = Decimal("0")
    exempt_private_loss = Decimal("0")

    for line in tax_lines:
        gain_loss = _parse_decimal(line.get("gain_loss_eur", "0"))
        status = str(line.get("tax_status", "")).lower().strip()
        if status == "exempt":
            if gain_loss >= 0:
                exempt_private_gain += gain_loss
            else:
                exempt_private_loss += gain_loss
        else:
            if gain_loss >= 0:
                taxable_private_gain += gain_loss
            else:
                taxable_private_loss += gain_loss

    derivative_net = Decimal("0")
    derivative_loss_abs = Decimal("0")
    for line in derivative_lines:
        gain_loss = _parse_decimal(line.get("gain_loss_eur", "0"))
        derivative_net += gain_loss
        if gain_loss < 0:
            derivative_loss_abs += abs(gain_loss)

    return {
        "ruleset_id": ruleset_id,
        "tax_year": tax_year,
        "classification_counts": {
            "reward_events": reward_event_count,
            "mining_events": mining_event_count,
            "data_credit_events": data_credit_event_count,
            "unresolved_valuation_events": unresolved_valuation_events,
        },
        "anlage_so": {
            "leistungen_income_eur": so_services_income.to_eng_string(),
            "private_veraeusserung_taxable_gain_eur": taxable_private_gain.to_eng_string(),
            "private_veraeusserung_taxable_loss_eur": taxable_private_loss.to_eng_string(),
            "private_veraeusserung_net_taxable_eur": (taxable_private_gain + taxable_private_loss).to_eng_string(),
            "private_veraeusserung_exempt_gain_eur": exempt_private_gain.to_eng_string(),
            "private_veraeusserung_exempt_loss_eur": exempt_private_loss.to_eng_string(),
        },
        "euer": {
            "betriebseinnahmen_mining_staking_eur": business_income.to_eng_string(),
            "betriebsausgaben_data_credits_eur": business_expenses.to_eng_string(),
            "betriebsergebnis_eur": (business_income - business_expenses).to_eng_string(),
        },
        "termingeschaefte": {
            "netto_eur": derivative_net.to_eng_string(),
            "verlust_summe_abs_eur": derivative_loss_abs.to_eng_string(),
        },
    }

