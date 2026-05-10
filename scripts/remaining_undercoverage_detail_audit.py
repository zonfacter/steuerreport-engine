#!/usr/bin/env python3
"""Create a focused detail report for remaining material transient undercoverage."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from chronological_balance_break_audit import (  # noqa: E402
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
TARGET_ASSETS = ("EUR", "USDT")
JSON_PATH = ROOT / "var" / f"remaining_undercoverage_detail_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"124_REMAINING_UNDERCOVERAGE_DETAIL_AUDIT_{CREATED_DATE}.md"


def main() -> None:
    token_aliases = _load_token_aliases()
    ignored_mints = set(_load_ignored_tokens().keys())
    movements = [
        movement
        for row in _effective_events()
        for movement in _movements(row, token_aliases=token_aliases, ignored_mints=ignored_mints)
        if _year(movement["timestamp"]) >= 2020
    ]
    movements.sort(key=_movement_sort_key)
    reports = [build_asset_report(asset, [row for row in movements if row["asset"] == asset]) for asset in TARGET_ASSETS]
    audit = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "target_assets": list(TARGET_ASSETS),
        "reports": reports,
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "assets": TARGET_ASSETS}, ensure_ascii=False, indent=2))


def build_asset_report(asset: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    balance = Decimal("0")
    first_negative: dict[str, Any] | None = None
    worst: dict[str, Any] | None = None
    timeline = []
    daily_net: defaultdict[str, Decimal] = defaultdict(Decimal)
    source_net: Counter[tuple[str, str, str]] = Counter()
    yearly_net: defaultdict[int, Decimal] = defaultdict(Decimal)

    for row in rows:
        before = balance
        after = before + row["delta"]
        balance = after
        enriched = dict(row)
        enriched["balance_before"] = before
        enriched["balance_after"] = after
        timeline.append(enriched)
        day = str(row["timestamp"])[:10]
        daily_net[day] += row["delta"]
        yearly_net[row["year"]] += row["delta"]
        source_net[(row["source"], row["event_type"], row["side"])] += row["delta"]
        if before >= 0 > after and first_negative is None:
            first_negative = _slim_movement(enriched)
        if worst is None or after < _decimal(worst["balance_after"]):
            worst = _slim_movement(enriched)

    focus_ts = parse_ts((first_negative or {}).get("timestamp") or (worst or {}).get("timestamp"))
    critical_window = []
    if focus_ts is not None:
        start = focus_ts - timedelta(days=14)
        end = focus_ts + timedelta(days=14)
        critical_window = [
            _slim_movement(row)
            for row in timeline
            if (ts := parse_ts(row.get("timestamp"))) is not None and start <= ts <= end
        ]

    return {
        "asset": asset,
        "event_count": len(rows),
        "final_balance": _plain(balance),
        "first_negative": first_negative,
        "worst_balance": worst,
        "yearly_net": {str(year): _plain(value) for year, value in sorted(yearly_net.items())},
        "daily_net_top": [
            {"day": day, "net": _plain(value)}
            for day, value in sorted(daily_net.items(), key=lambda item: abs(item[1]), reverse=True)[:20]
        ],
        "source_net_top": [
            {"source": key[0], "event_type": key[1], "side": key[2], "net": _plain(value)}
            for key, value in sorted(source_net.items(), key=lambda item: abs(item[1]), reverse=True)[:20]
        ],
        "critical_window": critical_window,
        "interpretation": interpret(asset, first_negative, worst),
    }


def parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def interpret(asset: str, first_negative: dict[str, Any] | None, worst: dict[str, Any] | None) -> list[str]:
    if asset == "EUR":
        return [
            "The first EUR break is a Blockpit/Binance FIAT Payments trade and fee without a prior EUR fiat deposit in the effective chronology.",
            "This should be reconciled against Binance fiat deposit/withdrawal exports, Bitget fiat records, WISO/Blockpit references and bank evidence before creating an adjustment.",
        ]
    if asset == "USDT":
        return [
            "The remaining USDT break is Pionex-local and small compared with the later positive final balance.",
            "The next evidence target is Pionex bot/opening balance or internal transfer state immediately before 2022-01-19 12:56:19 UTC.",
        ]
    return [
        f"First negative: {(first_negative or {}).get('timestamp', '')}.",
        f"Worst balance: {(worst or {}).get('balance_after', '')}.",
    ]


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Remaining Undercoverage Detail Audit - 2026-05-09",
        "",
        f"Generated: `{audit['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        "Material transient undercoverage remains limited to `EUR` and `USDT` after reference exclusions, ignored-token handling and dust tolerance.",
        "",
    ]
    for report in audit["reports"]:
        first = report["first_negative"] or {}
        worst = report["worst_balance"] or {}
        lines += [
            f"## {report['asset']}",
            "",
            f"- Events: `{report['event_count']}`",
            f"- Final balance: `{report['final_balance']}`",
            f"- First break: `{first.get('timestamp', '')}` `{first.get('source', '')}` / `{first.get('event_type', '')}` / `{first.get('side', '')}` delta `{first.get('delta', '')}` after `{first.get('balance_after', '')}`",
            f"- Worst balance: `{worst.get('balance_after', '')}` at `{worst.get('timestamp', '')}`",
            f"- Yearly net: `{report['yearly_net']}`",
            "",
            "### Top Source Nets",
            "",
        ]
        for item in report["source_net_top"][:12]:
            lines.append(f"- `{item['source']}` / `{item['event_type']}` / `{item['side']}`: `{item['net']}`")
        lines += ["", "### Top Daily Nets", ""]
        for item in report["daily_net_top"][:12]:
            lines.append(f"- `{item['day']}`: `{item['net']}`")
        lines += ["", "### Critical Window", ""]
        for item in report["critical_window"][:80]:
            lines.append(
                f"- `{item.get('timestamp', '')}` `{item.get('source', '')}` / `{item.get('event_type', '')}` / "
                f"`{item.get('side', '')}` qty `{item.get('quantity', '')}` delta `{item.get('delta', '')}` "
                f"after `{item.get('balance_after', '')}` tx `{item.get('tx_id', '')}`"
            )
        if len(report["critical_window"]) > 80:
            lines.append(f"- ... truncated, total critical-window events: `{len(report['critical_window'])}`")
        lines += ["", "### Interpretation", ""]
        lines.extend(f"- {line}" for line in report["interpretation"])
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
