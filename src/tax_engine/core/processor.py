from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(slots=True)
class SpotEvent:
    unique_event_id: str
    timestamp: datetime
    asset: str
    side: str
    qty: Decimal
    unit_price_eur: Decimal
    fee_eur: Decimal


@dataclass(slots=True)
class Lot:
    buy_timestamp: datetime
    remaining_qty: Decimal
    unit_cost_eur: Decimal
    source_event_id: str


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
                return abs(_parse_decimal(payload.get(key)))
            except InvalidOperation:
                return Decimal("0")
    return Decimal("0")


def _extract_unit_price_eur(payload: dict[str, Any]) -> Decimal:
    for key in ("price_eur", "unit_price_eur", "price"):
        if key in payload:
            try:
                return _parse_decimal(payload.get(key))
            except InvalidOperation:
                return Decimal("0")
    return Decimal("0")


def _extract_fee_eur(payload: dict[str, Any]) -> Decimal:
    for key in ("fee_eur", "fee", "commission_eur"):
        if key in payload:
            try:
                return abs(_parse_decimal(payload.get(key)))
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


def _extract_side(payload: dict[str, Any], qty: Decimal) -> str:
    side = str(payload.get("side", "")).lower().strip()
    if side in ("buy", "bid"):
        return "buy"
    if side in ("sell", "ask"):
        return "sell"
    return "buy" if qty >= 0 else "sell"


def _to_spot_events(raw_events: Iterable[dict[str, Any]]) -> tuple[list[SpotEvent], dict[str, int]]:
    spot_events: list[SpotEvent] = []
    class_counts: dict[str, int] = {
        "spot": 0,
        "derivative": 0,
        "reward": 0,
        "transfer": 0,
        "liquidation": 0,
    }

    for event in raw_events:
        payload = event["payload"]
        event_class = _classify(payload)
        class_counts[event_class] = class_counts.get(event_class, 0) + 1
        if event_class != "spot":
            continue
        ts = _extract_timestamp(payload)
        if ts is None:
            continue
        qty = _extract_qty(payload)
        if qty <= 0:
            continue
        spot_events.append(
            SpotEvent(
                unique_event_id=event["unique_event_id"],
                timestamp=ts,
                asset=_extract_asset(payload),
                side=_extract_side(payload, qty),
                qty=qty,
                unit_price_eur=_extract_unit_price_eur(payload),
                fee_eur=_extract_fee_eur(payload),
            )
        )

    spot_events.sort(key=lambda event: event.timestamp)
    return spot_events, class_counts


def process_events_for_year(raw_events: list[dict[str, Any]], tax_year: int) -> dict[str, Any]:
    spot_events, class_counts = _to_spot_events(raw_events)
    lots_by_asset: dict[str, deque[Lot]] = defaultdict(deque)

    tax_lines: list[dict[str, str | int]] = []
    short_sell_violations = 0
    processed_events = 0

    for event in spot_events:
        if event.timestamp.year > tax_year:
            continue
        processed_events += 1

        if event.side == "buy":
            total_cost = (event.qty * event.unit_price_eur) + event.fee_eur
            unit_cost = (total_cost / event.qty) if event.qty > 0 else Decimal("0")
            lots_by_asset[event.asset].append(
                Lot(
                    buy_timestamp=event.timestamp,
                    remaining_qty=event.qty,
                    unit_cost_eur=unit_cost,
                    source_event_id=event.unique_event_id,
                )
            )
            continue

        qty_to_sell = event.qty
        total_proceeds = (event.qty * event.unit_price_eur) - event.fee_eur
        unit_proceeds = (total_proceeds / event.qty) if event.qty > 0 else Decimal("0")

        while qty_to_sell > Decimal("0"):
            if not lots_by_asset[event.asset]:
                short_sell_violations += 1
                fallback_qty = qty_to_sell
                if event.timestamp.year == tax_year:
                    tax_lines.append(
                        {
                            "asset": event.asset,
                            "qty": fallback_qty.to_eng_string(),
                            "buy_timestamp_utc": event.timestamp.isoformat(),
                            "sell_timestamp_utc": event.timestamp.isoformat(),
                            "cost_basis_eur": Decimal("0").to_eng_string(),
                            "proceeds_eur": (fallback_qty * unit_proceeds).to_eng_string(),
                            "gain_loss_eur": (fallback_qty * unit_proceeds).to_eng_string(),
                            "hold_days": 0,
                            "tax_status": "taxable",
                            "source_event_id": event.unique_event_id,
                        }
                    )
                qty_to_sell = Decimal("0")
                break

            current_lot = lots_by_asset[event.asset][0]
            matched_qty = min(qty_to_sell, current_lot.remaining_qty)
            cost_basis = matched_qty * current_lot.unit_cost_eur
            proceeds = matched_qty * unit_proceeds
            gain_loss = proceeds - cost_basis
            hold_days = (event.timestamp.date() - current_lot.buy_timestamp.date()).days
            tax_status = "exempt" if hold_days > 365 else "taxable"

            if event.timestamp.year == tax_year:
                tax_lines.append(
                    {
                        "asset": event.asset,
                        "qty": matched_qty.to_eng_string(),
                        "buy_timestamp_utc": current_lot.buy_timestamp.isoformat(),
                        "sell_timestamp_utc": event.timestamp.isoformat(),
                        "cost_basis_eur": cost_basis.to_eng_string(),
                        "proceeds_eur": proceeds.to_eng_string(),
                        "gain_loss_eur": gain_loss.to_eng_string(),
                        "hold_days": hold_days,
                        "tax_status": tax_status,
                        "source_event_id": event.unique_event_id,
                    }
                )

            current_lot.remaining_qty -= matched_qty
            qty_to_sell -= matched_qty
            if current_lot.remaining_qty <= Decimal("0"):
                lots_by_asset[event.asset].popleft()

    inventory_end = {
        asset: sum((lot.remaining_qty for lot in lots), start=Decimal("0")).to_eng_string()
        for asset, lots in sorted(lots_by_asset.items(), key=lambda item: item[0])
        if lots
    }

    return {
        "tax_year": tax_year,
        "processed_events": processed_events,
        "class_counts": class_counts,
        "short_sell_violations": short_sell_violations,
        "inventory_end": inventory_end,
        "tax_line_count": len(tax_lines),
        "tax_lines": tax_lines,
    }

