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
        timeout_seconds=10,
        max_signatures=10,
        max_transactions=10,
    )
    assert result["signature_count"] == 1
    assert result["count"] == 2
    assert any(row["asset"] == "SOL" for row in result["rows"])
    assert any(row["asset"] == "MINT-A" for row in result["rows"])
