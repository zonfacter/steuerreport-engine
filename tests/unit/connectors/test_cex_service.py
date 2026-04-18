from __future__ import annotations

from tax_engine.connectors.service import (
    build_binance_signature,
    build_bitget_signature,
    build_coinbase_signature,
    fetch_cex_transactions_preview,
    mask_api_key,
)


def test_mask_api_key_masks_middle() -> None:
    assert mask_api_key("ABCDEFGH12345678") == "ABCD...5678"
    assert mask_api_key("short") == "***"


def test_build_binance_signature_is_deterministic() -> None:
    query = "timestamp=1700000000000&recvWindow=5000"
    secret = "binance-secret"
    sig = build_binance_signature(query, secret)
    assert sig == "667e9d513983eff125cfc4da4737fa614a1c78f331030d88a71503ea0a34642b"


def test_build_bitget_signature_is_deterministic() -> None:
    sig = build_bitget_signature(
        timestamp="1700000000000",
        method="GET",
        request_path_with_query="/api/v2/spot/account/assets",
        body="",
        secret="bitget-secret",
    )
    assert sig == "DO71IuLoetAIyQWZISaZWEUsaOdpfsUPlTigRHUrMQQ="


def test_build_coinbase_signature_is_deterministic() -> None:
    sig = build_coinbase_signature(
        timestamp="1700000000",
        method="GET",
        request_path="/accounts",
        body="",
        secret_base64="MDEyMzQ1Njc4OWFiY2RlZg==",
    )
    assert sig == "ZlOfu0gXk6iGbZw972kqUDBNnxxSFZlJ9eomAg0HZ/g="


def test_fetch_cex_transactions_preview_binance_maps_deposit_and_withdrawal(monkeypatch) -> None:
    def _fake_signed_get(**kwargs):
        if kwargs["path"] == "/sapi/v1/capital/deposit/hisrec":
            return [
                {
                    "insertTime": 1704067200000,
                    "coin": "USDT",
                    "amount": "100.5",
                    "txId": "dep-1",
                }
            ]
        if kwargs["path"] == "/sapi/v1/capital/withdraw/history":
            return [
                {
                    "applyTime": "2024-01-02T10:00:00Z",
                    "coin": "BTC",
                    "amount": "0.01",
                    "transactionFee": "0.0001",
                    "txId": "wd-1",
                }
            ]
        return []

    monkeypatch.setattr("tax_engine.connectors.service._binance_signed_get", _fake_signed_get)

    result = fetch_cex_transactions_preview(
        connector_id="binance",
        api_key="key",
        api_secret="secret",
        passphrase=None,
        timeout_seconds=10,
        max_rows=100,
        start_time_ms=None,
        end_time_ms=None,
    )
    assert result["count"] == 2
    assert any(row["event_type"] == "deposit" for row in result["rows"])
    assert any(row["event_type"] == "withdrawal" for row in result["rows"])


def test_fetch_cex_transactions_preview_not_implemented_returns_warning() -> None:
    result = fetch_cex_transactions_preview(
        connector_id="bitget",
        api_key="key",
        api_secret="secret",
        passphrase="pass",
        timeout_seconds=10,
        max_rows=100,
        start_time_ms=None,
        end_time_ms=None,
    )
    assert result["count"] == 0
    assert result["warnings"][0]["code"] == "not_implemented"
