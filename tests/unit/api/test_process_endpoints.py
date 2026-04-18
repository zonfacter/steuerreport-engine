from __future__ import annotations

from tax_engine.api.app import process_run, process_status, process_worker_run_next
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
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]

    result = process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    status = process_status(job_id)

    assert result.status == "success"
    assert result.data["job_id"] == job_id
    assert result.data["status"] == "completed"
    assert result.data["progress"] == 100
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
