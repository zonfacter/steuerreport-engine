from __future__ import annotations

from decimal import Decimal
from typing import Any

from tax_engine.core.reconciliation import auto_match_transfers, extract_transfer_events
from tax_engine.ingestion.store import STORE


def _matched_event_ids() -> set[str]:
    ids: set[str] = set()
    for match in STORE.list_transfer_matches():
        ids.add(match["outbound_event_id"])
        ids.add(match["inbound_event_id"])
    return ids


def auto_match_and_persist(
    time_window_seconds: int,
    amount_tolerance_ratio: float,
    min_confidence: float,
) -> dict[str, Any]:
    raw_events = STORE.list_raw_events()
    transfer_events = extract_transfer_events(raw_events)
    result = auto_match_transfers(
        transfer_events=transfer_events,
        matched_event_ids=_matched_event_ids(),
        time_window_seconds=time_window_seconds,
        amount_tolerance_ratio=Decimal(str(amount_tolerance_ratio)),
        min_confidence=Decimal(str(min_confidence)),
    )

    persisted_match_ids: list[str] = []
    for match in result["matches"]:
        persisted_match_ids.append(
            STORE.create_transfer_match(
                outbound_event_id=match["outbound_event_id"],
                inbound_event_id=match["inbound_event_id"],
                confidence_score=match["confidence_score"],
                time_diff_seconds=match["time_diff_seconds"],
                amount_diff=match["amount_diff"],
                status="matched",
                method="auto",
            )
        )

    return {
        "persisted_match_count": len(persisted_match_ids),
        "persisted_match_ids": persisted_match_ids,
        "matches": result["matches"],
        "unmatched_outbound_ids": result["unmatched_outbound_ids"],
        "unmatched_inbound_ids": result["unmatched_inbound_ids"],
    }


def list_unmatched_transfers(
    time_window_seconds: int,
    amount_tolerance_ratio: float,
    min_confidence: float,
) -> dict[str, Any]:
    raw_events = STORE.list_raw_events()
    transfer_events = extract_transfer_events(raw_events)
    result = auto_match_transfers(
        transfer_events=transfer_events,
        matched_event_ids=_matched_event_ids(),
        time_window_seconds=time_window_seconds,
        amount_tolerance_ratio=Decimal(str(amount_tolerance_ratio)),
        min_confidence=Decimal(str(min_confidence)),
    )
    return {
        "unmatched_outbound_ids": result["unmatched_outbound_ids"],
        "unmatched_inbound_ids": result["unmatched_inbound_ids"],
        "candidate_auto_matches": result["matches"],
    }


def manual_match(outbound_event_id: str, inbound_event_id: str, note: str | None) -> dict[str, Any]:
    raw_event_ids = {event["unique_event_id"] for event in STORE.list_raw_events()}
    if outbound_event_id not in raw_event_ids or inbound_event_id not in raw_event_ids:
        return {"ok": False, "error": "event_not_found"}

    match_id = STORE.create_transfer_match(
        outbound_event_id=outbound_event_id,
        inbound_event_id=inbound_event_id,
        confidence_score="1.0000",
        time_diff_seconds=0,
        amount_diff="0",
        status="matched",
        method="manual",
        note=note,
    )
    return {"ok": True, "match_id": match_id}

