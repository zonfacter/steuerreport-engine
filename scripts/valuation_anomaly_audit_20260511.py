#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE  # noqa: E402
from tax_engine.queue.service import (  # noqa: E402
    STABLE_ASSETS,
    _asset_price_symbol,
    _load_token_alias_symbols,
)

RUN_DATE = "2026-05-11"
OUT_JSON = ROOT / "var" / "valuation_anomaly_audit_2026-05-11.json"
OUT_MD = ROOT / "docs" / "224_VALUATION_ANOMALY_AUDIT_RESULTS_2026-05-11.md"
CURRENT_YEARS = {2024, 2025, 2026}
FAST_NULL_RATIO = Decimal("0.005")
MATERIAL_PROCEEDS_EUR = Decimal("10")
HIGH_MATERIAL_PROCEEDS_EUR = Decimal("50")


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Any) -> str:
    value_dec = dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == 0:
        return Decimal("0")
    return numerator / denominator


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


def event_timestamp(payload_data: dict[str, Any]) -> str:
    return str(payload_data.get("timestamp_utc") or payload_data.get("timestamp") or "")


def event_date(payload_data: dict[str, Any]) -> str:
    return event_timestamp(payload_data)[:10]


def event_side(payload_data: dict[str, Any]) -> str:
    return str(payload_data.get("side") or payload_data.get("direction") or "").lower().strip()


def event_tx_id(payload_data: dict[str, Any]) -> str:
    return str(payload_data.get("tx_id") or payload_data.get("transaction_hash") or payload_data.get("signature") or "").strip()


def event_quantity(payload_data: dict[str, Any]) -> Decimal:
    return dec(payload_data.get("quantity") or payload_data.get("amount"))


def has_value_anchor(payload_data: dict[str, Any]) -> bool:
    return any(
        dec(payload_data.get(key)) > 0
        for key in ("price_usd", "price_eur", "value_usd_sum", "value_eur", "raw_value_usd_sum")
    )


def is_swap_like(payload_data: dict[str, Any]) -> bool:
    event_type = str(payload_data.get("event_type") or "").lower().strip()
    defi_label = str(payload_data.get("defi_label") or "").lower().strip()
    if defi_label == "swap":
        return True
    return "swap" in event_type


def latest_completed_jobs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return rows(
        conn,
        """
        SELECT *
        FROM (
            SELECT
                pq.*,
                (
                    SELECT count(*)
                    FROM tax_lines tl
                    WHERE tl.job_id = pq.job_id
                ) AS tax_line_count,
                (
                    SELECT count(*)
                    FROM derivative_lines dl
                    WHERE dl.job_id = pq.job_id
                ) AS derivative_line_count,
                row_number() OVER (
                    PARTITION BY tax_year
                    ORDER BY updated_at_utc DESC, created_at_utc DESC
                ) AS rank
            FROM processing_queue pq
            WHERE pq.status = 'completed'
              AND pq.tax_year BETWEEN 2020 AND 2026
        )
        WHERE rank = 1
        ORDER BY tax_year
        """,
    )


def latest_tax_lines(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return rows(
        conn,
        """
        WITH latest AS (
            SELECT *
            FROM (
                SELECT
                    pq.*,
                    row_number() OVER (
                        PARTITION BY tax_year
                        ORDER BY updated_at_utc DESC, created_at_utc DESC
                    ) AS rank
                FROM processing_queue pq
                WHERE pq.status = 'completed'
                  AND pq.tax_year BETWEEN 2020 AND 2026
            )
            WHERE rank = 1
        )
        SELECT
            latest.tax_year,
            latest.updated_at_utc AS job_updated_at_utc,
            tl.*
        FROM tax_lines tl
        JOIN latest ON latest.job_id = tl.job_id
        ORDER BY latest.tax_year, tl.line_no
        """,
    )


def load_raw_events(conn: sqlite3.Connection, event_ids: set[str]) -> dict[str, dict[str, Any]]:
    if not event_ids:
        return {}
    output: dict[str, dict[str, Any]] = {}
    ordered = sorted(event_ids)
    for start in range(0, len(ordered), 800):
        chunk = ordered[start : start + 800]
        placeholders = ",".join("?" for _ in chunk)
        for row in rows(
            conn,
            f"""
            SELECT
                r.unique_event_id,
                r.source_file_id,
                r.row_index,
                r.payload_json,
                sf.source_name
            FROM raw_events r
            LEFT JOIN source_files sf ON sf.source_file_id = r.source_file_id
            WHERE r.unique_event_id IN ({placeholders})
            """,
            tuple(chunk),
        ):
            output[str(row["unique_event_id"])] = row
    return output


def load_solana_swap_in_events(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return rows(
        conn,
        """
        SELECT
            r.unique_event_id,
            r.source_file_id,
            r.row_index,
            r.payload_json,
            sf.source_name
        FROM raw_events r
        LEFT JOIN source_files sf ON sf.source_file_id = r.source_file_id
        WHERE json_extract(r.payload_json, '$.source') = 'solana_rpc'
          AND lower(coalesce(json_extract(r.payload_json, '$.side'), '')) = 'in'
          AND (
              lower(coalesce(json_extract(r.payload_json, '$.defi_label'), '')) = 'swap'
              OR lower(coalesce(json_extract(r.payload_json, '$.event_type'), '')) LIKE '%swap%'
          )
        ORDER BY coalesce(json_extract(r.payload_json, '$.timestamp_utc'), json_extract(r.payload_json, '$.timestamp'))
        """,
    )


def load_tx_events(conn: sqlite3.Connection, tx_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
    if not tx_ids:
        return {}
    output: dict[str, list[dict[str, Any]]] = defaultdict(list)
    ordered = sorted(tx_ids)
    for start in range(0, len(ordered), 400):
        chunk = ordered[start : start + 400]
        placeholders = ",".join("?" for _ in chunk)
        for row in rows(
            conn,
            f"""
            SELECT
                r.unique_event_id,
                r.source_file_id,
                r.row_index,
                r.payload_json,
                sf.source_name
            FROM raw_events r
            LEFT JOIN source_files sf ON sf.source_file_id = r.source_file_id
            WHERE json_extract(r.payload_json, '$.tx_id') IN ({placeholders})
            ORDER BY coalesce(json_extract(r.payload_json, '$.timestamp_utc'), json_extract(r.payload_json, '$.timestamp')),
                     r.unique_event_id
            """,
            tuple(chunk),
        ):
            data = payload(row)
            output[event_tx_id(data)].append(row)
    return dict(output)


def fx_rate_on_or_before(conn: sqlite3.Connection, asset: str, rate_date: str) -> dict[str, Any] | None:
    if not asset or not rate_date:
        return None
    result = rows(
        conn,
        """
        SELECT rate_date, base_ccy, quote_ccy, rate, source, source_rate_date
        FROM fx_cache
        WHERE base_ccy = ?
          AND quote_ccy = 'USD'
          AND rate_date <= ?
        ORDER BY rate_date DESC
        LIMIT 1
        """,
        (asset, rate_date),
    )
    return result[0] if result else None


def counterflow_summary(
    conn: sqlite3.Connection,
    *,
    payload_data: dict[str, Any],
    tx_events: dict[str, list[dict[str, Any]]],
    aliases: dict[str, str],
) -> dict[str, Any]:
    tx_id = event_tx_id(payload_data)
    target_asset = _asset_price_symbol(payload_data.get("asset"), aliases)
    rate_date = event_date(payload_data)
    if not tx_id or not target_asset or not rate_date:
        return {"available": False, "value_usd": "0", "assets": [], "tx_id": tx_id}

    total = Decimal("0")
    assets: list[str] = []
    event_ids: list[str] = []
    for raw_row in tx_events.get(tx_id, []):
        raw_payload = payload(raw_row)
        if event_side(raw_payload) != "out":
            continue
        quantity = event_quantity(raw_payload)
        if quantity <= 0:
            continue
        asset = _asset_price_symbol(raw_payload.get("asset"), aliases)
        if not asset or asset == target_asset:
            continue
        if asset in STABLE_ASSETS:
            value_usd = quantity
            rate = {"rate_date": rate_date, "rate": "1", "source": "stable_asset"}
        else:
            rate = fx_rate_on_or_before(conn, asset, rate_date)
            value_usd = quantity * dec(rate.get("rate")) if rate else Decimal("0")
        if value_usd <= 0:
            continue
        total += value_usd
        assets.append(asset)
        event_ids.append(str(raw_row.get("unique_event_id") or ""))
    return {
        "available": total > 0,
        "value_usd": plain(total),
        "assets": sorted(set(assets)),
        "event_ids": event_ids,
        "tx_id": tx_id,
    }


def tax_line_payload(line: dict[str, Any], raw_events: dict[str, dict[str, Any]], aliases: dict[str, str]) -> dict[str, Any]:
    lot_event_id = str(line.get("lot_source_event_id") or "")
    lot_raw = raw_events.get(lot_event_id)
    lot_payload = payload(lot_raw)
    asset = _asset_price_symbol(lot_payload.get("asset") or line.get("asset"), aliases)
    return {
        "tax_year": int(line.get("tax_year") or 0),
        "job_id": str(line.get("job_id") or ""),
        "line_no": int(line.get("line_no") or 0),
        "asset": str(line.get("asset") or ""),
        "qty": str(line.get("qty") or ""),
        "buy_timestamp_utc": str(line.get("buy_timestamp_utc") or ""),
        "sell_timestamp_utc": str(line.get("sell_timestamp_utc") or ""),
        "cost_basis_eur": plain(line.get("cost_basis_eur")),
        "proceeds_eur": plain(line.get("proceeds_eur")),
        "gain_loss_eur": plain(line.get("gain_loss_eur")),
        "cost_basis_ratio": plain(ratio(dec(line.get("cost_basis_eur")), dec(line.get("proceeds_eur")))),
        "hold_days": int(line.get("hold_days") or 0),
        "tax_status": str(line.get("tax_status") or ""),
        "source_event_id": str(line.get("source_event_id") or ""),
        "lot_source_event_id": lot_event_id,
        "lot_event": {
            "source": str(lot_payload.get("source") or ""),
            "event_type": str(lot_payload.get("event_type") or ""),
            "side": event_side(lot_payload),
            "asset": str(lot_payload.get("asset") or ""),
            "price_symbol": asset,
            "quantity": str(lot_payload.get("quantity") or ""),
            "defi_label": str(lot_payload.get("defi_label") or ""),
            "tx_id": event_tx_id(lot_payload),
            "timestamp_utc": event_timestamp(lot_payload),
            "source_file_id": str(lot_raw.get("source_file_id") if lot_raw else ""),
            "source_name": str(lot_raw.get("source_name") if lot_raw else ""),
        },
    }


def priority_for(line_item: dict[str, Any], counterflow: dict[str, Any], fx_available: bool) -> str:
    tax_year = int(line_item.get("tax_year") or 0)
    proceeds = dec(line_item.get("proceeds_eur"))
    cost_ratio = dec(line_item.get("cost_basis_ratio"))
    lot_event = line_item.get("lot_event") if isinstance(line_item.get("lot_event"), dict) else {}
    swap_like = is_swap_like(lot_event)
    if tax_year in CURRENT_YEARS and proceeds >= HIGH_MATERIAL_PROCEEDS_EUR and cost_ratio < Decimal("0.01"):
        if swap_like or counterflow.get("available") or fx_available:
            return "priority_1"
    if proceeds >= MATERIAL_PROCEEDS_EUR and cost_ratio < Decimal("0.01"):
        return "priority_2"
    return "priority_3"


def build_audit(conn: sqlite3.Connection) -> dict[str, Any]:
    STORE.initialize()
    aliases = _load_token_alias_symbols()
    jobs = latest_completed_jobs(conn)
    tax_lines = latest_tax_lines(conn)
    event_ids = {
        str(line.get("source_event_id") or "")
        for line in tax_lines
        if str(line.get("source_event_id") or "")
    } | {
        str(line.get("lot_source_event_id") or "")
        for line in tax_lines
        if str(line.get("lot_source_event_id") or "")
    }
    solana_swap_rows = load_solana_swap_in_events(conn)
    event_ids |= {str(row.get("unique_event_id") or "") for row in solana_swap_rows}
    raw_events = load_raw_events(conn, event_ids)
    tax_lines_by_lot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in tax_lines:
        tax_lines_by_lot[str(line.get("lot_source_event_id") or "")].append(line)

    candidate_tx_ids: set[str] = set()
    for raw_row in raw_events.values():
        tx_id = event_tx_id(payload(raw_row))
        if tx_id:
            candidate_tx_ids.add(tx_id)
    tx_events = load_tx_events(conn, candidate_tx_ids)

    fast_null: list[dict[str, Any]] = []
    fx_unused: list[dict[str, Any]] = []
    high_gain_ratio: list[dict[str, Any]] = []
    counterflow_candidates: list[dict[str, Any]] = []

    for line in tax_lines:
        proceeds = dec(line.get("proceeds_eur"))
        cost = dec(line.get("cost_basis_eur"))
        gain = dec(line.get("gain_loss_eur"))
        tax_status = str(line.get("tax_status") or "").lower()
        if tax_status not in {"taxable", "business"}:
            continue
        item = tax_line_payload(line, raw_events, aliases)
        lot_event = item["lot_event"]
        lot_payload = payload(raw_events.get(str(line.get("lot_source_event_id") or "")))
        counterflow = counterflow_summary(conn, payload_data=lot_payload, tx_events=tx_events, aliases=aliases)
        fx_row = fx_rate_on_or_before(conn, str(lot_event.get("price_symbol") or ""), event_date(lot_payload))
        fx_payload = {
            "available": fx_row is not None,
            "rate_date": str(fx_row.get("rate_date") if fx_row else ""),
            "rate": str(fx_row.get("rate") if fx_row else ""),
            "source": str(fx_row.get("source") if fx_row else ""),
        }
        enriched = {
            **item,
            "priority": priority_for(item, counterflow, fx_row is not None),
            "fx_cache_asset_usd": fx_payload,
            "same_tx_priced_counterflow": counterflow,
        }
        if proceeds > MATERIAL_PROCEEDS_EUR and cost > 0 and ratio(cost, proceeds) < FAST_NULL_RATIO:
            fast_null.append(enriched)
            if fx_row is not None and event_side(lot_payload) == "in":
                fx_unused.append(enriched)
            if counterflow.get("available"):
                counterflow_candidates.append(enriched)
        if proceeds >= HIGH_MATERIAL_PROCEEDS_EUR and proceeds > 0 and ratio(gain, proceeds) > Decimal("0.95"):
            high_gain_ratio.append(enriched)

    swap_without_anchor: list[dict[str, Any]] = []
    for raw_row in solana_swap_rows:
        raw_payload = payload(raw_row)
        if has_value_anchor(raw_payload):
            continue
        event_id = str(raw_row.get("unique_event_id") or "")
        related_lines = tax_lines_by_lot.get(event_id, [])
        related_payloads = [tax_line_payload(line, raw_events, aliases) for line in related_lines]
        suspicious_related_payloads = [
            item
            for item in related_payloads
            if str(item.get("tax_status") or "").lower() in {"taxable", "business"}
            and dec(item.get("proceeds_eur")) >= MATERIAL_PROCEEDS_EUR
            and dec(item.get("cost_basis_eur")) >= Decimal("0")
            and dec(item.get("cost_basis_ratio")) < FAST_NULL_RATIO
        ]
        min_ratio = min((dec(item.get("cost_basis_ratio")) for item in suspicious_related_payloads), default=Decimal("0"))
        proceeds_sum = sum((dec(item.get("proceeds_eur")) for item in suspicious_related_payloads), Decimal("0"))
        counterflow = counterflow_summary(conn, payload_data=raw_payload, tx_events=tx_events, aliases=aliases)
        price_symbol = _asset_price_symbol(raw_payload.get("asset"), aliases)
        fx_row = fx_rate_on_or_before(conn, price_symbol, event_date(raw_payload))
        if suspicious_related_payloads and proceeds_sum >= HIGH_MATERIAL_PROCEEDS_EUR:
            priority = "priority_1"
        elif suspicious_related_payloads and proceeds_sum >= MATERIAL_PROCEEDS_EUR:
            priority = "priority_2"
        else:
            priority = "informational"
        swap_without_anchor.append(
            {
                "priority": priority,
                "unique_event_id": event_id,
                "timestamp_utc": event_timestamp(raw_payload),
                "source_file_id": str(raw_row.get("source_file_id") or ""),
                "source_name": str(raw_row.get("source_name") or ""),
                "source": str(raw_payload.get("source") or ""),
                "event_type": str(raw_payload.get("event_type") or ""),
                "side": event_side(raw_payload),
                "asset": str(raw_payload.get("asset") or ""),
                "price_symbol": price_symbol,
                "quantity": str(raw_payload.get("quantity") or ""),
                "defi_label": str(raw_payload.get("defi_label") or ""),
                "tx_id": event_tx_id(raw_payload),
                "related_tax_line_count": len(related_payloads),
                "suspicious_related_tax_line_count": len(suspicious_related_payloads),
                "suspicious_related_proceeds_eur": plain(proceeds_sum),
                "min_related_cost_basis_ratio": plain(min_ratio),
                "fx_cache_asset_usd": {
                    "available": fx_row is not None,
                    "rate_date": str(fx_row.get("rate_date") if fx_row else ""),
                    "rate": str(fx_row.get("rate") if fx_row else ""),
                    "source": str(fx_row.get("source") if fx_row else ""),
                },
                "same_tx_priced_counterflow": counterflow,
                "related_tax_lines": related_payloads[:10],
                "suspicious_related_tax_lines": suspicious_related_payloads[:10],
            }
        )

    def sort_key(item: dict[str, Any]) -> tuple[int, Decimal]:
        priority_order = {"priority_1": 0, "priority_2": 1, "priority_3": 2, "informational": 3}
        return (
            priority_order.get(str(item.get("priority")), 9),
            -dec(item.get("proceeds_eur") or item.get("suspicious_related_proceeds_eur")),
        )

    fast_null.sort(key=sort_key)
    fx_unused.sort(key=sort_key)
    high_gain_ratio.sort(key=sort_key)
    counterflow_candidates.sort(key=sort_key)
    swap_without_anchor.sort(key=sort_key)

    return {
        "run_date": RUN_DATE,
        "created_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "db_path": str(STORE.db_path),
        "latest_jobs": [
            {
                "tax_year": int(job.get("tax_year") or 0),
                "job_id": str(job.get("job_id") or ""),
                "updated_at_utc": str(job.get("updated_at_utc") or ""),
                "tax_line_count": int(job.get("tax_line_count") or 0),
                "derivative_line_count": int(job.get("derivative_line_count") or 0),
            }
            for job in jobs
        ],
        "thresholds": {
            "fast_null_ratio": str(FAST_NULL_RATIO),
            "material_proceeds_eur": str(MATERIAL_PROCEEDS_EUR),
            "high_material_proceeds_eur": str(HIGH_MATERIAL_PROCEEDS_EUR),
        },
        "counts": {
            "latest_tax_lines": len(tax_lines),
            "solana_swap_in_raw_events_without_raw_anchor": len(swap_without_anchor),
            "fast_null_cost_basis": len(fast_null),
            "fx_available_but_low_cost_basis": len(fx_unused),
            "same_tx_priced_counterflow_candidates": len(counterflow_candidates),
            "high_gain_ratio": len(high_gain_ratio),
            "priority_1_total": sum(
                1
                for collection in (fast_null, fx_unused, counterflow_candidates, high_gain_ratio, swap_without_anchor)
                for item in collection
                if item.get("priority") == "priority_1"
            ),
        },
        "findings": {
            "fast_null_cost_basis": fast_null,
            "swap_semantics_without_raw_anchor": swap_without_anchor,
            "same_tx_priced_counterflow_candidates": counterflow_candidates,
            "fx_available_but_low_cost_basis": fx_unused,
            "high_gain_ratio": high_gain_ratio,
        },
    }


def md_table(items: list[dict[str, Any]], *, limit: int = 25) -> list[str]:
    lines = [
        "| Prio | Jahr | Line | Asset | Kostenbasis | Erloes | Quote | Lot-Event | Swap | Gegenfluss |",
        "| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for item in items[:limit]:
        lot_event = item.get("lot_event") if isinstance(item.get("lot_event"), dict) else {}
        counterflow = item.get("same_tx_priced_counterflow") if isinstance(item.get("same_tx_priced_counterflow"), dict) else {}
        lines.append(
            "| {priority} | {tax_year} | {line_no} | `{asset}` | {cost} | {proceeds} | {ratio} | `{source}/{event_type}/{side}` | {swap} | {counterflow} |".format(
                priority=item.get("priority", ""),
                tax_year=item.get("tax_year", ""),
                line_no=item.get("line_no", ""),
                asset=item.get("asset", ""),
                cost=item.get("cost_basis_eur", ""),
                proceeds=item.get("proceeds_eur", ""),
                ratio=item.get("cost_basis_ratio", ""),
                source=lot_event.get("source", ""),
                event_type=lot_event.get("event_type", ""),
                side=lot_event.get("side", ""),
                swap="ja" if is_swap_like(lot_event) else "nein",
                counterflow="ja" if counterflow.get("available") else "nein",
            )
        )
    if not items:
        lines.append("| - | - | - | - | - | - | - | - | - | - |")
    return lines


def write_report(audit: dict[str, Any]) -> None:
    counts = audit["counts"]
    latest_jobs = audit["latest_jobs"]
    findings = audit["findings"]
    lines = [
        "# Bewertungsanomalie-Audit",
        "",
        f"Stand: {RUN_DATE}",
        "",
        "## Scope",
        "",
        "Ausgewertet wurden die neuesten abgeschlossenen Jobs je Steuerjahr `2020` bis `2026`.",
        "",
        "| Jahr | Job | Tax-Lines | Derivate-Lines | Aktualisiert |",
        "| ---: | --- | ---: | ---: | --- |",
    ]
    for job in latest_jobs:
        lines.append(
            f"| {job['tax_year']} | `{job['job_id']}` | {job['tax_line_count']} | "
            f"{job['derivative_line_count']} | {job['updated_at_utc']} |"
        )
    lines.extend(
        [
            "",
            "## Zusammenfassung",
            "",
            f"- Tax-Lines im Scope: `{counts['latest_tax_lines']}`",
            f"- Fast-Null-Kostenbasis: `{counts['fast_null_cost_basis']}`",
            f"- FX vorhanden, aber niedrige Kostenbasis: `{counts['fx_available_but_low_cost_basis']}`",
            f"- Gleicher `tx_id` mit bepreistem Gegenfluss: `{counts['same_tx_priced_counterflow_candidates']}`",
            f"- Hohe Gewinnquote: `{counts['high_gain_ratio']}`",
            f"- Solana-Swap-In-Raw-Events ohne Raw-Preisanker: `{counts['solana_swap_in_raw_events_without_raw_anchor']}`",
            f"- Prioritaet-1-Treffer ueber alle Klassen: `{counts['priority_1_total']}`",
            "",
            "Hinweis: Raw-Events werden nicht zwingend mit Laufzeit-Preisankern zurueckgeschrieben.",
            "Raw-Swap-Treffer sind deshalb nur dann hoch priorisiert, wenn die daraus entstandenen",
            "Tax-Lines ebenfalls auffaellig sind.",
            "",
            "## Fast-Null-Kostenbasis",
            "",
        ]
    )
    lines.extend(md_table(findings["fast_null_cost_basis"]))
    lines.extend(["", "## Gleicher TX mit bepreistem Gegenfluss", ""])
    lines.extend(md_table(findings["same_tx_priced_counterflow_candidates"]))
    lines.extend(["", "## FX vorhanden, aber niedrige Kostenbasis", ""])
    lines.extend(md_table(findings["fx_available_but_low_cost_basis"]))
    lines.extend(["", "## Hohe Gewinnquote", ""])
    lines.extend(md_table(findings["high_gain_ratio"]))
    lines.extend(["", "## Solana-Swap-In-Raw-Events ohne Raw-Preisanker", ""])
    lines.extend(
        [
            "| Prio | Zeit | Event | Asset | Menge | Tax-Lines | Erloes | Min-Quote | FX | Gegenfluss |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for item in findings["swap_semantics_without_raw_anchor"][:50]:
        fx_info = item.get("fx_cache_asset_usd") if isinstance(item.get("fx_cache_asset_usd"), dict) else {}
        counterflow = item.get("same_tx_priced_counterflow") if isinstance(item.get("same_tx_priced_counterflow"), dict) else {}
        lines.append(
            "| {priority} | {timestamp} | `{event_id}` | `{asset}` | {qty} | {line_count} | {proceeds} | {min_ratio} | {fx} | {counterflow} |".format(
                priority=item.get("priority", ""),
                timestamp=item.get("timestamp_utc", ""),
                event_id=item.get("unique_event_id", ""),
                asset=item.get("price_symbol") or item.get("asset", ""),
                qty=item.get("quantity", ""),
                line_count=item.get("suspicious_related_tax_line_count", 0),
                proceeds=item.get("suspicious_related_proceeds_eur", "0"),
                min_ratio=item.get("min_related_cost_basis_ratio", "0"),
                fx="ja" if fx_info.get("available") else "nein",
                counterflow="ja" if counterflow.get("available") else "nein",
            )
        )
    if not findings["swap_semantics_without_raw_anchor"]:
        lines.append("| - | - | - | - | - | - | - | - | - | - |")
    lines.extend(
        [
            "",
            "## Bewertung",
            "",
            "- `priority_1` ist direkt zu pruefen und bei eindeutigem Codepfad deterministisch zu fixen.",
            "- `priority_2` ist nachgelagert zu pruefen, besonders wenn aktuelle Jahre oder hohe Summen betroffen sind.",
            "- `informational` bei Raw-Swaps bedeutet nicht automatisch Fehler, weil Preisanker zur Laufzeit entstehen koennen.",
            "- Kein Treffer in diesem Bericht ist eine steuerberaterliche Endfreigabe.",
            "",
            "## Naechster Schritt",
            "",
            "Die `priority_1`-Treffer werden einzeln gegen Rohereignis, FX-Cache und Gegenfluss geprueft.",
            "Nur belegbare technische Luecken werden automatisch korrigiert.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    STORE.initialize()
    conn = sqlite3.connect(STORE.db_path)
    conn.row_factory = sqlite3.Row
    audit = build_audit(conn)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(audit)
    print(json.dumps({"json": str(OUT_JSON), "report": str(OUT_MD), "counts": audit["counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
