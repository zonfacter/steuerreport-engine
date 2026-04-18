from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

JUPITER_PROGRAM_IDS = {
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5NtJmQJ",
}


def fetch_solana_wallet_preview(
    wallet_address: str,
    rpc_url: str,
    rpc_fallback_urls: list[str] | None,
    timeout_seconds: int,
    max_signatures: int,
    max_transactions: int,
    aggregate_jupiter: bool = True,
    jupiter_window_seconds: int = 2,
) -> dict[str, Any]:
    endpoints = _resolve_rpc_endpoints(primary=rpc_url, fallbacks=rpc_fallback_urls)
    signatures_payload = _solana_rpc(
        rpc_url=endpoints,
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
            rpc_url=endpoints,
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
        "rpc_endpoints": endpoints,
        "signature_count": len(signatures),
        "count": len(rows),
        "rows": rows,
        "warnings": warnings,
    }


def _solana_rpc(
    rpc_url: str | list[str],
    timeout_seconds: int,
    method: str,
    params: list[Any],
) -> Any:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    endpoints = [rpc_url] if isinstance(rpc_url, str) else list(rpc_url)
    last_error = "unknown"
    with httpx.Client(timeout=timeout_seconds) as client:
        for endpoint in endpoints:
            try:
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                # Öffentliche RPCs liefern häufig 429/403; nächster Fallback-Endpunkt wird versucht.
                if status_code in {403, 429}:
                    last_error = f"{status_code} on {endpoint}"
                    continue
                raise
            if not isinstance(data, dict):
                last_error = f"invalid_payload on {endpoint}"
                continue
            if data.get("error"):
                last_error = f"rpc_error on {endpoint}: {data['error']}"
                continue
            return data.get("result")
    raise ValueError(f"solana_rpc_all_endpoints_failed:{last_error}")


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
        "https://solana-rpc.publicnode.com",
        "https://api.mainnet-beta.solana.com",
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
