from __future__ import annotations

from decimal import Decimal

from tax_engine.core.reconciliation import auto_match_transfers, extract_transfer_events


def test_auto_match_transfers_matches_within_window_and_tolerance() -> None:
    raw_events = [
        {
            "unique_event_id": "w1",
            "payload": {
                "timestamp": "2026-01-01T12:00:00+00:00",
                "asset": "SOL",
                "event_type": "withdrawal",
                "amount": "10.00",
            },
        },
        {
            "unique_event_id": "d1",
            "payload": {
                "timestamp": "2026-01-01T12:03:00+00:00",
                "asset": "SOL",
                "event_type": "deposit",
                "amount": "9.99",
            },
        },
    ]
    transfers = extract_transfer_events(raw_events)
    result = auto_match_transfers(
        transfer_events=transfers,
        matched_event_ids=set(),
        time_window_seconds=600,
        amount_tolerance_ratio=Decimal("0.02"),
        min_confidence=Decimal("0.70"),
    )

    assert len(result["matches"]) == 1
    assert result["matches"][0]["outbound_event_id"] == "w1"
    assert result["matches"][0]["inbound_event_id"] == "d1"
    assert result["unmatched_outbound_ids"] == []
    assert result["unmatched_inbound_ids"] == []

