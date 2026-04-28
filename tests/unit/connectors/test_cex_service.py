from __future__ import annotations

import httpx

from tax_engine.connectors.service import (
    _safe_get_json,
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
    monkeypatch.setattr(
        "tax_engine.connectors.service._binance_fetch_asset_dividends",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        "tax_engine.connectors.service._binance_fetch_universal_transfers",
        lambda **kwargs: ([], []),
    )
    monkeypatch.setattr(
        "tax_engine.connectors.service._binance_fetch_dust_log",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        "tax_engine.connectors.service._binance_fetch_spot_trades",
        lambda **kwargs: ([], []),
    )

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


def test_fetch_cex_transactions_preview_binance_includes_trade_and_dividend_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        "tax_engine.connectors.service._binance_signed_get",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        "tax_engine.connectors.service._binance_fetch_asset_dividends",
        lambda **kwargs: [
            {
                "timestamp_utc": "2026-01-03T00:00:00+00:00",
                "asset": "BNB",
                "quantity": "1.5",
                "price": "",
                "fee": "0",
                "fee_asset": "",
                "side": "in",
                "event_type": "asset_dividend",
                "tx_id": "div-1",
                "source": "binance_api",
                "raw_row": {"id": 1},
            }
        ],
    )
    monkeypatch.setattr(
        "tax_engine.connectors.service._binance_fetch_universal_transfers",
        lambda **kwargs: ([], []),
    )
    monkeypatch.setattr(
        "tax_engine.connectors.service._binance_fetch_dust_log",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        "tax_engine.connectors.service._binance_fetch_spot_trades",
        lambda **kwargs: (
            [
                {
                    "timestamp_utc": "2026-01-04T00:00:00+00:00",
                    "asset": "BTCUSDT",
                    "quantity": "0.01",
                    "price": "40000",
                    "fee": "0.00001",
                    "fee_asset": "BNB",
                    "side": "buy",
                    "event_type": "trade",
                    "tx_id": "tr-1",
                    "source": "binance_api",
                    "raw_row": {"id": 1},
                }
            ],
            [],
        ),
    )

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
    event_types = {row["event_type"] for row in result["rows"]}
    assert "asset_dividend" in event_types
    assert "trade" in event_types


def test_fetch_cex_transactions_preview_unsupported_connector_raises() -> None:
    try:
        fetch_cex_transactions_preview(
            connector_id="unknown",
            api_key="key",
            api_secret="secret",
            passphrase="pass",
            timeout_seconds=10,
            max_rows=100,
            start_time_ms=None,
            end_time_ms=None,
        )
    except ValueError as exc:
        assert str(exc) == "unsupported_connector"
        return
    raise AssertionError("expected ValueError for unsupported connector")


def test_fetch_cex_transactions_preview_bitget_maps_data(monkeypatch) -> None:
    def _fake_bitget_signed_get(**kwargs):
        if kwargs["path"].endswith("deposit-records"):
            return {"code": "00000", "data": [{"coin": "USDT", "size": "50", "orderId": "dep-1", "cTime": "1704067200000"}]}
        if kwargs["path"].endswith("withdrawal-records"):
            return {"code": "00000", "data": [{"coin": "BTC", "amount": "0.01", "fee": "0.0001", "orderId": "wd-1", "cTime": "1704153600000"}]}
        return {"code": "00000", "data": [{"symbol": "BTCUSDT", "side": "Buy", "price": "40000", "size": "0.001", "tradeId": "tr-1", "cTime": "1704240000000"}]}

    monkeypatch.setattr("tax_engine.connectors.service._bitget_signed_get", _fake_bitget_signed_get)

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
    assert result["count"] == 3
    assert any(row["event_type"] == "deposit" for row in result["rows"])
    assert any(row["event_type"] == "withdrawal" for row in result["rows"])
    assert any(row["event_type"] == "trade" for row in result["rows"])


def test_fetch_cex_transactions_preview_coinbase_maps_data(monkeypatch) -> None:
    def _fake_coinbase_signed_get(**kwargs):
        path = kwargs["path"]
        if path == "/accounts":
            return [{"id": "acc-1", "currency": "BTC"}]
        if path == "/fills":
            return [{"created_at": "2026-01-01T00:00:00Z", "size": "0.01", "price": "40000", "fee": "1", "side": "buy", "product_id": "BTC-USD", "trade_id": "t-1"}]
        if path == "/accounts/acc-1/ledger":
            return [{"created_at": "2026-01-01T01:00:00Z", "id": "l-1", "amount": "0.5", "type": "transfer"}]
        return []

    monkeypatch.setattr("tax_engine.connectors.service._coinbase_signed_get", _fake_coinbase_signed_get)

    result = fetch_cex_transactions_preview(
        connector_id="coinbase",
        api_key="key",
        api_secret="MDEyMzQ1Njc4OWFiY2RlZg==",
        passphrase="pass",
        timeout_seconds=10,
        max_rows=100,
        start_time_ms=None,
        end_time_ms=None,
    )
    assert result["count"] == 2
    assert any(row["event_type"] == "transfer" for row in result["rows"])
    assert any(row["event_type"] == "trade" for row in result["rows"])


def test_safe_get_json_retries_on_429_then_succeeds(monkeypatch) -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.calls = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url, headers):
            self.calls += 1
            request = httpx.Request("GET", url)
            if self.calls == 1:
                response = httpx.Response(429, headers={"Retry-After": "0"}, request=request)
                raise httpx.HTTPStatusError("rate_limited", request=request, response=response)
            return httpx.Response(200, json={"ok": True}, request=request)

    fake_client = FakeClient()
    monkeypatch.setattr("tax_engine.connectors.service.httpx.Client", lambda timeout: fake_client)
    monkeypatch.setattr("tax_engine.connectors.service.time.sleep", lambda _: None)
    payload = _safe_get_json(url="https://example.test", headers={}, timeout_seconds=5, max_attempts=3)
    assert payload["ok"] is True
    assert fake_client.calls == 2


def test_safe_get_json_retries_on_timeout_then_succeeds(monkeypatch) -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.calls = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url, headers):
            self.calls += 1
            if self.calls == 1:
                raise httpx.TimeoutException("timeout")
            request = httpx.Request("GET", url)
            return httpx.Response(200, json={"ok": True}, request=request)

    fake_client = FakeClient()
    monkeypatch.setattr("tax_engine.connectors.service.httpx.Client", lambda timeout: fake_client)
    monkeypatch.setattr("tax_engine.connectors.service.time.sleep", lambda _: None)
    payload = _safe_get_json(url="https://example.test", headers={}, timeout_seconds=5, max_attempts=3)
    assert payload["ok"] is True
    assert fake_client.calls == 2
