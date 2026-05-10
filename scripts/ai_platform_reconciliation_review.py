#!/usr/bin/env python3
"""Ask the local llama.cpp model for reconciliation hypotheses from deterministic ledger facts."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CREATED_DATE = "2026-05-09"
SIM_JSON = ROOT / "var" / f"platform_balance_simulation_{CREATED_DATE}.json"
TRANSFERS_JSON = ROOT / "var" / f"platform_transfer_groups_{CREATED_DATE}.json"
OUTPUT_JSON = ROOT / "var" / f"ai_platform_reconciliation_review_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"133_AI_PLATFORM_RECONCILIATION_REVIEW_{CREATED_DATE}.md"
BASE_URL = os.getenv("LLAMA_CPP_BASE_URL", "http://192.168.2.203:11435").rstrip("/")
MODEL = os.getenv("LLAMA_CPP_MODEL", "qwen3.6-35b-a3b-iq4xs")


def main() -> None:
    simulation = read_json(SIM_JSON)
    transfers = read_json(TRANSFERS_JSON)
    prompt_payload = {
        "negative_assets": (simulation.get("negative_assets") or [])[:12],
        "first_timeline_breaks": (simulation.get("first_timeline_breaks") or [])[:20],
        "unmatched_transfer_like": (transfers.get("unmatched_transfer_like") or [])[:30],
        "transfer_group_count": transfers.get("transfer_group_count"),
    }
    audit: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "model": MODEL,
        "base_url": BASE_URL,
        "status": "not_run",
        "request_scope": {
            "negative_assets": len(prompt_payload["negative_assets"]),
            "first_timeline_breaks": len(prompt_payload["first_timeline_breaks"]),
            "unmatched_transfer_like": len(prompt_payload["unmatched_transfer_like"]),
        },
        "hypotheses": [],
        "raw_response": "",
        "finish_reason": "",
        "usage": {},
        "reasoning_content_present": False,
        "error": "",
    }
    try:
        model_result = call_model(prompt_payload)
        audit["raw_response"] = model_result["content"]
        audit["finish_reason"] = model_result["finish_reason"]
        audit["usage"] = model_result["usage"]
        audit["reasoning_content_present"] = model_result["reasoning_content_present"]
        content = model_result["content"]
        parsed = parse_json_object(content)
        audit["hypotheses"] = parsed.get("hypotheses", []) if isinstance(parsed, dict) else []
        audit["status"] = "success"
    except Exception as exc:  # noqa: BLE001
        audit["status"] = "failed"
        audit["error"] = str(exc)
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(DOC_PATH), "status": audit["status"]}, ensure_ascii=False, indent=2))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def call_model(facts: dict[str, Any]) -> dict[str, Any]:
    system = (
        "Du pruefst Krypto-Plattform-Salden fuer einen deutschen Steuerreport. "
        "Nutze keine versteckten Denkspuren und keinen Thinking Mode. "
        "Antworte ausschliesslich als JSON-Objekt mit dem Feld hypotheses. "
        "Erzeuge maximal 8 Hypothesen und fasse evidence sowie next_action kurz. "
        "Jede Hypothese braucht: priority, platform, asset, evidence, likely_cause, next_action. "
        "Erfinde keine Transaktionen; nutze nur die gelieferten Fakten."
    )
    user = "Deterministische Ledger-Fakten:\n" + json.dumps(facts, ensure_ascii=False, indent=2)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "max_tokens": 2500,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        f"{BASE_URL}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"llama.cpp HTTP {exc.code}: {body[:500]}") from exc
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("llama.cpp returned no choices")
    choice = choices[0]
    message = choice.get("message") or {}
    content = str(message.get("content") or "").strip()
    if not content:
        raise RuntimeError("llama.cpp returned empty content")
    return {
        "content": content,
        "finish_reason": str(choice.get("finish_reason") or ""),
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
        "# AI Platform Reconciliation Review - 2026-05-09",
        "",
        "## Lauf",
        "",
        f"- Status: `{audit['status']}`",
        f"- Modell: `{audit['model']}`",
        f"- Endpoint: `{audit['base_url']}`",
        f"- Finish Reason: `{audit.get('finish_reason', '')}`",
        f"- Reasoning Content vorhanden: `{audit.get('reasoning_content_present', False)}`",
        "",
        "## Hypothesen",
        "",
    ]
    if audit["status"] != "success":
        lines.append(f"- KI-Lauf fehlgeschlagen: `{audit.get('error', '')}`")
    elif not audit.get("hypotheses"):
        lines.append("- Keine Hypothesen geliefert.")
    else:
        for item in audit["hypotheses"][:40]:
            lines.append(
                f"- `{item.get('priority', '')}` `{item.get('platform', '')}` `{item.get('asset', '')}`: "
                f"{item.get('likely_cause', '')} | Aktion: {item.get('next_action', '')}"
            )
    lines += [
        "",
        "## Hinweis",
        "",
        "- Diese KI-Auswertung ist nur eine Hypothesenliste. Verbindlich bleiben Ledger, Quellbelege und deterministic scripts.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
