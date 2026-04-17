from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from tax_engine.integrity import (
    config_fingerprint,
    event_fingerprint,
    report_integrity_id,
)


def test_event_fingerprint_is_deterministic_across_key_order() -> None:
    payload_a = {
        "asset": "BTC",
        "amount": Decimal("1.2345"),
        "timestamp": datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
    }
    payload_b = {
        "timestamp": datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
        "amount": Decimal("1.2345"),
        "asset": "BTC",
    }

    assert event_fingerprint(payload_a) == event_fingerprint(payload_b)


def test_report_integrity_id_changes_with_config() -> None:
    event_hashes = ["a", "b", "c"]
    ruleset_hash = "ruleset"
    config_hash_a = config_fingerprint({"depot_mode": "global"})
    config_hash_b = config_fingerprint({"depot_mode": "separated"})

    value_a = report_integrity_id(event_hashes, ruleset_hash, config_hash_a)
    value_b = report_integrity_id(event_hashes, ruleset_hash, config_hash_b)

    assert value_a != value_b

