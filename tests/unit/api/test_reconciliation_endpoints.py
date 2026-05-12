from __future__ import annotations

from tax_engine.api.app import (
    audit_transfer_chain,
    import_confirm,
    reconcile_auto_match,
    reconcile_ledger,
    reconcile_manual,
    review_unmatched,
)
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE
from tax_engine.reconciliation.models import AutoMatchRequest, ManualMatchRequest


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_reconcile_auto_match_and_review_unmatched() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="x.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "SOL",
                    "event_type": "withdrawal",
                    "amount": "10.00",
                },
                {
                    "timestamp": "2026-01-01T12:03:00Z",
                    "asset": "SOL",
                    "event_type": "deposit",
                    "amount": "9.99",
                },
                {
                    "timestamp": "2026-01-01T12:10:00Z",
                    "asset": "BTC",
                    "event_type": "withdrawal",
                    "amount": "1.0",
                },
            ],
        )
    )

    matched = reconcile_auto_match(AutoMatchRequest())
    unmatched = review_unmatched()

    assert matched.status == "success"
    assert matched.data["persisted_match_count"] == 1
    assert unmatched.status == "success"
    assert unmatched.data["unmatched_outbound_ids"] != []


def test_reconcile_manual_creates_match() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="y.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "ETH",
                    "event_type": "withdrawal",
                    "amount": "2.0",
                },
                {
                    "timestamp": "2026-01-01T13:00:00Z",
                    "asset": "ETH",
                    "event_type": "deposit",
                    "amount": "1.99",
                },
            ],
        )
    )
    raw_events = STORE.list_raw_events()
    outbound_id = raw_events[0]["unique_event_id"]
    inbound_id = raw_events[1]["unique_event_id"]

    result = reconcile_manual(
        ManualMatchRequest(
            outbound_event_id=outbound_id,
            inbound_event_id=inbound_id,
            note="manual link",
        )
    )

    assert result.status == "success"
    assert result.data["ok"] is True


def test_reconcile_ledger_contains_from_to_trace() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="trace.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "SOL",
                    "event_type": "withdrawal",
                    "amount": "10.0",
                    "wallet_address": "binance-wallet",
                },
                {
                    "timestamp": "2026-01-01T12:02:00Z",
                    "asset": "SOL",
                    "event_type": "deposit",
                    "amount": "9.99",
                    "wallet_address": "phantom-wallet",
                },
            ],
        )
    )
    reconcile_auto_match(AutoMatchRequest())
    ledger = reconcile_ledger(limit=50, offset=0)

    assert ledger.status == "success"
    rows = ledger.data.get("rows", [])
    assert len(rows) == 1
    row = rows[0]
    assert row.get("status") == "matched"
    assert row.get("from_wallet") == "binance-wallet"
    assert row.get("to_wallet") == "phantom-wallet"
    chain_id = str(row.get("transfer_chain_id", ""))
    assert chain_id.startswith("transfer-chain:")

    chain = audit_transfer_chain(chain_id)

    assert chain.status == "success"
    assert chain.data["transfer_chain_id"] == chain_id
    assert chain.data["row_count"] == 1
    assert chain.data["assets"] == ["SOL"]
    assert chain.data["wallet_path"] == ["trace.csv:binance-wallet", "trace.csv:phantom-wallet"]
    assert chain.data["holding_period_continues"] is True
    assert chain.data["rows"][0]["from_wallet"] == "binance-wallet"


def test_audit_transfer_chain_returns_error_for_unknown_chain() -> None:
    _reset_store()

    result = audit_transfer_chain("transfer-chain:missing")

    assert result.status == "error"
    assert result.errors[0]["code"] == "transfer_chain_not_found"
