from __future__ import annotations

from tax_engine.connectors.solana_service import fetch_solana_wallet_preview


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
        timeout_seconds=10,
        max_signatures=10,
        max_transactions=10,
        aggregate_jupiter=False,
    )
    assert result["count"] >= 1
    assert any(row["defi_label"] == "staking" for row in result["rows"])
