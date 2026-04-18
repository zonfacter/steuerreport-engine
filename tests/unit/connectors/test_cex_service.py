from __future__ import annotations

from tax_engine.connectors.service import (
    build_binance_signature,
    build_bitget_signature,
    build_coinbase_signature,
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
