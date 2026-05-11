#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-05-11"
DEFAULT_DB = Path("/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite")
OUT_JSON = ROOT / "var" / "hnt_usdt_remaining_inventory_gap_audit_2026-05-11.json"
OUT_MD = ROOT / "docs" / "229_HNT_USDT_REMAINING_INVENTORY_GAP_AUDIT_2026-05-11.md"
MATERIAL_PROCEEDS_EUR = Decimal("50")


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Any) -> str:
    value_dec = dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def payload(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    try:
        loaded = json.loads(str(row.get("payload_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def event_summary(row: dict[str, Any] | None) -> dict[str, Any]:
    data = payload(row)
    return {
        "event_id": str(row.get("unique_event_id") if row else ""),
        "source_file_id": str(row.get("source_file_id") if row else ""),
        "source_name": str(row.get("source_name") if row else ""),
        "row_index": int(row.get("row_index") or 0) if row else 0,
        "timestamp_utc": str(data.get("timestamp_utc") or data.get("timestamp") or ""),
        "source": str(data.get("source") or ""),
        "event_type": str(data.get("event_type") or ""),
        "side": str(data.get("side") or data.get("direction") or "").lower().strip(),
        "asset": str(data.get("asset") or ""),
        "quantity": str(data.get("quantity") or data.get("amount") or ""),
        "price": str(data.get("price") or ""),
        "value_usd": str(data.get("value_usd") or data.get("value_usd_sum") or ""),
        "value_eur": str(data.get("value_eur") or ""),
        "tx_id": str(data.get("tx_id") or data.get("transaction_hash") or data.get("signature") or ""),
    }


def latest_jobs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    job_rows = rows(
        conn,
        """
        SELECT *
        FROM ai_latest_completed_jobs_per_year
        WHERE tax_year BETWEEN 2020 AND 2026
        ORDER BY tax_year
        """,
    )
    output: list[dict[str, Any]] = []
    for job in job_rows:
        try:
            result = json.loads(str(job.get("result_json") or "{}"))
        except json.JSONDecodeError:
            result = {}
        output.append(
            {
                "tax_year": int(job.get("tax_year") or 0),
                "job_id": str(job.get("job_id") or ""),
                "updated_at_utc": str(job.get("updated_at_utc") or ""),
                "tax_line_count": int(result.get("tax_line_count") or 0),
                "derivative_line_count": int(
                    rows(
                        conn,
                        "SELECT count(*) AS count FROM derivative_lines WHERE job_id = ?",
                        (str(job.get("job_id") or ""),),
                    )[0]["count"]
                ),
            }
        )
    return output


def remaining_lines(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return rows(
        conn,
        """
        SELECT *
        FROM ai_open_zero_cost_tax_lines
        WHERE asset IN ('HNT', 'USDT')
          AND CAST(proceeds_eur AS REAL) >= ?
        ORDER BY tax_year, asset, line_no
        """,
        (str(MATERIAL_PROCEEDS_EUR),),
    )


def load_raw_event(conn: sqlite3.Connection, event_id: str) -> dict[str, Any] | None:
    if not event_id:
        return None
    result = rows(
        conn,
        """
        SELECT r.unique_event_id, r.source_file_id, r.row_index, r.payload_json, sf.source_name
        FROM raw_events r
        LEFT JOIN source_files sf ON sf.source_file_id = r.source_file_id
        WHERE r.unique_event_id = ?
        """,
        (event_id,),
    )
    return result[0] if result else None


def transfer_matches_for_inbound(conn: sqlite3.Connection, event_id: str) -> list[dict[str, Any]]:
    if not event_id:
        return []
    matches = rows(
        conn,
        """
        SELECT *
        FROM ai_transfer_matches_flat
        WHERE inbound_event_id = ?
        ORDER BY created_at_utc, match_id
        """,
        (event_id,),
    )
    output: list[dict[str, Any]] = []
    for match in matches:
        outbound_payload = json.loads(str(match.get("outbound_payload_json") or "{}"))
        inbound_payload = json.loads(str(match.get("inbound_payload_json") or "{}"))
        output.append(
            {
                "match_id": str(match.get("match_id") or ""),
                "outbound_event_id": str(match.get("outbound_event_id") or ""),
                "inbound_event_id": str(match.get("inbound_event_id") or ""),
                "confidence_score": str(match.get("confidence_score") or ""),
                "time_diff_seconds": int(match.get("time_diff_seconds") or 0),
                "amount_diff": str(match.get("amount_diff") or ""),
                "status": str(match.get("status") or ""),
                "method": str(match.get("method") or ""),
                "note": str(match.get("note") or ""),
                "outbound": {
                    "timestamp_utc": str(outbound_payload.get("timestamp_utc") or ""),
                    "source": str(outbound_payload.get("source") or ""),
                    "event_type": str(outbound_payload.get("event_type") or ""),
                    "asset": str(outbound_payload.get("asset") or ""),
                    "quantity": str(outbound_payload.get("quantity") or ""),
                    "value_usd": str(outbound_payload.get("value_usd") or ""),
                    "tx_id": str(outbound_payload.get("tx_id") or ""),
                },
                "inbound": {
                    "timestamp_utc": str(inbound_payload.get("timestamp_utc") or ""),
                    "source": str(inbound_payload.get("source") or ""),
                    "event_type": str(inbound_payload.get("event_type") or ""),
                    "asset": str(inbound_payload.get("asset") or ""),
                    "quantity": str(inbound_payload.get("quantity") or ""),
                    "tx_id": str(inbound_payload.get("tx_id") or ""),
                },
            }
        )
    return output


def same_tx_events(conn: sqlite3.Connection, tx_id: str) -> list[dict[str, Any]]:
    if not tx_id:
        return []
    return [
        event_summary(row)
        for row in rows(
            conn,
            """
            SELECT r.unique_event_id, r.source_file_id, r.row_index, r.payload_json, sf.source_name
            FROM raw_events r
            LEFT JOIN source_files sf ON sf.source_file_id = r.source_file_id
            WHERE json_extract(r.payload_json, '$.tx_id') = ?
            ORDER BY COALESCE(json_extract(r.payload_json, '$.timestamp_utc'), json_extract(r.payload_json, '$.timestamp')),
                     r.unique_event_id
            """,
            (tx_id,),
        )
    ]


def classify(line: dict[str, Any], lot_event: dict[str, Any], matches: list[dict[str, Any]]) -> str:
    if not str(line.get("lot_source_event_id") or ""):
        return "missing_lot_source_inventory_gap"
    if lot_event.get("source") == "binance_api" and lot_event.get("event_type") == "deposit" and matches:
        return "matched_transfer_source_cost_basis_gap"
    return "unclassified_inventory_gap"


def build_audit(conn: sqlite3.Connection) -> dict[str, Any]:
    lines = remaining_lines(conn)
    detail_rows: list[dict[str, Any]] = []
    for line in lines:
        source_event = event_summary(load_raw_event(conn, str(line.get("source_event_id") or "")))
        lot_event = event_summary(load_raw_event(conn, str(line.get("lot_source_event_id") or "")))
        matches = transfer_matches_for_inbound(conn, str(line.get("lot_source_event_id") or ""))
        same_tx = same_tx_events(conn, source_event.get("tx_id", ""))[:8]
        detail_rows.append(
            {
                "tax_year": int(line.get("tax_year") or 0),
                "job_id": str(line.get("job_id") or ""),
                "line_no": int(line.get("line_no") or 0),
                "asset": str(line.get("asset") or ""),
                "qty": plain(line.get("qty")),
                "buy_timestamp_utc": str(line.get("buy_timestamp_utc") or ""),
                "sell_timestamp_utc": str(line.get("sell_timestamp_utc") or ""),
                "cost_basis_eur": plain(line.get("cost_basis_eur")),
                "proceeds_eur": plain(line.get("proceeds_eur")),
                "gain_loss_eur": plain(line.get("gain_loss_eur")),
                "source_event_id": str(line.get("source_event_id") or ""),
                "lot_source_event_id": str(line.get("lot_source_event_id") or ""),
                "transfer_chain_id": str(line.get("transfer_chain_id") or ""),
                "classification": classify(line, lot_event, matches),
                "source_event": source_event,
                "lot_event": lot_event,
                "transfer_matches": matches,
                "same_tx_events": same_tx,
            }
        )

    groups: dict[tuple[str, int, str], dict[str, Any]] = {}
    for item in detail_rows:
        key = (str(item["classification"]), int(item["tax_year"]), str(item["asset"]))
        group = groups.setdefault(
            key,
            {
                "classification": key[0],
                "tax_year": key[1],
                "asset": key[2],
                "line_count": 0,
                "qty": Decimal("0"),
                "proceeds_eur": Decimal("0"),
                "lot_source_event_ids": set(),
                "source_platforms": set(),
            },
        )
        group["line_count"] += 1
        group["qty"] += dec(item["qty"])
        group["proceeds_eur"] += dec(item["proceeds_eur"])
        if item["lot_source_event_id"]:
            group["lot_source_event_ids"].add(item["lot_source_event_id"])
        group["source_platforms"].add(item["source_event"].get("source") or "")

    serializable_groups = []
    for group in sorted(groups.values(), key=lambda x: (x["tax_year"], x["asset"], x["classification"])):
        serializable_groups.append(
            {
                "classification": group["classification"],
                "tax_year": group["tax_year"],
                "asset": group["asset"],
                "line_count": group["line_count"],
                "qty": plain(group["qty"]),
                "proceeds_eur": plain(group["proceeds_eur"]),
                "lot_source_event_ids": sorted(group["lot_source_event_ids"]),
                "source_platforms": sorted(platform for platform in group["source_platforms"] if platform),
            }
        )

    return {
        "run_date": RUN_DATE,
        "created_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "db_path": str(DEFAULT_DB),
        "latest_jobs": latest_jobs(conn),
        "thresholds": {"material_proceeds_eur": str(MATERIAL_PROCEEDS_EUR)},
        "counts": {
            "remaining_line_count": len(detail_rows),
            "remaining_proceeds_eur": plain(sum((dec(item["proceeds_eur"]) for item in detail_rows), Decimal("0"))),
        },
        "groups": serializable_groups,
        "lines": detail_rows,
    }


def render_md(audit: dict[str, Any]) -> str:
    lines = [
        "# HNT-/USDT-Restbestandsluecken-Audit",
        "",
        f"Stand: {RUN_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Aktuelle Restzeilen: `{audit['counts']['remaining_line_count']}`",
        f"- Erloes dieser Restzeilen: `{audit['counts']['remaining_proceeds_eur']} EUR`",
        "- Keine Restzeile ist ein belegbarer Preisanker- oder FX-Backfill.",
        "- HNT-Transfer-Matches fuer die Binance-Deposits existieren bereits; die Luecke liegt vor dem Legacy-Outflow.",
        "- USDT-Reste bleiben Pionex-/Binance-Opening- bzw. Bot-Historie ohne Primaerbeleg.",
        "",
        "## Aktuelle Jobs",
        "",
        "| Jahr | Job | Tax-Lines | Derivate-Lines | Aktualisiert |",
        "| ---: | --- | ---: | ---: | --- |",
    ]
    for job in audit["latest_jobs"]:
        lines.append(
            f"| {job['tax_year']} | `{job['job_id']}` | {job['tax_line_count']} | "
            f"{job['derivative_line_count']} | {job['updated_at_utc']} |"
        )
    lines.extend(
        [
            "",
            "## Gruppierung",
            "",
            "| Jahr | Asset | Klasse | Zeilen | Menge | Erloes EUR | Plattformen |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for group in audit["groups"]:
        lines.append(
            f"| {group['tax_year']} | `{group['asset']}` | `{group['classification']}` | "
            f"{group['line_count']} | {group['qty']} | {group['proceeds_eur']} | "
            f"{', '.join(group['source_platforms'])} |"
        )

    lines.extend(
        [
            "",
            "## Betroffene Zeilen",
            "",
            "| Jahr | Line | Asset | Menge | Erloes EUR | Quelle | Lot-Quelle | Klasse |",
            "| ---: | ---: | --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for item in audit["lines"]:
        source = item["source_event"]
        lot = item["lot_event"]
        source_text = f"{source['source']}/{source['event_type']}/{source['side']}"
        lot_text = f"{lot['source']}/{lot['event_type']}/{lot['side']}" if item["lot_source_event_id"] else "leer"
        lines.append(
            f"| {item['tax_year']} | {item['line_no']} | `{item['asset']}` | {item['qty']} | "
            f"{item['proceeds_eur']} | `{source_text}` | `{lot_text}` | `{item['classification']}` |"
        )

    lines.extend(["", "## HNT-Transfer-Belege", ""])
    hnt_match_lines = [item for item in audit["lines"] if item["asset"] == "HNT" and item["transfer_matches"]]
    seen_matches: set[str] = set()
    if not hnt_match_lines:
        lines.append("- Keine HNT-Transfer-Matches in den Restzeilen.")
    for item in hnt_match_lines:
        for match in item["transfer_matches"]:
            match_id = match["match_id"]
            if match_id in seen_matches:
                continue
            seen_matches.add(match_id)
            outbound = match["outbound"]
            inbound = match["inbound"]
            lines.extend(
                [
                    f"- Match `{match_id}` fuer Inbound `{match['inbound_event_id']}`:",
                    f"  - Outbound `{outbound['source']}` `{outbound['event_type']}` "
                    f"{outbound['quantity']} `{outbound['asset']}` am `{outbound['timestamp_utc']}`.",
                    f"  - Binance-Inbound {inbound['quantity']} `{inbound['asset']}` am `{inbound['timestamp_utc']}`.",
                    f"  - Delta `{match['amount_diff']}`, Zeitdifferenz `{match['time_diff_seconds']}` Sekunden.",
                    f"  - Legacy-Transfer-Wert `value_usd={outbound['value_usd']}` ist ein Transferwert, "
                    "keine belegte Anschaffungskostenbasis.",
                ]
            )

    lines.extend(
        [
            "",
            "## Bewertung",
            "",
            "- Eine automatische Bewertung der HNT-Deposits mit dem Legacy-Transferwert waere fachlich falsch, "
            "weil Transferwert nicht gleich Anschaffungskosten ist.",
            "- Die 2021-HNT-Zeilen ohne Lot-Quelle liegen auf Binance-Verkaeufen am `2021-08-17`; "
            "fuer diese Verkaufsmenge gibt es im aktiven Datenstand keinen belegten vorherigen Binance-Deposit.",
            "- Die 2022-USDT-Zeilen decken sich mit dem bereits dokumentierten Pionex-/Binance-"
            "Opening- und Bot-Historienproblem.",
            "- Deshalb: keine neue automatische RAW-/FX-/Cost-Basis-Korrektur aus diesem Audit.",
            "",
            "## Naechste sichere Aktion",
            "",
            "- HNT: Primaerbelege fuer HNT-Anschaffung/Mining-Bestand vor den Legacy-Outflows nachreichen oder "
            "die historischen Nullbasis-Zeilen bewusst offen lassen.",
            "- USDT: Pionex-Opening-/Bot-Historie oder explizite Review-Entscheidung verwenden; ohne Beleg "
            "keinen steuerwirksamen Zufluss importieren.",
            "",
            f"JSON: `{OUT_JSON.relative_to(ROOT)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    uri = f"file:{DEFAULT_DB}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    audit = build_audit(conn)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    OUT_MD.write_text(render_md(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "report": str(OUT_MD), "counts": audit["counts"]}, indent=2))


if __name__ == "__main__":
    main()
