#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin import resolve_cex_credentials  # noqa: E402
from tax_engine.connectors import fetch_cex_balance_preview  # noqa: E402
from tax_engine.connectors.service import _binance_signed_get  # noqa: E402, PLC2701
from tax_engine.ingestion.store import STORE  # noqa: E402

RUN_DATE = "2026-05-10"
JSON_PATH = ROOT / "var" / f"binance_earn_position_reconciliation_{RUN_DATE}.json"
DOC_PATH = ROOT / "docs" / f"201_BINANCE_EARN_POSITION_RECONCILIATION_{RUN_DATE}.md"


def main() -> None:
    creds = resolve_cex_credentials("binance")
    api_key = creds["api_key"]
    api_secret = creds["api_secret"]
    if not api_key or not api_secret:
        raise SystemExit("Binance credentials missing in secret store")

    now = datetime.now(UTC)
    balances = fetch_cex_balance_preview(
        connector_id="binance",
        api_key=api_key,
        api_secret=api_secret,
        passphrase=None,
        timeout_seconds=30,
        max_rows=5000,
    )
    history = fetch_earn_history(api_key=api_key, api_secret=api_secret)
    product_events = build_product_position_events(history)
    upsert_result = STORE.upsert_product_position_events(product_events)
    audit = {
        "created_at_utc": now.isoformat(),
        "balance_rows": balances.get("rows", []),
        "history": history,
        "summary": summarize(balances.get("rows", []), history),
        "product_position_upsert": upsert_result,
    }
    JSON_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "summary": audit["summary"]}, indent=2))


def fetch_earn_history(api_key: str, api_secret: str) -> dict[str, Any]:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    end = datetime(2026, 5, 10, 23, 59, 59, tzinfo=UTC)
    specs = [
        ("simple_locked_subscription", "/sapi/v1/simple-earn/locked/history/subscriptionRecord", {}, "amount"),
        ("simple_locked_redemption", "/sapi/v1/simple-earn/locked/history/redemptionRecord", {}, "amount"),
        ("simple_locked_rewards", "/sapi/v1/simple-earn/locked/history/rewardsRecord", {}, "amount"),
        ("simple_flexible_subscription", "/sapi/v1/simple-earn/flexible/history/subscriptionRecord", {}, "amount"),
        ("simple_flexible_redemption", "/sapi/v1/simple-earn/flexible/history/redemptionRecord", {}, "amount"),
        ("simple_flexible_rewards_realtime", "/sapi/v1/simple-earn/flexible/history/rewardsRecord", {"type": "REALTIME"}, "rewards"),
        ("simple_flexible_rewards_rewards", "/sapi/v1/simple-earn/flexible/history/rewardsRecord", {"type": "REWARDS"}, "rewards"),
    ]
    result: dict[str, Any] = {}
    for name, path, extra, amount_key in specs:
        rows: list[dict[str, Any]] = []
        errors: list[str] = []
        cursor = start
        while cursor < end:
            window_end = min(cursor + timedelta(days=29), end)
            params = {
                "startTime": str(int(cursor.timestamp() * 1000)),
                "endTime": str(int(window_end.timestamp() * 1000)),
                "current": "1",
                "size": "100",
                **extra,
            }
            try:
                payload = _binance_signed_get(
                    path=path,
                    api_key=api_key,
                    api_secret=api_secret,
                    timeout_seconds=30,
                    params=params,
                )
                page_rows = payload.get("rows", []) if isinstance(payload, dict) else []
                if isinstance(page_rows, list):
                    rows.extend(page_rows)
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc)[:300])
            cursor = window_end + timedelta(milliseconds=1)
        result[name] = {
            "path": path,
            "row_count": len(rows),
            "asset_totals": asset_totals(rows, amount_key),
            "rows": rows,
            "errors": sorted(set(errors))[:10],
        }
    return result


def build_product_position_events(history: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for endpoint_name, payload in sorted(history.items()):
        rows = payload.get("rows", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            asset = str(row.get("asset") or "").upper()
            if not asset:
                continue
            product_id = str(row.get("productId") or row.get("projectId") or "")
            position_id = str(row.get("positionId") or "")
            source_ref = str(row.get("purchaseId") or row.get("redeemId") or row.get("tranId") or row.get("id") or "")
            timestamp_utc = ms_to_iso(row.get("time") or row.get("rewardTime") or row.get("divTime"))
            quantity_key = "rewards" if endpoint_name.startswith("simple_flexible_rewards") else "amount"
            event_type = endpoint_name
            is_reward = "rewards" in endpoint_name
            tax_treatment = "reward_income_candidate" if is_reward else "non_taxable_principal_movement"
            event_id = ":".join(
                [
                    "binance_earn",
                    endpoint_name,
                    product_id,
                    position_id,
                    source_ref,
                    timestamp_utc,
                    asset,
                    str(row.get(quantity_key) or "0"),
                ]
            )
            events.append(
                {
                    "event_id": event_id,
                    "platform": "binance",
                    "product_type": endpoint_name,
                    "product_id": product_id,
                    "position_id": position_id,
                    "event_type": event_type,
                    "tax_treatment": tax_treatment,
                    "asset": asset,
                    "quantity": str(row.get(quantity_key) or "0"),
                    "timestamp_utc": timestamp_utc,
                    "source_ref": source_ref,
                    "raw": row,
                }
            )
    return events


def asset_totals(rows: list[dict[str, Any]], amount_key: str) -> dict[str, str]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        asset = str(row.get("asset") or "").upper()
        if not asset:
            continue
        totals[asset] += dec(row.get(amount_key))
    return {asset: value.to_eng_string() for asset, value in sorted(totals.items())}


def summarize(balance_rows: list[dict[str, Any]], history: dict[str, Any]) -> dict[str, Any]:
    balance_totals: dict[str, Decimal] = defaultdict(Decimal)
    balance_by_account: dict[str, dict[str, str]] = defaultdict(dict)
    for row in balance_rows:
        asset = str(row.get("asset") or "").upper()
        if not asset:
            continue
        qty = dec(row.get("quantity"))
        account_type = str(row.get("account_type") or "spot")
        event_type = str(row.get("event_type") or "balance_snapshot")
        key = f"{account_type}:{event_type}"
        balance_totals[asset] += qty
        balance_by_account[asset][key] = (dec(balance_by_account[asset].get(key, "0")) + qty).to_eng_string()
    return {
        "balance_totals": {asset: value.to_eng_string() for asset, value in sorted(balance_totals.items())},
        "balance_by_account": dict(sorted(balance_by_account.items())),
        "history_counts": {name: payload.get("row_count", 0) for name, payload in sorted(history.items())},
        "history_asset_totals": {name: payload.get("asset_totals", {}) for name, payload in sorted(history.items())},
    }


def render_doc(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        "# Binance Earn Position Reconciliation",
        "",
        f"Stand: {audit['created_at_utc']}",
        "",
        "## Aktuelle Binance-Bestaende",
        "",
        "| Asset | Gesamt | Aufteilung |",
        "|---|---:|---|",
    ]
    for asset, total in summary["balance_totals"].items():
        if asset not in {"SOL", "JUP", "LDJUP", "DOGE", "TRUMP", "BNSOL"}:
            continue
        split = ", ".join(f"{key}={value}" for key, value in summary["balance_by_account"].get(asset, {}).items())
        lines.append(f"| `{asset}` | `{total}` | {split} |")
    lines.extend(["", "## Binance-Earn-Historie 2025-01-01 bis 2026-05-10", "", "| Endpoint | Rows | Asset totals |", "|---|---:|---|"])
    for name, count in summary["history_counts"].items():
        totals = ", ".join(f"{asset}={value}" for asset, value in summary["history_asset_totals"].get(name, {}).items())
        lines.append(f"| `{name}` | `{count}` | {totals or '-'} |")
    lines.extend(
        [
            "",
            "## Persistenz",
            "",
            f"- Produktpositions-Events upserted: `{audit.get('product_position_upsert', {}).get('total', 0)}`",
            f"- Neu: `{audit.get('product_position_upsert', {}).get('inserted', 0)}`",
            f"- Aktualisiert: `{audit.get('product_position_upsert', {}).get('updated', 0)}`",
            "- Tabelle: `product_position_events`",
            "- API: `GET /api/v1/product-positions/events`",
            "",
            "## Bewertung",
            "",
            "- `simple_locked_subscription` zeigt die aktive SOL-Locked-Position als Subscription-Historie.",
            "- `simple_locked_rewards` deckt das aktuelle Binance-Reward-Feld fuer SOL rechnerisch ab.",
            "- `simple_flexible_subscription` und `simple_flexible_redemption` zeigen JUP/DOGE/TRUMP/BNSOL Produktbewegungen, die fuer FIFO/Portfolio nicht als Verkauf/Kauf fehlinterpretiert werden duerfen.",
            "- Naechster technischer Schritt: Earn-Produktbewegungen als eigene nicht-steuerliche Produktpositions-Historie modellieren und Rewards separat als steuerliche Zufluesse behandeln.",
            "",
        ]
    )
    return "\n".join(lines)


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def ms_to_iso(value: Any) -> str:
    try:
        raw = int(str(value))
    except Exception:
        return ""
    if raw <= 0:
        return ""
    return datetime.fromtimestamp(raw / 1000, tz=UTC).isoformat()


if __name__ == "__main__":
    main()
