from __future__ import annotations

import csv
from datetime import UTC, datetime
from io import BytesIO, StringIO
from typing import Any

from tax_engine.connectors.token_metadata import resolve_token_metadata

_PDF_MAX_PAGES_PER_FILE = 100
_PDF_ROWS_PER_PAGE = 28
_PDF_SUMMARY_PAGES_PER_FILE = 1
_PDF_ROWS_PER_FILE = (_PDF_MAX_PAGES_PER_FILE - _PDF_SUMMARY_PAGES_PER_FILE) * _PDF_ROWS_PER_PAGE


def build_export_rows(
    job: dict[str, Any],
    tax_lines: list[dict[str, Any]],
    derivative_lines: list[dict[str, Any]],
    include_derivatives: bool,
    include_summary: bool = True,
    integrity: dict[str, Any] | None = None,
    draft_notice: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    export_rows: list[dict[str, Any]] = []
    integrity_payload = integrity or {}
    if draft_notice:
        export_rows.append(_build_draft_notice_row(job, integrity_payload, draft_notice))
    if include_summary:
        export_rows.extend(_build_tax_domain_summary_rows(job, integrity_payload))
    for line in tax_lines:
        export_rows.append(
            {
                "line_type": "tax",
                "job_id": job.get("job_id"),
                "tax_year": job.get("tax_year"),
                "ruleset_id": job.get("ruleset_id"),
                "ruleset_version": job.get("ruleset_version"),
                "report_integrity_id": integrity_payload.get("report_integrity_id"),
                "config_hash": integrity_payload.get("config_hash"),
                "data_hash": integrity_payload.get("data_hash"),
                "line_no": line.get("line_no"),
                "asset": line.get("asset"),
                "qty": line.get("qty"),
                "buy_timestamp_utc": line.get("buy_timestamp_utc"),
                "sell_timestamp_utc": line.get("sell_timestamp_utc"),
                "cost_basis_eur": line.get("cost_basis_eur"),
                "proceeds_eur": line.get("proceeds_eur"),
                "gain_loss_eur": line.get("gain_loss_eur"),
                "hold_days": line.get("hold_days"),
                "tax_status": line.get("tax_status"),
                "tax_domain": line.get("tax_domain"),
                "lot_domain": line.get("lot_domain"),
                "source_event_id": line.get("source_event_id"),
                "lot_source_event_id": line.get("lot_source_event_id"),
                "transfer_chain_id": line.get("transfer_chain_id"),
            }
        )
    if include_derivatives:
        for line in derivative_lines:
            export_rows.append(
                {
                    "line_type": "derivative",
                    "job_id": job.get("job_id"),
                    "tax_year": job.get("tax_year"),
                    "ruleset_id": job.get("ruleset_id"),
                    "ruleset_version": job.get("ruleset_version"),
                    "report_integrity_id": integrity_payload.get("report_integrity_id"),
                    "config_hash": integrity_payload.get("config_hash"),
                    "data_hash": integrity_payload.get("data_hash"),
                    "line_no": line.get("line_no"),
                    "asset": line.get("asset"),
                    "qty": None,
                    "buy_timestamp_utc": line.get("open_timestamp_utc"),
                    "sell_timestamp_utc": line.get("close_timestamp_utc"),
                    "cost_basis_eur": line.get("collateral_eur"),
                    "proceeds_eur": line.get("proceeds_eur"),
                    "gain_loss_eur": line.get("gain_loss_eur"),
                    "hold_days": None,
                    "tax_status": line.get("loss_bucket"),
                    "source_event_id": line.get("source_event_id"),
                    "lot_source_event_id": None,
                    "transfer_chain_id": None,
                    "fees_eur": line.get("fees_eur"),
                    "funding_eur": line.get("funding_eur"),
                    "event_type": line.get("event_type"),
                    "position_id": line.get("position_id"),
                }
            )
    return export_rows


def _build_draft_notice_row(
    job: dict[str, Any],
    integrity_payload: dict[str, Any],
    draft_notice: dict[str, Any],
) -> dict[str, Any]:
    return {
        **_base_export_row(job, integrity_payload),
        "line_type": "draft_notice",
        "line_no": 0,
        "asset": "PIONEX/USDT",
        "event_type": "export_blocker",
        "tax_status": "draft_only",
        "notice_code": str(draft_notice.get("code") or "draft_export_blocked"),
        "notice_message": str(draft_notice.get("message") or ""),
        "notice_candidate_id": str(draft_notice.get("candidate_id") or ""),
        "notice_required_evidence": " | ".join(str(item) for item in draft_notice.get("required_evidence", []) if item),
    }


def _base_export_row(job: dict[str, Any], integrity_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job.get("job_id"),
        "tax_year": job.get("tax_year"),
        "ruleset_id": job.get("ruleset_id"),
        "ruleset_version": job.get("ruleset_version"),
        "report_integrity_id": integrity_payload.get("report_integrity_id"),
        "config_hash": integrity_payload.get("config_hash"),
        "data_hash": integrity_payload.get("data_hash"),
    }


def _summary_row(
    job: dict[str, Any],
    integrity_payload: dict[str, Any],
    *,
    line_no: int,
    domain: str,
    metric: str,
    value: Any,
) -> dict[str, Any]:
    return {
        **_base_export_row(job, integrity_payload),
        "line_type": "tax_domain_summary",
        "line_no": line_no,
        "asset": domain,
        "event_type": metric,
        "summary_value": value,
        "summary_value_eur": value,
    }


def _build_tax_domain_summary_rows(job: dict[str, Any], integrity_payload: dict[str, Any]) -> list[dict[str, Any]]:
    result_summary = job.get("result_summary")
    if not isinstance(result_summary, dict):
        return []
    summary = result_summary.get("tax_domain_summary")
    if not isinstance(summary, dict):
        return []
    rows: list[dict[str, Any]] = []
    line_no = 1
    metric_groups = [
        ("ANLAGE_SO", summary.get("anlage_so", {})),
        ("EUER", summary.get("euer", {})),
        ("TERMINGESCHAEFTE", summary.get("termingeschaefte", {})),
        ("COUNTS", summary.get("classification_counts", {})),
    ]
    for domain, metrics in metric_groups:
        if not isinstance(metrics, dict):
            continue
        for metric, value in metrics.items():
            rows.append(
                _summary_row(
                    job,
                    integrity_payload,
                    line_no=line_no,
                    domain=domain,
                    metric=str(metric),
                    value=value,
                )
            )
            line_no += 1
    return rows


def _tax_domain_summary_row_count(job: dict[str, Any]) -> int:
    return len(_build_tax_domain_summary_rows(job, {}))


def build_report_file_index(
    job: dict[str, Any],
    tax_line_count: int,
    derivative_line_count: int,
    summary_line_count: int = 0,
) -> list[dict[str, Any]]:
    job_id = str(job.get("job_id") or "")
    scopes = [
        ("all", "Vollreport", tax_line_count + derivative_line_count + summary_line_count),
        ("tax", "Tax Lines + Summary", tax_line_count + summary_line_count),
        ("derivatives", "Derivate", derivative_line_count),
    ]
    files: list[dict[str, Any]] = []
    for scope, label, row_count in scopes:
        if scope != "all" and row_count == 0:
            continue
        for fmt in ("json", "csv"):
            files.append(
                {
                    "file_id": f"{job_id}:{scope}:{fmt}",
                    "label": f"{label} ({fmt.upper()})",
                    "format": fmt,
                    "scope": scope,
                    "row_count": row_count,
                    "download_url": f"/api/v1/report/export?job_id={job_id}&scope={scope}&fmt={fmt}",
                }
            )
        if scope in {"all", "tax"}:
            files.append(
                {
                    "file_id": f"{job_id}:{scope}:wiso",
                    "label": f"{label} (WISO Steuer CSV)",
                    "format": "wiso",
                    "scope": scope,
                    "row_count": tax_line_count,
                    "download_url": f"/api/v1/report/export?job_id={job_id}&scope={scope}&fmt=wiso",
                }
            )
        part_count = max(1, (row_count + _PDF_ROWS_PER_FILE - 1) // _PDF_ROWS_PER_FILE)
        for part in range(1, part_count + 1):
            suffix = f" Teil {part}/{part_count}" if part_count > 1 else ""
            files.append(
                {
                    "file_id": f"{job_id}:{scope}:pdf:{part}",
                    "label": f"{label} (PDF){suffix}",
                    "format": "pdf",
                    "scope": scope,
                    "part": part,
                    "part_count": part_count,
                    "row_count": row_count,
                    "max_pages": _PDF_MAX_PAGES_PER_FILE,
                    "download_url": f"/api/v1/report/export?job_id={job_id}&scope={scope}&fmt=pdf&part={part}",
                }
            )
    return files


def build_csv_from_rows(rows: list[dict[str, Any]]) -> str:
    headers = [
        "line_type",
        "job_id",
        "tax_year",
        "ruleset_id",
        "ruleset_version",
        "report_integrity_id",
        "config_hash",
        "data_hash",
        "line_no",
        "position_id",
        "asset",
        "event_type",
        "qty",
        "buy_timestamp_utc",
        "sell_timestamp_utc",
        "cost_basis_eur",
        "proceeds_eur",
        "fees_eur",
        "funding_eur",
        "gain_loss_eur",
        "hold_days",
        "tax_status",
        "tax_domain",
        "lot_domain",
        "source_event_id",
        "lot_source_event_id",
        "transfer_chain_id",
        "summary_value",
        "summary_value_eur",
        "notice_code",
        "notice_message",
        "notice_candidate_id",
        "notice_required_evidence",
    ]
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in headers})
    return buffer.getvalue()


def build_wiso_tax_csv(
    job: dict[str, Any],
    tax_lines: list[dict[str, Any]],
    draft_notice: dict[str, Any] | None = None,
) -> str:
    tax_year = str(job.get("tax_year") or "")
    short_lines = [line for line in tax_lines if str(line.get("tax_status") or "").lower() == "taxable"]
    par22nr3 = _tax_domain_value(job, "anlage_so", "leistungen_income_eur")
    buffer = StringIO()
    buffer.write(
        ",".join(
            [
                "Identifier:Capital_Gains",
                "Method:FIFO",
                f"Tax_Year:{tax_year}",
                "Base_Currency:EUR",
                f"Par22Nr3:{_wiso_money(par22nr3)}",
                *(_wiso_draft_notice_fields(draft_notice) if draft_notice else []),
            ]
        )
        + "\n"
    )
    headers = [
        "Amount",
        "Currency",
        "Date Acquired",
        "Date Sold",
        "Short / Long",
        "Buy / Input at",
        "Sell / Output at",
        "Proceeds",
        "Cost Basis",
        "Gain / Loss",
    ]
    writer = csv.DictWriter(buffer, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    for line in short_lines:
        writer.writerow(
            {
                "Amount": _wiso_decimal(line.get("qty")),
                "Currency": _wiso_asset(line.get("asset")),
                "Date Acquired": _wiso_date(line.get("buy_timestamp_utc")),
                "Date Sold": _wiso_date(line.get("sell_timestamp_utc")),
                "Short / Long": "Short",
                "Buy / Input at": _wiso_platform(line.get("lot_source_event_id")),
                "Sell / Output at": _wiso_platform(line.get("source_event_id")),
                "Proceeds": _wiso_money(line.get("proceeds_eur")),
                "Cost Basis": _wiso_money(line.get("cost_basis_eur")),
                "Gain / Loss": _wiso_money(line.get("gain_loss_eur")),
            }
        )
    return buffer.getvalue()


def _wiso_draft_notice_fields(draft_notice: dict[str, Any]) -> list[str]:
    message = str(draft_notice.get("message") or "Draft export blocked by open review gate.")
    candidate_id = str(draft_notice.get("candidate_id") or "")
    return [
        "Draft_Status:NOT_FINAL",
        f"Draft_Blocker:{_csv_header_value(message)}",
        f"Draft_Candidate:{_csv_header_value(candidate_id)}",
    ]


def _csv_header_value(value: str) -> str:
    return value.replace(",", " ").replace("\n", " ").replace("\r", " ").strip()


def _tax_domain_value(job: dict[str, Any], group: str, metric: str) -> Any:
    result_summary = job.get("result_summary")
    if not isinstance(result_summary, dict):
        return "0"
    tax_domain = result_summary.get("tax_domain_summary")
    if not isinstance(tax_domain, dict):
        return "0"
    metric_group = tax_domain.get(group)
    if not isinstance(metric_group, dict):
        return "0"
    return metric_group.get(metric, "0")


def _wiso_date(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return raw[:10]
    return parsed.strftime("%d.%m.%Y")


def _wiso_decimal(value: Any) -> str:
    text = str(value or "0").strip()
    if not text:
        return "0"
    return text


def _wiso_money(value: Any) -> str:
    try:
        parsed = float(str(value or "0"))
    except ValueError:
        parsed = 0.0
    if abs(parsed) < 0.005:
        parsed = 0.0
    text = f"{parsed:.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _wiso_asset(value: Any) -> str:
    metadata = resolve_token_metadata(str(value or ""))
    symbol = str(metadata.get("symbol") or value or "").strip()
    return symbol.replace(",", " ")


def _wiso_platform(source_event_id: Any) -> str:
    event_id = str(source_event_id or "").lower()
    if "binance" in event_id:
        return "Binance"
    if "bitget" in event_id:
        return "Bitget"
    if "pionex" in event_id:
        return "Pionex"
    if "solana" in event_id or "jupiter" in event_id:
        return "Solana"
    if "helium" in event_id:
        return "Helium"
    return "Steuerreport"


def build_pdf_from_rows(
    *,
    job: dict[str, Any],
    rows: list[dict[str, Any]],
    integrity: dict[str, Any] | None,
    scope: str,
    part: int,
    part_count: int,
    draft_notice: dict[str, Any] | None = None,
) -> bytes:
    from reportlab.lib.pagesizes import A4, landscape  # type: ignore[import-untyped]
    from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

    buffer = BytesIO()
    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    integrity_payload = integrity or {}
    report_key = str(integrity_payload.get("report_integrity_id") or "nicht-verfuegbar")
    config_hash = str(integrity_payload.get("config_hash") or "nicht-verfuegbar")
    data_hash = str(integrity_payload.get("data_hash") or "nicht-verfuegbar")
    ruleset = f"{job.get('ruleset_id') or ''} {job.get('ruleset_version') or ''}".strip()
    generated_at = datetime.now(UTC).isoformat()
    detail_rows = [
        row for row in rows if str(row.get("line_type") or "") not in {"tax_domain_summary", "draft_notice"}
    ]
    table_pages = max(1, (len(detail_rows) + _PDF_ROWS_PER_PAGE - 1) // _PDF_ROWS_PER_PAGE)
    total_pages = min(_PDF_MAX_PAGES_PER_FILE, 1 + table_pages)

    _draw_pdf_summary_page(
        pdf=pdf,
        page_width=page_width,
        page_height=page_height,
        job=job,
        scope=scope,
        part=part,
        part_count=part_count,
        report_key=report_key,
        config_hash=config_hash,
        data_hash=data_hash,
        ruleset=ruleset,
        generated_at=generated_at,
        row_count=len(rows),
        draft_notice=draft_notice,
    )
    pdf.showPage()

    for page_index in range(table_pages):
        start = page_index * _PDF_ROWS_PER_PAGE
        page_rows = detail_rows[start : start + _PDF_ROWS_PER_PAGE]
        pdf.setTitle(f"Steuerreport {job.get('job_id')}")
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(36, page_height - 38, "Steuerreport Detailtabelle")
        pdf.setFont("Helvetica", 7)
        pdf.drawString(36, page_height - 52, f"Run: {job.get('job_id')} | Jahr: {job.get('tax_year')} | Scope: {scope}")
        pdf.drawString(36, page_height - 64, f"Ruleset: {ruleset or 'nicht-verfuegbar'} | Datei-Teil: {part}/{part_count}")
        pdf.drawString(36, page_height - 76, f"Report-Integrity-ID: {report_key}")
        pdf.drawString(36, page_height - 88, f"Config-Hash: {config_hash} | Data-Hash: {data_hash}")
        pdf.drawString(36, page_height - 100, f"Erstellt UTC: {generated_at}")
        header_offset = 0
        if draft_notice:
            pdf.setFont("Helvetica-Bold", 8)
            pdf.drawString(36, page_height - 114, "ENTWURF - NICHT FINAL")
            pdf.setFont("Helvetica", 7)
            pdf.drawString(36, page_height - 126, str(draft_notice.get("message") or "")[:130])
            evidence = " | ".join(str(item) for item in draft_notice.get("required_evidence", []) if item)
            pdf.drawString(36, page_height - 138, f"Belegbedarf: {evidence[:120]}")
            header_offset = 38

        y = page_height - 122 - header_offset
        pdf.setFont("Helvetica-Bold", 7)
        columns = [
            ("Typ", 36),
            ("Nr", 92),
            ("Asset", 124),
            ("Menge", 168),
            ("Kauf", 250),
            ("Verkauf", 360),
            ("Kosten EUR", 470),
            ("Erloes EUR", 548),
            ("G/V EUR", 626),
            ("Status", 704),
        ]
        for label, x_pos in columns:
            pdf.drawString(x_pos, y, label)
        y -= 10
        pdf.line(36, y + 6, page_width - 32, y + 6)
        pdf.setFont("Helvetica", 6.5)
        if not page_rows:
            pdf.setFont("Helvetica", 8)
            pdf.drawString(36, y, "Keine Detailzeilen fuer diesen Scope.")
        for row in page_rows:
            values = [
                row.get("line_type"),
                row.get("line_no"),
                row.get("asset"),
                _pdf_number(row.get("qty"), places=8),
                row.get("buy_timestamp_utc"),
                row.get("sell_timestamp_utc"),
                _pdf_number(row.get("cost_basis_eur"), places=2),
                _pdf_number(row.get("proceeds_eur"), places=2),
                _pdf_number(row.get("gain_loss_eur"), places=2),
                row.get("tax_status"),
            ]
            for value, (_, x_pos) in zip(values, columns, strict=False):
                text = str(value or "")[:28]
                pdf.drawString(x_pos, y, text)
            y -= 14

        pdf.setFont("Helvetica", 7)
        pdf.drawRightString(
            page_width - 36,
            24,
            f"Seite {page_index + 2}/{total_pages} in Datei, max. {_PDF_MAX_PAGES_PER_FILE} Seiten je PDF",
        )
        pdf.showPage()

    pdf.save()
    return buffer.getvalue()


def _draw_pdf_summary_page(
    *,
    pdf: Any,
    page_width: float,
    page_height: float,
    job: dict[str, Any],
    scope: str,
    part: int,
    part_count: int,
    report_key: str,
    config_hash: str,
    data_hash: str,
    ruleset: str,
    generated_at: str,
    row_count: int,
    draft_notice: dict[str, Any] | None,
) -> None:
    tax_year = int(job.get("tax_year") or 0)
    summary_raw = job.get("result_summary")
    summary: dict[str, Any] = summary_raw if isinstance(summary_raw, dict) else {}
    tax_domain_raw = summary.get("tax_domain_summary")
    tax_domain: dict[str, Any] = tax_domain_raw if isinstance(tax_domain_raw, dict) else {}
    anlage_so_raw = tax_domain.get("anlage_so")
    anlage_so: dict[str, Any] = anlage_so_raw if isinstance(anlage_so_raw, dict) else {}
    euer_raw = tax_domain.get("euer")
    euer: dict[str, Any] = euer_raw if isinstance(euer_raw, dict) else {}
    termingeschaefte_raw = tax_domain.get("termingeschaefte")
    termingeschaefte: dict[str, Any] = termingeschaefte_raw if isinstance(termingeschaefte_raw, dict) else {}
    counts_raw = tax_domain.get("classification_counts")
    counts: dict[str, Any] = counts_raw if isinstance(counts_raw, dict) else {}

    pdf.setTitle(f"Steuerreport {job.get('job_id')}")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(36, page_height - 44, f"Steuerreport {tax_year}")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(36, page_height - 64, f"Run: {job.get('job_id')} | Scope: {scope} | Datei-Teil: {part}/{part_count}")
    pdf.drawString(36, page_height - 80, f"Ruleset: {ruleset or 'nicht-verfuegbar'} | Methode: FIFO | Basiswaehrung: EUR")
    pdf.drawString(36, page_height - 96, f"Erstellt UTC: {generated_at} | Exportzeilen in diesem Teil: {row_count}")

    if draft_notice:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(36, page_height - 120, "ENTWURF - NICHT FINAL")
        pdf.setFont("Helvetica", 8)
        _draw_wrapped(pdf, str(draft_notice.get("message") or ""), 36, page_height - 136, page_width - 72, 10, max_lines=2)

    y = page_height - (154 if draft_notice else 126)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(36, y, "Steuerliche Summen")
    y -= 20

    summary_rows = [
        ("§22 Nr. 3 sonstige Leistungen nicht gewerblich", _pdf_money(anlage_so.get("leistungen_income_eur"))),
        ("§23 private Veraeusserungen steuerpflichtig netto", _pdf_money(anlage_so.get("private_veraeusserung_net_taxable_eur"))),
        ("§23 steuerpflichtige Gewinne", _pdf_money(anlage_so.get("private_veraeusserung_taxable_gain_eur"))),
        ("§23 steuerpflichtige Verluste", _pdf_money(anlage_so.get("private_veraeusserung_taxable_loss_eur"))),
        ("§23 ausserhalb Haltefrist Gewinne", _pdf_money(anlage_so.get("private_veraeusserung_exempt_gain_eur"))),
        ("§23 ausserhalb Haltefrist Verluste", _pdf_money(anlage_so.get("private_veraeusserung_exempt_loss_eur"))),
        ("Termingeschaefte netto", _pdf_money(termingeschaefte.get("netto_eur"))),
        ("Termingeschaefte Verlustsumme", _pdf_money(termingeschaefte.get("verlust_summe_abs_eur"))),
        ("EÜR/Gewerbe Mining-/Reward-Einnahmen", _pdf_money(euer.get("betriebseinnahmen_mining_staking_eur"))),
        ("EÜR/Gewerbe Betriebsergebnis", _pdf_money(euer.get("betriebsergebnis_eur"))),
        ("Unbewertete/zu pruefende Bewertungsereignisse", str(counts.get("unresolved_valuation_events") or "0")),
    ]
    label_x = 36
    value_x = 430
    for index, (label, value) in enumerate(summary_rows):
        row_y = y - index * 15
        pdf.setFont("Helvetica", 8)
        pdf.drawString(label_x, row_y, label)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawRightString(value_x, row_y, value)

    y -= len(summary_rows) * 15 + 22
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(36, y, "Einordnung und Grenzen")
    y -= 18
    notes = [
        "Der PDF-Report ist eine lesbare Pruefmappe. Vollstaendige Detailwerte, Event-IDs, Hashes und maschinenlesbare Felder stehen in JSON/CSV.",
        "Krypto-zu-Krypto-Tausch, Verkauf und Swap werden als private Veraeusserungsvorgaenge nach §23 ausgewiesen; Mining-/Reward-nahe Zufluesse werden im Projekt als gewerbliche EÜR-Positionen gefuehrt.",
        "Haltefrist und FIFO werden nach dem ausgewaehlten deutschen Jahres-Ruleset angewendet; interne Transfers sollen keine Veraeusserung ausloesen.",
    ]
    if tax_year >= 2026:
        notes.append(
            "DAC8/CARF/KStTG ist fuer 2026 als Melde- und Plausibilitaetskontext zu behandeln; es ersetzt keine deutsche FIFO-Steuerberechnung."
        )
    for note in notes:
        y = _draw_wrapped(pdf, f"- {note}", 36, y, page_width - 72, 11, max_lines=2) - 2

    y -= 8
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(36, y, "Integritaet")
    y -= 18
    integrity_rows = [
        ("Report-Integrity-ID", report_key),
        ("Config-Hash", config_hash),
        ("Data-Hash", data_hash),
    ]
    for label, value in integrity_rows:
        pdf.setFont("Helvetica", 8)
        pdf.drawString(36, y, label)
        pdf.setFont("Helvetica", 7)
        pdf.drawString(160, y, str(value)[:120])
        y -= 14

    pdf.setFont("Helvetica", 7)
    pdf.drawRightString(page_width - 36, 24, f"Seite 1/{max(1, min(_PDF_MAX_PAGES_PER_FILE, 1 + ((row_count + _PDF_ROWS_PER_PAGE - 1) // _PDF_ROWS_PER_PAGE)))} in Datei")


def _draw_wrapped(
    pdf: Any,
    text: str,
    x: float,
    y: float,
    width: float,
    line_height: float,
    *,
    max_lines: int,
) -> float:
    approx_chars = max(20, int(width / 4.4))
    words = str(text or "").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= approx_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    for line in lines[:max_lines]:
        pdf.setFont("Helvetica", 8)
        pdf.drawString(x, y, line[:approx_chars])
        y -= line_height
    return y


def _pdf_number(value: Any, *, places: int) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = float(raw)
    except ValueError:
        return raw
    if abs(parsed) < 10 ** (-(places + 1)):
        parsed = 0.0
    text = f"{parsed:.{places}f}".rstrip("0").rstrip(".")
    return text or "0"


def _pdf_money(value: Any) -> str:
    number = _pdf_number(value, places=2)
    return f"{number} EUR" if number else "0 EUR"
