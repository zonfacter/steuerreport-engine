from __future__ import annotations

import csv
from datetime import UTC, datetime
from io import BytesIO, StringIO
from typing import Any

_PDF_MAX_PAGES_PER_FILE = 100
_PDF_ROWS_PER_PAGE = 28
_PDF_ROWS_PER_FILE = _PDF_MAX_PAGES_PER_FILE * _PDF_ROWS_PER_PAGE


def build_export_rows(
    job: dict[str, Any],
    tax_lines: list[dict[str, Any]],
    derivative_lines: list[dict[str, Any]],
    include_derivatives: bool,
    integrity: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    export_rows: list[dict[str, Any]] = []
    integrity_payload = integrity or {}
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
                "source_event_id": line.get("source_event_id"),
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
                    "fees_eur": line.get("fees_eur"),
                    "funding_eur": line.get("funding_eur"),
                    "event_type": line.get("event_type"),
                    "position_id": line.get("position_id"),
                }
            )
    return export_rows


def build_report_file_index(job: dict[str, Any], tax_line_count: int, derivative_line_count: int) -> list[dict[str, Any]]:
    job_id = str(job.get("job_id") or "")
    scopes = [
        ("all", "Vollreport", tax_line_count + derivative_line_count),
        ("tax", "Tax Lines", tax_line_count),
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
        "source_event_id",
    ]
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in headers})
    return buffer.getvalue()


def build_pdf_from_rows(
    *,
    job: dict[str, Any],
    rows: list[dict[str, Any]],
    integrity: dict[str, Any] | None,
    scope: str,
    part: int,
    part_count: int,
) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    page_width, page_height = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)
    integrity_payload = integrity or {}
    report_key = str(integrity_payload.get("report_integrity_id") or "nicht-verfuegbar")
    config_hash = str(integrity_payload.get("config_hash") or "nicht-verfuegbar")
    data_hash = str(integrity_payload.get("data_hash") or "nicht-verfuegbar")
    ruleset = f"{job.get('ruleset_id') or ''} {job.get('ruleset_version') or ''}".strip()
    generated_at = datetime.now(UTC).isoformat()
    total_pages = max(1, (len(rows) + _PDF_ROWS_PER_PAGE - 1) // _PDF_ROWS_PER_PAGE)

    for page_index in range(total_pages):
        start = page_index * _PDF_ROWS_PER_PAGE
        page_rows = rows[start : start + _PDF_ROWS_PER_PAGE]
        pdf.setTitle(f"Steuerreport {job.get('job_id')}")
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(36, page_height - 38, "Steuerreport Export")
        pdf.setFont("Helvetica", 7)
        pdf.drawString(36, page_height - 52, f"Run: {job.get('job_id')} | Jahr: {job.get('tax_year')} | Scope: {scope}")
        pdf.drawString(36, page_height - 64, f"Ruleset: {ruleset or 'nicht-verfuegbar'} | Teil: {part}/{part_count}")
        pdf.drawString(36, page_height - 76, f"Report-Integrity-ID: {report_key}")
        pdf.drawString(36, page_height - 88, f"Config-Hash: {config_hash} | Data-Hash: {data_hash}")
        pdf.drawString(36, page_height - 100, f"Erstellt UTC: {generated_at}")

        y = page_height - 122
        pdf.setFont("Helvetica-Bold", 7)
        columns = [
            ("Typ", 36),
            ("Nr", 72),
            ("Asset", 98),
            ("Menge", 138),
            ("Kauf", 194),
            ("Verkauf", 284),
            ("Kosten EUR", 374),
            ("Erloes EUR", 432),
            ("G/V EUR", 490),
            ("Status", 548),
        ]
        for label, x_pos in columns:
            pdf.drawString(x_pos, y, label)
        y -= 10
        pdf.line(36, y + 6, page_width - 32, y + 6)
        pdf.setFont("Helvetica", 6)
        for row in page_rows:
            values = [
                row.get("line_type"),
                row.get("line_no"),
                row.get("asset"),
                row.get("qty"),
                row.get("buy_timestamp_utc"),
                row.get("sell_timestamp_utc"),
                row.get("cost_basis_eur"),
                row.get("proceeds_eur"),
                row.get("gain_loss_eur"),
                row.get("tax_status"),
            ]
            for value, (_, x_pos) in zip(values, columns, strict=False):
                text = str(value or "")[:22]
                pdf.drawString(x_pos, y, text)
            y -= 14

        pdf.setFont("Helvetica", 7)
        pdf.drawRightString(
            page_width - 36,
            24,
            f"Seite {page_index + 1}/{total_pages} in Datei, max. {_PDF_MAX_PAGES_PER_FILE} Seiten je PDF",
        )
        pdf.showPage()

    pdf.save()
    return buffer.getvalue()
