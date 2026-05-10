#!/usr/bin/env python3
"""Probe Binance Simple Earn primary reward history for remaining Blockpit rewards."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import _load_secret_json_value  # noqa: PLC2701
from tax_engine.connectors.service import (  # noqa: PLC2701
    _binance_fetch_asset_dividends,
    _binance_signed_get,
    _to_utc_iso,
)
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

JSON_PATH = ROOT / "var" / "binance_earn_primary_probe_2026-05-08.json"
DOC_PATH = ROOT / "docs" / "63_BINANCE_EARN_PRIMARY_PROBE_2026-05-08.md"
RAW_DIR = ROOT / "var" / "external_evidence" / "binance_earn_primary_2026-05-08"
START = datetime(2025, 1, 1, tzinfo=UTC)
END = datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC)
TIME_TOLERANCE_SECONDS = 90
AMOUNT_TOLERANCE = Decimal("0.00000001")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    refs = collect_remaining_blockpit_earn_refs()
    api_key = _load_secret_json_value("secret.cex.binance.api_key")
    api_secret = _load_secret_json_value("secret.cex.binance.api_secret")
    endpoint_results: list[dict[str, Any]] = []
    primary_rows: list[dict[str, Any]] = []
    if not api_key or not api_secret:
        endpoint_results.append({"endpoint": "credentials", "status": "missing"})
    else:
        primary_rows.extend(fetch_simple_earn_rewards(api_key, api_secret, endpoint_results))
        primary_rows.extend(fetch_asset_dividends(api_key, api_secret, endpoint_results))

    matches, unmatched = match_refs(refs, primary_rows)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": "Binance Earn primary probe for remaining 2025 Blockpit Earn Reward rows",
        "raw_dir": str(RAW_DIR),
        "blockpit_reference_count": len(refs),
        "primary_reward_row_count": len(primary_rows),
        "matched_count": len(matches),
        "unmatched_count": len(unmatched),
        "reference_asset_counts": dict(Counter(row["asset"] for row in refs)),
        "primary_asset_counts": dict(Counter(row["asset"] for row in primary_rows)),
        "endpoint_results": endpoint_results,
        "matches": matches,
        "unmatched_reference_rows": unmatched,
        "primary_rows": primary_rows,
        "conclusion": conclusion(endpoint_results, primary_rows, matches, unmatched),
    }
    JSON_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    DOC_PATH.write_text(render(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "primary_rows": len(primary_rows), "matches": len(matches), "unmatched": len(unmatched)}, indent=2))


def collect_remaining_blockpit_earn_refs() -> list[dict[str, Any]]:
    reviewed, _summary = apply_review_actions(STORE.list_raw_events())
    effective, _override_count = apply_tax_event_overrides(reviewed)
    rows: list[dict[str, Any]] = []
    for event in effective:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        if str(payload.get("source") or "") != "blockpit":
            continue
        if str(raw.get("Integration Name") or raw.get("Source Name") or "").lower() != "binance":
            continue
        if str(payload.get("event_type") or "") != "interest":
            continue
        if "earn reward" not in str(raw.get("Comment (optional)") or "").lower():
            continue
        rows.append(
            {
                "event_id": str(event.get("unique_event_id") or ""),
                "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
                "epoch_seconds": parse_epoch(str(payload.get("timestamp_utc") or payload.get("timestamp") or "")),
                "asset": str(payload.get("asset") or "").upper(),
                "amount": str(abs(dec(payload.get("quantity")))),
                "comment": str(raw.get("Comment (optional)") or ""),
                "source_tx_id": str(raw.get("Trx. ID (optional)") or ""),
            }
        )
    rows.sort(key=lambda row: (row["timestamp_utc"], row["asset"], row["event_id"]))
    return rows


def fetch_simple_earn_rewards(api_key: str, api_secret: str, endpoint_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    endpoints = [
        ("simple_earn_flexible", "/sapi/v1/simple-earn/flexible/history/rewardsRecord", ("REALTIME", "BONUS", "REWARDS")),
        ("simple_earn_locked", "/sapi/v1/simple-earn/locked/history/rewardsRecord", ("",)),
    ]
    for name, path, reward_types in endpoints:
        for reward_type in reward_types:
            endpoint_rows: list[dict[str, Any]] = []
            errors: list[str] = []
            for window_start, window_end in windows(START, END, days=30):
                for page in range(1, 101):
                    params = {
                        "startTime": str(to_ms(window_start)),
                        "endTime": str(to_ms(window_end)),
                        "current": str(page),
                        "size": "100",
                    }
                    if reward_type:
                        params["type"] = reward_type
                    try:
                        payload = _binance_signed_get(path=path, api_key=api_key, api_secret=api_secret, timeout_seconds=20, params=params)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(error_summary(exc))
                        break
                    raw_path = RAW_DIR / f"{name}_{reward_type or 'default'}_{window_start.date()}_{page}.json"
                    raw_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
                    page_rows = payload.get("rows", []) if isinstance(payload, dict) else []
                    if not isinstance(page_rows, list) or not page_rows:
                        break
                    endpoint_rows.extend(page_rows)
                    if len(page_rows) < 100:
                        break
            for item in endpoint_rows:
                normalized = normalize_earn_row(name, reward_type, item)
                if normalized:
                    rows.append(normalized)
            endpoint_results.append(
                {
                    "endpoint": name,
                    "reward_type": reward_type or "default",
                    "status": "ok" if not errors else "error",
                    "row_count": len(endpoint_rows),
                    "errors": sorted(set(errors))[:5],
                }
            )
    return rows


def fetch_asset_dividends(api_key: str, api_secret: str, endpoint_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for window_start, window_end in windows(START, END, days=170):
        try:
            raw_rows.extend(
                _binance_fetch_asset_dividends(
                    api_key=api_key,
                    api_secret=api_secret,
                    timeout_seconds=20,
                    start_time_ms=to_ms(window_start),
                    end_time_ms=to_ms(window_end),
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(error_summary(exc))
    (RAW_DIR / "asset_dividend_2025.json").write_text(json.dumps(raw_rows, indent=2, ensure_ascii=False), encoding="utf-8")
    endpoint_results.append({"endpoint": "asset_dividend", "status": "ok" if not errors else "error", "row_count": len(raw_rows), "errors": sorted(set(errors))[:5]})
    return [
        {
            "source_endpoint": "asset_dividend",
            "reward_type": "asset_dividend",
            "timestamp_utc": str(row.get("timestamp_utc") or ""),
            "epoch_seconds": parse_epoch(str(row.get("timestamp_utc") or "")),
            "asset": str(row.get("asset") or "").upper(),
            "amount": str(abs(dec(row.get("quantity")))),
            "source_tx_id": str(row.get("tx_id") or ""),
            "raw_row": row.get("raw_row") or row,
        }
        for row in raw_rows
    ]


def normalize_earn_row(endpoint: str, reward_type: str, item: dict[str, Any]) -> dict[str, Any] | None:
    amount = dec(item.get("rewards") if "rewards" in item else item.get("amount"))
    if amount == Decimal("0"):
        return None
    ts = _to_utc_iso(item.get("time") or item.get("rewardTime") or item.get("divTime"))
    return {
        "source_endpoint": endpoint,
        "reward_type": str(item.get("type") or reward_type or ""),
        "timestamp_utc": str(ts or ""),
        "epoch_seconds": parse_epoch(str(ts or "")),
        "asset": str(item.get("asset") or "").upper(),
        "amount": str(abs(amount)),
        "source_tx_id": str(item.get("tranId") or item.get("id") or ""),
        "raw_row": item,
    }


def match_refs(refs: list[dict[str, Any]], primary_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matches: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    used_primary: set[int] = set()
    for ref in refs:
        candidates: list[tuple[int, int, dict[str, Any]]] = []
        for idx, primary in enumerate(primary_rows):
            if idx in used_primary:
                continue
            if ref["asset"] != primary["asset"]:
                continue
            if abs(dec(ref["amount"]) - dec(primary["amount"])) > AMOUNT_TOLERANCE:
                continue
            delta = abs(int(ref["epoch_seconds"]) - int(primary["epoch_seconds"]))
            if delta <= TIME_TOLERANCE_SECONDS:
                candidates.append((delta, idx, primary))
        if not candidates:
            unmatched.append(ref)
            continue
        candidates.sort(key=lambda item: (item[0], item[1]))
        delta, idx, primary = candidates[0]
        used_primary.add(idx)
        matches.append(
            {
                "reference_event_id": ref["event_id"],
                "primary_source_endpoint": primary["source_endpoint"],
                "primary_reward_type": primary["reward_type"],
                "reference_timestamp_utc": ref["timestamp_utc"],
                "primary_timestamp_utc": primary["timestamp_utc"],
                "delta_seconds": delta,
                "asset": ref["asset"],
                "amount": ref["amount"],
                "primary_tx_id": primary["source_tx_id"],
            }
        )
    return matches, unmatched


def render(audit: dict[str, Any]) -> str:
    lines = [
        "# Binance Earn Primary Probe - 2026-05-08",
        "",
        "## Summary",
        "",
        f"- JSON: `{JSON_PATH}`",
        f"- Raw evidence dir: `{audit['raw_dir']}`",
        f"- Blockpit Earn reference rows: `{audit['blockpit_reference_count']}`",
        f"- Primary reward rows fetched: `{audit['primary_reward_row_count']}`",
        f"- Matched: `{audit['matched_count']}`",
        f"- Unmatched: `{audit['unmatched_count']}`",
        f"- Reference asset counts: `{audit['reference_asset_counts']}`",
        f"- Primary asset counts: `{audit['primary_asset_counts']}`",
        "",
        "## Endpoint Results",
        "",
    ]
    for row in audit["endpoint_results"]:
        lines.append(f"- `{row['endpoint']}` `{row.get('reward_type', '')}` status `{row['status']}` rows `{row.get('row_count', 0)}` errors `{row.get('errors', [])}`")
    lines += ["", "## Matches", ""]
    if not audit["matches"]:
        lines.append("- Keine.")
    for row in audit["matches"]:
        lines.append(
            f"- `{row['reference_timestamp_utc']}` `{row['asset']}` `{row['amount']}` -> `{row['primary_source_endpoint']}` `{row['primary_reward_type']}` delta `{row['delta_seconds']}s`"
        )
    lines += ["", "## Unmatched Blockpit Earn Rows", ""]
    for row in audit["unmatched_reference_rows"]:
        lines.append(f"- `{row['timestamp_utc']}` `{row['asset']}` amount `{row['amount']}` event `{row['event_id']}`")
    lines += ["", "## Conclusion", "", audit["conclusion"], ""]
    return "\n".join(lines)


def conclusion(
    endpoint_results: list[dict[str, Any]],
    primary_rows: list[dict[str, Any]],
    matches: list[dict[str, Any]],
    unmatched: list[dict[str, Any]],
) -> str:
    if matches and not unmatched:
        return "Alle Blockpit-Earn-Referenzen wurden durch Binance-Primary-Earn-Historie belegt."
    if any(row.get("status") == "error" for row in endpoint_results):
        return "Mindestens ein Binance-Earn-Endpunkt lieferte einen Fehler; fehlende Rewards bleiben als Referenz/Nachweisbedarf aktiv."
    if not primary_rows:
        return "Die abgefragten Binance-Earn-Endpunkte lieferten keine passenden Primary-Rewards fuer 2025; Blockpit Earn bleibt vorerst Referenzquelle."
    return "Es wurden Binance-Earn-Primary-Zeilen gefunden, aber nicht alle Blockpit-Referenzen matchen; unmatched Zeilen bleiben unter Review."


def windows(start: datetime, end: datetime, days: int) -> list[tuple[datetime, datetime]]:
    result: list[tuple[datetime, datetime]] = []
    current = start
    while current <= end:
        window_end = min(current + timedelta(days=days) - timedelta(milliseconds=1), end)
        result.append((current, window_end))
        current = window_end + timedelta(milliseconds=1)
    return result


def to_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def parse_epoch(ts: str) -> int:
    try:
        return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def error_summary(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        body = exc.response.text[:300]
        return f"HTTP {exc.response.status_code}: {body}"
    return f"{type(exc).__name__}: {str(exc)[:300]}"


if __name__ == "__main__":
    main()
