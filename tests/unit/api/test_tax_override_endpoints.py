from __future__ import annotations

from tax_engine.api.app import (
    TaxEventOverrideDeleteRequest,
    TaxEventOverrideUpsertRequest,
    import_confirm,
    tax_event_override_delete,
    tax_event_override_upsert,
    tax_event_overrides_list,
)
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE


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

