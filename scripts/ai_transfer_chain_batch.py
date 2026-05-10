from __future__ import annotations

import argparse
import json
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
DOC_PATH = ROOT / "docs" / "22_AI_TRANSFER_CHAIN_ANALYSIS_2026-05-06.md"
STATUS_PATH = VAR_DIR / "ai_transfer_chain_batch_status.json"
RESULTS_PATH = VAR_DIR / "ai_transfer_chain_batch_results.jsonl"
LOG_PATH = VAR_DIR / "ai_transfer_chain_batch.log"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run long AI transfer-chain analysis batches.")
    parser.add_argument("--max-batches", type=int, default=80)
    parser.add_argument("--sleep-seconds", type=float, default=20.0)
    parser.add_argument("--max-events-per-cluster", type=int, default=90)
    parser.add_argument("--max-output-tokens", type=int, default=1600)
    args = parser.parse_args()

    VAR_DIR.mkdir(parents=True, exist_ok=True)
    started_at = _now()
    try:
        _log("starting ai transfer chain batch")
        events = _effective_events()
        clusters = _build_clusters(events, max_events_per_cluster=args.max_events_per_cluster)
        _write_status(
            {
                "status": "running",
                "started_at_utc": started_at,
                "updated_at_utc": _now(),
                "cluster_count": len(clusters),
                "completed_count": 0,
                "current_cluster": "",
                "result_path": str(RESULTS_PATH),
                "doc_path": str(DOC_PATH),
            }
        )
        _initialize_doc(events, clusters)

        completed = 0
        for cluster in clusters[: max(args.max_batches, 0)]:
            _write_status(
                {
                    "status": "running",
                    "started_at_utc": started_at,
                    "updated_at_utc": _now(),
                    "cluster_count": len(clusters),
                    "completed_count": completed,
                    "current_cluster": cluster["cluster_id"],
                    "result_path": str(RESULTS_PATH),
                    "doc_path": str(DOC_PATH),
                }
            )
            result = _analyze_cluster(cluster, max_output_tokens=args.max_output_tokens)
            completed += 1
            _append_result(result)
            _append_doc_result(result)
            _log(f"completed {completed}/{len(clusters)} {cluster['cluster_id']} status={result.get('status')}")
            time.sleep(max(args.sleep_seconds, 0.0))

        _write_status(
            {
                "status": "completed",
                "started_at_utc": started_at,
                "updated_at_utc": _now(),
                "cluster_count": len(clusters),
                "completed_count": completed,
                "current_cluster": "",
                "result_path": str(RESULTS_PATH),
                "doc_path": str(DOC_PATH),
            }
        )
        _log("completed ai transfer chain batch")
    except BaseException as exc:
        _write_status(
            {
                "status": "error",
                "started_at_utc": started_at,
                "updated_at_utc": _now(),
                "error": f"{type(exc).__name__}: {exc}",
                "result_path": str(RESULTS_PATH),
                "doc_path": str(DOC_PATH),
            }
        )
        _log(f"fatal {type(exc).__name__}: {exc}")
        raise


def _effective_events() -> list[dict[str, Any]]:
    raw = STORE.list_raw_events()
    reviewed, _summary = apply_review_actions(raw)
    effective, _override_count = apply_tax_event_overrides(reviewed)
    return sorted(effective, key=lambda event: (_event_ts(event.get("payload", {})), str(event.get("unique_event_id"))))


def _build_clusters(events: list[dict[str, Any]], max_events_per_cluster: int) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    clusters.append(_critical_pionex_cluster(events, max_events_per_cluster))
    clusters.append(_legacy_hnt_binance_cluster(events, max_events_per_cluster))
    clusters.append(_pionex_deposit_cluster(events, max_events_per_cluster))

    # Asset/year transfer clusters give the LLM broad context without one huge prompt.
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict) or not _is_transfer_like(payload):
            continue
        asset = str(payload.get("asset") or "").upper().strip() or "UNKNOWN"
        year = _event_ts(payload)[:4] if _event_ts(payload)[:4].isdigit() else "unknown"
        grouped[(year, asset)].append(event)

    priority_assets = {"USDT", "HNT", "HNT2", "SOL", "BTC", "BUSD", "VTHO", "MOBILE", "BNB", "JUP"}
    for (year, asset), rows in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        if asset not in priority_assets and len(rows) < 3:
            continue
        clusters.append(
            {
                "cluster_id": f"transfer_like:{year}:{asset}",
                "question": (
                    f"Analysiere Transfer-Zusammenhaenge fuer {asset} im Jahr {year}. "
                    "Suche fehlende Gegenbuchungen, Plattformwechsel und moegliche Ketten ueber Trades."
                ),
                "events": [_slim_event(row) for row in rows[:max_events_per_cluster]],
                "summary": _cluster_summary(rows),
            }
        )
    return clusters


def _critical_pionex_cluster(events: list[dict[str, Any]], max_events: int) -> dict[str, Any]:
    selected = []
    daily = defaultdict(lambda: defaultdict(Decimal))
    pionex_usdt_balance = Decimal("0")
    pionex_usdt_min = {"balance": Decimal("999999999"), "event": None}
    for event in events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        timestamp = _event_ts(payload)
        source = str(payload.get("source") or "").lower()
        asset = str(payload.get("asset") or "").upper()
        event_type = str(payload.get("event_type") or "").lower()
        delta = _signed_quantity(payload)
        if "2021-12-01" <= timestamp < "2022-02-01":
            if source.startswith("helium") and asset == "HNT":
                selected.append(event)
            elif source.startswith("binance") and asset in {"HNT", "USDT"} and event_type in {
                "deposit",
                "withdrawal",
                "trade",
                "fiat_crypto_purchase",
            }:
                selected.append(event)
            elif source == "pionex" and asset in {"USDT", "HNT", "SHIB", "EGLD"}:
                selected.append(event)
        if "2021-12-01" <= timestamp < "2022-02-01" and source.startswith("binance") and asset in {"HNT", "USDT"}:
            if event_type == "trade":
                daily[timestamp[:10]][f"{asset}_{'in' if delta > 0 else 'out'}"] += abs(delta)
        if source == "pionex" and asset == "USDT" and timestamp < "2023-01-01":
            pionex_usdt_balance += delta
            if pionex_usdt_balance < pionex_usdt_min["balance"]:
                pionex_usdt_min = {"balance": pionex_usdt_balance, "event": _slim_event(event)}
    return {
        "cluster_id": "critical:pionex_usdt_start_2021_12_to_2022_02",
        "question": (
            "Pruefe die Hypothese Legacy-HNT -> Binance -> HNT/USDT -> USDT zu Pionex. "
            "Welche Teile sind belegt, was erklaert die Pionex-USDT-Unterdeckung noch nicht?"
        ),
        "events": [_slim_event(row) for row in selected[:max_events]],
        "summary": {
            "binance_hnt_usdt_daily": {day: {key: str(value) for key, value in values.items()} for day, values in daily.items()},
            "pionex_usdt_min_through_2022": {
                "balance": str(pionex_usdt_min["balance"]),
                "event": pionex_usdt_min["event"],
            },
            "known_addresses": {
                "pionex_usdt_trc20": "TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ",
                "binance_hnt_deposit": "138bCXPVfSq7yyTfoDUrVwztPmUr4WGyA7TED9Y41djmF7rjA8y",
                "unmatched_legacy_hnt_candidate": "13m4dWjjQrFSGfhC3tawCpQRv7oXAJxBSaSXCtr7DWFcMG6p4E9",
            },
        },
    }


def _legacy_hnt_binance_cluster(events: list[dict[str, Any]], max_events: int) -> dict[str, Any]:
    selected = []
    for event in events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        timestamp = _event_ts(payload)
        source = str(payload.get("source") or "").lower()
        asset = str(payload.get("asset") or "").upper()
        if not ("2021-01-01" <= timestamp < "2023-01-01"):
            continue
        if source.startswith("helium") and asset == "HNT" and _is_transfer_like(payload):
            selected.append(event)
        elif source.startswith("binance") and asset == "HNT" and _is_transfer_like(payload):
            selected.append(event)
    return {
        "cluster_id": "legacy_hnt_to_binance_2021_2022",
        "question": "Welche Legacy-HNT-Transfers wurden zu Binance gematcht, welche Zieladressen bleiben ungeklaert?",
        "events": [_slim_event(row) for row in selected[:max_events]],
        "summary": _cluster_summary(selected),
    }


def _pionex_deposit_cluster(events: list[dict[str, Any]], max_events: int) -> dict[str, Any]:
    selected = []
    for event in events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        source = str(payload.get("source") or "").lower()
        asset = str(payload.get("asset") or "").upper()
        event_type = str(payload.get("event_type") or "").lower()
        text = json.dumps(payload, ensure_ascii=False)
        if source == "pionex" and event_type in {"deposit", "withdrawal"}:
            selected.append(event)
        elif source.startswith("binance") and asset == "USDT" and "TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ" in text:
            selected.append(event)
    return {
        "cluster_id": "pionex_deposits_and_matching_binance_withdrawals",
        "question": "Pruefe Pionex-Deposits gegen Binance-Withdrawals. Fehlen USDT-Zufluesse oder sind alle CSV-Deposits belegt?",
        "events": [_slim_event(row) for row in selected[:max_events]],
        "summary": _cluster_summary(selected),
    }


def _analyze_cluster(cluster: dict[str, Any], max_output_tokens: int) -> dict[str, Any]:
    config = resolve_effective_runtime_config().get("runtime", {}).get("ai_review", {})
    base_url = str(config.get("llama_cpp_base_url") or "http://192.168.2.203:11435").rstrip("/")
    model = str(config.get("llama_cpp_model") or "qwen3-coder-30b-a3b-llamacpp")
    payload = {
        "model": model,
        "temperature": 0.1,
        "max_tokens": max(512, int(max_output_tokens)),
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du bist ein vorsichtiger Datenforensik-Assistent fuer Crypto-Transferketten. "
                    "Keine Steuerentscheidung. Keine API-Aktion. Antworte nur mit validem JSON."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "cluster_id": cluster["cluster_id"],
                        "question": cluster["question"],
                        "summary": cluster.get("summary", {}),
                        "events": cluster.get("events", []),
                        "required_json": {
                            "findings": ["kurze belegte Befunde"],
                            "strongest_chain": "beste belegte Kette oder leer",
                            "unresolved_gaps": ["offene Datenluecken"],
                            "recommended_next_checks": ["konkrete naechste Checks"],
                            "confidence": "high|medium|low",
                        },
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        ],
    }
    started = time.time()
    _log(f"requesting {cluster['cluster_id']} events={len(cluster.get('events', []))}")
    try:
        response = requests.post(f"{base_url}/v1/chat/completions", json=payload, timeout=300)
        if response.status_code >= 400:
            raise RuntimeError(f"{response.status_code} {response.text[:1200]}")
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        analysis = json.loads(content)
        status = "success"
        error = ""
    except Exception as exc:
        analysis = {}
        status = "error"
        error = str(exc)
    return {
        "cluster_id": cluster["cluster_id"],
        "status": status,
        "error": error,
        "duration_seconds": round(time.time() - started, 3),
        "created_at_utc": _now(),
        "analysis": analysis,
        "event_count": len(cluster.get("events", [])),
        "summary": cluster.get("summary", {}),
    }


def _slim_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    return {
        "event_id": event.get("unique_event_id", ""),
        "ts": _event_ts(payload),
        "source": payload.get("source", ""),
        "type": payload.get("event_type", ""),
        "side": payload.get("side", ""),
        "asset": str(payload.get("asset") or "").upper(),
        "qty_signed": str(_signed_quantity(payload)),
        "tx_id": payload.get("tx_id", ""),
        "symbol": raw.get("symbol") or raw.get("Market") or raw.get("Pair") or "",
        "address_or_comment": raw.get("address") or raw.get("Address") or raw.get("comment") or "",
        "file": raw.get("__source_name") or raw.get("__file_name") or "",
    }


def _cluster_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source: dict[str, int] = defaultdict(int)
    by_asset: dict[str, int] = defaultdict(int)
    quantity_by_asset: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        payload = row.get("payload", {})
        source = str(payload.get("source") or "")
        asset = str(payload.get("asset") or "").upper()
        by_source[source] += 1
        by_asset[asset] += 1
        quantity_by_asset[asset] += _signed_quantity(payload)
    return {
        "event_count": len(rows),
        "by_source": dict(sorted(by_source.items())),
        "by_asset": dict(sorted(by_asset.items())),
        "signed_quantity_by_asset": {key: str(value) for key, value in sorted(quantity_by_asset.items())},
    }


def _is_transfer_like(payload: dict[str, Any]) -> bool:
    event_type = str(payload.get("event_type") or "").lower()
    return any(token in event_type for token in ("transfer", "deposit", "withdraw"))


def _event_ts(payload: dict[str, Any]) -> str:
    return str(payload.get("timestamp_utc") or payload.get("timestamp") or "")


def _signed_quantity(payload: dict[str, Any]) -> Decimal:
    quantity = _decimal(payload.get("quantity") or payload.get("amount"))
    side = str(payload.get("side") or "").lower()
    event_type = str(payload.get("event_type") or "").lower()
    if side == "out" or event_type in {"withdrawal", "fee", "derivative fee", "derivative loss"}:
        return -abs(quantity)
    return quantity


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").replace(",", ""))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _initialize_doc(events: list[dict[str, Any]], clusters: list[dict[str, Any]]) -> None:
    lines = [
        "# AI Transfer Chain Analysis 2026-05-06",
        "",
        "Automatischer Hintergrundlauf fuer Transferkettenanalyse.",
        "",
        "## Lauf",
        f"- Start: `{_now()}`",
        f"- Effektive Events: `{len(events)}`",
        f"- Cluster: `{len(clusters)}`",
        f"- Status: `{STATUS_PATH}`",
        f"- JSONL-Resultate: `{RESULTS_PATH}`",
        "",
        "## Ergebnisse",
        "",
    ]
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def _append_doc_result(result: dict[str, Any]) -> None:
    analysis = result.get("analysis") if isinstance(result.get("analysis"), dict) else {}
    lines = [
        f"### {result.get('cluster_id')}",
        f"- Status: `{result.get('status')}`, Dauer: `{result.get('duration_seconds')}s`, Events: `{result.get('event_count')}`",
    ]
    if result.get("error"):
        lines.append(f"- Fehler: `{result.get('error')}`")
    if analysis:
        lines.append("```json")
        lines.append(json.dumps(analysis, ensure_ascii=False, indent=2))
        lines.append("```")
    lines.append("")
    with DOC_PATH.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def _append_result(result: dict[str, Any]) -> None:
    with RESULTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")


def _write_status(status: dict[str, Any]) -> None:
    current = {}
    if STATUS_PATH.exists():
        try:
            current = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except Exception:
            current = {}
    current.update(status)
    STATUS_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")


def _log(message: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{_now()} {message}\n")


def _now() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    main()
