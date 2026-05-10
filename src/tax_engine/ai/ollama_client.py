from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


class OllamaReviewError(RuntimeError):
    pass


@dataclass(frozen=True)
class OllamaReviewConfig:
    base_url: str
    model: str
    timeout_seconds: float = 120.0
    temperature: float = 0.1
    num_ctx: int = 4096


@dataclass(frozen=True)
class OpenAICompatibleReviewConfig:
    base_url: str
    model: str
    timeout_seconds: float = 120.0
    temperature: float = 0.1
    max_tokens: int = 384


def analyze_issue_with_ollama(
    context_payload: dict[str, Any],
    config: OllamaReviewConfig,
) -> dict[str, Any]:
    base_url = config.base_url.rstrip("/")
    if not base_url:
        raise OllamaReviewError("ollama_base_url_missing")
    if not config.model.strip():
        raise OllamaReviewError("ollama_model_missing")

    request_payload = {
        "model": config.model,
        "stream": False,
        "format": "json",
        "options": _ollama_options(config),
        "messages": [
            {
                "role": "system",
                "content": _system_prompt(),
            },
            {
                "role": "user",
                "content": _user_prompt(context_payload),
            },
        ],
    }
    try:
        with httpx.Client(timeout=config.timeout_seconds) as client:
            response = client.post(f"{base_url}/api/chat", json=request_payload)
            response.raise_for_status()
            response_payload = response.json()
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise OllamaReviewError(f"ollama_request_failed:{exc}") from exc

    content = _extract_ollama_content(response_payload)
    try:
        suggestion = json.loads(content)
    except json.JSONDecodeError as exc:
        raise OllamaReviewError("ollama_response_not_json") from exc
    if not isinstance(suggestion, dict):
        raise OllamaReviewError("ollama_response_not_object")
    normalized = _normalize_ollama_suggestion(suggestion)
    if not normalized["probable_cause"] and not normalized["recommended_api_actions"]:
        raise OllamaReviewError("ollama_response_missing_review_fields")
    return normalized


def classify_issue_with_ollama(
    context_payload: dict[str, Any],
    config: OllamaReviewConfig,
) -> dict[str, Any]:
    base_url = config.base_url.rstrip("/")
    if not base_url:
        raise OllamaReviewError("ollama_base_url_missing")
    if not config.model.strip():
        raise OllamaReviewError("ollama_model_missing")

    request_payload = {
        "model": config.model,
        "stream": False,
        "format": "json",
        "options": _ollama_options(config),
        "messages": [
            {
                "role": "system",
                "content": _classification_system_prompt(),
            },
            {
                "role": "user",
                "content": _classification_user_prompt(context_payload),
            },
        ],
    }
    try:
        with httpx.Client(timeout=config.timeout_seconds) as client:
            response = client.post(f"{base_url}/api/chat", json=request_payload)
            response.raise_for_status()
            response_payload = response.json()
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise OllamaReviewError(f"ollama_request_failed:{exc}") from exc

    content = _extract_ollama_content(response_payload)
    try:
        classification = json.loads(content)
    except json.JSONDecodeError as exc:
        raise OllamaReviewError("ollama_response_not_json") from exc
    if not isinstance(classification, dict):
        raise OllamaReviewError("ollama_response_not_object")
    normalized = _normalize_ollama_classification(classification)
    if not normalized["cause_category"] and not normalized["rationale"]:
        raise OllamaReviewError("ollama_response_missing_classification_fields")
    return normalized


def classify_issue_with_openai_compatible(
    context_payload: dict[str, Any],
    config: OpenAICompatibleReviewConfig,
) -> dict[str, Any]:
    base_url = config.base_url.rstrip("/")
    if not base_url:
        raise OllamaReviewError("openai_compatible_base_url_missing")
    if not config.model.strip():
        raise OllamaReviewError("openai_compatible_model_missing")

    request_payload = {
        "model": config.model,
        "temperature": config.temperature,
        "max_tokens": max(int(config.max_tokens), 128),
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [
            {
                "role": "system",
                "content": _classification_system_prompt()
                + " Maximal 3 evidence_event_ids. Rationale maximal 180 Zeichen. "
                + "Missing_data_questions maximal 2 kurze Fragen.",
            },
            {
                "role": "user",
                "content": _classification_user_prompt(context_payload)
                + "\nWichtig: Gib hoechstens 3 evidence_event_ids aus und beende das JSON vollstaendig.",
            },
        ],
    }
    try:
        with httpx.Client(timeout=config.timeout_seconds) as client:
            response = client.post(f"{base_url}/v1/chat/completions", json=request_payload)
            response.raise_for_status()
            response_payload = response.json()
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise OllamaReviewError(f"openai_compatible_request_failed:{exc}") from exc

    content = _extract_openai_compatible_content(response_payload)
    try:
        classification = json.loads(_extract_json_object_text(content))
    except json.JSONDecodeError as exc:
        raise OllamaReviewError("openai_compatible_response_not_json") from exc
    if not isinstance(classification, dict):
        raise OllamaReviewError("openai_compatible_response_not_object")
    normalized = _normalize_ollama_classification(classification)
    if not normalized["cause_category"] and not normalized["rationale"]:
        raise OllamaReviewError("openai_compatible_response_missing_classification_fields")
    return normalized


def _system_prompt() -> str:
    return (
        "Du bist ein vorsichtiger Steuerreport-Review-Assistent fuer deutsche Crypto-Steuerdaten. "
        "Du darfst keine steuerlich wirksamen Aenderungen direkt anordnen. "
        "Nutze DAC8/CARF/KStTG nur als verifizierten Referenzkontext fuer Plausibilitaet; "
        "diese Meldedaten ersetzen keine FIFO-Ermittlung, Haltefristpruefung, Anschaffungskosten "
        "oder Gebuehrenbehandlung. "
        "Unterscheide Datensammlung ab 01.01.2026 von Meldung/Austausch 2027; "
        "wenn ein EU-Fristdatum gebraucht wird, nutze 30.09.2027. "
        "CARF ist nicht identisch mit CRS. "
        "Antworte ausschliesslich als JSON-Objekt mit diesen Feldern: "
        "priority, probable_cause, confidence, evidence_event_ids, missing_data_questions, "
        "recommended_api_actions, risk_note. "
        "Erlaubte Prioritaeten: high, medium, low. Erlaubte Confidence: high, medium, low. "
        "Empfohlene API-Aktionen muessen method, path, body, action und auto_apply_safe enthalten. "
        "auto_apply_safe darf nur fuer set_status und comment_last_event true sein."
    )


def _ollama_options(config: OllamaReviewConfig) -> dict[str, Any]:
    options: dict[str, Any] = {"temperature": config.temperature}
    if config.num_ctx > 0:
        options["num_ctx"] = int(config.num_ctx)
    return options


def _classification_system_prompt() -> str:
    return (
        "Du bist ein vorsichtiger Klassifizierer fuer deutsche Crypto-Steuerdaten. "
        "Du entscheidest keine Steuerfolgen und empfiehlst keine API-Aktionen. "
        "Gib keine Felder wie priority, probable_cause, recommended_api_actions oder risk_note aus. "
        "Nutze DAC8/CARF/KStTG nur als Referenzkontext; Meldedaten sind keine Steuerberechnung. "
        "CARF ist nicht CRS. Behaupte keine regulatory violation, tax evasion oder fraud. "
        "Antworte ausschliesslich als JSON-Objekt mit diesen Feldern: "
        "cause_category, confidence, evidence_event_ids, rationale, missing_data_questions. "
        "Erlaubte cause_category-Werte: missing_inflow, duplicate_reference, swap_counterleg, "
        "derivative_or_fee_context, timing_boundary, provider_scope_unclear, unknown."
    )


def _user_prompt(context_payload: dict[str, Any]) -> str:
    context_json = json.dumps(_compact_context(context_payload), ensure_ascii=False, separators=(",", ":"))
    return (
        "Analysiere den folgenden Steuerreport-Review-Kontext. "
        "Erzeuge genau ein JSON-Objekt fuer einen Review-Vorschlag. "
        "Keine Markdown-Ausgabe, keine Erklaerung ausserhalb von JSON. "
        "Nutze dieses Schema exakt: "
        '{"priority":"high|medium|low","probable_cause":"kurze Ursache",'
        '"confidence":"high|medium|low","evidence_event_ids":["event_id"],'
        '"missing_data_questions":["frage"],'
        '"recommended_api_actions":[{"action":"set_status","method":"POST",'
        '"path":"/api/v1/issues/update-status","body":{"issue_id":"...","status":"in_review"},'
        '"auto_apply_safe":true}],"risk_note":"risiko"}'
        f"\nKontext JSON:\n{context_json}"
    )


def _classification_user_prompt(context_payload: dict[str, Any]) -> str:
    context_json = json.dumps(_compact_classification_context(context_payload), ensure_ascii=False, separators=(",", ":"))
    return (
        "Klassifiziere nur die wahrscheinlichste Ursache fuer diesen Review-Fall. "
        "Keine Markdown-Ausgabe, keine API-Aktionen, keine steuerliche Entscheidung. "
        f"\nKontext JSON:\n{context_json}\n"
        "Antworte jetzt ausschliesslich mit diesem JSON-Schema: "
        '{"cause_category":"missing_inflow|duplicate_reference|swap_counterleg|'
        'derivative_or_fee_context|timing_boundary|provider_scope_unclear|unknown",'
        '"confidence":"high|medium|low","evidence_event_ids":["event_id"],'
        '"rationale":"kurze technische Begruendung",'
        '"missing_data_questions":["frage"]}'
    )


def _compact_classification_context(context_payload: dict[str, Any]) -> dict[str, Any]:
    issue = context_payload.get("issue", {})
    context = context_payload.get("context", {})
    slim_issue = {
        "issue_id": context_payload.get("issue_id", ""),
        "type": issue.get("type", ""),
        "severity": issue.get("severity", ""),
        "date": issue.get("date", ""),
        "asset": issue.get("asset", ""),
        "balance": issue.get("balance", ""),
        "value_usd": issue.get("value_usd", ""),
        "source_breakdown": issue.get("source_breakdown", []),
        "last_event": _slim_classification_event(issue.get("last_event", {})),
        "recent_events": [_slim_classification_event(item) for item in list(issue.get("recent_events", []))[:8]],
    }
    return {
        "issue_id": context_payload.get("issue_id", ""),
        "issue_type": context_payload.get("issue_type", ""),
        "issue": slim_issue,
        "scope": context.get("scope", {}),
        "asset_yearly_totals": context.get("asset_yearly_totals", []),
        "context_events": [_slim_classification_event(item) for item in list(context.get("context_events", []))[-30:]],
        "same_transaction_events": [
            _slim_classification_event(item) for item in list(context.get("same_transaction_events", []))[:12]
        ],
        "guardrails": {
            "dac8_carf_reference_only": True,
            "no_tax_result_from_reporting_data": True,
            "no_regulatory_violation_claims": True,
        },
    }


def _slim_classification_event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "source_event_id": value.get("source_event_id", ""),
        "timestamp_utc": value.get("timestamp_utc", ""),
        "source": value.get("source", ""),
        "event_type": value.get("event_type", ""),
        "asset": value.get("asset", ""),
        "side": value.get("side", ""),
        "quantity": value.get("quantity", ""),
        "delta": value.get("delta", ""),
        "tx_id": value.get("tx_id", ""),
        "running_balance_after": value.get("running_balance_after", ""),
    }


def _compact_context(context_payload: dict[str, Any]) -> dict[str, Any]:
    issue = context_payload.get("issue", {})
    context = context_payload.get("context", {})
    return {
        "issue_id": context_payload.get("issue_id", ""),
        "issue_type": context_payload.get("issue_type", ""),
        "issue": issue,
        "scope": context.get("scope", {}),
        "asset_yearly_totals": context.get("asset_yearly_totals", []),
        "context_events": list(context.get("context_events", []))[:120],
        "same_transaction_events": list(context.get("same_transaction_events", []))[:80],
        "regulatory_context": context.get("regulatory_context", {}),
        "analysis_contract": context.get("analysis_contract", {}),
        "allowed_api": context_payload.get("api", {}),
    }


def _normalize_ollama_classification(classification: dict[str, Any]) -> dict[str, Any]:
    if isinstance(classification.get("classification"), dict):
        classification = dict(classification["classification"])
    rationale = str(
        classification.get("rationale")
        or classification.get("probable_cause")
        or classification.get("reason")
        or classification.get("explanation")
        or ""
    ).strip()
    category = str(classification.get("cause_category") or classification.get("category") or "").strip().lower()
    allowed_categories = {
        "missing_inflow",
        "duplicate_reference",
        "swap_counterleg",
        "derivative_or_fee_context",
        "timing_boundary",
        "provider_scope_unclear",
        "unknown",
    }
    aliases = {
        "missing_deposit": "missing_inflow",
        "missing_transfer": "missing_inflow",
        "duplicate": "duplicate_reference",
        "reference_duplicate": "duplicate_reference",
        "swap": "swap_counterleg",
        "fee": "derivative_or_fee_context",
        "derivative": "derivative_or_fee_context",
        "timing": "timing_boundary",
    }
    category = aliases.get(category, category)
    if category not in allowed_categories and rationale:
        category = _category_from_text(rationale)
    if category not in allowed_categories:
        category = "unknown"
    evidence = classification.get("evidence_event_ids")
    if not isinstance(evidence, list):
        evidence = []
    questions = classification.get("missing_data_questions")
    if not isinstance(questions, list):
        questions = []
    return {
        "cause_category": category,
        "confidence": _normalize_confidence(classification.get("confidence")),
        "evidence_event_ids": [str(item).strip() for item in evidence if str(item).strip()][:10],
        "rationale": rationale,
        "missing_data_questions": [_question_text(item) for item in questions if _question_text(item)][:10],
    }


def _category_from_text(value: str) -> str:
    text = value.lower()
    if "duplicate" in text or "split into multiple" in text or "same transaction" in text:
        return "duplicate_reference"
    if "swap" in text or "counter" in text or "gegenleg" in text:
        return "swap_counterleg"
    if "derivative" in text or "fee" in text or "gebuehr" in text or "loss" in text:
        return "derivative_or_fee_context"
    if "missing" in text or "inflow" in text or "deposit" in text or "zufluss" in text:
        return "missing_inflow"
    if "timing" in text or "date" in text or "stichtag" in text:
        return "timing_boundary"
    return "unknown"


def _question_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("question") or value.get("text") or "").strip()
    return str(value).strip()


def _extract_ollama_content(response_payload: dict[str, Any]) -> str:
    message = response_payload.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    content = response_payload.get("response")
    if isinstance(content, str) and content.strip():
        return content.strip()
    raise OllamaReviewError("ollama_response_content_missing")


def _extract_openai_compatible_content(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
    raise OllamaReviewError("openai_compatible_response_content_missing")


def _extract_json_object_text(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end >= start:
        return stripped[start : end + 1]
    return stripped


def _normalize_ollama_suggestion(suggestion: dict[str, Any]) -> dict[str, Any]:
    if isinstance(suggestion.get("llm_should_return"), dict):
        nested = dict(suggestion["llm_should_return"])
        if "risk_note" not in nested and suggestion.get("risk_note"):
            nested["risk_note"] = suggestion.get("risk_note")
        suggestion = nested
    priority = _normalize_priority(suggestion.get("priority"))
    confidence = _normalize_confidence(suggestion.get("confidence"))
    evidence = suggestion.get("evidence_event_ids")
    if not isinstance(evidence, list):
        evidence = []
    questions = suggestion.get("missing_data_questions")
    if not isinstance(questions, list):
        questions = []
    actions = suggestion.get("recommended_api_actions")
    if not isinstance(actions, list):
        actions = []
    return {
        "priority": priority,
        "probable_cause": str(suggestion.get("probable_cause") or "").strip(),
        "confidence": confidence,
        "evidence_event_ids": [str(item).strip() for item in evidence if str(item).strip()][:20],
        "missing_data_questions": [str(item).strip() for item in questions if str(item).strip()][:20],
        "recommended_api_actions": [_normalize_action(item) for item in actions if isinstance(item, dict)][:20],
        "risk_note": str(suggestion.get("risk_note") or "").strip(),
    }


def _normalize_priority(value: Any) -> str:
    if isinstance(value, (int, float)):
        if value >= 3:
            return "high"
        if value >= 2:
            return "medium"
        return "low"
    priority = str(value or "medium").strip().lower()
    if priority not in {"high", "medium", "low"}:
        priority = "medium"
    return priority


def _normalize_confidence(value: Any) -> str:
    if isinstance(value, (int, float)):
        if value >= 0.75:
            return "high"
        if value >= 0.45:
            return "medium"
        return "low"
    confidence = str(value or "low").strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"
    return confidence


def _normalize_action(item: dict[str, Any]) -> dict[str, Any]:
    action = str(item.get("action") or "").strip()
    if action == "comment_event":
        action = "comment_last_event"
    method = str(item.get("method") or "GET").strip().upper()
    path = str(item.get("path") or "").strip()
    if not path and action == "set_status":
        path = "/api/v1/issues/update-status"
        method = "POST"
    if not path and action == "comment_last_event":
        path = "/api/v1/review/comment"
        method = "POST"
    body = item.get("body") if isinstance(item.get("body"), dict) else {}
    auto_apply_safe = (bool(item.get("auto_apply_safe")) or action in {"set_status", "comment_last_event"}) and action in {
        "set_status",
        "comment_last_event",
    }
    return {
        "action": action,
        "method": method,
        "path": path,
        "body": body,
        "auto_apply_safe": auto_apply_safe,
    }
