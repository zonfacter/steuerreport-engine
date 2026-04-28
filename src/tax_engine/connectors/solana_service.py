from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from threading import Lock
from time import sleep
from typing import Any

import httpx

from tax_engine.connectors.token_metadata import resolve_token_metadata

JUPITER_PROGRAM_IDS = {
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5NtJmQJ",
}
JUPITER_PRICE_URL = "https://price.jup.ag/v6/price"
WSOL_MINT = "So11111111111111111111111111111111111111112"
COINGECKO_SIMPLE_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"


@dataclass
class _RpcRateState:
    delay_seconds: float
    success_streak: int = 0
    backpressure_count: int = 0


class _AdaptiveRpcRateController:
    """AIMD-Regler: additive/milde Beschleunigung, harte Bremsung bei Rate-Limits."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._states: dict[str, _RpcRateState] = {}

    def delay_before_request(self, endpoint: str) -> float:
        with self._lock:
            state = self._state(endpoint)
            delay = state.delay_seconds
        sleep(delay)
        return delay

    def record_success(self, endpoint: str) -> None:
        with self._lock:
            state = self._state(endpoint)
            state.success_streak += 1
            if state.success_streak >= 10:
                state.delay_seconds = max(self._min_delay(endpoint), state.delay_seconds * 0.92)
                state.success_streak = 0

    def record_backpressure(self, endpoint: str, retry_after: float | None = None) -> float:
        with self._lock:
            state = self._state(endpoint)
            state.success_streak = 0
            state.backpressure_count += 1
            increased = max(state.delay_seconds * 1.8, state.delay_seconds + 0.2)
            if retry_after is not None and retry_after > 0:
                increased = max(increased, retry_after)
            state.delay_seconds = min(self._max_delay(endpoint), increased)
            return state.delay_seconds

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {
                endpoint: {
                    "delay_seconds": round(state.delay_seconds, 4),
                    "success_streak": state.success_streak,
                    "backpressure_count": state.backpressure_count,
                }
                for endpoint, state in self._states.items()
            }

    def _state(self, endpoint: str) -> _RpcRateState:
        if endpoint not in self._states:
            self._states[endpoint] = _RpcRateState(delay_seconds=self._initial_delay(endpoint))
        return self._states[endpoint]

    def _initial_delay(self, endpoint: str) -> float:
        if "solana-mainnet.gateway.tatum.io" in endpoint:
            return _env_float("SOLANA_RPC_TATUM_INITIAL_DELAY_SECONDS", 0.18)
        return _env_float("SOLANA_RPC_PUBLIC_INITIAL_DELAY_SECONDS", 0.26)

    def _min_delay(self, endpoint: str) -> float:
        if "solana-mainnet.gateway.tatum.io" in endpoint:
            return _env_float("SOLANA_RPC_TATUM_MIN_DELAY_SECONDS", 0.08)
        return _env_float("SOLANA_RPC_PUBLIC_MIN_DELAY_SECONDS", 0.20)

    def _max_delay(self, endpoint: str) -> float:
        if "solana-mainnet.gateway.tatum.io" in endpoint:
            return _env_float("SOLANA_RPC_TATUM_MAX_DELAY_SECONDS", 3.0)
        return _env_float("SOLANA_RPC_PUBLIC_MAX_DELAY_SECONDS", 5.0)


_RPC_RATE_CONTROLLER = _AdaptiveRpcRateController()


def fetch_solana_wallet_preview(
    wallet_address: str,
    rpc_url: str,
    rpc_fallback_urls: list[str] | None,
    before_signature: str | None,
    timeout_seconds: int,
    max_signatures: int,
    max_transactions: int,
    aggregate_jupiter: bool = True,
    jupiter_window_seconds: int = 2,
) -> dict[str, Any]:
    endpoints = _resolve_rpc_endpoints(primary=rpc_url, fallbacks=rpc_fallback_urls)
    signatures = _fetch_signatures_paginated(
        wallet_address=wallet_address,
        endpoints=endpoints,
        timeout_seconds=timeout_seconds,
        max_signatures=max_signatures,
        start_before_signature=before_signature,
    )[:max_transactions]

    rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []

    for signature in signatures:
        tx_payload = _fetch_transaction_with_fallbacks(
            rpc_url=endpoints,
            timeout_seconds=timeout_seconds,
            signature=signature,
        )
        if not isinstance(tx_payload, dict):
            warnings.append({"code": "transaction_invalid_payload", "signature": signature})
            continue
        tx_rows = _map_transaction_rows(wallet_address=wallet_address, signature=signature, tx=tx_payload)
        rows.extend(tx_rows)

    if aggregate_jupiter:
        rows = _aggregate_jupiter_rows(rows=rows, window_seconds=jupiter_window_seconds)

    rows.sort(key=lambda r: str(r.get("timestamp_utc") or ""))
    return {
        "wallet_address": wallet_address,
        "rpc_url": rpc_url,
        "rpc_endpoints": endpoints,
        "signature_count": len(signatures),
        "first_signature": signatures[0] if signatures else None,
        "last_signature": signatures[-1] if signatures else None,
        "count": len(rows),
        "rows": rows,
        "warnings": warnings,
    }


def fetch_solana_wallet_full_history(
    wallet_address: str,
    rpc_url: str,
    rpc_fallback_urls: list[str] | None,
    timeout_seconds: int,
    start_time_ms: int | None,
    end_time_ms: int | None,
    before_signature: str | None = None,
    max_signatures_per_call: int = 1000,
    max_signatures_total: int = 5000,
    aggregate_jupiter: bool = True,
    jupiter_window_seconds: int = 2,
) -> dict[str, Any]:
    endpoints = _resolve_rpc_endpoints(primary=rpc_url, fallbacks=rpc_fallback_urls)
    if max_signatures_per_call <= 0:
        max_signatures_per_call = 1000
    page_size_limit = min(max(1, max_signatures_per_call), 1000)

    start_cutoff = _to_epoch_seconds(start_time_ms) if start_time_ms is not None else None
    end_cutoff = _to_epoch_seconds(end_time_ms) if end_time_ms is not None else None

    rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    scanned_signatures: list[str] = []
    included_signatures: list[str] = []

    before: str | None = before_signature
    remaining = max_signatures_total
    reached_start = False

    while remaining > 0 and not reached_start:
        page: list[str] = _fetch_signatures_page(
            wallet_address=wallet_address,
            endpoints=endpoints,
            timeout_seconds=timeout_seconds,
            max_signatures=page_size_limit,
            before=before,
        )
        if not page:
            break

        for signature in page:
            if len(scanned_signatures) >= max_signatures_total:
                break
            scanned_signatures.append(signature)

            tx_payload = _fetch_transaction_with_fallbacks(
                rpc_url=endpoints,
                timeout_seconds=timeout_seconds,
                signature=signature,
            )
            if not isinstance(tx_payload, dict):
                warnings.append({"code": "transaction_invalid_payload", "signature": signature})
                continue

            block_time = tx_payload.get("blockTime")
            tx_epoch = _to_epoch_seconds(block_time)

            if tx_epoch is not None:
                if end_cutoff is not None and tx_epoch > end_cutoff:
                    continue
                if start_cutoff is not None and tx_epoch < start_cutoff:
                    reached_start = True
                    break

                included_signatures.append(signature)
            else:
                # Wir können den Blockzeitpunkt nicht prüfen. Event trotzdem aufnehmen,
                # aber mit Warnung versehen.
                included_signatures.append(signature)
                warnings.append(
                    {
                        "code": "missing_block_time",
                        "signature": signature,
                        "message": "blockTime fehlt im RPC-Transaction; Zeitfilter konnte nicht angewendet werden",
                    }
                )

            tx_rows = _map_transaction_rows(wallet_address=wallet_address, signature=signature, tx=tx_payload)
            rows.extend(tx_rows)

        before = page[-1]
        remaining = max_signatures_total - len(scanned_signatures)

    if aggregate_jupiter:
        rows = _aggregate_jupiter_rows(rows=rows, window_seconds=jupiter_window_seconds)

    rows.sort(key=lambda r: str(r.get("timestamp_utc") or ""))
    return {
        "wallet_address": wallet_address,
        "rpc_url": rpc_url,
        "rpc_endpoints": endpoints,
        "signature_count": len(included_signatures),
        "signature_scanned_count": len(scanned_signatures),
        "first_signature": scanned_signatures[0] if scanned_signatures else None,
        "last_signature": scanned_signatures[-1] if scanned_signatures else None,
        "next_before_signature": (scanned_signatures[-1] if scanned_signatures else None),
        "reached_start": reached_start,
        "start_time_ms": start_time_ms,
        "end_time_ms": end_time_ms,
        "count": len(rows),
        "rows": rows,
        "warnings": warnings,
    }


def _fetch_signatures_page(
    wallet_address: str,
    endpoints: list[str],
    timeout_seconds: int,
    max_signatures: int,
    before: str | None,
) -> list[str]:
    payload = _solana_rpc(
        rpc_url=endpoints,
        timeout_seconds=timeout_seconds,
        method="getSignaturesForAddress",
        params=[
            wallet_address,
            {
                "limit": max_signatures,
                **({"before": before} if before else {}),
            },
        ],
        allow_null_result=False,
    )
    if not isinstance(payload, list):
        raise ValueError("solana_signatures_invalid_payload")
    signatures: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        signature = str(item.get("signature", "")).strip()
        if signature:
            signatures.append(signature)
    return signatures


def _fetch_signatures_paginated(
    wallet_address: str,
    endpoints: list[str],
    timeout_seconds: int,
    max_signatures: int,
    start_before_signature: str | None = None,
) -> list[str]:
    collected: list[str] = []
    seen: set[str] = set()
    before: str | None = start_before_signature
    remaining = max_signatures

    while remaining > 0:
        page_size = min(1000, remaining)
        params_cfg: dict[str, Any] = {"limit": page_size}
        if before:
            params_cfg["before"] = before

        payload = _solana_rpc(
            rpc_url=endpoints,
            timeout_seconds=timeout_seconds,
            method="getSignaturesForAddress",
            params=[wallet_address, params_cfg],
            allow_null_result=False,
        )
        if not isinstance(payload, list):
            raise ValueError("solana_signatures_invalid_payload")
        if not payload:
            break

        page_signatures: list[str] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            signature = str(item.get("signature", "")).strip()
            if not signature or signature in seen:
                continue
            seen.add(signature)
            page_signatures.append(signature)

        if not page_signatures:
            break

        collected.extend(page_signatures)
        remaining = max_signatures - len(collected)
        before = page_signatures[-1]
        if len(page_signatures) < page_size:
            break

    return collected[:max_signatures]


def probe_solana_rpc_endpoints(
    rpc_url: str,
    rpc_fallback_urls: list[str] | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    endpoints = _resolve_rpc_endpoints(primary=rpc_url, fallbacks=rpc_fallback_urls)
    results: list[dict[str, Any]] = []
    for endpoint in endpoints:
        try:
            block_height = _solana_rpc(
                rpc_url=endpoint,
                timeout_seconds=timeout_seconds,
                method="getBlockHeight",
                params=[],
                allow_null_result=False,
            )
            if isinstance(block_height, int):
                results.append(
                    {
                        "endpoint": endpoint,
                        "ok": True,
                        "block_height": block_height,
                        "error": "",
                    }
                )
            else:
                results.append(
                    {
                        "endpoint": endpoint,
                        "ok": False,
                        "block_height": None,
                        "error": "invalid_block_height_payload",
                    }
                )
        except Exception as exc:
            results.append(
                {
                    "endpoint": endpoint,
                    "ok": False,
                    "block_height": None,
                    "error": str(exc),
                }
            )
    working = [item for item in results if item.get("ok")]
    return {
        "rpc_url": rpc_url,
        "rpc_endpoints": endpoints,
        "probe_count": len(results),
        "ok_count": len(working),
        "first_working_endpoint": working[0]["endpoint"] if working else None,
        "results": results,
    }


def fetch_solana_wallet_balances(
    wallet_address: str,
    rpc_url: str,
    rpc_fallback_urls: list[str] | None,
    timeout_seconds: int,
    max_tokens: int,
    include_prices: bool = False,
) -> dict[str, Any]:
    endpoints = _resolve_rpc_endpoints(primary=rpc_url, fallbacks=rpc_fallback_urls)

    sol_balance_lamports = _solana_rpc(
        rpc_url=endpoints,
        timeout_seconds=timeout_seconds,
        method="getBalance",
        params=[wallet_address],
        allow_null_result=False,
    )
    if not isinstance(sol_balance_lamports, dict):
        raise ValueError("solana_balance_invalid_payload")
    lamports = _to_decimal(sol_balance_lamports.get("value", "0"))
    sol_amount = (lamports / Decimal("1000000000")).normalize()

    token_accounts = _solana_rpc(
        rpc_url=endpoints,
        timeout_seconds=timeout_seconds,
        method="getTokenAccountsByOwner",
        params=[
            wallet_address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"},
        ],
        allow_null_result=False,
    )
    token_rows = []
    if isinstance(token_accounts, dict):
        token_value = token_accounts.get("value", [])
        if isinstance(token_value, list):
            for item in token_value:
                if not isinstance(item, dict):
                    continue
                account = item.get("account", {})
                data = account.get("data", {}) if isinstance(account, dict) else {}
                parsed = data.get("parsed", {}) if isinstance(data, dict) else {}
                info = parsed.get("info", {}) if isinstance(parsed, dict) else {}
                mint = str(info.get("mint", "")).upper()
                token_amount = info.get("tokenAmount", {}) if isinstance(info, dict) else {}
                qty_raw = token_amount.get("uiAmountString") or token_amount.get("uiAmount") or "0"
                qty = _to_decimal(qty_raw)
                if not mint:
                    continue
                if qty == 0:
                    continue
                meta = resolve_token_metadata(mint)
                token_rows.append(
                    {
                        "asset": mint,
                        "symbol": str(meta["symbol"]),
                        "name": str(meta["name"]),
                        "quantity": qty.to_eng_string(),
                        "account_pubkey": str(item.get("pubkey", "")),
                    }
                )

    token_rows.sort(key=lambda row: _to_decimal(row.get("quantity", "0")), reverse=True)
    token_rows = token_rows[:max_tokens]

    total_estimated_usd = Decimal("0")
    priced_token_count = 0
    price_source = "none"
    sol_price = Decimal("0")
    sol_value = Decimal("0")
    if include_prices:
        price_ids = [WSOL_MINT, *(row["asset"] for row in token_rows)]
        price_map = _fetch_jupiter_prices_usd(price_ids=price_ids, timeout_seconds=timeout_seconds)
        if price_map:
            price_source = "jupiter_v6"
        if WSOL_MINT not in price_map:
            coingecko_sol_price = _fetch_sol_price_coingecko(timeout_seconds=timeout_seconds)
            if coingecko_sol_price > 0:
                price_map[WSOL_MINT] = coingecko_sol_price
                price_source = (
                    "coingecko_fallback" if price_source == "none" else f"{price_source}+coingecko_fallback"
                )
        sol_price = price_map.get(WSOL_MINT, Decimal("0"))
        sol_value = (sol_amount * sol_price) if sol_price > 0 else Decimal("0")
        total_estimated_usd += sol_value
        for row in token_rows:
            asset = str(row.get("asset") or "")
            qty = _to_decimal(row.get("quantity"))
            price = price_map.get(asset, Decimal("0"))
            usd_value = qty * price if price > 0 else Decimal("0")
            if price > 0:
                priced_token_count += 1
            row["usd_price"] = price.normalize().to_eng_string() if price > 0 else ""
            row["usd_value"] = usd_value.normalize().to_eng_string() if usd_value > 0 else ""
            total_estimated_usd += usd_value

    return {
        "wallet_address": wallet_address,
        "rpc_url": rpc_url,
        "rpc_endpoints": endpoints,
        "sol_balance": sol_amount.to_eng_string(),
        "sol_usd_price": sol_price.normalize().to_eng_string() if include_prices and sol_price > 0 else "",
        "sol_usd_value": sol_value.normalize().to_eng_string() if include_prices and sol_value > 0 else "",
        "token_count": len(token_rows),
        "priced_token_count": priced_token_count,
        "price_source": price_source,
        "total_estimated_usd": total_estimated_usd.normalize().to_eng_string()
        if include_prices and total_estimated_usd > 0
        else "",
        "tokens": token_rows,
    }


def _fetch_jupiter_prices_usd(price_ids: list[str], timeout_seconds: int) -> dict[str, Decimal]:
    # Öffentlicher Preisfeed ohne API-Key; kann jederzeit ratenlimitiert sein.
    normalized_ids: list[str] = []
    for value in price_ids:
        item = str(value).strip()
        if not item:
            continue
        if item not in normalized_ids:
            normalized_ids.append(item)
    if not normalized_ids:
        return {}

    result: dict[str, Decimal] = {}
    chunk_size = 100
    with httpx.Client(timeout=timeout_seconds) as client:
        for idx in range(0, len(normalized_ids), chunk_size):
            chunk = normalized_ids[idx : idx + chunk_size]
            try:
                response = client.get(JUPITER_PRICE_URL, params={"ids": ",".join(chunk)})
                response.raise_for_status()
                payload = response.json()
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            data = payload.get("data")
            if not isinstance(data, dict):
                continue
            for mint, item in data.items():
                if not isinstance(item, dict):
                    continue
                price = _to_decimal(item.get("price"))
                if price > 0:
                    result[str(mint).strip()] = price
    return result


def _fetch_sol_price_coingecko(timeout_seconds: int) -> Decimal:
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.get(
                COINGECKO_SIMPLE_PRICE_URL,
                params={"ids": "solana", "vs_currencies": "usd"},
            )
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return Decimal("0")
    if not isinstance(payload, dict):
        return Decimal("0")
    solana = payload.get("solana")
    if not isinstance(solana, dict):
        return Decimal("0")
    return _to_decimal(solana.get("usd"))


def _solana_rpc(
    rpc_url: str | list[str],
    timeout_seconds: int,
    method: str,
    params: list[Any],
    allow_null_result: bool = True,
) -> Any:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    endpoints = [rpc_url] if isinstance(rpc_url, str) else list(rpc_url)
    last_error = "unknown"
    max_attempts_per_endpoint = 3
    with httpx.Client(timeout=timeout_seconds) as client:
        for endpoint in endpoints:
            for attempt in range(max_attempts_per_endpoint):
                try:
                    _RPC_RATE_CONTROLLER.delay_before_request(endpoint)
                    response = client.post(endpoint, json=payload, headers=_rpc_headers(endpoint))
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPStatusError as exc:
                    status_code = exc.response.status_code
                    # Öffentliche RPCs liefern häufig 429/403; Retry auf gleichem Endpoint vor Fallback.
                    if status_code in {403, 408, 429} or status_code >= 500:
                        last_error = f"{status_code} on {endpoint}"
                        retry_after = _parse_retry_after(exc.response.headers.get("Retry-After"))
                        backoff = _RPC_RATE_CONTROLLER.record_backpressure(endpoint, retry_after=retry_after)
                        if attempt < max_attempts_per_endpoint - 1:
                            sleep(max(backoff, 0.2 * (attempt + 1)))
                            continue
                        sleep(backoff)
                        break
                    raise
                if not isinstance(data, dict):
                    last_error = f"invalid_payload on {endpoint}"
                    if attempt < max_attempts_per_endpoint - 1:
                        sleep(0.1)
                        continue
                    continue
                error = data.get("error")
                if error:
                    retryable = _is_retryable_rpc_error(error)
                    last_error = f"rpc_error on {endpoint}: {error}"
                    if retryable and attempt < max_attempts_per_endpoint - 1:
                        backoff = _RPC_RATE_CONTROLLER.record_backpressure(endpoint)
                        sleep(max(backoff, 0.2 * (attempt + 1)))
                        continue
                    continue
                result = data.get("result")
                if result is None and not allow_null_result:
                    last_error = f"null_result on {endpoint}"
                    if attempt < max_attempts_per_endpoint - 1:
                        sleep(0.1)
                        continue
                    continue
                _RPC_RATE_CONTROLLER.record_success(endpoint)
                return result
    raise ValueError(f"solana_rpc_all_endpoints_failed:{last_error}")


def _rpc_headers(endpoint: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    # Provider-Keys bleiben außerhalb von URL, UI und Audit-Log.
    if "solana-mainnet.gateway.tatum.io" in endpoint:
        tatum_key = os.getenv("TATUM_API_KEY", "").strip()
        if tatum_key:
            headers["x-api-key"] = tatum_key
    return headers


def solana_rpc_rate_snapshot() -> dict[str, dict[str, Any]]:
    return _RPC_RATE_CONTROLLER.snapshot()


def _parse_retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value.strip())
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        parsed = float(raw)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _fetch_transaction_with_fallbacks(
    rpc_url: str | list[str],
    timeout_seconds: int,
    signature: str,
) -> dict[str, Any] | None:
    params_variants = [
        [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
        [signature, {"encoding": "jsonParsed"}],
        [signature, {"encoding": "json"}],
    ]
    for params in params_variants:
        try:
            result = _solana_rpc(
                rpc_url=rpc_url,
                timeout_seconds=timeout_seconds,
                method="getTransaction",
                params=params,
                allow_null_result=False,
            )
        except ValueError:
            continue
        if isinstance(result, dict):
            return result
    return None


def _is_retryable_rpc_error(error: Any) -> bool:
    if not isinstance(error, dict):
        return False
    code = error.get("code")
    message = str(error.get("message", "")).lower()
    retryable_codes = {
        -32005,  # Node is behind / not available
        -32004,  # Block not available
        -32603,  # Internal error
    }
    if isinstance(code, int) and code in retryable_codes:
        return True
    return "rate limit" in message or "too many requests" in message


def _map_transaction_rows(wallet_address: str, signature: str, tx: dict[str, Any]) -> list[dict[str, Any]]:
    block_time = tx.get("blockTime")
    timestamp_utc = _to_utc_iso(block_time)
    meta = tx.get("meta", {}) if isinstance(tx.get("meta"), dict) else {}
    transaction = tx.get("transaction", {}) if isinstance(tx.get("transaction"), dict) else {}
    message = transaction.get("message", {}) if isinstance(transaction.get("message"), dict) else {}
    account_keys = message.get("accountKeys", [])
    defi_label = _classify_defi_label(tx)

    wallet_index = _find_wallet_index(wallet_address=wallet_address, account_keys=account_keys)
    fee_lamports = _to_decimal(meta.get("fee", 0))
    fee_sol = (fee_lamports / Decimal("1000000000")).normalize() if fee_lamports else Decimal("0")

    rows: list[dict[str, Any]] = []

    if wallet_index is not None:
        pre_balances = meta.get("preBalances", [])
        post_balances = meta.get("postBalances", [])
        pre_lamports = _safe_list_decimal(pre_balances, wallet_index)
        post_lamports = _safe_list_decimal(post_balances, wallet_index)
        if pre_lamports is not None and post_lamports is not None:
            diff_lamports = post_lamports - pre_lamports
            diff_sol = (diff_lamports / Decimal("1000000000")).normalize()
            if diff_sol != 0 or fee_sol != 0:
                rows.append(
                    {
                        "timestamp_utc": timestamp_utc,
                        "wallet_address": wallet_address,
                        "asset": "SOL",
                        "quantity": abs(diff_sol).to_eng_string(),
                        "price": "",
                        "fee": fee_sol.to_eng_string(),
                        "fee_asset": "SOL",
                        "side": "in" if diff_sol > 0 else "out",
                        "event_type": "sol_transfer",
                        "defi_label": defi_label,
                        "tx_id": signature,
                        "source": "solana_rpc",
                        "raw_row": tx,
                    }
                )

    token_rows = _map_token_balance_diffs(
        wallet_address=wallet_address,
        signature=signature,
        timestamp_utc=timestamp_utc,
        meta=meta,
        defi_label=defi_label,
        raw_tx=tx,
    )
    rows.extend(token_rows)

    if not rows:
        rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "wallet_address": wallet_address,
                "asset": "SOL",
                "quantity": "0",
                "price": "",
                "fee": fee_sol.to_eng_string(),
                "fee_asset": "SOL",
                "side": "neutral",
                "event_type": "solana_tx",
                "defi_label": defi_label,
                "tx_id": signature,
                "source": "solana_rpc",
                "raw_row": tx,
            }
        )
    return rows


def _map_token_balance_diffs(
    wallet_address: str,
    signature: str,
    timestamp_utc: str | None,
    meta: dict[str, Any],
    defi_label: str,
    raw_tx: dict[str, Any],
) -> list[dict[str, Any]]:
    pre = meta.get("preTokenBalances", [])
    post = meta.get("postTokenBalances", [])
    if not isinstance(pre, list) or not isinstance(post, list):
        return []

    pre_by_key: dict[tuple[str, str], Decimal] = {}
    post_by_key: dict[tuple[str, str], Decimal] = {}

    for item in pre:
        if not isinstance(item, dict):
            continue
        owner = str(item.get("owner", ""))
        mint = str(item.get("mint", "")).upper()
        if owner != wallet_address or not mint:
            continue
        amount = _token_ui_amount(item)
        pre_by_key[(owner, mint)] = amount

    for item in post:
        if not isinstance(item, dict):
            continue
        owner = str(item.get("owner", ""))
        mint = str(item.get("mint", "")).upper()
        if owner != wallet_address or not mint:
            continue
        amount = _token_ui_amount(item)
        post_by_key[(owner, mint)] = amount

    keys = set(pre_by_key.keys()) | set(post_by_key.keys())
    rows: list[dict[str, Any]] = []
    for key in keys:
        owner, mint = key
        diff = post_by_key.get(key, Decimal("0")) - pre_by_key.get(key, Decimal("0"))
        if diff == 0:
            continue
        rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "wallet_address": wallet_address,
                "asset": mint,
                "quantity": abs(diff).to_eng_string(),
                "price": "",
                "fee": "0",
                "fee_asset": "",
                "side": "in" if diff > 0 else "out",
                "event_type": "token_transfer",
                "defi_label": defi_label,
                "tx_id": signature,
                "source": "solana_rpc",
                "raw_row": raw_tx,
            }
        )
    return rows


def _aggregate_jupiter_rows(rows: list[dict[str, Any]], window_seconds: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    passthrough: list[dict[str, Any]] = []

    for row in rows:
        tx_id = str(row.get("tx_id") or "")
        if tx_id:
            group_key = f"tx:{tx_id}"
        else:
            ts = _to_epoch_seconds(row.get("timestamp_utc"))
            if ts is None:
                passthrough.append(row)
                continue
            bucket = ts // max(window_seconds, 1)
            group_key = f"time:{bucket}"
        grouped.setdefault(group_key, []).append(row)

    aggregated_rows: list[dict[str, Any]] = []

    for group_rows in grouped.values():
        token_rows = [
            r for r in group_rows if str(r.get("event_type", "")).lower() == "token_transfer"
        ]
        if not token_rows:
            aggregated_rows.extend(group_rows)
            continue

        out_by_asset: dict[str, Decimal] = {}
        in_by_asset: dict[str, Decimal] = {}
        fee_total = Decimal("0")
        tx_id = str(group_rows[0].get("tx_id") or "")
        timestamp_utc = group_rows[0].get("timestamp_utc")
        source = group_rows[0].get("source", "solana_rpc")
        labels = {str(r.get("defi_label", "unknown")) for r in group_rows}
        group_label = "swap" if "swap" in labels else next(iter(labels), "unknown")

        for row in group_rows:
            fee_total += _to_decimal(row.get("fee", "0"))
            if str(row.get("event_type", "")).lower() != "token_transfer":
                continue
            asset = str(row.get("asset", "")).upper()
            qty = _to_decimal(row.get("quantity", "0"))
            side = str(row.get("side", "")).lower()
            if side == "out":
                out_by_asset[asset] = out_by_asset.get(asset, Decimal("0")) + qty
            elif side == "in":
                in_by_asset[asset] = in_by_asset.get(asset, Decimal("0")) + qty

        # Nur aggregieren, wenn sowohl Input als auch Output existieren.
        if not out_by_asset or not in_by_asset:
            aggregated_rows.extend(group_rows)
            continue

        out_asset, out_qty = max(out_by_asset.items(), key=lambda item: item[1])
        in_asset, in_qty = max(in_by_asset.items(), key=lambda item: item[1])

        raw_summary = {
            "jupiter_aggregated": True,
            "window_seconds": window_seconds,
            "aggregated_sub_events": len(group_rows),
            "from_asset": out_asset,
            "from_quantity": out_qty.to_eng_string(),
            "to_asset": in_asset,
            "to_quantity": in_qty.to_eng_string(),
        }

        aggregated_rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "asset": out_asset,
                "quantity": out_qty.to_eng_string(),
                "price": "",
                "fee": fee_total.to_eng_string(),
                "fee_asset": "SOL",
                "side": "out",
                "event_type": "swap_out_aggregated",
                "defi_label": group_label,
                "tx_id": tx_id,
                "source": source,
                "raw_row": raw_summary,
            }
        )
        aggregated_rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "asset": in_asset,
                "quantity": in_qty.to_eng_string(),
                "price": "",
                "fee": "0",
                "fee_asset": "",
                "side": "in",
                "event_type": "swap_in_aggregated",
                "defi_label": group_label,
                "tx_id": tx_id,
                "source": source,
                "raw_row": raw_summary,
            }
        )

    aggregated_rows.extend(passthrough)
    return aggregated_rows


def _token_ui_amount(item: dict[str, Any]) -> Decimal:
    ui_amount = item.get("uiTokenAmount", {})
    if not isinstance(ui_amount, dict):
        return Decimal("0")
    raw = ui_amount.get("uiAmountString") or ui_amount.get("uiAmount") or "0"
    return _to_decimal(raw)


def _find_wallet_index(wallet_address: str, account_keys: Any) -> int | None:
    if not isinstance(account_keys, list):
        return None
    for idx, key in enumerate(account_keys):
        if isinstance(key, dict):
            pubkey = str(key.get("pubkey", ""))
            if pubkey == wallet_address:
                return idx
            continue
        if str(key) == wallet_address:
            return idx
    return None


def _safe_list_decimal(values: Any, index: int) -> Decimal | None:
    if not isinstance(values, list):
        return None
    if index < 0 or index >= len(values):
        return None
    return _to_decimal(values[index])


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


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


def _to_epoch_seconds(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) or str(value).isdigit():
        ts = int(str(value))
        if ts > 9999999999:
            return ts // 1000
        return ts
    raw = str(value)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return int(parsed.timestamp())
    except ValueError:
        return None


def _resolve_rpc_endpoints(primary: str, fallbacks: list[str] | None) -> list[str]:
    defaults = [
        "https://api.mainnet.solana.com",
        "https://api.mainnet-beta.solana.com",
        "https://solana-rpc.publicnode.com",
        "https://solana.publicnode.dev",
        "https://solana.api.pocket.network",
        "https://solana.rpc.subquery.network/public",
    ]
    candidates = [primary, *(fallbacks or []), *defaults]
    normalized: list[str] = []
    for item in candidates:
        value = str(item).strip()
        if not value:
            continue
        if value not in normalized:
            normalized.append(value)
    return normalized


def _classify_defi_label(tx: dict[str, Any]) -> str:
    tokens = _collect_classification_tokens(tx)
    if any(token in JUPITER_PROGRAM_IDS for token in tokens):
        return "swap"
    if any(k in token for token in tokens for k in ("swap", "route", "exactin", "exactout")):
        return "swap"
    if any(
        k in token
        for token in tokens
        for k in ("liquidity", "amm", "whirlpool", "raydium", "orca", "addliquidity", "removeliquidity")
    ):
        return "lp"
    if any(
        k in token
        for token in tokens
        for k in ("stake", "unstake", "delegate", "deactivate", "validator")
    ):
        return "staking"
    if any(
        k in token
        for token in tokens
        for k in ("claim", "harvest", "collectreward", "reward", "airdrop")
    ):
        return "claim"
    return "unknown"


def _collect_classification_tokens(tx: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    transaction = tx.get("transaction", {}) if isinstance(tx.get("transaction"), dict) else {}
    message = transaction.get("message", {}) if isinstance(transaction.get("message"), dict) else {}
    meta = tx.get("meta", {}) if isinstance(tx.get("meta"), dict) else {}

    for key in message.get("accountKeys", []) if isinstance(message.get("accountKeys"), list) else []:
        if isinstance(key, dict):
            pubkey = str(key.get("pubkey", "")).strip()
            if pubkey:
                tokens.add(pubkey)
        else:
            val = str(key).strip()
            if val:
                tokens.add(val)

    for instruction in message.get("instructions", []) if isinstance(message.get("instructions"), list) else []:
        _collect_instruction_tokens(instruction, tokens)

    for inner in meta.get("innerInstructions", []) if isinstance(meta.get("innerInstructions"), list) else []:
        if not isinstance(inner, dict):
            continue
        instructions = inner.get("instructions", [])
        if isinstance(instructions, list):
            for instruction in instructions:
                _collect_instruction_tokens(instruction, tokens)

    logs = meta.get("logMessages", [])
    if isinstance(logs, list):
        for item in logs:
            value = str(item).strip().lower().replace(" ", "")
            if value:
                tokens.add(value)

    normalized: set[str] = set()
    for token in tokens:
        normalized.add(token)
        normalized.add(token.lower().replace(" ", ""))
    return normalized


def _collect_instruction_tokens(instruction: Any, tokens: set[str]) -> None:
    if not isinstance(instruction, dict):
        return
    program_id = str(instruction.get("programId", "")).strip()
    if program_id:
        tokens.add(program_id)
    program = str(instruction.get("program", "")).strip()
    if program:
        tokens.add(program)
    parsed = instruction.get("parsed")
    if isinstance(parsed, dict):
        parsed_type = str(parsed.get("type", "")).strip()
        if parsed_type:
            tokens.add(parsed_type)
        info = parsed.get("info")
        if isinstance(info, dict):
            for key, value in info.items():
                tokens.add(str(key))
                tokens.add(str(value))
