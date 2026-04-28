from __future__ import annotations

from decimal import Decimal

from tax_engine.core.reconciliation import auto_match_transfers, extract_transfer_events


def test_extract_transfer_events_and_auto_match_with_time_window_and_fee_tolerance() -> None:
    raw_events = [
        {
            "unique_event_id": "out-1",
            "payload": {
                "timestamp": "2026-01-01T12:00:00+00:00",
                "asset": "SOL",
                "event_type": "withdrawal",
                "amount": "-10",
            },
        },
        {
            "unique_event_id": "in-1",
            "payload": {
                "timestamp": "2026-01-01T12:05:00+00:00",
                "symbol": "SOL",
                "event_type": "deposit",
                "amount": "9.99",
            },
        },
        {
            "unique_event_id": "in-used",
            "payload": {
                "timestamp": "2026-01-01T12:04:00+00:00",
                "symbol": "SOL",
                "event_type": "deposit",
                "amount": "10",
            },
        },
        {
            "unique_event_id": "out-unmatched",
            "payload": {
                "timestamp": "2026-01-02T12:00:00+00:00",
                "coin": "BTC",
                "type": "send",
                "qty": "0.1",
            },
        },
        {
            "unique_event_id": "ignored-trade",
            "payload": {
                "timestamp": "2026-01-02T13:00:00+00:00",
                "asset": "BTC",
                "event_type": "trade",
                "amount": "0.1",
            },
        },
    ]

    transfer_events = extract_transfer_events(raw_events)
    result = auto_match_transfers(
        transfer_events=transfer_events,
        matched_event_ids={"in-used"},
        time_window_seconds=600,
        amount_tolerance_ratio=Decimal("0.02"),
        min_confidence=Decimal("0.75"),
    )

    assert [event.unique_event_id for event in transfer_events] == [
        "out-1",
        "in-used",
        "in-1",
        "out-unmatched",
    ]
    assert len(result["matches"]) == 1
    assert result["matches"][0]["outbound_event_id"] == "out-1"
    assert result["matches"][0]["inbound_event_id"] == "in-1"
    assert result["matches"][0]["time_diff_seconds"] == 300
    assert result["matches"][0]["amount_diff"] == "0.01"
    assert result["unmatched_outbound_ids"] == ["out-unmatched"]
    assert result["unmatched_inbound_ids"] == []
