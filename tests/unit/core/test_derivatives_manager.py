from __future__ import annotations

from tax_engine.core.derivatives import process_derivatives_for_year


def test_derivatives_manager_handles_open_close_and_liquidation() -> None:
    raw_events = [
        {
            "unique_event_id": "open-1",
            "payload": {
                "timestamp": "2026-01-10T00:00:00+00:00",
                "position_id": "p1",
                "asset": "BTC",
                "event_type": "derivative_open",
                "collateral_eur": "1000",
                "fee_eur": "5",
                "funding_eur": "2",
            },
        },
        {
            "unique_event_id": "close-1",
            "payload": {
                "timestamp": "2026-01-20T00:00:00+00:00",
                "position_id": "p1",
                "asset": "BTC",
                "event_type": "close",
                "proceeds_eur": "1200",
                "fee_eur": "3",
                "funding_eur": "1",
            },
        },
        {
            "unique_event_id": "open-2",
            "payload": {
                "timestamp": "2026-02-01T00:00:00+00:00",
                "position_id": "p2",
                "asset": "ETH",
                "event_type": "open",
                "collateral_eur": "500",
                "fee_eur": "2",
            },
        },
        {
            "unique_event_id": "liq-2",
            "payload": {
                "timestamp": "2026-02-05T00:00:00+00:00",
                "position_id": "p2",
                "asset": "ETH",
                "event_type": "liquidation",
                "fee_eur": "1",
                "negative_equity_eur": "20",
            },
        },
    ]

    result = process_derivatives_for_year(raw_events=raw_events, tax_year=2026)

    assert result["processed_events"] == 4
    assert result["open_positions_remaining"] == 0
    assert result["unmatched_closes"] == 0
    assert result["derivative_gain_loss_total_eur"] == "-334"
    assert result["derivative_loss_bucket_total_eur"] == "523"
    assert len(result["lines"]) == 2
    assert result["lines"][0]["gain_loss_eur"] == "189"
    assert result["lines"][1]["event_type"] == "liquidation"
    assert result["lines"][1]["gain_loss_eur"] == "-523"

