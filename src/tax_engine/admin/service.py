from __future__ import annotations

import json
import logging
import os
from typing import Any

from tax_engine.ingestion.store import STORE
from tax_engine.security import decrypt_secret_value, encrypt_secret_value, has_master_key_material

_SECRET_KEY_PREFIXES = ("secret.", "credential.")
LOGGER = logging.getLogger(__name__)


def put_admin_setting(setting_key: str, value: Any, is_secret: bool) -> None:
    serialized = json.dumps(value, ensure_ascii=False)
    if is_secret:
        serialized = encrypt_secret_value(serialized)
    STORE.upsert_setting(setting_key=setting_key, value_json=serialized, is_secret=is_secret)


def get_admin_settings_view() -> dict[str, Any]:
    rows = STORE.list_settings()
    visible_settings: list[dict[str, Any]] = []
    for row in rows:
        key = str(row["setting_key"])
        is_secret = bool(row["is_secret"])
        if is_secret or key.startswith(_SECRET_KEY_PREFIXES):
            value = "***"
        else:
            try:
                value = json.loads(str(row["value_json"]))
            except json.JSONDecodeError:
                value = str(row["value_json"])
        visible_settings.append(
            {
                "setting_key": key,
                "value": value,
                "is_secret": is_secret,
                "updated_at_utc": str(row["updated_at_utc"]),
            }
        )
    return {
        "master_key_configured": has_master_key_material(),
        "settings": visible_settings,
    }


def resolve_effective_runtime_config() -> dict[str, Any]:
    solana_rpc_url = _load_value("runtime.solana.rpc_url")
    if not isinstance(solana_rpc_url, str) or not solana_rpc_url.strip():
        solana_rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

    solana_fallbacks = _load_value("runtime.solana.rpc_fallback_urls")
    if not isinstance(solana_fallbacks, list):
        raw_fallback = os.getenv("SOLANA_RPC_FALLBACK_URLS", "")
        solana_fallbacks = [item.strip() for item in raw_fallback.split(",") if item.strip()]

    alchemy_key = _load_secret_json_value("secret.alchemy.api_key")
    coingecko_key = _load_secret_json_value("secret.coingecko.api_key")
    binance_key = _load_secret_json_value("secret.cex.binance.api_key")
    bitget_key = _load_secret_json_value("secret.cex.bitget.api_key")
    coinbase_key = _load_secret_json_value("secret.cex.coinbase.api_key")
    default_wallet = _load_value("runtime.solana.default_wallet")
    if not isinstance(default_wallet, str):
        default_wallet = ""
    usd_to_eur = _load_value("runtime.fx.usd_to_eur")
    if isinstance(usd_to_eur, str):
        try:
            usd_to_eur = float(usd_to_eur)
        except ValueError:
            usd_to_eur = None
    if not isinstance(usd_to_eur, (int, float)) or usd_to_eur <= 0:
        try:
            usd_to_eur = float(os.getenv("USD_TO_EUR_RATE", "0"))
        except ValueError:
            usd_to_eur = 0.0
    if usd_to_eur <= 0:
        usd_to_eur = 1.0
    coingecko_plan = _load_value("runtime.coingecko.plan")
    if str(coingecko_plan).lower() not in {"demo", "pro"}:
        coingecko_plan = os.getenv("COINGECKO_PLAN", "demo")
    coingecko_plan = str(coingecko_plan).lower() if str(coingecko_plan).lower() in {"demo", "pro"} else "demo"
    return {
        "master_key_configured": has_master_key_material(),
        "runtime": {
            "solana": {
                "rpc_url": solana_rpc_url,
                "rpc_fallback_urls": solana_fallbacks,
                "default_wallet": default_wallet,
            },
            "fx": {
                "usd_to_eur": usd_to_eur,
            },
            "coingecko": {
                "plan": coingecko_plan,
            },
        },
        "credentials": {
            "alchemy_configured": bool(alchemy_key),
            "alchemy_api_key_masked": _mask_secret(str(alchemy_key or "")),
            "coingecko_configured": bool(coingecko_key),
            "coingecko_api_key_masked": _mask_secret(str(coingecko_key or "")),
            "binance_configured": bool(binance_key),
            "binance_api_key_masked": _mask_secret(str(binance_key or "")),
            "bitget_configured": bool(bitget_key),
            "bitget_api_key_masked": _mask_secret(str(bitget_key or "")),
            "coinbase_configured": bool(coinbase_key),
            "coinbase_api_key_masked": _mask_secret(str(coinbase_key or "")),
        },
    }


def resolve_cex_credentials(connector_id: str) -> dict[str, str]:
    connector = str(connector_id or "").strip().lower()
    if connector not in {"binance", "bitget", "coinbase"}:
        raise ValueError("unsupported_connector")
    api_key = _load_secret_json_value(f"secret.cex.{connector}.api_key")
    api_secret = _load_secret_json_value(f"secret.cex.{connector}.api_secret")
    passphrase = _load_secret_json_value(f"secret.cex.{connector}.passphrase")
    return {
        "connector_id": connector,
        "api_key": str(api_key or ""),
        "api_secret": str(api_secret or ""),
        "passphrase": str(passphrase or ""),
    }


def resolve_secret_value(setting_key: str) -> str:
    if not setting_key.startswith(_SECRET_KEY_PREFIXES):
        raise ValueError("unsupported_secret_key")
    value = _load_secret_json_value(setting_key)
    return str(value or "")


def _load_value(setting_key: str) -> Any:
    row = STORE.get_setting(setting_key)
    if row is None:
        return None
    raw = str(row["value_json"])
    if bool(row["is_secret"]):
        decrypted = _decrypt_setting_value(setting_key, raw)
        if decrypted is None:
            return None
        return json.loads(decrypted)
    return json.loads(raw)


def _load_secret_json_value(setting_key: str) -> Any:
    row = STORE.get_setting(setting_key)
    if row is None or not bool(row["is_secret"]):
        return None
    decrypted = _decrypt_setting_value(setting_key, str(row["value_json"]))
    if decrypted is None:
        return None
    return json.loads(decrypted)


def _decrypt_setting_value(setting_key: str, encrypted_value: str) -> str | None:
    try:
        return decrypt_secret_value(encrypted_value)
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Admin secret setting %s could not be decrypted: %s", setting_key, type(exc).__name__)
        return None


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"
