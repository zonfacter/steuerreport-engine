from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def _parse_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if not text:
            return Decimal("0")
        return Decimal(text)
    return Decimal("0")


def _extract_timestamp(payload: dict[str, Any]) -> datetime | None:
    for key in ("timestamp", "datetime", "date", "time"):
        raw = payload.get(key)
        if raw is None:
            continue
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            continue
    return None


def _extract_asset(payload: dict[str, Any]) -> str:
    for key in ("asset", "symbol", "base_asset", "coin"):
        value = payload.get(key)
        if value:
            return str(value).upper()
    return "UNKNOWN"


def _extract_qty(payload: dict[str, Any]) -> Decimal:
    for key in ("qty", "quantity", "amount", "size"):
        if key in payload:
            try:
                return _parse_decimal(payload.get(key))
            except InvalidOperation:
                return Decimal("0")
    return Decimal("0")


def _classify(payload: dict[str, Any]) -> str:
    text = " ".join(str(payload.get(k, "")).lower() for k in ("type", "event_type", "side", "tag"))
    if "liquidat" in text:
        return "liquidation"
    if any(token in text for token in ("future", "margin", "perp", "derivative")):
        return "derivative"
    if any(token in text for token in ("reward", "staking", "mining", "claim")):
        return "reward"
    if any(token in text for token in ("transfer", "deposit", "withdraw")):
        return "transfer"
    return "spot"


def process_events_for_year(raw_events: list[dict[str, Any]], tax_year: int) -> dict[str, Any]:
    relevant_events: list[dict[str, Any]] = []
    for event in raw_events:
        payload = event["payload"]
        ts = _extract_timestamp(payload)
        if ts is None:
            continue
        if ts.year == tax_year:
            relevant_events.append(event)

    inventory: dict[str, Decimal] = {}
    class_counts: dict[str, int] = {
        "spot": 0,
        "derivative": 0,
        "reward": 0,
        "transfer": 0,
        "liquidation": 0,
    }
    short_sell_violations = 0

    for event in relevant_events:
        payload = event["payload"]
        classification = _classify(payload)
        class_counts[classification] = class_counts.get(classification, 0) + 1

        asset = _extract_asset(payload)
        qty = _extract_qty(payload)
        if classification != "spot":
            continue

        side = str(payload.get("side", "")).lower()
        if not side:
            # Fallback: negative quantity als Verkauf interpretieren.
            side = "sell" if qty < 0 else "buy"

        inventory.setdefault(asset, Decimal("0"))
        if side in ("sell", "ask"):
            inventory[asset] -= abs(qty)
        else:
            inventory[asset] += abs(qty)

        if inventory[asset] < Decimal("0"):
            short_sell_violations += 1

    inventory_summary = {
        asset: amount.to_eng_string()
        for asset, amount in sorted(inventory.items(), key=lambda item: item[0])
    }

    return {
        "tax_year": tax_year,
        "processed_events": len(relevant_events),
        "class_counts": class_counts,
        "short_sell_violations": short_sell_violations,
        "inventory_end": inventory_summary,
    }

