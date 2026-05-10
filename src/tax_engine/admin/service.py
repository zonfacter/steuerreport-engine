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
    pionex_key = _load_secret_json_value("secret.cex.pionex.api_key")
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
    ai_review_provider = _load_value("runtime.ai_review.provider")
    if not isinstance(ai_review_provider, str) or not ai_review_provider.strip():
        ai_review_provider = os.getenv("AI_REVIEW_PROVIDER", "deterministic")
    ai_review_provider = str(ai_review_provider).strip().lower()
    ollama_base_url = _load_value("runtime.ai_review.ollama_base_url")
    if not isinstance(ollama_base_url, str) or not ollama_base_url.strip():
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model = _load_value("runtime.ai_review.ollama_model")
    if not isinstance(ollama_model, str) or not ollama_model.strip():
        ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
    ollama_timeout = _load_value("runtime.ai_review.ollama_timeout_seconds")
    if isinstance(ollama_timeout, str):
        try:
            ollama_timeout = float(ollama_timeout)
        except ValueError:
            ollama_timeout = None
    if not isinstance(ollama_timeout, (int, float)) or ollama_timeout <= 0:
        ollama_timeout = 120.0
    ollama_temperature = _load_value("runtime.ai_review.ollama_temperature")
    if isinstance(ollama_temperature, str):
        try:
            ollama_temperature = float(ollama_temperature)
        except ValueError:
            ollama_temperature = None
    if not isinstance(ollama_temperature, (int, float)) or ollama_temperature < 0:
        ollama_temperature = 0.1
    ollama_num_ctx = _load_value("runtime.ai_review.ollama_num_ctx")
    if isinstance(ollama_num_ctx, str):
        try:
            ollama_num_ctx = int(ollama_num_ctx)
        except ValueError:
            ollama_num_ctx = None
    if not isinstance(ollama_num_ctx, int) or ollama_num_ctx <= 0:
        try:
            ollama_num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        except ValueError:
            ollama_num_ctx = 4096
    ollama_num_ctx = min(max(int(ollama_num_ctx), 2048), 32768)
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
            "ai_review": {
                "provider": ai_review_provider,
                "ollama_base_url": str(ollama_base_url),
                "ollama_model": str(ollama_model),
                "ollama_timeout_seconds": float(ollama_timeout),
                "ollama_temperature": float(ollama_temperature),
                "ollama_num_ctx": int(ollama_num_ctx),
                "llama_cpp_base_url": _runtime_str(
                    "runtime.ai_review.llama_cpp_base_url",
                    "LLAMA_CPP_BASE_URL",
                    "http://127.0.0.1:11435",
                ),
                "llama_cpp_model": _runtime_str(
                    "runtime.ai_review.llama_cpp_model",
                    "LLAMA_CPP_MODEL",
                    "qwen3-coder-30b-a3b-llamacpp",
                ),
                "llama_cpp_timeout_seconds": float(
                    _runtime_float("runtime.ai_review.llama_cpp_timeout_seconds", "LLAMA_CPP_TIMEOUT_SECONDS", 180.0)
                ),
                "llama_cpp_temperature": float(
                    _runtime_float("runtime.ai_review.llama_cpp_temperature", "LLAMA_CPP_TEMPERATURE", 0.1)
                ),
                "llama_cpp_max_tokens": int(
                    min(
                        max(
                            _runtime_int("runtime.ai_review.llama_cpp_max_tokens", "LLAMA_CPP_MAX_TOKENS", 384),
                            128,
                        ),
                        2048,
                    )
                ),
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
            "pionex_configured": bool(pionex_key),
            "pionex_api_key_masked": _mask_secret(str(pionex_key or "")),
        },
    }


def resolve_cex_credentials(connector_id: str) -> dict[str, str]:
    connector = str(connector_id or "").strip().lower()
    if connector not in {"binance", "bitget", "coinbase", "pionex"}:
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


def _runtime_str(setting_key: str, env_key: str, default: str) -> str:
    value = _load_value(setting_key)
    if not isinstance(value, str) or not value.strip():
        value = os.getenv(env_key, default)
    return str(value)


def _runtime_float(setting_key: str, env_key: str, default: float) -> float:
    value = _load_value(setting_key)
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            value = None
    if not isinstance(value, (int, float)) or value <= 0:
        try:
            value = float(os.getenv(env_key, str(default)))
        except ValueError:
            value = default
    return float(value)


def _runtime_int(setting_key: str, env_key: str, default: int) -> int:
    value = _load_value(setting_key)
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            value = None
    if not isinstance(value, int) or value <= 0:
        try:
            value = int(os.getenv(env_key, str(default)))
        except ValueError:
            value = default
    return int(value)


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
