from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from tax_engine.admin import put_admin_setting
from tax_engine.ingestion.store import STORE


@dataclass(frozen=True)
class WisoReference:
    year: int
    path: str
    row_count: int
    par22nr3_eur: Decimal
    proceeds_eur: Decimal
    cost_basis_eur: Decimal
    gain_loss_eur: Decimal
    short_gain_loss_eur: Decimal
    long_gain_loss_eur: Decimal
    short_rows: int
    long_rows: int


def _parse_decimal(value: Any) -> Decimal:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return Decimal("0")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def _parse_metadata(line: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in line.strip().split(","):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def _read_wiso_csv(path: Path) -> WisoReference:
    with path.open("r", encoding="ascii", newline="") as handle:
        first_line = handle.readline()
        metadata = _parse_metadata(first_line)
        reader = csv.DictReader(handle)
        row_count = 0
        proceeds = Decimal("0")
        cost_basis = Decimal("0")
        gain_loss = Decimal("0")
        short_gain_loss = Decimal("0")
        long_gain_loss = Decimal("0")
        short_rows = 0
        long_rows = 0
        for row in reader:
            row_count += 1
            proceeds += _parse_decimal(row.get("Proceeds"))
            cost_basis += _parse_decimal(row.get("Cost Basis"))
            row_gain_loss = _parse_decimal(row.get("Gain / Loss"))
            gain_loss += row_gain_loss
            holding = str(row.get("Short / Long") or "").strip().lower()
            if holding == "short":
                short_rows += 1
                short_gain_loss += row_gain_loss
            elif holding == "long":
                long_rows += 1
                long_gain_loss += row_gain_loss

    year_raw = metadata.get("Tax_Year") or _infer_year_from_name(path.name)
    return WisoReference(
        year=int(year_raw),
        path=str(path),
        row_count=row_count,
        par22nr3_eur=_parse_decimal(metadata.get("Par22Nr3")),
        proceeds_eur=proceeds,
        cost_basis_eur=cost_basis,
        gain_loss_eur=gain_loss,
        short_gain_loss_eur=short_gain_loss,
        long_gain_loss_eur=long_gain_loss,
        short_rows=short_rows,
        long_rows=long_rows,
    )


def _infer_year_from_name(name: str) -> str:
    match = re.search(r"(20\d{2})", name)
    if not match:
        raise ValueError(f"Cannot infer tax year from {name}")
    return match.group(1)


def _latest_completed_jobs_by_year() -> dict[int, dict[str, Any]]:
    jobs = STORE.list_processing_jobs(status="completed", limit=500, offset=0)
    latest: dict[int, dict[str, Any]] = {}
    for job in jobs:
        try:
            year = int(job.get("tax_year") or 0)
        except (TypeError, ValueError):
            continue
        if year <= 0:
            continue
        previous = latest.get(year)
        if previous is None or str(job.get("updated_at_utc", "")) > str(previous.get("updated_at_utc", "")):
            latest[year] = STORE.get_processing_job(str(job.get("job_id"))) or job
    return latest


def _job_summary(job: dict[str, Any] | None) -> dict[str, Any]:
    if not job:
        return {}
    summary = job.get("result_summary") or {}
    if isinstance(summary, str):
        try:
            summary = json.loads(summary)
        except json.JSONDecodeError:
            summary = {}
    return summary if isinstance(summary, dict) else {}


def _current_values(job: dict[str, Any] | None) -> dict[str, Decimal | str | int]:
    summary = _job_summary(job)
    tax_domain = summary.get("tax_domain_summary") if isinstance(summary, dict) else {}
    if not isinstance(tax_domain, dict):
        tax_domain = {}
    anlage = tax_domain.get("anlage_so") if isinstance(tax_domain.get("anlage_so"), dict) else {}
    term = tax_domain.get("termingeschaefte") if isinstance(tax_domain.get("termingeschaefte"), dict) else {}
    income = _parse_decimal(anlage.get("leistungen_income_eur"))
    private_net = _parse_decimal(anlage.get("private_veraeusserung_net_taxable_eur"))
    return {
        "job_id": str((job or {}).get("job_id") or ""),
        "tax_line_count": int((job or {}).get("tax_line_count") or 0),
        "derivative_line_count": int((job or {}).get("derivative_line_count") or 0),
        "leistungen_income_eur": income,
        "private_veraeusserung_net_taxable_eur": private_net,
        "anlage_so_total_eur": income + private_net,
        "termingeschaefte_netto_eur": _parse_decimal(term.get("netto_eur")),
    }


def _reference_payload(reference: WisoReference, current: dict[str, Decimal | str | int]) -> dict[str, Any]:
    submitted_total = reference.par22nr3_eur + reference.short_gain_loss_eur
    current_income = current["leistungen_income_eur"]
    current_private = current["private_veraeusserung_net_taxable_eur"]
    current_total = current["anlage_so_total_eur"]
    assert isinstance(current_income, Decimal)
    assert isinstance(current_private, Decimal)
    assert isinstance(current_total, Decimal)
    return {
        "year": reference.year,
        "source_path": reference.path,
        "source_type": "wiso_blockpit_submitted_reference",
        "row_count": reference.row_count,
        "short_rows": reference.short_rows,
        "long_rows": reference.long_rows,
        "submitted": {
            "par22nr3_eur": _plain(reference.par22nr3_eur),
            "capital_gains_short_eur": _plain(reference.short_gain_loss_eur),
            "capital_gains_all_rows_eur": _plain(reference.gain_loss_eur),
            "capital_gains_long_eur": _plain(reference.long_gain_loss_eur),
            "anlage_so_total_eur": _plain(submitted_total),
            "proceeds_eur": _plain(reference.proceeds_eur),
            "cost_basis_eur": _plain(reference.cost_basis_eur),
        },
        "current": {
            "job_id": current["job_id"],
            "tax_line_count": current["tax_line_count"],
            "derivative_line_count": current["derivative_line_count"],
            "leistungen_income_eur": _plain(current_income),
            "private_veraeusserung_net_taxable_eur": _plain(current_private),
            "anlage_so_total_eur": _plain(current_total),
            "termingeschaefte_netto_eur": _plain(current["termingeschaefte_netto_eur"]),
        },
        "delta_current_minus_submitted": {
            "leistungen_income_eur": _plain(current_income - reference.par22nr3_eur),
            "private_veraeusserung_net_taxable_eur": _plain(current_private - reference.short_gain_loss_eur),
            "anlage_so_total_eur": _plain(current_total - submitted_total),
        },
    }


def _plain(value: Any) -> str:
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01")).to_eng_string()
    return str(value)


def _write_markdown(payloads: list[dict[str, Any]], output_path: Path) -> None:
    lines = [
        "# WISO/Blockpit eingereichter Referenzstand",
        "",
        f"Erstellt: {datetime.now(UTC).isoformat()}",
        "",
        "Diese Datei behandelt die WISO/Blockpit-CSV-Dateien als eingereichten Referenzstand. Sie werden nicht als Primärdaten in die Steuerberechnung übernommen.",
        "",
        "| Jahr | Eingereicht §22 Nr.3 | Eingereicht private VG short | Eingereicht Anlage SO gesamt | Aktuell Leistungen | Aktuell private VG netto | Aktuell Anlage SO gesamt | Delta gesamt | Aktuell Termingeschäfte |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for payload in sorted(payloads, key=lambda item: int(item["year"])):
        submitted = payload["submitted"]
        current = payload["current"]
        delta = payload["delta_current_minus_submitted"]
        lines.append(
            "| {year} | {sub_income} | {sub_private} | {sub_total} | {cur_income} | {cur_private} | {cur_total} | {delta_total} | {term} |".format(
                year=payload["year"],
                sub_income=submitted["par22nr3_eur"],
                sub_private=submitted["capital_gains_short_eur"],
                sub_total=submitted["anlage_so_total_eur"],
                cur_income=current["leistungen_income_eur"],
                cur_private=current["private_veraeusserung_net_taxable_eur"],
                cur_total=current["anlage_so_total_eur"],
                delta_total=delta["anlage_so_total_eur"],
                term=current["termingeschaefte_netto_eur"],
            )
        )
    lines.extend(["", "## Details", ""])
    for payload in sorted(payloads, key=lambda item: int(item["year"])):
        lines.extend(
            [
                f"### {payload['year']}",
                "",
                f"- Quelle: `{payload['source_path']}`",
                f"- Zeilen: `{payload['row_count']}` (`Short` {payload['short_rows']}, `Long` {payload['long_rows']})",
                f"- Aktueller Job: `{payload['current']['job_id']}`",
                f"- Delta Leistungen: `{payload['delta_current_minus_submitted']['leistungen_income_eur']} EUR`",
                f"- Delta private Veräußerungen netto: `{payload['delta_current_minus_submitted']['private_veraeusserung_net_taxable_eur']} EUR`",
                f"- Delta Anlage SO gesamt: `{payload['delta_current_minus_submitted']['anlage_so_total_eur']} EUR`",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="usertransfer/wiso")
    parser.add_argument("--output", default="docs/23_WISO_SUBMITTED_REFERENCE_COMPARE_2026-05-07.md")
    parser.add_argument("--no-store", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    references = [_read_wiso_csv(path) for path in sorted(input_dir.glob("*.csv"))]
    latest_jobs = _latest_completed_jobs_by_year()
    payloads = [_reference_payload(reference, _current_values(latest_jobs.get(reference.year))) for reference in references]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(payloads, output_path)
    if not args.no_store:
        put_admin_setting(
            "runtime.submitted_tax_reports.wiso_blockpit",
            {
                "updated_at_utc": datetime.now(UTC).isoformat(),
                "source_dir": str(input_dir),
                "references": payloads,
            },
            is_secret=False,
        )
    print(json.dumps({"count": len(payloads), "output": str(output_path), "years": [item["year"] for item in payloads]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
