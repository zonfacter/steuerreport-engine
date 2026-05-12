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


def test_derivatives_manager_reads_timestamp_utc_payloads() -> None:
    raw_events = [
        {
            "unique_event_id": "open-utc",
            "payload": {
                "timestamp_utc": "2026-01-10T00:00:00+00:00",
                "position_id": "p1",
                "asset": "BTC",
                "event_type": "derivative_open",
                "collateral_eur": "100",
            },
        },
        {
            "unique_event_id": "close-utc",
            "payload": {
                "timestamp_utc": "2026-01-11T00:00:00+00:00",
                "position_id": "p1",
                "asset": "BTC",
                "event_type": "derivative close",
                "proceeds_eur": "125",
            },
        },
    ]

    result = process_derivatives_for_year(raw_events=raw_events, tax_year=2026)

    assert result["processed_events"] == 2
    assert len(result["lines"]) == 1
    assert result["lines"][0]["gain_loss_eur"] == "25"


def test_derivatives_manager_maps_bitget_futures_cash_settlements() -> None:
    raw_events = [
        {
            "unique_event_id": "open-fee",
            "payload": {
                "timestamp_utc": "2025-01-29T06:03:58.547000+00:00",
                "source": "bitget_tax_api",
                "asset": "USDT",
                "event_type": "derivative open_short",
                "quantity": "0",
                "fee": "0.31065774",
                "fee_asset": "USDT",
                "side": "in",
                "tx_id": "1268377317784846369",
                "raw_row": {
                    "amount": "0",
                    "businessType": "open_short",
                    "fee": "-0.31065774",
                    "symbol": "JUPUSDT",
                },
            },
        },
        {
            "unique_event_id": "close-loss",
            "payload": {
                "timestamp_utc": "2025-01-29T06:05:56.518000+00:00",
                "source": "bitget_tax_api",
                "asset": "USDT",
                "event_type": "derivative close_short",
                "quantity": "5.67",
                "fee": "1.3504725",
                "fee_asset": "USDT",
                "side": "out",
                "tx_id": "1268377812591083525",
                "raw_row": {
                    "amount": "-5.67",
                    "businessType": "close_short",
                    "fee": "-1.3504725",
                    "symbol": "JUPUSDT",
                },
            },
        },
        {
            "unique_event_id": "funding-profit",
            "payload": {
                "timestamp_utc": "2025-01-29T16:00:08.581000+00:00",
                "source": "bitget_tax_api",
                "asset": "USDT",
                "event_type": "derivative fee",
                "quantity": "0.1806317",
                "fee": "0",
                "side": "in",
                "tx_id": "1268527348181532705",
                "raw_row": {
                    "amount": "0.1806317",
                    "businessType": "contract_settle_fee",
                    "fee": "0",
                    "symbol": "JUPUSDT",
                },
            },
        },
    ]

    result = process_derivatives_for_year(raw_events=raw_events, tax_year=2025)

    assert result["processed_events"] == 3
    assert result["standalone_cash_settlements"] == 3
    assert result["open_positions_remaining"] == 0
    assert [line["event_type"] for line in result["lines"]] == ["fee", "close", "fee"]
    assert [line["gain_loss_eur"] for line in result["lines"]] == ["-0.31065774", "-7.0204725", "0.1806317"]
    assert result["derivative_gain_loss_total_eur"] == "-7.15049854"
