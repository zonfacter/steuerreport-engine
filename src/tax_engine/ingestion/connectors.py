from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Any

from .parser import parse_datetime_value, parse_decimal_value


@dataclass(frozen=True)
class ConnectorSpec:
    connector_id: str
    label: str
    modes: tuple[str, ...]
    # Deutsche Kommentare: Aliaslisten kapseln abweichende CSV-Spaltennamen pro Anbieter.
    aliases: dict[str, tuple[str, ...]]


CONNECTOR_SPECS: dict[str, ConnectorSpec] = {
    "binance": ConnectorSpec(
        connector_id="binance",
        label="Binance",
        modes=("csv", "xlsx", "api_planned"),
        aliases={
            "timestamp": ("timestamp", "time", "date", "utc_time", "date(utc)", "datetime", "created time"),
            "asset": ("asset", "coin", "baseasset", "currency", "symbol", "base asset"),
            "quantity": ("amount", "qty", "quantity", "executed", "filled", "size", "change"),
            "price": ("price", "avgprice", "average", "avg price", "deal price"),
            "fee": ("fee", "trading fee", "commission", "transactionfee", "transaction fee"),
            "fee_asset": ("fee coin", "fee asset", "commissionasset", "commission asset", "fee currency"),
            "side": ("side", "type", "order side", "direction"),
            "event_type": ("operation", "transaction type", "type", "category", "business type"),
            "tx_id": ("transaction id", "order id", "orderid", "txid", "trade id", "tradeid", "tranid", "id"),
            "from_asset": ("from coin", "from asset", "from currency"),
            "to_asset": ("to coin", "to asset", "to currency"),
            "from_amount": ("from amount", "source amount"),
            "to_amount": ("to amount", "target amount", "amount received"),
            "network": ("network", "chain"),
            "address": ("address", "wallet address"),
        },
    ),
    "bitget": ConnectorSpec(
        connector_id="bitget",
        label="Bitget",
        modes=("csv", "xlsx", "api_planned"),
        aliases={
            "timestamp": ("time", "timestamp", "date"),
            "asset": ("coin", "asset", "currency", "symbol"),
            "quantity": ("size", "amount", "filled amount", "quantity"),
            "price": ("price", "avg price", "deal price"),
            "fee": ("fee", "transaction fee"),
            "fee_asset": ("fee coin", "fee currency", "fee asset"),
            "side": ("side", "trade type", "type"),
            "event_type": ("business type", "type", "event"),
            "tx_id": ("order id", "trade id", "txid"),
        },
    ),
    "coinbase": ConnectorSpec(
        connector_id="coinbase",
        label="Coinbase",
        modes=("csv", "xlsx", "api_planned"),
        aliases={
            "timestamp": ("timestamp", "time", "created at"),
            "asset": ("asset", "currency", "amount currency"),
            "quantity": ("amount", "quantity", "native amount"),
            "price": ("spot price", "price"),
            "fee": ("fees", "fee"),
            "fee_asset": ("fee currency", "asset"),
            "side": ("transaction type", "type", "side"),
            "event_type": ("transaction type", "type"),
            "tx_id": ("transaction id", "id"),
        },
    ),
    "pionex": ConnectorSpec(
        connector_id="pionex",
        label="Pionex",
        modes=("csv", "xlsx", "api_planned"),
        aliases={
            "timestamp": ("time", "date", "timestamp"),
            "asset": ("coin", "asset", "currency", "symbol"),
            "quantity": ("amount", "quantity", "filled", "deal amount"),
            "price": ("price", "deal price", "avg price"),
            "fee": ("fee", "trading fee"),
            "fee_asset": ("fee coin", "fee currency", "fee asset"),
            "side": ("side", "type"),
            "event_type": ("type", "order type", "business type"),
            "tx_id": ("order id", "trade id", "txid"),
        },
    ),
    "blockpit": ConnectorSpec(
        connector_id="blockpit",
        label="Blockpit Export",
        modes=("csv", "xlsx"),
        aliases={
            "timestamp": ("timestamp", "date", "time", "date (utc)"),
            "asset": ("buy cur", "sell cur", "asset", "currency"),
            "quantity": ("buy amount", "sell amount", "amount", "quantity"),
            "price": ("rate", "price"),
            "fee": ("fee amount", "fee", "fee value", "fee amount (optional)"),
            "fee_asset": ("fee currency", "fee asset", "fee asset (optional)"),
            "side": ("type", "direction"),
            "event_type": ("type", "transaction type"),
            "tx_id": ("txid", "transaction id", "id"),
            "incoming_asset": ("incoming asset", "buy cur"),
            "incoming_amount": ("incoming amount", "buy amount"),
            "outgoing_asset": ("outgoing asset", "sell cur"),
            "outgoing_amount": ("outgoing amount", "sell amount"),
            "label": ("label",),
        },
    ),
    "heliumgeek": ConnectorSpec(
        connector_id="heliumgeek",
        label="HeliumGeek Export",
        modes=("csv",),
        aliases={
            "timestamp": ("period start (utc)", "period start"),
            "asset": ("iot token", "mobile token"),
            "quantity": ("iot tokens", "mobile tokens"),
            "event_type": ("tag", "type"),
            "tx_id": ("gateway address",),
            "gateway": ("gateway address",),
            "name": ("name",),
            "tag": ("tag",),
            "iot_tokens": ("iot tokens",),
            "mobile_tokens": ("mobile tokens",),
            "iot_token_asset": ("iot token",),
            "mobile_token_asset": ("mobile token",),
            "raw_timestamp": ("date",),
            "raw_event_type": ("type",),
            "raw_tx_id": ("transaction_hash",),
            "raw_hnt_amount": ("hnt_amount",),
            "raw_hnt_fee": ("hnt_fee",),
            "raw_mobile_amount": ("mobile_amount",),
            "raw_usd_price": ("usd_oracle_price",),
            "raw_usd_amount": ("usd_amount",),
            "raw_usd_fee": ("usd_fee",),
            "raw_payer": ("payer",),
            "raw_payee": ("payee",),
            "raw_block": ("block",),
        },
    ),
}


def list_connectors() -> list[dict[str, Any]]:
    connectors: list[dict[str, Any]] = []
    for spec in CONNECTOR_SPECS.values():
        connectors.append(
            {
                "connector_id": spec.connector_id,
                "label": spec.label,
                "modes": list(spec.modes),
            }
        )
    return connectors


def _norm_key(key: str) -> str:
    return key.strip().lower().replace("_", " ")


def _get_value(row: dict[str, Any], aliases: tuple[str, ...]) -> Any | None:
    normalized_row = {_norm_key(str(k)): v for k, v in row.items()}
    for alias in aliases:
        value = normalized_row.get(_norm_key(alias))
        if value is not None and value != "":
            return value
    return None


def _normalize_binance_row(spec: ConnectorSpec, row: dict[str, Any], idx: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    warnings: list[dict[str, str]] = []
    out_rows: list[dict[str, Any]] = []

    timestamp_raw = _get_value(row, spec.aliases["timestamp"])
    event_type_raw = _get_value(row, spec.aliases["event_type"])
    side_raw = _get_value(row, spec.aliases["side"])
    tx_id_raw = _get_value(row, spec.aliases["tx_id"])
    network_raw = _get_value(row, spec.aliases.get("network", tuple()))
    address_raw = _get_value(row, spec.aliases.get("address", tuple()))

    timestamp_utc: str | None = None
    if timestamp_raw is not None:
        parsed_ts, ts_error = parse_datetime_value(timestamp_raw)
        if ts_error:
            warnings.append({"row": str(idx), "code": ts_error, "field": "timestamp"})
            timestamp_utc = str(timestamp_raw)
        else:
            timestamp_utc = parsed_ts

    def _num(value: Any, field: str) -> str:
        if value is None:
            return ""
        parsed, parse_error = parse_decimal_value(value)
        if parse_error:
            warnings.append({"row": str(idx), "code": parse_error, "field": field})
            return str(value)
        if parsed is None:
            return ""
        return parsed.to_eng_string()

    # Deutsche Kommentare: Convert-Exports enthalten From/To als zwei Assets in einer Zeile.
    from_asset = _get_value(row, spec.aliases.get("from_asset", tuple()))
    to_asset = _get_value(row, spec.aliases.get("to_asset", tuple()))
    from_amount = _get_value(row, spec.aliases.get("from_amount", tuple()))
    to_amount = _get_value(row, spec.aliases.get("to_amount", tuple()))
    if from_asset is not None and to_asset is not None and (from_amount is not None or to_amount is not None):
        tx_id = str(tx_id_raw) if tx_id_raw is not None else f"binance-convert-{idx}"
        event_type = str(event_type_raw).lower() if event_type_raw is not None else "convert"
        out_rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "asset": str(from_asset).upper(),
                "quantity": _num(from_amount, "from_amount"),
                "price": "",
                "fee": "",
                "fee_asset": "",
                "side": "out",
                "event_type": f"{event_type}_out",
                "tx_id": f"{tx_id}:out",
                "network": str(network_raw) if network_raw is not None else "",
                "address": str(address_raw) if address_raw is not None else "",
                "source": "binance",
                "raw_row": row,
            }
        )
        out_rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "asset": str(to_asset).upper(),
                "quantity": _num(to_amount, "to_amount"),
                "price": "",
                "fee": "",
                "fee_asset": "",
                "side": "in",
                "event_type": f"{event_type}_in",
                "tx_id": f"{tx_id}:in",
                "network": str(network_raw) if network_raw is not None else "",
                "address": str(address_raw) if address_raw is not None else "",
                "source": "binance",
                "raw_row": row,
            }
        )
        return out_rows, warnings

    asset_raw = _get_value(row, spec.aliases["asset"])
    quantity_raw = _get_value(row, spec.aliases["quantity"])
    price_raw = _get_value(row, spec.aliases["price"])
    fee_raw = _get_value(row, spec.aliases["fee"])
    fee_asset_raw = _get_value(row, spec.aliases["fee_asset"])

    if quantity_raw is None and asset_raw is None:
        warnings.append({"row": str(idx), "code": "row_not_mappable"})
        return out_rows, warnings

    parsed_qty, qty_error = parse_decimal_value(quantity_raw) if quantity_raw is not None else (None, None)
    if qty_error:
        warnings.append({"row": str(idx), "code": qty_error, "field": "quantity"})
    inferred_side = ""
    if parsed_qty is not None:
        if parsed_qty < 0:
            inferred_side = "out"
        elif parsed_qty > 0:
            inferred_side = "in"
    side = str(side_raw).strip().lower() if side_raw is not None else inferred_side

    out_rows.append(
        {
            "timestamp_utc": timestamp_utc,
            "asset": str(asset_raw).upper() if asset_raw is not None else "",
            "quantity": parsed_qty.to_eng_string() if parsed_qty is not None else "",
            "price": _num(price_raw, "price"),
            "fee": _num(fee_raw, "fee"),
            "fee_asset": str(fee_asset_raw).upper() if fee_asset_raw is not None else "",
            "side": side,
            "event_type": str(event_type_raw).lower() if event_type_raw is not None else "",
            "tx_id": str(tx_id_raw) if tx_id_raw is not None else "",
            "network": str(network_raw) if network_raw is not None else "",
            "address": str(address_raw) if address_raw is not None else "",
            "source": "binance",
            "raw_row": row,
        }
    )
    return out_rows, warnings


def _normalize_blockpit_row(spec: ConnectorSpec, row: dict[str, Any], idx: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    warnings: list[dict[str, str]] = []
    out_rows: list[dict[str, Any]] = []
    timestamp_raw = _get_value(row, spec.aliases["timestamp"])
    tx_id_raw = _get_value(row, spec.aliases["tx_id"])
    label_raw = _get_value(row, spec.aliases.get("label", tuple()))
    incoming_asset_raw = _get_value(row, spec.aliases.get("incoming_asset", tuple()))
    incoming_amount_raw = _get_value(row, spec.aliases.get("incoming_amount", tuple()))
    outgoing_asset_raw = _get_value(row, spec.aliases.get("outgoing_asset", tuple()))
    outgoing_amount_raw = _get_value(row, spec.aliases.get("outgoing_amount", tuple()))
    fee_asset_raw = _get_value(row, spec.aliases["fee_asset"])
    fee_raw = _get_value(row, spec.aliases["fee"])

    timestamp_utc: str | None = None
    if timestamp_raw is not None:
        parsed_ts, ts_error = parse_datetime_value(timestamp_raw)
        if ts_error:
            warnings.append({"row": str(idx), "code": ts_error, "field": "timestamp"})
            timestamp_utc = str(timestamp_raw)
        else:
            timestamp_utc = parsed_ts

    def _num(value: Any, field: str) -> str:
        if value is None:
            return ""
        parsed, parse_error = parse_decimal_value(value)
        if parse_error:
            warnings.append({"row": str(idx), "code": parse_error, "field": field})
            return str(value)
        if parsed is None:
            return ""
        return parsed.to_eng_string()

    base_tx = str(tx_id_raw) if tx_id_raw is not None and str(tx_id_raw).strip() else f"blockpit-{idx}"
    label = str(label_raw).strip().lower() if label_raw is not None else "transfer"

    incoming_amount = _num(incoming_amount_raw, "incoming_amount")
    outgoing_amount = _num(outgoing_amount_raw, "outgoing_amount")
    fee_amount = _num(fee_raw, "fee")

    if outgoing_asset_raw and outgoing_amount not in ("", "0"):
        out_rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "asset": str(outgoing_asset_raw).upper(),
                "quantity": outgoing_amount,
                "price": "",
                "fee": "",
                "fee_asset": "",
                "side": "out",
                "event_type": label or "outflow",
                "tx_id": f"{base_tx}:out",
                "source": "blockpit",
                "raw_row": row,
            }
        )
    if incoming_asset_raw and incoming_amount not in ("", "0"):
        out_rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "asset": str(incoming_asset_raw).upper(),
                "quantity": incoming_amount,
                "price": "",
                "fee": "",
                "fee_asset": "",
                "side": "in",
                "event_type": label or "inflow",
                "tx_id": f"{base_tx}:in",
                "source": "blockpit",
                "raw_row": row,
            }
        )
    if fee_asset_raw and fee_amount not in ("", "0"):
        out_rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "asset": str(fee_asset_raw).upper(),
                "quantity": fee_amount,
                "price": "",
                "fee": "",
                "fee_asset": "",
                "side": "out",
                "event_type": "fee",
                "tx_id": f"{base_tx}:fee",
                "source": "blockpit",
                "raw_row": row,
            }
        )
    if not out_rows:
        warnings.append({"row": str(idx), "code": "row_not_mappable"})
    return out_rows, warnings


def _normalize_heliumgeek_row(spec: ConnectorSpec, row: dict[str, Any], idx: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    warnings: list[dict[str, str]] = []
    out_rows: list[dict[str, Any]] = []
    timestamp_raw = _get_value(row, spec.aliases["timestamp"])
    gateway_raw = _get_value(row, spec.aliases.get("gateway", tuple()))
    name_raw = _get_value(row, spec.aliases.get("name", tuple()))
    tag_raw = _get_value(row, spec.aliases.get("tag", tuple()))

    timestamp_utc: str | None = None
    if timestamp_raw is not None:
        parsed_ts, ts_error = parse_datetime_value(timestamp_raw)
        if ts_error:
            warnings.append({"row": str(idx), "code": ts_error, "field": "timestamp"})
            timestamp_utc = str(timestamp_raw)
        else:
            timestamp_utc = parsed_ts

    def _parse_helium_decimal(value: Any, field: str) -> tuple[str, str | None]:
        if value is None:
            return "", None
        raw = str(value).strip()
        if not raw:
            return "", None

        # Deutsche Kommentare:
        # 1) Helium-Exports nutzen oft Komma als Dezimaltrennzeichen.
        # 2) In einigen Zeilen taucht fehlerhaft "e.7" statt "e-7" auf.
        repaired = raw.replace("e.", "e-").replace("E.", "E-")
        locale_hint = "comma_decimal" if "," in repaired else None
        parsed, parse_error = parse_decimal_value(repaired, locale_hint=locale_hint)
        if parse_error is None and parsed is not None:
            return parsed.to_eng_string(), None

        # Fallback: falls doch Punkt-Notation vorliegt, nochmals ohne festen Locale-Hint parsen.
        parsed_fallback, fallback_error = parse_decimal_value(repaired)
        if fallback_error is None and parsed_fallback is not None:
            return parsed_fallback.to_eng_string(), None

        return "", parse_error or fallback_error or "invalid_numeric_token"

    def _maybe_add(asset_key: str, amount_key: str, suffix: str) -> None:
        asset_raw = _get_value(row, spec.aliases.get(asset_key, tuple()))
        amount_raw = _get_value(row, spec.aliases.get(amount_key, tuple()))
        if asset_raw is None or amount_raw is None:
            return
        amount_value, amount_error = _parse_helium_decimal(amount_raw, amount_key)
        if amount_error:
            warnings.append({"row": str(idx), "code": amount_error, "field": amount_key})
            return
        if amount_value in ("", "0", "0.0", "-0", "-0.0"):
            return
        gateway = str(gateway_raw).strip() if gateway_raw is not None else ""
        period = str(timestamp_raw).strip() if timestamp_raw is not None else str(idx)
        out_rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "asset": str(asset_raw).upper(),
                "quantity": amount_value,
                "price": "",
                "fee": "",
                "fee_asset": "",
                "side": "in",
                "event_type": "mining_reward",
                "tx_id": f"heliumgeek:{gateway}:{period}:{suffix}",
                "gateway_address": gateway,
                "gateway_name": str(name_raw) if name_raw is not None else "",
                "tag": str(tag_raw) if tag_raw is not None else "",
                "source": "heliumgeek",
                "raw_row": row,
            }
        )

    _maybe_add("iot_token_asset", "iot_tokens", "iot")
    _maybe_add("mobile_token_asset", "mobile_tokens", "mobile")
    if not out_rows:
        # Fallback für Helium "all-raw" Exporte (block;date;type;transaction_hash;...).
        raw_ts = _get_value(row, spec.aliases.get("raw_timestamp", tuple()))
        raw_type = _get_value(row, spec.aliases.get("raw_event_type", tuple()))
        raw_tx = _get_value(row, spec.aliases.get("raw_tx_id", tuple()))
        raw_block = _get_value(row, spec.aliases.get("raw_block", tuple()))
        raw_payer = _get_value(row, spec.aliases.get("raw_payer", tuple()))
        raw_payee = _get_value(row, spec.aliases.get("raw_payee", tuple()))

        raw_timestamp_utc: str | None = None
        if raw_ts is not None:
            parsed_ts, ts_error = parse_datetime_value(raw_ts)
            if ts_error:
                warnings.append({"row": str(idx), "code": ts_error, "field": "date"})
                raw_timestamp_utc = str(raw_ts)
            else:
                raw_timestamp_utc = parsed_ts

        def _raw_num(alias_key: str, field_name: str) -> str:
            value = _get_value(row, spec.aliases.get(alias_key, tuple()))
            parsed_text, parse_error = _parse_helium_decimal(value, field_name)
            if parse_error:
                warnings.append({"row": str(idx), "code": parse_error, "field": field_name})
                return ""
            return parsed_text

        hnt_amount = _raw_num("raw_hnt_amount", "hnt_amount")
        mobile_amount = _raw_num("raw_mobile_amount", "mobile_amount")
        hnt_fee = _raw_num("raw_hnt_fee", "hnt_fee")
        usd_price = _raw_num("raw_usd_price", "usd_oracle_price")
        usd_amount = _raw_num("raw_usd_amount", "usd_amount")
        usd_fee = _raw_num("raw_usd_fee", "usd_fee")

        def _side_for(amount_text: str) -> str:
            parsed, _ = parse_decimal_value(amount_text)
            if parsed is None:
                return ""
            return "in" if parsed >= 0 else "out"

        base_tx = str(raw_tx).strip() if raw_tx is not None and str(raw_tx).strip() else f"helium-raw-{idx}"
        event_type = str(raw_type).strip().lower() if raw_type is not None else "helium_raw"

        if hnt_amount not in ("", "0", "0.0"):
            out_rows.append(
                {
                    "timestamp_utc": raw_timestamp_utc,
                    "asset": "HNT",
                    "quantity": hnt_amount.lstrip("+"),
                    "price": usd_price,
                    "fee": "",
                    "fee_asset": "",
                    "side": _side_for(hnt_amount),
                    "event_type": event_type,
                    "tx_id": f"{base_tx}:hnt",
                    "network": "helium",
                    "address": str(raw_payee or raw_payer or ""),
                    "source": "heliumgeek",
                    "gateway_address": str(gateway_raw or ""),
                    "payer": str(raw_payer or ""),
                    "payee": str(raw_payee or ""),
                    "block": str(raw_block or ""),
                    "amount_usd": usd_amount,
                    "raw_row": row,
                }
            )
        if mobile_amount not in ("", "0", "0.0"):
            out_rows.append(
                {
                    "timestamp_utc": raw_timestamp_utc,
                    "asset": "MOBILE",
                    "quantity": mobile_amount.lstrip("+"),
                    "price": usd_price,
                    "fee": "",
                    "fee_asset": "",
                    "side": _side_for(mobile_amount),
                    "event_type": event_type,
                    "tx_id": f"{base_tx}:mobile",
                    "network": "helium",
                    "address": str(raw_payee or raw_payer or ""),
                    "source": "heliumgeek",
                    "gateway_address": str(gateway_raw or ""),
                    "payer": str(raw_payer or ""),
                    "payee": str(raw_payee or ""),
                    "block": str(raw_block or ""),
                    "amount_usd": usd_amount,
                    "raw_row": row,
                }
            )
        if hnt_fee not in ("", "0", "0.0"):
            out_rows.append(
                {
                    "timestamp_utc": raw_timestamp_utc,
                    "asset": "HNT",
                    "quantity": hnt_fee.lstrip("+"),
                    "price": "",
                    "fee": hnt_fee.lstrip("+"),
                    "fee_asset": "HNT",
                    "side": "out",
                    "event_type": "fee",
                    "tx_id": f"{base_tx}:fee_hnt",
                    "network": "helium",
                    "address": str(raw_payer or ""),
                    "source": "heliumgeek",
                    "gateway_address": str(gateway_raw or ""),
                    "payer": str(raw_payer or ""),
                    "payee": str(raw_payee or ""),
                    "block": str(raw_block or ""),
                    "fee_usd": usd_fee,
                    "raw_row": row,
                }
            )

    if not out_rows:
        # Rewards-Zeilen mit exakt 0-Zufluss sind in Helium-Exports möglich und kein echter Mapping-Fehler.
        row_type = str(_get_value(row, spec.aliases.get("raw_event_type", tuple())) or "").strip().lower()
        if row_type.startswith("rewards"):
            hnt_value, _ = _parse_helium_decimal(_get_value(row, spec.aliases.get("raw_hnt_amount", tuple())), "hnt_amount")
            mobile_value, _ = _parse_helium_decimal(
                _get_value(row, spec.aliases.get("raw_mobile_amount", tuple())),
                "mobile_amount",
            )
            if hnt_value in ("", "0", "0.0", "-0", "-0.0") and mobile_value in ("", "0", "0.0", "-0", "-0.0"):
                return out_rows, warnings
        warnings.append({"row": str(idx), "code": "row_not_mappable"})
    return out_rows, warnings


def normalize_connector_rows(
    connector_id: str,
    rows: list[dict[str, Any]],
    max_rows: int = 5000,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    spec = CONNECTOR_SPECS.get(connector_id.lower())
    if spec is None:
        return [], [], [{"code": "unsupported_connector", "message": connector_id}]

    normalized_rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    limited_rows = rows[:max_rows]

    for idx, row in enumerate(limited_rows):
        if connector_id.lower() == "binance":
            row_items, row_warnings = _normalize_binance_row(spec, row, idx)
            warnings.extend(row_warnings)
            normalized_rows.extend(row_items)
            continue
        if connector_id.lower() == "blockpit":
            row_items, row_warnings = _normalize_blockpit_row(spec, row, idx)
            warnings.extend(row_warnings)
            normalized_rows.extend(row_items)
            continue
        if connector_id.lower() == "heliumgeek":
            row_items, row_warnings = _normalize_heliumgeek_row(spec, row, idx)
            warnings.extend(row_warnings)
            normalized_rows.extend(row_items)
            continue

        timestamp_raw = _get_value(row, spec.aliases["timestamp"])
        asset_raw = _get_value(row, spec.aliases["asset"])
        quantity_raw = _get_value(row, spec.aliases["quantity"])
        price_raw = _get_value(row, spec.aliases["price"])
        fee_raw = _get_value(row, spec.aliases["fee"])
        fee_asset_raw = _get_value(row, spec.aliases["fee_asset"])
        side_raw = _get_value(row, spec.aliases["side"])
        event_type_raw = _get_value(row, spec.aliases["event_type"])
        tx_id_raw = _get_value(row, spec.aliases["tx_id"])

        if quantity_raw is None and asset_raw is None:
            warnings.append({"row": str(idx), "code": "row_not_mappable"})
            continue

        timestamp_utc: str | None = None
        if timestamp_raw is not None:
            timestamp_utc, dt_error = parse_datetime_value(timestamp_raw)
            if dt_error:
                warnings.append({"row": str(idx), "code": dt_error, "field": "timestamp"})
                timestamp_utc = str(timestamp_raw)

        quantity = ""
        if quantity_raw is not None:
            parsed_qty, qty_error = parse_decimal_value(quantity_raw)
            if qty_error:
                warnings.append({"row": str(idx), "code": qty_error, "field": "quantity"})
                quantity = str(quantity_raw)
            elif parsed_qty is not None:
                quantity = parsed_qty.to_eng_string()

        price = ""
        if price_raw is not None:
            parsed_price, price_error = parse_decimal_value(price_raw)
            if price_error:
                warnings.append({"row": str(idx), "code": price_error, "field": "price"})
                price = str(price_raw)
            elif parsed_price is not None:
                price = parsed_price.to_eng_string()

        fee = ""
        if fee_raw is not None:
            parsed_fee, fee_error = parse_decimal_value(fee_raw)
            if fee_error:
                warnings.append({"row": str(idx), "code": fee_error, "field": "fee"})
                fee = str(fee_raw)
            elif parsed_fee is not None:
                fee = parsed_fee.to_eng_string()

        normalized_rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "asset": str(asset_raw) if asset_raw is not None else "",
                "quantity": quantity,
                "price": price,
                "fee": fee,
                "fee_asset": str(fee_asset_raw) if fee_asset_raw is not None else "",
                "side": str(side_raw).lower() if side_raw is not None else "",
                "event_type": str(event_type_raw).lower() if event_type_raw is not None else "",
                "tx_id": str(tx_id_raw) if tx_id_raw is not None else "",
                "source": connector_id.lower(),
                "raw_row": row,
            }
        )

    return normalized_rows, warnings, errors


def parse_upload_file(filename: str, content: bytes) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    lower_name = filename.lower()
    warnings: list[dict[str, str]] = []

    if lower_name.endswith(".csv") or lower_name.endswith(".txt"):
        text: str
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
            warnings.append({"code": "fallback_latin1_decode"})
        sample = text[:8192]
        delimiter = ","
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        return [dict(row) for row in reader], warnings

    if lower_name.endswith(".json"):
        parsed = json.loads(content.decode("utf-8"))
        if isinstance(parsed, list):
            return [dict(item) for item in parsed if isinstance(item, dict)], warnings
        if isinstance(parsed, dict) and isinstance(parsed.get("rows"), list):
            rows = [dict(item) for item in parsed["rows"] if isinstance(item, dict)]
            return rows, warnings
        raise ValueError("invalid_json_shape")

    if lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
        try:
            import pandas as pd  # type: ignore[import-untyped]
        except Exception as exc:  # pragma: no cover
            raise ValueError("xlsx_support_missing") from exc

        frame = pd.read_excel(io.BytesIO(content), dtype=str, header=None)
        frame = frame.where(frame.notna(), "")
        rows_2d = frame.values.tolist()

        best_header_idx = 0
        best_score = -1
        header_keywords = {
            "time",
            "date",
            "coin",
            "asset",
            "amount",
            "network",
            "txid",
            "transaction id",
            "status",
            "fee",
            "side",
        }
        for idx, row in enumerate(rows_2d[:50]):
            cells = [str(cell).strip() for cell in row]
            non_empty = [cell for cell in cells if cell]
            if not non_empty:
                continue
            score = 0
            for cell in non_empty:
                norm = cell.lower()
                if norm in header_keywords:
                    score += 2
                elif any(key in norm for key in ("time", "date", "coin", "amount", "tx", "network", "status")):
                    score += 1
            if score > best_score:
                best_score = score
                best_header_idx = idx

        header = [str(cell).strip() for cell in rows_2d[best_header_idx]]
        data_rows = rows_2d[best_header_idx + 1 :]
        cleaned_header = []
        for col_idx, name in enumerate(header):
            cleaned_header.append(name if name else f"col_{col_idx}")

        out_rows: list[dict[str, Any]] = []
        for raw_row in data_rows:
            mapped = {cleaned_header[i]: (str(raw_row[i]).strip() if i < len(raw_row) else "") for i in range(len(cleaned_header))}
            if any(str(v).strip() for v in mapped.values()):
                out_rows.append(mapped)
        return out_rows, warnings

    raise ValueError("unsupported_file_type")
