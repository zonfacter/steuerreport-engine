from __future__ import annotations

import os

from pydantic import BaseModel, Field


def _default_solana_rpc_url() -> str:
    value = os.getenv("SOLANA_RPC_URL", "").strip()
    return value or "https://api.mainnet.solana.com"


def _default_solana_rpc_fallback_urls() -> list[str]:
    raw = os.getenv("SOLANA_RPC_FALLBACK_URLS", "").strip()
    if not raw:
        return []
    values = [item.strip() for item in raw.split(",")]
    return [item for item in values if item]


class CexVerifyRequest(BaseModel):
    connector_id: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    api_secret: str = Field(min_length=1)
    passphrase: str | None = Field(default=None)
    timeout_seconds: int = Field(default=15, ge=3, le=60)


class CexBalancesPreviewRequest(BaseModel):
    connector_id: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    api_secret: str = Field(min_length=1)
    passphrase: str | None = Field(default=None)
    timeout_seconds: int = Field(default=20, ge=3, le=90)
    max_rows: int = Field(default=500, ge=1, le=5000)


class CexTransactionsPreviewRequest(BaseModel):
    connector_id: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    api_secret: str = Field(min_length=1)
    passphrase: str | None = Field(default=None)
    timeout_seconds: int = Field(default=20, ge=3, le=90)
    max_rows: int = Field(default=500, ge=1, le=5000)
    start_time_ms: int | None = Field(default=None, ge=0)
    end_time_ms: int | None = Field(default=None, ge=0)


class CexImportConfirmRequest(BaseModel):
    connector_id: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    api_secret: str = Field(min_length=1)
    passphrase: str | None = Field(default=None)
    timeout_seconds: int = Field(default=20, ge=3, le=90)
    max_rows: int = Field(default=500, ge=1, le=5000)
    start_time_ms: int | None = Field(default=None, ge=0)
    end_time_ms: int | None = Field(default=None, ge=0)
    source_name: str | None = Field(default=None)


class SolanaWalletPreviewRequest(BaseModel):
    wallet_address: str = Field(min_length=32)
    rpc_url: str = Field(default_factory=_default_solana_rpc_url)
    rpc_fallback_urls: list[str] = Field(default_factory=_default_solana_rpc_fallback_urls)
    before_signature: str | None = Field(default=None)
    timeout_seconds: int = Field(default=20, ge=3, le=120)
    max_signatures: int = Field(default=1000, ge=1, le=50000)
    max_transactions: int = Field(default=1000, ge=1, le=50000)
    aggregate_jupiter: bool = Field(default=True)
    jupiter_window_seconds: int = Field(default=2, ge=1, le=30)


class SolanaImportConfirmRequest(BaseModel):
    wallet_address: str = Field(min_length=32)
    rpc_url: str = Field(default_factory=_default_solana_rpc_url)
    rpc_fallback_urls: list[str] = Field(default_factory=_default_solana_rpc_fallback_urls)
    before_signature: str | None = Field(default=None)
    timeout_seconds: int = Field(default=20, ge=3, le=120)
    max_signatures: int = Field(default=1000, ge=1, le=50000)
    max_transactions: int = Field(default=1000, ge=1, le=50000)
    aggregate_jupiter: bool = Field(default=True)
    jupiter_window_seconds: int = Field(default=2, ge=1, le=30)
    source_name: str | None = Field(default=None)


class SolanaFullHistoryImportRequest(BaseModel):
    wallet_address: str = Field(min_length=32)
    rpc_url: str = Field(default_factory=_default_solana_rpc_url)
    rpc_fallback_urls: list[str] = Field(default_factory=_default_solana_rpc_fallback_urls)
    timeout_seconds: int = Field(default=20, ge=3, le=120)
    before_signature: str | None = Field(default=None, min_length=32)
    start_time_ms: int | None = Field(default=None, ge=0)
    end_time_ms: int | None = Field(default=None, ge=0)
    max_signatures_per_call: int = Field(default=1000, ge=1, le=50000)
    max_signatures_total: int = Field(default=50000, ge=1, le=500000)
    aggregate_jupiter: bool = Field(default=True)
    jupiter_window_seconds: int = Field(default=2, ge=1, le=30)
    source_name: str | None = Field(default=None)


class SolanaRpcProbeRequest(BaseModel):
    rpc_url: str = Field(default_factory=_default_solana_rpc_url)
    rpc_fallback_urls: list[str] = Field(default_factory=_default_solana_rpc_fallback_urls)
    timeout_seconds: int = Field(default=10, ge=2, le=60)


class SolanaBalanceSnapshotRequest(BaseModel):
    wallet_address: str = Field(min_length=32)
    rpc_url: str = Field(default_factory=_default_solana_rpc_url)
    rpc_fallback_urls: list[str] = Field(default_factory=_default_solana_rpc_fallback_urls)
    timeout_seconds: int = Field(default=15, ge=2, le=60)
    max_tokens: int = Field(default=500, ge=1, le=5000)
    include_prices: bool = Field(default=True)


class DashboardRoleOverrideRequest(BaseModel):
    mode: str = Field(pattern="^(private|business|auto)$")


class WalletGroupUpsertRequest(BaseModel):
    group_id: str | None = Field(default=None)
    name: str = Field(min_length=2, max_length=120)
    wallet_addresses: list[str] = Field(min_length=1, max_length=200)
    source_filters: list[str] = Field(default_factory=list, max_length=200)
    description: str | None = Field(default=None, max_length=400)


class WalletGroupDeleteRequest(BaseModel):
    group_id: str = Field(min_length=8, max_length=120)


class SolanaGroupBalanceSnapshotRequest(BaseModel):
    group_id: str | None = Field(default=None)
    wallet_addresses: list[str] = Field(default_factory=list)
    rpc_url: str = Field(default_factory=_default_solana_rpc_url)
    rpc_fallback_urls: list[str] = Field(default_factory=_default_solana_rpc_fallback_urls)
    timeout_seconds: int = Field(default=20, ge=2, le=120)
    max_tokens: int = Field(default=500, ge=1, le=5000)
    include_prices: bool = Field(default=True)


class SolanaGroupImportConfirmRequest(BaseModel):
    group_id: str | None = Field(default=None)
    wallet_addresses: list[str] = Field(default_factory=list)
    rpc_url: str = Field(default_factory=_default_solana_rpc_url)
    rpc_fallback_urls: list[str] = Field(default_factory=_default_solana_rpc_fallback_urls)
    timeout_seconds: int = Field(default=20, ge=3, le=120)
    max_signatures: int = Field(default=1000, ge=1, le=50000)
    max_transactions: int = Field(default=1000, ge=1, le=50000)
    aggregate_jupiter: bool = Field(default=True)
    jupiter_window_seconds: int = Field(default=2, ge=1, le=30)
    source_name: str | None = Field(default=None)
