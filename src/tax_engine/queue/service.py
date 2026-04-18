from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from tax_engine.core.derivatives import process_derivatives_for_year
from tax_engine.core.processor import process_events_for_year
from tax_engine.ingestion.store import STORE
from tax_engine.integrity import config_fingerprint

from .models import ProcessRunRequest


def create_processing_job(payload: ProcessRunRequest) -> dict[str, Any]:
    job_id = str(uuid4())
    cfg_hash = config_fingerprint(
        {
            "tax_year": payload.tax_year,
            "ruleset_id": payload.ruleset_id,
            "dry_run": payload.dry_run,
            "config": payload.config,
        }
    )
    STORE.create_processing_job(
        job_id=job_id,
        tax_year=payload.tax_year,
        ruleset_id=payload.ruleset_id,
        config_hash=cfg_hash,
        status="queued",
        progress=0,
    )
    job = STORE.get_processing_job(job_id)
    if job is None:
        raise RuntimeError("Job creation failed unexpectedly")
    return job


def get_processing_job(job_id: str) -> dict[str, Any] | None:
    return STORE.get_processing_job(job_id)


def run_next_queued_job(simulate_fail: bool = False) -> dict[str, Any] | None:
    claimed = STORE.claim_next_queued_job()
    if claimed is None:
        return None

    job_id = claimed["job_id"]
    try:
        STORE.update_processing_job_state(
            job_id=job_id,
            status="running",
            progress=35,
            current_step="load_events",
        )
        raw_events = STORE.list_raw_events()

        STORE.update_processing_job_state(
            job_id=job_id,
            status="running",
            progress=70,
            current_step="core_processing",
        )
        processing_result = process_events_for_year(raw_events=raw_events, tax_year=claimed["tax_year"])
        tax_lines = processing_result.pop("tax_lines")
        derivative_result = process_derivatives_for_year(raw_events=raw_events, tax_year=claimed["tax_year"])
        derivative_lines = derivative_result.pop("lines")

        if simulate_fail:
            raise RuntimeError("Simulated worker error")

        STORE.replace_tax_lines(job_id=job_id, tax_lines=tax_lines)
        STORE.replace_derivative_lines(job_id=job_id, derivative_lines=derivative_lines)
        processing_result["derivatives"] = derivative_result

        STORE.update_processing_job_state(
            job_id=job_id,
            status="completed",
            progress=100,
            current_step="completed",
            error_message=None,
            result_json=json.dumps(processing_result, sort_keys=True, separators=(",", ":")),
        )
    except Exception as exc:
        STORE.update_processing_job_state(
            job_id=job_id,
            status="failed",
            progress=70,
            current_step="failed",
            error_message=str(exc),
            result_json=None,
        )

    return STORE.get_processing_job(job_id)
