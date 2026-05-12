#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DB = Path.home() / ".local" / "share" / "steuerreport" / "ai_readonly" / "steuerreport_ai_readonly.sqlite"
OUT_DIR = ROOT / "var"
DEFAULT_BASE_URL = "http://192.168.2.203:11435"
DEFAULT_MODEL = "qwen3.6-35b-a3b-iq4xs"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a controlled read-only DB countercheck with local llama.cpp.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--db", type=Path, default=SNAPSHOT_DB)
    parser.add_argument("--task", default="Pruefe offene Zero-Cost-/Kostenbasis-Themen und ob deterministische DB-Fixes naheliegen.")
    parser.add_argument("--max-queries", type=int, default=8)
    parser.add_argument("--row-limit", type=int, default=80)
    parser.add_argument("--max-tokens", type=int, default=5000)
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"Readonly snapshot fehlt: {args.db}. Erst scripts/build_ai_readonly_db_snapshot.py ausfuehren.")

    schema = collect_schema(args.db)
    seed = collect_seed_context(args.db)
    query_request = ask_model_for_queries(args, schema=schema, seed=seed)
    queries = normalize_queries(query_request, max_queries=args.max_queries)
    query_results = execute_queries(args.db, queries=queries, row_limit=args.row_limit)
    final = ask_model_for_final(args, schema=schema, seed=seed, query_results=query_results)

    stamp = time.strftime("%Y-%m-%d_%H%M%S", time.gmtime())
    payload = {
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "llm": {"base_url": args.base_url, "model": args.model},
        "db": str(args.db),
        "task": args.task,
        "query_request": query_request,
        "queries": queries,
        "query_results": query_results,
        "final": final,
    }
    out_json = OUT_DIR / f"ai_db_countercheck_{stamp}.json"
    out_md = OUT_DIR / f"ai_db_countercheck_{stamp}.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"json": str(out_json), "md": str(out_md), "queries": len(queries)}, ensure_ascii=False, indent=2))
    return 0


def connect_ro(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def collect_schema(db: Path) -> dict[str, Any]:
    with connect_ro(db) as conn:
        objects = [
            dict(row)
            for row in conn.execute(
                """
                SELECT type, name, sql
                FROM sqlite_master
                WHERE type IN ('table', 'view')
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY type, name
                """
            )
        ]
        counts: dict[str, int] = {}
        for obj in objects:
            name = obj["name"]
            try:
                counts[name] = int(conn.execute(f"SELECT count(*) FROM {quote_ident(name)}").fetchone()[0])
            except sqlite3.Error:
                counts[name] = -1
    return {"objects": objects, "counts": counts}


def collect_seed_context(db: Path) -> dict[str, Any]:
    with connect_ro(db) as conn:
        latest_jobs = rows(
            conn,
            """
            SELECT tax_year, job_id, updated_at_utc
            FROM ai_latest_completed_jobs_per_year
            ORDER BY tax_year
            """,
        )
        zero_cost_summary = rows(
            conn,
            """
            SELECT tax_year, asset, count(*) AS line_count,
                   printf('%.2f', sum(CAST(proceeds_eur AS REAL))) AS proceeds_eur
            FROM ai_open_zero_cost_tax_lines
            GROUP BY tax_year, asset
            ORDER BY tax_year, asset
            """,
        )
        transfer_summary = rows(
            conn,
            """
            SELECT status, method, count(*) AS match_count
            FROM transfer_matches
            GROUP BY status, method
            ORDER BY status, method
            """,
            limit=60,
        )
    return {
        "latest_jobs": latest_jobs,
        "zero_cost_summary": zero_cost_summary,
        "transfer_match_summary": transfer_summary,
        "rules": [
            "Nur read-only Analyse. Keine Schreiboperationen.",
            "Keine Cost Basis erfinden.",
            "Deterministische Fixes nur bei belegtem Event-/Transfer-Zusammenhang.",
            "Bei fehlender Primaerquelle als Evidenz-/Review-Gap markieren.",
        ],
    }


def ask_model_for_queries(args: argparse.Namespace, *, schema: dict[str, Any], seed: dict[str, Any]) -> dict[str, Any]:
    prompt = {
        "task": args.task,
        "instruction": (
            "Du bekommst SQLite-Schema und Seed-Kontext. Formuliere gezielte SQL-SELECT-Abfragen, "
            "um die offenen Cost-Basis-/Transfer-Bezuege selbst zu pruefen. "
            "Nur JSON mit Feld queries. Jede Query: name, why, sql. "
            "Nur SELECT oder WITH SELECT, keine Semikolons, keine Schreibbefehle."
        ),
        "schema": compact_schema(schema),
        "seed": seed,
    }
    return call_llm_json(args, prompt, max_tokens=2200)


def ask_model_for_final(
    args: argparse.Namespace,
    *,
    schema: dict[str, Any],
    seed: dict[str, Any],
    query_results: list[dict[str, Any]],
) -> dict[str, Any]:
    prompt = {
        "task": args.task,
        "instruction": (
            "Werte die DB-Abfrageergebnisse aus. Antworte als JSON mit Feldern: "
            "overall, issue_assessments, deterministic_fixes, evidence_gaps, next_checks, unsafe_actions. "
            "Keine sichtbare Reasoning-Kette. Benenne konkrete Tabellen/Events, aber erfinde keine Fakten."
        ),
        "schema_summary": compact_schema(schema),
        "seed": seed,
        "query_results": query_results,
    }
    return call_llm_json(args, prompt, max_tokens=args.max_tokens)


def call_llm_json(args: argparse.Namespace, payload: dict[str, Any], *, max_tokens: int) -> dict[str, Any]:
    request_payload = {
        "model": args.model,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [
            {
                "role": "system",
                "content": "Du bist ein vorsichtiger DB-Audit-Assistent. Antworte ausschliesslich als gueltiges JSON.",
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "stream": False,
    }
    body = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{args.base_url.rstrip('/')}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=900) as response:
        raw = response.read().decode("utf-8")
    decoded = json.loads(raw)
    content = decoded["choices"][0]["message"].get("content") or "{}"
    return {
        "content": json.loads(extract_json_object(content)),
        "usage": decoded.get("usage", {}),
        "finish_reason": decoded["choices"][0].get("finish_reason"),
    }


def normalize_queries(query_request: dict[str, Any], *, max_queries: int) -> list[dict[str, str]]:
    content = query_request.get("content", {})
    raw_queries = content.get("queries", []) if isinstance(content, dict) else []
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(raw_queries):
        if not isinstance(item, dict):
            continue
        sql = str(item.get("sql") or "").strip()
        if not is_safe_select(sql):
            continue
        normalized.append(
            {
                "name": str(item.get("name") or f"query_{index + 1}")[:80],
                "why": str(item.get("why") or "")[:500],
                "sql": sql,
            }
        )
        if len(normalized) >= max_queries:
            break
    return normalized


def execute_queries(db: Path, *, queries: list[dict[str, str]], row_limit: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with connect_ro(db) as conn:
        for query in queries:
            sql = enforce_limit(query["sql"], row_limit=row_limit)
            try:
                result_rows = rows(conn, sql, limit=row_limit)
                results.append({**query, "executed_sql": sql, "row_count": len(result_rows), "rows": result_rows})
            except sqlite3.Error as exc:
                results.append({**query, "executed_sql": sql, "error": str(exc), "rows": []})
    return results


def rows(conn: sqlite3.Connection, sql: str, *, limit: int | None = None) -> list[dict[str, Any]]:
    cur = conn.execute(sql)
    out = [dict(row) for row in cur.fetchall()]
    if limit is not None:
        return out[:limit]
    return out


def is_safe_select(sql: str) -> bool:
    compact = sql.strip().lower()
    if ";" in compact:
        return False
    if not (compact.startswith("select") or compact.startswith("with")):
        return False
    forbidden = r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|reindex)\b"
    return re.search(forbidden, compact) is None


def enforce_limit(sql: str, *, row_limit: int) -> str:
    if re.search(r"\blimit\s+\d+\b", sql, flags=re.IGNORECASE):
        return sql
    return f"{sql}\nLIMIT {int(row_limit)}"


def compact_schema(schema: dict[str, Any]) -> dict[str, Any]:
    objects = []
    for obj in schema["objects"]:
        sql = str(obj.get("sql") or "")
        objects.append({"type": obj["type"], "name": obj["name"], "rows": schema["counts"].get(obj["name"], -1), "sql": sql[:2200]})
    return {"objects": objects}


def extract_json_object(content: str) -> str:
    text = content.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    raise ValueError("LLM response did not contain a JSON object")


def quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def render_markdown(payload: dict[str, Any]) -> str:
    final = payload["final"]["content"]
    lines = [
        "# AI DB Countercheck",
        "",
        f"- Created UTC: `{payload['created_at_utc']}`",
        f"- DB: `{payload['db']}`",
        f"- LLM: `{payload['llm']['model']}` via `{payload['llm']['base_url']}`",
        f"- Queries executed: `{len(payload['queries'])}`",
        "",
        "## Overall",
        "",
        str(final.get("overall", "")),
        "",
        "## Deterministic Fixes",
        "",
    ]
    lines.extend(f"- {item}" for item in final.get("deterministic_fixes", []))
    lines.extend(["", "## Evidence Gaps", ""])
    lines.extend(f"- {item}" for item in final.get("evidence_gaps", []))
    lines.extend(["", "## Next Checks", ""])
    lines.extend(f"- {item}" for item in final.get("next_checks", []))
    lines.extend(["", "## Unsafe Actions", ""])
    lines.extend(f"- {item}" for item in final.get("unsafe_actions", []))
    lines.extend(["", "## Raw Final JSON", "", "```json", json.dumps(final, ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
