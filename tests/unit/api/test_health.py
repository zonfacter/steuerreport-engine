from tax_engine.api.app import StandardResponse, health


def test_health_payload_matches_standard_response_contract() -> None:
    payload = health()

    assert isinstance(payload, StandardResponse)
    assert payload.status == "success"
    assert isinstance(payload.trace_id, str)
    assert isinstance(payload.data, dict)
    assert payload.data["service"] == "steuerreport-engine"
    assert payload.data["uptime_state"] == "ok"
    assert isinstance(payload.errors, list)
    assert isinstance(payload.warnings, list)
