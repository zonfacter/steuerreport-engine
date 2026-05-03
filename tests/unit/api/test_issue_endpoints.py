from __future__ import annotations

from tax_engine.api.app import (
    IssueStatusUpdateRequest,
    ReviewMergeRequest,
    ReviewSplitRequest,
    ReviewTimezoneCorrectRequest,
    import_confirm,
    issues_inbox,
    issues_update_status,
    process_run,
    process_worker_run_next,
    review_actions,
    review_gates,
    review_integration_conflicts,
    review_merge,
    review_split,
    review_timezone_correct,
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


def test_review_timezone_correction_closes_timezone_issue_and_is_applied() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="timezone.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "amount": "0.1",
                    "price_eur": "100",
                }
            ],
        )
    )
    inbox = issues_inbox()
    issue = next(item for item in inbox.data.get("issues", []) if item.get("type") == "timezone_conflict")
    event_id = str(issue["source_event_id"])

    corrected = review_timezone_correct(
        ReviewTimezoneCorrectRequest(
            source_event_id=event_id,
            corrected_timestamp_utc="2026-01-01T11:00:00Z",
            reason_code="source_timezone_cet",
            note="Importquelle war CET, nicht UTC.",
        )
    )
    assert corrected.status == "success"

    inbox_after = issues_inbox()
    assert not any(
        str(item.get("type")) == "timezone_conflict" and str(item.get("source_event_id")) == event_id
        for item in inbox_after.data.get("issues", [])
    )

    from tax_engine.queue import apply_review_actions

    adjusted, summary = apply_review_actions(STORE.list_raw_events())
    assert summary["timezone_correction_count"] == 1
    assert adjusted[0]["payload"]["timestamp_utc"] == "2026-01-01T11:00:00+00:00"
    assert adjusted[0]["payload"]["review_action"] == "timezone_correct"


def test_review_merge_and_split_actions_are_persisted_without_raw_delete() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="merge_split.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T12:00:00Z",
                    "asset": "SOL",
                    "event_type": "swap_out_aggregated",
                    "side": "sell",
                    "amount": "1",
                    "price_eur": "10",
                },
                {
                    "timestamp_utc": "2026-01-01T12:00:01Z",
                    "asset": "USDC",
                    "event_type": "swap_in_aggregated",
                    "side": "buy",
                    "amount": "10",
                    "price_eur": "1",
                },
            ],
        )
    )
    event_ids = [str(item["unique_event_id"]) for item in STORE.list_raw_events()]

    merge = review_merge(
        ReviewMergeRequest(
            source_event_ids=event_ids,
            reason_code="same_economic_event",
            note="Jupiter Multi-Hop als ein wirtschaftlicher Swap.",
        )
    )
    assert merge.status == "success"

    split = review_split(
        ReviewSplitRequest(
            source_event_id=event_ids[0],
            split_rows=[{"asset": "SOL", "quantity": "0.5"}, {"asset": "SOL", "quantity": "0.5"}],
            reason_code="bundled_event_split",
            note="Teilvorgaenge fuer Review dokumentiert.",
        )
    )
    assert split.status == "success"
    assert len(STORE.list_raw_events()) == 2

    actions = review_actions()
    action_types = {str(item.get("action_type")) for item in actions.data.get("rows", [])}
    assert {"merge", "split"}.issubset(action_types)
