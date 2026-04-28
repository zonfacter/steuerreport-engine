from __future__ import annotations

from tax_engine.api.app import (
    TaxEventOverrideDeleteRequest,
    TaxEventOverrideUpsertRequest,
    import_confirm,
    process_run,
    process_tax_lines,
    process_worker_run_next,
    tax_event_override_delete,
    tax_event_override_upsert,
    tax_event_overrides_list,
)
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE
from tax_engine.queue import ProcessRunRequest, WorkerRunNextRequest


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_tax_override_upsert_list_delete_flow() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="override_src.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "asset": "IOT",
                    "event_type": "mining_reward",
                    "amount": "1",
                    "price_eur": "1",
                }
            ],
        )
    )
    event_id = STORE.list_raw_events()[0]["unique_event_id"]

    upsert = tax_event_override_upsert(
        TaxEventOverrideUpsertRequest(
            source_event_id=event_id,
            tax_category="BUSINESS",
            note="gewerblich",
        )
    )
    assert upsert.status == "success"
    assert upsert.data["tax_category"] == "BUSINESS"

    listed = tax_event_overrides_list()
    assert listed.status == "success"
    assert listed.data["count"] == 1
    assert listed.data["rows"][0]["source_event_id"] == event_id

    deleted = tax_event_override_delete(TaxEventOverrideDeleteRequest(source_event_id=event_id))
    assert deleted.status == "success"
    assert deleted.data["deleted"] is True


def test_tax_override_excludes_event_from_processing_without_deleting_raw() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="override_excluded.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "asset": "SOL",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "10",
                },
                {
                    "timestamp": "2026-02-01T00:00:00Z",
                    "asset": "SOL",
                    "side": "sell",
                    "amount": "1",
                    "price_eur": "12",
                },
            ],
        )
    )
    sell_event_id = STORE.list_raw_events()[1]["unique_event_id"]

    upsert = tax_event_override_upsert(
        TaxEventOverrideUpsertRequest(
            source_event_id=sell_event_id,
            tax_category="EXCLUDED",
            reason_code="duplicate_import",
            note="Blockpit-Referenzimport, Primärdaten bereits vorhanden",
        )
    )
    assert upsert.status == "success"
    assert upsert.data["tax_category"] == "EXCLUDED"
    assert len(STORE.list_raw_events()) == 2

    job = process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    tax_lines = process_tax_lines(job.data["job_id"])

    assert tax_lines.status == "success"
    assert tax_lines.data["count"] == 0
    assert len(STORE.list_raw_events()) == 2


def test_tax_override_exclusion_requires_reason_and_note() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="override_excluded_invalid.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "asset": "SOL",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "10",
                }
            ],
        )
    )
    event_id = STORE.list_raw_events()[0]["unique_event_id"]

    missing_reason = tax_event_override_upsert(
        TaxEventOverrideUpsertRequest(
            source_event_id=event_id,
            tax_category="EXCLUDED",
            note="manuell geprüft",
        )
    )
    assert missing_reason.status == "error"
    assert missing_reason.errors[0]["code"] == "invalid_exclusion_reason"

    missing_note = tax_event_override_upsert(
        TaxEventOverrideUpsertRequest(
            source_event_id=event_id,
            tax_category="EXCLUDED",
            reason_code="duplicate_import",
        )
    )
    assert missing_note.status == "error"
    assert missing_note.errors[0]["code"] == "exclusion_note_required"
