from __future__ import annotations

from tax_engine.core.processor import process_events_for_year


def test_fifo_generates_split_tax_lines_with_hold_period_and_fees() -> None:
    raw_events = [
        {
            "unique_event_id": "buy-1",
            "payload": {
                "timestamp": "2025-01-01T00:00:00+00:00",
                "asset": "BTC",
                "side": "buy",
                "amount": "1",
                "price_eur": "100",
                "fee_eur": "1",
            },
        },
        {
            "unique_event_id": "buy-2",
            "payload": {
                "timestamp": "2026-01-01T00:00:00+00:00",
                "asset": "BTC",
                "side": "buy",
                "amount": "1",
                "price_eur": "200",
                "fee_eur": "1",
            },
        },
        {
            "unique_event_id": "sell-1",
            "payload": {
                "timestamp": "2026-06-01T00:00:00+00:00",
                "asset": "BTC",
                "side": "sell",
                "amount": "1.5",
                "price_eur": "300",
                "fee_eur": "3",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2026)
    tax_lines = result["tax_lines"]

    assert result["processed_events"] == 3
    assert result["short_sell_violations"] == 0
    assert result["inventory_end"]["BTC"] == "0.5"
    assert result["tax_line_count"] == 2

    assert tax_lines[0]["qty"] == "1"
    assert tax_lines[0]["cost_basis_eur"] == "101"
    assert tax_lines[0]["proceeds_eur"] == "298"
    assert tax_lines[0]["gain_loss_eur"] == "197"
    assert tax_lines[0]["tax_status"] == "exempt"

    assert tax_lines[1]["qty"] == "0.5"
    assert tax_lines[1]["cost_basis_eur"] == "100.5"
    assert tax_lines[1]["proceeds_eur"] == "149.0"
    assert tax_lines[1]["gain_loss_eur"] == "48.5"
    assert tax_lines[1]["tax_status"] == "taxable"


def test_fifo_flags_short_sell_and_creates_fallback_tax_line() -> None:
    raw_events = [
        {
            "unique_event_id": "sell-first",
            "payload": {
                "timestamp": "2026-03-01T00:00:00+00:00",
                "asset": "SOL",
                "side": "sell",
                "amount": "2",
                "price_eur": "50",
                "fee_eur": "0",
            },
        }
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2026)
    tax_lines = result["tax_lines"]

    assert result["short_sell_violations"] == 1
    assert result["tax_line_count"] == 1
    assert tax_lines[0]["asset"] == "SOL"
    assert tax_lines[0]["cost_basis_eur"] == "0"
    assert tax_lines[0]["proceeds_eur"] == "100"

