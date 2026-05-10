from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from tax_engine.api.app import review_negative_balances
from tax_engine.ingestion.store import STORE

REFERENCE_KEY = "runtime.submitted_tax_reports.wiso_blockpit"
OUTPUT_PATH = Path("docs/24_KORREKTURPAKET_2024_ENTWURF_2026-05-07.md")


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _money(value: Any) -> str:
    return _decimal(value).quantize(Decimal("0.01")).to_eng_string()


def _load_submitted_reference(year: int) -> dict[str, Any]:
    row = STORE.get_setting(REFERENCE_KEY)
    if row is None:
        raise RuntimeError(f"Missing setting {REFERENCE_KEY}")
    payload = json.loads(str(row.get("value_json") or "{}"))
    refs = payload.get("references") if isinstance(payload, dict) else []
    if not isinstance(refs, list):
        raise RuntimeError("Invalid WISO reference payload")
    for item in refs:
        if isinstance(item, dict) and int(item.get("year") or 0) == year:
            return item
    raise RuntimeError(f"Missing WISO reference for {year}")


def _latest_completed_job(year: int) -> dict[str, Any]:
    latest: dict[str, Any] | None = None
    for job in STORE.list_processing_jobs(status="completed", limit=500, offset=0):
        if int(job.get("tax_year") or 0) != year:
            continue
        full = STORE.get_processing_job(str(job.get("job_id"))) or job
        if latest is None or str(full.get("updated_at_utc", "")) > str(latest.get("updated_at_utc", "")):
            latest = full
    if latest is None:
        raise RuntimeError(f"No completed job for {year}")
    return latest


def _tax_summary(job: dict[str, Any]) -> dict[str, Any]:
    summary = job.get("result_summary") or {}
    if not isinstance(summary, dict):
        return {}
    tax = summary.get("tax_domain_summary") or {}
    return tax if isinstance(tax, dict) else {}


def _asset_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        asset = str(row.get("asset") or "").upper()
        counts[asset] = counts.get(asset, 0) + 1
    return dict(sorted(counts.items()))


def _tax_line_asset_summary(job_id: str) -> list[dict[str, str]]:
    buckets: dict[str, dict[str, Decimal]] = {}
    for line in STORE.get_tax_lines(job_id):
        asset = str(line.get("asset") or "UNKNOWN")
        bucket = buckets.setdefault(asset, {"gain_loss": Decimal("0"), "proceeds": Decimal("0"), "cost_basis": Decimal("0"), "count": Decimal("0")})
        bucket["gain_loss"] += _decimal(line.get("gain_loss_eur"))
        bucket["proceeds"] += _decimal(line.get("proceeds_eur"))
        bucket["cost_basis"] += _decimal(line.get("cost_basis_eur"))
        bucket["count"] += Decimal("1")
    rows = []
    for asset, values in sorted(buckets.items(), key=lambda item: abs(item[1]["gain_loss"]), reverse=True):
        rows.append(
            {
                "asset": asset,
                "count": str(int(values["count"])),
                "gain_loss_eur": _money(values["gain_loss"]),
                "proceeds_eur": _money(values["proceeds"]),
                "cost_basis_eur": _money(values["cost_basis"]),
            }
        )
    return rows


def _derivative_asset_summary(job_id: str) -> list[dict[str, str]]:
    buckets: dict[str, dict[str, Decimal]] = {}
    for line in STORE.get_derivative_lines(job_id):
        asset = str(line.get("asset") or "UNKNOWN")
        bucket = buckets.setdefault(asset, {"gain_loss": Decimal("0"), "fees": Decimal("0"), "count": Decimal("0")})
        bucket["gain_loss"] += _decimal(line.get("gain_loss_eur"))
        bucket["fees"] += _decimal(line.get("fees_eur"))
        bucket["count"] += Decimal("1")
    rows = []
    for asset, values in sorted(buckets.items(), key=lambda item: abs(item[1]["gain_loss"]), reverse=True):
        rows.append(
            {
                "asset": asset,
                "count": str(int(values["count"])),
                "gain_loss_eur": _money(values["gain_loss"]),
                "fees_eur": _money(values["fees"]),
            }
        )
    return rows


def main() -> int:
    year = 2024
    reference = _load_submitted_reference(year)
    job = _latest_completed_job(year)
    tax = _tax_summary(job)
    term = tax.get("termingeschaefte") if isinstance(tax.get("termingeschaefte"), dict) else {}
    neg = review_negative_balances(year=year, limit=500, include_events=0)
    neg_rows = neg.data.get("rows", []) if neg.status == "success" else []
    submitted = reference["submitted"]
    current = reference["current"]
    delta = reference["delta_current_minus_submitted"]
    tax_assets = _tax_line_asset_summary(str(job["job_id"]))[:15]
    derivative_assets = _derivative_asset_summary(str(job["job_id"]))[:15]

    lines = [
        "# Korrekturpaket 2024 Entwurf",
        "",
        f"Erstellt: {datetime.now(UTC).isoformat()}",
        "",
        "Status: Entwurf, nicht final einreichen.",
        "",
        "Grund: Der aktuelle Steuerlauf ist technisch erfolgreich, aber 2024 hat weiterhin Negativbestände. Dieses Paket dient als Arbeitsgrundlage für eine mögliche Änderung des Einkommensteuerbescheids 2024.",
        "",
        "## Kurzfazit",
        "",
        f"- Eingereichter Referenzstand WISO/Blockpit Anlage SO gesamt: `{submitted['anlage_so_total_eur']} EUR`.",
        f"- Aktueller Steuerreport Anlage SO gesamt: `{current['anlage_so_total_eur']} EUR`.",
        f"- Delta Anlage SO aktuell minus eingereicht: `{delta['anlage_so_total_eur']} EUR`.",
        f"- Aktuelle Termingeschäfte netto: `{current['termingeschaefte_netto_eur']} EUR`.",
        f"- Aktuelle Termingeschäfte Verlustsumme absolut: `{_money(term.get('verlust_summe_abs_eur'))} EUR`.",
        f"- Aktueller Job: `{job['job_id']}`.",
        "",
        "## Eingereicht vs. aktuell",
        "",
        "| Position | Eingereicht | Aktuell | Delta |",
        "|---|---:|---:|---:|",
        f"| Anlage SO Leistungen/Rewards | {submitted['par22nr3_eur']} | {current['leistungen_income_eur']} | {delta['leistungen_income_eur']} |",
        f"| Anlage SO private Veräußerungen netto | {submitted['capital_gains_short_eur']} | {current['private_veraeusserung_net_taxable_eur']} | {delta['private_veraeusserung_net_taxable_eur']} |",
        f"| Anlage SO gesamt | {submitted['anlage_so_total_eur']} | {current['anlage_so_total_eur']} | {delta['anlage_so_total_eur']} |",
        f"| Termingeschäfte netto | nicht im WISO-Referenz-CSV | {current['termingeschaefte_netto_eur']} | n/a |",
        "",
        "## Offene Qualitätsmarker",
        "",
        f"- Negativbestände 2024: `{len(neg_rows)}`.",
        f"- Nach Assets: `{json.dumps(_asset_counts(neg_rows), ensure_ascii=False, sort_keys=True)}`.",
        "- Benötigte Klärung: Bitget-Web-Exports/Statements für Spot/Bot/Grid/Strategy/Internal Transfers 2024; SOL- und Stablecoin-Bestände prüfen.",
        "",
        "## Größte aktuelle Anlage-SO-Assetgruppen",
        "",
        "| Asset | Zeilen | Gewinn/Verlust EUR | Erlöse EUR | Kostenbasis EUR |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in tax_assets:
        lines.append(f"| {row['asset']} | {row['count']} | {row['gain_loss_eur']} | {row['proceeds_eur']} | {row['cost_basis_eur']} |")
    lines.extend(
        [
            "",
            "## Termingeschäfte nach Asset",
            "",
            "| Asset | Zeilen | Gewinn/Verlust EUR | Gebühren EUR |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in derivative_assets:
        lines.append(f"| {row['asset']} | {row['count']} | {row['gain_loss_eur']} | {row['fees_eur']} |")
    lines.extend(
        [
            "",
            "## Entwurf Begründung Finanzamt",
            "",
            "Nach Abgabe der Einkommensteuererklärung 2024 wurden weitere Primärdaten aus Wallets und Börsen sowie ergänzende Export-/API-Daten ausgewertet. Der ursprünglich eingereichte WISO/Blockpit-Report wird als Referenzstand behandelt, ist nach aktuellem Datenstand aber nicht mehr vollständig deckungsgleich mit den verfügbaren Primärdaten.",
            "",
            "Die aktuelle Neuberechnung weist abweichende Besteuerungsgrundlagen in Anlage SO sowie gesondert zu berücksichtigende Termingeschäfte aus. Vor Einreichung dieses Entwurfs werden die noch offenen Bestandsdifferenzen und Plattform-Statements final abgeglichen.",
            "",
        ]
    )
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_PATH), "job_id": job["job_id"], "negative_count": len(neg_rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
