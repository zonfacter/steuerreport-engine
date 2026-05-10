#!/usr/bin/env python3
"""Ask the local LLM to rank candidate Pionex deposit-address gaps."""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import requests

from tax_engine.admin.service import resolve_effective_runtime_config
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

ROOT = Path(__file__).resolve().parents[1]
VAR_DIR = ROOT / "var"
DOC_PATH = ROOT / "docs" / "51_AI_PIONEX_ADDRESS_DISCOVERY_2026-05-08.md"
RESULT_PATH = VAR_DIR / "ai_pionex_address_discovery_2026-05-08.json"
CANDIDATE_PATH = VAR_DIR / "pionex_address_discovery_candidates_2026-05-08.json"

ADDRESS_RE = re.compile(r"\b(?:T[A-Za-z0-9]{33}|0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44})\b")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-events", type=int, default=260)
    parser.add_argument("--max-output-tokens", type=int, default=1400)
    parser.add_argument("--base-url", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--disable-thinking", action="store_true")
    parser.add_argument("--label", default="")
    args = parser.parse_args()

    VAR_DIR.mkdir(parents=True, exist_ok=True)
    events = _effective_events()
    candidates = _build_candidates(events, max_events=args.max_events)
    CANDIDATE_PATH.write_text(json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8")
    result = _ask_ai(
        candidates,
        max_output_tokens=args.max_output_tokens,
        base_url_override=args.base_url,
        model_override=args.model,
        disable_thinking=args.disable_thinking,
    )
    result_path = _variant_path(RESULT_PATH, args.label)
    doc_path = _variant_path(DOC_PATH, args.label)
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_doc(candidates, result, doc_path=doc_path, result_path=result_path)
    print(
        json.dumps(
            {
                "candidate_path": str(CANDIDATE_PATH),
                "result_path": str(result_path),
                "doc_path": str(doc_path),
                "status": result.get("status"),
            },
            indent=2,
        )
    )


def _effective_events() -> list[dict[str, Any]]:
    raw = STORE.list_raw_events()
    reviewed, _review_summary = apply_review_actions(raw)
    effective, _override_count = apply_tax_event_overrides(reviewed)
    return sorted(effective, key=lambda event: (_event_ts(event.get("payload", {})), str(event.get("unique_event_id"))))


def _build_candidates(events: list[dict[str, Any]], *, max_events: int) -> dict[str, Any]:
    address_groups: dict[str, dict[str, Any]] = {}
    transfer_events: list[dict[str, Any]] = []
    focused_events: list[dict[str, Any]] = []
    for event in events:
        payload = event.get("payload") if isinstance(event, dict) else {}
        if not isinstance(payload, dict):
            continue
        if not _is_relevant_transfer(payload):
            continue
        slim = _slim_event(event)
        transfer_events.append(slim)
        if _is_focus_event(slim):
            focused_events.append(slim)
        for address in _extract_addresses(payload):
            group = address_groups.setdefault(
                address,
                {
                    "address": address,
                    "event_count": 0,
                    "first_seen": slim["timestamp_utc"],
                    "last_seen": slim["timestamp_utc"],
                    "sources": defaultdict(int),
                    "assets": defaultdict(int),
                    "net_by_asset": defaultdict(Decimal),
                    "sample_events": [],
                },
            )
            group["event_count"] += 1
            group["first_seen"] = min(group["first_seen"], slim["timestamp_utc"])
            group["last_seen"] = max(group["last_seen"], slim["timestamp_utc"])
            group["sources"][slim["source"]] += 1
            group["assets"][slim["asset"]] += 1
            group["net_by_asset"][slim["asset"]] += Decimal(str(slim["signed_quantity"] or "0"))
            if len(group["sample_events"]) < 8:
                group["sample_events"].append(slim)

    normalized_groups = []
    for group in address_groups.values():
        normalized_groups.append(
            {
                "address": group["address"],
                "event_count": group["event_count"],
                "first_seen": group["first_seen"],
                "last_seen": group["last_seen"],
                "sources": dict(sorted(group["sources"].items())),
                "assets": dict(sorted(group["assets"].items())),
                "net_by_asset": {asset: str(value) for asset, value in sorted(group["net_by_asset"].items())},
                "sample_events": group["sample_events"],
            }
        )
    normalized_groups.sort(key=lambda row: (row["first_seen"], -row["event_count"], row["address"]))

    tron_summary = _load_json(ROOT / "var" / "tron_pionex_deposit_address_all_trc20_summary_2026-05-08.json")
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "question": (
            "Find whether another Pionex deposit address or missing platform export is likely to explain "
            "the early 2022 Pionex USDT opening gap."
        ),
        "known_confirmed_pionex_tron_deposit_address": "TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ",
        "known_pionex_tron_sweep_address": "TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU",
        "known_tron_audit_summary": tron_summary,
        "address_groups": normalized_groups[:80],
        "focused_events": focused_events[:max_events],
        "event_count_relevant_transfer_like": len(transfer_events),
        "notes": [
            "RAW events must not be changed by AI output.",
            "Known TRON address has exactly 4 USDT deposits and 4 sweeps, no earlier TRC20 transfers.",
            "Pionex-only USDT minimum gap is about -1643.4055675662 USDT.",
            "The AI should rank checks and hypotheses, not create tax events.",
        ],
    }


def _ask_ai(
    candidates: dict[str, Any],
    *,
    max_output_tokens: int,
    base_url_override: str = "",
    model_override: str = "",
    disable_thinking: bool = False,
) -> dict[str, Any]:
    config = resolve_effective_runtime_config().get("runtime", {}).get("ai_review", {})
    base_url = str(base_url_override or config.get("llama_cpp_base_url") or "http://192.168.2.203:11435").rstrip("/")
    model = str(model_override or config.get("llama_cpp_model") or "qwen3-coder-30b-a3b-llamacpp")
    payload = {
        "model": model,
        "temperature": float(config.get("llama_cpp_temperature") or 0.1),
        "max_tokens": max_output_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du bist ein vorsichtiger Crypto-Datenforensik-Assistent. "
                    "Bewerte nur Datenluecken und Plausibilitaet. Keine Steuerentscheidung, keine Buchung. "
                    "Antworte ausschliesslich mit validem JSON."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": (
                            "Analysiere die Kandidaten. Welche weiteren Adressen/Quellen sollten geprueft werden, "
                            "um die Pionex-USDT-Unterdeckung Anfang 2022 zu erklaeren?"
                        ),
                        "data": candidates,
                        "required_json": {
                            "summary": "kurze Gesamteinschaetzung",
                            "confirmed_facts": ["belegte Fakten"],
                            "unlikely_explanations": ["warum bestimmte Hypothesen weniger wahrscheinlich sind"],
                            "ranked_next_checks": [
                                {
                                    "rank": 1,
                                    "check": "konkreter Check",
                                    "target": "Adresse/Quelle/Datei",
                                    "reason": "warum",
                                    "expected_evidence": "was wuerde die Luecke belegen oder ausschliessen",
                                }
                            ],
                            "candidate_pionex_addresses": [
                                {"address": "string", "confidence": "high|medium|low", "reason": "string"}
                            ],
                            "confidence": "high|medium|low",
                        },
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        ],
    }
    if disable_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    started = time.time()
    try:
        response = requests.post(f"{base_url}/v1/chat/completions", json=payload, timeout=float(config.get("llama_cpp_timeout_seconds") or 240.0))
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        analysis = json.loads(content)
        return {
            "status": "success",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "duration_seconds": round(time.time() - started, 3),
            "base_url": base_url,
            "model": model,
            "analysis": analysis,
        }
    except Exception as exc:
        return {
            "status": "error",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "duration_seconds": round(time.time() - started, 3),
            "base_url": base_url,
            "model": model,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _write_doc(candidates: dict[str, Any], result: dict[str, Any], *, doc_path: Path, result_path: Path) -> None:
    analysis = result.get("analysis") if isinstance(result.get("analysis"), dict) else {}
    lines = [
        "# AI Pionex Address Discovery - 2026-05-08",
        "",
        "## Scope",
        "",
        "Local llama.cpp review for the hypothesis that another Pionex deposit address or missing platform export explains the early 2022 Pionex-USDT gap.",
        "",
        "## Inputs",
        "",
        f"- Candidate JSON: `{CANDIDATE_PATH}`",
        f"- Result JSON: `{result_path}`",
        f"- Known Pionex TRON deposit address: `{candidates.get('known_confirmed_pionex_tron_deposit_address')}`",
        f"- Known Pionex sweep address: `{candidates.get('known_pionex_tron_sweep_address')}`",
        f"- Relevant transfer-like events scanned: `{candidates.get('event_count_relevant_transfer_like')}`",
        f"- Address groups sent to AI: `{len(candidates.get('address_groups') or [])}`",
        f"- Focused events sent to AI: `{len(candidates.get('focused_events') or [])}`",
        "",
        "## LLM Status",
        "",
        f"- status: `{result.get('status')}`",
        f"- model: `{result.get('model')}`",
        f"- endpoint: `{result.get('base_url')}`",
        f"- duration_seconds: `{result.get('duration_seconds')}`",
        "",
    ]
    if result.get("status") != "success":
        lines += ["## Error", "", f"`{result.get('error')}`", ""]
    else:
        lines += [
            "## Summary",
            "",
            str(analysis.get("summary") or ""),
            "",
            "## Confirmed Facts",
            "",
        ]
        lines += [f"- {item}" for item in analysis.get("confirmed_facts", [])]
        lines += ["", "## Unlikely Explanations", ""]
        lines += [f"- {item}" for item in analysis.get("unlikely_explanations", [])]
        lines += ["", "## Ranked Next Checks", ""]
        for item in analysis.get("ranked_next_checks", []):
            lines.append(f"- `{item.get('rank')}` {item.get('check')} | target: `{item.get('target')}` | reason: {item.get('reason')}")
        lines += ["", "## Candidate Pionex Addresses", ""]
        for item in analysis.get("candidate_pionex_addresses", []):
            lines.append(f"- `{item.get('address')}` confidence `{item.get('confidence')}`: {item.get('reason')}")
        lines += ["", "## Confidence", "", str(analysis.get("confidence") or ""), ""]
    doc_path.write_text("\n".join(lines), encoding="utf-8")


def _variant_path(path: Path, label: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", label.strip())
    if not safe:
        return path
    return path.with_name(f"{path.stem}_{safe}{path.suffix}")


def _is_relevant_transfer(payload: dict[str, Any]) -> bool:
    event_type = str(payload.get("event_type") or "").lower()
    source = str(payload.get("source") or "").lower()
    asset = str(payload.get("asset") or "").upper()
    text = json.dumps(payload, ensure_ascii=False).lower()
    if any(token in event_type for token in ("deposit", "withdraw", "transfer")):
        return True
    if source in {"binance_api", "pionex", "bitget_tax_api", "solana_rpc"} and asset in {"USDT", "HNT", "SOL"}:
        return any(token in text for token in ("address", "wallet", "tx_id", "txid", "network"))
    return False


def _is_focus_event(event: dict[str, Any]) -> bool:
    ts = event["timestamp_utc"]
    source = event["source"].lower()
    asset = event["asset"].upper()
    if "2021-01-01" <= ts < "2022-03-01" and asset in {"USDT", "HNT", "SOL"}:
        return source.startswith(("binance", "pionex", "helium"))
    if event.get("addresses"):
        return True
    return False


def _slim_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload") or {}
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    return {
        "event_id": event.get("unique_event_id"),
        "timestamp_utc": _event_ts(payload),
        "source": str(payload.get("source") or ""),
        "event_type": str(payload.get("event_type") or ""),
        "side": str(payload.get("side") or ""),
        "asset": str(payload.get("asset") or "").upper(),
        "signed_quantity": str(_signed_quantity(payload)),
        "network": str(payload.get("network") or raw.get("network") or raw.get("Network") or ""),
        "tx_id": str(payload.get("tx_id") or raw.get("txid") or raw.get("TxID") or raw.get("Transaction ID") or ""),
        "addresses": sorted(_extract_addresses(payload)),
        "raw_file": str(raw.get("__file_name") or raw.get("__source_name") or ""),
    }


def _extract_addresses(payload: dict[str, Any]) -> set[str]:
    addresses: set[str] = set()
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    for obj in (payload, raw):
        for key, value in obj.items():
            key_l = str(key).lower()
            if not any(token in key_l for token in ("address", "wallet", "from", "to", "destination", "recipient")):
                continue
            if isinstance(value, str):
                addresses.update(ADDRESS_RE.findall(value))
    for value in (payload.get("address"), payload.get("to_wallet"), payload.get("from_wallet"), payload.get("counterparty_wallet")):
        if isinstance(value, str):
            addresses.update(ADDRESS_RE.findall(value))
    return addresses


def _event_ts(payload: dict[str, Any]) -> str:
    return str(payload.get("timestamp_utc") or payload.get("timestamp") or "")


def _signed_quantity(payload: dict[str, Any]) -> Decimal:
    quantity = _decimal(payload.get("quantity") or payload.get("amount"))
    side = str(payload.get("side") or "").lower()
    event_type = str(payload.get("event_type") or "").lower()
    if side == "out" or "withdraw" in event_type:
        return -abs(quantity)
    return quantity


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
