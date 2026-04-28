from __future__ import annotations

import asyncio
import json

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError

from tax_engine.api.app import (
    ReportSnapshotCreateRequest,
    RulesetUpsertRequest,
    _build_csv_from_rows,
    _build_export_rows,
    _build_report_file_index,
    _decorate_token_rows,
    _format_ruleset_row,
    _http_exception_handler,
    _load_issue_overrides,
    _load_tax_event_overrides,
    _load_token_aliases,
    _load_unresolved_fx_issues,
    _parse_iso_timestamp,
    _to_iso_date,
    _unhandled_exception_handler,
    _validation_exception_handler,
    compliance_classification,
    create_snapshot,
    get_snapshot,
    import_confirm,
    integrity_event,
    integrity_report,
    process_run,
    process_worker_run_next,
    report_export,
    review_gates,
    ruleset_get,
    ruleset_list,
    ruleset_upsert,
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


def _request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/test", "headers": []})


def _completed_job_with_events() -> str:
    import_confirm(
        ConfirmImportRequest(
            source_name="coverage_api.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                },
                {
                    "timestamp": "2026-02-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "sell",
                    "amount": "0.2",
                    "price_eur": "130",
                },
                {
                    "timestamp": "2026-03-01T12:00:00Z",
                    "asset": "IOT",
                    "event_type": "mining_reward",
                    "amount": "10",
                    "value_eur": "300",
                    "source": "heliumgeek",
                },
            ],
        )
    )
    created = process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))
    job_id = str(created.data["job_id"])
    processed = process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    assert processed.status == "success"
    return job_id


def test_api_exception_handlers_return_standard_envelope() -> None:
    validation_response = asyncio.run(
        _validation_exception_handler(_request(), RequestValidationError([]))
    )
    assert validation_response.status_code == 422
    assert json.loads(validation_response.body)["errors"][0]["code"] == "validation_error"

    http_response = asyncio.run(
        _http_exception_handler(_request(), HTTPException(status_code=404, detail="missing"))
    )
    assert http_response.status_code == 404
    assert json.loads(http_response.body)["errors"][0]["code"] == "http_error"

    internal_response = asyncio.run(_unhandled_exception_handler(_request(), RuntimeError("boom")))
    assert internal_response.status_code == 500
    assert json.loads(internal_response.body)["errors"][0]["code"] == "internal_error"


def test_ruleset_catalog_roundtrip_and_validation_paths() -> None:
    _reset_store()

    assert _to_iso_date("2026-04-28") == "2026-04-28"
    assert _to_iso_date("2026-04-28T12:00:00") == "2026-04-28"
    formatted = _format_ruleset_row(
        {
            "ruleset_id": "DE-TEST",
            "ruleset_version": "1.0",
            "status": "draft",
            "source_hash": "secret",
            "approved_by": "tester",
            "notes": "internal",
            "created_at_utc": "now",
        }
    )
    assert formatted == {"ruleset_id": "DE-TEST", "ruleset_version": "1.0"}
    assert _format_ruleset_row({"ruleset_id": "DE-TEST", "status": "draft"}, include_status=True)["status"] == "draft"
    try:
        _to_iso_date("28.04.2026")
    except ValueError as exc:
        assert str(exc) == "invalid_date"
    else:  # pragma: no cover
        raise AssertionError("invalid date was accepted")

    invalid = ruleset_upsert(
        RulesetUpsertRequest(
            ruleset_id="DE-CUSTOM",
            ruleset_version="1.0",
            jurisdiction="DE",
            valid_from="2026/01/01",
            valid_to="2026-12-31",
            exemption_limit_so="1000",
            holding_period_months=12,
            mining_tax_category="INCOME",
        )
    )
    assert invalid.status == "error"
    assert invalid.errors[0]["code"] == "invalid_ruleset_dates"

    saved = ruleset_upsert(
        RulesetUpsertRequest(
            ruleset_id="DE-CUSTOM",
            ruleset_version="1.0",
            jurisdiction="DE",
            valid_from="2026-01-01",
            valid_to="2026-12-31",
            exemption_limit_so="1000",
            other_services_exemption_limit="256",
            holding_period_months=12,
            staking_extension=False,
            mining_tax_category="BUSINESS",
            approved_by="Test",
            notes="Coverage gate",
        )
    )
    assert saved.status == "success"

    listed = ruleset_list(include_pending=True)
    assert any(row["ruleset_id"] == "DE-CUSTOM" for row in listed.data["rulesets"])
    fetched = ruleset_get("DE-CUSTOM", "1.0")
    assert fetched.status == "success"
    missing = ruleset_get("NOPE", "1.0")
    assert missing.status == "error"


def test_report_export_integrity_snapshot_and_compliance_paths() -> None:
    _reset_store()
    job_id = _completed_job_with_events()

    integrity = integrity_report(job_id)
    assert integrity.status == "success"
    assert integrity.data["report_integrity_id"]

    json_export = report_export(job_id=job_id, scope="all", fmt="json")
    assert json_export.status == "success"
    assert json_export.data["integrity"]["report_integrity_id"] == integrity.data["report_integrity_id"]

    csv_export = report_export(job_id=job_id, scope="tax", fmt="csv")
    csv_body = asyncio.run(_read_streaming_body(csv_export)).decode("utf-8")
    assert "report_integrity_id" in csv_body

    assert report_export(job_id=job_id, scope="unknown", fmt="json").errors[0]["code"] == "invalid_scope"
    assert report_export(job_id=job_id, scope="all", fmt="xlsx").errors[0]["code"] == "invalid_format"
    assert report_export(job_id="missing", scope="all", fmt="json").errors[0]["code"] == "job_not_found"
    assert report_export(job_id=job_id, scope="all", fmt="pdf", part=2).errors[0]["code"] == "report_part_not_found"

    classification = compliance_classification(job_id)
    assert classification.status == "success"
    assert classification.data["is_commercial"] is True
    assert any(reason["code"] == "mining_threshold" for reason in classification.data["reasons"])

    snapshot = create_snapshot(job_id, ReportSnapshotCreateRequest(notes="coverage snapshot"))
    assert snapshot.status == "success"
    snapshot_id = str(snapshot.data["snapshot_id"])
    fetched_snapshot = get_snapshot(snapshot_id)
    assert fetched_snapshot.status == "success"
    assert fetched_snapshot.data["summary"]
    assert get_snapshot("missing").errors[0]["code"] == "snapshot_not_found"

    event_id = STORE.list_raw_events()[0]["unique_event_id"]
    event_resp = integrity_event(str(event_id))
    assert event_resp.status == "success"
    assert integrity_event("missing-event").errors[0]["code"] == "event_not_found"


def test_report_helpers_and_review_gate_empty_completed_job_paths() -> None:
    _reset_store()
    created = process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    job_id = str(created.data["job_id"])

    gates = review_gates(job_id=job_id)
    assert gates.status == "success"
    assert any(item["code"] == "process_job_empty" for item in gates.data["warning_reasons"])
    assert any(item["code"] == "job_id_missing" for item in review_gates().data["warning_reasons"])

    job = {"job_id": job_id, "tax_year": 2026, "ruleset_id": "DE-2026-v1.0", "ruleset_version": "1.0"}
    tax_rows = [{"line_no": 1, "asset": "BTC", "qty": "0.1", "gain_loss_eur": "5"}]
    derivative_rows = [{"line_no": 1, "asset": "ETH", "position_id": "p1", "gain_loss_eur": "-7"}]
    export_rows = _build_export_rows(
        job,
        tax_rows,
        derivative_rows,
        include_derivatives=True,
        integrity={"report_integrity_id": "rid", "config_hash": "cfg", "data_hash": "data"},
    )
    assert {row["line_type"] for row in export_rows} == {"tax", "derivative"}
    assert "report_integrity_id" in _build_csv_from_rows(export_rows)
    files = _build_report_file_index(job, tax_line_count=1, derivative_line_count=1)
    assert any(item["format"] == "pdf" and item["scope"] == "all" for item in files)


def test_dashboard_setting_helpers_cover_alias_overrides_and_invalid_payloads() -> None:
    _reset_store()
    mint = "CM8VSESV7MBHAFD5UDXH84QFGXMAVWJCVVHOPB1DZIF4"
    STORE.upsert_setting(
        "runtime.token_aliases",
        json.dumps({mint: {"symbol": "IOT", "name": "Helium IOT", "notes": "known"}}),
        False,
    )
    STORE.upsert_setting(
        "runtime.ignored_tokens",
        json.dumps({mint: {"reason": "Spam", "updated_at_utc": "2026-01-01T00:00:00+00:00"}}),
        False,
    )
    STORE.upsert_setting(
        "runtime.tax_event_overrides",
        json.dumps({"evt-1": {"tax_category": "gewerbe", "note": "manual", "updated_at_utc": "now"}}),
        False,
    )
    STORE.upsert_setting(
        "runtime.issue_status_overrides",
        json.dumps({"issue-1": {"status": "won_t_fix", "note": "ignored", "updated_at_utc": "now"}}),
        False,
    )
    STORE.upsert_setting(
        "runtime.fx.unresolved_events",
        json.dumps([{"source_event_id": "evt-1", "rate_date": "2026-01-01"}]),
        False,
    )

    assert _load_token_aliases()[mint]["symbol"] == "IOT"
    decorated = _decorate_token_rows([{"asset": mint, "quantity": "1000000000"}])
    assert decorated[0]["symbol"] == "IOT"
    assert decorated[0]["ignored"] == "true"
    assert _load_tax_event_overrides()["evt-1"]["tax_category"] == "BUSINESS"
    assert _load_issue_overrides()["issue-1"]["status"] == "wont_fix"
    assert _load_unresolved_fx_issues()[0]["reason"] == "unknown"
    assert _parse_iso_timestamp("2026-01-01T00:00:00Z") is not None
    assert _parse_iso_timestamp("not-a-date") is None

    STORE.upsert_setting("runtime.token_aliases", "{bad-json", False)
    STORE.upsert_setting("runtime.ignored_tokens", "[]", False)
    STORE.upsert_setting("runtime.tax_event_overrides", "[]", False)
    STORE.upsert_setting("runtime.issue_status_overrides", "{bad-json", False)
    STORE.upsert_setting("runtime.fx.unresolved_events", "{}", False)
    assert _load_token_aliases() == {}
    assert _decorate_token_rows([{"asset": "UNKNOWNMINT", "quantity": "1E+9"}])[0]["spam_candidate"] == "true"
    assert _load_tax_event_overrides() == {}
    assert _load_issue_overrides() == {}
    assert _load_unresolved_fx_issues() == []
