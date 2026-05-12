#!/usr/bin/env python3
"""Read-only local-LLM review for the Bitget 2025 API/Blockpit gap."""

from __future__ import annotations

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

CREATED_DATE = "2026-05-09"
INPUTS = {
    "api_probe": ROOT / "var" / f"bitget_2025_api_deep_probe_{CREATED_DATE}.json",
    "blockpit_import": ROOT / "var" / f"blockpit_reference_export_import_{CREATED_DATE}.json",
    "global_match": ROOT / "var" / f"bitget_2025_blockpit_global_match_{CREATED_DATE}.json",
}
JSON_PATH = ROOT / "var" / f"ai_bitget_2025_blockpit_review_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"91_AI_BITGET_2025_BLOCKPIT_REVIEW_{CREATED_DATE}.md"


def main() -> None:
    config = llm_config()
    facts = build_prompt_facts()
    payload = {
        "model": config["model"],
        "temperature": config["temperature"],
        "max_tokens": 1800,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du bist ein vorsichtiger deutscher Crypto-Steuer-Datenforensik-Assistent. "
                    "Arbeite strikt read-only und antworte nur als valides JSON. "
                    "Keine Buchungen, keine Overrides, keine Umdeutung von Blockpit als Primaerquelle."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "safety_boundary": [
                            "READ ONLY",
                            "Blockpit ist Referenz/Suchanker, nicht automatisch Primaerquelle",
                            "Bitget-API/Support/On-Chain-Belege bleiben bevorzugte Primaerquellen",
                            "Keine Steuerwerte erfinden",
                        ],
                        "question": (
                            "Bewerte den aktuellen Bitget-2025-Stand nach API-Probe, neuem Blockpit-Export "
                            "und globalem Matching. Liefere Prioritaeten fuer die naechsten Pruefschritte, "
                            "insbesondere wie die 2923 offenen effektiven Blockpit-Referenzzeilen zu clustern sind."
                        ),
                        "facts": facts,
                        "required_output": {
                            "summary": "kurz",
                            "traffic_light": "green|yellow|red",
                            "confirmed_facts": ["belegte Fakten"],
                            "risk_clusters": ["Cluster nach Monat/Typ/Asset"],
                            "recommended_next_steps": ["konkrete Pruefschritte"],
                            "must_not_do": ["verbotene Aktionen"],
                        },
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        ],
    }
    started = time.time()
    with httpx.Client(timeout=config["timeout_seconds"]) as client:
        response = client.post(f"{config['base_url'].rstrip('/')}/v1/chat/completions", json=payload)
        response.raise_for_status()
        raw = response.json()
    content = str(raw.get("choices", [{}])[0].get("message", {}).get("content") or "{}")
    try:
        analysis = json.loads(content)
    except json.JSONDecodeError:
        analysis = {"summary": content, "parse_error": "invalid_json"}
    result = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "duration_seconds": round(time.time() - started, 3),
        "llm": config,
        "usage": raw.get("usage", {}),
        "input_files": {key: str(value) for key, value in INPUTS.items()},
        "analysis": analysis,
    }
    JSON_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(result), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "usage": result["usage"]}, indent=2, ensure_ascii=False))


def llm_config() -> dict[str, Any]:
    runtime = resolve_effective_runtime_config().get("runtime", {}).get("ai_review", {})
    base_url = str(runtime.get("llama_cpp_base_url") or runtime.get("ollama_base_url") or "http://127.0.0.1:11435")
    return {
        "base_url": base_url,
        "model": str(runtime.get("llama_cpp_model") or runtime.get("ollama_model") or "local-model"),
        "temperature": float(runtime.get("llama_cpp_temperature", runtime.get("ollama_temperature", 0.1))),
        "timeout_seconds": float(runtime.get("llama_cpp_timeout_seconds", 240.0)),
    }


def build_prompt_facts() -> dict[str, Any]:
    api_probe = load_json(INPUTS["api_probe"])
    blockpit = load_json(INPUTS["blockpit_import"])
    match = load_json(INPUTS["global_match"])
    return {
        "api_probe_summary": api_probe.get("summary", {}),
        "api_probe_interpretation": api_probe.get("interpretation", []),
        "blockpit_import_compact": {
            "raw_row_count": blockpit.get("raw_row_count"),
            "normalized_row_count": blockpit.get("normalized_row_count"),
            "raw_summary": blockpit.get("raw_summary", {}),
            "normalized_summary": blockpit.get("normalized_summary", {}),
            "import_result": blockpit.get("import_result"),
            "interpretation": blockpit.get("interpretation", []),
        },
        "global_match_summary": {
            key: match.get(key)
            for key in (
                "primary_count",
                "reference_count",
                "matched_count",
                "unmatched_count",
                "effective_matched_reference_count",
                "effective_unmatched_reference_count",
                "primary_source_counts",
                "reference_label_counts",
                "matched_label_counts",
                "effective_unmatched_label_counts",
                "effective_unmatched_month_counts",
                "effective_unmatched_asset_counts",
                "match_basis_counts",
                "recommendation",
            )
        },
        "open_reference_sample": match.get("effective_unmatched_reference_rows", [])[:40],
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_doc(result: dict[str, Any]) -> str:
    analysis = result.get("analysis", {})
    lines = [
        "# AI Bitget 2025 Blockpit Review - 2026-05-09",
        "",
        "## Lauf",
        "",
        f"- Dauer: `{result['duration_seconds']}s`",
        f"- LLM: `{result['llm'].get('base_url')}` / `{result['llm'].get('model')}`",
        f"- Usage: `{result.get('usage', {})}`",
        "",
        "## Summary",
        "",
        str(analysis.get("summary", "")),
        "",
        f"- Ampel: `{analysis.get('traffic_light', '')}`",
        "",
        "## Confirmed Facts",
        "",
    ]
    for item in ensure_list(analysis.get("confirmed_facts")):
        lines.append(f"- {item}")
    lines += ["", "## Risk Clusters", ""]
    for item in ensure_list(analysis.get("risk_clusters")):
        lines.append(f"- {item}")
    lines += ["", "## Recommended Next Steps", ""]
    for item in ensure_list(analysis.get("recommended_next_steps")):
        lines.append(f"- {item}")
    lines += ["", "## Must Not Do", ""]
    for item in ensure_list(analysis.get("must_not_do")):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []


if __name__ == "__main__":
    main()
