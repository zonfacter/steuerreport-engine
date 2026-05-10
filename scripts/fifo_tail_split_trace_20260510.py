#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.core.processor import (  # noqa: E402
    Lot,
    TransferLotFragment,
    _to_spot_events,
    _transfer_links_by_event_id,
)
from tax_engine.fx.service import FallbackFxResolver  # noqa: E402
from tax_engine.ingestion.store import STORE  # noqa: E402
from tax_engine.integrations import filter_events_for_processing  # noqa: E402
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides  # noqa: E402
from tax_engine.queue.service import (  # noqa: E402
    attach_cached_usd_prices_to_reward_events,
    attach_cached_usd_prices_to_swap_in_events,
    attach_reference_usd_value_anchors,
    drop_exact_pionex_duplicate_events,
    drop_solscan_duplicates_when_solana_rpc_is_active,
)

CREATED_DATE = "2026-05-10"
OUT_JSON = ROOT / "var" / f"fifo_tail_split_trace_{CREATED_DATE}.json"
OUT_MD = ROOT / "docs" / f"211_FIFO_TAIL_SPLIT_TRACE_{CREATED_DATE}.md"

TARGETS = [
    {
        "label": "USDT 2022",
        "job_id": "3bf608f7-31c4-430c-855f-3a88dd123ed8",
        "tax_year": 2022,
        "asset": "USDT",
    },
    {
        "label": "JUP 2024",
        "job_id": "356890b8-99b7-4562-89d0-79f4aa21804c",
        "tax_year": 2024,
        "asset": "JUP",
    },
]


def main() -> int:
    STORE.initialize()
    report: dict[str, Any] = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "targets": [],
    }
    for target in TARGETS:
        report["targets"].append(trace_target(target))
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "doc": str(OUT_MD)}, ensure_ascii=False, indent=2))
    return 0


def trace_target(target: dict[str, Any]) -> dict[str, Any]:
    job = STORE.get_processing_job(str(target["job_id"]))
    if not job:
        raise RuntimeError(f"missing job {target['job_id']}")
    tax_lines = STORE.get_tax_lines(str(target["job_id"]))
    zero_lines = [
        line
        for line in tax_lines
        if str(line.get("asset")) == target["asset"]
        and dec(line.get("proceeds_eur")) > 0
        and dec(line.get("cost_basis_eur")) == 0
    ]
    source_event_ids = sorted({str(line.get("source_event_id") or "") for line in zero_lines if str(line.get("source_event_id") or "")})
    effective_events, pipeline_summary = build_effective_events(job.get("config") if isinstance(job.get("config"), dict) else {})
    traces = replay_fifo(
        effective_events=effective_events,
        tax_year=int(target["tax_year"]),
        target_asset=str(target["asset"]),
        target_source_event_ids=set(source_event_ids),
    )
    grouped_tax_lines: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in tax_lines:
        if str(line.get("asset")) != target["asset"]:
            continue
        if str(line.get("source_event_id") or "") in source_event_ids:
            grouped_tax_lines[str(line.get("source_event_id") or "")].append(slim_tax_line(line))

    for trace in traces:
        trace["tax_lines_for_source_event"] = grouped_tax_lines.get(trace["event_id"], [])

    return {
        **target,
        "job_status": job.get("status"),
        "job_updated_at_utc": job.get("updated_at_utc"),
        "zero_cost_lines": [slim_tax_line(line) for line in zero_lines],
        "zero_cost_source_event_ids": source_event_ids,
        "pipeline_summary": pipeline_summary,
        "traces": traces,
    }


def build_effective_events(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_raw_events = STORE.list_raw_events()
    raw_events, integration_filter_summary = filter_events_for_processing(all_raw_events, config)
    raw_events, pionex_duplicate_summary = drop_exact_pionex_duplicate_events(raw_events)
    raw_events, solscan_duplicate_summary = drop_solscan_duplicates_when_solana_rpc_is_active(raw_events)
    raw_events, valuation_anchor_summary = attach_reference_usd_value_anchors(raw_events, all_raw_events)
    raw_events, reward_price_summary = attach_cached_usd_prices_to_reward_events(raw_events)
    raw_events, swap_in_price_summary = attach_cached_usd_prices_to_swap_in_events(raw_events)
    adjusted_events, review_action_summary = apply_review_actions(raw_events)
    effective_events, override_count = apply_tax_event_overrides(adjusted_events)
    effective_events, fx_summary = FallbackFxResolver(fallback_rate="1").enrich_events_with_fx(effective_events)
    return effective_events, {
        "raw_count": len(all_raw_events),
        "after_integration_filter": len(raw_events),
        "effective_count": len(effective_events),
        "integration_filter_summary": integration_filter_summary,
        "pionex_duplicate_summary": pionex_duplicate_summary,
        "solscan_duplicate_summary": solscan_duplicate_summary,
        "valuation_anchor_summary": valuation_anchor_summary,
        "reward_price_summary": reward_price_summary,
        "swap_in_price_summary": swap_in_price_summary,
        "review_action_summary": review_action_summary,
        "override_count": override_count,
        "fx_summary_counts": {
            "unresolved_events": len(fx_summary.get("unresolved_events", [])) if isinstance(fx_summary, dict) else 0,
        },
    }


def replay_fifo(
    *,
    effective_events: list[dict[str, Any]],
    tax_year: int,
    target_asset: str,
    target_source_event_ids: set[str],
) -> list[dict[str, Any]]:
    transfer_matches = STORE.list_transfer_matches()
    spot_events, class_counts = _to_spot_events(effective_events, transfer_matches=transfer_matches)
    outbound_to_inbound, _ = _transfer_links_by_event_id(transfer_matches)
    pending_transfer_lots_by_inbound: dict[str, deque[TransferLotFragment]] = defaultdict(deque)
    lots_by_asset: dict[str, deque[Lot]] = defaultdict(deque)
    traces: list[dict[str, Any]] = []

    for event in spot_events:
        if event.timestamp.year > tax_year:
            continue

        if event.side == "buy":
            pending_fragments = pending_transfer_lots_by_inbound.get(event.unique_event_id)
            if event.event_class == "transfer" and pending_fragments:
                qty_left = event.qty
                while qty_left > Decimal("0") and pending_fragments:
                    fragment = pending_fragments[0]
                    matched_qty = min(qty_left, fragment.qty)
                    lots_by_asset[event.asset].append(
                        Lot(
                            buy_timestamp=fragment.buy_timestamp,
                            remaining_qty=matched_qty,
                            unit_cost_eur=fragment.unit_cost_eur,
                            source_event_id=fragment.source_event_id,
                            domain=fragment.domain,
                        )
                    )
                    fragment.qty -= matched_qty
                    qty_left -= matched_qty
                    if fragment.qty <= Decimal("0"):
                        pending_fragments.popleft()
                if qty_left <= Decimal("0"):
                    continue
            buy_qty = qty_left if event.event_class == "transfer" and pending_fragments else event.qty
            unit_cost = ((buy_qty * event.unit_price_eur) + event.fee_eur) / buy_qty if buy_qty > 0 else Decimal("0")
            lots_by_asset[event.asset].append(
                Lot(
                    buy_timestamp=event.timestamp,
                    remaining_qty=buy_qty,
                    unit_cost_eur=unit_cost,
                    source_event_id=event.unique_event_id,
                    domain=event.domain,
                )
            )
            continue

        is_target = event.unique_event_id in target_source_event_ids and event.asset == target_asset
        trace: dict[str, Any] | None = None
        if is_target:
            trace = {
                "event_id": event.unique_event_id,
                "timestamp_utc": event.timestamp.isoformat(),
                "asset": event.asset,
                "side": event.side,
                "event_class": event.event_class,
                "sell_qty": plain(event.qty),
                "unit_price_eur": plain(event.unit_price_eur),
                "lots_before_count": len(lots_by_asset[event.asset]),
                "lots_before_qty": plain(sum((lot.remaining_qty for lot in lots_by_asset[event.asset]), start=Decimal("0"))),
                "lots_before_head": [slim_lot(lot) for lot in list(lots_by_asset[event.asset])[:12]],
                "matched_lots": [],
                "fallback_zero_cost_qty": "0",
            }

        qty_to_sell = event.qty
        is_non_tax_transfer_out = event.side == "transfer_out"
        while qty_to_sell > Decimal("0"):
            if not lots_by_asset[event.asset]:
                fallback_qty = qty_to_sell
                if trace is not None:
                    trace["fallback_zero_cost_qty"] = plain(fallback_qty)
                qty_to_sell = Decimal("0")
                break

            current_lot = lots_by_asset[event.asset][0]
            matched_qty = min(qty_to_sell, current_lot.remaining_qty)
            if trace is not None:
                trace["matched_lots"].append(
                    {
                        "matched_qty": plain(matched_qty),
                        "lot_before_qty": plain(current_lot.remaining_qty),
                        "unit_cost_eur": plain(current_lot.unit_cost_eur),
                        "source_event_id": current_lot.source_event_id,
                        "buy_timestamp_utc": current_lot.buy_timestamp.isoformat(),
                        "domain": current_lot.domain,
                    }
                )
            if is_non_tax_transfer_out:
                inbound_event_id = outbound_to_inbound.get(event.unique_event_id)
                if inbound_event_id:
                    pending_transfer_lots_by_inbound[inbound_event_id].append(
                        TransferLotFragment(
                            buy_timestamp=current_lot.buy_timestamp,
                            qty=matched_qty,
                            unit_cost_eur=current_lot.unit_cost_eur,
                            source_event_id=current_lot.source_event_id,
                            domain=current_lot.domain,
                        )
                    )
            current_lot.remaining_qty -= matched_qty
            qty_to_sell -= matched_qty
            if current_lot.remaining_qty <= Decimal("0"):
                lots_by_asset[event.asset].popleft()

        if trace is not None:
            trace["lots_after_count"] = len(lots_by_asset[event.asset])
            trace["lots_after_qty"] = plain(sum((lot.remaining_qty for lot in lots_by_asset[event.asset]), start=Decimal("0")))
            trace["class_counts"] = class_counts
            traces.append(trace)

    return traces


def slim_tax_line(line: dict[str, Any]) -> dict[str, Any]:
    return {
        "line_no": line.get("line_no"),
        "asset": line.get("asset"),
        "qty": str(line.get("qty") or ""),
        "buy_timestamp_utc": str(line.get("buy_timestamp_utc") or ""),
        "sell_timestamp_utc": str(line.get("sell_timestamp_utc") or ""),
        "cost_basis_eur": str(line.get("cost_basis_eur") or ""),
        "proceeds_eur": str(line.get("proceeds_eur") or ""),
        "source_event_id": str(line.get("source_event_id") or ""),
        "lot_source_event_id": str(line.get("lot_source_event_id") or ""),
        "transfer_chain_id": str(line.get("transfer_chain_id") or ""),
    }


def slim_lot(lot: Lot) -> dict[str, Any]:
    return {
        "qty": plain(lot.remaining_qty),
        "unit_cost_eur": plain(lot.unit_cost_eur),
        "source_event_id": lot.source_event_id,
        "buy_timestamp_utc": lot.buy_timestamp.isoformat(),
        "domain": lot.domain,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# FIFO Tail-Split Trace - 2026-05-10",
        "",
        f"- Created UTC: `{report['created_at_utc']}`",
        "- Zweck: Pruefen, warum Zero-Cost-Restmengen entstehen, obwohl dasselbe Verkaufs-Event teilweise Cost Basis hat.",
        "",
    ]
    for target in report["targets"]:
        lines.extend(
            [
                f"## {target['label']}",
                "",
                f"- Job: `{target['job_id']}`",
                f"- Zero-Cost-Zeilen: `{len(target['zero_cost_lines'])}`",
                f"- Betroffene Source-Events: `{len(target['zero_cost_source_event_ids'])}`",
                "",
            ]
        )
        for trace in target["traces"]:
            lines.extend(
                [
                    f"### Event `{trace['event_id']}`",
                    "",
                    f"- Zeit: `{trace['timestamp_utc']}`",
                    f"- Verkaufte Menge: `{trace['sell_qty']} {trace['asset']}`",
                    f"- FIFO-Lots vorher: `{trace['lots_before_count']}` / `{trace['lots_before_qty']} {trace['asset']}`",
                    f"- Gematchte Lots: `{len(trace['matched_lots'])}`",
                    f"- Zero-Cost-Restmenge: `{trace['fallback_zero_cost_qty']} {trace['asset']}`",
                    f"- FIFO-Lots danach: `{trace['lots_after_count']}` / `{trace['lots_after_qty']} {trace['asset']}`",
                    "",
                    "Tax-Lines fuer dieses Source-Event:",
                    "",
                    "| Line | Menge | Cost Basis EUR | Erloes EUR | Lot Source |",
                    "|---:|---:|---:|---:|---|",
                ]
            )
            for line in trace.get("tax_lines_for_source_event", []):
                lines.append(
                    f"| {line['line_no']} | {line['qty']} | {line['cost_basis_eur']} | {line['proceeds_eur']} | `{line['lot_source_event_id'] or 'empty'}` |"
                )
            lines.extend(["", "FIFO-Lots vor dem Event (erste 12):", "", "| Menge | Unit Cost EUR | Zeit | Source Event |", "|---:|---:|---|---|"])
            for lot in trace.get("lots_before_head", []):
                lines.append(
                    f"| {lot['qty']} | {lot['unit_cost_eur']} | `{lot['buy_timestamp_utc']}` | `{lot['source_event_id']}` |"
                )
            lines.extend(["", "Gematchte Lots:", "", "| Menge | Unit Cost EUR | Zeit | Source Event |", "|---:|---:|---|---|"])
            for lot in trace.get("matched_lots", []):
                lines.append(
                    f"| {lot['matched_qty']} | {lot['unit_cost_eur']} | `{lot['buy_timestamp_utc']}` | `{lot['source_event_id']}` |"
                )
            lines.append("")
    lines.extend(
        [
            "## Bewertung",
            "",
            "- Zero-Cost-Tail-Splits entstehen, wenn der FIFO-Pool fuer das Asset innerhalb eines Verkaufs-Events erschoepft wird.",
            "- Ein Fix darf nicht am Verkaufs-Event ansetzen, sondern muss fehlende/ausgefilterte Inflows oder Transferlot-Fortschreibung vor diesem Zeitpunkt klaeren.",
        ]
    )
    return "\n".join(lines) + "\n"


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").replace(",", ""))
    except Exception:
        return Decimal("0")


def plain(value: Decimal) -> str:
    return value.normalize().to_eng_string() if value else "0"


if __name__ == "__main__":
    raise SystemExit(main())
