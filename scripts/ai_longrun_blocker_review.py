#!/usr/bin/env python3
"""Run a read-only long-running local-LLM review over open tax-report blockers.

The script orchestrates work; llama.cpp only answers individual prompts.
It writes Markdown/JSONL evidence reports and never changes raw events, overrides,
or review candidates.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import resolve_effective_runtime_config

VAR_DIR = ROOT / "var"
DOCS_DIR = ROOT / "docs"
STATUS_PATH = VAR_DIR / "ai_longrun_blocker_review_status.json"
RESULTS_PATH = VAR_DIR / "ai_longrun_blocker_review_results.jsonl"
DOC_PATH = DOCS_DIR / "86_AI_LONGRUN_BLOCKER_REVIEW_2026-05-08.md"
LOG_PATH = VAR_DIR / "ai_longrun_blocker_review.log"

DEFAULT_INPUTS = {
    "handoff": "docs/99_CHAT_HANDOFF_AKTUELL.md",
    "readiness": "docs/79_TAX_REPORT_READINESS_STATUS_2026-05-08.md",
    "pionex_reconstruction": "docs/84_PIONEX_OPENING_RECONSTRUCTION_AUDIT_2026-05-08.md",
    "bitget_remaining": "docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md",
    "jupiter_2025": "docs/80_JUPITER_2025_SOLSCAN_COVERAGE_AUDIT_2026-05-08.md",
    "dust_detail": "docs/83_DUST_RESIDUAL_DETAIL_AUDIT_2026-05-08.md",
    "cex_coverage": "docs/54_CEX_COMPLIANCE_COVERAGE_2026-05-08.md",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only 16h local LLM blocker review supervisor.")
    parser.add_argument("--max-hours", type=float, default=16.0)
    parser.add_argument("--max-tasks", type=int, default=20)
    parser.add_argument("--sleep-seconds", type=float, default=10.0)
    parser.add_argument("--max-input-chars", type=int, default=52000)
    parser.add_argument("--max-output-tokens", type=int, default=2200)
    parser.add_argument("--base-url", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--temperature", type=float, default=-1.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    VAR_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    started = _now()
    deadline = time.time() + max(args.max_hours, 0.01) * 3600
    tasks = _tasks()
    if args.max_tasks > 0:
        tasks = tasks[: args.max_tasks]
    config = _llm_config(args)

    _write_status(
        {
            "status": "running",
            "started_at_utc": started,
            "updated_at_utc": _now(),
            "task_count": len(tasks),
            "completed_count": 0,
            "current_task": "",
            "result_path": str(RESULTS_PATH),
            "doc_path": str(DOC_PATH),
            "llm": config,
            "dry_run": args.dry_run,
        }
    )
    _initialize_doc(started, tasks, config, dry_run=args.dry_run)
    _log("started ai_longrun_blocker_review")

    completed = 0
    try:
        for task in tasks:
            if time.time() >= deadline:
                break
            _write_status(
                {
                    "status": "running",
                    "started_at_utc": started,
                    "updated_at_utc": _now(),
                    "task_count": len(tasks),
                    "completed_count": completed,
                    "current_task": task["task_id"],
                    "result_path": str(RESULTS_PATH),
                    "doc_path": str(DOC_PATH),
                    "llm": config,
                    "dry_run": args.dry_run,
                }
            )
            result = _run_task(task, config=config, max_input_chars=args.max_input_chars, max_output_tokens=args.max_output_tokens, dry_run=args.dry_run)
            completed += 1
            _append_jsonl(RESULTS_PATH, result)
            _append_doc_result(result)
            _log(f"completed {completed}/{len(tasks)} {task['task_id']} status={result.get('status')}")
            if time.time() < deadline:
                time.sleep(max(args.sleep_seconds, 0.0))

        final_status = "completed" if completed == len(tasks) else "stopped_by_deadline"
        _write_status(
            {
                "status": final_status,
                "started_at_utc": started,
                "updated_at_utc": _now(),
                "task_count": len(tasks),
                "completed_count": completed,
                "current_task": "",
                "result_path": str(RESULTS_PATH),
                "doc_path": str(DOC_PATH),
                "llm": config,
                "dry_run": args.dry_run,
            }
        )
        _log(f"finished status={final_status}")
    except BaseException as exc:
        _write_status(
            {
                "status": "error",
                "started_at_utc": started,
                "updated_at_utc": _now(),
                "task_count": len(tasks),
                "completed_count": completed,
                "current_task": "",
                "error": f"{type(exc).__name__}: {exc}",
                "result_path": str(RESULTS_PATH),
                "doc_path": str(DOC_PATH),
                "llm": config,
                "dry_run": args.dry_run,
            }
        )
        _log(f"fatal {type(exc).__name__}: {exc}")
        raise


def _tasks() -> list[dict[str, Any]]:
    base_inputs = ["handoff", "readiness"]
    return [
        {
            "task_id": "bitget_2025_unavailable_source_dossier",
            "title": "Bitget 2025 unavailable-source dossier",
            "inputs": base_inputs + ["bitget_remaining", "cex_coverage"],
            "question": (
                "Erstelle ein fachliches Dossier zu Bitget 2025. Welche Daten sind primaer belegt, "
                "welche aktiven Blockpit-Referenzen bleiben offen, und welche konkrete Supportanfrage/"
                "unavailable-source-Entscheidung ist noetig? Keine Buchungen vorschlagen."
            ),
        },
        {
            "task_id": "bitget_2025_symbol_month_risk",
            "title": "Bitget 2025 symbol/month risk map",
            "inputs": base_inputs + ["bitget_remaining"],
            "question": (
                "Erzeuge eine Ampelliste nach Monat und Symbol fuer die offenen Bitget-Referenzen. "
                "Trenne Fees, PnL, Liquidationen, Trades und Margin/Borrow/Repay. Bewerte nur "
                "Nachweisqualitaet, nicht Steuerhoehe."
            ),
        },
        {
            "task_id": "pionex_opening_reconstruction_argument",
            "title": "Pionex opening reconstruction argument",
            "inputs": base_inputs + ["pionex_reconstruction"],
            "question": (
                "Bewerte die Pionex-Opening-Ersatzrekonstruktion. Liefere Pro/Contra, belegte Fakten, "
                "Restrisiko und welche Formulierung fuer eine manuelle Review-Entscheidung geeignet waere. "
                "Keine Aktivierung des Kandidaten empfehlen, nur Entscheidungsgrundlage."
            ),
        },
        {
            "task_id": "jupiter_remaining_years_plan",
            "title": "Jupiter remaining years control plan",
            "inputs": base_inputs + ["jupiter_2025", "cex_coverage"],
            "question": (
                "2025 ist erledigt. Leite daraus einen konkreten Read-only-Pruefplan fuer Jupiter 2023, "
                "2024 und 2026 ab: welche Solscan/Solana/Jupiter-Perps-Belege muessen verglichen werden, "
                "welche Abschlusskriterien nehmen ein Jahr aus der Blockerliste?"
            ),
        },
        {
            "task_id": "dust_vtho_busd_decision_basis",
            "title": "Dust VTHO/BUSD decision basis",
            "inputs": base_inputs + ["dust_detail"],
            "question": (
                "Bewerte VTHO und BUSD als Dust-/Altbestandsreste. Welche Belege sprechen fuer "
                "Mini-Residual, welche Gegenbelege fehlen, und welche Review-Entscheidung waere "
                "fachlich sauber dokumentierbar?"
            ),
        },
        {
            "task_id": "final_readiness_traffic_light",
            "title": "Final readiness traffic light",
            "inputs": list(DEFAULT_INPUTS),
            "question": (
                "Erstelle eine konsolidierte Ampelliste fuer den Steuerreport: gruen belegbar, gelb "
                "ersatzrekonstruiert, rot fremddatenabhaengig. Nenne je Punkt den entscheidenden "
                "naechsten Schritt und die zugehoerigen Reportdateien."
            ),
        },
    ]


def _run_task(
    task: dict[str, Any],
    *,
    config: dict[str, Any],
    max_input_chars: int,
    max_output_tokens: int,
    dry_run: bool,
) -> dict[str, Any]:
    prompt_data = {
        "safety_boundary": [
            "READ ONLY.",
            "Keine RAW-Daten aendern.",
            "Keine Overrides setzen.",
            "Keine Kandidaten tax_effective=true setzen.",
            "Keine Blockpit-Referenz als Primary umdeuten.",
            "Nur Analyse, Ampeln, Dossier und konkrete naechste Pruefschritte.",
        ],
        "task_id": task["task_id"],
        "question": task["question"],
        "input_documents": _load_inputs(task["inputs"], max_chars=max_input_chars),
        "required_output": {
            "summary": "kurze Zusammenfassung",
            "traffic_light": "green|yellow|red",
            "confirmed_facts": ["belegte Fakten mit Dateiverweis"],
            "open_risks": ["offene Risiken"],
            "recommended_next_steps": ["konkrete naechste Schritte"],
            "must_not_do": ["verbotene automatische Aktionen"],
        },
    }
    started = time.time()
    if dry_run:
        return {
            "task_id": task["task_id"],
            "title": task["title"],
            "status": "dry_run",
            "created_at_utc": _now(),
            "duration_seconds": 0,
            "analysis": {
                "summary": "Dry run: prompt assembled, LLM not called.",
                "traffic_light": "yellow",
                "confirmed_facts": [],
                "open_risks": [],
                "recommended_next_steps": [],
                "must_not_do": [],
            },
            "usage": {},
        }

    payload = {
        "model": config["model"],
        "temperature": config["temperature"],
        "max_tokens": max_output_tokens,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du bist ein vorsichtiger deutscher Crypto-Steuer-Datenforensik-Assistent. "
                    "Arbeite strikt read-only. Antworte ausschliesslich mit validem JSON."
                ),
            },
            {"role": "user", "content": json.dumps(prompt_data, ensure_ascii=False, separators=(",", ":"))},
        ],
    }
    try:
        with httpx.Client(timeout=float(config["timeout_seconds"])) as client:
            response = client.post(f"{config['base_url'].rstrip('/')}/v1/chat/completions", json=payload)
            response.raise_for_status()
            body = response.json()
        content = str(body["choices"][0]["message"]["content"])
        try:
            analysis = json.loads(content)
            status = "success"
        except json.JSONDecodeError:
            analysis = {"summary": content, "traffic_light": "yellow", "confirmed_facts": [], "open_risks": ["LLM returned non-JSON"], "recommended_next_steps": [], "must_not_do": []}
            status = "non_json"
        return {
            "task_id": task["task_id"],
            "title": task["title"],
            "status": status,
            "created_at_utc": _now(),
            "duration_seconds": round(time.time() - started, 3),
            "analysis": analysis,
            "usage": body.get("usage", {}),
            "llm": {"base_url": config["base_url"], "model": config["model"]},
        }
    except Exception as exc:
        return {
            "task_id": task["task_id"],
            "title": task["title"],
            "status": "error",
            "created_at_utc": _now(),
            "duration_seconds": round(time.time() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
            "analysis": {
                "summary": "LLM-Aufruf fehlgeschlagen.",
                "traffic_light": "red",
                "confirmed_facts": [],
                "open_risks": [f"{type(exc).__name__}: {exc}"],
                "recommended_next_steps": ["Endpoint/Modell pruefen und Task erneut starten."],
                "must_not_do": ["Keine automatischen Buchungen aus Fehlerlauf ableiten."],
            },
            "usage": {},
            "llm": {"base_url": config["base_url"], "model": config["model"]},
        }


def _load_inputs(input_keys: list[str], *, max_chars: int) -> dict[str, str]:
    remaining = max(max_chars, 1000)
    loaded: dict[str, str] = {}
    for key in input_keys:
        rel = DEFAULT_INPUTS.get(key, key)
        path = ROOT / rel
        text = _read_text(path)
        if len(text) > remaining:
            text = text[:remaining] + "\n\n[TRUNCATED]\n"
        loaded[rel] = text
        remaining -= len(text)
        if remaining <= 0:
            break
    return loaded


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"[missing file: {path.relative_to(ROOT)}]"


def _llm_config(args: argparse.Namespace) -> dict[str, Any]:
    runtime = resolve_effective_runtime_config().get("runtime", {}).get("ai_review", {})
    return {
        "base_url": str(args.base_url or runtime.get("llama_cpp_base_url") or "http://192.168.2.203:11435").rstrip("/"),
        "model": str(args.model or runtime.get("llama_cpp_model") or "qwen3.6-35b-a3b-iq4xs"),
        "timeout_seconds": float(runtime.get("llama_cpp_timeout_seconds") or 900),
        "temperature": float(args.temperature if args.temperature >= 0 else runtime.get("llama_cpp_temperature") or 0.1),
    }


def _initialize_doc(started_at: str, tasks: list[dict[str, Any]], config: dict[str, Any], *, dry_run: bool) -> None:
    lines = [
        "# AI Longrun Blocker Review 2026-05-08",
        "",
        f"- Started: `{started_at}`",
        f"- Endpoint: `{config['base_url']}`",
        f"- Model: `{config['model']}`",
        f"- Dry run: `{dry_run}`",
        f"- Status: `{STATUS_PATH.relative_to(ROOT)}`",
        f"- JSONL: `{RESULTS_PATH.relative_to(ROOT)}`",
        "",
        "## Safety Boundary",
        "",
        "- Read-only only.",
        "- Keine RAW-Daten, Overrides oder Kandidaten veraendern.",
        "- Keine Referenzdaten automatisch als Primary umdeuten.",
        "",
        "## Task Queue",
        "",
    ]
    for index, task in enumerate(tasks, start=1):
        lines.append(f"{index}. `{task['task_id']}` - {task['title']}")
    lines.append("")
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def _append_doc_result(result: dict[str, Any]) -> None:
    analysis = result.get("analysis") if isinstance(result.get("analysis"), dict) else {}
    lines = [
        "",
        f"## {result.get('title') or result.get('task_id')}",
        "",
        f"- Task: `{result.get('task_id')}`",
        f"- Status: `{result.get('status')}`",
        f"- Duration seconds: `{result.get('duration_seconds')}`",
        f"- Traffic light: `{analysis.get('traffic_light', '')}`",
        "",
        "### Summary",
        "",
        str(analysis.get("summary") or ""),
        "",
        "### Confirmed Facts",
        "",
    ]
    for item in _as_list(analysis.get("confirmed_facts")):
        lines.append(f"- {item}")
    lines += ["", "### Open Risks", ""]
    for item in _as_list(analysis.get("open_risks")):
        lines.append(f"- {item}")
    lines += ["", "### Recommended Next Steps", ""]
    for item in _as_list(analysis.get("recommended_next_steps")):
        lines.append(f"- {item}")
    lines += ["", "### Must Not Do", ""]
    for item in _as_list(analysis.get("must_not_do")):
        lines.append(f"- {item}")
    with DOC_PATH.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value in (None, ""):
        return []
    return [str(value)]


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def _write_status(payload: dict[str, Any]) -> None:
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _log(message: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{_now()} {message}\n")


def _now() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    main()
