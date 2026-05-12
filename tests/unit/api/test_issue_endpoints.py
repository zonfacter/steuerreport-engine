from __future__ import annotations

from tax_engine.admin import put_admin_setting
from tax_engine.api.app import (
    AiReviewAnalyzeRequest,
    AiReviewApplySuggestionRequest,
    BalanceAdjustmentCandidateDecisionRequest,
    BalanceAdjustmentCandidateUpsertRequest,
    IntegrationConflictResolveRequest,
    IssueStatusUpdateRequest,
    ReviewMergeRequest,
    ReviewSplitRequest,
    ReviewTimezoneCorrectRequest,
    TaxEventOverrideUpsertRequest,
    ai_review_analyze,
    ai_review_apply_suggestion,
    ai_review_suggestions,
    balance_adjustment_candidate_decide,
    balance_adjustment_candidate_decision_preview,
    balance_adjustment_candidate_evidence_package,
    balance_adjustment_candidate_upsert,
    balance_adjustment_candidates_list,
    import_confirm,
    issues_inbox,
    issues_update_status,
    process_run,
    process_worker_run_next,
    regulatory_dac8_carf_context,
    review_actions,
    review_gates,
    review_integration_conflicts,
    review_integration_conflicts_resolve,
    review_issue_context,
    review_merge,
    review_negative_balances,
    review_split,
    review_timezone_correct,
    tax_event_override_upsert,
    tax_event_overrides_list,
)
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE
from tax_engine.integrations import upsert_integration_mode
from tax_engine.queue.models import ProcessRunRequest, WorkerRunNextRequest


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_issues_inbox_contains_unmatched_transfer_issue() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="issues.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "SOL",
                    "event_type": "withdrawal",
                    "amount": "1.0",
                }
            ],
        )
    )
    resp = issues_inbox()
    assert resp.status == "success"
    issues = resp.data.get("issues", [])
    assert any(str(item.get("type")) == "unmatched_transfer" for item in issues)


def test_issue_status_update_persists() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="issues2.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "amount": "0.1",
                    "price_eur": "0",
                }
            ],
        )
    )
    inbox = issues_inbox()
    assert inbox.status == "success"
    issue_id = str(inbox.data.get("issues", [])[0].get("issue_id"))
    upd = issues_update_status(
        IssueStatusUpdateRequest(issue_id=issue_id, status="in_review", note="Manuell geprüft")
    )
    assert upd.status == "success"

    inbox2 = issues_inbox()
    assert inbox2.status == "success"
    issue = next(item for item in inbox2.data.get("issues", []) if str(item.get("issue_id")) == issue_id)
    assert issue.get("status") == "in_review"


def test_review_gates_blocks_when_unmatched_and_open_issues_exist() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="gates.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "amount": "0.1",
                    "price_eur": "0",
                },
                {
                    "timestamp": "2026-01-01T12:05:00Z",
                    "asset": "SOL",
                    "event_type": "withdrawal",
                    "amount": "2.0",
                },
            ],
        )
    )
    resp = review_gates()
    assert resp.status == "success"
    assert resp.data.get("allow_export") is False
    assert (resp.data.get("counts") or {}).get("unmatched_total", 0) >= 1
    blocking_codes = {str(item.get("code")) for item in (resp.data.get("blocking_reasons") or [])}
    assert "unmatched_transfers_open" in blocking_codes


def test_review_gates_block_on_balance_adjustment_candidate_needing_evidence() -> None:
    _reset_store()
    upsert = balance_adjustment_candidate_upsert(
        BalanceAdjustmentCandidateUpsertRequest(
            candidate_id="pionex-usdt-opening-balance-2021-12-28",
            platform="pionex",
            asset="USDT",
            quantity_delta="1643.2312211162",
            effective_timestamp_utc="2021-12-28T00:49:11+00:00",
            adjustment_type="opening_balance_candidate",
            status="needs_evidence",
            reason_code="missing_pionex_bot_start_capital",
            note="Needs primary Pionex evidence or explicit non-tax review decision.",
            evidence={"report": "docs/167_PIONEX_USDT_FINAL_BLOCKER_AUDIT_2026-05-09.md"},
        )
    )
    assert upsert.status == "success"

    resp = review_gates()

    assert resp.status == "success"
    assert resp.data["allow_export"] is False
    assert resp.data["counts"]["balance_adjustment_candidates_open"] == 1
    blocking_codes = {str(item.get("code")) for item in (resp.data.get("blocking_reasons") or [])}
    assert "balance_adjustment_candidates_need_decision" in blocking_codes
    candidates = resp.data["balance_adjustment_candidates"]
    assert candidates[0]["candidate_id"] == "pionex-usdt-opening-balance-2021-12-28"
    assert candidates[0]["tax_effective"] is False
    assert "required_evidence" in candidates[0]
    assert candidates[0]["api_actions"]["approve_non_tax_inventory_normalization"]["path"].endswith("/decide")
    assert resp.data["draft_export_policy"]["draft_export_allowed"] is True
    assert resp.data["draft_export_policy"]["final_export_allowed"] is False


def test_review_gates_block_on_material_zero_cost_tax_lots() -> None:
    _reset_store()
    job_id = "zero-cost-job"
    STORE.create_processing_job(
        job_id=job_id,
        tax_year=2025,
        ruleset_id="DE-2025-v1.0",
        ruleset_version="1.0",
        config_hash="test",
        config_json="{}",
        status="completed",
        progress=100,
    )
    STORE.replace_tax_lines(
        job_id,
        [
            {
                "asset": "JUP",
                "qty": "1500",
                "buy_timestamp_utc": "2024-12-09T08:21:44+00:00",
                "sell_timestamp_utc": "2025-01-19T22:39:56+00:00",
                "cost_basis_eur": "0",
                "proceeds_eur": "5500.00",
                "gain_loss_eur": "5500.00",
                "hold_days": 41,
                "tax_status": "taxable",
                "source_event_id": "sell-event-1",
                "lot_source_event_id": "lot-event-1",
                "transfer_chain_id": "",
            }
        ],
    )

    inbox = issues_inbox()
    assert inbox.status == "success"
    zero_cost_issues = [item for item in inbox.data["issues"] if item["type"] == "zero_cost_tax_lots"]
    assert len(zero_cost_issues) == 1
    assert zero_cost_issues[0]["severity"] == "high"
    assert "Cost Basis 0" in zero_cost_issues[0]["title"]
    assert zero_cost_issues[0]["api_actions"]["context"]["path"].endswith(zero_cost_issues[0]["issue_id"])
    assert zero_cost_issues[0]["api_actions"]["confirm_zero_basis"]["body"]["status"] == "wont_fix"

    context = review_issue_context(zero_cost_issues[0]["issue_id"])
    assert context.status == "success"
    assert context.data["type"] == "zero_cost_tax_lots"
    assert context.data["tax_year"] == 2025
    assert context.data["asset"] == "JUP"
    assert context.data["row_count"] == 1
    assert context.data["total_proceeds_eur"] == "5500.00"
    assert context.data["tax_lines"][0]["source_event_id"] == "sell-event-1"

    gates = review_gates()
    assert gates.status == "success"
    assert gates.data["allow_export"] is False
    assert gates.data["counts"]["issues_open"] == 1

    updated = issues_update_status(
        IssueStatusUpdateRequest(
            issue_id=zero_cost_issues[0]["issue_id"],
            status="wont_fix",
            note="Explizite Nullbasis bestaetigt.",
        )
    )
    assert updated.status == "success"
    gates_after_decision = review_gates()
    assert gates_after_decision.status == "success"
    assert gates_after_decision.data["allow_export"] is True
    assert gates_after_decision.data["counts"]["issues_open"] == 0


def test_review_gates_counts_closed_tax_year_zero_cost_lots_separately() -> None:
    _reset_store()
    put_admin_setting("runtime.review.closed_tax_years", [2021, 2022], is_secret=False)
    job_id = "closed-year-zero-cost-job"
    STORE.create_processing_job(
        job_id=job_id,
        tax_year=2022,
        ruleset_id="DE-2022-v1.0",
        ruleset_version="1.0",
        config_hash="test",
        config_json="{}",
        status="completed",
        progress=100,
    )
    STORE.replace_tax_lines(
        job_id,
        [
            {
                "asset": "HNT",
                "qty": "100",
                "buy_timestamp_utc": "2022-09-09T04:17:39+00:00",
                "sell_timestamp_utc": "2022-09-09T04:17:39+00:00",
                "cost_basis_eur": "0",
                "proceeds_eur": "6000.00",
                "gain_loss_eur": "6000.00",
                "hold_days": 0,
                "tax_status": "taxable",
                "source_event_id": "sell-event-closed-year",
                "lot_source_event_id": "",
                "transfer_chain_id": "",
            }
        ],
    )

    inbox = issues_inbox()
    zero_cost_issues = [item for item in inbox.data["issues"] if item["type"] == "zero_cost_tax_lots"]

    assert len(zero_cost_issues) == 1
    assert zero_cost_issues[0]["tax_year"] == 2022
    assert zero_cost_issues[0]["review_scope"] == "closed_tax_year"
    assert zero_cost_issues[0]["is_current_scope"] is False

    gates = review_gates()
    assert gates.status == "success"
    assert gates.data["allow_export"] is True
    assert gates.data["counts"]["issues_open"] == 0
    assert gates.data["counts"]["issues_open_total"] == 1
    assert gates.data["counts"]["issues_historical_open"] == 1
    assert gates.data["counts"]["issues_high_open"] == 0


def test_issues_inbox_contains_missing_fx_rate_issue(monkeypatch) -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="fx_missing.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "amount": "0.1",
                    "price": "100",
                    "quote_asset": "USDT",
                }
            ],
        )
    )

    from tax_engine.queue import service as queue_service

    monkeypatch.setattr(
        queue_service.FallbackFxResolver,
        "get_usd_to_eur_rate",
        lambda self, rate_date: None,
    )

    process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}, dry_run=False))
    process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    resp = issues_inbox()
    assert resp.status == "success"
    issues = resp.data.get("issues", [])
    assert any(str(item.get("type")) == "missing_fx_rate" for item in issues)


def test_issues_inbox_does_not_flag_binance_api_eur_quote_trade_as_missing_price() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="binance-api-eur-quote.csv",
            rows=[
                {
                    "timestamp_utc": "2025-10-13T12:45:07.878000+00:00",
                    "source": "binance_api",
                    "asset": "BNBEUR",
                    "base_asset": "BNB",
                    "quote_asset": "EUR",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "0.05",
                    "price": "1122.48",
                }
            ],
        )
    )

    resp = issues_inbox()

    assert resp.status == "success"
    assert not any(str(item.get("type")) == "missing_price" for item in resp.data.get("issues", []))


def test_review_negative_balances_uses_base_asset_for_binance_api_pairs() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="binance-api-pair-assets.csv",
            rows=[
                {
                    "timestamp_utc": "2025-01-01T10:00:00+00:00",
                    "source": "binance_api",
                    "asset": "JUPUSDT",
                    "base_asset": "JUP",
                    "quote_asset": "USDT",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "10",
                    "price": "0.8",
                },
                {
                    "timestamp_utc": "2025-01-02T10:00:00+00:00",
                    "source": "binance_api",
                    "asset": "JUPUSDT",
                    "base_asset": "JUP",
                    "quote_asset": "USDT",
                    "event_type": "trade",
                    "side": "sell",
                    "quantity": "5",
                    "price": "0.9",
                },
            ],
        )
    )

    resp = review_negative_balances(as_of="2025-12-31", include_events=5)

    assert resp.status == "success"
    assets = {str(item.get("asset")) for item in resp.data.get("rows", [])}
    assert "JUPUSDT" not in assets
    assert "JUP" not in assets


def test_integration_conflicts_compare_reference_and_primary_sources() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="primary.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T12:00:00Z",
                    "source": "binance",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "0.5",
                    "price_eur": "100",
                }
            ],
        )
    )
    import_confirm(
        ConfirmImportRequest(
            source_name="blockpit_reference.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T14:00:00Z",
                    "source": "blockpit",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "0.500000000",
                    "price_eur": "100",
                }
            ],
        )
    )

    conflicts = review_integration_conflicts()
    assert conflicts.status == "success"
    assert conflicts.data["count"] == 1
    row = conflicts.data["conflicts"][0]
    assert row["asset"] == "BTC"
    assert row["primary_sources"] == ["binance"]
    assert row["reference_sources"] == ["blockpit"]

    inbox = issues_inbox()
    assert not any(str(item.get("type")) == "integration_conflict" for item in inbox.data.get("issues", []))


def test_integration_conflict_resolve_excludes_reference_events() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="primary.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T12:00:00Z",
                    "source": "binance",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "0.5",
                    "price_eur": "100",
                }
            ],
        )
    )
    import_confirm(
        ConfirmImportRequest(
            source_name="blockpit_reference.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T14:00:00Z",
                    "source": "blockpit",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "0.500000000",
                    "price_eur": "100",
                }
            ],
        )
    )
    conflict = review_integration_conflicts().data["conflicts"][0]

    result = review_integration_conflicts_resolve(
        IntegrationConflictResolveRequest(
            conflict_ids=[conflict["conflict_id"]],
            action="exclude_reference_events",
            reason_code="duplicate_import",
            note="Blockpit ist nur Referenz, Primärdaten sind vorhanden.",
        )
    )

    assert result.status == "success"
    assert result.data["resolved_count"] == 1
    assert result.data["excluded_event_count"] == 1
    overrides = tax_event_overrides_list()
    assert overrides.data["rows"][0]["tax_category"] == "EXCLUDED"
    inbox = issues_inbox()
    conflict_issues = [item for item in inbox.data["issues"] if item["type"] == "integration_conflict"]
    assert conflict_issues[0]["status"] == "resolved"


def test_reference_integrations_do_not_create_missing_price_issues() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="blockpit_reference.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T12:00:00Z",
                    "source": "blockpit",
                    "asset": "TRUMP",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "10",
                }
            ],
        )
    )

    inbox = issues_inbox()
    assert not any(str(item.get("type")) == "missing_price" for item in inbox.data.get("issues", []))


def test_active_blockpit_trade_uses_raw_counterparty_value() -> None:
    _reset_store()
    upsert_integration_mode("blockpit", "active", "Primaerquelle fuer Bewertungstest")
    import_confirm(
        ConfirmImportRequest(
            source_name="blockpit_active.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T12:00:00Z",
                    "source": "blockpit",
                    "asset": "TRUMP",
                    "event_type": "trade",
                    "side": "buy",
                    "quantity": "10",
                    "raw_row": {
                        "Incoming Asset": "TRUMP",
                        "Incoming Amount": "10",
                        "Outgoing Asset": "USDT",
                        "Outgoing Amount": "100",
                    },
                }
            ],
        )
    )

    inbox = issues_inbox()
    assert not any(str(item.get("type")) == "missing_price" for item in inbox.data.get("issues", []))


def test_solscan_indexed_swap_value_is_not_missing_price() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="solscan_mobile_swap.json",
            rows=[
                {
                    "timestamp_utc": "2023-07-30T06:59:13+00:00",
                    "source": "solscan_wallet_discovery",
                    "asset": "MOBILE",
                    "asset_address": "mb1eu7TzEc71KxDpsmsKoucSSuuoGLv1drys1oP2jh6",
                    "event_type": "swap_in_aggregated",
                    "side": "in",
                    "quantity": "64729.546356",
                    "raw_row": {
                        "classification": "dex_swap_or_route",
                        "token_address": "mb1eu7TzEc71KxDpsmsKoucSSuuoGLv1drys1oP2jh6",
                        "value_usd_sum": "22.000764000000007",
                    },
                }
            ],
        )
    )

    inbox = issues_inbox()
    assert not any(str(item.get("type")) == "missing_price" for item in inbox.data.get("issues", []))


def test_eur_event_is_priced_from_fiat_quantity() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="bitget_tax_api.csv",
            rows=[
                {
                    "timestamp_utc": "2025-04-22T10:22:51Z",
                    "source": "bitget_tax_api",
                    "asset": "EUR",
                    "event_type": "trade",
                    "side": "out",
                    "quantity": "999.8598",
                }
            ],
        )
    )

    inbox = issues_inbox()
    assert not any(str(item.get("type")) == "missing_price" for item in inbox.data.get("issues", []))


def test_review_negative_balances_exposes_api_actions_and_status_override() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="negative_balances.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T12:00:00Z",
                    "source": "binance",
                    "asset": "USDT",
                    "event_type": "trade",
                    "side": "out",
                    "quantity": "150",
                },
                {
                    "timestamp_utc": "2026-01-01T12:05:00Z",
                    "source": "binance",
                    "asset": "USDT",
                    "event_type": "trade",
                    "side": "in",
                    "quantity": "25",
                },
            ],
        )
    )

    resp = review_negative_balances(as_of="2026-01-01")
    assert resp.status == "success"
    assert resp.data["count"] == 1
    row = resp.data["rows"][0]
    assert row["issue_id"] == "negative_balance:2026-01-01:USDT"
    assert row["balance"] == "-125"
    assert row["value_usd"] == "-125"
    assert row["status"] == "open"
    assert row["api_actions"]["set_status"]["path"] == "/api/v1/issues/update-status"
    assert row["api_actions"]["comment_last_event"]["body"]["source_event_id"]
    assert resp.data["api"]["transaction_search"] == "GET /api/v1/dashboard/transaction-search"

    without_events = review_negative_balances(as_of="2026-01-01", include_events=0)
    assert without_events.status == "success"
    assert without_events.data["rows"][0]["recent_events"] == []
    assert without_events.data["rows"][0]["last_event"] == {}
    assert without_events.data["rows"][0]["api_actions"]["comment_last_event"]["body"]["source_event_id"] == ""

    updated = issues_update_status(
        IssueStatusUpdateRequest(
            issue_id=row["issue_id"],
            status="in_review",
            note="USDT-Abfluss gegen Margin-/Futures-Quelle prüfen.",
        )
    )
    assert updated.status == "success"
    after = review_negative_balances(as_of="2026-01-01")
    assert after.data["rows"][0]["status"] == "in_review"


def test_review_negative_balances_year_without_events_returns_empty_success() -> None:
    _reset_store()

    resp = review_negative_balances(year=2020)

    assert resp.status == "success"
    assert resp.data["mode"] == "year"
    assert resp.data["year"] == 2020
    assert resp.data["checkpoint_count"] == 0
    assert resp.data["count"] == 0
    assert resp.data["rows"] == []
    assert resp.data["api"]["set_status"] == "POST /api/v1/issues/update-status"


def test_review_negative_balances_canonicalizes_known_token_mints() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="jup_alias_balances.csv",
            rows=[
                {
                    "timestamp_utc": "2025-06-12T08:49:25Z",
                    "source": "blockpit",
                    "asset": "JUP",
                    "event_type": "deposit",
                    "side": "in",
                    "quantity": "100",
                    "tx_id": "jup-alias-tx",
                },
                {
                    "timestamp_utc": "2025-06-12T08:49:25Z",
                    "source": "solana_rpc",
                    "asset": "JUPYIWRYJFSKUPIHA7HKER8VUTAEFOSYBKEDZNSDVCN",
                    "event_type": "token_transfer",
                    "side": "out",
                    "quantity": "150",
                    "tx_id": "jup-alias-tx",
                },
            ],
        )
    )

    resp = review_negative_balances(as_of="2025-06-12")
    assert resp.status == "success"
    assert resp.data["count"] == 1
    row = resp.data["rows"][0]
    assert row["issue_id"] == "negative_balance:2025-06-12:JUP"
    assert row["asset"] == "JUP"
    assert row["balance"] == "-50"
    assert row["event_counts"] == {"in": 1, "out": 1, "neutral": 0}

    context = review_issue_context("negative_balance:2025-06-12:JUP")
    assert context.status == "success"
    assert context.data["context"]["asset_yearly_totals"][0]["net_quantity"] == "-50"
    assert {item["asset"] for item in context.data["context"]["context_events"]} == {
        "JUP",
        "JUPYIWRYJFSKUPIHA7HKER8VUTAEFOSYBKEDZNSDVCN",
    }


def test_review_negative_balances_respects_tax_event_exclusions() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="negative_excluded.csv",
            rows=[
                {
                    "timestamp_utc": "2025-01-02T00:00:00Z",
                    "source": "blockpit",
                    "asset": "ADA",
                    "event_type": "auto-balancing out",
                    "side": "out",
                    "quantity": "11.67396699",
                },
                {
                    "timestamp_utc": "2025-01-03T00:00:00Z",
                    "source": "binance",
                    "asset": "ADA",
                    "event_type": "trade",
                    "side": "in",
                    "quantity": "10.6",
                },
            ],
        )
    )
    excluded_event_id = STORE.list_raw_events()[0]["unique_event_id"]

    before = review_negative_balances(as_of="2025-01-03", asset="ADA")
    assert before.status == "success"
    assert before.data["count"] == 1

    tax_event_override_upsert(
        TaxEventOverrideUpsertRequest(
            source_event_id=excluded_event_id,
            tax_category="EXCLUDED",
            reason_code="reference_import_only",
            note="Blockpit Auto-Balancing ist nur Referenzabgleich.",
        )
    )

    after = review_negative_balances(as_of="2025-01-03", asset="ADA")
    assert after.status == "success"
    assert after.data["count"] == 0


def test_review_issue_context_for_negative_balance_contract() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="negative_context.csv",
            rows=[
                {
                    "timestamp_utc": "2025-12-31T23:00:00Z",
                    "source": "binance",
                    "asset": "USDT",
                    "event_type": "trade",
                    "side": "out",
                    "quantity": "10",
                    "tx_id": "tx-context-1",
                },
                {
                    "timestamp_utc": "2025-12-31T23:00:00Z",
                    "source": "binance",
                    "asset": "SOL",
                    "event_type": "trade",
                    "side": "in",
                    "quantity": "0.1",
                    "tx_id": "tx-context-1",
                },
            ],
        )
    )

    resp = review_issue_context("negative_balance:2025-12-31:USDT")
    assert resp.status == "success"
    assert resp.data["issue"]["balance"] == "-10"
    context = resp.data["context"]
    assert context["scope"]["asset"] == "USDT"
    assert context["context_events"][0]["running_balance_after"] == "-10"
    assert {item["asset"] for item in context["same_transaction_events"]} == {"USDT", "SOL"}
    assert "recommended_api_actions" in context["analysis_contract"]["llm_should_return"]
    regulatory_context = context["regulatory_context"]
    assert regulatory_context["timeline"]["dac8_applies_from"] == "2026-01-01"
    assert regulatory_context["timeline"]["first_reporting_year"] == 2026
    assert regulatory_context["timeline"]["first_exchange_deadline_eu"] == "2027-09-30"
    assert regulatory_context["engine_policy"]["reporting_data_is_reference_only"] is True
    assert resp.data["api"]["set_status"] == "POST /api/v1/issues/update-status"


def test_regulatory_dac8_carf_context_contract() -> None:
    resp = regulatory_dac8_carf_context()
    assert resp.status == "success"
    context = resp.data["regulatory_context"]
    assert "DAC8" in context["framework"]
    assert "OECD-CARF" in context["framework"]
    assert "KStTG" in context["framework"]
    assert context["timeline"]["dac8_applies_from"] == "2026-01-01"
    assert context["timeline"]["first_reporting_year"] == 2026
    assert context["timeline"]["first_reporting_exchange_year"] == 2027
    assert context["timeline"]["first_exchange_deadline_eu"] == "2027-09-30"
    assert context["llm_guardrails"]["must_not_treat_carf_as_identical_to_crs"] is True
    assert context["engine_policy"]["no_tax_result_without_ruleset"] is True


def test_ai_review_analyze_persists_and_applies_safe_actions() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="ai_review_context.csv",
            rows=[
                {
                    "timestamp_utc": "2025-12-31T23:00:00Z",
                    "source": "binance",
                    "asset": "USDT",
                    "event_type": "trade",
                    "side": "out",
                    "quantity": "10",
                    "tx_id": "tx-ai-1",
                }
            ],
        )
    )

    issue_id = "negative_balance:2025-12-31:USDT"
    analyzed = ai_review_analyze(AiReviewAnalyzeRequest(issue_id=issue_id, persist=True))
    assert analyzed.status == "success"
    suggestion = analyzed.data["suggestion"]
    assert suggestion["issue_id"] == issue_id
    assert suggestion["priority"] in {"high", "medium", "low"}
    assert suggestion["recommended_api_actions"][0]["auto_apply_safe"] is True

    listed = ai_review_suggestions(issue_id=issue_id)
    assert listed.status == "success"
    assert listed.data["count"] == 1

    applied = ai_review_apply_suggestion(
        AiReviewApplySuggestionRequest(
            suggestion_id=suggestion["suggestion_id"],
            actions=["set_status", "comment_last_event"],
            note="Trockenlauf bestaetigt.",
        )
    )
    assert applied.status == "success"
    assert {item["action"] for item in applied.data["applied"]} == {"set_status", "comment_last_event"}
    after = review_negative_balances(as_of="2025-12-31")
    assert after.data["rows"][0]["status"] == "in_review"


def test_ai_review_analyze_ollama_engine_uses_validated_response(monkeypatch) -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="ai_review_ollama.csv",
            rows=[
                {
                    "timestamp_utc": "2025-12-31T23:00:00Z",
                    "source": "binance",
                    "asset": "USDT",
                    "event_type": "trade",
                    "side": "out",
                    "quantity": "10",
                    "tx_id": "tx-ai-ollama",
                }
            ],
        )
    )

    from tax_engine.api import review as review_api

    def _fake_ollama(context_payload, config):  # noqa: ANN001
        assert config.base_url
        assert context_payload["issue_id"] == "negative_balance:2025-12-31:USDT"
        return {
            "priority": "high",
            "confidence": "high",
            "probable_cause": "Ollama erkennt einen fehlenden USDT-Zufluss vor dem Out-Leg.",
            "evidence_event_ids": [context_payload["issue"]["last_event"]["source_event_id"]],
            "missing_data_questions": ["Fehlt ein Exchange-Import vor dem 31.12.2025?"],
            "recommended_api_actions": [
                {
                    "action": "set_status",
                    "method": "POST",
                    "path": "/api/v1/issues/update-status",
                    "body": {"status": "in_review"},
                    "auto_apply_safe": True,
                },
                {
                    "action": "unsafe_override",
                    "method": "POST",
                    "path": "/api/v1/tax/event-override/upsert",
                    "body": {},
                    "auto_apply_safe": True,
                },
            ],
            "risk_note": "Keine steuerwirksame Aktion automatisch anwenden.",
        }

    monkeypatch.setattr(review_api, "analyze_issue_with_ollama", _fake_ollama)
    analyzed = ai_review_analyze(
        AiReviewAnalyzeRequest(
            issue_id="negative_balance:2025-12-31:USDT",
            engine="ollama",
            persist=False,
        )
    )

    assert analyzed.status == "success"
    suggestion = analyzed.data["suggestion"]
    assert suggestion["engine"].startswith("ollama:")
    assert suggestion["confidence"] == "high"
    assert suggestion["probable_cause"].startswith("Ollama erkennt")
    assert all(
        action["path"] != "/api/v1/tax/event-override/upsert"
        for action in suggestion["recommended_api_actions"]
    )


def test_ai_review_analyze_ollama_regulatory_overclaim_falls_back(monkeypatch) -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="ai_review_regulatory_guardrail.csv",
            rows=[
                {
                    "timestamp_utc": "2025-07-01T12:00:00Z",
                    "source": "blockpit",
                    "asset": "USDT",
                    "event_type": "derivative loss",
                    "side": "out",
                    "quantity": "100",
                    "tx_id": "tx-ai-guardrail",
                }
            ],
        )
    )

    from tax_engine.api import review as review_api

    def _fake_ollama(context_payload, config):  # noqa: ANN001, ARG001
        return {
            "priority": "high",
            "confidence": "high",
            "probable_cause": "Negative balance indicates a potential regulatory violation.",
            "evidence_event_ids": [context_payload["issue"]["last_event"]["source_event_id"]],
            "missing_data_questions": ["Is there a regulatory requirement to report this loss?"],
            "recommended_api_actions": [],
            "risk_note": "Potential violation of DAC8 reporting rules.",
        }

    monkeypatch.setattr(review_api, "analyze_issue_with_ollama", _fake_ollama)
    analyzed = ai_review_analyze(
        AiReviewAnalyzeRequest(
            issue_id="negative_balance:2025-07-01:USDT",
            engine="ollama",
            persist=False,
        )
    )

    assert analyzed.status == "success"
    assert analyzed.data["suggestion"]["engine"] == "deterministic-v1"
    assert analyzed.warnings[0]["code"] == "ollama_review_fallback"
    assert "ollama_regulatory_guardrail" in analyzed.warnings[0]["message"]


def test_ai_review_analyze_ollama_classifier_keeps_safe_actions(monkeypatch) -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="ai_review_classifier.csv",
            rows=[
                {
                    "timestamp_utc": "2025-02-01T12:00:00Z",
                    "source": "blockpit",
                    "asset": "JUP",
                    "event_type": "trade",
                    "side": "out",
                    "quantity": "100",
                    "tx_id": "tx-ai-classifier",
                }
            ],
        )
    )

    from tax_engine.api import review as review_api

    def _fake_classify(context_payload, config):  # noqa: ANN001
        assert config.base_url
        return {
            "cause_category": "duplicate_reference",
            "confidence": "high",
            "evidence_event_ids": [context_payload["issue"]["last_event"]["source_event_id"]],
            "rationale": "Blockpit-Referenzdaten dominieren den Stichtagsbefund.",
            "missing_data_questions": ["Ist Blockpit fuer diesen Zeitraum nur Referenzquelle?"],
        }

    monkeypatch.setattr(review_api, "classify_issue_with_ollama", _fake_classify)
    analyzed = ai_review_analyze(
        AiReviewAnalyzeRequest(
            issue_id="negative_balance:2025-02-01:JUP",
            engine="ollama-classifier",
            persist=False,
        )
    )

    assert analyzed.status == "success"
    suggestion = analyzed.data["suggestion"]
    assert suggestion["engine"].startswith("ollama-classifier:")
    assert suggestion["classification"]["cause_category"] == "duplicate_reference"
    assert suggestion["confidence"] == "high"
    assert suggestion["recommended_api_actions"][0]["action"] == "set_status"
    assert all(action["path"] != "/api/v1/tax/event-override/upsert" for action in suggestion["recommended_api_actions"])


def test_ai_review_analyze_ollama_classifier_guardrail_falls_back(monkeypatch) -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="ai_review_classifier_guardrail.csv",
            rows=[
                {
                    "timestamp_utc": "2025-07-01T12:00:00Z",
                    "source": "blockpit",
                    "asset": "USDT",
                    "event_type": "derivative loss",
                    "side": "out",
                    "quantity": "100",
                    "tx_id": "tx-ai-classifier-guardrail",
                }
            ],
        )
    )

    from tax_engine.api import review as review_api

    def _fake_classify(context_payload, config):  # noqa: ANN001, ARG001
        return {
            "cause_category": "derivative_or_fee_context",
            "confidence": "high",
            "evidence_event_ids": [context_payload["issue"]["last_event"]["source_event_id"]],
            "rationale": "Potential regulatory violation of DAC8.",
            "missing_data_questions": [],
        }

    monkeypatch.setattr(review_api, "classify_issue_with_ollama", _fake_classify)
    analyzed = ai_review_analyze(
        AiReviewAnalyzeRequest(
            issue_id="negative_balance:2025-07-01:USDT",
            engine="ollama-classifier",
            persist=False,
        )
    )

    assert analyzed.status == "success"
    assert analyzed.data["suggestion"]["engine"] == "deterministic-v1"
    assert analyzed.warnings[0]["code"] == "ollama_classification_fallback"
    assert "ollama_regulatory_guardrail" in analyzed.warnings[0]["message"]


def test_ai_review_analyze_llama_cpp_classifier_keeps_safe_actions(monkeypatch) -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="ai_review_llama_cpp_classifier.csv",
            rows=[
                {
                    "timestamp_utc": "2025-02-01T12:00:00Z",
                    "source": "blockpit",
                    "asset": "JUP",
                    "event_type": "trade",
                    "side": "out",
                    "quantity": "100",
                    "tx_id": "tx-ai-llama-cpp-classifier",
                }
            ],
        )
    )

    from tax_engine.api import review as review_api

    def _fake_classify(context_payload, config):  # noqa: ANN001
        assert config.base_url
        assert config.max_tokens >= 128
        return {
            "cause_category": "missing_inflow",
            "confidence": "high",
            "evidence_event_ids": [context_payload["issue"]["last_event"]["source_event_id"]],
            "rationale": "Es fehlt ein vorheriger Zufluss im Kontextfenster.",
            "missing_data_questions": ["Gibt es einen externen Wallet-Import?"],
        }

    monkeypatch.setattr(review_api, "classify_issue_with_openai_compatible", _fake_classify)
    analyzed = ai_review_analyze(
        AiReviewAnalyzeRequest(
            issue_id="negative_balance:2025-02-01:JUP",
            engine="llama-cpp-classifier",
            persist=False,
        )
    )

    assert analyzed.status == "success"
    suggestion = analyzed.data["suggestion"]
    assert suggestion["engine"].startswith("llama-cpp-classifier:")
    assert suggestion["classification"]["cause_category"] == "missing_inflow"
    assert suggestion["recommended_api_actions"][0]["action"] == "set_status"
    assert all(action["path"] != "/api/v1/tax/event-override/upsert" for action in suggestion["recommended_api_actions"])


def test_review_timezone_correction_closes_timezone_issue_and_is_applied() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="timezone.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00",
                    "asset": "BTC",
                    "event_type": "trade",
                    "side": "buy",
                    "amount": "0.1",
                    "price_eur": "100",
                }
            ],
        )
    )
    inbox = issues_inbox()
    issue = next(item for item in inbox.data.get("issues", []) if item.get("type") == "timezone_conflict")
    event_id = str(issue["source_event_id"])

    corrected = review_timezone_correct(
        ReviewTimezoneCorrectRequest(
            source_event_id=event_id,
            corrected_timestamp_utc="2026-01-01T11:00:00Z",
            reason_code="source_timezone_cet",
            note="Importquelle war CET, nicht UTC.",
        )
    )
    assert corrected.status == "success"

    inbox_after = issues_inbox()
    assert not any(
        str(item.get("type")) == "timezone_conflict" and str(item.get("source_event_id")) == event_id
        for item in inbox_after.data.get("issues", [])
    )

    from tax_engine.queue import apply_review_actions

    adjusted, summary = apply_review_actions(STORE.list_raw_events())
    assert summary["timezone_correction_count"] == 1
    assert adjusted[0]["payload"]["timestamp_utc"] == "2026-01-01T11:00:00+00:00"
    assert adjusted[0]["payload"]["review_action"] == "timezone_correct"


def test_review_merge_and_split_actions_are_persisted_without_raw_delete() -> None:
    _reset_store()
    import_confirm(
        ConfirmImportRequest(
            source_name="merge_split.csv",
            rows=[
                {
                    "timestamp_utc": "2026-01-01T12:00:00Z",
                    "asset": "SOL",
                    "event_type": "swap_out_aggregated",
                    "side": "sell",
                    "amount": "1",
                    "price_eur": "10",
                },
                {
                    "timestamp_utc": "2026-01-01T12:00:01Z",
                    "asset": "USDC",
                    "event_type": "swap_in_aggregated",
                    "side": "buy",
                    "amount": "10",
                    "price_eur": "1",
                },
            ],
        )
    )
    event_ids = [str(item["unique_event_id"]) for item in STORE.list_raw_events()]

    merge = review_merge(
        ReviewMergeRequest(
            source_event_ids=event_ids,
            reason_code="same_economic_event",
            note="Jupiter Multi-Hop als ein wirtschaftlicher Swap.",
        )
    )
    assert merge.status == "success"

    split = review_split(
        ReviewSplitRequest(
            source_event_id=event_ids[0],
            split_rows=[{"asset": "SOL", "quantity": "0.5"}, {"asset": "SOL", "quantity": "0.5"}],
            reason_code="bundled_event_split",
            note="Teilvorgaenge fuer Review dokumentiert.",
        )
    )
    assert split.status == "success"
    assert len(STORE.list_raw_events()) == 2

    actions = review_actions()
    action_types = {str(item.get("action_type")) for item in actions.data.get("rows", [])}
    assert {"merge", "split"}.issubset(action_types)

    from tax_engine.queue import apply_review_actions

    adjusted, summary = apply_review_actions(STORE.list_raw_events())
    assert len(STORE.list_raw_events()) == 2
    assert summary["merge_annotation_count"] == 1
    assert summary["split_replacement_count"] == 2
    split_rows = [item for item in adjusted if ":split:" in str(item["unique_event_id"])]
    assert [row["payload"]["amount"] for row in split_rows] == ["0.5", "0.5"]
    assert split_rows[0]["payload"]["review_action_parent_event_id"] == event_ids[0]
    merged_rows = [item for item in adjusted if item["payload"].get("economic_event_id")]
    assert len(merged_rows) == 1


def test_balance_adjustment_candidate_decision_is_review_only() -> None:
    _reset_store()
    upsert = balance_adjustment_candidate_upsert(
        BalanceAdjustmentCandidateUpsertRequest(
            candidate_id="pionex-usdt-opening-balance-test",
            platform="pionex",
            asset="USDT",
            quantity_delta="1643.23",
            effective_timestamp_utc="2021-12-28T00:49:11+00:00",
            adjustment_type="opening_balance_candidate",
            status="ready_for_explicit_review_decision",
            reason_code="missing_pionex_bot_start_capital",
            note="Review-only test candidate for Pionex opening balance documentation.",
            evidence={"report": "docs/example.md"},
        )
    )
    assert upsert.status == "success"
    assert upsert.data["tax_effective"] is False

    decision = balance_adjustment_candidate_decide(
        BalanceAdjustmentCandidateDecisionRequest(
            candidate_id="pionex-usdt-opening-balance-test",
            decision="approve_non_tax_inventory_normalization",
            reviewer="unit-test",
            note="Explicitly approved as non-tax inventory normalization for test coverage.",
            evidence={"decision_report": "docs/example.md"},
        )
    )

    assert decision.status == "success"
    assert decision.data["status"] == "approved_non_tax_inventory_normalization"
    assert decision.data["tax_effective"] is False
    assert decision.data["review_decision"]["decision"] == "approve_non_tax_inventory_normalization"
    assert decision.warnings[0]["code"] == "not_tax_effective"

    listed = balance_adjustment_candidates_list()
    row = listed.data["rows"][0]
    assert row["status"] == "approved_non_tax_inventory_normalization"
    assert row["tax_effective"] is False


def test_balance_adjustment_candidate_decision_preview_is_read_only() -> None:
    _reset_store()
    upsert = balance_adjustment_candidate_upsert(
        BalanceAdjustmentCandidateUpsertRequest(
            candidate_id="pionex-usdt-opening-balance-preview",
            platform="pionex",
            asset="USDT",
            quantity_delta="1643.2312211162",
            effective_timestamp_utc="2021-12-28T00:49:11+00:00",
            adjustment_type="opening_balance_candidate",
            status="needs_evidence",
            reason_code="missing_pionex_bot_start_capital",
            note="Needs primary Pionex evidence or explicit non-tax review decision.",
            evidence={"report": "docs/167_PIONEX_USDT_FINAL_BLOCKER_AUDIT_2026-05-09.md"},
        )
    )
    assert upsert.status == "success"

    preview = balance_adjustment_candidate_decision_preview("pionex-usdt-opening-balance-preview")

    assert preview.status == "success"
    assert preview.data["candidate"]["candidate_id"] == "pionex-usdt-opening-balance-preview"
    assert preview.data["current_gate_effect"]["blocks_final_export"] is True
    assert preview.data["approval_payload_template"]["decision"] == "approve_non_tax_inventory_normalization"
    assert preview.data["approval_payload_template"]["evidence"]["evidence_package"].endswith("172_PIONEX_EVIDENCE_REQUEST_PACKAGE_2026-05-09.md")

    listed = balance_adjustment_candidates_list()
    assert listed.data["rows"][0]["status"] == "needs_evidence"


def test_pionex_balance_adjustment_candidate_evidence_package_builds_zip() -> None:
    _reset_store()
    upsert = balance_adjustment_candidate_upsert(
        BalanceAdjustmentCandidateUpsertRequest(
            candidate_id="pionex-usdt-opening-balance-2021-12-28",
            platform="pionex",
            asset="USDT",
            quantity_delta="197.8470311162",
            effective_timestamp_utc="2021-12-28T00:49:11+00:00",
            adjustment_type="opening_balance_candidate",
            status="needs_evidence",
            reason_code="missing_pionex_bot_start_capital",
            note="Needs primary Pionex evidence or explicit non-tax review decision.",
            evidence={"report": "docs/167_PIONEX_USDT_FINAL_BLOCKER_AUDIT_2026-05-09.md"},
        )
    )
    assert upsert.status == "success"

    package = balance_adjustment_candidate_evidence_package("pionex-usdt-opening-balance-2021-12-28")

    assert package.status == "success"
    assert package.data["candidate_id"] == "pionex-usdt-opening-balance-2021-12-28"
    assert package.data["zip_file"]["path"].endswith("pionex_support_package_2026-05-09.zip")
    assert package.data["zip_file"]["exists"] is True
    assert package.data["zip_file"]["size_bytes"] > 0
    assert "Pionex" in package.data["support_request_en"]
    assert package.data["known_transfer_count"] >= 1
    assert any(item["key"] == "support_request_en" and item["exists"] for item in package.data["files"])
