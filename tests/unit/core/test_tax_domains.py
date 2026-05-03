from __future__ import annotations

from tax_engine.core.tax_domains import build_tax_domain_summary


def test_tax_domain_summary_splits_private_business_data_credits_and_derivatives() -> None:
    raw_events = [
        {
            "unique_event_id": "reward-private",
            "payload": {
                "timestamp_utc": "2026-01-01T12:00:00+00:00",
                "asset": "IOT",
                "event_type": "staking_reward",
                "quantity": "10",
                "price_eur": "0.5",
            },
        },
        {
            "unique_event_id": "reward-business",
            "payload": {
                "timestamp": "2026-01-02T12:00:00+00:00",
                "asset": "HNT",
                "event_type": "mining_reward",
                "value_eur": "12.50",
                "tax_category": "BUSINESS",
            },
        },
        {
            "unique_event_id": "dc-fee",
            "payload": {
                "timestamp": "2026-01-03T12:00:00+00:00",
                "asset": "DC",
                "event_type": "data_credit_usage",
                "fee_eur": "1.25",
            },
        },
        {
            "unique_event_id": "unresolved-reward",
            "payload": {
                "timestamp": "2026-01-04T12:00:00+00:00",
                "asset": "MOBILE",
                "event_type": "reward_claim",
                "source": "heliumgeek",
            },
        },
        {
            "unique_event_id": "old-reward",
            "payload": {
                "timestamp": "2025-01-04T12:00:00+00:00",
                "asset": "IOT",
                "event_type": "staking_reward",
                "value_eur": "99",
            },
        },
    ]
    tax_lines = [
        {"gain_loss_eur": "20", "tax_status": "taxable"},
        {"gain_loss_eur": "-3", "tax_status": "taxable"},
        {"gain_loss_eur": "100", "tax_status": "exempt"},
        {"gain_loss_eur": "-7", "tax_status": "exempt"},
    ]
    derivative_lines = [
        {"gain_loss_eur": "15"},
        {"gain_loss_eur": "-40"},
    ]

    summary = build_tax_domain_summary(
        raw_events=raw_events,
        tax_lines=tax_lines,
        derivative_lines=derivative_lines,
        tax_year=2026,
        ruleset_id="DE-2026-v1.0",
    )

    assert summary["classification_counts"]["reward_events"] == 3
    assert summary["classification_counts"]["mining_events"] == 2
    assert summary["classification_counts"]["data_credit_events"] == 1
    assert summary["classification_counts"]["unresolved_valuation_events"] == 1
    assert summary["anlage_so"]["leistungen_income_eur"] == "5.0"
    assert summary["anlage_so"]["private_veraeusserung_net_taxable_eur"] == "17"
    assert summary["anlage_so"]["private_veraeusserung_exempt_gain_eur"] == "100"
    assert summary["euer"]["betriebseinnahmen_mining_staking_eur"] == "12.50"
    assert summary["euer"]["betriebsausgaben_data_credits_eur"] == "1.25"
    assert summary["euer"]["betriebsergebnis_eur"] == "11.25"
    assert summary["termingeschaefte"]["netto_eur"] == "-25"
    assert summary["termingeschaefte"]["verlust_summe_abs_eur"] == "40"
