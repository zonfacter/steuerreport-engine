from decimal import Decimal

from tax_engine.integrity.fingerprint import unique_event_id


def test_unique_event_id_is_deterministic_for_same_payload() -> None:
    payload_a = {"asset": "BTC", "qty": Decimal("1.2300"), "timestamp": "2026-01-01T00:00:00Z"}
    payload_b = {"timestamp": "2026-01-01T00:00:00Z", "qty": Decimal("1.23"), "asset": "BTC"}

    assert unique_event_id(payload_a) == unique_event_id(payload_b)


def test_unique_event_id_changes_on_payload_change() -> None:
    payload_a = {"asset": "BTC", "qty": "1.23", "timestamp": "2026-01-01T00:00:00Z"}
    payload_b = {"asset": "BTC", "qty": "1.24", "timestamp": "2026-01-01T00:00:00Z"}

    assert unique_event_id(payload_a) != unique_event_id(payload_b)
