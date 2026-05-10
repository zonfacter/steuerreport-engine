#!/usr/bin/env python3
"""Audit private vs business lot origin for crypto holdings and disposals."""

from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from tax_engine.core.processor import (  # noqa: E402
    STABLE_ASSETS,
    _classify,
    _extract_asset,
    _extract_fee_eur,
    _extract_qty,
    _extract_side,
    _extract_timestamp,
    _extract_unit_price_eur,
    _infer_unit_price_eur,
)
from tax_engine.core.tax_domains import _is_business_override, _is_reward_like  # noqa: E402
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
OUT_JSON = ROOT / "var" / f"business_private_lot_audit_{CREATED_DATE}.json"
OUT_MD = ROOT / "docs" / f"197_BUSINESS_PRIVATE_LOT_AUDIT_{CREATED_DATE}.md"
FOCUS_ASSETS = {"HNT", "IOT", "SOL", "JUP", "MOBILE", "USDT"}


@dataclass(slots=True)
class AuditEvent:
    event_id: str
    timestamp: datetime
    asset: str
    side: str
    qty: Decimal
    unit_price_eur: Decimal
    fee_eur: Decimal
    event_class: str
    source: str
    event_type: str
    domain: str


@dataclass(slots=True)
class AuditLot:
    acquired_at: datetime
    remaining_qty: Decimal
    unit_cost_eur: Decimal
    source_event_id: str
    domain: str
    source: str
    event_type: str


def main() -> None:
    raw_events = STORE.list_raw_events()
    effective_events, processing_summary = _effective_processing_events_for_audit(raw_events)
    events = _to_audit_events(effective_events)
    simulation = _simulate(events)
    latest_jobs = _latest_jobs_by_year()
    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "read_only_audit",
        "basis": "processing_pipeline_effective_events_fifo_domain_simulation",
        "processing_summary": processing_summary,
        "latest_jobs": latest_jobs,
        "summary": _summary(simulation),
        "open_lots_by_asset_domain": simulation["open_lots_by_asset_domain"],
        "business_origin_disposals_by_year": simulation["business_origin_disposals_by_year"],
        "focus_open_lots_by_asset_domain": _focus_open_lots(simulation),
        "focus_business_origin_disposals_by_asset_year": _focus_business_disposals(simulation),
        "mixed_assets": simulation["mixed_assets"],
        "important_notes": [
            "Reward-/Mining-nahe Zufluesse werden als Betriebsvermoegen markiert.",
            "Spaetere Verkaeufe/Swaps aus solchen Lots bleiben Betriebsvermoegen, solange keine dokumentierte Entnahme ins Privatvermoegen existiert.",
            "Private Kauf-/Swap-Lots bleiben Privatvermoegen.",
            "Transferketten propagieren die Herkunftsdomain noch nicht automatisch ueber Plattformgrenzen.",
            "Diese Auswertung ist read-only und aendert keine Steuerzeilen.",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_render_doc(report), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "doc": str(OUT_MD)}, ensure_ascii=False, indent=2))


def _effective_processing_events_for_audit(raw_events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    filtered, integration_filter_summary = filter_events_for_processing(raw_events, {"include_reference_sources": False})
    deduped_pionex, pionex_duplicate_summary = drop_exact_pionex_duplicate_events(filtered)
    deduped_solscan, solscan_duplicate_summary = drop_solscan_duplicates_when_solana_rpc_is_active(deduped_pionex)
    anchored, valuation_anchor_summary = attach_reference_usd_value_anchors(deduped_solscan, raw_events)
    reward_priced, reward_price_summary = attach_cached_usd_prices_to_reward_events(anchored)
    swap_priced, swap_price_summary = attach_cached_usd_prices_to_swap_in_events(reward_priced)
    reviewed, review_action_summary = apply_review_actions(swap_priced)
    overridden, override_count = apply_tax_event_overrides(reviewed)
    fx_enriched, fx_summary = FallbackFxResolver(fallback_rate="1").enrich_events_with_fx(overridden)
    return fx_enriched, {
        "basis": "processing_pipeline_event_basis_with_reward_swap_fx_enrichment",
        "integration_filter": integration_filter_summary,
        "pionex_dedupe": pionex_duplicate_summary,
        "solscan_dedupe": solscan_duplicate_summary,
        "valuation_anchors": valuation_anchor_summary,
        "reward_prices": reward_price_summary,
        "swap_prices": swap_price_summary,
        "review_actions": review_action_summary,
        "tax_event_override_count": override_count,
        "fx_enrichment": fx_summary,
    }


def _to_audit_events(rows: list[dict[str, Any]]) -> list[AuditEvent]:
    events: list[AuditEvent] = []
    for row in rows:
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        event_class = _classify(payload)
        asset = _extract_asset(payload)
        side = _extract_side(payload, _extract_qty(payload))
        is_stable_transfer = event_class == "transfer" and asset in (STABLE_ASSETS - {"EUR"})
        if event_class not in {"spot", "reward"} and not is_stable_transfer:
            continue
        ts = _extract_timestamp(payload)
        qty = _extract_qty(payload)
        if ts is None or qty <= 0:
            continue
        if event_class == "reward" and side != "buy":
            continue
        if event_class == "transfer" and side == "sell":
            side = "transfer_out"
        domain = _domain_for_acquisition(payload, event_class)
        events.append(
            AuditEvent(
                event_id=str(row.get("unique_event_id") or ""),
                timestamp=ts,
                asset=asset,
                side=side,
                qty=qty,
                unit_price_eur=_infer_unit_price_eur(
                    payload=payload,
                    asset=asset,
                    qty=qty,
                    base_price=_extract_unit_price_eur(payload),
                ),
                fee_eur=_extract_fee_eur(payload),
                event_class=event_class,
                source=str(payload.get("source") or ""),
                event_type=str(payload.get("event_type") or ""),
                domain=domain,
            )
        )
    events.sort(key=lambda item: (item.timestamp, 0 if item.side == "buy" else 1, item.event_id))
    return events


def _domain_for_acquisition(payload: dict[str, Any], event_class: str) -> str:
    if _is_business_override(payload):
        return "business"
    if event_class == "reward" or _is_reward_like(payload):
        return "business"
    return "private"


def _simulate(events: list[AuditEvent]) -> dict[str, Any]:
    lots_by_asset: dict[str, deque[AuditLot]] = defaultdict(deque)
    disposals_by_year: dict[str, list[dict[str, Any]]] = defaultdict(list)
    shortfalls: list[dict[str, Any]] = []

    for event in events:
        if event.side == "buy":
            total_cost = event.qty * event.unit_price_eur + event.fee_eur
            unit_cost = total_cost / event.qty if event.qty else Decimal("0")
            lots_by_asset[event.asset].append(
                AuditLot(
                    acquired_at=event.timestamp,
                    remaining_qty=event.qty,
                    unit_cost_eur=unit_cost,
                    source_event_id=event.event_id,
                    domain=event.domain,
                    source=event.source,
                    event_type=event.event_type,
                )
            )
            continue

        qty_left = event.qty
        non_tax_transfer = event.side == "transfer_out"
        total_proceeds = Decimal("0") if non_tax_transfer else event.qty * event.unit_price_eur - event.fee_eur
        unit_proceeds = total_proceeds / event.qty if event.qty else Decimal("0")
        while qty_left > 0:
            if not lots_by_asset[event.asset]:
                shortfalls.append(
                    {
                        "timestamp": event.timestamp.isoformat(),
                        "asset": event.asset,
                        "qty": _plain(qty_left),
                        "sell_event_id": event.event_id,
                        "source": event.source,
                        "event_type": event.event_type,
                    }
                )
                break
            lot = lots_by_asset[event.asset][0]
            matched = min(qty_left, lot.remaining_qty)
            if not non_tax_transfer and lot.domain == "business":
                disposals_by_year[str(event.timestamp.year)].append(
                    {
                        "timestamp": event.timestamp.isoformat(),
                        "asset": event.asset,
                        "qty": _plain(matched),
                        "proceeds_eur": _plain(matched * unit_proceeds),
                        "cost_basis_eur": _plain(matched * lot.unit_cost_eur),
                        "gain_loss_eur": _plain((matched * unit_proceeds) - (matched * lot.unit_cost_eur)),
                        "sell_event_id": event.event_id,
                        "lot_source_event_id": lot.source_event_id,
                        "lot_acquired_at": lot.acquired_at.isoformat(),
                        "lot_source": lot.source,
                        "lot_event_type": lot.event_type,
                        "sell_source": event.source,
                        "sell_event_type": event.event_type,
                    }
                )
            lot.remaining_qty -= matched
            qty_left -= matched
            if lot.remaining_qty <= 0:
                lots_by_asset[event.asset].popleft()

    open_lots = []
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for asset, lots in lots_by_asset.items():
        for lot in lots:
            key = (asset, lot.domain)
            item = grouped.setdefault(
                key,
                {
                    "asset": asset,
                    "domain": lot.domain,
                    "qty": Decimal("0"),
                    "cost_basis_eur": Decimal("0"),
                    "lot_count": 0,
                    "oldest_acquired_at": lot.acquired_at.isoformat(),
                    "sample_lots": [],
                },
            )
            item["qty"] += lot.remaining_qty
            item["cost_basis_eur"] += lot.remaining_qty * lot.unit_cost_eur
            item["lot_count"] += 1
            if lot.acquired_at.isoformat() < item["oldest_acquired_at"]:
                item["oldest_acquired_at"] = lot.acquired_at.isoformat()
            if len(item["sample_lots"]) < 5:
                item["sample_lots"].append(
                    {
                        "acquired_at": lot.acquired_at.isoformat(),
                        "qty": _plain(lot.remaining_qty),
                        "unit_cost_eur": _plain(lot.unit_cost_eur),
                        "source_event_id": lot.source_event_id,
                        "source": lot.source,
                        "event_type": lot.event_type,
                    }
                )
    for item in grouped.values():
        item["qty"] = _plain(item["qty"])
        item["cost_basis_eur"] = _plain(item["cost_basis_eur"])
        open_lots.append(item)
    open_lots.sort(key=lambda row: (row["asset"], row["domain"]))

    assets_with_domains: defaultdict[str, set[str]] = defaultdict(set)
    for item in open_lots:
        assets_with_domains[item["asset"]].add(item["domain"])
    mixed_assets = [
        {"asset": asset, "domains": sorted(domains)}
        for asset, domains in sorted(assets_with_domains.items())
        if len(domains) > 1
    ]

    return {
        "open_lots_by_asset_domain": open_lots,
        "business_origin_disposals_by_year": {year: rows for year, rows in sorted(disposals_by_year.items())},
        "mixed_assets": mixed_assets,
        "shortfalls": shortfalls[:100],
        "shortfall_count": len(shortfalls),
    }


def _summary(simulation: dict[str, Any]) -> dict[str, Any]:
    open_rows = simulation["open_lots_by_asset_domain"]
    disposal_rows = [row for rows in simulation["business_origin_disposals_by_year"].values() for row in rows]
    business_open = [row for row in open_rows if row["domain"] == "business"]
    private_open = [row for row in open_rows if row["domain"] == "private"]
    by_year: dict[str, dict[str, str]] = {}
    for year, rows in simulation["business_origin_disposals_by_year"].items():
        by_year[year] = {
            "line_count": str(len(rows)),
            "proceeds_eur": _plain(sum((_dec(row["proceeds_eur"]) for row in rows), Decimal("0"))),
            "cost_basis_eur": _plain(sum((_dec(row["cost_basis_eur"]) for row in rows), Decimal("0"))),
            "gain_loss_eur": _plain(sum((_dec(row["gain_loss_eur"]) for row in rows), Decimal("0"))),
        }
    return {
        "open_business_asset_count": len({row["asset"] for row in business_open}),
        "open_private_asset_count": len({row["asset"] for row in private_open}),
        "open_mixed_asset_count": len(simulation["mixed_assets"]),
        "business_origin_disposal_count": len(disposal_rows),
        "business_origin_disposals_by_year": by_year,
        "shortfall_count": simulation.get("shortfall_count", 0),
    }


def _focus_open_lots(simulation: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        row
        for row in simulation["open_lots_by_asset_domain"]
        if row["asset"] in FOCUS_ASSETS or row["domain"] == "business"
    ]
    return sorted(rows, key=lambda row: (row["asset"], row["domain"]))


def _focus_business_disposals(simulation: dict[str, Any]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for year, rows in simulation["business_origin_disposals_by_year"].items():
        for row in rows:
            asset = str(row["asset"])
            if asset not in FOCUS_ASSETS:
                continue
            key = (year, asset)
            item = grouped.setdefault(
                key,
                {
                    "year": year,
                    "asset": asset,
                    "line_count": 0,
                    "proceeds_eur": Decimal("0"),
                    "cost_basis_eur": Decimal("0"),
                    "gain_loss_eur": Decimal("0"),
                },
            )
            item["line_count"] += 1
            item["proceeds_eur"] += _dec(row["proceeds_eur"])
            item["cost_basis_eur"] += _dec(row["cost_basis_eur"])
            item["gain_loss_eur"] += _dec(row["gain_loss_eur"])
    result = []
    for item in grouped.values():
        result.append(
            {
                "year": str(item["year"]),
                "asset": str(item["asset"]),
                "line_count": str(item["line_count"]),
                "proceeds_eur": _plain(item["proceeds_eur"]),
                "cost_basis_eur": _plain(item["cost_basis_eur"]),
                "gain_loss_eur": _plain(item["gain_loss_eur"]),
            }
        )
    return sorted(result, key=lambda row: (row["year"], row["asset"]))


def _latest_jobs_by_year() -> dict[str, str]:
    latest: dict[str, dict[str, Any]] = {}
    for job in STORE.list_processing_jobs(status="completed", limit=10000):
        year = str(job.get("tax_year") or "")
        if not year:
            continue
        if year not in latest or str(job.get("updated_at_utc") or "") > str(latest[year].get("updated_at_utc") or ""):
            latest[year] = job
    return {year: str(job.get("job_id") or "") for year, job in sorted(latest.items())}


def _render_doc(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Betriebsvermoegen vs Privatvermoegen Lot-Audit",
        "",
        f"Stand: {CREATED_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Status: `{report['status']}`",
        f"- Offene Business-Assets: `{summary['open_business_asset_count']}`",
        f"- Offene Private-Assets: `{summary['open_private_asset_count']}`",
        f"- Assets mit gemischten offenen Lots: `{summary['open_mixed_asset_count']}`",
        f"- Verkaeufe/Swaps aus Business-Origin-Lots: `{summary['business_origin_disposal_count']}`",
        f"- Shortfall-Hinweise in dieser Simulation: `{summary['shortfall_count']}`",
        "",
        "## Interpretation",
        "",
        "- Mining-/Reward-Lots bleiben Betriebsvermoegen, bis eine Entnahme ins Privatvermoegen dokumentiert wird.",
        "- Private Trading-Lots bleiben Privatvermoegen.",
        "- Wenn ein Verkauf/Swap aus einem Business-Origin-Lot bedient wurde, sollte dieser Vorgang nicht als private §23-Zeile behandelt werden.",
        "- Die Solana-Wallet ist nicht automatisch insgesamt Betriebsvermoegen; entscheidend ist die Herkunft der verbrauchten FIFO-Lots.",
        "- Diese Auswertung ist read-only; die aktuelle Steuerlogik wurde dadurch noch nicht umgebucht.",
        "",
        "## Fokus Solana/HNT/IOT",
        "",
        "| Asset | Herkunft | Menge | Kostenbasis EUR | Lots | Aeltester Erwerb |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in report["focus_open_lots_by_asset_domain"]:
        lines.append(
            f"| `{row['asset']}` | `{row['domain']}` | {row['qty']} | {row['cost_basis_eur']} | {row['lot_count']} | `{row['oldest_acquired_at']}` |"
        )
    lines += [
        "",
        "## Fokus Business-Origin-Verkaeufe/Swaps",
        "",
        "| Jahr | Asset | Zeilen | Erloes EUR | Kostenbasis EUR | Gewinn/Verlust EUR |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in report["focus_business_origin_disposals_by_asset_year"]:
        lines.append(
            f"| {row['year']} | `{row['asset']}` | {row['line_count']} | {row['proceeds_eur']} | {row['cost_basis_eur']} | {row['gain_loss_eur']} |"
        )
    lines += [
        "",
        "## Offene Lots nach Herkunft",
        "",
        "| Asset | Herkunft | Menge | Kostenbasis EUR | Lots | Aeltester Erwerb |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in report["open_lots_by_asset_domain"]:
        lines.append(
            f"| `{row['asset']}` | `{row['domain']}` | {row['qty']} | {row['cost_basis_eur']} | {row['lot_count']} | `{row['oldest_acquired_at']}` |"
        )
    lines += ["", "## Gemischte offene Assets", ""]
    if report["mixed_assets"]:
        for row in report["mixed_assets"]:
            lines.append(f"- `{row['asset']}`: {', '.join(row['domains'])}")
    else:
        lines.append("- Keine offenen Assets mit gleichzeitig privaten und gewerblichen Lots.")
    lines += ["", "## Business-Origin-Verkaeufe/Swaps nach Jahr", ""]
    by_year = summary["business_origin_disposals_by_year"]
    lines += ["| Jahr | Zeilen | Erloes EUR | Kostenbasis EUR | Gewinn/Verlust EUR |", "|---:|---:|---:|---:|---:|"]
    for year, row in by_year.items():
        lines.append(
            f"| {year} | {row['line_count']} | {row['proceeds_eur']} | {row['cost_basis_eur']} | {row['gain_loss_eur']} |"
        )
    lines += ["", "## Beispiele Business-Origin-Verkaeufe/Swaps", ""]
    examples = [
        item
        for rows in report["business_origin_disposals_by_year"].values()
        for item in rows
        if item["asset"] in FOCUS_ASSETS
    ][:20]
    for item in examples:
        lines.append(
            f"- `{item['timestamp']}` `{item['asset']}` qty `{item['qty']}` G/V `{item['gain_loss_eur']}` "
            f"Lot `{item['lot_source_event_id']}` ({item['lot_source']}/{item['lot_event_type']}) "
            f"-> Sell `{item['sell_event_id']}` ({item['sell_source']}/{item['sell_event_type']})"
        )
    lines += [
        "",
        "## Grenzen dieser Auswertung",
        "",
        "- Transfer-Outs verbrauchen zwar FIFO-Lots; Transfer-Ins auf einer anderen Plattform tragen die Herkunftsdomain aktuell noch nicht automatisch weiter.",
        "- Es gibt noch keine Entnahme-Events. Ohne dokumentierte Entnahme bleibt ein Reward-/Mining-Lot in dieser Sicht Betriebsvermoegen.",
        "- Shortfalls zeigen, dass einzelne historische Bewegungen weiterhin nicht vollstaendig gedeckt sind.",
    ]
    lines += [
        "",
        "## Naechste technische Konsequenz",
        "",
        "- Steuerlogik erweitern: Lots muessen eine Domain tragen (`business`/`private`).",
        "- Transfer-Matching erweitern: Domain beim Transfer von Quelle zu Ziel fortschreiben.",
        "- Tax-Lines aus Business-Lots muessen als EÜR-/Business-Verkaeufe oder separater Business-Disposal-Export erscheinen.",
        "- Optional: Entnahme-Event modellieren, falls ein gewerblicher Reward bewusst ins Privatvermoegen ueberfuehrt wurde.",
        "",
        f"JSON: `{OUT_JSON.relative_to(ROOT)}`",
    ]
    return "\n".join(lines) + "\n"


def _dec(value: Any) -> Decimal:
    return Decimal(str(value or "0"))


def _plain(value: Any) -> str:
    value_dec = _dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


if __name__ == "__main__":
    main()
