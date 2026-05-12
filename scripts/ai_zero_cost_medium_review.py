#!/usr/bin/env python3
"""Read-only local-AI review for remaining medium zero-cost tax-lot issues."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE

CREATED_DATE = "2026-05-10"
OUTPUT_JSON = ROOT / "var" / f"zero_cost_medium_review_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"180_ZERO_COST_MEDIUM_REVIEW_{CREATED_DATE}.md"
LLAMA_CPP_BASE_URL = os.getenv("LLAMA_CPP_BASE_URL", "http://192.168.2.203:11435").rstrip("/")
LLAMA_CPP_MODEL = os.getenv("LLAMA_CPP_MODEL", "qwen3.6-35b-a3b-iq4xs")
TARGETS = {(2022, "USDT"), (2024, "IOT"), (2024, "USDC"), (2024, "JUP")}


def main() -> None:
    events = STORE.list_raw_events()
    events_by_id = {str(event.get("unique_event_id") or ""): event for event in events}
    latest_jobs = _latest_completed_jobs_by_year()
    issues = []
    for year, asset in sorted(TARGETS):
        job = latest_jobs.get(year)
        if not job:
            continue
        lines = _zero_cost_lines(str(job["job_id"]), asset)
        issue = _build_issue_context(year=year, asset=asset, job=job, lines=lines, events=events, events_by_id=events_by_id)
        issues.append(issue)

    audit: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "model": LLAMA_CPP_MODEL,
        "base_url": LLAMA_CPP_BASE_URL,
        "status": "not_run",
        "issues": issues,
        "ai_review": {},
        "raw_response": "",
        "error": "",
    }
    try:
        model_result = call_model(_prompt_payload(issues))
        audit["raw_response"] = model_result["content"]
        audit["ai_review"] = parse_json_object(model_result["content"])
        audit["ai_usage"] = model_result.get("usage", {})
        audit["reasoning_content_present"] = model_result.get("reasoning_content_present", False)
        audit["status"] = "success"
    except Exception as exc:  # noqa: BLE001
        audit["status"] = "failed"
        audit["error"] = f"{type(exc).__name__}: {exc}"

    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"status": audit["status"], "json": str(OUTPUT_JSON), "doc": str(DOC_PATH)}, ensure_ascii=False, indent=2))


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _latest_completed_jobs_by_year() -> dict[int, dict[str, Any]]:
    latest: dict[int, dict[str, Any]] = {}
    for row in STORE.list_processing_jobs(status="completed", limit=5000):
        year = int(row.get("tax_year") or 0)
        if year <= 0:
            continue
        current = latest.get(year)
        if current is None or str(row.get("updated_at_utc") or "") > str(current.get("updated_at_utc") or ""):
            latest[year] = row
    return latest


def _zero_cost_lines(job_id: str, asset: str) -> list[dict[str, Any]]:
    lines = []
    for line in STORE.get_tax_lines(job_id):
        if str(line.get("asset") or "").upper() != asset:
            continue
        if str(line.get("tax_status") or "").lower() != "taxable":
            continue
        if _safe_decimal(line.get("cost_basis_eur")) != Decimal("0"):
            continue
        if _safe_decimal(line.get("proceeds_eur")) <= Decimal("0"):
            continue
        lines.append(line)
    return lines


def _payload(event: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(event, dict):
        return {}
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def _tx_id(payload: dict[str, Any]) -> str:
    return str(payload.get("tx_id") or payload.get("txid") or payload.get("signature") or payload.get("transaction_id") or "").strip()


def _qty(payload: dict[str, Any]) -> str:
    return str(payload.get("quantity") or payload.get("qty") or payload.get("amount") or "").strip()


def _event_brief(event_id: str, events_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    event = events_by_id.get(event_id)
    payload = _payload(event)
    if not payload:
        return {"event_id": event_id, "found": False}
    return {
        "event_id": event_id,
        "found": True,
        "timestamp_utc": str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
        "source": str(payload.get("source") or ""),
        "event_type": str(payload.get("event_type") or ""),
        "side": str(payload.get("side") or ""),
        "asset": str(payload.get("asset") or ""),
        "quantity": _qty(payload),
        "tx_id": _tx_id(payload),
        "value_usd_sum": str(payload.get("value_usd_sum") or ""),
        "valuation_reference_source": str(payload.get("valuation_reference_source") or ""),
        "wallet_address": str(payload.get("wallet_address") or ""),
    }


def _same_tx_events(tx_id: str, events: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    if not tx_id:
        return []
    rows = []
    for event in events:
        payload = _payload(event)
        if _tx_id(payload) != tx_id:
            continue
        rows.append(_event_brief(str(event.get("unique_event_id") or ""), {str(event.get("unique_event_id") or ""): event}))
    rows.sort(key=lambda item: (item.get("timestamp_utc", ""), item.get("source", ""), item.get("event_type", ""), item.get("side", "")))
    return rows[:limit]


def _window_events(asset: str, center_ts: str, events: list[dict[str, Any]], hours: int = 2, limit: int = 50) -> list[dict[str, Any]]:
    try:
        center = datetime.fromisoformat(center_ts.replace("Z", "+00:00"))
    except ValueError:
        return []
    start = center - timedelta(hours=hours)
    end = center + timedelta(hours=hours)
    rows = []
    asset_upper = asset.upper()
    for event in events:
        payload = _payload(event)
        ts_raw = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts < start or ts > end:
            continue
        event_asset = str(payload.get("asset") or "").upper()
        symbol = event_asset
        if asset_upper == "USDC" and event_asset.startswith("EPJFWD"):
            symbol = "USDC"
        if asset_upper not in {symbol, event_asset}:
            continue
        rows.append(_event_brief(str(event.get("unique_event_id") or ""), {str(event.get("unique_event_id") or ""): event}))
    rows.sort(key=lambda item: (item.get("timestamp_utc", ""), item.get("source", ""), item.get("event_type", ""), item.get("side", "")))
    return rows[:limit]


def _duplicate_signal(asset: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str, str, str], list[str]] = defaultdict(list)
    for event in events:
        payload = _payload(event)
        event_asset = str(payload.get("asset") or "").upper()
        if asset == "USDC" and event_asset.startswith("EPJFWD"):
            event_asset = "USDC"
        if event_asset != asset:
            continue
        key = (
            str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
            str(payload.get("source") or ""),
            str(payload.get("event_type") or ""),
            str(payload.get("side") or ""),
            _qty(payload),
        )
        groups[key].append(str(event.get("unique_event_id") or ""))
    duplicate_groups = [(key, ids) for key, ids in groups.items() if len(ids) > 1]
    return {
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_event_excess_count": sum(len(ids) - 1 for _, ids in duplicate_groups),
        "samples": [
            {
                "key": list(key),
                "event_ids": ids[:8],
            }
            for key, ids in duplicate_groups[:10]
        ],
    }


def _build_issue_context(
    *,
    year: int,
    asset: str,
    job: dict[str, Any],
    lines: list[dict[str, Any]],
    events: list[dict[str, Any]],
    events_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_counter = Counter()
    lot_source_counter = Counter()
    samples = []
    for line in lines:
        source_event_id = str(line.get("source_event_id") or "")
        lot_event_id = str(line.get("lot_source_event_id") or "")
        source_payload = _payload(events_by_id.get(source_event_id))
        lot_payload = _payload(events_by_id.get(lot_event_id))
        source_counter[str(source_payload.get("source") or "missing")] += 1
        lot_source_counter[str(lot_payload.get("source") or ("empty_lot" if not lot_event_id else "missing"))] += 1
        source_tx = _tx_id(source_payload)
        lot_tx = _tx_id(lot_payload)
        samples.append(
            {
                "line_no": line.get("line_no"),
                "qty": line.get("qty"),
                "buy_timestamp_utc": line.get("buy_timestamp_utc"),
                "sell_timestamp_utc": line.get("sell_timestamp_utc"),
                "proceeds_eur": line.get("proceeds_eur"),
                "source_event": _event_brief(source_event_id, events_by_id),
                "lot_event": _event_brief(lot_event_id, events_by_id) if lot_event_id else {"event_id": "", "found": False},
                "same_tx_events": _same_tx_events(source_tx or lot_tx, events, limit=12),
                "nearby_same_asset_events": _window_events(asset, str(line.get("sell_timestamp_utc") or ""), events, hours=2, limit=20),
            }
        )
    return {
        "year": year,
        "asset": asset,
        "job_id": str(job.get("job_id") or ""),
        "updated_at_utc": str(job.get("updated_at_utc") or ""),
        "line_count": len(lines),
        "proceeds_eur": str(sum((_safe_decimal(line.get("proceeds_eur")) for line in lines), start=Decimal("0"))),
        "qty": str(sum((_safe_decimal(line.get("qty")) for line in lines), start=Decimal("0"))),
        "source_counter": dict(source_counter.most_common()),
        "lot_source_counter": dict(lot_source_counter.most_common()),
        "duplicate_signal": _duplicate_signal(asset, events),
        "samples": samples[:20],
    }


def _prompt_payload(issues: list[dict[str, Any]]) -> dict[str, Any]:
    compact_issues = []
    for issue in issues:
        compact_samples = []
        for sample in issue["samples"][:4]:
            source = sample.get("source_event", {})
            lot = sample.get("lot_event", {})
            same_tx = sample.get("same_tx_events", [])
            nearby = sample.get("nearby_same_asset_events", [])
            compact_samples.append(
                {
                    "line_no": sample.get("line_no"),
                    "qty": sample.get("qty"),
                    "proceeds_eur": sample.get("proceeds_eur"),
                    "buy_timestamp_utc": sample.get("buy_timestamp_utc"),
                    "sell_timestamp_utc": sample.get("sell_timestamp_utc"),
                    "source": {
                        "source": source.get("source"),
                        "event_type": source.get("event_type"),
                        "side": source.get("side"),
                        "asset": source.get("asset"),
                        "quantity": source.get("quantity"),
                        "tx_id": source.get("tx_id"),
                    },
                    "lot": {
                        "found": lot.get("found"),
                        "source": lot.get("source"),
                        "event_type": lot.get("event_type"),
                        "side": lot.get("side"),
                        "asset": lot.get("asset"),
                        "quantity": lot.get("quantity"),
                        "tx_id": lot.get("tx_id"),
                        "value_usd_sum": lot.get("value_usd_sum"),
                        "valuation_reference_source": lot.get("valuation_reference_source"),
                    },
                    "same_tx_event_count": len(same_tx) if isinstance(same_tx, list) else 0,
                    "nearby_same_asset_event_count": len(nearby) if isinstance(nearby, list) else 0,
                }
            )
        compact_issues.append(
            {
                "year": issue["year"],
                "asset": issue["asset"],
                "line_count": issue["line_count"],
                "proceeds_eur": issue["proceeds_eur"],
                "source_counter": issue["source_counter"],
                "lot_source_counter": issue["lot_source_counter"],
                "duplicate_signal": issue["duplicate_signal"],
                "samples": compact_samples,
            }
        )
    return {"issues": compact_issues}


def call_model(facts: dict[str, Any]) -> dict[str, Any]:
    system = (
        "Du bist ein lokaler Review-Assistent fuer einen deutschen Krypto-Steuerreport. "
        "Kein Reasoning ausgeben, keine Gedankenkette, keine versteckten Schritte. "
        "Antworte nur als JSON-Objekt. Erfinde keine Transaktionen und schlage keine Rohdatenaenderung vor. "
        "Bewerte nur die gelieferten Fakten und unterscheide: missing_acquisition_chain, duplicate_or_reference_overlap, "
        "same_timestamp_ordering, valuation_only, non_tax_transfer_context, needs_manual_evidence."
    )
    user = (
        "Pruefe diese Medium-Nullbasis-Issues. Gib fuer jedes Issue ein Objekt mit "
        "year, asset, likely_cause, confidence, evidence, recommended_next_step, safe_to_auto_fix_boolean. "
        "Setze safe_to_auto_fix_boolean nur true, wenn die Fakten eine deterministische, eng begrenzte Processing-Korrektur zeigen.\n\n"
        + json.dumps(facts, ensure_ascii=False, indent=2)
    )
    payload = {
        "model": LLAMA_CPP_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "temperature": 0,
        "max_tokens": 2500,
        "chat_template_kwargs": {"enable_thinking": False},
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        f"{LLAMA_CPP_BASE_URL}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=float(os.getenv("LLAMA_CPP_TIMEOUT_SECONDS", "900"))) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"llama.cpp HTTP {exc.code}: {body[:500]}") from exc
    choices = data.get("choices") if isinstance(data, dict) else []
    if not choices:
        raise RuntimeError("llama.cpp returned no choices")
    choice = choices[0]
    message = choice.get("message") or {}
    content = str(message.get("content") or "").strip()
    if not content:
        raise RuntimeError("llama.cpp returned empty content")
    return {
        "content": content,
        "usage": data.get("usage") if isinstance(data.get("usage"), dict) else {},
        "reasoning_content_present": bool(message.get("reasoning_content")),
    }


def parse_json_object(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(content[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("model response is not a JSON object")
    return parsed


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Zero-Cost Medium Review",
        "",
        f"Stand: {CREATED_DATE}",
        "",
        "## Lauf",
        "",
        f"- Status: `{audit['status']}`",
        f"- Modell: `{audit['model']}`",
        f"- Endpoint: `{audit['base_url']}`",
        f"- Reasoning Content vorhanden: `{audit.get('reasoning_content_present', False)}`",
        "",
        "## Deterministische Issues",
        "",
    ]
    for issue in audit.get("issues", []):
        lines += [
            f"### {issue['year']} {issue['asset']}",
            "",
            f"- Job: `{issue['job_id']}`",
            f"- Zeilen: `{issue['line_count']}`",
            f"- Erloes: `{issue['proceeds_eur']} EUR`",
            f"- Source Counter: `{issue['source_counter']}`",
            f"- Lot Source Counter: `{issue['lot_source_counter']}`",
            f"- Duplicate Signal: `{issue['duplicate_signal'].get('duplicate_group_count')}` Gruppen, `{issue['duplicate_signal'].get('duplicate_event_excess_count')}` Ueberhang",
            "",
        ]
        for sample in issue.get("samples", [])[:5]:
            source = sample.get("source_event", {})
            lot = sample.get("lot_event", {})
            lines.append(
                f"- Line `{sample.get('line_no')}` qty `{sample.get('qty')}` proceeds `{sample.get('proceeds_eur')}`: "
                f"source `{source.get('source')}` `{source.get('event_type')}` `{source.get('side')}` tx `{source.get('tx_id')}`; "
                f"lot `{lot.get('source', '')}` `{lot.get('event_type', '')}` `{lot.get('side', '')}` tx `{lot.get('tx_id', '')}`"
            )
        lines.append("")
    lines += ["## Lokale KI-Auswertung", ""]
    if audit["status"] != "success":
        lines.append(f"- Fehler: `{audit.get('error', '')}`")
    else:
        review = audit.get("ai_review", {})
        items = review.get("issues") if isinstance(review.get("issues"), list) else review.get("reviews", [])
        if not isinstance(items, list):
            items = []
        if not items:
            lines.append("```json")
            lines.append(json.dumps(review, ensure_ascii=False, indent=2))
            lines.append("```")
        for item in items:
            lines.append(
                f"- `{item.get('year')}` `{item.get('asset')}` `{item.get('confidence', '')}`: "
                f"{item.get('likely_cause', '')} | Next: {item.get('recommended_next_step', '')} | "
                f"Auto-Fix: `{item.get('safe_to_auto_fix_boolean', False)}`"
            )
    lines += [
        "",
        "## Hinweis",
        "",
        "- Die lokale KI ist nur Zweitpruefung. Verbindlich bleiben Rohdaten, deterministische Ableitungen und manuelle Review-Entscheidungen.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
