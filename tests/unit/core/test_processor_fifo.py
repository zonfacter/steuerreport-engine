from __future__ import annotations

from tax_engine.core.processor import build_open_lot_aging_snapshot, process_events_for_year


def test_binance_wallet_deposit_shape_is_transfer_not_acquisition() -> None:
    raw_events = [
        {
            "unique_event_id": "deposit-1",
            "payload": {
                "timestamp_utc": "2025-06-15T09:47:02+00:00",
                "source": "binance",
                "asset": "SOL",
                "quantity": "7.0700475",
                "side": "in",
                "event_type": "",
                "tx_id": "sol-deposit-tx",
                "network": "SOL",
                "address": "EnbD7GwdYtWgPv5ReEKgCVpExuZsFxiYqjeEM4SgEvhn",
                "raw_row": {
                    "Address": "EnbD7GwdYtWgPv5ReEKgCVpExuZsFxiYqjeEM4SgEvhn",
                    "Amount": "7.0700475",
                    "Coin": "SOL",
                    "Network": "SOL",
                    "Status": "Completed",
                    "TXID": "sol-deposit-tx",
                },
            },
        }
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2025)

    assert result["class_counts"]["transfer"] == 1
    assert result["class_counts"]["spot"] == 0
    assert result["inventory_end"] == {}


def test_pionex_stable_quote_price_eur_creates_nonzero_hnt_lot_basis() -> None:
    raw_events = [
        {
            "unique_event_id": "pionex-hnt-buy",
            "payload": {
                "timestamp_utc": "2022-09-20T00:01:52+00:00",
                "source": "pionex",
                "asset": "HNT",
                "event_type": "trade",
                "side": "in",
                "quantity": "10",
                "price": "4.91690625",
                "price_eur": "4.425215625",
                "raw_row": {"symbol": "HNT_USDT", "price": "4.91690625"},
            },
        },
        {
            "unique_event_id": "pionex-hnt-sell",
            "payload": {
                "timestamp_utc": "2023-04-26T14:42:15+00:00",
                "source": "pionex",
                "asset": "HNT",
                "event_type": "trade",
                "side": "out",
                "quantity": "10",
                "price_eur": "1.68",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2023)

    assert result["short_sell_violations"] == 0
    assert result["tax_lines"][0]["lot_source_event_id"] == "pionex-hnt-buy"
    assert result["tax_lines"][0]["cost_basis_eur"] == "44.252156250"


def test_stable_asset_ignores_pair_market_price_for_unit_basis() -> None:
    raw_events = [
        {
            "unique_event_id": "usdt-in-from-btc-sell",
            "payload": {
                "timestamp_utc": "2021-04-26T20:11:31+00:00",
                "source": "binance",
                "asset": "USDT",
                "event_type": "trade",
                "side": "in",
                "quantity": "263.53351",
                "price": "15.11",
                "price_eur": "13.70",
                "fx_rate_usd_eur": "0.9",
                "raw_row": {"Market": "HNTUSDT", "Price": "15.11", "Total": "263.53351"},
            },
        },
        {
            "unique_event_id": "usdt-out-for-btc-buy",
            "payload": {
                "timestamp_utc": "2021-04-27T04:44:01+00:00",
                "source": "binance",
                "asset": "USDT",
                "event_type": "trade",
                "side": "out",
                "quantity": "100",
                "price": "53421.18",
                "price_eur": "48400",
                "fx_rate_usd_eur": "0.9",
                "raw_row": {"Market": "BTCUSDT", "Price": "53421.18", "Total": "100"},
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2021)

    assert result["tax_lines"][0]["asset"] == "USDT"
    assert result["tax_lines"][0]["cost_basis_eur"] == "90.0"
    assert result["tax_lines"][0]["proceeds_eur"] == "90.0"


def test_stablecoin_transfer_in_creates_fifo_lot_cost_basis() -> None:
    raw_events = [
        {
            "unique_event_id": "usdc-deposit",
            "payload": {
                "timestamp_utc": "2024-12-01T13:12:52+00:00",
                "source": "bitget_tax_api",
                "asset": "USDC",
                "event_type": "deposit",
                "side": "in",
                "quantity": "500",
                "fx_rate_usd_eur": "0.95",
            },
        },
        {
            "unique_event_id": "usdc-trade",
            "payload": {
                "timestamp_utc": "2024-12-01T13:28:04+00:00",
                "source": "bitget_tax_api",
                "asset": "USDC",
                "event_type": "trade",
                "side": "out",
                "quantity": "500",
                "value_eur": "480",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2024)

    assert result["class_counts"]["transfer"] == 1
    assert result["short_sell_violations"] == 0
    assert result["tax_lines"][0]["cost_basis_eur"] == "475.00"
    assert result["tax_lines"][0]["gain_loss_eur"] == "5.00"
    assert result["tax_lines"][0]["lot_source_event_id"] == "usdc-deposit"


def test_stablecoin_transfer_out_consumes_lot_without_tax_line() -> None:
    raw_events = [
        {
            "unique_event_id": "usdc-in",
            "payload": {
                "timestamp_utc": "2024-12-01T10:00:00+00:00",
                "source": "solana_rpc",
                "asset": "USDC",
                "event_type": "token_transfer",
                "side": "in",
                "quantity": "1000",
                "fx_rate_usd_eur": "0.95",
            },
        },
        {
            "unique_event_id": "usdc-out-transfer",
            "payload": {
                "timestamp_utc": "2024-12-01T11:00:00+00:00",
                "source": "solana_rpc",
                "asset": "USDC",
                "event_type": "token_transfer",
                "side": "out",
                "quantity": "400",
                "fx_rate_usd_eur": "0.95",
            },
        },
        {
            "unique_event_id": "usdc-swap",
            "payload": {
                "timestamp_utc": "2024-12-01T12:00:00+00:00",
                "source": "solana_rpc",
                "asset": "USDC",
                "event_type": "swap_out_aggregated",
                "side": "out",
                "quantity": "600",
                "value_eur": "580",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2024)

    assert result["tax_line_count"] == 1
    assert result["inventory_end"] == {}
    assert result["tax_lines"][0]["source_event_id"] == "usdc-swap"


def test_unmatched_non_stable_transfer_out_consumes_inventory_without_tax_line() -> None:
    raw_events = [
        {
            "unique_event_id": "sol-buy",
            "payload": {
                "timestamp_utc": "2025-01-01T00:00:00+00:00",
                "asset": "SOL",
                "event_type": "trade",
                "side": "in",
                "quantity": "10",
                "price_eur": "100",
            },
        },
        {
            "unique_event_id": "sol-withdraw",
            "payload": {
                "timestamp_utc": "2025-02-01T00:00:00+00:00",
                "asset": "SOL",
                "event_type": "withdrawal",
                "side": "out",
                "quantity": "9",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2025)

    assert result["tax_lines"] == []
    assert result["inventory_end"]["SOL"] == "1"


def test_bitget_fiat_balance_success_user_in_is_internal_transfer_not_acquisition() -> None:
    raw_events = [
        {
            "unique_event_id": "bitget-internal-sol",
            "payload": {
                "timestamp_utc": "2025-04-24T07:06:45.651000+00:00",
                "source": "bitget_tax_api",
                "asset": "SOL",
                "event_type": "fiat_balance_success_user_in",
                "side": "in",
                "quantity": "15.1554",
            },
        }
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2025)

    assert result["class_counts"]["transfer"] == 1
    assert result["inventory_end"] == {}


def test_binance_fiat_payment_out_eur_is_not_taxable_disposal() -> None:
    raw_events = [
        {
            "unique_event_id": "binance-fiat-eur-out",
            "payload": {
                "timestamp_utc": "2025-12-19T07:11:38+00:00",
                "source": "binance_api",
                "asset": "EUR",
                "event_type": "fiat_payment_out",
                "side": "out",
                "quantity": "96",
            },
        },
        {
            "unique_event_id": "binance-fiat-sol-in",
            "payload": {
                "timestamp_utc": "2025-12-19T07:11:38+00:00",
                "source": "binance_api",
                "asset": "SOL",
                "event_type": "fiat_payment_in",
                "side": "in",
                "quantity": "0.89711941",
                "price": "107.00916615",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2025)

    assert result["tax_lines"] == []
    assert result["class_counts"]["transfer"] == 1
    assert result["class_counts"]["spot"] == 1
    assert result["inventory_end"]["SOL"] == "0.89711941"
    assert "EUR" not in result["inventory_end"]


def test_business_reward_disposal_is_marked_as_euer_domain() -> None:
    raw_events = [
        {
            "unique_event_id": "iot-reward",
            "payload": {
                "timestamp_utc": "2024-01-01T00:00:00+00:00",
                "source": "heliumgeek",
                "asset": "IOT",
                "event_type": "mining_reward",
                "side": "in",
                "quantity": "100",
                "price_eur": "0.001",
            },
        },
        {
            "unique_event_id": "iot-sell",
            "payload": {
                "timestamp_utc": "2024-06-01T00:00:00+00:00",
                "source": "solana_rpc",
                "asset": "IOT",
                "event_type": "swap_out_aggregated",
                "side": "out",
                "quantity": "40",
                "price_eur": "0.002",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2024)

    assert result["tax_lines"][0]["tax_status"] == "business"
    assert result["tax_lines"][0]["tax_domain"] == "euer_business_disposal"
    assert result["tax_lines"][0]["lot_domain"] == "business"


def test_transfer_match_carries_business_lot_domain_and_holding_period() -> None:
    raw_events = [
        {
            "unique_event_id": "hnt-reward",
            "payload": {
                "timestamp_utc": "2024-01-01T00:00:00+00:00",
                "source": "heliumgeek",
                "asset": "HNT",
                "event_type": "mining_reward",
                "side": "in",
                "quantity": "10",
                "price_eur": "5",
            },
        },
        {
            "unique_event_id": "hnt-withdraw",
            "payload": {
                "timestamp_utc": "2024-02-01T00:00:00+00:00",
                "source": "binance",
                "asset": "HNT",
                "event_type": "withdraw",
                "side": "out",
                "quantity": "10",
            },
        },
        {
            "unique_event_id": "hnt-deposit",
            "payload": {
                "timestamp_utc": "2024-02-01T00:30:00+00:00",
                "source": "bitget_tax_api",
                "asset": "HNT",
                "event_type": "deposit",
                "side": "in",
                "quantity": "10",
            },
        },
        {
            "unique_event_id": "hnt-sell",
            "payload": {
                "timestamp_utc": "2024-03-01T00:00:00+00:00",
                "source": "bitget_tax_api",
                "asset": "HNT",
                "event_type": "trade",
                "side": "out",
                "quantity": "10",
                "price_eur": "4",
            },
        },
    ]
    matches = [
        {
            "outbound_event_id": "hnt-withdraw",
            "inbound_event_id": "hnt-deposit",
            "status": "matched",
        }
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2024, transfer_matches=matches)

    assert result["short_sell_violations"] == 0
    assert result["tax_lines"][0]["buy_timestamp_utc"] == "2024-01-01T00:00:00+00:00"
    assert result["tax_lines"][0]["lot_source_event_id"] == "hnt-reward"
    assert result["tax_lines"][0]["tax_domain"] == "euer_business_disposal"


def test_transfer_match_carries_lot_basis_when_inbound_timestamp_is_slightly_earlier() -> None:
    raw_events = [
        {
            "unique_event_id": "hnt-buy-bitget",
            "payload": {
                "timestamp_utc": "2025-03-01T00:00:00+00:00",
                "source": "bitget_tax_api",
                "asset": "HNT",
                "event_type": "trade",
                "side": "in",
                "quantity": "10",
                "price_eur": "2",
            },
        },
        {
            "unique_event_id": "hnt-solana-in",
            "payload": {
                "timestamp_utc": "2025-03-09T18:59:51+00:00",
                "source": "solscan_wallet_discovery",
                "asset": "HNT",
                "event_type": "token_transfer",
                "side": "in",
                "quantity": "10",
            },
        },
        {
            "unique_event_id": "hnt-bitget-out",
            "payload": {
                "timestamp_utc": "2025-03-09T19:00:22+00:00",
                "source": "bitget_tax_api",
                "asset": "HNT",
                "event_type": "withdrawal",
                "side": "out",
                "quantity": "10",
            },
        },
        {
            "unique_event_id": "hnt-jupiter-sell",
            "payload": {
                "timestamp_utc": "2025-03-09T19:04:42+00:00",
                "source": "solana_rpc",
                "asset": "HNT",
                "event_type": "swap_out_aggregated",
                "side": "out",
                "quantity": "10",
                "price_eur": "3",
            },
        },
    ]
    matches = [
        {
            "outbound_event_id": "hnt-bitget-out",
            "inbound_event_id": "hnt-solana-in",
            "status": "matched",
        }
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2025, transfer_matches=matches)

    assert result["short_sell_violations"] == 0
    assert result["tax_lines"][0]["buy_timestamp_utc"] == "2025-03-01T00:00:00+00:00"
    assert result["tax_lines"][0]["cost_basis_eur"] == "20"
    assert result["tax_lines"][0]["proceeds_eur"] == "30"
    assert result["tax_lines"][0]["lot_source_event_id"] == "hnt-buy-bitget"


def test_lot_aging_private_rows_are_split_from_business_rows() -> None:
    from datetime import datetime

    raw_events = [
        {
            "unique_event_id": "sol-private",
            "payload": {
                "timestamp_utc": "2025-01-01T00:00:00+00:00",
                "asset": "SOL",
                "event_type": "trade",
                "side": "in",
                "quantity": "3",
                "price_eur": "100",
            },
        },
        {
            "unique_event_id": "sol-reward",
            "payload": {
                "timestamp_utc": "2025-02-01T00:00:00+00:00",
                "asset": "SOL",
                "event_type": "staking_reward",
                "side": "in",
                "quantity": "1",
                "price_eur": "120",
            },
        },
    ]

    snapshot = build_open_lot_aging_snapshot(
        raw_events=raw_events,
        as_of=datetime.fromisoformat("2026-03-01T00:00:00+00:00"),
    )

    assert {row["domain"] for row in snapshot["lot_rows"]} == {"private", "business"}
    assert snapshot["private_lot_count"] == 1
    assert snapshot["private_assets"][0]["asset"] == "SOL"
    assert snapshot["private_assets"][0]["total_qty"] == "3"


def test_raw_value_usd_sum_with_fx_sets_unit_price_for_swap() -> None:
    raw_events = [
        {
            "unique_event_id": "mobile-buy",
            "payload": {
                "timestamp_utc": "2023-07-30T06:59:13+00:00",
                "source": "solscan_wallet_discovery",
                "asset": "MOBILE",
                "side": "in",
                "event_type": "swap_in_aggregated",
                "quantity": "100",
                "fx_rate_usd_eur": "0.9",
                "raw_row": {"value_usd_sum": "22"},
            },
        }
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2023)

    assert result["inventory_end"]["MOBILE"] == "100"
    assert result["tax_line_count"] == 0


def test_raw_value_usd_sum_with_fx_sets_eur_cost_basis() -> None:
    raw_events = [
        {
            "unique_event_id": "jup-buy",
            "payload": {
                "timestamp_utc": "2025-01-01T00:00:00+00:00",
                "source": "solana_rpc",
                "asset": "JUP",
                "side": "in",
                "event_type": "swap_in_aggregated",
                "quantity": "100",
                "fx_rate_usd_eur": "0.9",
                "raw_row": {"value_usd_sum": "200"},
            },
        },
        {
            "unique_event_id": "jup-sell",
            "payload": {
                "timestamp_utc": "2025-01-02T00:00:00+00:00",
                "source": "binance_api",
                "asset": "JUP",
                "side": "out",
                "event_type": "trade",
                "quantity": "100",
                "value_eur": "250",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2025)

    assert result["tax_line_count"] == 1
    assert result["tax_lines"][0]["cost_basis_eur"] == "180.0"
    assert result["tax_lines"][0]["gain_loss_eur"] == "70.0"


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
    assert tax_lines[0]["source_event_id"] == "sell-1"
    assert tax_lines[0]["lot_source_event_id"] == "buy-1"

    assert tax_lines[1]["qty"] == "0.5"
    assert tax_lines[1]["cost_basis_eur"] == "100.5"
    assert tax_lines[1]["proceeds_eur"] == "149.0"
    assert tax_lines[1]["gain_loss_eur"] == "48.5"
    assert tax_lines[1]["tax_status"] == "taxable"
    assert tax_lines[1]["source_event_id"] == "sell-1"
    assert tax_lines[1]["lot_source_event_id"] == "buy-2"


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


def test_fifo_uses_base_asset_for_binance_api_pair_symbol() -> None:
    raw_events = [
        {
            "unique_event_id": "jup-buy",
            "payload": {
                "timestamp_utc": "2025-01-01T10:00:00+00:00",
                "source": "binance_api",
                "asset": "JUPUSDT",
                "base_asset": "JUP",
                "quote_asset": "USDT",
                "event_type": "trade",
                "side": "buy",
                "quantity": "10",
                "price_eur": "0.8",
            },
        },
        {
            "unique_event_id": "jup-sell",
            "payload": {
                "timestamp_utc": "2025-01-02T10:00:00+00:00",
                "source": "binance_api",
                "asset": "JUPUSDT",
                "base_asset": "JUP",
                "quote_asset": "USDT",
                "event_type": "trade",
                "side": "sell",
                "quantity": "5",
                "price_eur": "0.9",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2025)

    assert result["short_sell_violations"] == 0
    assert result["inventory_end"] == {"JUP": "5"}
    assert result["tax_lines"][0]["asset"] == "JUP"


def test_fifo_canonicalizes_known_solana_mints() -> None:
    raw_events = [
        {
            "unique_event_id": "jup-buy-symbol",
            "payload": {
                "timestamp_utc": "2025-03-01T10:00:00+00:00",
                "asset": "JUP",
                "event_type": "token_transfer",
                "defi_label": "swap",
                "side": "in",
                "quantity": "100",
                "price_eur": "0.8",
            },
        },
        {
            "unique_event_id": "jup-sell-mint",
            "payload": {
                "timestamp_utc": "2025-03-02T10:00:00+00:00",
                "asset": "JUPYIWRYJFSKUPIHA7HKER8VUTAEFOSYBKEDZNSDVCN",
                "event_type": "token_transfer",
                "defi_label": "swap",
                "side": "out",
                "quantity": "40",
                "price_eur": "1.0",
            },
        },
        {
            "unique_event_id": "usdc-buy-mint",
            "payload": {
                "timestamp_utc": "2025-03-03T10:00:00+00:00",
                "asset": "EPJFWDD5AUFQSSQEM2QN1XZYBAPC8G4WEGGKZWYTDT1V",
                "event_type": "token_transfer",
                "defi_label": "swap",
                "side": "in",
                "quantity": "10",
                "fx_rate_usd_eur": "0.9",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2025)

    assert result["short_sell_violations"] == 0
    assert result["inventory_end"] == {"JUP": "60", "USDC": "10"}
    assert result["tax_lines"][0]["asset"] == "JUP"
    assert result["tax_lines"][0]["gain_loss_eur"] == "8.0"


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


def test_legacy_helium_transfers_and_network_fees_do_not_create_spot_disposals() -> None:
    raw_events = [
        {
            "unique_event_id": "legacy-transfer",
            "payload": {
                "timestamp_utc": "2022-01-01T00:00:00+00:00",
                "asset": "HNT",
                "event_type": "legacy_transfer",
                "side": "out",
                "quantity": "10",
                "value_usd": "100",
                "source": "helium_legacy_cointracking",
            },
        },
        {
            "unique_event_id": "legacy-fee",
            "payload": {
                "timestamp_utc": "2022-01-01T00:01:00+00:00",
                "asset": "HNT",
                "event_type": "legacy_network_fee",
                "side": "out",
                "quantity": "0.0001",
                "value_usd": "0.01",
                "source": "helium_legacy_cointracking",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2022)

    assert result["class_counts"]["transfer"] == 2
    assert result["tax_line_count"] == 0
    assert result["short_sell_violations"] == 0


def test_reward_inflow_creates_fifo_lot_cost_basis() -> None:
    raw_events = [
        {
            "unique_event_id": "iot-reward",
            "payload": {
                "timestamp_utc": "2024-03-01T00:00:00+00:00",
                "source": "heliumgeek",
                "asset": "IOT",
                "event_type": "mining_reward",
                "side": "in",
                "quantity": "1000000",
                "price_eur": "0.002",
                "raw_row": {
                    "IOT Token": "IOT",
                    "IOT Tokens": "10000",
                },
            },
        },
        {
            "unique_event_id": "iot-sale",
            "payload": {
                "timestamp_utc": "2024-03-02T00:00:00+00:00",
                "source": "solana_rpc",
                "asset": "IOT",
                "event_type": "swap_out_aggregated",
                "side": "out",
                "quantity": "5000",
                "value_eur": "15",
            },
        },
    ]

    result = process_events_for_year(raw_events=raw_events, tax_year=2024)

    assert result["class_counts"]["reward"] == 1
    assert result["short_sell_violations"] == 0
    assert result["tax_lines"][0]["cost_basis_eur"] == "10.000"
    assert result["tax_lines"][0]["gain_loss_eur"] == "5.000"
    assert result["tax_lines"][0]["lot_source_event_id"] == "iot-reward"


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
