from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from tax_engine.admin.service import resolve_effective_runtime_config
from tax_engine.connectors.token_metadata import resolve_token_metadata
from tax_engine.core.derivatives import process_derivatives_for_year
from tax_engine.core.processor import process_events_for_year
from tax_engine.core.tax_domains import build_tax_domain_summary
from tax_engine.fx import FallbackFxResolver
from tax_engine.ingestion.store import STORE
from tax_engine.integrations import filter_events_for_processing
from tax_engine.integrity import (
    config_fingerprint,
    data_fingerprint,
    report_integrity_id,
    ruleset_fingerprint,
)
from tax_engine.reconciliation.chains import build_transfer_chain_index
from tax_engine.rulesets import build_default_registry

from .models import ProcessRunRequest

STABLE_ASSETS = {"USD", "USDT", "USDC", "BUSD", "FDUSD", "DAI", "TUSD", "USDP"}
USD_STABLE_ASSETS = {"USD", "USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USDP"}
BINANCE_MARKET_QUOTE_ASSETS = ("USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USDP", "EUR", "BTC", "ETH", "BNB")
SOLSCAN_STABLE_MINTS = {
    "EPJFWDDAUFQSSQEM2QN1XZYBAPC8G4WEGGKZWYTD1V": "USDC",
    "ES9VMFRZACERMJFRF4H2FYD4KCONKY11MCCE8BENWNYB": "USDT",
}
SOLSCAN_WSOL_MINT = "SO11111111111111111111111111111111111111112"
HELIUM_SOLANA_DISTRIBUTOR_PROGRAM_IDS = {
    "1ATRMQS3EQ1N2FEYWU6TYTXBCJP4UQWEXPJTNHXTS8H",
}


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _load_token_alias_symbols() -> dict[str, str]:
    row = STORE.get_setting("runtime.token_aliases")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    aliases: dict[str, str] = {}
    for mint_raw, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        mint = str(mint_raw or "").upper().strip()
        symbol = str(payload.get("symbol") or "").upper().strip()
        if mint and symbol:
            aliases[mint] = symbol
    return aliases


def _asset_price_symbol(asset: Any, aliases: dict[str, str]) -> str:
    normalized = str(asset or "").upper().strip()
    if not normalized:
        return ""
    if normalized in aliases:
        return aliases[normalized]
    metadata = resolve_token_metadata(normalized)
    symbol = str(metadata.get("symbol") or normalized).upper().strip()
    return symbol if symbol else normalized


def _event_date(payload: dict[str, Any]) -> str:
    return str(payload.get("timestamp_utc") or payload.get("timestamp") or "")[:10]


def _event_quantity(payload: dict[str, Any]) -> Decimal:
    heliumgeek_qty = _heliumgeek_display_quantity(payload)
    if heliumgeek_qty > Decimal("0"):
        return heliumgeek_qty
    for key in ("quantity", "qty", "amount", "size"):
        value = _safe_decimal(payload.get(key))
        if value != Decimal("0"):
            return abs(value)
    return Decimal("0")


def _event_side(payload: dict[str, Any]) -> str:
    return str(payload.get("side") or "").lower().strip()


def _event_tx_id(payload: dict[str, Any]) -> str:
    return str(payload.get("tx_id") or payload.get("transaction_hash") or payload.get("signature") or "").strip()


def _valuation_anchor_key(payload: dict[str, Any], aliases: dict[str, str]) -> tuple[str, str, str, str] | None:
    tx_id = _event_tx_id(payload)
    side = _event_side(payload)
    asset = _asset_price_symbol(payload.get("asset"), aliases)
    quantity = _event_quantity(payload)
    if not tx_id or side not in {"in", "out"} or not asset or quantity <= Decimal("0"):
        return None
    return (tx_id, side, asset, quantity.normalize().to_eng_string())


def _payload_value_usd_sum(payload: dict[str, Any]) -> Decimal:
    value = _safe_decimal(payload.get("value_usd_sum"))
    if value > Decimal("0"):
        return value
    raw_row = payload.get("raw_row")
    if isinstance(raw_row, dict):
        value = _safe_decimal(raw_row.get("value_usd_sum"))
        if value > Decimal("0"):
            return value
    return Decimal("0")


def _raw_row_field(payload: dict[str, Any], key: str) -> str:
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return ""
    return str(raw_row.get(key) or "").strip()


def _bitget_spot_biz_order_id(payload: dict[str, Any]) -> str:
    return _raw_row_field(payload, "bizOrderId")


def _binance_account_statement_group_id(payload: dict[str, Any]) -> str:
    raw_row = payload.get("raw_row")
    remark = str(raw_row.get("Remark") or raw_row.get("remark") or "").strip() if isinstance(raw_row, dict) else ""
    if remark:
        return remark
    tx_id = _event_tx_id(payload)
    if ":" in tx_id:
        return tx_id.split(":", 1)[0]
    return tx_id


def _split_binance_market_symbol(market: str) -> tuple[str, str]:
    normalized = str(market or "").upper().strip()
    for quote in BINANCE_MARKET_QUOTE_ASSETS:
        if normalized.endswith(quote) and len(normalized) > len(quote):
            return normalized[: -len(quote)], quote
    return "", ""


def _lookup_asset_usd_rate(asset: str, rate_date: str, cache: dict[tuple[str, str], tuple[Decimal, str]]) -> tuple[Decimal, str]:
    key = (asset, rate_date)
    cached = cache.get(key)
    if cached is not None:
        return cached
    row = STORE.get_fx_rate(rate_date=rate_date, base_ccy=asset, quote_ccy="USD") if rate_date else None
    if row is None and rate_date:
        row = STORE.get_fx_rate_on_or_before(rate_date=rate_date, base_ccy=asset, quote_ccy="USD")
    rate = _safe_decimal(row.get("rate")) if isinstance(row, dict) else Decimal("0")
    source_rate_date = str(row.get("source_rate_date") or row.get("rate_date") or rate_date) if isinstance(row, dict) else ""
    cache[key] = (rate, source_rate_date)
    return rate, source_rate_date


def _normalized_mint(value: Any) -> str:
    return str(value or "").upper().strip()


def _solscan_token_change_amount(item: dict[str, Any]) -> Decimal:
    amount = _safe_decimal(item.get("change_amount") or item.get("changeAmount"))
    decimals_raw = item.get("decimals")
    try:
        decimals = int(str(decimals_raw))
    except (TypeError, ValueError):
        decimals = int(str(item.get("token_decimals") or 0))
    if decimals > 0:
        amount = amount / (Decimal(10) ** decimals)
    return amount


def _token_balance_changes_from_solscan_transaction(signature: str) -> list[dict[str, Any]]:
    if not signature:
        return []
    row = STORE.get_solscan_transaction(signature)
    if row is None:
        return []
    raw = row.get("raw")
    if isinstance(raw, dict):
        body = raw
    else:
        try:
            body = json.loads(str(row.get("raw_json") or "{}"))
        except json.JSONDecodeError:
            return []
    data = body.get("data") if isinstance(body, dict) and isinstance(body.get("data"), dict) else body
    if not isinstance(data, dict):
        return []
    changes = data.get("token_bal_change")
    return changes if isinstance(changes, list) else []


def _solscan_stable_counterflow_value_usd(
    *,
    payload: dict[str, Any],
    aliases: dict[str, str],
    tx_cache: dict[str, list[dict[str, Any]]],
    sol_usd_cache: dict[str, Decimal],
) -> Decimal:
    tx_id = _event_tx_id(payload)
    wallet_address = str(payload.get("wallet_address") or "").strip()
    asset = _normalized_mint(payload.get("asset"))
    quantity = _event_quantity(payload)
    side = _event_side(payload)
    if not tx_id or not wallet_address or not asset or quantity <= Decimal("0") or side not in {"in", "out"}:
        return Decimal("0")
    changes = tx_cache.get(tx_id)
    if changes is None:
        changes = _token_balance_changes_from_solscan_transaction(tx_id)
        tx_cache[tx_id] = changes
    if not changes:
        return Decimal("0")

    matched_wallet_change = False
    for item in changes:
        if not isinstance(item, dict):
            continue
        if str(item.get("owner") or "").strip() != wallet_address:
            continue
        if _normalized_mint(item.get("token_address")) != asset:
            continue
        amount = _solscan_token_change_amount(item)
        if side == "in" and amount <= Decimal("0"):
            continue
        if side == "out" and amount >= Decimal("0"):
            continue
        if abs(amount - quantity) <= Decimal("0.000001"):
            matched_wallet_change = True
            break
    if not matched_wallet_change:
        return Decimal("0")

    stable_values: list[Decimal] = []
    wsol_positive = Decimal("0")
    wsol_negative = Decimal("0")
    for item in changes:
        if not isinstance(item, dict):
            continue
        token_address = _normalized_mint(item.get("token_address"))
        symbol = SOLSCAN_STABLE_MINTS.get(token_address) or aliases.get(token_address, "")
        amount = _solscan_token_change_amount(item)
        if symbol.upper().strip() not in STABLE_ASSETS:
            if token_address == SOLSCAN_WSOL_MINT:
                if amount > Decimal("0"):
                    wsol_positive += amount
                elif amount < Decimal("0"):
                    wsol_negative += abs(amount)
            continue
        abs_amount = abs(amount)
        if abs_amount > Decimal("0"):
            stable_values.append(abs_amount)
    stable_value = max(stable_values, default=Decimal("0"))
    if stable_value > Decimal("0"):
        return stable_value

    rate_date = _event_date(payload)
    sol_usd = sol_usd_cache.get(rate_date)
    if sol_usd is None:
        row = STORE.get_fx_rate(rate_date=rate_date, base_ccy="SOL", quote_ccy="USD") if rate_date else None
        if row is None and rate_date:
            row = STORE.get_fx_rate_on_or_before(rate_date=rate_date, base_ccy="SOL", quote_ccy="USD")
        sol_usd = _safe_decimal(row.get("rate")) if isinstance(row, dict) else Decimal("0")
        sol_usd_cache[rate_date] = sol_usd
    wsol_counterflow = wsol_positive if side == "in" else wsol_negative
    if wsol_counterflow > Decimal("0") and sol_usd > Decimal("0"):
        return wsol_counterflow * sol_usd
    return Decimal("0")


def _raw_stable_counterflow_value_usd(payload: dict[str, Any], aliases: dict[str, str]) -> Decimal:
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0")
    side = _event_side(payload)
    if side == "in":
        stable_asset = _asset_price_symbol(raw_row.get("from_asset"), aliases)
        stable_quantity = _safe_decimal(raw_row.get("from_quantity"))
    elif side == "out":
        stable_asset = _asset_price_symbol(raw_row.get("to_asset"), aliases)
        stable_quantity = _safe_decimal(raw_row.get("to_quantity"))
    else:
        return Decimal("0")
    if stable_asset.upper().strip() not in STABLE_ASSETS or stable_quantity <= Decimal("0"):
        return Decimal("0")
    return stable_quantity


def attach_reference_usd_value_anchors(
    active_events: list[dict[str, Any]],
    all_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aliases = _load_token_alias_symbols()
    anchors: dict[tuple[str, str, str, str], tuple[str, Decimal]] = {}
    solscan_tx_cache: dict[str, list[dict[str, Any]]] = {}
    sol_usd_cache: dict[str, Decimal] = {}
    counterflow_available = 0
    raw_counterflow_available = 0
    for event in all_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source") or "").lower().strip()
        if source != "solscan_wallet_discovery":
            continue
        value_usd_sum = _payload_value_usd_sum(payload)
        if value_usd_sum <= Decimal("0"):
            continue
        key = _valuation_anchor_key(payload, aliases)
        if key is None:
            continue
        anchors.setdefault(key, (str(event.get("unique_event_id") or ""), value_usd_sum))

    transformed: list[dict[str, Any]] = []
    attached = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        source = str(payload.get("source") or "").lower().strip()
        if source != "solana_rpc" or _payload_value_usd_sum(payload) > Decimal("0"):
            transformed.append(event)
            continue
        key = _valuation_anchor_key(payload, aliases)
        anchor = anchors.get(key) if key is not None else None
        if anchor is None:
            raw_counterflow_value = _raw_stable_counterflow_value_usd(payload, aliases)
            stable_counterflow_value = raw_counterflow_value
            reference_source = "raw_stable_counterflow"
            from_raw_counterflow = stable_counterflow_value > Decimal("0")
            if stable_counterflow_value <= Decimal("0"):
                stable_counterflow_value = _solscan_stable_counterflow_value_usd(
                    payload=payload,
                    aliases=aliases,
                    tx_cache=solscan_tx_cache,
                    sol_usd_cache=sol_usd_cache,
                )
                reference_source = "solscan_transaction_counterflow"
            if stable_counterflow_value <= Decimal("0"):
                transformed.append(event)
                continue
            updated_payload = dict(payload)
            updated_payload["value_usd_sum"] = stable_counterflow_value.to_eng_string()
            updated_payload["valuation_reference_source"] = reference_source
            updated_payload["valuation_reference_tx_id"] = _event_tx_id(payload)
            updated_event = dict(event)
            updated_event["payload"] = updated_payload
            transformed.append(updated_event)
            attached += 1
            if from_raw_counterflow:
                raw_counterflow_available += 1
            else:
                counterflow_available += 1
            continue
        reference_event_id, value_usd_sum = anchor
        updated_payload = dict(payload)
        updated_payload["value_usd_sum"] = value_usd_sum.to_eng_string()
        updated_payload["valuation_reference_source"] = "solscan_wallet_discovery"
        updated_payload["valuation_reference_source_event_id"] = reference_event_id
        updated_event = dict(event)
        updated_event["payload"] = updated_payload
        transformed.append(updated_event)
        attached += 1

    return transformed, {
        "valuation_anchor_source": "solscan_wallet_discovery",
        "available_anchor_count": len(anchors),
        "attached_anchor_count": attached,
        "solscan_counterflow_attached_count": counterflow_available,
        "raw_stable_counterflow_attached_count": raw_counterflow_available,
    }


def attach_bitget_tax_api_spot_trade_value_anchors(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aliases = _load_token_alias_symbols()
    stable_outflows_by_biz_order: dict[str, tuple[str, str, Decimal]] = {}
    available_counterflows = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source") or "").lower().strip()
        event_type = str(payload.get("event_type") or "").lower().strip()
        if source != "bitget_tax_api" or event_type != "trade" or _event_side(payload) != "out":
            continue
        biz_order_id = _bitget_spot_biz_order_id(payload)
        asset = _asset_price_symbol(payload.get("asset"), aliases)
        quantity = _event_quantity(payload)
        if not biz_order_id or asset not in STABLE_ASSETS or quantity <= Decimal("0"):
            continue
        available_counterflows += 1
        existing = stable_outflows_by_biz_order.get(biz_order_id)
        if existing is None:
            stable_outflows_by_biz_order[biz_order_id] = (str(event.get("unique_event_id") or ""), asset, quantity)
            continue
        existing_event_id, existing_asset, existing_quantity = existing
        stable_outflows_by_biz_order[biz_order_id] = (
            existing_event_id,
            existing_asset if existing_asset == asset else f"{existing_asset}+{asset}",
            existing_quantity + quantity,
        )

    transformed: list[dict[str, Any]] = []
    attached = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        source = str(payload.get("source") or "").lower().strip()
        event_type = str(payload.get("event_type") or "").lower().strip()
        if source != "bitget_tax_api" or event_type != "trade" or _event_side(payload) != "in":
            transformed.append(event)
            continue
        if _payload_value_usd_sum(payload) > Decimal("0") or _safe_decimal(payload.get("value_eur")) > Decimal("0"):
            transformed.append(event)
            continue
        asset = _asset_price_symbol(payload.get("asset"), aliases)
        if not asset or asset in STABLE_ASSETS:
            transformed.append(event)
            continue
        biz_order_id = _bitget_spot_biz_order_id(payload)
        counterflow = stable_outflows_by_biz_order.get(biz_order_id)
        if counterflow is None:
            transformed.append(event)
            continue
        reference_event_id, reference_asset, value_usd_sum = counterflow
        if value_usd_sum <= Decimal("0"):
            transformed.append(event)
            continue
        updated_payload = dict(payload)
        updated_payload["value_usd_sum"] = value_usd_sum.to_eng_string()
        updated_payload["valuation_reference_source"] = "bitget_tax_api_biz_order_stable_counterflow"
        updated_payload["valuation_reference_source_event_id"] = reference_event_id
        updated_payload["valuation_reference_asset"] = reference_asset
        updated_payload["valuation_reference_biz_order_id"] = biz_order_id
        updated_event = dict(event)
        updated_event["payload"] = updated_payload
        transformed.append(updated_event)
        attached += 1

    return transformed, {
        "valuation_anchor_source": "bitget_tax_api_biz_order_stable_counterflow",
        "available_counterflow_count": available_counterflows,
        "attached_anchor_count": attached,
    }


def attach_binance_market_quote_value_anchors(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aliases = _load_token_alias_symbols()
    quote_usd_cache: dict[tuple[str, str], tuple[Decimal, str]] = {}
    transformed: list[dict[str, Any]] = []
    available_market_rows = 0
    attached_usd = 0
    attached_eur = 0
    missing_quote_rates = 0

    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        source = str(payload.get("source") or "").lower().strip()
        event_type = str(payload.get("event_type") or "").lower().strip()
        side = _event_side(payload)
        raw_row = payload.get("raw_row")
        if source != "binance" or event_type != "trade" or side not in {"in", "out"} or not isinstance(raw_row, dict):
            transformed.append(event)
            continue
        if _payload_value_usd_sum(payload) > Decimal("0") or _safe_decimal(payload.get("value_eur")) > Decimal("0"):
            transformed.append(event)
            continue
        market = str(raw_row.get("Market") or raw_row.get("market") or "").upper().strip()
        total = _safe_decimal(raw_row.get("Total") or raw_row.get("total"))
        base_asset, quote_asset = _split_binance_market_symbol(market)
        asset = _asset_price_symbol(payload.get("asset"), aliases)
        quantity = _event_quantity(payload)
        if not market or not base_asset or not quote_asset or asset not in {base_asset, quote_asset} or total <= 0 or quantity <= 0:
            transformed.append(event)
            continue

        available_market_rows += 1
        updated_payload = dict(payload)
        updated_payload["valuation_reference_source"] = "binance_market_quote_total"
        updated_payload["valuation_reference_market"] = market
        updated_payload["valuation_reference_asset"] = quote_asset
        updated_payload["binance_market_quote_unit_price"] = str(payload.get("price") or "")
        updated_payload["price"] = ""

        if quote_asset == "EUR":
            updated_payload["value_eur"] = total.to_eng_string()
            updated_payload["valuation_reference_rate_date"] = _event_date(payload)
            updated_event = dict(event)
            updated_event["payload"] = updated_payload
            transformed.append(updated_event)
            attached_eur += 1
            continue

        if quote_asset in USD_STABLE_ASSETS:
            updated_payload["value_usd_sum"] = total.to_eng_string()
            updated_payload["valuation_reference_rate_date"] = _event_date(payload)
            updated_event = dict(event)
            updated_event["payload"] = updated_payload
            transformed.append(updated_event)
            attached_usd += 1
            continue

        rate_date = _event_date(payload)
        quote_usd_rate, source_rate_date = _lookup_asset_usd_rate(quote_asset, rate_date, quote_usd_cache)
        if quote_usd_rate <= Decimal("0"):
            missing_quote_rates += 1
            transformed.append(event)
            continue
        updated_payload["value_usd_sum"] = (total * quote_usd_rate).to_eng_string()
        updated_payload["valuation_reference_quote_usd_rate"] = quote_usd_rate.to_eng_string()
        updated_payload["valuation_reference_rate_date"] = source_rate_date or rate_date
        updated_event = dict(event)
        updated_event["payload"] = updated_payload
        transformed.append(updated_event)
        attached_usd += 1

    return transformed, {
        "valuation_anchor_source": "binance_market_quote_total",
        "available_market_row_count": available_market_rows,
        "attached_usd_value_count": attached_usd,
        "attached_eur_value_count": attached_eur,
        "missing_quote_rate_count": missing_quote_rates,
        "quote_usd_cache_key_count": len(quote_usd_cache),
    }


def attach_binance_fiat_purchase_value_anchors(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aliases = _load_token_alias_symbols()
    eur_outflows_by_group: dict[str, tuple[str, Decimal]] = {}
    crypto_inflow_counts_by_group: dict[str, int] = {}
    available_counterflows = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source") or "").lower().strip()
        event_type = str(payload.get("event_type") or "").lower().strip()
        if source == "binance" and event_type == "fiat_crypto_purchase" and _event_side(payload) == "in":
            asset = _asset_price_symbol(payload.get("asset"), aliases)
            group_id = _binance_account_statement_group_id(payload)
            if asset and asset != "EUR" and group_id:
                crypto_inflow_counts_by_group[group_id] = crypto_inflow_counts_by_group.get(group_id, 0) + 1
            continue
        if source != "binance" or event_type != "fiat_crypto_purchase" or _event_side(payload) != "out":
            continue
        asset = _asset_price_symbol(payload.get("asset"), aliases)
        quantity = _event_quantity(payload)
        group_id = _binance_account_statement_group_id(payload)
        if asset != "EUR" or quantity <= Decimal("0") or not group_id:
            continue
        available_counterflows += 1
        existing = eur_outflows_by_group.get(group_id)
        if existing is None:
            eur_outflows_by_group[group_id] = (str(event.get("unique_event_id") or ""), quantity)
        else:
            reference_event_id, existing_quantity = existing
            eur_outflows_by_group[group_id] = (reference_event_id, existing_quantity + quantity)

    transformed: list[dict[str, Any]] = []
    attached = 0
    ambiguous_groups: set[str] = set()
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        source = str(payload.get("source") or "").lower().strip()
        event_type = str(payload.get("event_type") or "").lower().strip()
        if source != "binance" or event_type != "fiat_crypto_purchase" or _event_side(payload) != "in":
            transformed.append(event)
            continue
        if _payload_value_usd_sum(payload) > Decimal("0") or _safe_decimal(payload.get("value_eur")) > Decimal("0"):
            transformed.append(event)
            continue
        asset = _asset_price_symbol(payload.get("asset"), aliases)
        if not asset or asset == "EUR":
            transformed.append(event)
            continue
        group_id = _binance_account_statement_group_id(payload)
        if crypto_inflow_counts_by_group.get(group_id, 0) != 1:
            if group_id:
                ambiguous_groups.add(group_id)
            transformed.append(event)
            continue
        counterflow = eur_outflows_by_group.get(group_id)
        if counterflow is None:
            transformed.append(event)
            continue
        reference_event_id, value_eur = counterflow
        if value_eur <= Decimal("0"):
            transformed.append(event)
            continue
        updated_payload = dict(payload)
        updated_payload["value_eur"] = value_eur.to_eng_string()
        updated_payload["valuation_reference_source"] = "binance_fiat_purchase_eur_counterflow"
        updated_payload["valuation_reference_source_event_id"] = reference_event_id
        updated_payload["valuation_reference_asset"] = "EUR"
        updated_payload["valuation_reference_group_id"] = group_id
        updated_event = dict(event)
        updated_event["payload"] = updated_payload
        transformed.append(updated_event)
        attached += 1

    return transformed, {
        "valuation_anchor_source": "binance_fiat_purchase_eur_counterflow",
        "available_counterflow_count": available_counterflows,
        "attached_anchor_count": attached,
        "ambiguous_inflow_group_count": len(ambiguous_groups),
    }


def _binance_transaction_history_group_key(event: dict[str, Any], payload: dict[str, Any]) -> tuple[str, str] | None:
    source = str(payload.get("source") or "").lower().strip()
    event_type = str(payload.get("event_type") or "").lower().strip()
    tx_id = _event_tx_id(payload)
    timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "").strip()
    source_file_id = str(event.get("source_file_id") or "").strip()
    if source != "binance" or event_type != "trade" or not tx_id.startswith("binance-txhist-"):
        return None
    if not timestamp or not source_file_id:
        return None
    return source_file_id, timestamp


def attach_binance_transaction_history_stable_counterflow_value_anchors(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aliases = _load_token_alias_symbols()
    grouped: dict[tuple[str, str], list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        key = _binance_transaction_history_group_key(event, payload)
        if key is None:
            continue
        grouped.setdefault(key, []).append((event, payload))

    group_values: dict[tuple[str, str], tuple[str, Decimal, Decimal, str]] = {}
    usable_groups = 0
    ambiguous_groups = 0
    for key, group in grouped.items():
        stable_out_total = Decimal("0")
        stable_assets: set[str] = set()
        non_stable_in_total = Decimal("0")
        non_stable_in_assets: set[str] = set()
        non_stable_out_count = 0
        reference_event_id = ""

        for event, payload in group:
            side = _event_side(payload)
            asset = _asset_price_symbol(payload.get("asset"), aliases)
            quantity = _event_quantity(payload)
            if quantity <= Decimal("0") or not asset:
                continue
            if side == "out" and asset in USD_STABLE_ASSETS:
                stable_out_total += quantity
                stable_assets.add(asset)
                if not reference_event_id:
                    reference_event_id = str(event.get("unique_event_id") or "")
                continue
            if side == "in" and asset not in STABLE_ASSETS:
                non_stable_in_total += quantity
                non_stable_in_assets.add(asset)
                continue
            if side == "out" and asset not in STABLE_ASSETS:
                non_stable_out_count += 1

        if stable_out_total <= Decimal("0") or non_stable_in_total <= Decimal("0") or len(non_stable_in_assets) != 1:
            ambiguous_groups += 1
            continue
        if non_stable_out_count > 0:
            ambiguous_groups += 1
            continue
        usable_groups += 1
        group_values[key] = (
            reference_event_id,
            stable_out_total,
            non_stable_in_total,
            "+".join(sorted(stable_assets)),
        )

    transformed: list[dict[str, Any]] = []
    attached = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        key = _binance_transaction_history_group_key(event, payload)
        group_value = group_values.get(key) if key is not None else None
        if group_value is None:
            transformed.append(event)
            continue
        if _payload_value_usd_sum(payload) > Decimal("0") or _safe_decimal(payload.get("value_eur")) > Decimal("0"):
            transformed.append(event)
            continue
        side = _event_side(payload)
        asset = _asset_price_symbol(payload.get("asset"), aliases)
        quantity = _event_quantity(payload)
        if side != "in" or asset in STABLE_ASSETS or quantity <= Decimal("0"):
            transformed.append(event)
            continue

        reference_event_id, stable_out_total, non_stable_in_total, reference_asset = group_value
        value_usd_sum = stable_out_total * quantity / non_stable_in_total
        updated_payload = dict(payload)
        updated_payload["value_usd_sum"] = value_usd_sum.to_eng_string()
        updated_payload["valuation_reference_source"] = "binance_transaction_history_stable_counterflow"
        updated_payload["valuation_reference_source_event_id"] = reference_event_id
        updated_payload["valuation_reference_asset"] = reference_asset
        updated_payload["valuation_reference_group_key"] = ":".join(key or ("", ""))
        updated_event = dict(event)
        updated_event["payload"] = updated_payload
        transformed.append(updated_event)
        attached += 1

    return transformed, {
        "valuation_anchor_source": "binance_transaction_history_stable_counterflow",
        "available_group_count": usable_groups,
        "ambiguous_group_count": ambiguous_groups,
        "attached_anchor_count": attached,
    }


def attach_cached_usd_prices_to_binance_dust_convert_in_events(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aliases = _load_token_alias_symbols()
    price_cache: dict[tuple[str, str], tuple[Decimal, str]] = {}
    transformed: list[dict[str, Any]] = []
    attached = 0
    missing_prices = 0

    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        if _safe_decimal(payload.get("price_eur")) > Decimal("0") or _safe_decimal(payload.get("price_usd")) > Decimal("0"):
            transformed.append(event)
            continue
        if _payload_value_usd_sum(payload) > Decimal("0") or _safe_decimal(payload.get("value_eur")) > Decimal("0"):
            transformed.append(event)
            continue
        source = str(payload.get("source") or "").lower().strip()
        event_type = str(payload.get("event_type") or "").lower().strip()
        if source != "binance_api" or event_type != "dust_convert_in" or _event_side(payload) != "in":
            transformed.append(event)
            continue
        asset = _asset_price_symbol(payload.get("asset"), aliases)
        if not asset or asset in STABLE_ASSETS:
            transformed.append(event)
            continue
        rate_date = _event_date(payload)
        price_usd, source_rate_date = _lookup_asset_usd_rate(asset, rate_date, price_cache)
        if price_usd <= Decimal("0"):
            missing_prices += 1
            transformed.append(event)
            continue
        updated_payload = dict(payload)
        updated_payload["price_usd"] = price_usd.to_eng_string()
        updated_payload["valuation_reference_source"] = "fx_cache_asset_usd_binance_dust_convert_in"
        updated_payload["valuation_reference_asset"] = asset
        updated_payload["valuation_reference_rate_date"] = source_rate_date or rate_date
        updated_event = dict(event)
        updated_event["payload"] = updated_payload
        transformed.append(updated_event)
        attached += 1

    return transformed, {
        "valuation_anchor_source": "fx_cache_asset_usd_binance_dust_convert_in",
        "attached_price_count": attached,
        "missing_price_count": missing_prices,
        "price_cache_key_count": len(price_cache),
    }


def drop_solscan_duplicates_when_solana_rpc_is_active(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aliases = _load_token_alias_symbols()
    solana_rpc_keys: set[tuple[str, str, str, str]] = set()
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if str(payload.get("source") or "").lower().strip() != "solana_rpc":
            continue
        key = _valuation_anchor_key(payload, aliases)
        if key is not None:
            solana_rpc_keys.add(key)

    transformed: list[dict[str, Any]] = []
    dropped = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        if str(payload.get("source") or "").lower().strip() != "solscan_wallet_discovery":
            transformed.append(event)
            continue
        key = _valuation_anchor_key(payload, aliases)
        if key is not None and key in solana_rpc_keys:
            dropped += 1
            continue
        transformed.append(event)

    return transformed, {
        "dedupe_rule": "drop_solscan_wallet_discovery_when_matching_solana_rpc_active",
        "solana_rpc_key_count": len(solana_rpc_keys),
        "dropped_solscan_duplicate_count": dropped,
    }


def drop_malformed_binance_market_summary_events(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    dropped = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        source = str(payload.get("source") or "").lower().strip()
        event_type = str(payload.get("event_type") or "").lower().strip()
        side = _event_side(payload)
        asset = str(payload.get("asset") or "").strip()
        raw_row = payload.get("raw_row")
        market = str(raw_row.get("Market") or raw_row.get("market") or "").strip() if isinstance(raw_row, dict) else ""
        if source == "binance" and event_type in {"buy", "sell"} and side in {"buy", "sell"} and not asset and market:
            dropped += 1
            continue
        transformed.append(event)

    return transformed, {
        "dedupe_rule": "drop_malformed_binance_market_summary_events",
        "dropped_malformed_binance_market_summary_count": dropped,
    }


def drop_exact_pionex_duplicate_events(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seen: set[tuple[str, str, str, str, str, str, str]] = set()
    transformed: list[dict[str, Any]] = []
    dropped = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        if str(payload.get("source") or "").lower().strip() != "pionex":
            transformed.append(event)
            continue
        key = (
            str(payload.get("timestamp_utc") or payload.get("timestamp") or "").strip(),
            str(payload.get("event_type") or "").lower().strip(),
            str(payload.get("side") or "").lower().strip(),
            _asset_price_symbol(payload.get("asset"), {}),
            _event_quantity(payload).normalize().to_eng_string(),
            _safe_decimal(payload.get("fee")).normalize().to_eng_string(),
            str(payload.get("fee_asset") or "").upper().strip(),
        )
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        transformed.append(event)

    return transformed, {
        "dedupe_rule": "drop_exact_pionex_duplicate_events",
        "pionex_key_count": len(seen),
        "dropped_pionex_duplicate_count": dropped,
    }


def attach_cached_usd_prices_to_reward_events(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aliases = _load_token_alias_symbols()
    price_cache: dict[tuple[str, str], Decimal] = {}
    transformed: list[dict[str, Any]] = []
    attached = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        if _safe_decimal(payload.get("price_eur")) > Decimal("0") or _safe_decimal(payload.get("price_usd")) > Decimal("0"):
            transformed.append(event)
            continue
        if _payload_value_usd_sum(payload) > Decimal("0") or _safe_decimal(payload.get("value_eur")) > Decimal("0"):
            transformed.append(event)
            continue
        side = _event_side(payload)
        event_type = str(payload.get("event_type") or "").lower().strip()
        defi_label = str(payload.get("defi_label") or "").lower().strip()
        is_reward_like = (
            "reward" in event_type
            or "mining" in event_type
            or "interest" in event_type
            or defi_label in {"claim", "staking"}
        )
        if side != "in" or not is_reward_like:
            transformed.append(event)
            continue
        asset = _asset_price_symbol(payload.get("asset"), aliases)
        if not asset or asset in STABLE_ASSETS:
            transformed.append(event)
            continue
        rate_date = _event_date(payload)
        cache_key = (asset, rate_date)
        price_usd = price_cache.get(cache_key)
        if price_usd is None:
            row = STORE.get_fx_rate(rate_date=rate_date, base_ccy=asset, quote_ccy="USD") if rate_date else None
            if row is None and rate_date:
                row = STORE.get_fx_rate_on_or_before(rate_date=rate_date, base_ccy=asset, quote_ccy="USD")
            price_usd = _safe_decimal(row.get("rate")) if isinstance(row, dict) else Decimal("0")
            price_cache[cache_key] = price_usd
        if price_usd <= Decimal("0"):
            transformed.append(event)
            continue
        updated_payload = dict(payload)
        updated_payload["price_usd"] = price_usd.to_eng_string()
        updated_payload["valuation_reference_source"] = "fx_cache_asset_usd_reward"
        updated_payload["valuation_reference_asset"] = asset
        updated_payload["valuation_reference_rate_date"] = rate_date
        updated_event = dict(event)
        updated_event["payload"] = updated_payload
        transformed.append(updated_event)
        attached += 1
    return transformed, {
        "valuation_anchor_source": "fx_cache_asset_usd_reward",
        "attached_price_count": attached,
        "price_cache_key_count": len(price_cache),
    }


def label_helium_solana_claim_events(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aliases = _load_token_alias_symbols()
    transformed: list[dict[str, Any]] = []
    labelled = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        if not _is_helium_solana_claim_payload(payload, aliases):
            transformed.append(event)
            continue
        updated_payload = dict(payload)
        updated_payload["defi_label"] = "claim"
        updated_payload["valuation_reference_source"] = "helium_solana_distribution_label"
        updated_event = dict(event)
        updated_event["payload"] = updated_payload
        transformed.append(updated_event)
        labelled += 1
    return transformed, {
        "label_source": "helium_solana_distribution_label",
        "labelled_count": labelled,
    }


def _is_helium_solana_claim_payload(payload: dict[str, Any], aliases: dict[str, str]) -> bool:
    if str(payload.get("source") or "").lower().strip() != "solana_rpc":
        return False
    if str(payload.get("event_type") or "").lower().strip() != "token_transfer":
        return False
    if _event_side(payload) != "in":
        return False
    defi_label = str(payload.get("defi_label") or "").lower().strip()
    if defi_label not in {"", "unknown"}:
        return False
    asset = _asset_price_symbol(payload.get("asset"), aliases)
    if asset not in {"HNT", "IOT", "MOBILE"}:
        return False
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return False
    raw_text = json.dumps(raw_row, ensure_ascii=False).upper()
    return any(program_id in raw_text for program_id in HELIUM_SOLANA_DISTRIBUTOR_PROGRAM_IDS)


def attach_cached_usd_prices_to_swap_in_events(
    active_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aliases = _load_token_alias_symbols()
    price_cache: dict[tuple[str, str], Decimal] = {}
    events_by_tx: dict[str, list[dict[str, Any]]] = {}
    for candidate_event in active_events:
        candidate_payload = candidate_event.get("payload", {})
        if not isinstance(candidate_payload, dict):
            continue
        tx_id = _event_tx_id(candidate_payload)
        if tx_id:
            events_by_tx.setdefault(tx_id, []).append(candidate_payload)
    transformed: list[dict[str, Any]] = []
    attached = 0
    counterflow_attached = 0
    raw_route_attached = 0
    for event in active_events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        if _safe_decimal(payload.get("price_eur")) > Decimal("0") or _safe_decimal(payload.get("price_usd")) > Decimal("0"):
            transformed.append(event)
            continue
        if _payload_value_usd_sum(payload) > Decimal("0") or _safe_decimal(payload.get("value_eur")) > Decimal("0"):
            transformed.append(event)
            continue
        if str(payload.get("source") or "").lower().strip() != "solana_rpc":
            transformed.append(event)
            continue
        event_type = str(payload.get("event_type") or "").lower().strip()
        defi_label = str(payload.get("defi_label") or "").lower().strip()
        is_swap_in = event_type == "swap_in_aggregated" or (
            event_type in {"sol_transfer", "token_transfer"} and defi_label == "swap"
        )
        if _event_side(payload) != "in" or not is_swap_in:
            transformed.append(event)
            continue
        asset = _asset_price_symbol(payload.get("asset"), aliases)
        if not asset or asset in STABLE_ASSETS:
            transformed.append(event)
            continue
        rate_date = _event_date(payload)
        cache_key = (asset, rate_date)
        price_usd = price_cache.get(cache_key)
        if price_usd is None:
            row = STORE.get_fx_rate(rate_date=rate_date, base_ccy=asset, quote_ccy="USD") if rate_date else None
            if row is None and rate_date:
                row = STORE.get_fx_rate_on_or_before(rate_date=rate_date, base_ccy=asset, quote_ccy="USD")
            price_usd = _safe_decimal(row.get("rate")) if isinstance(row, dict) else Decimal("0")
            price_cache[cache_key] = price_usd
        if price_usd <= Decimal("0"):
            counterflow_value_usd, counterflow_asset, counterflow_rate_date = _same_tx_priced_counterflow_value_usd(
                payload=payload,
                aliases=aliases,
                events_by_tx=events_by_tx,
                price_cache=price_cache,
            )
            if counterflow_value_usd <= Decimal("0"):
                counterflow_value_usd, counterflow_asset, counterflow_rate_date = _raw_priced_route_counterflow_value_usd(
                    payload=payload,
                    aliases=aliases,
                    price_cache=price_cache,
                )
                if counterflow_value_usd <= Decimal("0"):
                    transformed.append(event)
                    continue
                reference_source = "raw_priced_route_counterflow"
                raw_route_attached += 1
            else:
                reference_source = "same_tx_priced_counterflow"
            updated_payload = dict(payload)
            updated_payload["value_usd_sum"] = counterflow_value_usd.to_eng_string()
            updated_payload["valuation_reference_source"] = reference_source
            updated_payload["valuation_reference_asset"] = counterflow_asset
            updated_payload["valuation_reference_rate_date"] = counterflow_rate_date
            updated_payload["valuation_reference_tx_id"] = _event_tx_id(payload)
            updated_event = dict(event)
            updated_event["payload"] = updated_payload
            transformed.append(updated_event)
            attached += 1
            if reference_source == "same_tx_priced_counterflow":
                counterflow_attached += 1
            continue
        updated_payload = dict(payload)
        updated_payload["price_usd"] = price_usd.to_eng_string()
        updated_payload["valuation_reference_source"] = "fx_cache_asset_usd_swap_in"
        updated_payload["valuation_reference_asset"] = asset
        updated_payload["valuation_reference_rate_date"] = rate_date
        updated_event = dict(event)
        updated_event["payload"] = updated_payload
        transformed.append(updated_event)
        attached += 1
    return transformed, {
        "valuation_anchor_source": "fx_cache_asset_usd_swap_in",
        "attached_price_count": attached,
        "same_tx_priced_counterflow_attached_count": counterflow_attached,
        "raw_priced_route_counterflow_attached_count": raw_route_attached,
        "price_cache_key_count": len(price_cache),
    }


def _same_tx_priced_counterflow_value_usd(
    *,
    payload: dict[str, Any],
    aliases: dict[str, str],
    events_by_tx: dict[str, list[dict[str, Any]]],
    price_cache: dict[tuple[str, str], Decimal],
) -> tuple[Decimal, str, str]:
    tx_id = _event_tx_id(payload)
    target_asset = _asset_price_symbol(payload.get("asset"), aliases)
    rate_date = _event_date(payload)
    if not tx_id or not target_asset or not rate_date:
        return Decimal("0"), "", ""

    total_value_usd = Decimal("0")
    reference_assets: list[str] = []
    for candidate in events_by_tx.get(tx_id, []):
        if candidate is payload:
            continue
        if str(candidate.get("source") or "").lower().strip() != "solana_rpc":
            continue
        if _event_side(candidate) != "out":
            continue
        quantity = _event_quantity(candidate)
        if quantity <= Decimal("0"):
            continue
        candidate_asset = _asset_price_symbol(candidate.get("asset"), aliases)
        if not candidate_asset or candidate_asset == target_asset:
            continue
        if candidate_asset in STABLE_ASSETS:
            value_usd = quantity
        else:
            cache_key = (candidate_asset, rate_date)
            price_usd = price_cache.get(cache_key)
            if price_usd is None:
                row = STORE.get_fx_rate(rate_date=rate_date, base_ccy=candidate_asset, quote_ccy="USD")
                if row is None:
                    row = STORE.get_fx_rate_on_or_before(rate_date=rate_date, base_ccy=candidate_asset, quote_ccy="USD")
                price_usd = _safe_decimal(row.get("rate")) if isinstance(row, dict) else Decimal("0")
                price_cache[cache_key] = price_usd
            if price_usd <= Decimal("0"):
                continue
            value_usd = quantity * price_usd
        if value_usd <= Decimal("0"):
            continue
        total_value_usd += value_usd
        reference_assets.append(candidate_asset)

    if total_value_usd <= Decimal("0"):
        return Decimal("0"), "", ""
    return total_value_usd, "+".join(sorted(set(reference_assets))), rate_date


def _raw_priced_route_counterflow_value_usd(
    *,
    payload: dict[str, Any],
    aliases: dict[str, str],
    price_cache: dict[tuple[str, str], Decimal],
) -> tuple[Decimal, str, str]:
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0"), "", ""
    target_asset = _asset_price_symbol(payload.get("asset"), aliases)
    rate_date = _event_date(payload)
    if not target_asset or not rate_date:
        return Decimal("0"), "", ""

    best_value_usd = Decimal("0")
    best_asset = ""
    for transfer in _iter_raw_token_amounts(raw_row):
        asset = _asset_price_symbol(transfer.get("mint"), aliases)
        quantity = _safe_decimal(transfer.get("quantity"))
        if not asset or asset == target_asset or quantity <= Decimal("0"):
            continue
        if asset in STABLE_ASSETS:
            value_usd = quantity
        else:
            cache_key = (asset, rate_date)
            price_usd = price_cache.get(cache_key)
            if price_usd is None:
                row = STORE.get_fx_rate(rate_date=rate_date, base_ccy=asset, quote_ccy="USD")
                if row is None:
                    row = STORE.get_fx_rate_on_or_before(rate_date=rate_date, base_ccy=asset, quote_ccy="USD")
                price_usd = _safe_decimal(row.get("rate")) if isinstance(row, dict) else Decimal("0")
                price_cache[cache_key] = price_usd
            if price_usd <= Decimal("0"):
                continue
            value_usd = quantity * price_usd
        if value_usd > best_value_usd:
            best_value_usd = value_usd
            best_asset = asset

    if best_value_usd <= Decimal("0"):
        return Decimal("0"), "", ""
    return best_value_usd, best_asset, rate_date


def _iter_raw_token_amounts(value: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            parsed = node.get("parsed")
            if isinstance(parsed, dict):
                info = parsed.get("info")
                if isinstance(info, dict):
                    token_amount = info.get("tokenAmount") or info.get("token_amount")
                    mint = str(info.get("mint") or "").strip()
                    if isinstance(token_amount, dict) and mint:
                        quantity = str(token_amount.get("uiAmountString") or token_amount.get("ui_amount_string") or "").strip()
                        if not quantity:
                            quantity = str(token_amount.get("uiAmount") or token_amount.get("ui_amount") or "").strip()
                        if quantity:
                            out.append({"mint": mint, "quantity": quantity})
                    amount = str(info.get("amount") or "").strip()
                    if mint and amount and "decimals" in info:
                        decimals = int(_safe_decimal(info.get("decimals")))
                        quantity_decimal = _safe_decimal(amount) / (Decimal(10) ** decimals)
                        out.append({"mint": mint, "quantity": quantity_decimal.to_eng_string()})
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return out


def _heliumgeek_display_quantity(payload: dict[str, Any]) -> Decimal:
    if str(payload.get("source", "")).lower().strip() != "heliumgeek":
        return Decimal("0")
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0")
    asset = str(payload.get("asset") or "").upper().strip()
    for token_field, amount_field in (
        ("HNT Token", "HNT Tokens"),
        ("IOT Token", "IOT Tokens"),
        ("MOBILE Token", "MOBILE Tokens"),
    ):
        if str(raw_row.get(token_field, "")).upper().strip() != asset:
            continue
        value = _safe_decimal(raw_row.get(amount_field))
        if value != Decimal("0"):
            return abs(value)
    return Decimal("0")


def _usd_to_eur_rate(payload: dict[str, Any], rate_date: str) -> Decimal:
    direct = _safe_decimal(payload.get("fx_rate_usd_eur"))
    if direct > Decimal("0"):
        return direct
    row = STORE.get_fx_rate_on_or_before(rate_date=rate_date, base_ccy="USD", quote_ccy="EUR") if rate_date else None
    if isinstance(row, dict):
        rate = _safe_decimal(row.get("rate"))
        if rate > Decimal("0"):
            return rate
    fallback = resolve_effective_runtime_config().get("runtime", {}).get("fx", {}).get("usd_to_eur", 1)
    return _safe_decimal(fallback)


def build_tax_domain_value_resolver() -> Any:
    aliases = _load_token_alias_symbols()
    price_cache: dict[tuple[str, str], Decimal] = {}
    fx_cache: dict[str, Decimal] = {}

    def resolve(payload: dict[str, Any]) -> Decimal:
        rate_date = _event_date(payload)
        fx_rate = fx_cache.get(rate_date)
        if fx_rate is None:
            fx_rate = _usd_to_eur_rate(payload, rate_date)
            fx_cache[rate_date] = fx_rate

        for key in ("value_usd", "amount_usd", "income_usd", "proceeds_usd", "raw_value_usd", "raw_amount_usd"):
            usd_value = _safe_decimal(payload.get(key))
            if usd_value > Decimal("0") and fx_rate > Decimal("0"):
                return usd_value * fx_rate

        qty = _event_quantity(payload)
        if qty <= Decimal("0"):
            return Decimal("0")
        asset = _asset_price_symbol(payload.get("asset"), aliases)
        if asset in STABLE_ASSETS and fx_rate > Decimal("0"):
            return qty * fx_rate
        cache_key = (asset, rate_date)
        price = price_cache.get(cache_key)
        if price is None:
            row = STORE.get_fx_rate(rate_date=rate_date, base_ccy=asset, quote_ccy="USD") if rate_date else None
            if row is None and rate_date:
                row = STORE.get_fx_rate_on_or_before(rate_date=rate_date, base_ccy=asset, quote_ccy="USD")
            price = _safe_decimal(row.get("rate")) if isinstance(row, dict) else Decimal("0")
            price_cache[cache_key] = price
        if price > Decimal("0") and fx_rate > Decimal("0"):
            return qty * price * fx_rate
        return Decimal("0")

    return resolve


def _load_tax_event_overrides() -> dict[str, dict[str, str]]:
    row = STORE.get_setting("runtime.tax_event_overrides")
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for event_id_raw, payload in raw.items():
        event_id = str(event_id_raw).strip()
        if not event_id or not isinstance(payload, dict):
            continue
        category = str(payload.get("tax_category", "")).strip().upper()
        if category not in {"PRIVATE_SO", "BUSINESS", "EXCLUDED"}:
            continue
        result[event_id] = {
            "tax_category": category,
            "reason_code": str(payload.get("reason_code", "")).strip(),
            "reason_label": str(payload.get("reason_label", "")).strip(),
            "note": str(payload.get("note", "")).strip(),
            "updated_at_utc": str(payload.get("updated_at_utc", "")).strip(),
        }
    return result


def _load_review_actions() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting("runtime.review_actions")
    empty: dict[str, dict[str, Any]] = {"timezone_corrections": {}, "merges": {}, "splits": {}}
    if row is None:
        return empty
    try:
        raw = json.loads(str(row.get("value_json", "{}")))
    except Exception:
        return empty
    if not isinstance(raw, dict):
        return empty
    result: dict[str, dict[str, Any]] = {"timezone_corrections": {}, "merges": {}, "splits": {}}
    for section in result:
        value = raw.get(section, {})
        if isinstance(value, dict):
            result[section] = value
    return result


def apply_review_actions(raw_events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    actions = _load_review_actions()
    timezone_corrections = actions.get("timezone_corrections", {})
    merges = actions.get("merges", {})
    splits = actions.get("splits", {})
    if not timezone_corrections and not merges and not splits:
        return raw_events, {"timezone_correction_count": 0, "merge_annotation_count": 0, "split_replacement_count": 0}

    merge_index: dict[str, dict[str, Any]] = {}
    for action_id, merge in merges.items():
        if not isinstance(merge, dict):
            continue
        for event_id in merge.get("source_event_ids", []):
            event_id_str = str(event_id or "").strip()
            if event_id_str:
                merge_index[event_id_str] = {"action_id": str(action_id), **merge}

    transformed: list[dict[str, Any]] = []
    applied_timezone = 0
    applied_merges = 0
    applied_splits = 0
    for event in raw_events:
        event_id = str(event.get("unique_event_id", "")).strip()
        split_action = splits.get(event_id)
        if isinstance(split_action, dict):
            payload = event.get("payload", {})
            split_rows = split_action.get("split_rows", [])
            if isinstance(payload, dict) and isinstance(split_rows, list) and split_rows:
                for index, split_row in enumerate(split_rows, start=1):
                    if not isinstance(split_row, dict):
                        continue
                    payload_copy = dict(payload)
                    for key, value in split_row.items():
                        normalized_key = "amount" if str(key) == "quantity" else str(key)
                        payload_copy[normalized_key] = value
                    payload_copy["review_action"] = "split"
                    payload_copy["review_action_id"] = str(split_action.get("action_id", f"split:{event_id}"))
                    payload_copy["review_action_parent_event_id"] = event_id
                    payload_copy["review_action_note"] = str(split_action.get("note", "")).strip()
                    payload_copy["review_action_updated_at_utc"] = str(split_action.get("updated_at_utc", "")).strip()
                    event_copy = dict(event)
                    event_copy["unique_event_id"] = f"{event_id}:split:{index}"
                    event_copy["payload"] = payload_copy
                    transformed.append(event_copy)
                    applied_splits += 1
                continue

        correction = timezone_corrections.get(event_id)
        event_copy = dict(event)
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event_copy)
            continue
        payload_copy = dict(payload)
        if not isinstance(correction, dict):
            correction = None
        if correction is not None:
            corrected_timestamp = str(correction.get("corrected_timestamp_utc", "")).strip()
            if corrected_timestamp:
                payload_copy["original_timestamp_utc"] = payload_copy.get("timestamp_utc", "")
                payload_copy["timestamp_utc"] = corrected_timestamp
                payload_copy["review_action"] = "timezone_correct"
                payload_copy["review_action_note"] = str(correction.get("note", "")).strip()
                payload_copy["review_action_updated_at_utc"] = str(correction.get("updated_at_utc", "")).strip()
                applied_timezone += 1
        merge_action = merge_index.get(event_id)
        if merge_action is not None:
            payload_copy["review_merge_action_id"] = str(merge_action.get("action_id", ""))
            payload_copy["economic_event_id"] = str(merge_action.get("action_id", ""))
            payload_copy["review_merge_note"] = str(merge_action.get("note", "")).strip()
            applied_merges += 1
        event_copy["payload"] = payload_copy
        transformed.append(event_copy)

    return transformed, {
        "timezone_correction_count": applied_timezone,
        "merge_annotation_count": applied_merges,
        "split_replacement_count": applied_splits,
    }


def apply_tax_event_overrides(raw_events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    overrides = _load_tax_event_overrides()
    if not overrides:
        return raw_events, 0
    transformed: list[dict[str, Any]] = []
    applied = 0
    for event in raw_events:
        event_id = str(event.get("unique_event_id", "")).strip()
        override = overrides.get(event_id)
        if override is None:
            transformed.append(event)
            continue
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            transformed.append(event)
            continue
        payload_copy = dict(payload)
        category = override["tax_category"]
        if category == "EXCLUDED":
            applied += 1
            continue
        payload_copy["tax_category"] = "BUSINESS" if category == "BUSINESS" else "INCOME_SO"
        payload_copy["tax_override_note"] = override.get("note", "")
        payload_copy["tax_override_updated_at_utc"] = override.get("updated_at_utc") or datetime.now(UTC).isoformat()
        event_copy = dict(event)
        event_copy["payload"] = payload_copy
        transformed.append(event_copy)
        applied += 1
    return transformed, applied


def create_processing_job(payload: ProcessRunRequest) -> dict[str, Any]:
    registry = build_default_registry()
    ruleset, _warnings = registry.resolve_for_year(
        tax_year=payload.tax_year,
        ruleset_id=payload.ruleset_id,
        ruleset_version=payload.ruleset_version,
    )
    job_id = str(uuid4())
    cfg_hash = config_fingerprint(
        {
            "tax_year": payload.tax_year,
            "ruleset_id": ruleset.ruleset_id,
            "ruleset_version": ruleset.ruleset_version,
            "dry_run": payload.dry_run,
            "config": payload.config,
        }
    )
    STORE.create_processing_job(
        job_id=job_id,
        tax_year=payload.tax_year,
        ruleset_id=ruleset.ruleset_id,
        ruleset_version=ruleset.ruleset_version,
        config_hash=cfg_hash,
        config_json=json.dumps(payload.config, sort_keys=True, separators=(",", ":")),
        status="queued",
        progress=0,
    )
    job = STORE.get_processing_job(job_id)
    if job is None:
        raise RuntimeError("Job creation failed unexpectedly")
    return job


def get_processing_job(job_id: str) -> dict[str, Any] | None:
    return STORE.get_processing_job(job_id)


def run_next_queued_job(simulate_fail: bool = False) -> dict[str, Any] | None:
    claimed = STORE.claim_next_queued_job()
    if claimed is None:
        return None

    job_id = claimed["job_id"]
    try:
        STORE.update_processing_job_state(
            job_id=job_id,
            status="running",
            progress=35,
            current_step="load_events",
        )
        job_config = claimed.get("config", {}) if isinstance(claimed.get("config"), dict) else {}
        all_raw_events = STORE.list_raw_events()
        raw_events, integration_filter_summary = filter_events_for_processing(all_raw_events, job_config)
        raw_events, malformed_binance_summary = drop_malformed_binance_market_summary_events(raw_events)
        raw_events, pionex_duplicate_summary = drop_exact_pionex_duplicate_events(raw_events)
        raw_events, solscan_duplicate_summary = drop_solscan_duplicates_when_solana_rpc_is_active(raw_events)
        raw_events, review_action_summary = apply_review_actions(raw_events)
        raw_events, helium_solana_claim_summary = label_helium_solana_claim_events(raw_events)
        raw_events, valuation_anchor_summary = attach_reference_usd_value_anchors(raw_events, all_raw_events)
        raw_events, bitget_spot_anchor_summary = attach_bitget_tax_api_spot_trade_value_anchors(raw_events)
        raw_events, binance_market_anchor_summary = attach_binance_market_quote_value_anchors(raw_events)
        raw_events, binance_fiat_purchase_summary = attach_binance_fiat_purchase_value_anchors(raw_events)
        raw_events, binance_txhist_anchor_summary = (
            attach_binance_transaction_history_stable_counterflow_value_anchors(raw_events)
        )
        raw_events, binance_dust_price_summary = attach_cached_usd_prices_to_binance_dust_convert_in_events(raw_events)
        raw_events, reward_price_summary = attach_cached_usd_prices_to_reward_events(raw_events)
        raw_events, swap_in_price_summary = attach_cached_usd_prices_to_swap_in_events(raw_events)
        effective_events, override_count = apply_tax_event_overrides(raw_events)
        fx_config = resolve_effective_runtime_config()
        runtime_fx = fx_config.get("runtime", {}).get("fx", {})
        fallback_rate = runtime_fx.get("usd_to_eur", 1.0)
        fx_resolver = FallbackFxResolver(fallback_rate=fallback_rate)
        effective_events, fx_summary = fx_resolver.enrich_events_with_fx(effective_events)
        STORE.upsert_setting(
            setting_key="runtime.fx.unresolved_events",
            value_json=json.dumps(fx_summary.get("unresolved_events", []), separators=(",", ":")),
            is_secret=False,
        )

        STORE.update_processing_job_state(
            job_id=job_id,
            status="running",
            progress=70,
            current_step="core_processing",
        )
        ruleset_id = str(claimed["ruleset_id"])
        ruleset_version = claimed.get("ruleset_version")
        if ruleset_version is not None and not str(ruleset_version).strip():
            ruleset_version = None

        processing_result = process_events_for_year(
            raw_events=effective_events,
            tax_year=claimed["tax_year"],
            ruleset_id=ruleset_id,
            ruleset_version=ruleset_version,
            transfer_matches=STORE.list_transfer_matches(),
        )
        processing_result["integration_filter_summary"] = integration_filter_summary
        processing_result["malformed_binance_summary"] = malformed_binance_summary
        processing_result["pionex_duplicate_summary"] = pionex_duplicate_summary
        processing_result["solscan_duplicate_summary"] = solscan_duplicate_summary
        processing_result["helium_solana_claim_summary"] = helium_solana_claim_summary
        processing_result["valuation_anchor_summary"] = valuation_anchor_summary
        processing_result["bitget_spot_anchor_summary"] = bitget_spot_anchor_summary
        processing_result["binance_market_anchor_summary"] = binance_market_anchor_summary
        processing_result["binance_fiat_purchase_summary"] = binance_fiat_purchase_summary
        processing_result["binance_transaction_history_anchor_summary"] = binance_txhist_anchor_summary
        processing_result["binance_dust_price_summary"] = binance_dust_price_summary
        processing_result["reward_price_summary"] = reward_price_summary
        processing_result["swap_in_price_summary"] = swap_in_price_summary
        tax_lines = processing_result.pop("tax_lines")
        tax_lines = _attach_transfer_trace(tax_lines)
        derivative_result = process_derivatives_for_year(raw_events=effective_events, tax_year=claimed["tax_year"])
        derivative_lines = derivative_result.pop("lines")
        tax_domain_summary = build_tax_domain_summary(
            raw_events=effective_events,
            tax_lines=tax_lines,
            derivative_lines=derivative_lines,
            tax_year=claimed["tax_year"],
            ruleset_id=ruleset_id,
            value_resolver=build_tax_domain_value_resolver(),
        )

        registry = build_default_registry()
        ruleset = registry.get(ruleset_id, ruleset_version)
        ruleset_hash = ruleset_fingerprint(ruleset)

        event_ids = [event.get("unique_event_id", "") for event in effective_events]
        data_hash = data_fingerprint([str(value) for value in event_ids])
        integrity_id = report_integrity_id(
            event_hashes=[str(event_id) for event_id in event_ids],
            ruleset_hash=ruleset_hash,
            config_hash=claimed["config_hash"],
        )
        STORE.insert_report_integrity(
            job_id=job_id,
            data_hash=data_hash,
            ruleset_id=ruleset_id,
            ruleset_version=ruleset.ruleset_version,
            ruleset_hash=ruleset_hash,
            config_hash=claimed["config_hash"],
            report_integrity_id=integrity_id,
            event_count=len(event_ids),
            run_started_at_utc=claimed["created_at_utc"],
        )

        if simulate_fail:
            raise RuntimeError("Simulated worker error")

        STORE.replace_tax_lines(job_id=job_id, tax_lines=tax_lines)
        STORE.replace_derivative_lines(job_id=job_id, derivative_lines=derivative_lines)
        processing_result["derivatives"] = derivative_result
        processing_result["tax_domain_summary"] = tax_domain_summary
        processing_result["tax_event_override_count"] = override_count
        processing_result["review_actions"] = review_action_summary
        processing_result["fx_enrichment"] = fx_summary
        processing_result["ruleset_id"] = ruleset_id
        processing_result["ruleset_version"] = ruleset.ruleset_version
        processing_result["report_integrity_id"] = integrity_id

        STORE.update_processing_job_state(
            job_id=job_id,
            status="completed",
            progress=100,
            current_step="completed",
            error_message=None,
            result_json=json.dumps(processing_result, sort_keys=True, separators=(",", ":")),
        )
    except Exception as exc:
        STORE.update_processing_job_state(
            job_id=job_id,
            status="failed",
            progress=70,
            current_step="failed",
            error_message=str(exc),
            result_json=None,
        )

    return STORE.get_processing_job(job_id)


def _attach_transfer_trace(tax_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transfer_chain_by_event_id = build_transfer_chain_index(STORE.list_transfer_matches())

    enriched: list[dict[str, Any]] = []
    for line in tax_lines:
        row = dict(line)
        lot_source_event_id = str(row.get("lot_source_event_id", "")).strip()
        sell_source_event_id = str(row.get("source_event_id", "")).strip()
        row["transfer_chain_id"] = (
            transfer_chain_by_event_id.get(lot_source_event_id)
            or transfer_chain_by_event_id.get(sell_source_event_id)
            or str(row.get("transfer_chain_id", "")).strip()
        )
        enriched.append(row)
    return enriched
