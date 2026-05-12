#!/usr/bin/env python3
"""Build a reproducible CEX coverage matrix for tax-report data sources."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import resolve_effective_runtime_config
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

USERTRANSFER = ROOT / "usertransfer"
VAR_DIR = ROOT / "var"
JSON_PATH = VAR_DIR / "cex_compliance_coverage_2026-05-08.json"
DOC_PATH = ROOT / "docs" / "54_CEX_COMPLIANCE_COVERAGE_2026-05-08.md"
AI_JSON_PATH = VAR_DIR / "ai_cex_compliance_review_2026-05-08.json"
AI_DOC_PATH = ROOT / "docs" / "55_AI_CEX_COMPLIANCE_REVIEW_2026-05-08.md"

PLATFORMS = ("binance", "pionex", "bitget", "jupiter", "coinbase", "wiso_blockpit")
REFERENCE_MARKERS = ("blockpit", "wiso", "cointracking", "cointracker")
DERIVATIVE_MARKERS = ("future", "futures", "perp", "perps", "margin", "liquidation", "derivative")
PRIMARY_SOURCES = {
    "binance",
    "binance_api",
    "bitget_api",
    "bitget_tax_api",
    "coinbase",
    "coinbase_api",
    "jupiter_perps",
    "pionex",
    "solana_rpc",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=datetime.now(UTC).year)
    parser.add_argument("--ai", action="store_true", help="Run local Qwen review after deterministic audit.")
    parser.add_argument("--max-ai-tokens", type=int, default=1800)
    args = parser.parse_args()

    VAR_DIR.mkdir(parents=True, exist_ok=True)
    audit = build_audit(args.start_year, args.end_year)
    JSON_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(audit)
    result: dict[str, Any] | None = None
    if args.ai:
        result = run_ai_review(audit, max_tokens=args.max_ai_tokens)
        AI_JSON_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        write_ai_report(audit, result)
    print(
        json.dumps(
            {
                "json": str(JSON_PATH),
                "report": str(DOC_PATH),
                "ai_json": str(AI_JSON_PATH) if result is not None else None,
                "ai_report": str(AI_DOC_PATH) if result is not None else None,
                "effective_event_count": audit["summary"]["effective_event_count"],
            },
            indent=2,
        )
    )


def build_audit(start_year: int, end_year: int) -> dict[str, Any]:
    raw_events = STORE.list_raw_events()
    reviewed, review_summary = apply_review_actions(raw_events)
    effective_events, override_count = apply_tax_event_overrides(reviewed)
    source_files = {row["source_file_id"]: row for row in STORE.list_source_file_summaries(limit=5000)}
    file_inventory = scan_usertransfer()

    matrix = {
        platform: {str(year): empty_cell(platform, year) for year in range(start_year, end_year + 1)}
        for platform in PLATFORMS
    }
    reference_sources = {str(year): empty_cell("reference", year) for year in range(start_year, end_year + 1)}

    for event in effective_events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        year = event_year(payload)
        if year is None or year < start_year or year > end_year:
            continue
        source_file = source_files.get(str(event.get("source_file_id") or ""), {})
        source_name = str(source_file.get("source_name") or event.get("source_file_id") or "")
        platforms = classify_platforms(payload, source_name)
        if not platforms:
            continue
        for platform in platforms:
            add_event(matrix[platform][str(year)], event, payload, source_name)
        if is_reference(payload, source_name):
            add_event(reference_sources[str(year)], event, payload, source_name)

    attach_file_inventory(matrix, file_inventory, start_year, end_year)
    for platform, years in matrix.items():
        for year, cell in years.items():
            finalize_cell(cell, int(year), platform)
    for year, cell in reference_sources.items():
        finalize_cell(cell, int(year), "reference")
        if cell["effective_event_count"]:
            cell["statuses"] = ["reference_only"]
            cell["reasons"] = ["Blockpit/WISO/CoinTracking/CoinTracker sind Referenzquellen, keine primaere Wahrheit."]
        else:
            cell["statuses"] = ["no_data"]
            cell["reasons"] = ["Keine Referenzdaten im Jahr gefunden."]

    next_actions = build_next_actions(matrix, reference_sources)
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": {"start_year": start_year, "end_year": end_year, "platforms": list(PLATFORMS)},
        "summary": {
            "raw_event_count": len(raw_events),
            "effective_event_count": len(effective_events),
            "review_action_summary": review_summary,
            "override_count": override_count,
        },
        "matrix": matrix,
        "reference_sources": reference_sources,
        "file_inventory": file_inventory,
        "known_facts": known_facts(),
        "next_actions": next_actions,
    }


def empty_cell(platform: str, year: int) -> dict[str, Any]:
    return {
        "platform": platform,
        "year": int(year),
        "effective_event_count": 0,
        "primary_event_count": 0,
        "reference_event_count": 0,
        "first_event_utc": "",
        "last_event_utc": "",
        "sources": {},
        "source_files": {},
        "event_types": {},
        "assets": {},
        "side_counts": {},
        "transfer_txid_count": 0,
        "address_count": 0,
        "derivative_event_count": 0,
        "available_files": [],
        "statuses": [],
        "reasons": [],
        "_sources": Counter(),
        "_source_files": Counter(),
        "_event_types": Counter(),
        "_assets": Counter(),
        "_side_counts": Counter(),
        "_txids": set(),
        "_addresses": set(),
    }


def add_event(cell: dict[str, Any], event: dict[str, Any], payload: dict[str, Any], source_name: str) -> None:
    ts = event_ts(payload)
    source = str(payload.get("source") or "unknown")
    event_type = str(payload.get("event_type") or "unknown")
    asset = str(payload.get("asset") or payload.get("symbol") or "unknown").upper()
    side = str(payload.get("side") or "unknown")
    cell["effective_event_count"] += 1
    if is_reference(payload, source_name):
        cell["reference_event_count"] += 1
    else:
        cell["primary_event_count"] += 1
    if ts:
        cell["first_event_utc"] = min(filter(None, [cell["first_event_utc"], ts])) if cell["first_event_utc"] else ts
        cell["last_event_utc"] = max(cell["last_event_utc"], ts)
    cell["_sources"][source] += 1
    cell["_source_files"][source_name] += 1
    cell["_event_types"][event_type] += 1
    cell["_assets"][asset] += 1
    cell["_side_counts"][side] += 1
    if any(marker in event_type.lower() or marker in source.lower() for marker in DERIVATIVE_MARKERS):
        cell["derivative_event_count"] += 1
    txid = extract_txid(payload)
    if txid:
        cell["_txids"].add(txid)
    for address in extract_addresses(payload):
        cell["_addresses"].add(address)


def finalize_cell(cell: dict[str, Any], year: int, platform: str) -> None:
    cell["sources"] = top_counter(cell.pop("_sources"), 12)
    cell["source_files"] = top_counter(cell.pop("_source_files"), 12)
    cell["event_types"] = top_counter(cell.pop("_event_types"), 12)
    cell["assets"] = top_counter(cell.pop("_assets"), 12)
    cell["side_counts"] = top_counter(cell.pop("_side_counts"), 8)
    cell["transfer_txid_count"] = len(cell.pop("_txids"))
    cell["address_count"] = len(cell.pop("_addresses"))
    statuses, reasons = infer_status(cell, year, platform)
    cell["statuses"] = statuses
    cell["reasons"] = reasons


def infer_status(cell: dict[str, Any], year: int, platform: str) -> tuple[list[str], list[str]]:
    statuses: list[str] = []
    reasons: list[str] = []
    count = int(cell["effective_event_count"])
    files = cell.get("available_files") or []
    primary = int(cell["primary_event_count"])
    reference = int(cell["reference_event_count"])

    if count == 0 and not files:
        return ["no_data"], ["Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt."]
    if count == 0 and files:
        statuses.append("csv_required")
        reasons.append("Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt.")
    if count > 0 and primary == 0 and reference > 0:
        statuses.append("reference_only")
        reasons.append("Nur Referenzdaten erkannt; Primaerexport/API fehlt.")
    if count > 0 and primary > 0:
        statuses.append("partial")
        reasons.append("Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben.")

    if platform == "pionex":
        if year in {2021, 2022}:
            add_status(statuses, "opening_balance_required")
            reasons.append("Bekannte Pionex-USDT-Unterdeckung Anfang 2022; Opening-Balance/Bot-Startkapital bleibt Nachweisbedarf.")
        if year < 2021:
            add_status(statuses, "no_data")
            reasons.append("Pionex-Aktivitaet startet nach aktuellem Bestand erst Ende 2021.")
        if year >= 2024 and count == 0 and files:
            add_status(statuses, "csv_required")
            reasons.append("Pionex-Dateien vorhanden; pruefen, ob der Zeitraum wirklich importiert ist.")
    elif platform == "bitget":
        if year <= 2024 or year == 2025:
            add_status(statuses, "api_limited")
            add_status(statuses, "support_required")
            add_status(statuses, "unavailable_source_possible")
            reasons.append(
                "Bitget-Support ist angefragt; alte Spot/Bot/Grid/Internal-Transfer-Details koennen API-/Retention-bedingt fehlen."
            )
        if int(cell["derivative_event_count"]) > 0:
            add_status(statuses, "manual_review")
            reasons.append("Derivate/Hebel-Events muessen als Einsatz/Gewinn/Verlust und Liquidationen getrennt plausibilisiert werden.")
    elif platform == "binance":
        if year == 2025:
            if reference > 0:
                add_status(statuses, "manual_review")
                reasons.append(
                    "2025 enthaelt noch Blockpit-Referenzereignisse; Binance Spot/Convert/Earn/Fiat muss gegen Primaerdaten abgeglichen werden."
                )
            else:
                reasons.append(
                    "Binance 2025 ist nach aktuellem Stand primaerdatengefuehrt; Blockpit-Referenzereignisse wurden gegen API/CSV belegt und ausgeschlossen."
                )
        if year <= 2021 and count > 0:
            add_status(statuses, "manual_review")
            reasons.append("Fruehe Binance-Historie ist zentral fuer Startbestaende und Pionex-Zufluesse.")
    elif platform == "jupiter":
        if count > 0:
            add_status(statuses, "manual_review")
            reasons.append("Jupiter/Jup.ag ist Wallet-/On-Chain-nahe; Solscan/Jup-Export und Perps muessen gegeneinander abgeglichen bleiben.")
        if year >= 2024 and not files and count > 0:
            add_status(statuses, "csv_required")
            reasons.append("On-Chain-Events vorhanden, aber kein zugeordneter Jup.ag-Export fuer das Jahr erkannt.")
    elif platform == "coinbase":
        if count == 0:
            add_status(statuses, "no_data")
            reasons.append("Keine Coinbase-Daten im aktuellen Bestand erkannt.")

    if count > 0 and count < 3 and platform not in {"coinbase"}:
        add_status(statuses, "manual_review")
        reasons.append("Sehr wenige Events; pruefen, ob nur Teilhistorie oder Einzelimport vorliegt.")
    if not statuses:
        statuses.append("complete")
        reasons.append("Keine offensichtliche Luecke aus der heuristischen Matrix erkannt.")
    return compact(statuses), compact(reasons)


def classify_platforms(payload: dict[str, Any], source_name: str) -> list[str]:
    text = " ".join(
        [
            str(payload.get("source") or ""),
            str(payload.get("event_type") or ""),
            source_name,
            json.dumps(payload.get("raw_row") or {}, ensure_ascii=False)[:2000],
        ]
    ).lower()
    platforms: list[str] = []
    if "binance" in text:
        platforms.append("binance")
    if "pionex" in text:
        platforms.append("pionex")
    if "bitget" in text:
        platforms.append("bitget")
    if "jupiter" in text or "jup.ag" in text or "jupiter_perps" in text:
        platforms.append("jupiter")
    if "coinbase" in text:
        platforms.append("coinbase")
    if any(marker in text for marker in ("blockpit", "wiso")):
        platforms.append("wiso_blockpit")
    return compact(platforms)


def scan_usertransfer() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    by_platform_year: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    if not USERTRANSFER.exists():
        return {"root": str(USERTRANSFER), "files": [], "by_platform_year": {}}
    for path in sorted(USERTRANSFER.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        lower = rel.lower()
        platforms = []
        for platform in PLATFORMS:
            if platform == "wiso_blockpit":
                if "wiso" in lower or "blockpit" in lower:
                    platforms.append(platform)
            elif platform == "jupiter":
                if "jup" in lower or "wallet.wbrpoi" in lower:
                    platforms.append(platform)
            elif platform in lower:
                platforms.append(platform)
        if not platforms:
            continue
        years = sorted({year for year in range(2020, datetime.now(UTC).year + 1) if str(year) in lower})
        if not years:
            years = infer_years_from_path(lower)
        row = {
            "path": rel,
            "size_bytes": path.stat().st_size,
            "platforms": platforms,
            "years": years,
        }
        rows.append(row)
        for platform in platforms:
            target_years = years or [0]
            for year in target_years:
                by_platform_year[platform][str(year)].append(row)
    return {
        "root": str(USERTRANSFER),
        "files": rows,
        "by_platform_year": {
            platform: {year: slim_files(files) for year, files in sorted(years.items())}
            for platform, years in sorted(by_platform_year.items())
        },
    }


def infer_years_from_path(lower_path: str) -> list[int]:
    if "pionex" in lower_path and "2021-12-31_2022-12-30" in lower_path:
        return [2021, 2022]
    if "pionex" in lower_path and "2022-12-31_2023-12-30" in lower_path:
        return [2022, 2023]
    if "pionex" in lower_path and "2023-12-31_2024-12-30" in lower_path:
        return [2023, 2024]
    if "pionex/" in lower_path:
        return [2021, 2022, 2023, 2024]
    if "binance" in lower_path and "export 2021" in lower_path:
        return [2021]
    if "jup/" in lower_path:
        return [2024, 2025, 2026]
    return []


def attach_file_inventory(matrix: dict[str, dict[str, dict[str, Any]]], inventory: dict[str, Any], start_year: int, end_year: int) -> None:
    by_platform_year = inventory.get("by_platform_year") or {}
    for platform, years in matrix.items():
        platform_files = by_platform_year.get(platform) or {}
        undated = platform_files.get("0") or []
        for year in range(start_year, end_year + 1):
            files = list(platform_files.get(str(year)) or [])
            if undated:
                files.extend(undated)
            years[str(year)]["available_files"] = slim_files(files, limit=18)


def build_next_actions(matrix: dict[str, dict[str, dict[str, Any]]], reference_sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    priority = 1
    candidates = [
        ("pionex", "2022", "Pionex Opening-Balance/Bot-Startkapital Anfang 2022 belegen oder Adjustment-Review vorbereiten."),
        (
            "bitget",
            "2025",
            "Bitget-Supportantwort abwarten; falls Bot-Trade-Details nicht mehr lieferbar sind, Rekonstruktionsbericht ueber Salden/Transfers/PnL erzeugen.",
        ),
        ("binance", "2021", "Binance 2021 als Startkette fuer HNT/USDT/Pionex-Zufluesse final gegen Withdraw/Trade/Fiat-Dateien pruefen."),
        ("jupiter", "2025", "Jup.ag Export, Solscan-Transfers und Jupiter-Perps fuer 2025 gegen Wallet-Bestand abgleichen."),
    ]
    for platform, year, action in candidates:
        cell = matrix.get(platform, {}).get(year)
        if not cell:
            continue
        if platform == "binance" and year == "2025" and int(cell.get("reference_event_count", 0)) == 0:
            continue
        actions.append(
            {
                "priority": priority,
                "platform": platform,
                "year": int(year),
                "action": action,
                "current_statuses": cell.get("statuses", []),
                "reason": "; ".join(cell.get("reasons", [])[:3]),
            }
        )
        priority += 1
    for year, cell in reference_sources.items():
        if cell["effective_event_count"] and any(
            matrix.get(platform, {}).get(year, {}).get("primary_event_count", 0) == 0
            for platform in ("binance", "bitget")
        ):
            actions.append(
                {
                    "priority": priority,
                    "platform": "wiso_blockpit",
                    "year": int(year),
                    "action": "Referenzdaten nur als Suchhinweis nutzen; Primaerexport/API fuer passende Plattform beschaffen.",
                    "current_statuses": cell.get("statuses", []),
                    "reason": "Referenzereignisse ohne passende Primaerabdeckung koennen keine alleinige Steuerbasis sein.",
                }
            )
            priority += 1
    return actions


def run_ai_review(audit: dict[str, Any], *, max_tokens: int) -> dict[str, Any]:
    config = resolve_effective_runtime_config().get("runtime", {}).get("ai_review", {})
    base_url = str(config.get("llama_cpp_base_url") or "http://192.168.2.203:11435").rstrip("/")
    model = str(config.get("llama_cpp_model") or "qwen3.6-35b-a3b-iq4xs")
    compact_audit = compact_for_ai(audit)
    payload = {
        "model": model,
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du bist ein vorsichtiger Datenforensik-Assistent fuer deutsche Crypto-Steuerdaten. "
                    "Du darfst keine Buchungen erfinden und keine RAW-Daten korrigieren. "
                    "Bewerte nur Coverage, Risiken und naechste Datenbeschaffung. Antworte nur als valides JSON."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": "Pruefe diese CEX-Coverage-Matrix auf priorisierte Luecken und CEX-Konformitaet.",
                        "audit": compact_audit,
                        "required_json": {
                            "summary": "kurze Einschaetzung",
                            "ranked_gaps": [
                                {
                                    "rank": 1,
                                    "platform": "string",
                                    "year": 2025,
                                    "risk": "high|medium|low",
                                    "gap": "konkrete Luecke",
                                    "evidence": "welche Daten zeigen das",
                                }
                            ],
                            "next_data_requests": [
                                {
                                    "platform": "string",
                                    "period": "YYYY or date range",
                                    "data_type": "string",
                                    "why_needed": "string",
                                }
                            ],
                            "risk_by_tax_year": [{"year": 2025, "risk": "high|medium|low", "reason": "string"}],
                            "safe_automation_steps": ["deterministische Schritte"],
                            "do_not_auto_apply": ["was nicht automatisch gebucht werden darf"],
                        },
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        ],
    }
    started = time.time()
    try:
        response = httpx.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            timeout=float(config.get("llama_cpp_timeout_seconds") or 900),
        )
        response.raise_for_status()
        body = response.json()
        usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
        content = body["choices"][0]["message"]["content"]
        return {
            "status": "success",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "duration_seconds": round(time.time() - started, 3),
            "base_url": base_url,
            "model": model,
            "usage": usage,
            "analysis": json.loads(content),
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


def compact_for_ai(audit: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for platform, years in audit["matrix"].items():
        for year, cell in years.items():
            if cell["effective_event_count"] or cell["available_files"] or "no_data" not in cell["statuses"]:
                rows.append(
                    {
                        "platform": platform,
                        "year": int(year),
                        "statuses": cell["statuses"],
                        "event_count": cell["effective_event_count"],
                        "primary": cell["primary_event_count"],
                        "reference": cell["reference_event_count"],
                        "first": cell["first_event_utc"],
                        "last": cell["last_event_utc"],
                        "top_sources": cell["sources"][:5],
                        "top_types": cell["event_types"][:5],
                        "reasons": cell["reasons"][:5],
                        "file_count": len(cell["available_files"]),
                    }
                )
    return {
        "summary": audit["summary"],
        "known_facts": audit["known_facts"],
        "rows": rows,
        "next_actions": audit["next_actions"],
    }


def write_report(audit: dict[str, Any]) -> None:
    lines = [
        "# CEX Compliance Coverage - 2026-05-08",
        "",
        "## Scope",
        "",
        f"- Erstellt: `{audit['created_at_utc']}`",
        f"- Roh-Events: `{audit['summary']['raw_event_count']}`",
        f"- Effektive Events nach Review/Overrides: `{audit['summary']['effective_event_count']}`",
        f"- JSON: `{JSON_PATH}`",
        "",
        "## Status-Legende",
        "",
        "- `complete`: keine offensichtliche Luecke aus der Matrix",
        "- `partial`: Primaerdaten vorhanden, Vollstaendigkeit nicht final belegt",
        "- `api_limited`: API-/Historienlimit bekannt",
        "- `csv_required`: Datei/Export erforderlich oder liegt nur unimportiert vor",
        "- `support_required`: Support/Statement benoetigt",
        "- `unavailable_source_possible`: Quelle koennte historisch nicht mehr beschaffbar sein",
        "- `opening_balance_required`: Startbestand/Botkapital muss belegt werden",
        "- `manual_review`: fachliche Pruefung erforderlich",
        "- `reference_only`: nur Referenzquelle, keine Primaerquelle",
        "- `no_data`: keine Daten erkannt",
        "",
        "## Matrix",
        "",
        "| Plattform | Jahr | Status | Events | Primaer | Referenz | Zeitraum | Top-Quellen | Hinweise |",
        "|---|---:|---|---:|---:|---:|---|---|---|",
    ]
    for platform, years in audit["matrix"].items():
        for year in sorted(years, key=int):
            cell = years[year]
            top_sources = ", ".join(f"{row['key']}:{row['count']}" for row in cell["sources"][:3]) or "-"
            period = f"{cell['first_event_utc'][:10]}..{cell['last_event_utc'][:10]}" if cell["first_event_utc"] else "-"
            reasons = " / ".join(cell["reasons"][:2]).replace("|", "/")
            lines.append(
                f"| `{platform}` | {year} | `{', '.join(cell['statuses'])}` | {cell['effective_event_count']} | "
                f"{cell['primary_event_count']} | {cell['reference_event_count']} | {period} | {top_sources} | {reasons} |"
            )
    lines += [
        "",
        "## Referenzquellen",
        "",
        "| Jahr | Events | Zeitraum | Top-Quellen |",
        "|---:|---:|---|---|",
    ]
    for year, cell in sorted(audit["reference_sources"].items(), key=lambda item: int(item[0])):
        top_sources = ", ".join(f"{row['key']}:{row['count']}" for row in cell["sources"][:4]) or "-"
        period = f"{cell['first_event_utc'][:10]}..{cell['last_event_utc'][:10]}" if cell["first_event_utc"] else "-"
        lines.append(f"| {year} | {cell['effective_event_count']} | {period} | {top_sources} |")
    lines += ["", "## Bekannte Fakten", ""]
    lines += [f"- {item}" for item in audit["known_facts"]]
    lines += ["", "## Naechste Datenaufgaben", ""]
    for item in audit["next_actions"]:
        lines.append(
            f"- `{item['priority']}` `{item['platform']}` `{item['year']}`: {item['action']} "
            f"(Status: `{', '.join(item['current_statuses'])}`)"
        )
    lines += ["", "## File-Inventar Kurzfassung", ""]
    by_platform_year = audit["file_inventory"].get("by_platform_year") or {}
    for platform in sorted(by_platform_year):
        total = sum(len(files) for files in by_platform_year[platform].values())
        lines.append(f"- `{platform}`: {total} platform/year-Dateizuordnungen")
    lines.append("")
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_ai_report(audit: dict[str, Any], result: dict[str, Any]) -> None:
    analysis = result.get("analysis") if isinstance(result.get("analysis"), dict) else {}
    lines = [
        "# AI CEX Compliance Review - 2026-05-08",
        "",
        f"- Coverage JSON: `{JSON_PATH}`",
        f"- AI JSON: `{AI_JSON_PATH}`",
        f"- Status: `{result.get('status')}`",
        f"- Modell: `{result.get('model')}`",
        f"- Endpoint: `{result.get('base_url')}`",
        f"- Dauer Sekunden: `{result.get('duration_seconds')}`",
    ]
    usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
    if usage:
        lines.append(f"- Usage: `{json.dumps(usage, ensure_ascii=False)}`")
    lines += ["", "## Zusammenfassung", "", str(analysis.get("summary") or result.get("error") or "")]
    lines += ["", "## Priorisierte Luecken", ""]
    for item in analysis.get("ranked_gaps", []):
        lines.append(
            f"- `{item.get('rank')}` `{item.get('platform')}` `{item.get('year')}` "
            f"risk `{item.get('risk')}`: {item.get('gap')} | evidence: {item.get('evidence')}"
        )
    lines += ["", "## Datenanforderungen", ""]
    for item in analysis.get("next_data_requests", []):
        lines.append(
            f"- `{item.get('platform')}` `{item.get('period')}` `{item.get('data_type')}`: {item.get('why_needed')}"
        )
    lines += ["", "## Risiko je Steuerjahr", ""]
    for item in analysis.get("risk_by_tax_year", []):
        lines.append(f"- `{item.get('year')}` risk `{item.get('risk')}`: {item.get('reason')}")
    lines += ["", "## Sichere Automatisierung", ""]
    lines += [f"- {item}" for item in analysis.get("safe_automation_steps", [])]
    lines += ["", "## Nicht automatisch anwenden", ""]
    lines += [f"- {item}" for item in analysis.get("do_not_auto_apply", [])]
    lines.append("")
    AI_DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def event_year(payload: dict[str, Any]) -> int | None:
    ts = event_ts(payload)
    if len(ts) >= 4 and ts[:4].isdigit():
        return int(ts[:4])
    return None


def event_ts(payload: dict[str, Any]) -> str:
    return str(payload.get("timestamp_utc") or payload.get("timestamp") or payload.get("date") or "")


def extract_txid(payload: dict[str, Any]) -> str:
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    for key in ("tx_id", "txid", "transaction_hash", "signature", "TxID", "Transaction ID", "Hash"):
        value = payload.get(key) if key in payload else raw.get(key)
        if value:
            return str(value).strip()
    return ""


def extract_addresses(payload: dict[str, Any]) -> set[str]:
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    addresses: set[str] = set()
    for key, value in list(payload.items()) + list(raw.items()):
        if not value or not isinstance(value, (str, int)):
            continue
        key_l = str(key).lower()
        if "address" in key_l or key_l in {"from", "to", "from_address", "to_address", "wallet"}:
            text = str(value).strip()
            if 20 <= len(text) <= 80 and " " not in text:
                addresses.add(text)
    return addresses


def is_reference(payload: dict[str, Any], source_name: str) -> bool:
    source = str(payload.get("source") or "").lower().strip()
    if source in PRIMARY_SOURCES:
        return False
    text = f"{source} {source_name}".lower()
    return any(marker in text for marker in REFERENCE_MARKERS)


def top_counter(counter: Counter[str], limit: int) -> list[dict[str, Any]]:
    return [{"key": str(key), "count": int(count)} for key, count in counter.most_common(limit)]


def slim_files(files: list[dict[str, Any]], limit: int = 25) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for row in files:
        unique[row["path"]] = {"path": row["path"], "size_bytes": row["size_bytes"]}
    return list(unique.values())[:limit]


def add_status(statuses: list[str], status: str) -> None:
    if status not in statuses:
        statuses.append(status)


def compact(items: list[Any]) -> list[Any]:
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def known_facts() -> list[str]:
    return [
        "RAW-Daten werden nicht geloescht oder still korrigiert; nur Review/Overrides/Adjustments.",
        "Pionex TRC20 Deposit-Adresse TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ hat 4 bekannte USDT-Deposits und 4 Sweeps.",
        "Die 4 bekannten Pionex-USDT-Deposits matchen Binance-Withdrawals per TXID.",
        "Bekannte Pionex-only USDT-Unterdeckung Anfang 2022 bleibt Opening-Balance/Bot-Startkapital-Thema.",
        "Bitget alte Spot-/Bot-/Grid-/Internal-Transfer-Historie ist per API limitiert; Support ist angefragt.",
        "Wenn Bitget alte Bot-Trade-Details nicht mehr liefern kann, wird die Luecke als unavailable_source_possible dokumentiert und nur ueber belegbare Salden/Transfers/PnL plausibilisiert.",
        "Blockpit/WISO sind eingereichte oder externe Referenzen, aber keine primaere Wahrheit.",
        "Jupiter/Jup.ag ist wallet-/on-chain-nah und muss gegen Solscan/Jup-Export/Jupiter-Perps abgeglichen werden.",
    ]


if __name__ == "__main__":
    os.environ.setdefault("PYTHONPATH", str(ROOT / "src"))
    main()
