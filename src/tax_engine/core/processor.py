from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from tax_engine.rulesets import RuleContext, TaxStatus, TaxStrategy, build_default_registry

STABLE_ASSETS = {"EUR", "USDT", "USDC", "BUSD", "FDUSD", "DAI", "TUSD", "USDP"}


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
    for key in ("timestamp_utc", "timestamp", "datetime", "date", "time"):
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
    normalized_helium_qty = _extract_heliumgeek_display_qty(payload)
    if normalized_helium_qty > 0:
        return normalized_helium_qty
    for key in ("qty", "quantity", "amount", "size"):
        if key in payload:
            try:
                return abs(_parse_decimal(payload.get(key)))
            except InvalidOperation:
                return Decimal("0")
    return Decimal("0")


def _extract_heliumgeek_display_qty(payload: dict[str, Any]) -> Decimal:
    if str(payload.get("source", "")).lower().strip() != "heliumgeek":
        return Decimal("0")
    asset = _extract_asset(payload)
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0")
    token_fields = (
        ("IOT Token", "IOT Tokens"),
        ("MOBILE Token", "MOBILE Tokens"),
    )
    for token_field, amount_field in token_fields:
        if str(raw_row.get(token_field, "")).upper().strip() != asset:
            continue
        try:
            return abs(_parse_decimal(raw_row.get(amount_field)))
        except InvalidOperation:
            return Decimal("0")
    return Decimal("0")


def _extract_unit_price_eur(payload: dict[str, Any]) -> Decimal:
    lookup = _normalize_payload_lookup(payload)
    for key in (
        "price_eur",
        "unit_price_eur",
        "unitpriceeur",
        "price",
        "averageprice",
        "avgprice",
        "executionprice",
        "spotprice",
        "tradeprice",
    ):
        if key in payload:
            try:
                return _parse_decimal(payload.get(key))
            except InvalidOperation:
                return Decimal("0")
        raw = _lookup_decimal(lookup, (key,))
        if raw is not None:
            return raw
    return Decimal("0")


def _extract_fee_eur(payload: dict[str, Any]) -> Decimal:
    for key in ("fee_eur", "fee", "commission_eur"):
        if key in payload:
            try:
                return abs(_parse_decimal(payload.get(key)))
            except InvalidOperation:
                return Decimal("0")
    return Decimal("0")


def _extract_event_fx_rate(payload: dict[str, Any]) -> Decimal:
    for key in ("fx_rate_usd_eur", "usd_to_eur", "fx_usd_eur", "usd_eur_rate"):
        try:
            rate = _parse_decimal(payload.get(key))
        except InvalidOperation:
            rate = Decimal("0")
        if rate > 0:
            return rate
    return Decimal("0")


def _stable_to_eur_rate(asset: str, payload: dict[str, Any]) -> Decimal:
    normalized = str(asset or "").upper()
    if normalized == "EUR":
        return Decimal("1")
    if normalized in STABLE_ASSETS:
        return _extract_event_fx_rate(payload)
    return Decimal("0")


def _infer_unit_price_eur(payload: dict[str, Any], asset: str, qty: Decimal, base_price: Decimal) -> Decimal:
    if base_price > 0:
        return base_price
    if qty <= 0:
        return Decimal("0")

    asset_norm = str(asset or "").upper()
    direct_rate = _stable_to_eur_rate(asset_norm, payload)
    if direct_rate > 0:
        return direct_rate

    lookup = _normalize_payload_lookup(payload)
    incoming_asset = _lookup_value(lookup, ("incomingasset", "incoming_asset", "toasset", "to_asset", "buyasset"))
    outgoing_asset = _lookup_value(lookup, ("outgoingasset", "outgoing_asset", "fromasset", "from_asset", "sellasset"))
    incoming_amount = _lookup_decimal(lookup, ("incomingamount", "incoming_amount", "toamount", "to_amount", "buyamount"))
    outgoing_amount = _lookup_decimal(lookup, ("outgoingamount", "outgoing_amount", "fromamount", "from_amount", "sellamount"))
    if incoming_amount is None or incoming_amount == Decimal("0"):
        incoming_amount = _lookup_decimal(lookup, ("quantity", "amount", "size", "received_amount", "executed_amount", "inamount"))
    if outgoing_amount is None or outgoing_amount == Decimal("0"):
        outgoing_amount = _lookup_decimal(lookup, ("sold_amount", "spent_amount", "outamount"))
    incoming_amount = abs(incoming_amount)
    outgoing_amount = abs(outgoing_amount)

    in_rate = _stable_to_eur_rate(incoming_asset, payload)
    out_rate = _stable_to_eur_rate(outgoing_asset, payload)

    if in_rate == Decimal("0") and asset_norm == incoming_asset and incoming_amount > 0:
        usd_candidate = _lookup_decimal(lookup, ("income_usd", "proceeds_usd", "amount_usd", "rawusdamount"))
        if usd_candidate > 0 and _extract_event_fx_rate(payload) > 0:
            return (usd_candidate / incoming_amount).copy_abs()

    if asset_norm == incoming_asset and incoming_amount > 0 and out_rate > 0 and outgoing_amount > 0:
        total_eur = outgoing_amount * out_rate
        return total_eur / incoming_amount
    if asset_norm == outgoing_asset and outgoing_amount > 0 and in_rate > 0 and incoming_amount > 0:
        total_eur = incoming_amount * in_rate
        return total_eur / outgoing_amount

    # fallback: berechne aus USD-Wert auf Event-Ebene, wenn vorhanden
    usd_value = _lookup_decimal(lookup, ("priceusd", "valueusd", "incomeusd", "proceedsusd"))
    if usd_value is not None and usd_value > 0 and _extract_event_fx_rate(payload) > 0:
        return usd_value / qty

    return Decimal("0")


def _normalize_payload_lookup(payload: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(key, str):
            values[key.strip().lower().replace(" ", "").replace("_", "")] = value
    raw_row = payload.get("raw_row")
    if isinstance(raw_row, dict):
        for key, value in raw_row.items():
            if isinstance(key, str):
                values[f"raw:{key.strip().lower().replace(' ', '').replace('_', '')}"] = value
    return values


def _lookup_value(lookup: dict[str, Any], aliases: tuple[str, ...]) -> str:
    for alias in aliases:
        for candidate in (alias.lower().replace(" ", "").replace("_", ""), f"raw:{alias.lower().replace(' ', '').replace('_', '')}"):
            raw_value = lookup.get(candidate)
            if raw_value is None:
                continue
            text = str(raw_value).strip()
            if text:
                return text.upper()
    return ""


def _lookup_decimal(lookup: dict[str, Any], aliases: tuple[str, ...]) -> Decimal:
    for alias in aliases:
        for candidate in (alias.lower().replace(" ", "").replace("_", ""), f"raw:{alias.lower().replace(' ', '').replace('_', '')}"):
            raw_value = lookup.get(candidate)
            if raw_value is None or raw_value == "":
                continue
            try:
                return abs(_parse_decimal(raw_value))
            except InvalidOperation:
                continue
    return Decimal("0")


def _classify(payload: dict[str, Any]) -> str:
    text = " ".join(
        str(payload.get(k, "")).lower()
        for k in ("type", "event_type", "side", "tag", "defi_label", "source")
    )
    event_type = str(payload.get("event_type", "")).lower().strip()
    side = str(payload.get("side", "")).lower().strip()
    defi_label = str(payload.get("defi_label", "")).lower().strip()

    if "liquidat" in text:
        return "liquidation"
    if any(token in text for token in ("future", "margin", "perp", "derivative")):
        return "derivative"

    if event_type in {"swap_in_aggregated", "swap_out_aggregated"}:
        return "spot"

    if event_type in {"token_transfer", "sol_transfer"}:
        if defi_label in {"swap", "lp"}:
            return "spot"
        if defi_label in {"claim", "staking"} and side == "in":
            return "reward"

    if any(token in text for token in ("reward", "staking", "mining", "claim")):
        return "reward"
    if any(token in text for token in ("transfer", "deposit", "withdraw", "fee")):
        return "transfer"
    return "spot"


def _resolve_tax_status(
    strategy: TaxStrategy,
    acquisition_timestamp: datetime,
    disposal_timestamp: datetime,
) -> str:
    status = strategy.calculate_tax_status(
        context=RuleContext(
            acquisition_date=acquisition_timestamp.date(),
            disposal_date=disposal_timestamp.date(),
            amount=Decimal("0"),
        )
    )
    return "exempt" if status == TaxStatus.EXEMPT else "taxable"


def _extract_side(payload: dict[str, Any], qty: Decimal) -> str:
    side = str(payload.get("side", "")).lower().strip()
    if side in ("buy", "bid"):
        return "buy"
    if side in ("sell", "ask"):
        return "sell"
    if side == "in":
        return "buy"
    if side == "out":
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
                unit_price_eur=_infer_unit_price_eur(
                    payload=payload,
                    asset=_extract_asset(payload),
                    qty=qty,
                    base_price=_extract_unit_price_eur(payload),
                ),
                fee_eur=_extract_fee_eur(payload),
            )
        )

    spot_events.sort(key=lambda event: event.timestamp)
    return spot_events, class_counts


def process_events_for_year(
    raw_events: list[dict[str, Any]],
    tax_year: int,
    ruleset_id: str = "DE-2026-v1.0",
    ruleset_version: str | None = None,
) -> dict[str, Any]:
    spot_events, class_counts = _to_spot_events(raw_events)
    lots_by_asset: dict[str, deque[Lot]] = defaultdict(deque)
    registry = build_default_registry()
    strategy = registry.build_strategy(ruleset_id=ruleset_id, ruleset_version=ruleset_version)

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
            tax_status = _resolve_tax_status(
                strategy=strategy,
                acquisition_timestamp=current_lot.buy_timestamp,
                disposal_timestamp=event.timestamp,
            )

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


def build_open_lot_aging_snapshot(
    raw_events: list[dict[str, Any]],
    as_of: datetime,
    ruleset_id: str = "DE-2026-v1.0",
    ruleset_version: str | None = None,
) -> dict[str, Any]:
    spot_events, _ = _to_spot_events(raw_events)
    registry = build_default_registry()
    strategy = registry.build_strategy(ruleset_id=ruleset_id, ruleset_version=ruleset_version)
    lots_by_asset: dict[str, deque[Lot]] = defaultdict(deque)

    for event in spot_events:
        if event.timestamp > as_of:
            continue

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
        while qty_to_sell > Decimal("0") and lots_by_asset[event.asset]:
            current_lot = lots_by_asset[event.asset][0]
            matched_qty = min(qty_to_sell, current_lot.remaining_qty)
            current_lot.remaining_qty -= matched_qty
            qty_to_sell -= matched_qty
            if current_lot.remaining_qty <= Decimal("0"):
                lots_by_asset[event.asset].popleft()

    assets: list[dict[str, Any]] = []
    lot_rows: list[dict[str, Any]] = []
    for asset, lots in sorted(lots_by_asset.items(), key=lambda item: item[0]):
        if not lots:
            continue
        total_qty = Decimal("0")
        qty_exempt = Decimal("0")
        qty_taxable = Decimal("0")
        for lot in lots:
            qty = lot.remaining_qty
            if qty <= Decimal("0"):
                continue
            hold_days = (as_of.date() - lot.buy_timestamp.date()).days
            tax_status = _resolve_tax_status(
                strategy=strategy,
                acquisition_timestamp=lot.buy_timestamp,
                disposal_timestamp=as_of,
            )
            total_qty += qty
            if tax_status == "exempt":
                qty_exempt += qty
            else:
                qty_taxable += qty
            lot_rows.append(
                {
                    "asset": asset,
                    "qty": qty.to_eng_string(),
                    "buy_timestamp_utc": lot.buy_timestamp.isoformat(),
                    "hold_days": hold_days,
                    "tax_status": tax_status,
                    "source_event_id": lot.source_event_id,
                }
            )

        if total_qty > Decimal("0"):
            assets.append(
                {
                    "asset": asset,
                    "total_qty": total_qty.to_eng_string(),
                    "qty_exempt": qty_exempt.to_eng_string(),
                    "qty_taxable": qty_taxable.to_eng_string(),
                }
            )

    lot_rows.sort(key=lambda row: (str(row["asset"]), -int(row["hold_days"])))
    return {
        "as_of_utc": as_of.isoformat(),
        "asset_count": len(assets),
        "lot_count": len(lot_rows),
        "assets": assets,
        "lot_rows": lot_rows,
    }
