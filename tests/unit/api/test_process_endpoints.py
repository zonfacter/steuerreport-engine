from __future__ import annotations

from tax_engine.api.app import (
    import_confirm,
    process_derivative_lines,
    process_run,
    process_status,
    process_tax_lines,
    process_worker_run_next,
)
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE
from tax_engine.queue.models import ProcessRunRequest, WorkerRunNextRequest


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_process_run_creates_queued_job() -> None:
    _reset_store()
    response = process_run(
        ProcessRunRequest(
            tax_year=2026,
            ruleset_id="DE-2026-v1.0",
            config={"calculation_mode": "depot_separated"},
            dry_run=True,
        )
    )

    assert response.status == "success"
    assert response.data["status"] == "queued"
    assert response.data["progress"] == 0
    assert response.data["tax_year"] == 2026
    assert response.data["ruleset_id"] == "DE-2026-v1.0"


def test_process_status_returns_created_job() -> None:
    _reset_store()
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]

    status = process_status(job_id)

    assert status.status == "success"
    assert status.data["job_id"] == job_id
    assert status.data["status"] == "queued"


def test_process_status_returns_error_for_unknown_job() -> None:
    _reset_store()

    status = process_status("does-not-exist")

    assert status.status == "error"
    assert status.errors[0]["code"] == "job_not_found"


def test_worker_run_next_completes_queued_job() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="test.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                    "fee_eur": "1",
                },
                {
                    "timestamp": "2026-02-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "sell",
                    "amount": "0.4",
                    "price_eur": "120",
                    "fee_eur": "0.4",
                },
                {
                    "timestamp": "2026-03-01T12:00:00Z",
                    "position_id": "d1",
                    "asset": "ETH",
                    "event_type": "derivative_open",
                    "collateral_eur": "300",
                    "fee_eur": "2",
                },
                {
                    "timestamp": "2026-03-03T12:00:00Z",
                    "position_id": "d1",
                    "asset": "ETH",
                    "event_type": "close",
                    "proceeds_eur": "250",
                    "fee_eur": "1",
                },
            ],
        )
    )
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]

    result = process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    status = process_status(job_id)
    tax_lines_response = process_tax_lines(job_id)
    derivative_lines_response = process_derivative_lines(job_id)

    assert result.status == "success"
    assert result.data["job_id"] == job_id
    assert result.data["status"] == "completed"
    assert result.data["progress"] == 100
    assert result.data["result_summary"] is not None
    assert result.data["result_summary"]["processed_events"] == 2
    assert result.data["result_summary"]["derivatives"]["processed_events"] == 2
    assert result.data["tax_line_count"] == 1
    assert result.data["derivative_line_count"] == 1
    tax_lines = STORE.get_tax_lines(job_id)
    derivative_lines = STORE.get_derivative_lines(job_id)
    assert len(tax_lines) == 1
    assert len(derivative_lines) == 1
    assert tax_lines[0]["asset"] == "BTC"
    assert derivative_lines[0]["asset"] == "ETH"
    assert tax_lines_response.status == "success"
    assert derivative_lines_response.status == "success"
    assert tax_lines_response.data["count"] == 1
    assert derivative_lines_response.data["count"] == 1
    assert status.data["status"] == "completed"


def test_worker_run_next_can_fail_job() -> None:
    _reset_store()
    process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))

    result = process_worker_run_next(WorkerRunNextRequest(simulate_fail=True))

    assert result.status == "success"
    assert result.data["status"] == "failed"
    assert result.data["error_message"] == "Simulated worker error"


def test_worker_run_next_returns_warning_when_queue_empty() -> None:
    _reset_store()

    result = process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))

    assert result.status == "success"
    assert result.warnings[0]["code"] == "no_queued_job"
