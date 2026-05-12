from __future__ import annotations

from tax_engine.api.product_positions import product_position_events, product_position_summary
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_product_position_events_and_summary_roundtrip() -> None:
    _reset_store()
    result = STORE.upsert_product_position_events(
        [
            {
                "event_id": "evt-principal",
                "platform": "binance",
                "product_type": "simple_locked_subscription",
                "product_id": "Sol*120",
                "position_id": "123",
                "event_type": "simple_locked_subscription",
                "tax_treatment": "non_taxable_principal_movement",
                "asset": "SOL",
                "quantity": "9.84095708",
                "timestamp_utc": "2026-01-25T13:58:59+00:00",
                "source_ref": "purchase-1",
                "raw": {"amount": "9.84095708"},
            },
            {
                "event_id": "evt-reward",
                "platform": "binance",
                "product_type": "simple_locked_rewards",
                "product_id": "Sol*120",
                "position_id": "123",
                "event_type": "simple_locked_rewards",
                "tax_treatment": "reward_income_candidate",
                "asset": "SOL",
                "quantity": "0.001",
                "timestamp_utc": "2026-01-27T01:05:50+00:00",
                "source_ref": "reward-1",
                "raw": {"amount": "0.001"},
            },
        ]
    )

    assert result == {"inserted": 2, "updated": 0, "total": 2}

    events = product_position_events(platform="binance", asset="SOL")
    assert events.status == "success"
    assert events.data["count"] == 2
    assert events.data["rows"][0]["event_id"] == "evt-principal"

    summary = product_position_summary(platform="binance")
    assert summary.status == "success"
    assert summary.data["tax_treatment_counts"]["non_taxable_principal_movement"] == 1
    assert summary.data["tax_treatment_counts"]["reward_income_candidate"] == 1
    sol = summary.data["assets"][0]
    assert sol["asset"] == "SOL"
    assert sol["principal_movement_abs_qty"] == "9.84095708"
    assert sol["reward_income_candidate_qty"] == "0.001"
