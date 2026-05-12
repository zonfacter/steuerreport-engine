from __future__ import annotations

import calendar
from collections import defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from tax_engine.connectors.token_metadata import resolve_token_metadata
from tax_engine.core.tax_domains import _is_business_override, _is_reward_like
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
    event_class: str
    domain: str


@dataclass(slots=True)
class Lot:
    buy_timestamp: datetime
    remaining_qty: Decimal
    unit_cost_eur: Decimal
    source_event_id: str
    domain: str


@dataclass(slots=True)
class TransferLotFragment:
    buy_timestamp: datetime
    qty: Decimal
    unit_cost_eur: Decimal
    source_event_id: str
    domain: str


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


def _canonical_asset(value: Any) -> str:
    normalized = str(value or "").upper().strip()
    if not normalized:
        return ""
    metadata = resolve_token_metadata(normalized)
    return str(metadata.get("symbol") or normalized).upper().strip()


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
    raw_asset = str(payload.get("asset") or payload.get("symbol") or "").upper().strip()
    base_asset = str(payload.get("base_asset") or "").upper().strip()
    quote_asset = str(payload.get("quote_asset") or "").upper().strip()
    source = str(payload.get("source") or "").lower().strip()
    event_type = str(payload.get("event_type") or "").lower().strip()
    side = str(payload.get("side") or "").lower().strip()
    if base_asset and quote_asset and raw_asset:
        pair_symbols = {
            f"{base_asset}{quote_asset}",
            f"{base_asset}-{quote_asset}",
            f"{base_asset}/{quote_asset}",
            f"{base_asset}_{quote_asset}",
        }
        if raw_asset in pair_symbols or (
            source.endswith("_api") and event_type in {"trade", "spot_trade", "order"} and side in {"buy", "sell"}
        ):
            return _canonical_asset(base_asset)
    for key in ("asset", "symbol", "base_asset", "coin"):
        value = payload.get(key)
        if value:
            return _canonical_asset(value)
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
        ("HNT Token", "HNT Tokens"),
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
        if raw > Decimal("0"):
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
    normalized = _canonical_asset(asset)
    if normalized == "EUR":
        return Decimal("1")
    if normalized in STABLE_ASSETS:
        return _extract_event_fx_rate(payload)
    return Decimal("0")


def _infer_unit_price_eur(payload: dict[str, Any], asset: str, qty: Decimal, base_price: Decimal) -> Decimal:
    asset_norm = _canonical_asset(asset)
    direct_rate = _stable_to_eur_rate(asset_norm, payload)
    if direct_rate > 0:
        return direct_rate

    if base_price > 0:
        return base_price
    if qty <= 0:
        return Decimal("0")

    lookup = _normalize_payload_lookup(payload)
    incoming_asset = _canonical_asset(_lookup_value(lookup, ("incomingasset", "incoming_asset", "toasset", "to_asset", "buyasset")))
    outgoing_asset = _canonical_asset(_lookup_value(lookup, ("outgoingasset", "outgoing_asset", "fromasset", "from_asset", "sellasset")))
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
            return (usd_candidate * _extract_event_fx_rate(payload) / incoming_amount).copy_abs()

    if asset_norm == incoming_asset and incoming_amount > 0 and out_rate > 0 and outgoing_amount > 0:
        total_eur = outgoing_amount * out_rate
        return total_eur / incoming_amount
    if asset_norm == outgoing_asset and outgoing_amount > 0 and in_rate > 0 and incoming_amount > 0:
        total_eur = incoming_amount * in_rate
        return total_eur / outgoing_amount

    # fallback: berechne aus Event-Wert, wenn vorhanden
    eur_value = _lookup_decimal(lookup, ("valueeur", "amounteur", "incomeeur", "proceedseur"))
    if eur_value is not None and eur_value > 0:
        return eur_value / qty

    usd_value = _lookup_decimal(lookup, ("priceusd", "valueusd", "valueusdsum", "incomeusd", "proceedsusd"))
    if usd_value is not None and usd_value > 0 and _extract_event_fx_rate(payload) > 0:
        return (usd_value * _extract_event_fx_rate(payload)) / qty

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
    if _looks_like_binance_wallet_transfer(payload):
        return "transfer"

    if event_type in {"swap_in_aggregated", "swap_out_aggregated"}:
        return "spot"

    if event_type in {"fiat_balance_success_user_in", "fiat_balance_success_user_out"}:
        return "transfer"

    if event_type in {"fiat_payment_in", "fiat_payment_out"} and _extract_asset(payload) == "EUR":
        return "transfer"

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


def _looks_like_binance_wallet_transfer(payload: dict[str, Any]) -> bool:
    if str(payload.get("source") or "").strip().lower() != "binance":
        return False
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return False
    lookup = {str(key).lower().replace(" ", "_"): value for key, value in raw_row.items()}
    tx_id = str(payload.get("tx_id") or lookup.get("txid") or lookup.get("transaction_id") or "").strip()
    address = str(payload.get("address") or lookup.get("address") or lookup.get("wallet_address") or "").strip()
    network = str(payload.get("network") or lookup.get("network") or lookup.get("chain") or "").strip()
    status = str(lookup.get("status") or "").strip().lower()
    return bool(tx_id and address and network and (not status or "complete" in status))


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


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    max_day = calendar.monthrange(year, month)[1]
    day = min(value.day, max_day)
    return value.replace(year=year, month=month, day=day)


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


def _domain_for_event(payload: dict[str, Any], event_class: str) -> str:
    if _is_business_override(payload):
        return "business"
    if event_class == "reward" or _is_reward_like(payload):
        return "business"
    return "private"


def _transfer_links_by_event_id(transfer_matches: list[dict[str, Any]] | None) -> tuple[dict[str, str], set[str]]:
    outbound_to_inbound: dict[str, str] = {}
    linked_ids: set[str] = set()
    for match in transfer_matches or []:
        if str(match.get("status", "matched")).lower() not in {"matched", "approved"}:
            continue
        outbound = str(match.get("outbound_event_id") or "").strip()
        inbound = str(match.get("inbound_event_id") or "").strip()
        if not outbound or not inbound:
            continue
        outbound_to_inbound[outbound] = inbound
        linked_ids.add(outbound)
        linked_ids.add(inbound)
    return outbound_to_inbound, linked_ids


def _sort_spot_events_for_fifo(
    spot_events: list[SpotEvent],
    outbound_to_inbound: dict[str, str],
) -> None:
    timestamp_by_id = {event.unique_event_id: event.timestamp for event in spot_events}
    inbound_to_outbound = {inbound: outbound for outbound, inbound in outbound_to_inbound.items()}

    def sort_key(event: SpotEvent) -> tuple[datetime, int, datetime, str]:
        inbound_id = outbound_to_inbound.get(event.unique_event_id)
        if inbound_id:
            paired_timestamp = timestamp_by_id.get(inbound_id, event.timestamp)
            return min(event.timestamp, paired_timestamp), 0, event.timestamp, event.unique_event_id

        outbound_id = inbound_to_outbound.get(event.unique_event_id)
        if outbound_id:
            paired_timestamp = timestamp_by_id.get(outbound_id, event.timestamp)
            return min(event.timestamp, paired_timestamp), 1, event.timestamp, event.unique_event_id

        return event.timestamp, 0, event.timestamp, event.unique_event_id

    spot_events.sort(key=sort_key)


def _to_spot_events(
    raw_events: Iterable[dict[str, Any]],
    transfer_matches: list[dict[str, Any]] | None = None,
) -> tuple[list[SpotEvent], dict[str, int]]:
    spot_events: list[SpotEvent] = []
    outbound_to_inbound, linked_transfer_event_ids = _transfer_links_by_event_id(transfer_matches)
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
        asset = _extract_asset(payload)
        side = _extract_side(payload, _extract_qty(payload))
        is_stable_transfer = event_class == "transfer" and asset in (STABLE_ASSETS - {"EUR"})
        event_id = str(event["unique_event_id"])
        is_linked_transfer = event_class == "transfer" and event_id in linked_transfer_event_ids
        is_transfer_out = event_class == "transfer" and side == "sell"
        if event_class not in {"spot", "reward"} and not is_stable_transfer and not is_linked_transfer and not is_transfer_out:
            continue
        ts = _extract_timestamp(payload)
        if ts is None:
            continue
        qty = _extract_qty(payload)
        if qty <= 0:
            continue
        side = _extract_side(payload, qty)
        if event_class == "reward" and side != "buy":
            continue
        if event_class == "transfer" and side == "sell":
            side = "transfer_out"
        spot_events.append(
            SpotEvent(
                unique_event_id=event["unique_event_id"],
                timestamp=ts,
                asset=asset,
                side=side,
                qty=qty,
                unit_price_eur=_infer_unit_price_eur(
                    payload=payload,
                    asset=_extract_asset(payload),
                    qty=qty,
                    base_price=_extract_unit_price_eur(payload),
                ),
                fee_eur=_extract_fee_eur(payload),
                event_class=event_class,
                domain=_domain_for_event(payload, event_class),
            )
        )

    _sort_spot_events_for_fifo(spot_events, outbound_to_inbound)
    return spot_events, class_counts


def process_events_for_year(
    raw_events: list[dict[str, Any]],
    tax_year: int,
    ruleset_id: str = "DE-2026-v1.0",
    ruleset_version: str | None = None,
    transfer_matches: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    spot_events, class_counts = _to_spot_events(raw_events, transfer_matches=transfer_matches)
    outbound_to_inbound, _ = _transfer_links_by_event_id(transfer_matches)
    pending_transfer_lots_by_inbound: dict[str, deque[TransferLotFragment]] = defaultdict(deque)
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
            pending_fragments = pending_transfer_lots_by_inbound.get(event.unique_event_id)
            if event.event_class == "transfer" and pending_fragments:
                qty_left = event.qty
                while qty_left > Decimal("0") and pending_fragments:
                    fragment = pending_fragments[0]
                    matched_qty = min(qty_left, fragment.qty)
                    lots_by_asset[event.asset].append(
                        Lot(
                            buy_timestamp=fragment.buy_timestamp,
                            remaining_qty=matched_qty,
                            unit_cost_eur=fragment.unit_cost_eur,
                            source_event_id=fragment.source_event_id,
                            domain=fragment.domain,
                        )
                    )
                    fragment.qty -= matched_qty
                    qty_left -= matched_qty
                    if fragment.qty <= Decimal("0"):
                        pending_fragments.popleft()
                if qty_left <= Decimal("0"):
                    continue

            buy_qty = qty_left if event.event_class == "transfer" and pending_fragments else event.qty
            total_cost = (buy_qty * event.unit_price_eur) + event.fee_eur
            unit_cost = (total_cost / buy_qty) if buy_qty > 0 else Decimal("0")
            lots_by_asset[event.asset].append(
                Lot(
                    buy_timestamp=event.timestamp,
                    remaining_qty=buy_qty,
                    unit_cost_eur=unit_cost,
                    source_event_id=event.unique_event_id,
                    domain=event.domain,
                )
            )
            continue

        qty_to_sell = event.qty
        is_non_tax_transfer_out = event.side == "transfer_out"
        total_proceeds = Decimal("0") if is_non_tax_transfer_out else (event.qty * event.unit_price_eur) - event.fee_eur
        unit_proceeds = (total_proceeds / event.qty) if event.qty > 0 else Decimal("0")

        while qty_to_sell > Decimal("0"):
            if not lots_by_asset[event.asset]:
                fallback_qty = qty_to_sell
                if is_non_tax_transfer_out:
                    qty_to_sell = Decimal("0")
                    break
                short_sell_violations += 1
                if event.timestamp.year == tax_year and not is_non_tax_transfer_out:
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
                            "tax_domain": "private_veraeusserung",
                            "lot_domain": "private",
                            "source_event_id": event.unique_event_id,
                            "lot_source_event_id": "",
                            "transfer_chain_id": "",
                        }
                    )
                qty_to_sell = Decimal("0")
                break

            current_lot = lots_by_asset[event.asset][0]
            matched_qty = min(qty_to_sell, current_lot.remaining_qty)
            if is_non_tax_transfer_out:
                inbound_event_id = outbound_to_inbound.get(event.unique_event_id)
                if inbound_event_id:
                    pending_transfer_lots_by_inbound[inbound_event_id].append(
                        TransferLotFragment(
                            buy_timestamp=current_lot.buy_timestamp,
                            qty=matched_qty,
                            unit_cost_eur=current_lot.unit_cost_eur,
                            source_event_id=current_lot.source_event_id,
                            domain=current_lot.domain,
                        )
                    )
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
                if is_non_tax_transfer_out:
                    current_lot.remaining_qty -= matched_qty
                    qty_to_sell -= matched_qty
                    if current_lot.remaining_qty <= Decimal("0"):
                        lots_by_asset[event.asset].popleft()
                    continue
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
                        "tax_status": "business" if current_lot.domain == "business" else tax_status,
                        "tax_domain": "euer_business_disposal" if current_lot.domain == "business" else "private_veraeusserung",
                        "lot_domain": current_lot.domain,
                        "source_event_id": event.unique_event_id,
                        "lot_source_event_id": current_lot.source_event_id,
                        "transfer_chain_id": "",
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
    transfer_matches: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    spot_events, _ = _to_spot_events(raw_events, transfer_matches=transfer_matches)
    outbound_to_inbound, _ = _transfer_links_by_event_id(transfer_matches)
    pending_transfer_lots_by_inbound: dict[str, deque[TransferLotFragment]] = defaultdict(deque)
    registry = build_default_registry()
    strategy = registry.build_strategy(ruleset_id=ruleset_id, ruleset_version=ruleset_version)
    lots_by_asset: dict[str, deque[Lot]] = defaultdict(deque)

    for event in spot_events:
        if event.timestamp > as_of:
            continue

        if event.side == "buy":
            pending_fragments = pending_transfer_lots_by_inbound.get(event.unique_event_id)
            if event.event_class == "transfer" and pending_fragments:
                qty_left = event.qty
                while qty_left > Decimal("0") and pending_fragments:
                    fragment = pending_fragments[0]
                    matched_qty = min(qty_left, fragment.qty)
                    lots_by_asset[event.asset].append(
                        Lot(
                            buy_timestamp=fragment.buy_timestamp,
                            remaining_qty=matched_qty,
                            unit_cost_eur=fragment.unit_cost_eur,
                            source_event_id=fragment.source_event_id,
                            domain=fragment.domain,
                        )
                    )
                    fragment.qty -= matched_qty
                    qty_left -= matched_qty
                    if fragment.qty <= Decimal("0"):
                        pending_fragments.popleft()
                if qty_left <= Decimal("0"):
                    continue

            buy_qty = qty_left if event.event_class == "transfer" and pending_fragments else event.qty
            total_cost = (buy_qty * event.unit_price_eur) + event.fee_eur
            unit_cost = (total_cost / buy_qty) if buy_qty > 0 else Decimal("0")
            lots_by_asset[event.asset].append(
                Lot(
                    buy_timestamp=event.timestamp,
                    remaining_qty=buy_qty,
                    unit_cost_eur=unit_cost,
                    source_event_id=event.unique_event_id,
                    domain=event.domain,
                )
            )
            continue

        qty_to_sell = event.qty
        while qty_to_sell > Decimal("0") and lots_by_asset[event.asset]:
            current_lot = lots_by_asset[event.asset][0]
            matched_qty = min(qty_to_sell, current_lot.remaining_qty)
            if event.side == "transfer_out":
                inbound_event_id = outbound_to_inbound.get(event.unique_event_id)
                if inbound_event_id:
                    pending_transfer_lots_by_inbound[inbound_event_id].append(
                        TransferLotFragment(
                            buy_timestamp=current_lot.buy_timestamp,
                            qty=matched_qty,
                            unit_cost_eur=current_lot.unit_cost_eur,
                            source_event_id=current_lot.source_event_id,
                            domain=current_lot.domain,
                        )
                    )
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
        qty_business = Decimal("0")
        qty_private = Decimal("0")
        oldest_hold_days = 0
        lot_count = 0
        for lot in lots:
            qty = lot.remaining_qty
            if qty <= Decimal("0"):
                continue
            hold_days = (as_of.date() - lot.buy_timestamp.date()).days
            threshold_timestamp = _add_months(lot.buy_timestamp, strategy.ruleset.holding_period_months)
            total_required_days = max((threshold_timestamp.date() - lot.buy_timestamp.date()).days, 1)
            days_to_exempt = max((threshold_timestamp.date() - as_of.date()).days, 0)
            holding_progress_ratio = min(Decimal("1"), Decimal(max(hold_days, 0)) / Decimal(total_required_days))
            tax_status = _resolve_tax_status(
                strategy=strategy,
                acquisition_timestamp=lot.buy_timestamp,
                disposal_timestamp=as_of,
            )
            total_qty += qty
            oldest_hold_days = max(oldest_hold_days, hold_days)
            lot_count += 1
            if tax_status == "exempt":
                qty_exempt += qty
            else:
                qty_taxable += qty
            if lot.domain == "business":
                qty_business += qty
            else:
                qty_private += qty
            lot_rows.append(
                {
                    "asset": asset,
                    "qty": qty.to_eng_string(),
                    "domain": lot.domain,
                    "buy_timestamp_utc": lot.buy_timestamp.isoformat(),
                    "hold_days": hold_days,
                    "days_to_exempt": days_to_exempt,
                    "holding_progress_ratio": holding_progress_ratio.quantize(Decimal("0.0001")).to_eng_string(),
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
                    "lot_count": lot_count,
                    "oldest_hold_days": oldest_hold_days,
                    "qty_business": qty_business.to_eng_string(),
                    "qty_private": qty_private.to_eng_string(),
                }
            )

    private_assets: list[dict[str, Any]] = []
    private_lot_rows = [row for row in lot_rows if row.get("domain") == "private"]
    for asset, rows in sorted(
        ((asset, [row for row in private_lot_rows if str(row.get("asset")) == asset]) for asset in {str(row.get("asset")) for row in private_lot_rows}),
        key=lambda item: item[0],
    ):
        total_qty = sum((_parse_decimal(row.get("qty")) for row in rows), Decimal("0"))
        qty_exempt = sum((_parse_decimal(row.get("qty")) for row in rows if row.get("tax_status") == "exempt"), Decimal("0"))
        qty_taxable = total_qty - qty_exempt
        private_assets.append(
            {
                "asset": asset,
                "total_qty": total_qty.to_eng_string(),
                "qty_exempt": qty_exempt.to_eng_string(),
                "qty_taxable": qty_taxable.to_eng_string(),
                "lot_count": len(rows),
                "oldest_hold_days": max((int(row.get("hold_days", 0)) for row in rows), default=0),
            }
        )

    lot_rows.sort(key=lambda row: (str(row["asset"]), str(row.get("domain", "")), -int(row["hold_days"])))
    return {
        "as_of_utc": as_of.isoformat(),
        "asset_count": len(assets),
        "lot_count": len(lot_rows),
        "assets": assets,
        "lot_rows": lot_rows,
        "private_asset_count": len(private_assets),
        "private_lot_count": len(private_lot_rows),
        "private_assets": private_assets,
        "private_lot_rows": private_lot_rows,
    }
