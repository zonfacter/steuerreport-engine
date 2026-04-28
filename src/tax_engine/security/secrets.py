from __future__ import annotations

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_KEY_FILE = Path("/tmp/steuerreport/master.key")
_KEY_ENV = "STEUERREPORT_MASTER_KEY_B64"


def has_master_key_material() -> bool:
    env_value = os.getenv(_KEY_ENV, "").strip()
    return bool(env_value) or _KEY_FILE.exists()


def encrypt_secret_value(plain_text: str) -> str:
    key = _load_or_create_master_key()
    aes = AESGCM(key)
    nonce = os.urandom(12)
    cipher = aes.encrypt(nonce, plain_text.encode("utf-8"), associated_data=None)
    payload = nonce + cipher
    return "v1:" + base64.urlsafe_b64encode(payload).decode("ascii")


def decrypt_secret_value(encrypted_value: str) -> str:
    if not encrypted_value.startswith("v1:"):
        raise ValueError("unsupported_secret_format")
    raw = base64.urlsafe_b64decode(encrypted_value[3:].encode("ascii"))
    if len(raw) < 13:
        raise ValueError("invalid_secret_payload")
    nonce = raw[:12]
    cipher = raw[12:]
    key = _load_or_create_master_key()
    aes = AESGCM(key)
    plain = aes.decrypt(nonce, cipher, associated_data=None)
    return plain.decode("utf-8")


def _load_or_create_master_key() -> bytes:
    env_value = os.getenv(_KEY_ENV, "").strip()
    if env_value:
        return _decode_key(env_value)

    if _KEY_FILE.exists():
        return _decode_key(_KEY_FILE.read_text(encoding="utf-8").strip())

    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    key = AESGCM.generate_key(256)
    encoded = base64.urlsafe_b64encode(key).decode("ascii")
    _KEY_FILE.write_text(encoded, encoding="utf-8")
    os.chmod(_KEY_FILE, 0o600)
    return key


def _decode_key(encoded: str) -> bytes:
    key = base64.urlsafe_b64decode(encoded.encode("ascii"))
    if len(key) != 32:
        raise ValueError("invalid_master_key_length")
    return key
