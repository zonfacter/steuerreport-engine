from __future__ import annotations

from pydantic import BaseModel, Field


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
    rpc_url: str = Field(default="https://api.mainnet-beta.solana.com")
    timeout_seconds: int = Field(default=20, ge=3, le=120)
    max_signatures: int = Field(default=100, ge=1, le=1000)
    max_transactions: int = Field(default=50, ge=1, le=500)


class SolanaImportConfirmRequest(BaseModel):
    wallet_address: str = Field(min_length=32)
    rpc_url: str = Field(default="https://api.mainnet-beta.solana.com")
    timeout_seconds: int = Field(default=20, ge=3, le=120)
    max_signatures: int = Field(default=100, ge=1, le=1000)
    max_transactions: int = Field(default=50, ge=1, le=500)
    source_name: str | None = Field(default=None)
