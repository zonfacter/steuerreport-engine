from __future__ import annotations

from decimal import Decimal

from tax_engine.connectors.solana_service import (
    fetch_solana_wallet_balances,
    fetch_solana_wallet_preview,
    probe_solana_rpc_endpoints,
)


def test_fetch_solana_wallet_preview_maps_sol_and_token_rows(monkeypatch) -> None:
    def _fake_rpc(**kwargs):
        method = kwargs["method"]
        if method == "getSignaturesForAddress":
            return [{"signature": "sig-1"}]
        if method == "getTransaction":
            return {
                "blockTime": 1704067200,
                "transaction": {
                    "message": {
                        "accountKeys": [{"pubkey": "wallet-1"}, {"pubkey": "other"}],
                    }
                },
                "meta": {
                    "fee": 5000,
                    "preBalances": [1000000000, 0],
                    "postBalances": [1500000000, 0],
                    "preTokenBalances": [
                        {
                            "owner": "wallet-1",
                            "mint": "mint-a",
                            "uiTokenAmount": {"uiAmountString": "1.0"},
                        }
                    ],
                    "postTokenBalances": [
                        {
                            "owner": "wallet-1",
                            "mint": "mint-a",
                            "uiTokenAmount": {"uiAmountString": "2.5"},
                        }
                    ],
                },
            }
        return None

    monkeypatch.setattr("tax_engine.connectors.solana_service._solana_rpc", _fake_rpc)

    result = fetch_solana_wallet_preview(
        wallet_address="wallet-1",
        rpc_url="https://rpc.test",
        rpc_fallback_urls=[],
        before_signature=None,
        timeout_seconds=10,
        max_signatures=10,
        max_transactions=10,
    )
    assert result["signature_count"] == 1
    assert result["count"] == 2
    assert any(row["asset"] == "SOL" for row in result["rows"])
    assert any(row["asset"] == "MINT-A" for row in result["rows"])
    assert all("defi_label" in row for row in result["rows"])


def test_fetch_solana_wallet_preview_aggregates_jupiter_multihop(monkeypatch) -> None:
    def _fake_rpc(**kwargs):
        method = kwargs["method"]
        if method == "getSignaturesForAddress":
            return [{"signature": "sig-1"}]
        if method == "getTransaction":
            return {
                "blockTime": 1704067200,
                "transaction": {
                    "message": {
                        "instructions": [{"programId": "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB"}],
                        "accountKeys": [{"pubkey": "wallet-1"}, {"pubkey": "other"}],
                    }
                },
                "meta": {
                    "fee": 5000,
                    "preBalances": [1000000000, 0],
                    "postBalances": [1000000000, 0],
                    "preTokenBalances": [
                        {"owner": "wallet-1", "mint": "SOL-MINT", "uiTokenAmount": {"uiAmountString": "10"}},
                        {"owner": "wallet-1", "mint": "USDC-MINT", "uiTokenAmount": {"uiAmountString": "0"}},
                        {"owner": "wallet-1", "mint": "JUP-MINT", "uiTokenAmount": {"uiAmountString": "0"}},
                    ],
                    "postTokenBalances": [
                        {"owner": "wallet-1", "mint": "SOL-MINT", "uiTokenAmount": {"uiAmountString": "8"}},
                        {"owner": "wallet-1", "mint": "USDC-MINT", "uiTokenAmount": {"uiAmountString": "1"}},
                        {"owner": "wallet-1", "mint": "JUP-MINT", "uiTokenAmount": {"uiAmountString": "0.5"}},
                    ],
                },
            }
        return None

    monkeypatch.setattr("tax_engine.connectors.solana_service._solana_rpc", _fake_rpc)

    result = fetch_solana_wallet_preview(
        wallet_address="wallet-1",
        rpc_url="https://rpc.test",
        rpc_fallback_urls=[],
        before_signature=None,
        timeout_seconds=10,
        max_signatures=10,
        max_transactions=10,
        aggregate_jupiter=True,
        jupiter_window_seconds=2,
    )
    assert result["count"] == 2
    event_types = {row["event_type"] for row in result["rows"]}
    assert "swap_out_aggregated" in event_types
    assert "swap_in_aggregated" in event_types
    assert all(row["defi_label"] == "swap" for row in result["rows"])


def test_fetch_solana_wallet_preview_labels_staking_from_logs(monkeypatch) -> None:
    def _fake_rpc(**kwargs):
        method = kwargs["method"]
        if method == "getSignaturesForAddress":
            return [{"signature": "sig-1"}]
        if method == "getTransaction":
            return {
                "blockTime": 1704067200,
                "transaction": {
                    "message": {
                        "accountKeys": [{"pubkey": "wallet-1"}],
                    }
                },
                "meta": {
                    "fee": 5000,
                    "preBalances": [1000000000],
                    "postBalances": [900000000],
                    "logMessages": ["Program log: Stake instruction: Delegate"],
                    "preTokenBalances": [],
                    "postTokenBalances": [],
                },
            }
        return None

    monkeypatch.setattr("tax_engine.connectors.solana_service._solana_rpc", _fake_rpc)

    result = fetch_solana_wallet_preview(
        wallet_address="wallet-1",
        rpc_url="https://rpc.test",
        rpc_fallback_urls=[],
        before_signature=None,
        timeout_seconds=10,
        max_signatures=10,
        max_transactions=10,
        aggregate_jupiter=False,
    )
    assert result["count"] >= 1
    assert any(row["defi_label"] == "staking" for row in result["rows"])


def test_fetch_solana_wallet_preview_retries_transaction_variants(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    def _fake_rpc(**kwargs):
        method = kwargs["method"]
        calls.append((method, kwargs["params"]))
        if method == "getSignaturesForAddress":
            return [{"signature": "sig-1"}]
        if method == "getTransaction":
            params = kwargs["params"]
            if isinstance(params, list) and len(params) == 2 and params[1] == {
                "encoding": "jsonParsed",
                "maxSupportedTransactionVersion": 0,
            }:
                return None
            return {
                "blockTime": 1704067200,
                "transaction": {
                    "message": {
                        "accountKeys": [{"pubkey": "wallet-1"}, {"pubkey": "other"}],
                    }
                },
                "meta": {
                    "fee": 5000,
                    "preBalances": [1000000000, 0],
                    "postBalances": [1000000000, 0],
                    "preTokenBalances": [],
                    "postTokenBalances": [],
                },
            }
        return None

    monkeypatch.setattr("tax_engine.connectors.solana_service._solana_rpc", _fake_rpc)

    result = fetch_solana_wallet_preview(
        wallet_address="wallet-1",
        rpc_url="https://rpc.test",
        rpc_fallback_urls=[],
        before_signature=None,
        timeout_seconds=10,
        max_signatures=10,
        max_transactions=10,
        aggregate_jupiter=False,
    )
    tx_calls = [params for method, params in calls if method == "getTransaction"]
    assert len(tx_calls) >= 2
    assert result["count"] >= 1


def test_probe_solana_rpc_endpoints_reports_status(monkeypatch) -> None:
    def _fake_rpc(**kwargs):
        endpoint = kwargs["rpc_url"]
        if endpoint == "https://bad.rpc":
            raise ValueError("rpc_unreachable")
        return 123456

    monkeypatch.setattr("tax_engine.connectors.solana_service._solana_rpc", _fake_rpc)

    result = probe_solana_rpc_endpoints(
        rpc_url="https://good.rpc",
        rpc_fallback_urls=["https://bad.rpc"],
        timeout_seconds=10,
    )

    assert result["probe_count"] >= 2
    assert result["ok_count"] >= 1
    assert result["first_working_endpoint"] == "https://good.rpc"


def test_fetch_solana_wallet_preview_paginates_signatures(monkeypatch) -> None:
    seen_before: list[str | None] = []

    def _fake_rpc(**kwargs):
        method = kwargs["method"]
        if method == "getSignaturesForAddress":
            params = kwargs["params"]
            cfg = params[1]
            before = cfg.get("before")
            seen_before.append(before)
            if before is None:
                return [{"signature": f"sig-{idx}"} for idx in range(1, 1001)]
            if before == "sig-1000":
                return [{"signature": "sig-1001"}]
            return []
        if method == "getTransaction":
            return {
                "blockTime": 1704067200,
                "transaction": {"message": {"accountKeys": [{"pubkey": "wallet-1"}]}},
                "meta": {
                    "fee": 5000,
                    "preBalances": [1000000000],
                    "postBalances": [1000000000],
                    "preTokenBalances": [],
                    "postTokenBalances": [],
                },
            }
        return None

    monkeypatch.setattr("tax_engine.connectors.solana_service._solana_rpc", _fake_rpc)

    result = fetch_solana_wallet_preview(
        wallet_address="wallet-1",
        rpc_url="https://rpc.test",
        rpc_fallback_urls=[],
        before_signature=None,
        timeout_seconds=10,
        max_signatures=1001,
        max_transactions=1001,
        aggregate_jupiter=False,
    )
    assert result["signature_count"] == 1001
    assert seen_before == [None, "sig-1000"]


def test_fetch_solana_wallet_balances_maps_sol_and_tokens(monkeypatch) -> None:
    def _fake_rpc(**kwargs):
        method = kwargs["method"]
        if method == "getBalance":
            return {"value": 1500000000}
        if method == "getTokenAccountsByOwner":
            return {
                "value": [
                    {
                        "pubkey": "token-1",
                        "account": {
                            "data": {
                                "parsed": {
                                    "info": {
                                        "mint": "mint-a",
                                        "tokenAmount": {"uiAmountString": "12.5"},
                                    }
                                }
                            }
                        },
                    }
                ]
            }
        return None

    monkeypatch.setattr("tax_engine.connectors.solana_service._solana_rpc", _fake_rpc)

    result = fetch_solana_wallet_balances(
        wallet_address="wallet-1",
        rpc_url="https://rpc.test",
        rpc_fallback_urls=[],
        timeout_seconds=10,
        max_tokens=100,
    )

    assert result["sol_balance"] == "1.5"
    assert result["token_count"] == 1
    assert result["tokens"][0]["asset"] == "MINT-A"


def test_fetch_solana_wallet_balances_includes_price_estimates(monkeypatch) -> None:
    def _fake_rpc(**kwargs):
        method = kwargs["method"]
        if method == "getBalance":
            return {"value": 2_000_000_000}
        if method == "getTokenAccountsByOwner":
            return {
                "value": [
                    {
                        "pubkey": "token-1",
                        "account": {
                            "data": {
                                "parsed": {
                                    "info": {
                                        "mint": "mint-a",
                                        "tokenAmount": {"uiAmountString": "10"},
                                    }
                                }
                            }
                        },
                    }
                ]
            }
        return None

    def _fake_prices(price_ids: list[str], timeout_seconds: int) -> dict[str, Decimal]:
        return {
            "So11111111111111111111111111111111111111112": Decimal("125"),
            "MINT-A": Decimal("2.5"),
        }

    monkeypatch.setattr("tax_engine.connectors.solana_service._solana_rpc", _fake_rpc)
    monkeypatch.setattr("tax_engine.connectors.solana_service._fetch_jupiter_prices_usd", _fake_prices)

    result = fetch_solana_wallet_balances(
        wallet_address="wallet-1",
        rpc_url="https://rpc.test",
        rpc_fallback_urls=[],
        timeout_seconds=10,
        max_tokens=100,
        include_prices=True,
    )

    assert result["price_source"] == "jupiter_v6"
    assert result["sol_usd_value"] == "250"
    assert result["tokens"][0]["usd_price"] == "2.5"
    assert result["tokens"][0]["usd_value"] == "25"
    assert result["total_estimated_usd"] == "275"


def test_fetch_solana_wallet_balances_uses_coingecko_fallback_for_sol(monkeypatch) -> None:
    def _fake_rpc(**kwargs):
        method = kwargs["method"]
        if method == "getBalance":
            return {"value": 1_000_000_000}
        if method == "getTokenAccountsByOwner":
            return {"value": []}
        return None

    monkeypatch.setattr("tax_engine.connectors.solana_service._solana_rpc", _fake_rpc)
    monkeypatch.setattr("tax_engine.connectors.solana_service._fetch_jupiter_prices_usd", lambda **_: {})
    monkeypatch.setattr(
        "tax_engine.connectors.solana_service._fetch_sol_price_coingecko",
        lambda timeout_seconds: Decimal("80"),
    )

    result = fetch_solana_wallet_balances(
        wallet_address="wallet-1",
        rpc_url="https://rpc.test",
        rpc_fallback_urls=[],
        timeout_seconds=10,
        max_tokens=100,
        include_prices=True,
    )

    assert result["price_source"] == "coingecko_fallback"
    assert result["sol_usd_price"] == "80"
    assert result["sol_usd_value"] == "80"
    assert result["total_estimated_usd"] == "80"
