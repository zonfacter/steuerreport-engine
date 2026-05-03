from __future__ import annotations

from tax_engine.api.app import (
    IssueStatusUpdateRequest,
    import_confirm,
    issues_inbox,
    issues_update_status,
    process_run,
    process_worker_run_next,
    review_gates,
    review_integration_conflicts,
)
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE
from tax_engine.queue.models import ProcessRunRequest, WorkerRunNextRequest


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_issues_inbox_contains_unmatched_transfer_issue() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="issues.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "SOL",
                    "event_type": "withdrawal",
                    "amount": "1.0",
                }
            ],
        )
    )
    resp = issues_inbox()
    assert resp.status == "success"
    issues = resp.data.get("issues", [])
    assert any(str(item.get("type")) == "unmatched_transfer" for item in issues)


def test_issue_status_update_persists() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="issues2.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "amount": "0.1",
                    "price_eur": "0",
                }
            ],
        )
    )
    inbox = issues_inbox()
    assert inbox.status == "success"
    issue_id = str(inbox.data.get("issues", [])[0].get("issue_id"))
    upd = issues_update_status(
        IssueStatusUpdateRequest(issue_id=issue_id, status="in_review", note="Manuell geprüft")
    )
    assert upd.status == "success"

    inbox2 = issues_inbox()
    assert inbox2.status == "success"
    issue = next(item for item in inbox2.data.get("issues", []) if str(item.get("issue_id")) == issue_id)
    assert issue.get("status") == "in_review"


def test_review_gates_blocks_when_unmatched_and_open_issues_exist() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="gates.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "amount": "0.1",
                    "price_eur": "0",
                },
                {
                    "timestamp": "2026-01-01T12:05:00Z",
                    "asset": "SOL",
                    "event_type": "withdrawal",
                    "amount": "2.0",
                },
            ],
        )
    )
    resp = review_gates()
    assert resp.status == "success"
    assert resp.data.get("allow_export") is False
    assert (resp.data.get("counts") or {}).get("unmatched_total", 0) >= 1
    blocking_codes = {str(item.get("code")) for item in (resp.data.get("blocking_reasons") or [])}
    assert "unmatched_transfers_open" in blocking_codes


def test_issues_inbox_contains_missing_fx_rate_issue(monkeypatch) -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="fx_missing.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "amount": "0.1",
                    "price": "100",
                    "quote_asset": "USDT",
                }
            ],
        )
    )

    from tax_engine.queue import service as queue_service

    monkeypatch.setattr(
        queue_service.FallbackFxResolver,
        "get_usd_to_eur_rate",
        lambda self, rate_date: None,
    )

    process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    resp = issues_inbox()
    assert resp.status == "success"
    issues = resp.data.get("issues", [])
    assert any(str(item.get("type")) == "missing_fx_rate" for item in issues)


def test_integration_conflicts_compare_reference_and_primary_sources() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="primary.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T12:00:00Z",
                    "source": "binance",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "0.5",
                    "price_eur": "100",
                }
            ],
        )
    )
    import_confirm(
        ConfirmImportRequest(
            source_name="blockpit_reference.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T14:00:00Z",
                    "source": "blockpit",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "0.500000000",
                    "price_eur": "100",
                }
            ],
        )
    )

    conflicts = review_integration_conflicts()
    assert conflicts.status == "success"
    assert conflicts.data["count"] == 1
    row = conflicts.data["conflicts"][0]
    assert row["asset"] == "BTC"
    assert row["primary_sources"] == ["binance"]
    assert row["reference_sources"] == ["blockpit"]

    inbox = issues_inbox()
    assert any(str(item.get("type")) == "integration_conflict" for item in inbox.data.get("issues", []))
