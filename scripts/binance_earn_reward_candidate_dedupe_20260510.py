#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE  # noqa: E402
from tax_engine.queue.service import apply_review_actions  # noqa: E402

RUN_DATE = "2026-05-10"
JSON_PATH = ROOT / "var" / f"binance_earn_reward_dedupe_{RUN_DATE}.json"
DOC_PATH = ROOT / "docs" / f"202_BINANCE_EARN_REWARD_DEDUPE_{RUN_DATE}.md"

REWARD_EVENT_TYPES = {
    "asset_dividend",
    "interest",
    "staking_reward",
    "reward_claim",
    "mining_reward",
}
TIME_TOLERANCE_SECONDS = 3600


@dataclass(frozen=True)
class RawReward:
    event_id: str
    source: str
    event_type: str
    asset: str
    quantity: Decimal
    timestamp_utc: str
    timestamp_epoch: int | None
    payload: dict[str, Any]


def main() -> None:
    STORE.initialize()
    raw_events, review_summary = apply_review_actions(STORE.list_raw_events())
    raw_rewards = collect_raw_rewards(raw_events)
    candidates = STORE.list_product_position_events(
        platform="binance",
        tax_treatment="reward_income_candidate",
        limit=100000,
    )
    matches, unmatched = match_candidates(candidates, raw_rewards)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "rules": {
            "time_tolerance_seconds": TIME_TOLERANCE_SECONDS,
            "match_basis": "asset + exact Decimal quantity + nearest timestamp within tolerance",
            "reward_event_types": sorted(REWARD_EVENT_TYPES),
            "raw_events_after_review_actions": True,
        },
        "review_summary": review_summary,
        "candidate_count": len(candidates),
        "raw_reward_count": len(raw_rewards),
        "matched_count": len(matches),
        "unmatched_count": len(unmatched),
        "matched_summary": summarize_matches(matches),
        "unmatched_summary": summarize_candidates(unmatched),
        "matches": matches,
        "unmatched": unmatched,
    }
    JSON_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": compact_summary(audit)}, indent=2, ensure_ascii=False))


def collect_raw_rewards(raw_events: list[dict[str, Any]]) -> list[RawReward]:
    rewards: list[RawReward] = []
    for event in raw_events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        event_type = str(payload.get("event_type") or "").strip()
        side = str(payload.get("side") or "").strip().lower()
        asset = str(payload.get("asset") or "").strip().upper()
        qty = dec(payload.get("quantity"))
        if event_type not in REWARD_EVENT_TYPES or side not in {"", "in"} or not asset or qty <= 0:
            continue
        timestamp_utc = normalize_ts(payload.get("timestamp_utc") or payload.get("timestamp"))
        rewards.append(
            RawReward(
                event_id=str(event.get("unique_event_id") or ""),
                source=str(payload.get("source") or ""),
                event_type=event_type,
                asset=asset,
                quantity=qty,
                timestamp_utc=timestamp_utc,
                timestamp_epoch=parse_epoch(timestamp_utc),
                payload=payload,
            )
        )
    return rewards


def match_candidates(candidates: list[dict[str, Any]], raw_rewards: list[RawReward]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    index: dict[tuple[str, Decimal], list[RawReward]] = defaultdict(list)
    for raw in raw_rewards:
        index[(raw.asset, raw.quantity)].append(raw)

    matches: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    used_raw_ids: set[str] = set()
    for candidate in candidates:
        asset = str(candidate.get("asset") or "").upper()
        qty = dec(candidate.get("quantity"))
        candidate_ts = normalize_ts(candidate.get("timestamp_utc"))
        candidate_epoch = parse_epoch(candidate_ts)
        nearest: tuple[int, RawReward] | None = None
        for raw in index.get((asset, qty), []):
            if raw.event_id in used_raw_ids:
                continue
            if candidate_epoch is None or raw.timestamp_epoch is None:
                continue
            diff = abs(candidate_epoch - raw.timestamp_epoch)
            if diff <= TIME_TOLERANCE_SECONDS and (nearest is None or diff < nearest[0]):
                nearest = (diff, raw)
        if nearest is None:
            unmatched.append(candidate_to_record(candidate))
            continue
        diff, raw = nearest
        used_raw_ids.add(raw.event_id)
        matches.append(
            {
                "candidate": candidate_to_record(candidate),
                "raw_event": {
                    "unique_event_id": raw.event_id,
                    "source": raw.source,
                    "event_type": raw.event_type,
                    "asset": raw.asset,
                    "quantity": raw.quantity.to_eng_string(),
                    "timestamp_utc": raw.timestamp_utc,
                    "tx_id": str(raw.payload.get("tx_id") or ""),
                },
                "time_diff_seconds": diff,
                "match_status": "existing_raw_event",
            }
        )
    return matches, unmatched


def candidate_to_record(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": str(candidate.get("event_id") or ""),
        "asset": str(candidate.get("asset") or "").upper(),
        "quantity": dec(candidate.get("quantity")).to_eng_string(),
        "timestamp_utc": normalize_ts(candidate.get("timestamp_utc")),
        "product_type": str(candidate.get("product_type") or ""),
        "product_id": str(candidate.get("product_id") or ""),
        "source_ref": str(candidate.get("source_ref") or ""),
    }


def summarize_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    by_year_asset: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    counts: Counter[tuple[str, str]] = Counter()
    for candidate in candidates:
        asset = str(candidate.get("asset") or "").upper()
        qty = dec(candidate.get("quantity"))
        year = normalize_ts(candidate.get("timestamp_utc"))[:4] or "unknown"
        totals[asset] += qty
        by_year_asset[year][asset] += qty
        counts[(year, asset)] += 1
    return {
        "asset_totals": {asset: value.to_eng_string() for asset, value in sorted(totals.items())},
        "year_asset_totals": {
            year: {asset: value.to_eng_string() for asset, value in sorted(asset_totals.items())}
            for year, asset_totals in sorted(by_year_asset.items())
        },
        "year_asset_counts": {f"{year}:{asset}": count for (year, asset), count in sorted(counts.items())},
    }


def summarize_matches(matches: list[dict[str, Any]]) -> dict[str, Any]:
    by_raw_source: Counter[str] = Counter()
    candidates = []
    for match in matches:
        raw = match.get("raw_event", {})
        by_raw_source[f"{raw.get('source')}:{raw.get('event_type')}"] += 1
        candidates.append(match.get("candidate", {}))
    return {
        "by_raw_source_event_type": dict(sorted(by_raw_source.items())),
        **summarize_candidates(candidates),
    }


def compact_summary(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_count": audit["candidate_count"],
        "matched_count": audit["matched_count"],
        "unmatched_count": audit["unmatched_count"],
        "matched_asset_totals": audit["matched_summary"].get("asset_totals", {}),
        "unmatched_asset_totals": audit["unmatched_summary"].get("asset_totals", {}),
    }


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Binance Earn Reward Dedupe",
        "",
        f"Stand: {audit['created_at_utc']}",
        "",
        "## Ziel",
        "",
        "Die Tabelle `product_position_events` enthaelt Binance-Earn-Rewards zunaechst nur als Kandidaten. Dieses Audit prueft, welche Kandidaten bereits als steuerlich relevante Rohereignisse in `raw_events` vorhanden sind.",
        "",
        "## Match-Regel",
        "",
        f"- Asset gleich, Betrag exakt gleich, Zeitdifferenz maximal `{audit['rules']['time_tolerance_seconds']}` Sekunden.",
        "- Rohereignisse werden nach Review-Actions gelesen, damit bereits ausgeschlossene Referenzen nicht erneut zaehlen.",
        "- Kein automatischer Import in diesem Schritt; Ergebnis ist ein Beleg- und Entscheidungsprotokoll.",
        "",
        "## Ergebnis",
        "",
        f"- Reward-Kandidaten: `{audit['candidate_count']}`",
        f"- Bereits in `raw_events` gefunden: `{audit['matched_count']}`",
        f"- Noch offen: `{audit['unmatched_count']}`",
        "",
        "### Gefundene Rewards nach Quelle",
        "",
        "| Quelle/Event-Type | Anzahl |",
        "|---|---:|",
    ]
    for key, count in audit["matched_summary"].get("by_raw_source_event_type", {}).items():
        lines.append(f"| `{key}` | `{count}` |")

    lines.extend(["", "### Gefundene Reward-Mengen", "", "| Asset | Menge |", "|---|---:|"])
    for asset, total in audit["matched_summary"].get("asset_totals", {}).items():
        lines.append(f"| `{asset}` | `{total}` |")

    lines.extend(["", "### Offene Reward-Mengen", "", "| Asset | Menge |", "|---|---:|"])
    for asset, total in audit["unmatched_summary"].get("asset_totals", {}).items():
        lines.append(f"| `{asset}` | `{total}` |")

    lines.extend(["", "### Offene Rewards nach Jahr/Asset", "", "| Jahr | Asset | Anzahl | Menge |", "|---|---|---:|---:|"])
    counts = audit["unmatched_summary"].get("year_asset_counts", {})
    totals = audit["unmatched_summary"].get("year_asset_totals", {})
    for year, asset_totals in totals.items():
        for asset, total in asset_totals.items():
            lines.append(f"| `{year}` | `{asset}` | `{counts.get(f'{year}:{asset}', 0)}` | `{total}` |")

    lines.extend(
        [
            "",
            "## Naechste Umsetzung",
            "",
            "- Kandidaten mit Match bleiben reine Produktpositions-Referenz und duerfen nicht erneut als Einkommen importiert werden.",
            "- Offene Kandidaten sind Import-Kandidaten fuer `raw_events` als `interest`/`side=in`, sobald Preis-/EUR-Bewertung hinterlegt ist.",
            "- Fuer Principal-Bewegungen bleibt `tax_treatment=non_taxable_principal_movement`; sie duerfen FIFO nicht als Kauf/Verkauf veraendern.",
            "",
        ]
    )
    return "\n".join(lines)


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def normalize_ts(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw).astimezone(UTC).isoformat()
    except ValueError:
        return raw


def parse_epoch(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(datetime.fromisoformat(value).astimezone(UTC).timestamp())
    except ValueError:
        return None


if __name__ == "__main__":
    main()
