from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from tax_engine.api.processing import _current_draft_notice, process_run, process_worker_run_next
from tax_engine.api.reporting import build_csv_from_rows, build_export_rows, build_wiso_tax_csv
from tax_engine.api.review import issues_inbox, review_gates
from tax_engine.ingestion.store import STORE
from tax_engine.queue.models import ProcessRunRequest, WorkerRunNextRequest

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-05-10"
YEARS = range(2020, 2027)
JOBS_JSONL = ROOT / "var" / f"current_tax_jobs_{RUN_DATE}.jsonl"
SUMMARY_JSON = ROOT / "var" / f"current_tax_summary_{RUN_DATE}.json"
GATE_JSON = ROOT / "var" / f"review_gate_snapshot_{RUN_DATE}.json"
EXPORT_DIR = ROOT / "var" / f"report_exports_current_{RUN_DATE}"
DOC_PATH = ROOT / "docs" / f"190_CURRENT_TAX_RUNS_{RUN_DATE}.md"


def _dec(value: Any) -> Decimal:
    return Decimal(str(value or "0"))


def _plain(value: Any) -> str:
    value_dec = _dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _job_summary(job: dict[str, Any]) -> dict[str, Any]:
    summary = job.get("result_summary") or {}
    domain = summary.get("tax_domain_summary") or {}
    anlage = domain.get("anlage_so") or {}
    euer = domain.get("euer") or {}
    derivatives = domain.get("termingeschaefte") or {}
    classification = domain.get("classification_counts") or {}
    return {
        "tax_year": int(job.get("tax_year") or 0),
        "job_id": str(job.get("job_id") or ""),
        "status": str(job.get("status") or ""),
        "tax_line_count": int(job.get("tax_line_count") or 0),
        "derivative_line_count": int(job.get("derivative_line_count") or 0),
        "processed_events": int(summary.get("processed_events") or 0),
        "short_sell_violations": int(summary.get("short_sell_violations") or 0),
        "private_veraeusserung_net_taxable_eur": _plain(anlage.get("private_veraeusserung_net_taxable_eur")),
        "leistungen_income_eur": _plain(anlage.get("leistungen_income_eur")),
        "euer_mining_reward_income_eur": _plain(euer.get("betriebseinnahmen_mining_staking_eur")),
        "euer_business_disposal_net_eur": _plain(euer.get("business_disposal_net_eur")),
        "euer_business_result_eur": _plain(euer.get("betriebsergebnis_eur")),
        "termingeschaefte_netto_eur": _plain(derivatives.get("netto_eur")),
        "termingeschaefte_verlust_summe_abs_eur": _plain(derivatives.get("verlust_summe_abs_eur")),
        "unresolved_valuation_events": int(classification.get("unresolved_valuation_events") or 0),
        "report_integrity_id": str(summary.get("report_integrity_id") or ""),
        "ruleset_id": str(summary.get("ruleset_id") or job.get("ruleset_id") or ""),
        "ruleset_version": str(summary.get("ruleset_version") or job.get("ruleset_version") or ""),
    }


def _export_job(job: dict[str, Any]) -> dict[str, str]:
    job_id = str(job.get("job_id") or "")
    year = int(job.get("tax_year") or 0)
    tax_lines = STORE.get_tax_lines(job_id)
    derivative_lines = STORE.get_derivative_lines(job_id)
    integrity = STORE.get_report_integrity(job_id)
    draft_notice = _current_draft_notice()
    export_rows = build_export_rows(
        job,
        tax_lines,
        derivative_lines,
        include_derivatives=True,
        include_summary=True,
        integrity=integrity,
        draft_notice=draft_notice,
    )
    out_dir = EXPORT_DIR / f"{year}_{job_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    all_json = out_dir / "all.json"
    tax_csv = out_dir / "tax.csv"
    wiso_csv = out_dir / "wiso.csv"
    _write_json(all_json, {"job": job, "integrity": integrity, "draft_notice": draft_notice, "rows": export_rows})
    tax_csv.write_text(build_csv_from_rows(export_rows), encoding="utf-8")
    wiso_csv.write_text(build_wiso_tax_csv(job, tax_lines, draft_notice=draft_notice), encoding="utf-8")
    result = {"all_json": str(all_json), "tax_csv": str(tax_csv), "wiso_csv": str(wiso_csv)}
    if derivative_lines:
        derivative_csv = out_dir / "derivatives.csv"
        derivative_rows = build_export_rows(
            job,
            [],
            derivative_lines,
            include_derivatives=True,
            include_summary=False,
            integrity=integrity,
            draft_notice=None,
        )
        derivative_csv.write_text(build_csv_from_rows(derivative_rows), encoding="utf-8")
        result["derivatives_csv"] = str(derivative_csv)
    return result


def _write_doc(payload: dict[str, Any]) -> None:
    gate = payload["gate"]
    lines = [
        f"# Current Tax Runs - {RUN_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Neu berechnete Steuerjahre: `{payload['year_count']}`",
        f"- Gesamt Tax Lines: `{payload['totals']['tax_line_count']}`",
        f"- Gesamt Derivative Lines: `{payload['totals']['derivative_line_count']}`",
        f"- Review-Gate `allow_export`: `{gate.get('allow_export')}`",
        f"- Issues offen: `{(gate.get('counts') or {}).get('issues_open', 0)}`",
        f"- High-Issues offen: `{(gate.get('counts') or {}).get('issues_high_open', 0)}`",
        "",
        "## Jahresübersicht",
        "",
        "| Jahr | Job | Tax Lines | Derivate | Anlage SO netto EUR | §22 Leistungen EUR | EÜR Mining/Reward EUR | EÜR Veräußerung BV netto EUR | EÜR Ergebnis EUR | Termingeschäfte netto EUR | Derivate Verlustsumme EUR | Valuation offen | Short-Sell-Hinweise |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["jobs"]:
        lines.append(
            "| {tax_year} | `{job_id}` | {tax_line_count} | {derivative_line_count} | {private_veraeusserung_net_taxable_eur} | {leistungen_income_eur} | {euer_mining_reward_income_eur} | {euer_business_disposal_net_eur} | {euer_business_result_eur} | {termingeschaefte_netto_eur} | {termingeschaefte_verlust_summe_abs_eur} | {unresolved_valuation_events} | {short_sell_violations} |".format(
                **row
            )
        )
    lines.extend(["", "## Offene Issues", ""])
    for item in payload["issues"]:
        lines.append(
            f"- `{item.get('issue_id')}`: `{item.get('severity')}` / `{item.get('status')}` / "
            f"`{item.get('asset')}` - {item.get('detail')}"
        )
    lines.extend(["", "## Exportdateien", ""])
    lines.append(f"- Verzeichnis: `{EXPORT_DIR}`")
    lines.append("- Je Jahr: `all.json`, `tax.csv`, `wiso.csv`; bei Derivaten zusätzlich `derivatives.csv`.")
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    JOBS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    jobs: list[dict[str, Any]] = []
    with JOBS_JSONL.open("w", encoding="utf-8") as fh:
        for year in YEARS:
            created = process_run(ProcessRunRequest(tax_year=year, ruleset_id=f"DE-{year}-v1.0", config={}))
            if created.status != "success":
                raise RuntimeError(f"process_run failed for {year}: {created.errors}")
            worked = process_worker_run_next(WorkerRunNextRequest(simulate_fail=False))
            if worked.status != "success" or worked.data.get("status") != "completed":
                raise RuntimeError(f"worker failed for {year}: {worked.errors or worked.data}")
            job = worked.data
            export_paths = _export_job(job)
            row = {"created": created.data, "worker": worked.data, "exports": export_paths}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            jobs.append({**_job_summary(job), "exports": export_paths})
            print(json.dumps({"tax_year": year, "job_id": job.get("job_id"), "status": job.get("status")}, ensure_ascii=False))

    gate_resp = review_gates()
    gate = gate_resp.data if gate_resp.status == "success" else {"errors": gate_resp.errors}
    issues_resp = issues_inbox()
    issues = issues_resp.data.get("issues", []) if issues_resp.status == "success" else []
    _write_json(GATE_JSON, gate_resp.model_dump())
    payload = {
        "run_date": RUN_DATE,
        "year_count": len(jobs),
        "jobs": jobs,
        "totals": {
            "tax_line_count": sum(item["tax_line_count"] for item in jobs),
            "derivative_line_count": sum(item["derivative_line_count"] for item in jobs),
            "processed_events": sum(item["processed_events"] for item in jobs),
        },
        "gate": gate,
        "issues": issues,
    }
    _write_json(SUMMARY_JSON, payload)
    _write_doc(payload)
    print(json.dumps({"summary": str(SUMMARY_JSON), "doc": str(DOC_PATH), "exports": str(EXPORT_DIR)}, indent=2))


if __name__ == "__main__":
    main()
