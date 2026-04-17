from decimal import Decimal

from tax_engine.ingestion.models import ImportProfile, NormalizePreviewRequest
from tax_engine.ingestion.normalizer import normalize_preview


def test_normalize_preview_with_subunit_conversion() -> None:
    request = NormalizePreviewRequest(
        rows=[{"asset": "SOL", "amount": "1000000000", "timestamp": "2026-01-01T00:00:00Z"}],
        profile=ImportProfile(
            profile_id="sol_profile",
            profile_version="1.0.0",
            decimal_separator=".",
            thousand_separator=",",
            subunit_factors={"lamports": Decimal("0.000000001")},
            subunit_field_map={"amount": "lamports"},
        ),
        numeric_fields=["amount"],
        datetime_fields=["timestamp"],
    )

    data, errors, warnings = normalize_preview(request)

    assert errors == []
    assert warnings == []
    assert data.normalized_rows[0].values["amount"] == "1"
    assert str(data.normalized_rows[0].values["timestamp"]).endswith("+00:00")


def test_normalize_preview_missing_conversion_factor_marks_error() -> None:
    request = NormalizePreviewRequest(
        rows=[{"asset": "SOL", "amount": "1000000000"}],
        profile=ImportProfile(
            profile_id="sol_profile",
            profile_version="1.0.0",
            subunit_field_map={"amount": "lamports"},
        ),
        numeric_fields=["amount"],
    )

    _, errors, warnings = normalize_preview(request)

    assert warnings == []
    assert len(errors) == 1
    assert errors[0].code == "conversion_factor_missing"


def test_normalize_preview_ambiguous_number_stays_unresolved() -> None:
    request = NormalizePreviewRequest(
        rows=[{"asset": "BTC", "amount": "1,234"}],
        profile=ImportProfile(profile_id="btc_profile", profile_version="1.0.0"),
        numeric_fields=["amount"],
    )

    data, errors, warnings = normalize_preview(request)

    assert errors == []
    assert len(warnings) == 1
    assert warnings[0].code == "number_format_error"
    assert "amount" in data.normalized_rows[0].unresolved_fields
    assert data.normalized_rows[0].values["amount"] == "1,234"
