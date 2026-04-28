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


def test_solana_swap_transfers_are_classified_as_spot() -> None:
    raw_events = [
        {
            "unique_event_id": "swap-out-1",
            "payload": {
                "timestamp_utc": "2026-02-01T00:00:00+00:00",
                "asset": "SOL",
                "event_type": "token_transfer",
                "defi_label": "swap",
                "side": "out",
                "quantity": "1",
                "price_eur": "120",
            },
        },
        {
            "unique_event_id": "swap-in-1",
            "payload": {
                "timestamp_utc": "2026-01-01T00:00:00+00:00",
                "asset": "SOL",
                "event_type": "token_transfer",
                "defi_label": "swap",
                "side": "in",
                "quantity": "2",
                "price_eur": "100",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2026)

    assert result["class_counts"]["spot"] == 2
    assert result["processed_events"] == 2
    assert result["tax_line_count"] == 1
    assert result["tax_lines"][0]["asset"] == "SOL"


def test_stable_asset_events_convert_usd_to_eur_without_explicit_price_eur() -> None:
    raw_events = [
        {
            "unique_event_id": "usdt-buy",
            "payload": {
                "timestamp_utc": "2026-01-10T12:00:00Z",
                "asset": "USDT",
                "side": "buy",
                "amount": "558.64384",
                "fx_rate_usd_eur": "0.90",
                "fee_eur": "0",
            },
        },
        {
            "unique_event_id": "usdt-sell",
            "payload": {
                "timestamp": "2026-06-10T12:00:00+00:00",
                "asset": "USDT",
                "side": "sell",
                "amount": "200",
                "fx_rate_usd_eur": "0.95",
                "fee_eur": "0",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2026)
    tax_lines = result["tax_lines"]

    assert result["tax_line_count"] == 1
    assert result["tax_lines"][0]["asset"] == "USDT"
    assert tax_lines[0]["qty"] == "200"
    assert tax_lines[0]["cost_basis_eur"] == "180.00"
    assert tax_lines[0]["proceeds_eur"] == "190.00"
    assert tax_lines[0]["gain_loss_eur"] == "10.00"
