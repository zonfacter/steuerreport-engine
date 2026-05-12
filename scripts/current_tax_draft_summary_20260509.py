from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-05-09"
JOBS_JSONL = ROOT / "var" / f"current_tax_draft_jobs_{RUN_DATE}.jsonl"


def _dec(value: Any) -> Decimal:
    return Decimal(str(value or "0"))


def _plain(value: Any) -> str:
    dec = _dec(value)
    text = format(dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _read_jobs() -> list[dict[str, Any]]:
    rows_by_year: dict[int, dict[str, Any]] = {}
    for line in JOBS_JSONL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        data = payload["worker"]["data"]
        summary = data.get("result_summary") or {}
        domain = summary.get("tax_domain_summary") or {}
        anlage = domain.get("anlage_so") or {}
        derivatives = domain.get("termingeschaefte") or {}
        classification = domain.get("classification_counts") or {}
        row = (
            {
                "tax_year": int(data["tax_year"]),
                "job_id": data["job_id"],
                "status": data["status"],
                "tax_line_count": int(data.get("tax_line_count") or 0),
                "derivative_line_count": int(data.get("derivative_line_count") or 0),
                "processed_events": int(summary.get("processed_events") or 0),
                "short_sell_violations": int(summary.get("short_sell_violations") or 0),
                "private_veraeusserung_net_taxable_eur": _plain(
                    anlage.get("private_veraeusserung_net_taxable_eur")
                ),
                "leistungen_income_eur": _plain(anlage.get("leistungen_income_eur")),
                "termingeschaefte_netto_eur": _plain(derivatives.get("netto_eur")),
                "termingeschaefte_verlust_summe_abs_eur": _plain(derivatives.get("verlust_summe_abs_eur")),
                "unresolved_valuation_events": int(classification.get("unresolved_valuation_events") or 0),
                "report_integrity_id": summary.get("report_integrity_id", ""),
                "ruleset_id": summary.get("ruleset_id", data.get("ruleset_id", "")),
                "ruleset_version": summary.get("ruleset_version", data.get("ruleset_version", "")),
            }
        )
        rows_by_year[row["tax_year"]] = row
    return sorted(rows_by_year.values(), key=lambda item: item["tax_year"])


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_doc(path: Path, payload: dict[str, Any]) -> None:
    final_allowed = bool(payload["gate"]["allow_export"])
    status_label = "Current Tax Runs" if final_allowed else "Current Tax Draft Runs"
    export_note = (
        "Die Laeufe sind nach aktuellem Review-Gate final exportfaehig. Alte Pionex-USDT-Kontextluecke ist "
        "als nicht steuerwirksame Bestandsnormalisierung dokumentiert und freigegeben."
        if final_allowed
        else "Die Laeufe sind aktuelle Draft-Arbeitslaeufe. Wegen offenem Review-Gate duerfen sie nicht als final sauber markiert werden."
    )
    wiso_note = (
        "- WISO-CSV ist nach aktuellem Review-Gate final exportfaehig."
        if final_allowed
        else "- WISO-CSV ist verfuegbar, aber wegen offenem Gate nur als Entwurf zu behandeln."
    )
    lines = [
        f"# {status_label} - {RUN_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Neu berechnete Steuerjahre: `{payload['year_count']}`",
        f"- Gesamt Tax Lines: `{payload['totals']['tax_line_count']}`",
        f"- Gesamt Derivative Lines: `{payload['totals']['derivative_line_count']}`",
        f"- Export-Gate: `{payload['gate']['allow_export']}`",
        f"- Offene Balance-Review-Kandidaten: `{payload['gate']['balance_adjustment_candidates_open']}`",
        "",
        export_note,
        "",
        "## Jahresuebersicht",
        "",
        "| Jahr | Job | Tax Lines | Derivate | Anlage SO netto EUR | Leistungen EUR | Termingeschaefte netto EUR | Derivate Verlustsumme EUR | Valuation offen | Short-Sell-Hinweise |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["jobs"]:
        lines.append(
            "| {tax_year} | `{job_id}` | {tax_line_count} | {derivative_line_count} | {private_veraeusserung_net_taxable_eur} | {leistungen_income_eur} | {termingeschaefte_netto_eur} | {termingeschaefte_verlust_summe_abs_eur} | {unresolved_valuation_events} | {short_sell_violations} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Offene Gate-Blocker",
            "",
        ]
    )
    for item in payload["gate"]["blocking_reasons"]:
        lines.append(f"- `{item.get('code', '')}`: {item.get('message', '')}")
    lines.extend(
        [
            "",
            "## Offene Balance-Kandidaten",
            "",
        ]
    )
    for item in payload["gate"]["balance_adjustment_candidates"]:
        decision = item.get("review_decision") or {}
        lines.append(
            f"- `{item.get('candidate_id')}`: `{item.get('platform')}/{item.get('asset')}` "
            f"`{item.get('quantity_delta')}`, status `{item.get('status')}`, "
            f"tax_effective `{item.get('tax_effective')}`, Entscheidung `{decision.get('decision', '')}`."
        )
    lines.extend(
        [
            "",
            "## Export-Hinweis",
            "",
            "- Exportdateien koennen ueber `GET /api/v1/report/files/{job_id}` gelistet werden.",
            "- Einzelne Downloads laufen ueber `/api/v1/report/export?job_id=<job>&scope=<all|tax|derivatives>&fmt=<json|csv|pdf|wiso>`.",
            wiso_note,
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    jobs = _read_jobs()
    gate_path = ROOT / "var" / f"review_gate_snapshot_{RUN_DATE}.json"
    gate_raw = json.loads(gate_path.read_text(encoding="utf-8")) if gate_path.exists() else {}
    gate = gate_raw.get("data", gate_raw) if isinstance(gate_raw, dict) else {}
    totals = {
        "tax_line_count": sum(item["tax_line_count"] for item in jobs),
        "derivative_line_count": sum(item["derivative_line_count"] for item in jobs),
        "processed_events": sum(item["processed_events"] for item in jobs),
    }
    payload = {
        "run_date": RUN_DATE,
        "year_count": len(jobs),
        "jobs": jobs,
        "totals": totals,
        "gate": {
            "allow_export": bool(gate.get("allow_export", False)),
            "blocking_reasons": gate.get("blocking_reasons", []),
            "warning_reasons": gate.get("warning_reasons", []),
            "balance_adjustment_candidates_open": (gate.get("counts") or {}).get(
                "balance_adjustment_candidates_open", 0
            ),
            "balance_adjustment_candidates": gate.get("balance_adjustment_candidates", []),
        },
    }
    json_path = ROOT / "var" / f"current_tax_draft_summary_{RUN_DATE}.json"
    doc_path = ROOT / "docs" / f"168_CURRENT_TAX_DRAFT_RUNS_{RUN_DATE}.md"
    _write_json(json_path, payload)
    _write_doc(doc_path, payload)
    print(json.dumps({"json": str(json_path), "doc": str(doc_path), "year_count": len(jobs)}, indent=2))


if __name__ == "__main__":
    main()
