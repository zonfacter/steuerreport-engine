from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx


def fetch_solana_wallet_preview(
    wallet_address: str,
    rpc_url: str,
    timeout_seconds: int,
    max_signatures: int,
    max_transactions: int,
    aggregate_jupiter: bool = True,
    jupiter_window_seconds: int = 2,
) -> dict[str, Any]:
    signatures_payload = _solana_rpc(
        rpc_url=rpc_url,
        timeout_seconds=timeout_seconds,
        method="getSignaturesForAddress",
        params=[wallet_address, {"limit": max_signatures}],
    )
    if not isinstance(signatures_payload, list):
        raise ValueError("solana_signatures_invalid_payload")

    signatures = [str(item.get("signature", "")) for item in signatures_payload if isinstance(item, dict)]
    signatures = [sig for sig in signatures if sig][:max_transactions]

    rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []

    for signature in signatures:
        tx_payload = _solana_rpc(
            rpc_url=rpc_url,
            timeout_seconds=timeout_seconds,
            method="getTransaction",
            params=[signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
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
        "signature_count": len(signatures),
        "count": len(rows),
        "rows": rows,
        "warnings": warnings,
    }


def _solana_rpc(
    rpc_url: str,
    timeout_seconds: int,
    method: str,
    params: list[Any],
) -> Any:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(rpc_url, json=payload)
        response.raise_for_status()
        data = response.json()
    if not isinstance(data, dict):
        raise ValueError("solana_rpc_invalid_response")
    if data.get("error"):
        raise ValueError(f"solana_rpc_error:{data['error']}")
    return data.get("result")


def _map_transaction_rows(wallet_address: str, signature: str, tx: dict[str, Any]) -> list[dict[str, Any]]:
    block_time = tx.get("blockTime")
    timestamp_utc = _to_utc_iso(block_time)
    meta = tx.get("meta", {}) if isinstance(tx.get("meta"), dict) else {}
    transaction = tx.get("transaction", {}) if isinstance(tx.get("transaction"), dict) else {}
    message = transaction.get("message", {}) if isinstance(transaction.get("message"), dict) else {}
    account_keys = message.get("accountKeys", [])

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
                        "asset": "SOL",
                        "quantity": abs(diff_sol).to_eng_string(),
                        "price": "",
                        "fee": fee_sol.to_eng_string(),
                        "fee_asset": "SOL",
                        "side": "in" if diff_sol > 0 else "out",
                        "event_type": "sol_transfer",
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
        raw_tx=tx,
    )
    rows.extend(token_rows)

    if not rows:
        rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "asset": "SOL",
                "quantity": "0",
                "price": "",
                "fee": fee_sol.to_eng_string(),
                "fee_asset": "SOL",
                "side": "neutral",
                "event_type": "solana_tx",
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
                "asset": mint,
                "quantity": abs(diff).to_eng_string(),
                "price": "",
                "fee": "0",
                "fee_asset": "",
                "side": "in" if diff > 0 else "out",
                "event_type": "token_transfer",
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
