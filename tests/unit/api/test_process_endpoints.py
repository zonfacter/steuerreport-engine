from __future__ import annotations

import asyncio

from tax_engine.api.app import (
    ProcessCompareRulesetsRequest,
    ProcessPreflightRequest,
    TaxEventOverrideUpsertRequest,
    audit_tax_line,
    import_confirm,
    portfolio_lot_aging,
    process_compare_rulesets_post,
    process_derivative_lines,
    process_options,
    process_preflight,
    process_run,
    process_status,
    process_tax_domain_summary,
    process_tax_lines,
    process_worker_run_next,
    report_export,
    report_files,
    tax_event_override_upsert,
)
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE
from tax_engine.queue.models import ProcessRunRequest, WorkerRunNextRequest


def _reset_store() -> None:
    STORE.reset_for_tests()


async def _read_streaming_body(response: object) -> bytes:
    chunks: list[bytes] = []
    async for chunk in response.body_iterator:  # type: ignore[attr-defined]
        chunks.append(chunk if isinstance(chunk, bytes) else str(chunk).encode("utf-8"))
    return b"".join(chunks)


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


def test_process_run_normalizes_de_alias_and_version_from_ui() -> None:
    _reset_store()
    response = process_run(
        ProcessRunRequest(
            tax_year=2026,
            ruleset_id="DE",
            ruleset_version="2026-v1",
            config={},
            dry_run=True,
        )
    )

    assert response.status == "success"
    assert response.data["ruleset_id"] == "DE-2026-v1.0"
    assert response.data["ruleset_version"] == "1.0"
    assert any(item["code"] == "ruleset_resolved" for item in response.warnings)


def test_process_options_returns_wizard_choices() -> None:
    _reset_store()

    response = process_options()

    assert response.status == "success"
    assert 2026 in response.data["tax_years"]
    assert any(item["id"] == "fifo" for item in response.data["tax_methods"])
    assert any(item["id"] == "global" for item in response.data["depot_modes"])
    assert any(item["ruleset_id"] == "DE-2026-v1.0" for item in response.data["rulesets"])


def test_process_preflight_blocks_without_import_data() -> None:
    _reset_store()

    response = process_preflight(
        ProcessPreflightRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={})
    )

    assert response.status == "success"
    assert response.data["allow_run"] is False
    assert any(item["code"] == "no_import_data" for item in response.data["blockers"])


def test_process_preflight_allows_clean_year_with_priced_trade() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="preflight.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                    "event_type": "buy",
                }
            ],
        )
    )

    response = process_preflight(
        ProcessPreflightRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={})
    )

    assert response.status == "success"
    assert response.data["allow_run"] is True
    assert response.data["counts"]["tax_year_events"] == 1
    assert response.data["blockers"] == []


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
    report_files_response = report_files(job_id)

    assert result.status == "success"
    assert result.data["job_id"] == job_id
    assert result.data["status"] == "completed"
    assert result.data["progress"] == 100
    assert result.data["result_summary"] is not None
    assert result.data["result_summary"]["processed_events"] == 2
    assert result.data["result_summary"]["derivatives"]["processed_events"] == 2
    assert "tax_domain_summary" in result.data["result_summary"]
    assert "fx_enrichment" in result.data["result_summary"]
    assert result.data["result_summary"]["fx_enrichment"]["unresolved_count"] == 0
    assert "anlage_so" in result.data["result_summary"]["tax_domain_summary"]
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
    assert report_files_response.status == "success"
    assert report_files_response.data["tax_line_count"] == 1
    assert report_files_response.data["derivative_line_count"] == 1
    file_scopes = {(item["scope"], item["format"]) for item in report_files_response.data["files"]}
    assert ("all", "json") in file_scopes
    assert ("all", "csv") in file_scopes
    assert ("all", "pdf") in file_scopes
    assert ("tax", "json") in file_scopes
    assert ("derivatives", "csv") in file_scopes
    pdf_response = report_export(job_id=job_id, scope="all", fmt="pdf")
    assert getattr(pdf_response, "media_type", "") == "application/pdf"
    pdf_body = asyncio.run(_read_streaming_body(pdf_response))
    assert pdf_body.startswith(b"%PDF")
    audit_response = audit_tax_line(job_id=job_id, line_no=1)
    assert audit_response.status == "success"
    assert audit_response.data["tax_line"]["line_no"] == 1
    assert audit_response.data["source_event"] is not None
    assert audit_response.data["calculation_trace"]["formula"] == "gain_loss_eur = proceeds_eur - cost_basis_eur"
    assert status.data["status"] == "completed"


def test_tax_domain_summary_endpoint_returns_split_blocks() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="tax_domains.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "IOT",
                    "event_type": "mining_reward",
                    "amount": "10",
                    "price_eur": "0.5",
                    "source": "heliumgeek",
                },
                {
                    "timestamp": "2026-01-02T12:00:00Z",
                    "asset": "DC",
                    "event_type": "data_credit_usage",
                    "amount_eur": "3",
                },
                {
                    "timestamp": "2026-01-03T12:00:00Z",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                },
                {
                    "timestamp": "2026-01-04T12:00:00Z",
                    "asset": "BTC",
                    "side": "sell",
                    "amount": "1",
                    "price_eur": "120",
                },
            ],
        )
    )
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))

    response = process_tax_domain_summary(job_id)
    assert response.status == "success"
    summary = response.data["tax_domain_summary"]
    assert summary["anlage_so"]["leistungen_income_eur"] == "5.0"
    assert summary["anlage_so"]["private_veraeusserung_net_taxable_eur"] == "20"
    assert summary["euer"]["betriebsausgaben_data_credits_eur"] == "3"


def test_process_compare_rulesets_post_matches_api_contract() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="compare.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                },
                {
                    "timestamp": "2026-01-02T12:00:00Z",
                    "asset": "BTC",
                    "side": "sell",
                    "amount": "1",
                    "price_eur": "120",
                },
            ],
        )
    )
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))

    response = process_compare_rulesets_post(
        ProcessCompareRulesetsRequest(
            job_id=job_id,
            compare_ruleset_id="DE-2026-v1.0",
            compare_ruleset_version="1.0",
        )
    )

    assert response.status == "success"
    assert response.data["job_id"] == job_id
    assert response.data["comparison"]["ruleset_id"] == "DE-2026-v1.0"


def test_tax_event_override_changes_domain_assignment() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="tax_override.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "IOT",
                    "event_type": "mining_reward",
                    "amount": "10",
                    "price_eur": "0.5",
                    "source": "heliumgeek",
                }
            ],
        )
    )
    first_job = process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))
    first_job_id = first_job.data["job_id"]
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    first_summary = process_tax_domain_summary(first_job_id).data["tax_domain_summary"]
    assert first_summary["anlage_so"]["leistungen_income_eur"] == "5.0"
    assert first_summary["euer"]["betriebseinnahmen_mining_staking_eur"] == "0"

    event_id = STORE.list_raw_events()[0]["unique_event_id"]
    upsert_response = tax_event_override_upsert(
        TaxEventOverrideUpsertRequest(
            source_event_id=event_id,
            tax_category="BUSINESS",
            note="Mining als gewerblich klassifiziert",
        )
    )
    assert upsert_response.status == "success"

    second_job = process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))
    second_job_id = second_job.data["job_id"]
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    second_summary = process_tax_domain_summary(second_job_id).data["tax_domain_summary"]
    assert second_summary["anlage_so"]["leistungen_income_eur"] == "0"
    assert second_summary["euer"]["betriebseinnahmen_mining_staking_eur"] == "5.0"


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


def test_audit_tax_line_not_found_returns_error() -> None:
    _reset_store()
    created = process_run(
        ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False)
    )
    job_id = created.data["job_id"]
    response = audit_tax_line(job_id=job_id, line_no=1)
    assert response.status == "error"
    assert response.errors[0]["code"] == "tax_line_not_found"


def test_portfolio_lot_aging_shows_split_lots() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="lots.csv",
            rows=[
                {
                    "timestamp": "2025-01-01T00:00:00Z",
                    "asset": "SOL",
                    "side": "buy",
                    "amount": "3",
                    "price_eur": "100",
                },
                {
                    "timestamp": "2025-05-01T00:00:00Z",
                    "asset": "SOL",
                    "side": "buy",
                    "amount": "4",
                    "price_eur": "110",
                },
                {
                    "timestamp": "2026-03-01T00:00:00Z",
                    "asset": "SOL",
                    "side": "buy",
                    "amount": "8",
                    "price_eur": "120",
                },
            ],
        )
    )
    resp = portfolio_lot_aging(as_of_utc="2026-05-01T00:00:00Z", asset="SOL")
    assert resp.status == "success"
    rows = resp.data.get("lot_rows", [])
    assert len(rows) == 3
    qtys = sorted([row["qty"] for row in rows])
    assert qtys == ["3", "4", "8"]
