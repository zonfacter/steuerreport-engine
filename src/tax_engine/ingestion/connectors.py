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
            "timestamp": ("timestamp", "time", "date", "utc_time", "date(utc)"),
            "asset": ("asset", "coin", "baseasset", "currency", "symbol"),
            "quantity": ("amount", "qty", "quantity", "executed", "filled"),
            "price": ("price", "avgprice", "average"),
            "fee": ("fee", "trading fee", "commission"),
            "fee_asset": ("fee coin", "fee asset", "commissionasset"),
            "side": ("side", "type", "order side"),
            "event_type": ("operation", "transaction type", "type"),
            "tx_id": ("transaction id", "order id", "orderid", "txid"),
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
            "timestamp": ("timestamp", "date", "time"),
            "asset": ("buy cur", "sell cur", "asset", "currency"),
            "quantity": ("buy amount", "sell amount", "amount", "quantity"),
            "price": ("rate", "price"),
            "fee": ("fee amount", "fee", "fee value"),
            "fee_asset": ("fee currency", "fee asset"),
            "side": ("type", "direction"),
            "event_type": ("type", "transaction type"),
            "tx_id": ("txid", "transaction id", "id"),
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
        reader = csv.DictReader(io.StringIO(text))
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

        frame = pd.read_excel(io.BytesIO(content), dtype=str)
        frame = frame.where(frame.notna(), "")
        return frame.to_dict(orient="records"), warnings

    raise ValueError("unsupported_file_type")
