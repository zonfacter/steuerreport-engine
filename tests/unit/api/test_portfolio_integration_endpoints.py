from __future__ import annotations

from tax_engine.api.app import (
    IntegrationModeUpdateRequest,
    import_confirm,
    portfolio_integration_mode_update,
    portfolio_integrations,
)
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_portfolio_integrations_groups_by_source() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="src_a.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T00:00:00Z",
                    "source": "binance_api",
                    "event_type": "deposit",
                    "asset": "USDT",
                    "quantity": "100",
                    "side": "in",
                },
                {
                    "timestamp_utc": "2026-01-02T00:00:00Z",
                    "source": "binance_api",
                    "event_type": "trade",
                    "asset": "BTC",
                    "quantity": "0.01",
                    "side": "in",
                },
            ],
        )
    )
    import_confirm(
        ConfirmImportRequest(
            source_name="src_b.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-03T00:00:00Z",
                    "source": "solana_rpc",
                    "event_type": "sol_transfer",
                    "asset": "SOL",
                    "quantity": "1.5",
                    "side": "in",
                }
            ],
        )
    )

    response = portfolio_integrations()
    assert response.status == "success"
    assert response.data["count"] >= 2
    rows = response.data["rows"]
    ids = {row["integration_id"] for row in rows}
    assert "binance_api" in ids
    assert "solana_rpc" in ids
    binance = next(row for row in rows if row["integration_id"] == "binance_api")
    assert int(binance["event_count"]) == 2
    assert int(binance["asset_count"]) >= 2
    assert binance["mode"] == "active"


def test_portfolio_integration_mode_can_mark_reference_source() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="blockpit.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T00:00:00Z",
                    "source": "blockpit",
                    "event_type": "trade",
                    "asset": "BTC",
                    "quantity": "1",
                    "side": "in",
                }
            ],
        )
    )

    response = portfolio_integrations()
    blockpit = next(row for row in response.data["rows"] if row["integration_id"] == "blockpit")
    assert blockpit["mode"] == "reference"

    update = portfolio_integration_mode_update(
        IntegrationModeUpdateRequest(integration_id="blockpit", mode="active", note="Primaerdaten fuer Test")
    )
    assert update.status == "success"

    response2 = portfolio_integrations()
    blockpit2 = next(row for row in response2.data["rows"] if row["integration_id"] == "blockpit")
    assert blockpit2["mode"] == "active"
    assert blockpit2["mode_overridden"] is True
