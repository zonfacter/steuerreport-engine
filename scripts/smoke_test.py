#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from tax_engine.api.app import (
    import_confirm,
    process_run,
    process_status,
    process_worker_run_next,
    reconcile_auto_match,
    review_unmatched,
)
from tax_engine.ingestion.models import ConfirmImportRequest
from tax_engine.ingestion.store import STORE
from tax_engine.queue.models import ProcessRunRequest, WorkerRunNextRequest
from tax_engine.reconciliation.models import AutoMatchRequest


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _print_step(name: str, payload: dict[str, Any]) -> None:
    print(f"\n=== {name} ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    STORE.reset_for_tests()

    imported = import_confirm(
        ConfirmImportRequest(
            source_name="smoke.csv",
            rows=[
                {
                    "timestamp": "2026-01-01T12:00:00Z",
                    "asset": "SOL",
                    "event_type": "withdrawal",
                    "amount": "10.00",
                },
                {
                    "timestamp": "2026-01-01T12:03:00Z",
                    "asset": "SOL",
                    "event_type": "deposit",
                    "amount": "9.99",
                },
                {
                    "timestamp": "2026-02-01T12:00:00Z",
                    "asset": "BTC",
                    "side": "buy",
                    "amount": "1",
                    "price_eur": "100",
                    "fee_eur": "1",
                },
                {
                    "timestamp": "2026-02-10T12:00:00Z",
                    "asset": "BTC",
                    "side": "sell",
                    "amount": "0.4",
                    "price_eur": "125",
                    "fee_eur": "0.5",
                },
                {
                    "timestamp": "2026-03-01T12:00:00Z",
                    "position_id": "drv-1",
                    "asset": "ETH",
                    "event_type": "derivative_open",
                    "collateral_eur": "300",
                    "fee_eur": "2",
                },
                {
                    "timestamp": "2026-03-05T12:00:00Z",
                    "position_id": "drv-1",
                    "asset": "ETH",
                    "event_type": "liquidation",
                    "fee_eur": "1",
                    "negative_equity_eur": "10",
                },
            ],
        )
    )
    _assert(imported.status == "success", "import_confirm failed")
    _print_step("import_confirm", imported.model_dump())

    auto_match = reconcile_auto_match(AutoMatchRequest())
    _assert(auto_match.status == "success", "reconcile_auto_match failed")
    _print_step("reconcile_auto_match", auto_match.model_dump())

    unmatched = review_unmatched()
    _assert(unmatched.status == "success", "review_unmatched failed")
    _print_step("review_unmatched", unmatched.model_dump())

    created = process_run(ProcessRunRequest(tax_year=2026, ruleset_id="DE-2026-v1.0", config={}))
    _assert(created.status == "success", "process_run failed")
    job_id = str(created.data["job_id"])
    _print_step("process_run", created.model_dump())

    worked = process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
    _assert(worked.status == "success", "process_worker_run_next failed")
    _print_step("process_worker_run_next", worked.model_dump())

    status = process_status(job_id)
    _assert(status.status == "success", "process_status failed")
    _assert(status.data.get("status") == "completed", "job not completed")
    _assert(int(status.data.get("tax_line_count", 0)) >= 1, "no tax lines generated")
    _assert(int(status.data.get("derivative_line_count", 0)) >= 1, "no derivative lines generated")
    _print_step("process_status", status.model_dump())

    print("\nSMOKE TEST: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

