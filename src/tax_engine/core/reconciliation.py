from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(slots=True)
class TransferEvent:
    unique_event_id: str
    timestamp: datetime
    asset: str
    amount: Decimal
    direction: str  # "out" | "in"


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
    for key in ("asset", "symbol", "coin", "base_asset"):
        value = payload.get(key)
        if value:
            return str(value).upper()
    return "UNKNOWN"


def _extract_amount(payload: dict[str, Any]) -> Decimal:
    for key in ("amount", "qty", "quantity", "size"):
        if key in payload:
            try:
                return _parse_decimal(payload.get(key))
            except InvalidOperation:
                return Decimal("0")
    return Decimal("0")


def _extract_direction(payload: dict[str, Any], amount: Decimal) -> str | None:
    text = " ".join(str(payload.get(k, "")).lower() for k in ("type", "event_type", "side", "tag"))
    if any(token in text for token in ("withdraw", "outbound", "send")):
        return "out"
    if any(token in text for token in ("deposit", "inbound", "receive")):
        return "in"
    if "transfer" in text:
        return "out" if amount < 0 else "in"
    return None


def extract_transfer_events(raw_events: list[dict[str, Any]]) -> list[TransferEvent]:
    transfer_events: list[TransferEvent] = []
    for event in raw_events:
        payload = event["payload"]
        amount = _extract_amount(payload)
        direction = _extract_direction(payload, amount)
        if direction is None:
            continue
        timestamp = _extract_timestamp(payload)
        if timestamp is None:
            continue
        transfer_events.append(
            TransferEvent(
                unique_event_id=event["unique_event_id"],
                timestamp=timestamp,
                asset=_extract_asset(payload),
                amount=abs(amount),
                direction=direction,
            )
        )
    transfer_events.sort(key=lambda item: item.timestamp)
    return transfer_events


def auto_match_transfers(
    transfer_events: list[TransferEvent],
    matched_event_ids: set[str],
    time_window_seconds: int,
    amount_tolerance_ratio: Decimal,
    min_confidence: Decimal,
) -> dict[str, Any]:
    out_events = [e for e in transfer_events if e.direction == "out" and e.unique_event_id not in matched_event_ids]
    in_events = [e for e in transfer_events if e.direction == "in" and e.unique_event_id not in matched_event_ids]
    used_in_ids: set[str] = set()
    matches: list[dict[str, Any]] = []
    unmatched_out_ids: list[str] = []

    for out_event in out_events:
        best: tuple[TransferEvent, Decimal, int, Decimal] | None = None
        for in_event in in_events:
            if in_event.unique_event_id in used_in_ids:
                continue
            if in_event.asset != out_event.asset:
                continue
            delta_seconds = int(abs((in_event.timestamp - out_event.timestamp).total_seconds()))
            if delta_seconds > time_window_seconds:
                continue
            max_amount = max(out_event.amount, in_event.amount, Decimal("1"))
            diff_amount = abs(out_event.amount - in_event.amount)
            if diff_amount > (max_amount * amount_tolerance_ratio):
                continue

            time_score = Decimal("1") - (Decimal(delta_seconds) / Decimal(time_window_seconds))
            amount_score = Decimal("1") - (diff_amount / max_amount)
            confidence = (amount_score * Decimal("0.6")) + (time_score * Decimal("0.4"))
            if best is None or confidence > best[1]:
                best = (in_event, confidence, delta_seconds, diff_amount)

        if best is None or best[1] < min_confidence:
            unmatched_out_ids.append(out_event.unique_event_id)
            continue

        in_event, confidence, delta_seconds, diff_amount = best
        used_in_ids.add(in_event.unique_event_id)
        matches.append(
            {
                "outbound_event_id": out_event.unique_event_id,
                "inbound_event_id": in_event.unique_event_id,
                "confidence_score": confidence.quantize(Decimal("0.0001")).to_eng_string(),
                "time_diff_seconds": delta_seconds,
                "amount_diff": diff_amount.to_eng_string(),
            }
        )

    unmatched_in_ids = [e.unique_event_id for e in in_events if e.unique_event_id not in used_in_ids]
    return {
        "matches": matches,
        "unmatched_outbound_ids": unmatched_out_ids,
        "unmatched_inbound_ids": unmatched_in_ids,
    }

