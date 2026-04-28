from __future__ import annotations

from tax_engine.connectors.models import SolanaWalletPreviewRequest


def test_solana_model_reads_rpc_defaults_from_env(monkeypatch) -> None:
    monkeypatch.setenv("SOLANA_RPC_URL", "https://rpc.primary.test")
    monkeypatch.setenv("SOLANA_RPC_FALLBACK_URLS", "https://rpc.f1.test, https://rpc.f2.test")

    payload = SolanaWalletPreviewRequest(wallet_address="A" * 32)
    assert payload.rpc_url == "https://rpc.primary.test"
    assert payload.rpc_fallback_urls == ["https://rpc.f1.test", "https://rpc.f2.test"]
