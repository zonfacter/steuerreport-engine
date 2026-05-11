from __future__ import annotations

import asyncio

from tax_engine.api.app import (
    ProcessCompareRulesetsRequest,
    ProcessPreflightRequest,
    ReviewTimezoneCorrectRequest,
    TaxEventOverrideUpsertRequest,
    audit_tax_line,
    import_confirm,
    portfolio_lot_aging,
    process_compare_rulesets_post,
    process_derivative_lines,
    process_options,
    process_preflight,
    process_run,
    process_status,
    process_tax_domain_summary,
    process_tax_lines,
    process_worker_run_next,
    report_export,
    report_files,
    review_timezone_correct,
    tax_event_override_upsert,
)
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE
from tax_engine.queue.models import ProcessRunRequest, WorkerRunNextRequest
from tax_engine.queue.service import (
    attach_binance_fiat_purchase_value_anchors,
    attach_binance_market_quote_value_anchors,
    attach_bitget_tax_api_spot_trade_value_anchors,
    attach_cached_usd_prices_to_binance_dust_convert_in_events,
    attach_cached_usd_prices_to_reward_events,
    attach_cached_usd_prices_to_swap_in_events,
    attach_reference_usd_value_anchors,
    drop_exact_pionex_duplicate_events,
    drop_malformed_binance_market_summary_events,
    drop_solscan_duplicates_when_solana_rpc_is_active,
    label_helium_solana_claim_events,
)


def _reset_store() -> None:
    STORE.reset_for_tests()


async def _read_streaming_body(response: object) -> bytes:
    chunks: list[bytes] = []
    async for chunk in response.body_iterator:  # type: ignore[attr-defined]
        chunks.append(chunk if isinstance(chunk, bytes) else str(chunk).encode("utf-8"))
    return b"".join(chunks)


def test_process_run_creates_queued_job() -> None:
    _reset_store()
    response = process_run(
        ProcessRunRequest(
            tax_year=2026,
            ruleset_id="DE-2026-v1.0",
            config={"calculation_mode": "depot_separated"},
            dry_run=True,
        )
    )

    assert response.status == "success"
    assert response.data["status"] == "queued"
    assert response.data["progress"] == 0
    assert response.data["tax_year"] == 2026
    assert response.data["ruleset_id"] == "DE-2026-v1.0"


def test_attach_reference_usd_value_anchors_from_solscan_to_solana_rpc() -> None:
    active_events = [
        {
            "unique_event_id": "solana-rpc-in",
            "payload": {
                "timestamp_utc": "2024-12-09T08:21:44+00:00",
                "source": "solana_rpc",
                "asset": "JUP",
                "side": "in",
                "event_type": "swap_in_aggregated",
                "quantity": "3701.700000",
                "tx_id": "same-signature",
            },
        }
    ]
    all_events = [
        *active_events,
        {
            "unique_event_id": "solscan-reference-in",
            "payload": {
                "timestamp_utc": "2024-12-09T08:21:44+00:00",
                "source": "solscan_wallet_discovery",
                "asset": "JUP",
                "side": "in",
                "event_type": "swap_in_aggregated",
                "quantity": "3701.7",
                "tx_id": "same-signature",
                "raw_row": {"value_usd_sum": "4682.284012091743"},
            },
        },
    ]

    enriched, summary = attach_reference_usd_value_anchors(active_events, all_events)

    payload = enriched[0]["payload"]
    assert summary["attached_anchor_count"] == 1
    assert payload["value_usd_sum"] == "4682.284012091743"
    assert payload["valuation_reference_source"] == "solscan_wallet_discovery"
    assert payload["valuation_reference_source_event_id"] == "solscan-reference-in"


def test_attach_reference_usd_value_anchors_from_solscan_stable_counterflow() -> None:
    _reset_store()
    STORE.upsert_solscan_transaction(
        signature="same-signature",
        wallet_address="wallet-1",
        endpoint="https://pro-api.solscan.io/v2.0/transaction/detail",
        http_status=200,
        success=True,
        block_time_utc="2024-12-09T08:21:44+00:00",
        slot=1,
        raw_json=(
            '{"success": true, "data": {"token_bal_change": ['
            '{"owner": "wallet-1", "token_address": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN", '
            '"change_amount": "1547517296", "decimals": 6},'
            '{"owner": "pool-1", "token_address": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", '
            '"change_amount": "1781426316", "decimals": 6}'
            ']}}'
        ),
        summary_json="{}",
    )
    active_events = [
        {
            "unique_event_id": "solana-rpc-in",
            "payload": {
                "timestamp_utc": "2024-12-09T08:21:44+00:00",
                "source": "solana_rpc",
                "asset": "JUPYIWRYJFSKUPIHA7HKER8VUTAEFOSYBKEDZNSDVCN",
                "side": "in",
                "event_type": "token_transfer",
                "quantity": "1547.517296",
                "tx_id": "same-signature",
                "wallet_address": "wallet-1",
            },
        }
    ]

    enriched, summary = attach_reference_usd_value_anchors(active_events, active_events)

    payload = enriched[0]["payload"]
    assert summary["attached_anchor_count"] == 1
    assert summary["solscan_counterflow_attached_count"] == 1
    assert payload["value_usd_sum"] == "1781.426316"
    assert payload["valuation_reference_source"] == "solscan_transaction_counterflow"
    assert payload["valuation_reference_tx_id"] == "same-signature"


def test_attach_reference_usd_value_anchors_from_solscan_wsol_counterflow() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2024-09-18", "SOL", "USD", "150", "test", "2024-09-18")
    STORE.upsert_solscan_transaction(
        signature="same-signature",
        wallet_address="wallet-1",
        endpoint="https://pro-api.solscan.io/v2.0/transaction/detail",
        http_status=200,
        success=True,
        block_time_utc="2024-09-18T08:21:44+00:00",
        slot=1,
        raw_json=(
            '{"success": true, "data": {"token_bal_change": ['
            '{"owner": "wallet-1", "token_address": "ZEUS1aR7aX8DFFJf5QjWj2ftDDdNTroMNGo8YoQm3Gq", '
            '"change_amount": "1815225707", "decimals": 6},'
            '{"owner": "pool-1", "token_address": "So11111111111111111111111111111111111111112", '
            '"change_amount": "3966000000", "decimals": 9}'
            ']}}'
        ),
        summary_json="{}",
    )
    active_events = [
        {
            "unique_event_id": "solana-rpc-in",
            "payload": {
                "timestamp_utc": "2024-09-18T08:21:44+00:00",
                "source": "solana_rpc",
                "asset": "ZEUS1AR7AX8DFFJF5QJWJ2FTDDDNTROMNGO8YOQM3GQ",
                "side": "in",
                "event_type": "token_transfer",
                "quantity": "1815.225707",
                "tx_id": "same-signature",
                "wallet_address": "wallet-1",
            },
        }
    ]

    enriched, summary = attach_reference_usd_value_anchors(active_events, active_events)

    payload = enriched[0]["payload"]
    assert summary["solscan_counterflow_attached_count"] == 1
    assert payload["value_usd_sum"] == "594.900"
    assert payload["valuation_reference_source"] == "solscan_transaction_counterflow"


def test_attach_reference_usd_value_anchors_from_raw_stable_counterflow() -> None:
    active_events = [
        {
            "unique_event_id": "iot-swap-out",
            "payload": {
                "timestamp_utc": "2024-02-23T21:01:15+00:00",
                "source": "solana_rpc",
                "asset": "IOTEVVZLEYWOTN1QDWNPDDXPWSZN3ZFHEOT3MFL9FNS",
                "side": "out",
                "event_type": "swap_out_aggregated",
                "quantity": "421245.10905",
                "tx_id": "same-signature",
                "raw_row": {
                    "from_asset": "IOTEVVZLEYWOTN1QDWNPDDXPWSZN3ZFHEOT3MFL9FNS",
                    "from_quantity": "421245.10905",
                    "to_asset": "ES9VMFRZACERMJFRF4H2FYD4KCONKY11MCCE8BENWNYB",
                    "to_quantity": "902.309402",
                },
            },
        }
    ]

    enriched, summary = attach_reference_usd_value_anchors(active_events, active_events)

    payload = enriched[0]["payload"]
    assert summary["attached_anchor_count"] == 1
    assert summary["raw_stable_counterflow_attached_count"] == 1
    assert payload["value_usd_sum"] == "902.309402"
    assert payload["valuation_reference_source"] == "raw_stable_counterflow"
    assert payload["valuation_reference_tx_id"] == "same-signature"


def test_attach_bitget_tax_api_spot_trade_value_anchors_from_biz_order() -> None:
    events = [
        {
            "unique_event_id": "hnt-buy",
            "payload": {
                "timestamp_utc": "2025-01-29T05:58:45.618000+00:00",
                "source": "bitget_tax_api",
                "event_type": "trade",
                "side": "in",
                "asset": "HNT",
                "quantity": "845.931",
                "fee": "0.845931",
                "fee_asset": "HNT",
                "tx_id": "1268376005322551306",
                "raw_row": {
                    "bizOrderId": "1268376005262102633",
                    "spotTaxType": "Buy",
                },
            },
        },
        {
            "unique_event_id": "usdt-sell",
            "payload": {
                "timestamp_utc": "2025-01-29T05:58:45.618000+00:00",
                "source": "bitget_tax_api",
                "event_type": "trade",
                "side": "out",
                "asset": "USDT",
                "quantity": "3112.180149",
                "fee": "0",
                "tx_id": "1268376005326745601",
                "raw_row": {
                    "bizOrderId": "1268376005262102633",
                    "spotTaxType": "Sell",
                },
            },
        },
    ]

    enriched, summary = attach_bitget_tax_api_spot_trade_value_anchors(events)

    payload = enriched[0]["payload"]
    assert summary["available_counterflow_count"] == 1
    assert summary["attached_anchor_count"] == 1
    assert payload["value_usd_sum"] == "3112.180149"
    assert payload["valuation_reference_source"] == "bitget_tax_api_biz_order_stable_counterflow"
    assert payload["valuation_reference_source_event_id"] == "usdt-sell"
    assert payload["valuation_reference_asset"] == "USDT"
    assert payload["valuation_reference_biz_order_id"] == "1268376005262102633"


def test_attach_binance_market_quote_value_anchors_from_crypto_quote() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2021-02-06", "BTC", "USD", "39266.01171875", "test", "2021-02-06")
    events = [
        {
            "unique_event_id": "hnt-in",
            "payload": {
                "timestamp_utc": "2021-02-06T21:23:58+00:00",
                "source": "binance",
                "event_type": "trade",
                "side": "in",
                "asset": "HNT",
                "quantity": "30",
                "price": "0.000092",
                "raw_row": {
                    "Market": "HNTBTC",
                    "Type": "BUY",
                    "Amount": "30",
                    "Total": "0.00276",
                },
            },
        },
        {
            "unique_event_id": "btc-out",
            "payload": {
                "timestamp_utc": "2021-02-06T21:23:58+00:00",
                "source": "binance",
                "event_type": "trade",
                "side": "out",
                "asset": "BTC",
                "quantity": "0.00276",
                "price": "0.000092",
                "raw_row": {
                    "Market": "HNTBTC",
                    "Type": "BUY",
                    "Amount": "30",
                    "Total": "0.00276",
                },
            },
        },
    ]

    enriched, summary = attach_binance_market_quote_value_anchors(events)

    assert summary["available_market_row_count"] == 2
    assert summary["attached_usd_value_count"] == 2
    assert enriched[0]["payload"]["value_usd_sum"] == "108.3741923437500"
    assert enriched[0]["payload"]["price"] == ""
    assert enriched[0]["payload"]["binance_market_quote_unit_price"] == "0.000092"
    assert enriched[0]["payload"]["valuation_reference_source"] == "binance_market_quote_total"
    assert enriched[0]["payload"]["valuation_reference_asset"] == "BTC"
    assert enriched[0]["payload"]["valuation_reference_rate_date"] == "2021-02-06"
    assert enriched[1]["payload"]["value_usd_sum"] == "108.3741923437500"


def test_attach_binance_market_quote_value_anchors_from_eur_quote() -> None:
    events = [
        {
            "unique_event_id": "win-in",
            "payload": {
                "timestamp_utc": "2021-05-01T18:40:17+00:00",
                "source": "binance",
                "event_type": "trade",
                "side": "in",
                "asset": "WIN",
                "quantity": "56570",
                "price": "0.001106",
                "raw_row": {
                    "Market": "WINEUR",
                    "Type": "BUY",
                    "Amount": "56570",
                    "Total": "62.56642",
                },
            },
        }
    ]

    enriched, summary = attach_binance_market_quote_value_anchors(events)

    assert summary["attached_eur_value_count"] == 1
    assert enriched[0]["payload"]["value_eur"] == "62.56642"
    assert enriched[0]["payload"]["price"] == ""
    assert enriched[0]["payload"]["valuation_reference_asset"] == "EUR"


def test_attach_cached_usd_prices_to_binance_dust_convert_in_events() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2021-04-28", "BNB", "USD", "562.63256836", "test", "2021-04-28")
    events = [
        {
            "unique_event_id": "dust-bnb-in",
            "payload": {
                "timestamp_utc": "2021-04-28T05:14:15+00:00",
                "source": "binance_api",
                "event_type": "dust_convert_in",
                "side": "in",
                "asset": "BNB",
                "quantity": "0.27191796",
                "fee": "0.00543836",
                "fee_asset": "BNB",
                "tx_id": "55615425065",
            },
        },
        {
            "unique_event_id": "dust-sol-out",
            "payload": {
                "timestamp_utc": "2021-04-28T05:14:15+00:00",
                "source": "binance_api",
                "event_type": "dust_convert_out",
                "side": "out",
                "asset": "SOL",
                "quantity": "0.099",
                "tx_id": "55615425065",
            },
        },
    ]

    enriched, summary = attach_cached_usd_prices_to_binance_dust_convert_in_events(events)

    assert summary["attached_price_count"] == 1
    assert enriched[0]["payload"]["price_usd"] == "562.63256836"
    assert enriched[0]["payload"]["valuation_reference_source"] == "fx_cache_asset_usd_binance_dust_convert_in"
    assert enriched[0]["payload"]["valuation_reference_asset"] == "BNB"
    assert enriched[0]["payload"]["valuation_reference_rate_date"] == "2021-04-28"
    assert "price_usd" not in enriched[1]["payload"]


def test_attach_binance_fiat_purchase_value_anchors_from_eur_counterflow() -> None:
    events = [
        {
            "unique_event_id": "eur-out",
            "payload": {
                "timestamp_utc": "2021-02-06T21:18:15+00:00",
                "source": "binance",
                "event_type": "fiat_crypto_purchase",
                "side": "out",
                "asset": "EUR",
                "quantity": "98.1",
                "tx_id": "2ae01da3bd9f4522a103b8c54f0eb1c6:0:EUR",
                "raw_row": {"Remark": "2ae01da3bd9f4522a103b8c54f0eb1c6"},
            },
        },
        {
            "unique_event_id": "bnb-in",
            "payload": {
                "timestamp_utc": "2021-02-06T21:18:15+00:00",
                "source": "binance",
                "event_type": "fiat_crypto_purchase",
                "side": "in",
                "asset": "BNB",
                "quantity": "1.625",
                "tx_id": "2ae01da3bd9f4522a103b8c54f0eb1c6:2:BNB",
                "raw_row": {"Remark": "2ae01da3bd9f4522a103b8c54f0eb1c6"},
            },
        },
    ]

    enriched, summary = attach_binance_fiat_purchase_value_anchors(events)

    assert summary["available_counterflow_count"] == 1
    assert summary["attached_anchor_count"] == 1
    assert enriched[1]["payload"]["value_eur"] == "98.1"
    assert enriched[1]["payload"]["valuation_reference_source"] == "binance_fiat_purchase_eur_counterflow"
    assert enriched[1]["payload"]["valuation_reference_source_event_id"] == "eur-out"
    assert enriched[1]["payload"]["valuation_reference_asset"] == "EUR"


def test_attach_binance_fiat_purchase_value_anchors_skips_ambiguous_group() -> None:
    events = [
        {
            "unique_event_id": "eur-out",
            "payload": {
                "source": "binance",
                "event_type": "fiat_crypto_purchase",
                "side": "out",
                "asset": "EUR",
                "quantity": "100",
                "tx_id": "group-1:0:EUR",
            },
        },
        {
            "unique_event_id": "bnb-in",
            "payload": {
                "source": "binance",
                "event_type": "fiat_crypto_purchase",
                "side": "in",
                "asset": "BNB",
                "quantity": "1",
                "tx_id": "group-1:1:BNB",
            },
        },
        {
            "unique_event_id": "eth-in",
            "payload": {
                "source": "binance",
                "event_type": "fiat_crypto_purchase",
                "side": "in",
                "asset": "ETH",
                "quantity": "0.01",
                "tx_id": "group-1:2:ETH",
            },
        },
    ]

    enriched, summary = attach_binance_fiat_purchase_value_anchors(events)

    assert summary["attached_anchor_count"] == 0
    assert summary["ambiguous_inflow_group_count"] == 1
    assert "value_eur" not in enriched[1]["payload"]
    assert "value_eur" not in enriched[2]["payload"]


def test_attach_cached_usd_prices_to_reward_events() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2024-03-01", "IOT", "USD", "0.002", "test", "2024-03-01")
    events = [
        {
            "unique_event_id": "iot-reward",
            "payload": {
                "timestamp_utc": "2024-03-01T00:00:00+00:00",
                "source": "heliumgeek",
                "asset": "IOT",
                "side": "in",
                "event_type": "mining_reward",
                "quantity": "100",
            },
        }
    ]

    enriched, summary = attach_cached_usd_prices_to_reward_events(events)

    payload = enriched[0]["payload"]
    assert summary["attached_price_count"] == 1
    assert payload["price_usd"] == "0.002"
    assert payload["valuation_reference_source"] == "fx_cache_asset_usd_reward"
    assert payload["valuation_reference_asset"] == "IOT"
    assert payload["valuation_reference_rate_date"] == "2024-03-01"


def test_attach_cached_usd_prices_to_claim_label_events() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2023-06-24", "IOT", "USD", "0.0006", "test", "2023-06-24")
    events = [
        {
            "unique_event_id": "iot-claim",
            "payload": {
                "timestamp_utc": "2023-06-24T04:20:16+00:00",
                "source": "solana_rpc",
                "asset": "IOTEVVZLEYWOTN1QDWNPDDXPWSZN3ZFHEOT3MFL9FNS",
                "side": "in",
                "event_type": "token_transfer",
                "defi_label": "claim",
                "quantity": "23617.275455",
            },
        }
    ]

    enriched, summary = attach_cached_usd_prices_to_reward_events(events)

    payload = enriched[0]["payload"]
    assert summary["attached_price_count"] == 1
    assert payload["price_usd"] == "0.0006"
    assert payload["valuation_reference_source"] == "fx_cache_asset_usd_reward"


def test_label_helium_solana_claim_events_from_distribution_program() -> None:
    events = [
        {
            "unique_event_id": "iot-distribution",
            "payload": {
                "timestamp_utc": "2023-04-20T17:56:12+00:00",
                "source": "solana_rpc",
                "asset": "IOTEVVZLEYWOTN1QDWNPDDXPWSZN3ZFHEOT3MFL9FNS",
                "side": "in",
                "event_type": "token_transfer",
                "defi_label": "unknown",
                "quantity": "40591.287485",
                "raw_row": {
                    "transaction": {
                        "message": {
                            "accountKeys": [
                                {"pubkey": "1atrmQs3eq1N2FEYWu6tyTXbCjP4uQwExpjtnhXtS8h"}
                            ]
                        }
                    }
                },
            },
        }
    ]

    enriched, summary = label_helium_solana_claim_events(events)

    assert summary["labelled_count"] == 1
    assert enriched[0]["payload"]["defi_label"] == "claim"
    assert enriched[0]["payload"]["valuation_reference_source"] == "helium_solana_distribution_label"


def test_attach_cached_usd_prices_to_interest_events() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2025-01-20", "JUP", "USD", "0.97078", "test", "2025-01-20")
    events = [
        {
            "unique_event_id": "jup-interest",
            "payload": {
                "timestamp_utc": "2025-01-20T23:59:59+00:00",
                "source": "binance_api",
                "asset": "JUP",
                "side": "in",
                "event_type": "interest",
                "quantity": "0.12031391",
            },
        }
    ]

    enriched, summary = attach_cached_usd_prices_to_reward_events(events)

    payload = enriched[0]["payload"]
    assert summary["attached_price_count"] == 1
    assert payload["price_usd"] == "0.97078"
    assert payload["valuation_reference_source"] == "fx_cache_asset_usd_reward"


def test_attach_cached_usd_prices_skips_plain_transfers() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2024-03-01", "IOT", "USD", "0.002", "test", "2024-03-01")
    events = [
        {
            "unique_event_id": "iot-transfer",
            "payload": {
                "timestamp_utc": "2024-03-01T00:00:00+00:00",
                "source": "solana_rpc",
                "asset": "IOT",
                "side": "in",
                "event_type": "token_transfer",
                "quantity": "100",
            },
        }
    ]

    enriched, summary = attach_cached_usd_prices_to_reward_events(events)

    assert summary["attached_price_count"] == 0
    assert "price_usd" not in enriched[0]["payload"]
    assert "valuation_reference_source" not in enriched[0]["payload"]


def test_attach_cached_usd_prices_to_swap_in_events() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2024-08-23", "JUP", "USD", "0.84", "test", "2024-08-23")
    events = [
        {
            "unique_event_id": "jup-swap-in",
            "payload": {
                "timestamp_utc": "2024-08-23T20:13:31+00:00",
                "source": "solana_rpc",
                "asset": "JUPYIWRYJFSKUPIHA7HKER8VUTAEFOSYBKEDZNSDVCN",
                "side": "in",
                "event_type": "swap_in_aggregated",
                "quantity": "750",
            },
        }
    ]

    enriched, summary = attach_cached_usd_prices_to_swap_in_events(events)

    payload = enriched[0]["payload"]
    assert summary["attached_price_count"] == 1
    assert payload["price_usd"] == "0.84"
    assert payload["valuation_reference_source"] == "fx_cache_asset_usd_swap_in"
    assert payload["valuation_reference_asset"] == "JUP"


def test_attach_cached_usd_prices_to_swap_in_events_skips_transfers() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2024-08-23", "JUP", "USD", "0.84", "test", "2024-08-23")
    events = [
        {
            "unique_event_id": "jup-transfer-in",
            "payload": {
                "timestamp_utc": "2024-08-23T20:13:31+00:00",
                "source": "solana_rpc",
                "asset": "JUP",
                "side": "in",
                "event_type": "token_transfer",
                "quantity": "750",
            },
        }
    ]

    enriched, summary = attach_cached_usd_prices_to_swap_in_events(events)

    assert summary["attached_price_count"] == 0
    assert "price_usd" not in enriched[0]["payload"]


def test_attach_cached_usd_prices_to_swap_token_transfer_events() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2024-08-29", "IOT", "USD", "0.0012571", "test", "2024-08-29")
    events = [
        {
            "unique_event_id": "iot-swap-transfer-in",
            "payload": {
                "timestamp_utc": "2024-08-29T11:23:49+00:00",
                "source": "solana_rpc",
                "asset": "IOT",
                "side": "in",
                "event_type": "token_transfer",
                "defi_label": "swap",
                "quantity": "554625.934520",
            },
        }
    ]

    enriched, summary = attach_cached_usd_prices_to_swap_in_events(events)

    payload = enriched[0]["payload"]
    assert summary["attached_price_count"] == 1
    assert payload["price_usd"] == "0.0012571"
    assert payload["valuation_reference_source"] == "fx_cache_asset_usd_swap_in"
    assert payload["valuation_reference_asset"] == "IOT"


def test_attach_cached_usd_prices_to_swap_sol_transfer_events() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2025-01-04", "SOL", "USD", "217.76", "test", "2025-01-04")
    events = [
        {
            "unique_event_id": "sol-swap-transfer-in",
            "payload": {
                "timestamp_utc": "2025-01-04T08:32:56+00:00",
                "source": "solana_rpc",
                "asset": "SOL",
                "side": "in",
                "event_type": "sol_transfer",
                "defi_label": "swap",
                "quantity": "0.289811571",
            },
        }
    ]

    enriched, summary = attach_cached_usd_prices_to_swap_in_events(events)

    payload = enriched[0]["payload"]
    assert summary["attached_price_count"] == 1
    assert payload["price_usd"] == "217.76"
    assert payload["valuation_reference_source"] == "fx_cache_asset_usd_swap_in"
    assert payload["valuation_reference_asset"] == "SOL"


def test_attach_cached_usd_prices_to_swap_in_events_uses_priced_counterflow() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2024-03-11", "MOBILE", "USD", "0.00411878", "test", "2024-03-11")
    events = [
        {
            "unique_event_id": "unknown-swap-in",
            "payload": {
                "timestamp_utc": "2024-03-11T19:40:08+00:00",
                "source": "solana_rpc",
                "tx_id": "same-signature",
                "asset": "CBDC",
                "side": "in",
                "event_type": "swap_in_aggregated",
                "quantity": "18902619.55",
            },
        },
        {
            "unique_event_id": "mobile-swap-out",
            "payload": {
                "timestamp_utc": "2024-03-11T19:40:08+00:00",
                "source": "solana_rpc",
                "tx_id": "same-signature",
                "asset": "MOBILE",
                "side": "out",
                "event_type": "swap_out_aggregated",
                "quantity": "23700",
            },
        },
    ]

    enriched, summary = attach_cached_usd_prices_to_swap_in_events(events)

    payload = enriched[0]["payload"]
    assert summary["attached_price_count"] == 1
    assert summary["same_tx_priced_counterflow_attached_count"] == 1
    assert payload["value_usd_sum"] == "97.61508600"
    assert payload["valuation_reference_source"] == "same_tx_priced_counterflow"
    assert payload["valuation_reference_asset"] == "MOBILE"


def test_attach_cached_usd_prices_to_swap_in_events_uses_raw_route_counterflow() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2024-04-28", "JUP", "USD", "1.011", "test", "2024-04-28")
    events = [
        {
            "unique_event_id": "unknown-route-swap-in",
            "payload": {
                "timestamp_utc": "2024-04-28T19:08:19+00:00",
                "source": "solana_rpc",
                "tx_id": "route-signature",
                "asset": "25HAYB3GUHCVJDGKIFHGUSKFQOZSNFF46CACVT2WLMTDJ",
                "side": "in",
                "event_type": "token_transfer",
                "defi_label": "swap",
                "quantity": "7445.66318",
                "raw_row": {
                    "inner_instructions": [
                        {
                            "instructions": [
                                {
                                    "parsed": {
                                        "info": {
                                            "mint": "JUP",
                                            "tokenAmount": {"uiAmountString": "100"},
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                },
            },
        }
    ]

    enriched, summary = attach_cached_usd_prices_to_swap_in_events(events)

    payload = enriched[0]["payload"]
    assert summary["attached_price_count"] == 1
    assert summary["raw_priced_route_counterflow_attached_count"] == 1
    assert payload["value_usd_sum"] == "101.100"
    assert payload["valuation_reference_source"] == "raw_priced_route_counterflow"
    assert payload["valuation_reference_asset"] == "JUP"


def test_drop_solscan_duplicate_when_solana_rpc_is_active() -> None:
    events = [
        {
            "unique_event_id": "solana-rpc-out",
            "payload": {
                "source": "solana_rpc",
                "asset": "USDC",
                "side": "out",
                "quantity": "1303.122096",
                "tx_id": "same-signature",
            },
        },
        {
            "unique_event_id": "solscan-out",
            "payload": {
                "source": "solscan_wallet_discovery",
                "asset": "USDC",
                "side": "out",
                "quantity": "1303.122096",
                "tx_id": "same-signature",
            },
        },
        {
            "unique_event_id": "solscan-missing-primary",
            "payload": {
                "source": "solscan_wallet_discovery",
                "asset": "JUP",
                "side": "in",
                "quantity": "10",
                "tx_id": "other-signature",
            },
        },
    ]

    filtered, summary = drop_solscan_duplicates_when_solana_rpc_is_active(events)

    assert [event["unique_event_id"] for event in filtered] == ["solana-rpc-out", "solscan-missing-primary"]
    assert summary["dropped_solscan_duplicate_count"] == 1


def test_drop_malformed_binance_market_summary_events() -> None:
    events = [
        {
            "unique_event_id": "malformed-summary",
            "payload": {
                "timestamp_utc": "2021-05-01T18:40:17+00:00",
                "source": "binance",
                "event_type": "buy",
                "side": "buy",
                "asset": "",
                "quantity": "56570",
                "price": "0.001106",
                "fee": "0.00009036",
                "fee_asset": "BNB",
                "raw_row": {
                    "Market": "WINEUR",
                    "Type": "BUY",
                    "Amount": "56570",
                    "Total": "62.56642",
                },
            },
        },
        {
            "unique_event_id": "win-in",
            "payload": {
                "timestamp_utc": "2021-05-01T18:40:17+00:00",
                "source": "binance",
                "event_type": "trade",
                "side": "in",
                "asset": "WIN",
                "quantity": "56570",
                "price": "0.001106",
                "fee": "0.00009036",
                "fee_asset": "BNB",
            },
        },
        {
            "unique_event_id": "eur-out",
            "payload": {
                "timestamp_utc": "2021-05-01T18:40:17+00:00",
                "source": "binance",
                "event_type": "trade",
                "side": "out",
                "asset": "EUR",
                "quantity": "62.56642",
                "price": "0.001106",
            },
        },
    ]

    filtered, summary = drop_malformed_binance_market_summary_events(events)

    assert [event["unique_event_id"] for event in filtered] == ["win-in", "eur-out"]
    assert summary["dropped_malformed_binance_market_summary_count"] == 1


def test_drop_exact_pionex_duplicate_events_keeps_first_copy() -> None:
    events = [
        {
            "unique_event_id": "pionex-a",
            "payload": {
                "source": "pionex",
                "timestamp_utc": "2022-01-19T12:45:42+00:00",
                "event_type": "trade",
                "side": "out",
                "asset": "USDT",
                "quantity": "479.99307717000000000000",
                "fee": "0",
                "fee_asset": "",
            },
        },
        {
            "unique_event_id": "pionex-b",
            "payload": {
                "source": "pionex",
                "timestamp_utc": "2022-01-19T12:45:42+00:00",
                "event_type": "trade",
                "side": "out",
                "asset": "USDT",
                "quantity": "479.99307717000000000000",
                "fee": "0",
                "fee_asset": "",
            },
        },
        {
            "unique_event_id": "binance-same-shape",
            "payload": {
                "source": "binance",
                "timestamp_utc": "2022-01-19T12:45:42+00:00",
                "event_type": "trade",
                "side": "out",
                "asset": "USDT",
                "quantity": "479.99307717000000000000",
            },
        },
    ]

    filtered, summary = drop_exact_pionex_duplicate_events(events)

    assert [event["unique_event_id"] for event in filtered] == ["pionex-a", "binance-same-shape"]
    assert summary["dropped_pionex_duplicate_count"] == 1


def test_process_run_normalizes_de_alias_and_version_from_ui() -> None:
    _reset_store()
    response = process_run(
        ProcessRunRequest(
            tax_year=2026,
            ruleset_id="DE",
            ruleset_version="2026-v1",
            config={},
            dry_run=True,
        )
    )

    assert response.status == "success"
    assert response.data["ruleset_id"] == "DE-2026-v1.0"
    assert response.data["ruleset_version"] == "1.0"
    assert any(item["code"] == "ruleset_resolved" for item in response.warnings)


def test_process_options_returns_wizard_choices() -> None:
    _reset_store()

    response = process_options()

    assert response.status == "success"
    assert 2026 in response.data["tax_years"]
    assert any(item["id"] == "fifo" for item in response.data["tax_methods"])
    assert any(item["id"] == "global" for item in response.data["depot_modes"])
    assert any(item["ruleset_id"] == "DE-2026-v1.0" for item in response.data["rulesets"])


def test_process_preflight_blocks_without_import_data() -> None:
    _reset_store()

    response = process_preflight(
        ProcessPreflightRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={})
    )

    assert response.status == "success"
    assert response.data["allow_run"] is False
    blocker = next(item for item in response.data["blockers"] if item["code"] == "no_import_data")
    assert blocker["action"]["target_step"] == "1"
    assert blocker["action"]["target_element_id"] == "integrationHub"


def test_process_preflight_allows_clean_year_with_priced_trade() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="preflight.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                    "event_type": "buy",
                }
            ],
        )
    )

    response = process_preflight(
        ProcessPreflightRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={})
    )

    assert response.status == "success"
    assert response.data["allow_run"] is True
    assert response.data["counts"]["tax_year_events"] == 1
    assert response.data["blockers"] == []


def test_process_preflight_treats_binance_api_eur_quote_as_priced() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="binance-api-eur-quote.csv",
            rows=[
                {
                    "timestamp_utc": "2025-10-13T12:45:07.878000+00:00",
                    "source": "binance_api",
                    "asset": "ADAEUR",
                    "base_asset": "ADA",
                    "quote_asset": "EUR",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "126.5",
                    "price": "0.6167",
                }
            ],
        )
    )

    response = process_preflight(
        ProcessPreflightRequest(tax_year=2025, ruleset_id="DE-2025-v1.0", config={})
    )

    assert response.status == "success"
    assert response.data["allow_run"] is True
    assert response.data["counts"]["unresolved_valuation_events"] == 0
    assert response.data["blockers"] == []


def test_process_preflight_applies_review_timestamp_corrections() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2023-04-20", "IOT", "USD", "0.0006", "test", "2023-04-20")
    import_confirm(
        ConfirmImportRequest(
            source_name="preflight-review-correction.csv",
            rows=[
                {
                    "timestamp": "2023-04-01T00:00:00Z",
                    "asset": "IOT",
                    "side": "in",
                    "amount": "1000",
                    "event_type": "mining_reward",
                    "source": "heliumgeek",
                }
            ],
        )
    )
    event_id = STORE.list_raw_events()[0]["unique_event_id"]
    review_timezone_correct(
        ReviewTimezoneCorrectRequest(
            source_event_id=str(event_id),
            corrected_timestamp_utc="2023-04-20T00:00:00Z",
            reason_code="source_period_start",
            note="Periodenstart auf ersten bepreisten Markttag korrigiert.",
        )
    )

    response = process_preflight(
        ProcessPreflightRequest(tax_year=2023, ruleset_id="DE-2023-v1.0", config={})
    )

    assert response.status == "success"
    assert response.data["counts"]["tax_year_events"] == 1
    assert response.data["counts"]["unresolved_valuation_events"] == 0
    assert response.data["review_action_summary"]["timezone_correction_count"] == 1


def test_worker_applies_review_timestamp_corrections_before_reward_pricing() -> None:
    _reset_store()
    STORE.upsert_fx_rate("2023-04-20", "IOT", "USD", "0.0006", "test", "2023-04-20")
    STORE.upsert_fx_rate("2023-04-20", "USD", "EUR", "0.9", "test", "2023-04-20")
    import_confirm(
        ConfirmImportRequest(
            source_name="worker-review-correction.csv",
            rows=[
                {
                    "timestamp": "2023-04-01T00:00:00Z",
                    "asset": "IOT",
                    "side": "in",
                    "amount": "1000",
                    "event_type": "mining_reward",
                    "source": "heliumgeek",
                },
                {
                    "timestamp": "2023-04-26T12:00:00Z",
                    "asset": "IOT",
                    "side": "out",
                    "amount": "1000",
                    "event_type": "swap_out_aggregated",
                    "source": "solana_rpc",
                    "price_eur": "0.002",
                },
            ],
        )
    )
    reward_event_id = STORE.list_raw_events()[0]["unique_event_id"]
    review_timezone_correct(
        ReviewTimezoneCorrectRequest(
            source_event_id=str(reward_event_id),
            corrected_timestamp_utc="2023-04-20T00:00:00Z",
            reason_code="source_period_start",
            note="Periodenstart auf ersten bepreisten Markttag korrigiert.",
        )
    )

    created = process_run(ProcessRunRequest(tax_year=2023, ruleset_id="DE-2023-v1.0", config={}, dry_run=False))
    job_id = created.data["job_id"]
    result = process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))

    tax_lines = STORE.get_tax_lines(job_id)
    assert result.status == "success"
    assert result.data["result_summary"]["review_actions"]["timezone_correction_count"] == 1
    assert result.data["result_summary"]["reward_price_summary"]["attached_price_count"] == 1
    assert tax_lines[0]["buy_timestamp_utc"] == "2023-04-20T00:00:00+00:00"
    assert tax_lines[0]["cost_basis_eur"] == "0.54000"


def test_process_preflight_ignores_zero_quantity_reward_without_value() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="preflight-zero-reward.csv",
            rows=[
                {
                    "timestamp": "2022-09-22T21:17:59Z",
                    "asset": "HNT",
                    "side": "in",
                    "amount": "0",
                    "event_type": "mining_reward",
                    "source": "helium_legacy_cointracking",
                }
            ],
        )
    )

    response = process_preflight(
        ProcessPreflightRequest(tax_year=2022, ruleset_id="DE-2022-v1.0", config={})
    )

    assert response.status == "success"
    assert response.data["counts"]["tax_year_events"] == 1
    assert response.data["counts"]["unresolved_valuation_events"] == 0


def test_process_preflight_classifies_binance_wallet_deposit_shape() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="binance_deposit_shape.csv",
            rows=[
                {
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
                }
            ],
        )
    )

    response = process_preflight(
        ProcessPreflightRequest(tax_year=2025, ruleset_id="DE-2025-v1.0", config={})
    )

    assert response.status == "success"
    assert response.data["counts"]["unclassified_events"] == 0
    assert response.data["warnings"] == []


def test_process_preflight_ignores_reference_integrations_by_default() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="blockpit_reference.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "source": "blockpit",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                    "event_type": "buy",
                }
            ],
        )
    )

    response = process_preflight(
        ProcessPreflightRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={})
    )

    assert response.status == "success"
    assert response.data["counts"]["raw_events_total"] == 1
    assert response.data["counts"]["effective_events_total"] == 0
    assert response.data["counts"]["tax_year_events"] == 0
    assert any(item["code"] == "tax_year_no_events" for item in response.data["blockers"])


def test_process_preflight_returns_guided_action_for_missing_valuation() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="preflight_unpriced.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "HNT",
                    "side": "in",
                    "amount": "1",
                    "event_type": "mining_reward",
                }
            ],
        )
    )

    response = process_preflight(
        ProcessPreflightRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={})
    )

    assert response.status == "success"
    warning = next(item for item in response.data["warnings"] if item["code"] == "valuation_coverage_incomplete")
    assert warning["action"]["target_review_tab"] == "transfers"
    assert warning["action"]["issue_search"] == "valuation"


def test_process_status_returns_created_job() -> None:
    _reset_store()
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]

    status = process_status(job_id)

    assert status.status == "success"
    assert status.data["job_id"] == job_id
    assert status.data["status"] == "queued"


def test_process_status_returns_error_for_unknown_job() -> None:
    _reset_store()

    status = process_status("does-not-exist")

    assert status.status == "error"
    assert status.errors[0]["code"] == "job_not_found"


def test_worker_run_next_completes_queued_job() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="test.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                    "fee_eur": "1",
                },
                {
                    "timestamp": "2026-02-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "sell",
                    "amount": "0.4",
                    "price_eur": "120",
                    "fee_eur": "0.4",
                },
                {
                    "timestamp": "2026-03-01T12:00:00Z",
                    "position_id": "d1",
                    "asset": "ETH",
                    "event_type": "derivative_open",
                    "collateral_eur": "300",
                    "fee_eur": "2",
                },
                {
                    "timestamp": "2026-03-03T12:00:00Z",
                    "position_id": "d1",
                    "asset": "ETH",
                    "event_type": "close",
                    "proceeds_eur": "250",
                    "fee_eur": "1",
                },
            ],
        )
    )
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]

    result = process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    status = process_status(job_id)
    tax_lines_response = process_tax_lines(job_id)
    derivative_lines_response = process_derivative_lines(job_id)
    report_files_response = report_files(job_id)

    assert result.status == "success"
    assert result.data["job_id"] == job_id
    assert result.data["status"] == "completed"
    assert result.data["progress"] == 100
    assert result.data["result_summary"] is not None
    assert result.data["result_summary"]["processed_events"] == 2
    assert result.data["result_summary"]["derivatives"]["processed_events"] == 2
    assert "tax_domain_summary" in result.data["result_summary"]
    assert "fx_enrichment" in result.data["result_summary"]
    assert result.data["result_summary"]["fx_enrichment"]["unresolved_count"] == 0
    assert "anlage_so" in result.data["result_summary"]["tax_domain_summary"]
    assert result.data["tax_line_count"] == 1
    assert result.data["derivative_line_count"] == 1
    tax_lines = STORE.get_tax_lines(job_id)
    derivative_lines = STORE.get_derivative_lines(job_id)
    assert len(tax_lines) == 1
    assert len(derivative_lines) == 1
    assert tax_lines[0]["asset"] == "BTC"
    assert derivative_lines[0]["asset"] == "ETH"
    assert tax_lines_response.status == "success"
    assert derivative_lines_response.status == "success"
    assert tax_lines_response.data["count"] == 1
    assert derivative_lines_response.data["count"] == 1
    assert report_files_response.status == "success"
    assert report_files_response.data["tax_line_count"] == 1
    assert report_files_response.data["derivative_line_count"] == 1
    file_scopes = {(item["scope"], item["format"]) for item in report_files_response.data["files"]}
    assert ("all", "json") in file_scopes
    assert ("all", "csv") in file_scopes
    assert ("all", "pdf") in file_scopes
    assert ("tax", "wiso") in file_scopes
    assert ("tax", "json") in file_scopes
    assert ("derivatives", "csv") in file_scopes
    pdf_response = report_export(job_id=job_id, scope="all", fmt="pdf")
    assert getattr(pdf_response, "media_type", "") == "application/pdf"
    pdf_body = asyncio.run(_read_streaming_body(pdf_response))
    assert pdf_body.startswith(b"%PDF")
    audit_response = audit_tax_line(job_id=job_id, line_no=1)
    assert audit_response.status == "success"
    assert audit_response.data["tax_line"]["line_no"] == 1
    assert audit_response.data["source_event"] is not None
    assert audit_response.data["calculation_trace"]["formula"] == "gain_loss_eur = proceeds_eur - cost_basis_eur"
    assert status.data["status"] == "completed"


def test_tax_domain_summary_endpoint_returns_split_blocks() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="tax_domains.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "IOT",
                    "event_type": "mining_reward",
                    "amount": "10",
                    "price_eur": "0.5",
                    "source": "heliumgeek",
                },
                {
                    "timestamp": "2026-01-02T12:00:00Z",
                    "asset": "DC",
                    "event_type": "data_credit_usage",
                    "amount_eur": "3",
                },
                {
                    "timestamp": "2026-01-03T12:00:00Z",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                },
                {
                    "timestamp": "2026-01-04T12:00:00Z",
                    "asset": "BTC",
                    "side": "sell",
                    "amount": "1",
                    "price_eur": "120",
                },
            ],
        )
    )
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))

    response = process_tax_domain_summary(job_id)
    assert response.status == "success"
    summary = response.data["tax_domain_summary"]
    assert summary["anlage_so"]["leistungen_income_eur"] == "0"
    assert summary["anlage_so"]["private_veraeusserung_net_taxable_eur"] == "20"
    assert summary["euer"]["betriebseinnahmen_mining_staking_eur"] == "5.0"
    assert summary["euer"]["betriebsausgaben_data_credits_eur"] == "3"


def test_process_compare_rulesets_post_matches_api_contract() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="compare.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                },
                {
                    "timestamp": "2026-01-02T12:00:00Z",
                    "asset": "BTC",
                    "side": "sell",
                    "amount": "1",
                    "price_eur": "120",
                },
            ],
        )
    )
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))

    response = process_compare_rulesets_post(
        ProcessCompareRulesetsRequest(
            job_id=job_id,
            compare_ruleset_id="DE-2026-v1.0",
            compare_ruleset_version="1.0",
        )
    )

    assert response.status == "success"
    assert response.data["job_id"] == job_id
    assert response.data["comparison"]["ruleset_id"] == "DE-2026-v1.0"


def test_tax_event_override_keeps_business_domain_assignment_auditable() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="tax_override.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "IOT",
                    "event_type": "mining_reward",
                    "amount": "10",
                    "price_eur": "0.5",
                    "source": "heliumgeek",
                }
            ],
        )
    )
    first_job = process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))
    first_job_id = first_job.data["job_id"]
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    first_summary = process_tax_domain_summary(first_job_id).data["tax_domain_summary"]
    assert first_summary["anlage_so"]["leistungen_income_eur"] == "0"
    assert first_summary["euer"]["betriebseinnahmen_mining_staking_eur"] == "5.0"

    event_id = STORE.list_raw_events()[0]["unique_event_id"]
    upsert_response = tax_event_override_upsert(
        TaxEventOverrideUpsertRequest(
            source_event_id=event_id,
            tax_category="BUSINESS",
            note="Mining als gewerblich klassifiziert",
        )
    )
    assert upsert_response.status == "success"

    second_job = process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))
    second_job_id = second_job.data["job_id"]
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    second_summary = process_tax_domain_summary(second_job_id).data["tax_domain_summary"]
    assert second_summary["anlage_so"]["leistungen_income_eur"] == "0"
    assert second_summary["euer"]["betriebseinnahmen_mining_staking_eur"] == "5.0"


def test_worker_run_next_can_fail_job() -> None:
    _reset_store()
    process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))

    result = process_worker_run_next(WorkerRunNextRequest(simulate_fail=True))

    assert result.status == "success"
    assert result.data["status"] == "failed"
    assert result.data["error_message"] == "Simulated worker error"


def test_worker_run_next_returns_warning_when_queue_empty() -> None:
    _reset_store()

    result = process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))

    assert result.status == "success"
    assert result.warnings[0]["code"] == "no_queued_job"


def test_audit_tax_line_not_found_returns_error() -> None:
    _reset_store()
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]
    response = audit_tax_line(job_id=job_id, line_no=1)
    assert response.status == "error"
    assert response.errors[0]["code"] == "tax_line_not_found"


def test_portfolio_lot_aging_shows_split_lots() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="lots.csv",
            rows=[
                {
                    "timestamp": "2025-01-01T00:00:00Z",
                    "asset": "SOL",
                    "side": "buy",
                    "amount": "3",
                    "price_eur": "100",
                },
                {
                    "timestamp": "2025-05-01T00:00:00Z",
                    "asset": "SOL",
                    "side": "buy",
                    "amount": "4",
                    "price_eur": "110",
                },
                {
                    "timestamp": "2026-03-01T00:00:00Z",
                    "asset": "SOL",
                    "side": "buy",
                    "amount": "8",
                    "price_eur": "120",
                },
            ],
        )
    )
    resp = portfolio_lot_aging(as_of_utc="2026-05-01T00:00:00Z", asset="SOL")
    assert resp.status == "success"
    rows = resp.data.get("lot_rows", [])
    assert len(rows) == 3
    qtys = sorted([row["qty"] for row in rows])
    assert qtys == ["3", "4", "8"]
    first = rows[0]
    assert "days_to_exempt" in first
    assert "holding_progress_ratio" in first
    assets = resp.data.get("assets", [])
    assert assets[0]["lot_count"] == 3
    assert assets[0]["qty_exempt"] == "7"
    assert assets[0]["qty_taxable"] == "8"


def test_portfolio_lot_aging_uses_known_solana_mint_symbols() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="solana-mint-lots.csv",
            rows=[
                {
                    "timestamp": "2025-01-01T00:00:00Z",
                    "asset": "2KFZCKFXJ1US8YRQZA5VKTSXY3GPZFZVVHWJ91N8FV2J",
                    "side": "buy",
                    "amount": "4202343.53",
                    "price_eur": "0",
                },
                {
                    "timestamp": "2025-01-01T00:00:00Z",
                    "asset": "SHARKSYJJQANYXVFRPNBN9PJGKHWDHATNMYICWPNR1S",
                    "side": "buy",
                    "amount": "963.536668",
                    "price_eur": "0",
                },
            ],
        )
    )

    resp = portfolio_lot_aging(as_of_utc="2026-05-01T00:00:00Z")

    assert resp.status == "success"
    assets = {row["asset"]: row["total_qty"] for row in resp.data.get("assets", [])}
    assert assets["CBDC"] == "4202343.53"
    assert assets["SHARK"] == "963.536668"
    assert "2KFZCK...FV2J" not in assets
    assert "SHARKS...NR1S" not in assets
