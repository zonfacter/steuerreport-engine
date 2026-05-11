from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class DerivativePosition:
    position_id: str
    asset: str
    open_timestamp: datetime
    collateral_eur: Decimal
    fees_eur: Decimal
    funding_eur: Decimal
    source_event_id: str


def _parse_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip().replace(",", "")
    if not text:
        return Decimal("0")
    return Decimal(text)


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


def _extract_position_id(payload: dict[str, Any], unique_event_id: str) -> str:
    explicit = _explicit_position_id(payload)
    if explicit:
        return explicit
    tx_id = payload.get("tx_id")
    if tx_id:
        return str(tx_id)
    return f"fallback-{unique_event_id}"


def _explicit_position_id(payload: dict[str, Any]) -> str:
    for key in ("position_id", "trade_id", "order_id"):
        value = payload.get(key)
        if value:
            return str(value)
    return ""


def _event_type(payload: dict[str, Any]) -> str:
    raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    text = " ".join(
        str(value).lower()
        for value in (
            payload.get("type", ""),
            payload.get("event_type", ""),
            payload.get("side", ""),
            payload.get("tag", ""),
            raw_row.get("businessType", ""),
            raw_row.get("spotTaxType", ""),
            raw_row.get("type", ""),
        )
    )
    if "liquidat" in text or "burst" in text:
        return "liquidation"
    if "grant" in text or "user_grants" in text:
        return "unknown"
    if any(token in text for token in ("fee", "funding", "settle")):
        return "fee"
    if any(token in text for token in ("close", "realize", "pnl", "profit", "loss")):
        return "close"
    if any(token in text for token in ("open", "entry", "margin", "future", "perp", "derivative")):
        return "open"
    return "unknown"


def _signed_quantity(payload: dict[str, Any]) -> Decimal:
    raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    if "amount" in raw_row:
        return _parse_decimal(raw_row.get("amount"))
    amount = _parse_decimal(payload.get("quantity", payload.get("amount", 0)))
    side = str(payload.get("side", "")).lower()
    if side in {"out", "sell", "close"}:
        return -abs(amount)
    return abs(amount)


def _signed_fee(payload: dict[str, Any]) -> Decimal:
    raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    if "fee" in raw_row:
        return _parse_decimal(raw_row.get("fee"))
    fee = _parse_decimal(payload.get("fee_eur", payload.get("fees_eur", payload.get("fee", 0))))
    side = str(payload.get("side", "")).lower()
    if side in {"in", "buy"}:
        return fee
    return -abs(fee)


def _is_bitget_tax_derivative_cash_event(payload: dict[str, Any], ev_type: str) -> bool:
    if str(payload.get("source", "")).lower() != "bitget_tax_api":
        return False
    event_type = str(payload.get("event_type", "")).lower()
    if "derivative" not in event_type:
        return False
    if ev_type in {"close", "fee", "liquidation"}:
        return True
    raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    return ev_type == "open" and _parse_decimal(raw_row.get("amount", payload.get("quantity", 0))) == Decimal("0")


def _build_standalone_cash_line(
    *,
    event: dict[str, Any],
    payload: dict[str, Any],
    ts: datetime,
    ev_type: str,
) -> dict[str, str]:
    position_id = _extract_position_id(payload, event["unique_event_id"])
    gross_amount = _signed_quantity(payload)
    signed_fee = _signed_fee(payload)
    fee_abs = abs(signed_fee)
    if ev_type == "open":
        event_type = "fee"
        proceeds = gross_amount
        gain_loss = gross_amount + signed_fee
    elif ev_type == "fee":
        event_type = "fee"
        proceeds = gross_amount
        fee_abs = Decimal("0") if gross_amount != Decimal("0") else fee_abs
        gain_loss = gross_amount if gross_amount != Decimal("0") else signed_fee
    else:
        event_type = ev_type
        proceeds = gross_amount
        gain_loss = gross_amount + signed_fee
    return {
        "position_id": position_id,
        "asset": _extract_asset(payload),
        "event_type": event_type,
        "open_timestamp_utc": ts.isoformat(),
        "close_timestamp_utc": ts.isoformat(),
        "collateral_eur": "0",
        "proceeds_eur": proceeds.to_eng_string(),
        "fees_eur": fee_abs.to_eng_string(),
        "funding_eur": "0",
        "gain_loss_eur": gain_loss.to_eng_string(),
        "loss_bucket": "termingeschaefte",
        "source_event_id": event["unique_event_id"],
    }


def process_derivatives_for_year(raw_events: list[dict[str, Any]], tax_year: int) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for event in raw_events:
        payload = event["payload"]
        ts = _extract_timestamp(payload)
        if ts is None or ts.year != tax_year:
            continue
        ev_type = _event_type(payload)
        if ev_type == "unknown":
            continue
        events.append({"unique_event_id": event["unique_event_id"], "payload": payload, "timestamp": ts, "ev_type": ev_type})

    events.sort(key=lambda item: item["timestamp"])
    open_positions: dict[str, DerivativePosition] = {}
    lines: list[dict[str, str]] = []
    unmatched_closes = 0
    total_gain_loss = Decimal("0")
    total_negative_losses = Decimal("0")
    standalone_cash_settlements = 0

    for event in events:
        payload = event["payload"]
        position_id = _extract_position_id(payload, event["unique_event_id"])
        asset = _extract_asset(payload)
        ts = event["timestamp"]
        if not _explicit_position_id(payload) and _is_bitget_tax_derivative_cash_event(payload, event["ev_type"]):
            line = _build_standalone_cash_line(event=event, payload=payload, ts=ts, ev_type=event["ev_type"])
            gain_loss = _parse_decimal(line["gain_loss_eur"])
            total_gain_loss += gain_loss
            if gain_loss < 0:
                total_negative_losses += abs(gain_loss)
            standalone_cash_settlements += 1
            lines.append(line)
            continue

        collateral = abs(_parse_decimal(payload.get("collateral_eur", payload.get("margin_eur", 0))))
        fees = abs(_parse_decimal(payload.get("fee_eur", payload.get("fees_eur", 0))))
        funding = abs(_parse_decimal(payload.get("funding_eur", 0)))
        proceeds = _parse_decimal(payload.get("proceeds_eur", payload.get("close_value_eur", payload.get("pnl_eur", 0))))
        extra_loss = abs(_parse_decimal(payload.get("negative_equity_eur", 0)))

        if event["ev_type"] == "fee":
            gain_loss = -fees - funding
            total_gain_loss += gain_loss
            if gain_loss < 0:
                total_negative_losses += abs(gain_loss)
            lines.append(
                {
                    "position_id": position_id,
                    "asset": asset,
                    "event_type": "fee",
                    "open_timestamp_utc": ts.isoformat(),
                    "close_timestamp_utc": ts.isoformat(),
                    "collateral_eur": "0",
                    "proceeds_eur": "0",
                    "fees_eur": fees.to_eng_string(),
                    "funding_eur": funding.to_eng_string(),
                    "gain_loss_eur": gain_loss.to_eng_string(),
                    "loss_bucket": "termingeschaefte",
                    "source_event_id": event["unique_event_id"],
                }
            )
            continue

        if event["ev_type"] == "open":
            open_positions[position_id] = DerivativePosition(
                position_id=position_id,
                asset=asset,
                open_timestamp=ts,
                collateral_eur=collateral,
                fees_eur=fees,
                funding_eur=funding,
                source_event_id=event["unique_event_id"],
            )
            continue

        base = open_positions.pop(
            position_id,
            DerivativePosition(
                position_id=position_id,
                asset=asset,
                open_timestamp=ts,
                collateral_eur=Decimal("0"),
                fees_eur=Decimal("0"),
                funding_eur=Decimal("0"),
                source_event_id=event["unique_event_id"],
            ),
        )
        if base.collateral_eur == Decimal("0") and event["ev_type"] != "liquidation":
            unmatched_closes += 1

        final_proceeds = Decimal("0") if event["ev_type"] == "liquidation" else proceeds
        total_fees = base.fees_eur + fees
        total_funding = base.funding_eur + funding
        gain_loss = final_proceeds - base.collateral_eur - total_fees - total_funding - extra_loss
        total_gain_loss += gain_loss
        if gain_loss < 0:
            total_negative_losses += abs(gain_loss)

        lines.append(
            {
                "position_id": position_id,
                "asset": base.asset,
                "event_type": event["ev_type"],
                "open_timestamp_utc": base.open_timestamp.isoformat(),
                "close_timestamp_utc": ts.isoformat(),
                "collateral_eur": base.collateral_eur.to_eng_string(),
                "proceeds_eur": final_proceeds.to_eng_string(),
                "fees_eur": total_fees.to_eng_string(),
                "funding_eur": total_funding.to_eng_string(),
                "gain_loss_eur": gain_loss.to_eng_string(),
                "loss_bucket": "termingeschaefte",
                "source_event_id": event["unique_event_id"],
            }
        )

    return {
        "processed_events": len(events),
        "open_positions_remaining": len(open_positions),
        "unmatched_closes": unmatched_closes,
        "standalone_cash_settlements": standalone_cash_settlements,
        "derivative_gain_loss_total_eur": total_gain_loss.to_eng_string(),
        "derivative_loss_bucket_total_eur": total_negative_losses.to_eng_string(),
        "lines": lines,
    }
