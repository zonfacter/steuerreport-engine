from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

DERIVATIVE_MARKERS = ("derivative", "future", "futures", "perp", "margin", "liquidation")
REFERENCE_SOURCES = ("blockpit", "cointracking", "cointracker", "wiso")


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _timestamp(payload: dict[str, Any]) -> str:
    return str(payload.get("timestamp_utc") or payload.get("timestamp") or "")


def _day(payload: dict[str, Any]) -> str:
    ts = _timestamp(payload)
    return ts[:10] if len(ts) >= 10 else "unknown"


def _source_name(source_files: dict[str, dict[str, Any]], source_file_id: str) -> str:
    return str(source_files.get(source_file_id, {}).get("source_name") or source_file_id)


def _is_derivative(payload: dict[str, Any]) -> bool:
    event_type = str(payload.get("event_type") or "").lower()
    source = str(payload.get("source") or "").lower()
    return any(marker in event_type or marker in source for marker in DERIVATIVE_MARKERS)


def _is_reference(payload: dict[str, Any], source_name: str) -> bool:
    source = str(payload.get("source") or "").lower()
    source_name = source_name.lower()
    return any(marker in source or marker in source_name for marker in REFERENCE_SOURCES)


def _solana_tx_failed(payload: dict[str, Any]) -> bool:
    if str(payload.get("source") or "").lower().strip() != "solana_rpc":
        return False
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return False
    meta = raw_row.get("meta")
    if not isinstance(meta, dict):
        return False
    status = meta.get("status")
    if isinstance(status, dict) and status.get("Err") is not None:
        return True
    return meta.get("err") is not None


def _heliumgeek_display_quantity(payload: dict[str, Any]) -> Decimal:
    if str(payload.get("source") or "").lower().strip() != "heliumgeek":
        return Decimal("0")
    asset = str(payload.get("asset") or "").upper().strip()
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0")
    for token_field, amount_field in (
        ("HNT Token", "HNT Tokens"),
        ("IOT Token", "IOT Tokens"),
        ("MOBILE Token", "MOBILE Tokens"),
    ):
        if str(raw_row.get(token_field, "")).upper().strip() != asset:
            continue
        value = _decimal(raw_row.get(amount_field))
        if value != Decimal("0"):
            return abs(value)
    return Decimal("0")


def _event_quantity(payload: dict[str, Any]) -> Decimal:
    display_quantity = _heliumgeek_display_quantity(payload)
    if display_quantity > Decimal("0"):
        return display_quantity
    return _decimal(payload.get("quantity"))


def _counter_top(counter: Counter[Any], limit: int = 10) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, count in counter.most_common(limit):
        if isinstance(key, tuple):
            label = " / ".join(str(item) for item in key)
        else:
            label = str(key)
        rows.append({"key": label, "count": int(count)})
    return rows


def _event_summary(events: list[dict[str, Any]], source_files: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()
    source_type_counter: Counter[tuple[str, str]] = Counter()
    asset_counter: Counter[str] = Counter()
    side_counter: Counter[str] = Counter()
    source_file_counter: Counter[str] = Counter()
    minute_counter: Counter[str] = Counter()
    zero_quantity_count = 0
    failed_zero_solana_count = 0
    derivative_count = 0
    reference_count = 0
    primary_count = 0
    quantity_by_source_type: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
        lambda: {"count": 0, "in": Decimal("0"), "out": Decimal("0"), "unknown": Decimal("0")}
    )
    huge_quantity_events: list[dict[str, Any]] = []

    for event in events:
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        source_file_id = str(event.get("source_file_id") or "")
        source_name = _source_name(source_files, source_file_id)
        source = str(payload.get("source") or "unknown")
        event_type = str(payload.get("event_type") or "unknown")
        asset = str(payload.get("asset") or payload.get("symbol") or "unknown")
        side = str(payload.get("side") or "unknown")
        raw_quantity = _decimal(payload.get("quantity"))
        quantity = _event_quantity(payload)
        ts = _timestamp(payload)

        source_counter[source] += 1
        type_counter[event_type] += 1
        source_type_counter[(source, event_type)] += 1
        asset_counter[asset] += 1
        side_counter[side] += 1
        source_file_counter[source_name] += 1
        if len(ts) >= 16:
            minute_counter[ts[:16]] += 1
        if quantity == 0:
            zero_quantity_count += 1
            if _solana_tx_failed(payload):
                failed_zero_solana_count += 1
        if _is_derivative(payload):
            derivative_count += 1
        if _is_reference(payload, source_name):
            reference_count += 1
        else:
            primary_count += 1

        bucket = quantity_by_source_type[(source, event_type)]
        bucket["count"] = int(bucket["count"]) + 1
        if side in {"in", "out"}:
            bucket[side] = Decimal(bucket[side]) + quantity
        else:
            bucket["unknown"] = Decimal(bucket["unknown"]) + quantity

        if asset in {"HNT", "IOT", "MOBILE"} and raw_quantity > Decimal("10000") and quantity <= Decimal("10000"):
            huge_quantity_events.append(
                {
                    "event_id": str(event.get("unique_event_id") or ""),
                    "timestamp_utc": ts,
                    "source": source,
                    "event_type": event_type,
                    "asset": asset,
                    "quantity": str(raw_quantity),
                    "effective_quantity": str(quantity),
                    "source_file": source_name,
                }
            )
        elif asset in {"HNT", "IOT", "MOBILE"} and quantity > Decimal("10000"):
            huge_quantity_events.append(
                {
                    "event_id": str(event.get("unique_event_id") or ""),
                    "timestamp_utc": ts,
                    "source": source,
                    "event_type": event_type,
                    "asset": asset,
                    "quantity": str(quantity),
                    "effective_quantity": str(quantity),
                    "source_file": source_name,
                }
            )

    source_type_quantities = []
    for key, value in sorted(quantity_by_source_type.items(), key=lambda item: int(item[1]["count"]), reverse=True)[:15]:
        source, event_type = key
        source_type_quantities.append(
            {
                "source": source,
                "event_type": event_type,
                "count": int(value["count"]),
                "in": str(value["in"]),
                "out": str(value["out"]),
                "unknown": str(value["unknown"]),
            }
        )

    return {
        "event_count": len(events),
        "derivative_count": derivative_count,
        "reference_count": reference_count,
        "primary_count": primary_count,
        "zero_quantity_count": zero_quantity_count,
        "failed_zero_solana_count": failed_zero_solana_count,
        "source_counts": _counter_top(source_counter, 15),
        "event_type_counts": _counter_top(type_counter, 15),
        "source_type_counts": _counter_top(source_type_counter, 15),
        "asset_counts": _counter_top(asset_counter, 15),
        "side_counts": _counter_top(side_counter, 8),
        "source_file_counts": _counter_top(source_file_counter, 15),
        "minute_clusters": _counter_top(minute_counter, 15),
        "source_type_quantities": source_type_quantities,
        "huge_quantity_events": huge_quantity_events[:25],
    }


def _day_flags(summary: dict[str, Any], *, min_day_events: int, cluster_min_events: int) -> list[dict[str, str]]:
    count = int(summary["event_count"])
    derivative = int(summary["derivative_count"])
    reference = int(summary["reference_count"])
    zero_quantity = int(summary["zero_quantity_count"])
    failed_zero_solana = int(summary.get("failed_zero_solana_count", 0))
    flags: list[dict[str, str]] = []
    if count >= min_day_events:
        flags.append({"severity": "medium", "code": "high_daily_event_count", "message": f"{count} Events an einem Tag"})
    if count and derivative / count >= 0.60:
        flags.append({"severity": "info", "code": "derivative_dominated", "message": f"{derivative} von {count} Events sind Derivate/Futures"})
    if count and reference / count >= 0.40:
        flags.append({"severity": "medium", "code": "reference_dominated", "message": f"{reference} von {count} Events kommen aus Referenzquellen"})
    if count and zero_quantity / count >= 0.10:
        flags.append({"severity": "info", "code": "many_zero_quantity_events", "message": f"{zero_quantity} Events mit Menge 0"})
    if failed_zero_solana:
        flags.append({"severity": "medium", "code": "failed_zero_solana_tx", "message": f"{failed_zero_solana} fehlgeschlagene Solana-Zero-Quantity-Events"})
    top_cluster = summary["minute_clusters"][0] if summary["minute_clusters"] else None
    if top_cluster and int(top_cluster["count"]) >= cluster_min_events:
        flags.append({"severity": "medium", "code": "timestamp_cluster", "message": f"{top_cluster['count']} Events in Minute {top_cluster['key']}"})
    if summary["huge_quantity_events"]:
        flags.append({"severity": "high", "code": "suspicious_reward_unit", "message": "Sehr grosse HNT/IOT/MOBILE-Rohmengen oder effektive Mengen"})
    return flags


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Aktivitaets-Plausibilitaetsaudit",
        "",
        f"Erstellt: `{report['created_at_utc']}`",
        f"Eventbasis: `{report['event_basis']}`",
        f"Gesamt-Events: `{report['total_events']}`",
        "",
        "## Zusammenfassung",
        "",
    ]
    for item in report["flag_summary"]:
        lines.append(f"- `{item['code']}`: {item['count']} Tage")
    if not report["flag_summary"]:
        lines.append("- Keine Flags.")
    lines.extend(["", "## Top-Tage nach Aktivitaet", ""])
    for day in report["top_days"]:
        flags = ", ".join(flag["code"] for flag in day["flags"]) or "keine"
        lines.append(
            f"- `{day['day']}`: `{day['event_count']}` Events, Derivate `{day['derivative_count']}`, "
            f"Referenz `{day['reference_count']}`, Primaer `{day['primary_count']}`, "
            f"Failed-Solana-0 `{day.get('failed_zero_solana_count', 0)}`, Flags: {flags}"
        )
    if report.get("selected_day"):
        day = report["selected_day"]
        lines.extend(["", f"## Detailtag {day['day']}", ""])
        lines.append(
            f"- Events: `{day['event_count']}`, Derivate: `{day['derivative_count']}`, "
            f"Referenz: `{day['reference_count']}`, Primaer: `{day['primary_count']}`, "
            f"Zero-Quantity: `{day['zero_quantity_count']}`, "
            f"Failed-Solana-0: `{day.get('failed_zero_solana_count', 0)}`"
        )
        lines.append(f"- Flags: {', '.join(flag['code'] for flag in day['flags']) or 'keine'}")
        for section, title in [
            ("source_counts", "Quellen"),
            ("event_type_counts", "Event-Typen"),
            ("source_file_counts", "Importdateien"),
            ("minute_clusters", "Minuten-Cluster"),
        ]:
            lines.extend(["", f"### {title}", ""])
            for row in day[section]:
                lines.append(f"- `{row['count']}` `{row['key']}`")
        lines.extend(["", "### Mengen nach Quelle/Typ", ""])
        for row in day["source_type_quantities"]:
            lines.append(
                f"- `{row['count']}` `{row['source']} / {row['event_type']}`: "
                f"in `{row['in']}`, out `{row['out']}`, unknown `{row['unknown']}`"
            )
        if day["huge_quantity_events"]:
            lines.extend(["", "### Auffaellige Reward-Mengen", ""])
            for row in day["huge_quantity_events"][:10]:
                lines.append(
                    f"- `{row['timestamp_utc']}` `{row['source']} / {row['event_type']}` "
                    f"`{row['asset']}` Rohmenge `{row['quantity']}`, effektiv `{row.get('effective_quantity', row['quantity'])}` "
                    f"Event `{row['event_id']}`"
                )
    lines.extend(
        [
            "",
            "## Bewertung",
            "",
            "- Hohe Aktivitaet bedeutet hier technische Import-Events, nicht automatisch manuelle Trades.",
            "- Derivate/Futures sollten im Dashboard getrennt von Spot/Transfers und Referenzimporten angezeigt werden.",
            "- Tage mit `suspicious_reward_unit` muessen fachlich geprueft werden, weil Rohunits sonst Bestand und Bewertung verfaelschen koennen.",
            "- `failed_zero_solana_tx` sind fehlgeschlagene On-Chain-Versuche mit 0 SOL-Delta; diese sollten nicht wie echte Transfers/Trades bewertet werden.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    raw_events = STORE.list_raw_events()
    adjusted_events, review_summary = apply_review_actions(raw_events)
    effective_events, override_count = apply_tax_event_overrides(adjusted_events)
    source_files = {row["source_file_id"]: row for row in STORE.list_source_file_summaries(limit=5000)}

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in effective_events:
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        day = _day(payload)
        if args.year and not day.startswith(str(args.year)):
            continue
        if day != "unknown":
            grouped[day].append(event)

    day_rows = []
    flag_counter: Counter[str] = Counter()
    for day, events in grouped.items():
        summary = _event_summary(events, source_files)
        flags = _day_flags(summary, min_day_events=args.min_day_events, cluster_min_events=args.cluster_min_events)
        for flag in flags:
            flag_counter[flag["code"]] += 1
        day_rows.append({"day": day, "flags": flags, **summary})
    day_rows.sort(key=lambda item: (int(item["event_count"]), item["day"]), reverse=True)

    selected_day = None
    if args.day:
        events = grouped.get(args.day, [])
        summary = _event_summary(events, source_files)
        selected_day = {
            "day": args.day,
            "flags": _day_flags(summary, min_day_events=args.min_day_events, cluster_min_events=args.cluster_min_events),
            **summary,
        }

    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "event_basis": "review_actions + tax_event_overrides",
        "total_events": len(effective_events),
        "review_action_summary": review_summary,
        "tax_event_override_count": override_count,
        "year": args.year,
        "flag_summary": [{"code": code, "count": count} for code, count in flag_counter.most_common()],
        "top_days": day_rows[: args.top_days],
        "flagged_days": [row for row in day_rows if row["flags"]][: args.max_flagged_days],
        "selected_day": selected_day,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueft Aktivitaets-Peaks und Import-Plausibilitaet.")
    parser.add_argument("--day", default="", help="Detailtag YYYY-MM-DD")
    parser.add_argument("--year", type=int, default=0, help="Optional nur ein Jahr pruefen")
    parser.add_argument("--top-days", type=int, default=25)
    parser.add_argument("--max-flagged-days", type=int, default=200)
    parser.add_argument("--min-day-events", type=int, default=150)
    parser.add_argument("--cluster-min-events", type=int, default=40)
    parser.add_argument("--output-md", default="")
    parser.add_argument("--output-json", default="")
    args = parser.parse_args()

    report = build_report(args)
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.output_md:
        Path(args.output_md).write_text(_render_markdown(report), encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
