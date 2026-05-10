#!/usr/bin/env python3
"""Audit assets that go negative temporarily even when their final balance is non-negative."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from chronological_balance_break_audit import (  # noqa: E402
    _context_for_asset,
    _decimal,
    _effective_events,
    _load_ignored_tokens,
    _load_token_aliases,
    _movement_sort_key,
    _movements,
    _plain,
    _slim_movement,
    _year,
)

CREATED_DATE = "2026-05-09"
JSON_PATH = ROOT / "var" / f"transient_balance_undercoverage_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"119_TRANSIENT_BALANCE_UNDERCOVERAGE_AUDIT_{CREATED_DATE}.md"
DUST_UNDERCOVERAGE_TOLERANCE = Decimal("0.000001")
FIAT_ASSETS = {"EUR", "USD", "GBP", "CHF"}


def main() -> None:
    events = _effective_events()
    token_aliases = _load_token_aliases()
    ignored_mints = set(_load_ignored_tokens().keys())
    movements = [
        movement
        for row in events
        for movement in _movements(row, token_aliases=token_aliases, ignored_mints=ignored_mints)
    ]
    movements = [row for row in movements if _year(row["timestamp"]) >= 2020]
    movements.sort(key=_movement_sort_key)
    audit = build_audit(movements)
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "transient_assets": audit["transient_asset_count"], "top": [(r["asset"], r["worst_balance"]["balance_after"]) for r in audit["asset_reports"][:10]]}, ensure_ascii=False, indent=2))


def build_audit(movements: list[dict[str, Any]]) -> dict[str, Any]:
    balances: dict[str, Decimal] = defaultdict(Decimal)
    first_negative: dict[str, dict[str, Any]] = {}
    worst_balance: dict[str, dict[str, Any]] = {}
    event_count: Counter[str] = Counter()
    yearly_net: dict[str, dict[int, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    source_net: dict[str, Counter[tuple[str, str, str]]] = defaultdict(Counter)
    movement_by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in movements:
        asset = row["asset"]
        before = balances[asset]
        after = before + row["delta"]
        balances[asset] = after
        row["balance_before"] = before
        row["balance_after"] = after
        event_count[asset] += 1
        yearly_net[asset][row["year"]] += row["delta"]
        source_net[asset][(row["source"], row["event_type"], row["side"])] += row["delta"]
        movement_by_asset[asset].append(row)
        if before >= 0 > after and asset not in first_negative:
            first_negative[asset] = _slim_movement(row)
        current = worst_balance.get(asset)
        if current is None or after < _decimal(current["balance_after"]):
            worst_balance[asset] = _slim_movement(row)

    reports = []
    ignored_dust_undercoverage = []
    fiat_undercoverage = []
    for asset, first in first_negative.items():
        final_balance = balances[asset]
        worst = worst_balance[asset]
        worst_after = _decimal(worst["balance_after"])
        if worst_after >= 0:
            continue
        if asset in FIAT_ASSETS:
            fiat_undercoverage.append(
                {
                    "asset": asset,
                    "final_balance": _plain(final_balance),
                    "event_count": event_count[asset],
                    "first_negative": first,
                    "worst_balance": worst,
                    "yearly_net": {str(year): _plain(value) for year, value in sorted(yearly_net[asset].items())},
                    "source_net_top": [
                        {"source": key[0], "event_type": key[1], "side": key[2], "net": _plain(value)}
                        for key, value in sorted(source_net[asset].items(), key=lambda item: abs(item[1]), reverse=True)[:20]
                    ],
                    "context": _context_for_asset(movement_by_asset[asset], focus_ts=str(first.get("timestamp") or ""), days=7),
                }
            )
            continue
        if abs(worst_after) <= DUST_UNDERCOVERAGE_TOLERANCE:
            ignored_dust_undercoverage.append(
                {
                    "asset": asset,
                    "final_balance": _plain(final_balance),
                    "event_count": event_count[asset],
                    "first_negative": first,
                    "worst_balance": worst,
                    "tolerance": _plain(DUST_UNDERCOVERAGE_TOLERANCE),
                }
            )
            continue
        reports.append(
            {
                "asset": asset,
                "final_balance": _plain(final_balance),
                "event_count": event_count[asset],
                "first_negative": first,
                "worst_balance": worst,
                "yearly_net": {str(year): _plain(value) for year, value in sorted(yearly_net[asset].items())},
                "source_net_top": [
                    {"source": key[0], "event_type": key[1], "side": key[2], "net": _plain(value)}
                    for key, value in sorted(source_net[asset].items(), key=lambda item: abs(item[1]), reverse=True)[:20]
                ],
                "context": _context_for_asset(movement_by_asset[asset], focus_ts=str(first.get("timestamp") or ""), days=7),
            }
        )
    reports.sort(
        key=lambda row: (
            abs(_decimal(row["worst_balance"]["balance_after"])),
            abs(_decimal(row["final_balance"])),
            int(row["event_count"]),
        ),
        reverse=True,
    )
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "movement_count": len(movements),
        "asset_count": len(balances),
        "transient_asset_count": len(reports),
        "dust_tolerance": _plain(DUST_UNDERCOVERAGE_TOLERANCE),
        "ignored_dust_undercoverage_count": len(ignored_dust_undercoverage),
        "ignored_dust_undercoverage": ignored_dust_undercoverage,
        "fiat_undercoverage_count": len(fiat_undercoverage),
        "fiat_undercoverage": fiat_undercoverage,
        "asset_reports": reports,
    }


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Transient Balance Undercoverage Audit - 2026-05-09",
        "",
        "## Überblick",
        "",
        f"- Bewegungen: `{audit['movement_count']}`",
        f"- Assets: `{audit['asset_count']}`",
        f"- Assets mit zwischenzeitlicher Unterdeckung: `{audit['transient_asset_count']}`",
        f"- Dust-Toleranz: `{audit['dust_tolerance']}`",
        f"- Ignorierte Dust-Unterdeckungen: `{audit['ignored_dust_undercoverage_count']}`",
        f"- Separat dokumentierte Fiat-Cash-Unterdeckungen: `{audit['fiat_undercoverage_count']}`",
        "",
        "## Top Findings",
        "",
    ]
    for report in audit["asset_reports"][:30]:
        first = report["first_negative"]
        worst = report["worst_balance"]
        lines += [
            f"### {report['asset']}",
            "",
            f"- Final Balance: `{report['final_balance']}`",
            f"- Events: `{report['event_count']}`",
            f"- Erster Bruch: `{first.get('timestamp', '')}` `{first.get('source', '')}` / `{first.get('event_type', '')}` / `{first.get('side', '')}` delta `{first.get('delta', '')}` after `{first.get('balance_after', '')}`",
            f"- Schlimmster Stand: `{worst.get('balance_after', '')}` am `{worst.get('timestamp', '')}`",
            f"- Jahres-Netto: `{report['yearly_net']}`",
            f"- Top Quellen: `{report['source_net_top'][:8]}`",
            "",
        ]
    lines += [
        "## Fiat-Cash-Unterdeckungen",
        "",
    ]
    if audit["fiat_undercoverage"]:
        for item in audit["fiat_undercoverage"]:
            first = item["first_negative"]
            worst = item["worst_balance"]
            lines += [
                f"### {item['asset']}",
                "",
                f"- Final Balance: `{item['final_balance']}`",
                f"- Erster Bruch: `{first.get('timestamp', '')}` `{first.get('source', '')}` / `{first.get('event_type', '')}` / `{first.get('side', '')}` delta `{first.get('delta', '')}` after `{first.get('balance_after', '')}`",
                f"- Schlimmster Stand: `{worst.get('balance_after', '')}` am `{worst.get('timestamp', '')}`",
                f"- Jahres-Netto: `{item['yearly_net']}`",
                f"- Top Quellen: `{item['source_net_top'][:8]}`",
                "",
            ]
    else:
        lines.append("- Keine.")
    lines += [
        "",
        "## Ignorierte Dust-Unterdeckungen",
        "",
    ]
    if audit["ignored_dust_undercoverage"]:
        for item in audit["ignored_dust_undercoverage"][:30]:
            worst = item["worst_balance"]
            lines.append(
                f"- `{item['asset']}` worst `{worst.get('balance_after', '')}` am `{worst.get('timestamp', '')}` "
                f"(Toleranz `{item['tolerance']}`)"
            )
    else:
        lines.append("- Keine.")
    lines += [
        "",
        "## Bewertung",
        "",
        "- Dieser Report ist ein Chronologie-Audit: Endbestände können positiv sein, obwohl die Reihenfolge oder fehlende Transfers temporär negativ wird.",
        "- Fiat-Cash-Unterdeckungen werden separat dokumentiert, weil Kreditkarte/Apple Pay/Bankzahlungen externe Zahlungswege sind und keine Crypto-Asset-Deckung beweisen muessen.",
        "- Unterdeckungen bis zur Dust-Toleranz werden dokumentiert, aber nicht als offener Fehler gezählt.",
        "- Keine automatische Korrektur. Die Top-Fälle müssen je Asset gegen Primary-/Reference-Quellen entschieden werden.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
