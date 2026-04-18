from __future__ import annotations

import base64
import hashlib
import hmac
import time
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlencode

import httpx


def mask_api_key(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def build_binance_signature(query_string: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()


def build_bitget_signature(
    timestamp: str,
    method: str,
    request_path_with_query: str,
    body: str,
    secret: str,
) -> str:
    prehash = f"{timestamp}{method.upper()}{request_path_with_query}{body}"
    digest = hmac.new(secret.encode("utf-8"), prehash.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def build_coinbase_signature(
    timestamp: str,
    method: str,
    request_path: str,
    body: str,
    secret_base64: str,
) -> str:
    key = base64.b64decode(secret_base64)
    prehash = f"{timestamp}{method.upper()}{request_path}{body}"
    digest = hmac.new(key, prehash.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _safe_get_json(url: str, headers: dict[str, str], timeout_seconds: int) -> Any:
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


def verify_cex_credentials(
    connector_id: str,
    api_key: str,
    api_secret: str,
    passphrase: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    connector = connector_id.lower().strip()
    if connector == "binance":
        return _verify_binance(api_key, api_secret, timeout_seconds)
    if connector == "bitget":
        return _verify_bitget(api_key, api_secret, passphrase, timeout_seconds)
    if connector == "coinbase":
        return _verify_coinbase(api_key, api_secret, passphrase, timeout_seconds)
    return {"ok": False, "error_code": "unsupported_connector", "connector_id": connector}


def fetch_cex_balance_preview(
    connector_id: str,
    api_key: str,
    api_secret: str,
    passphrase: str | None,
    timeout_seconds: int,
    max_rows: int,
) -> dict[str, Any]:
    connector = connector_id.lower().strip()
    now_iso = datetime.now(UTC).isoformat()
    if connector == "binance":
        payload = _binance_account_payload(api_key, api_secret, timeout_seconds)
        balances = payload.get("balances", [])
        lines = []
        for item in balances:
            free = _to_decimal(item.get("free", "0"))
            locked = _to_decimal(item.get("locked", "0"))
            total = free + locked
            if total <= Decimal("0"):
                continue
            lines.append(
                {
                    "timestamp_utc": now_iso,
                    "asset": str(item.get("asset", "")).upper(),
                    "quantity": total.to_eng_string(),
                    "event_type": "balance_snapshot",
                    "source": "binance_api",
                }
            )
        return {"connector_id": connector, "count": len(lines[:max_rows]), "rows": lines[:max_rows]}

    if connector == "bitget":
        payload = _bitget_assets_payload(api_key, api_secret, passphrase, timeout_seconds)
        raw_items = payload.get("data", [])
        lines = []
        for item in raw_items:
            available = _to_decimal(item.get("available", "0"))
            frozen = _to_decimal(item.get("frozen", "0"))
            total = available + frozen
            if total <= Decimal("0"):
                continue
            lines.append(
                {
                    "timestamp_utc": now_iso,
                    "asset": str(item.get("coin", "")).upper(),
                    "quantity": total.to_eng_string(),
                    "event_type": "balance_snapshot",
                    "source": "bitget_api",
                }
            )
        return {"connector_id": connector, "count": len(lines[:max_rows]), "rows": lines[:max_rows]}

    if connector == "coinbase":
        payload = _coinbase_accounts_payload(api_key, api_secret, passphrase, timeout_seconds)
        if not isinstance(payload, list):
            raise ValueError("coinbase_invalid_payload")
        lines = []
        for item in payload:
            balance = _to_decimal(item.get("balance", "0"))
            if balance <= Decimal("0"):
                continue
            lines.append(
                {
                    "timestamp_utc": now_iso,
                    "asset": str(item.get("currency", "")).upper(),
                    "quantity": balance.to_eng_string(),
                    "event_type": "balance_snapshot",
                    "source": "coinbase_api",
                }
            )
        return {"connector_id": connector, "count": len(lines[:max_rows]), "rows": lines[:max_rows]}

    raise ValueError("unsupported_connector")


def fetch_cex_transactions_preview(
    connector_id: str,
    api_key: str,
    api_secret: str,
    passphrase: str | None,
    timeout_seconds: int,
    max_rows: int,
    start_time_ms: int | None,
    end_time_ms: int | None,
) -> dict[str, Any]:
    connector = connector_id.lower().strip()
    if connector == "binance":
        return _binance_transactions_preview(
            api_key=api_key,
            api_secret=api_secret,
            timeout_seconds=timeout_seconds,
            max_rows=max_rows,
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
        )
    if connector == "bitget":
        return _bitget_transactions_preview(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            timeout_seconds=timeout_seconds,
            max_rows=max_rows,
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
        )
    if connector == "coinbase":
        return _coinbase_transactions_preview(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            timeout_seconds=timeout_seconds,
            max_rows=max_rows,
        )
    raise ValueError("unsupported_connector")


def _verify_binance(api_key: str, api_secret: str, timeout_seconds: int) -> dict[str, Any]:
    payload = _binance_account_payload(api_key, api_secret, timeout_seconds)
    return {
        "ok": True,
        "connector_id": "binance",
        "account_type": payload.get("accountType", "SPOT"),
        "permissions": payload.get("permissions", []),
    }


def _verify_bitget(
    api_key: str, api_secret: str, passphrase: str | None, timeout_seconds: int
) -> dict[str, Any]:
    if not passphrase:
        return {
            "ok": False,
            "connector_id": "bitget",
            "error_code": "missing_passphrase",
        }
    payload = _bitget_assets_payload(api_key, api_secret, passphrase, timeout_seconds)
    code = str(payload.get("code", ""))
    if code != "00000":
        return {
            "ok": False,
            "connector_id": "bitget",
            "error_code": "bitget_api_error",
            "error_message": str(payload.get("msg", "unknown")),
        }
    return {"ok": True, "connector_id": "bitget", "account_items": len(payload.get("data", []))}


def _verify_coinbase(
    api_key: str, api_secret: str, passphrase: str | None, timeout_seconds: int
) -> dict[str, Any]:
    if not passphrase:
        return {
            "ok": False,
            "connector_id": "coinbase",
            "error_code": "missing_passphrase",
        }
    payload = _coinbase_accounts_payload(api_key, api_secret, passphrase, timeout_seconds)
    if not isinstance(payload, list):
        return {
            "ok": False,
            "connector_id": "coinbase",
            "error_code": "coinbase_api_error",
        }
    return {"ok": True, "connector_id": "coinbase", "account_items": len(payload)}


def _binance_account_payload(api_key: str, api_secret: str, timeout_seconds: int) -> dict[str, Any]:
    timestamp = str(int(time.time() * 1000))
    params = {"timestamp": timestamp, "recvWindow": "5000"}
    query = urlencode(params)
    signature = build_binance_signature(query, api_secret)
    signed_query = f"{query}&signature={signature}"
    url = f"https://api.binance.com/api/v3/account?{signed_query}"
    headers = {"X-MBX-APIKEY": api_key}
    payload = _safe_get_json(url=url, headers=headers, timeout_seconds=timeout_seconds)
    if not isinstance(payload, dict):
        raise ValueError("binance_invalid_payload")
    return payload


def _binance_signed_get(
    path: str,
    api_key: str,
    api_secret: str,
    timeout_seconds: int,
    params: dict[str, str] | None = None,
) -> Any:
    base_params = {"timestamp": str(int(time.time() * 1000)), "recvWindow": "5000"}
    if params:
        base_params.update(params)
    query = urlencode(base_params)
    signature = build_binance_signature(query, api_secret)
    signed_query = f"{query}&signature={signature}"
    url = f"https://api.binance.com{path}?{signed_query}"
    headers = {"X-MBX-APIKEY": api_key}
    return _safe_get_json(url=url, headers=headers, timeout_seconds=timeout_seconds)


def _binance_transactions_preview(
    api_key: str,
    api_secret: str,
    timeout_seconds: int,
    max_rows: int,
    start_time_ms: int | None,
    end_time_ms: int | None,
) -> dict[str, Any]:
    params: dict[str, str] = {}
    if start_time_ms is not None:
        params["startTime"] = str(start_time_ms)
    if end_time_ms is not None:
        params["endTime"] = str(end_time_ms)
    params["limit"] = str(min(max_rows, 1000))

    deposits_payload = _binance_signed_get(
        path="/sapi/v1/capital/deposit/hisrec",
        api_key=api_key,
        api_secret=api_secret,
        timeout_seconds=timeout_seconds,
        params=params,
    )
    withdrawals_payload = _binance_signed_get(
        path="/sapi/v1/capital/withdraw/history",
        api_key=api_key,
        api_secret=api_secret,
        timeout_seconds=timeout_seconds,
        params=params,
    )

    if not isinstance(deposits_payload, list) or not isinstance(withdrawals_payload, list):
        raise ValueError("binance_transactions_invalid_payload")

    rows: list[dict[str, Any]] = []

    for item in deposits_payload:
        insert_time = int(item.get("insertTime", 0) or 0)
        event_time = datetime.fromtimestamp(insert_time / 1000, tz=UTC).isoformat() if insert_time else None
        rows.append(
            {
                "timestamp_utc": event_time,
                "asset": str(item.get("coin", "")).upper(),
                "quantity": _to_decimal(item.get("amount", "0")).to_eng_string(),
                "price": "",
                "fee": "0",
                "fee_asset": "",
                "side": "in",
                "event_type": "deposit",
                "tx_id": str(item.get("txId", "")),
                "source": "binance_api",
                "raw_row": item,
            }
        )

    for item in withdrawals_payload:
        apply_time_raw = str(item.get("applyTime", ""))
        withdrawal_time: str | None = None
        try:
            # Binance liefert hier normalerweise UTC-String, den Python ISO-Parser versteht.
            parsed_time = datetime.fromisoformat(apply_time_raw.replace("Z", "+00:00"))
            if parsed_time.tzinfo is None:
                parsed_time = parsed_time.replace(tzinfo=UTC)
            withdrawal_time = parsed_time.astimezone(UTC).isoformat()
        except ValueError:
            withdrawal_time = apply_time_raw
        amount = _to_decimal(item.get("amount", "0"))
        fee = _to_decimal(item.get("transactionFee", "0"))
        rows.append(
            {
                "timestamp_utc": withdrawal_time,
                "asset": str(item.get("coin", "")).upper(),
                "quantity": amount.to_eng_string(),
                "price": "",
                "fee": fee.to_eng_string(),
                "fee_asset": str(item.get("coin", "")).upper(),
                "side": "out",
                "event_type": "withdrawal",
                "tx_id": str(item.get("txId", "")),
                "source": "binance_api",
                "raw_row": item,
            }
        )

    rows.sort(key=lambda r: str(r.get("timestamp_utc") or ""))
    limited_rows = rows[:max_rows]
    return {"connector_id": "binance", "count": len(limited_rows), "rows": limited_rows}


def _bitget_assets_payload(
    api_key: str, api_secret: str, passphrase: str | None, timeout_seconds: int
) -> dict[str, Any]:
    if not passphrase:
        raise ValueError("missing_passphrase")
    path = "/api/v2/spot/account/assets"
    timestamp = str(int(time.time() * 1000))
    signature = build_bitget_signature(
        timestamp=timestamp,
        method="GET",
        request_path_with_query=path,
        body="",
        secret=api_secret,
    )
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json",
    }
    payload = _safe_get_json(
        url=f"https://api.bitget.com{path}",
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    if not isinstance(payload, dict):
        raise ValueError("bitget_invalid_payload")
    return payload


def _bitget_signed_get(
    path: str,
    api_key: str,
    api_secret: str,
    passphrase: str | None,
    timeout_seconds: int,
    params: dict[str, str] | None = None,
) -> Any:
    if not passphrase:
        raise ValueError("missing_passphrase")
    query = urlencode(params or {})
    request_path_with_query = path if not query else f"{path}?{query}"
    timestamp = str(int(time.time() * 1000))
    signature = build_bitget_signature(
        timestamp=timestamp,
        method="GET",
        request_path_with_query=request_path_with_query,
        body="",
        secret=api_secret,
    )
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json",
    }
    url = f"https://api.bitget.com{request_path_with_query}"
    return _safe_get_json(url=url, headers=headers, timeout_seconds=timeout_seconds)


def _bitget_transactions_preview(
    api_key: str,
    api_secret: str,
    passphrase: str | None,
    timeout_seconds: int,
    max_rows: int,
    start_time_ms: int | None,
    end_time_ms: int | None,
) -> dict[str, Any]:
    if not passphrase:
        raise ValueError("missing_passphrase")
    now_ms = int(time.time() * 1000)
    default_start = now_ms - (90 * 24 * 60 * 60 * 1000)
    start_ms = start_time_ms if start_time_ms is not None else default_start
    end_ms = end_time_ms if end_time_ms is not None else now_ms

    base_params = {
        "startTime": str(start_ms),
        "endTime": str(end_ms),
        "limit": str(min(max_rows, 1000)),
    }

    deposit_payload = _bitget_signed_get(
        path="/api/v2/spot/wallet/deposit-records",
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
        timeout_seconds=timeout_seconds,
        params=base_params,
    )
    withdrawal_payload = _bitget_signed_get(
        path="/api/v2/spot/wallet/withdrawal-records",
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
        timeout_seconds=timeout_seconds,
        params=base_params,
    )
    fills_payload = _bitget_signed_get(
        path="/api/v2/spot/trade/fills",
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
        timeout_seconds=timeout_seconds,
        params=base_params,
    )

    rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []

    for payload_name, payload in (
        ("deposit", deposit_payload),
        ("withdrawal", withdrawal_payload),
        ("fills", fills_payload),
    ):
        if not isinstance(payload, dict):
            warnings.append({"code": f"{payload_name}_invalid_payload"})

    dep_items = deposit_payload.get("data", []) if isinstance(deposit_payload, dict) else []
    wdr_items = withdrawal_payload.get("data", []) if isinstance(withdrawal_payload, dict) else []
    fill_items = fills_payload.get("data", []) if isinstance(fills_payload, dict) else []

    for item in dep_items:
        coin = str(item.get("coin") or item.get("currency") or "").upper()
        amount = _to_decimal(item.get("size") or item.get("amount") or item.get("quantity") or "0")
        ts_raw = item.get("uTime") or item.get("cTime") or item.get("ts") or item.get("createTime")
        event_time = _to_utc_iso(ts_raw)
        rows.append(
            {
                "timestamp_utc": event_time,
                "asset": coin,
                "quantity": amount.to_eng_string(),
                "price": "",
                "fee": "0",
                "fee_asset": "",
                "side": "in",
                "event_type": "deposit",
                "tx_id": str(item.get("orderId") or item.get("txId") or item.get("id") or ""),
                "source": "bitget_api",
                "raw_row": item,
            }
        )

    for item in wdr_items:
        coin = str(item.get("coin") or item.get("currency") or "").upper()
        amount = _to_decimal(item.get("size") or item.get("amount") or item.get("quantity") or "0")
        fee = _to_decimal(item.get("fee") or item.get("withdrawFee") or "0")
        ts_raw = item.get("uTime") or item.get("cTime") or item.get("ts") or item.get("createTime")
        event_time = _to_utc_iso(ts_raw)
        rows.append(
            {
                "timestamp_utc": event_time,
                "asset": coin,
                "quantity": amount.to_eng_string(),
                "price": "",
                "fee": fee.to_eng_string(),
                "fee_asset": coin,
                "side": "out",
                "event_type": "withdrawal",
                "tx_id": str(item.get("orderId") or item.get("txId") or item.get("id") or ""),
                "source": "bitget_api",
                "raw_row": item,
            }
        )

    for item in fill_items:
        symbol = str(item.get("symbol") or "")
        side = str(item.get("side") or item.get("tradeSide") or "").lower()
        event_type = "trade"
        quantity = _to_decimal(
            item.get("size")
            or item.get("baseVolume")
            or item.get("fillQuantity")
            or item.get("amount")
            or "0"
        )
        price = _to_decimal(item.get("price") or item.get("priceAvg") or item.get("fillPrice") or "0")
        fee = _to_decimal(item.get("feeDetail") or item.get("fee") or "0")
        fee_coin = str(item.get("feeCoin") or item.get("feeCurrency") or "")
        ts_raw = item.get("fillTime") or item.get("cTime") or item.get("uTime") or item.get("ts")
        event_time = _to_utc_iso(ts_raw)
        rows.append(
            {
                "timestamp_utc": event_time,
                "asset": symbol,
                "quantity": quantity.to_eng_string(),
                "price": price.to_eng_string() if price else "",
                "fee": fee.to_eng_string(),
                "fee_asset": fee_coin.upper(),
                "side": side,
                "event_type": event_type,
                "tx_id": str(item.get("tradeId") or item.get("orderId") or item.get("id") or ""),
                "source": "bitget_api",
                "raw_row": item,
            }
        )

    rows.sort(key=lambda r: str(r.get("timestamp_utc") or ""))
    limited_rows = rows[:max_rows]
    return {
        "connector_id": "bitget",
        "count": len(limited_rows),
        "rows": limited_rows,
        "warnings": warnings,
    }


def _coinbase_accounts_payload(
    api_key: str, api_secret: str, passphrase: str | None, timeout_seconds: int
) -> Any:
    if not passphrase:
        raise ValueError("missing_passphrase")
    path = "/accounts"
    timestamp = str(int(time.time()))
    signature = build_coinbase_signature(
        timestamp=timestamp,
        method="GET",
        request_path=path,
        body="",
        secret_base64=api_secret,
    )
    headers = {
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "CB-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json",
    }
    return _safe_get_json(
        url=f"https://api.exchange.coinbase.com{path}",
        headers=headers,
        timeout_seconds=timeout_seconds,
    )


def _coinbase_signed_get(
    path: str,
    api_key: str,
    api_secret: str,
    passphrase: str | None,
    timeout_seconds: int,
    params: dict[str, str] | None = None,
) -> Any:
    if not passphrase:
        raise ValueError("missing_passphrase")
    query = urlencode(params or {})
    request_path = path if not query else f"{path}?{query}"
    timestamp = str(int(time.time()))
    signature = build_coinbase_signature(
        timestamp=timestamp,
        method="GET",
        request_path=request_path,
        body="",
        secret_base64=api_secret,
    )
    headers = {
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "CB-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json",
    }
    return _safe_get_json(
        url=f"https://api.exchange.coinbase.com{request_path}",
        headers=headers,
        timeout_seconds=timeout_seconds,
    )


def _coinbase_transactions_preview(
    api_key: str,
    api_secret: str,
    passphrase: str | None,
    timeout_seconds: int,
    max_rows: int,
) -> dict[str, Any]:
    if not passphrase:
        raise ValueError("missing_passphrase")
    accounts_payload = _coinbase_signed_get(
        path="/accounts",
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
        timeout_seconds=timeout_seconds,
    )
    fills_payload = _coinbase_signed_get(
        path="/fills",
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
        timeout_seconds=timeout_seconds,
        params={"limit": str(min(max_rows, 1000))},
    )
    rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []

    if not isinstance(accounts_payload, list):
        warnings.append({"code": "accounts_invalid_payload"})
        accounts_payload = []
    if not isinstance(fills_payload, list):
        warnings.append({"code": "fills_invalid_payload"})
        fills_payload = []

    for account in accounts_payload:
        account_id = str(account.get("id", ""))
        currency = str(account.get("currency", "")).upper()
        try:
            ledger_payload = _coinbase_signed_get(
                path=f"/accounts/{account_id}/ledger",
                api_key=api_key,
                api_secret=api_secret,
                passphrase=passphrase,
                timeout_seconds=timeout_seconds,
                params={"limit": "100"},
            )
        except Exception:
            warnings.append({"code": "ledger_fetch_failed", "account_id": account_id})
            continue
        if not isinstance(ledger_payload, list):
            warnings.append({"code": "ledger_invalid_payload", "account_id": account_id})
            continue
        for item in ledger_payload:
            ledger_type = str(item.get("type", "")).lower()
            if ledger_type not in {"transfer", "match", "fee"}:
                continue
            amount = _to_decimal(item.get("amount", "0"))
            side = "in" if amount >= 0 else "out"
            event_type = "transfer" if ledger_type == "transfer" else "trade"
            rows.append(
                {
                    "timestamp_utc": str(item.get("created_at") or ""),
                    "asset": currency,
                    "quantity": abs(amount).to_eng_string(),
                    "price": "",
                    "fee": "0",
                    "fee_asset": "",
                    "side": side,
                    "event_type": event_type,
                    "tx_id": str(item.get("id") or ""),
                    "source": "coinbase_api",
                    "raw_row": item,
                }
            )

    for fill in fills_payload:
        created_at = str(fill.get("created_at") or "")
        size = _to_decimal(fill.get("size") or fill.get("filled_size") or "0")
        price = _to_decimal(fill.get("price") or "0")
        fee = _to_decimal(fill.get("fee") or "0")
        side = str(fill.get("side") or "").lower()
        product = str(fill.get("product_id") or "")
        fee_currency = "USD"
        if "-" in product:
            fee_currency = product.split("-")[1]
        rows.append(
            {
                "timestamp_utc": created_at,
                "asset": product,
                "quantity": size.to_eng_string(),
                "price": price.to_eng_string() if price else "",
                "fee": fee.to_eng_string(),
                "fee_asset": fee_currency.upper(),
                "side": side,
                "event_type": "trade",
                "tx_id": str(fill.get("trade_id") or fill.get("order_id") or ""),
                "source": "coinbase_api",
                "raw_row": fill,
            }
        )

    rows.sort(key=lambda r: str(r.get("timestamp_utc") or ""))
    limited_rows = rows[:max_rows]
    return {
        "connector_id": "coinbase",
        "count": len(limited_rows),
        "rows": limited_rows,
        "warnings": warnings,
    }


def _to_utc_iso(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) or str(value).isdigit():
        ts = int(str(value))
        if ts > 9999999999:
            return datetime.fromtimestamp(ts / 1000, tz=UTC).isoformat()
        return datetime.fromtimestamp(ts, tz=UTC).isoformat()
    raw = str(value)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat()
    except ValueError:
        return raw
