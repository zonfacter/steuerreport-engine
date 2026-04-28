from __future__ import annotations

from typing import Any

# Kern-Mints für Solana/Helium/Jupiter; erweiterbar über Datei/DB in späteren Etappen.
_KNOWN_TOKENS: dict[str, dict[str, str]] = {
    "SOL": {"symbol": "SOL", "name": "Solana"},
    "USDC": {"symbol": "USDC", "name": "USD Coin"},
    "USDT": {"symbol": "USDT", "name": "Tether USD"},
    "JUP": {"symbol": "JUP", "name": "Jupiter"},
    "HNT": {"symbol": "HNT", "name": "Helium"},
    "IOT": {"symbol": "IOT", "name": "Helium IOT"},
    "MOBILE": {"symbol": "MOBILE", "name": "Helium MOBILE"},
    "ZEUS": {"symbol": "ZEUS", "name": "Zeus Network"},
    "SO11111111111111111111111111111111111111112": {"symbol": "SOL", "name": "Wrapped SOL"},
    "EPJFWDD5AUFQSSQEM2QN1XZYBAPC8G4WEGGKZWYTDT1V": {"symbol": "USDC", "name": "USD Coin"},
    "ES9VMFRZACERMJFRF4H2FYD4KCONKY11MCCE8BENWNYB": {"symbol": "USDT", "name": "Tether USD"},
    "JUPYIWRYJFSKUPIHA7HKER8VUTAEFOSYBKEDZNSDVCN": {"symbol": "JUP", "name": "Jupiter"},
    "HNTYVP6YFM1HG25TN9WGLQM12B8TQMCKNKRDU1OXWUX": {"symbol": "HNT", "name": "Helium"},
    "IOTEVVZLEYWOTN1QDWNPDDXPWSZN3ZFHEOT3MFL9FNS": {"symbol": "IOT", "name": "Helium IOT"},
    "MOBILEX6QQ9X4RLAQHQA2GEEA9FSQAP8FKM95J4O5F1N": {"symbol": "MOBILE", "name": "Helium MOBILE"},
    "ZEUS1AR7AX8DFFJF5QJWJ2FTDDDNTROMNGO8YOQM3GQ": {"symbol": "ZEUS", "name": "Zeus Network"},
}


def resolve_token_metadata(asset: str) -> dict[str, Any]:
    value = str(asset or "").strip()
    key = value.upper()
    known = _KNOWN_TOKENS.get(key)
    if known is None:
        return {
            "asset": value,
            "symbol": value if len(value) <= 12 else f"{value[:6]}...{value[-4:]}",
            "name": "Unbekanntes Token",
            "is_known": False,
        }
    return {
        "asset": value,
        "symbol": known["symbol"],
        "name": known["name"],
        "is_known": True,
    }
