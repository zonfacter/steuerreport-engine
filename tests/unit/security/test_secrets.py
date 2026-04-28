from __future__ import annotations

from tax_engine.security import decrypt_secret_value, encrypt_secret_value


def test_secret_encrypt_decrypt_roundtrip() -> None:
    plain = "super-secret-value"
    encrypted = encrypt_secret_value(plain)
    assert encrypted.startswith("v1:")
    decrypted = decrypt_secret_value(encrypted)
    assert decrypted == plain
