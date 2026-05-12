#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUEUE_DIR = ROOT / "var" / "codex_autopilot_queue"
PENDING_DIR = QUEUE_DIR / "pending"
RUNNING_DIR = QUEUE_DIR / "running"
DONE_DIR = QUEUE_DIR / "done"
FAILED_DIR = QUEUE_DIR / "failed"
LOG_DIR = QUEUE_DIR / "logs"
RESULTS_JSONL = QUEUE_DIR / "results.jsonl"
STATUS_PATH = QUEUE_DIR / "status.json"
LOG_PATH = QUEUE_DIR / "runner.log"

FORBIDDEN_GIT_PATTERN = r"\.(csv|xlsx|db|sqlite|sqlite3)$|^var/|^\.env$"
VALIDATION_PROFILES = {"none", "quick", "full"}


DEFAULT_TASKS = [
    {
        "task_id": "roadmap_next_safe_step",
        "title": "Naechsten sicheren Roadmap-Schritt bearbeiten",
        "task": (
            "Lies AGENTS.md und docs/99_CHAT_HANDOFF_AKTUELL.md. Waehle den naechsten "
            "sicheren, klar belegbaren Entwicklungsschritt aus dem aktuellen Handoff, setze ihn "
            "um, fuehre passende lokale Validierung aus und dokumentiere Ergebnis und Blocker."
        ),
        "validation_profile": "quick",
        "allow_push": False,
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Persistent Codex autopilot task queue.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-defaults", help="Create a conservative default roadmap task.")

    enqueue = sub.add_parser("enqueue", help="Add one Codex autopilot task.")
    enqueue.add_argument("--task-id", required=True)
    enqueue.add_argument("--title", required=True)
    enqueue.add_argument("--task", required=True)
    enqueue.add_argument("--validation-profile", choices=sorted(VALIDATION_PROFILES), default="quick")
    enqueue.add_argument("--allow-push", action="store_true")

    run = sub.add_parser("run", help="Run pending tasks.")
    run.add_argument("--max-hours", type=float, default=12.0)
    run.add_argument("--max-tasks", type=int, default=1, help="0 means unlimited until deadline/pending empty.")
    run.add_argument("--sleep-seconds", type=float, default=10.0)
    run.add_argument("--codex-bin", default="codex")
    run.add_argument("--model", default="")

    sub.add_parser("status", help="Print queue status.")
    args = parser.parse_args()

    ensure_dirs()
    if args.cmd == "init-defaults":
        created = 0
        for task in DEFAULT_TASKS:
            if enqueue_task(task, overwrite=False):
                created += 1
        write_status({"status": "idle", "updated_at_utc": now(), "created_defaults": created, **count_tasks()})
        print(json.dumps({"created": created, **count_tasks()}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "enqueue":
        task = {
            "task_id": args.task_id,
            "title": args.title,
            "task": args.task,
            "validation_profile": args.validation_profile,
            "allow_push": args.allow_push,
        }
        created = enqueue_task(task, overwrite=False)
        write_status({"status": "idle", "updated_at_utc": now(), **count_tasks()})
        print(json.dumps({"created": created, "task_id": args.task_id, **count_tasks()}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "run":
        return run_queue(args)
    if args.cmd == "status":
        print(json.dumps({"status_file": read_json(STATUS_PATH), **count_tasks()}, ensure_ascii=False, indent=2))
        return 0
    raise AssertionError(args.cmd)


def run_queue(args: argparse.Namespace) -> int:
    started_at = now()
    deadline = time.time() + max(args.max_hours, 0.01) * 3600
    completed = 0
    failed = 0
    write_status({"status": "running", "started_at_utc": started_at, "updated_at_utc": now(), **count_tasks()})
    log("runner started")

    while time.time() < deadline:
        pending = sorted(PENDING_DIR.glob("*.json"))
        if not pending:
            break
        if args.max_tasks and completed + failed >= args.max_tasks:
            break
        pending_path = pending[0]
        running_path = RUNNING_DIR / pending_path.name
        pending_path.replace(running_path)
        task = read_json(running_path)
        task_id = str(task.get("task_id") or running_path.stem)
        write_status(
            {
                "status": "running",
                "started_at_utc": started_at,
                "updated_at_utc": now(),
                "current_task": task_id,
                "completed_this_run": completed,
                "failed_this_run": failed,
                **count_tasks(),
            }
        )
        try:
            result = run_task(task, args=args)
            append_jsonl(RESULTS_JSONL, result)
            shutil.move(str(running_path), str(DONE_DIR / running_path.name))
            completed += 1
            log(f"completed {task_id}")
        except Exception as exc:
            failure = {
                "task_id": task_id,
                "title": task.get("title", ""),
                "status": "error",
                "created_at_utc": now(),
                "error": f"{type(exc).__name__}: {exc}",
            }
            append_jsonl(RESULTS_JSONL, failure)
            task["last_error"] = failure["error"]
            running_path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
            shutil.move(str(running_path), str(FAILED_DIR / running_path.name))
            failed += 1
            log(f"failed {task_id}: {failure['error']}")
        if time.time() < deadline:
            time.sleep(max(args.sleep_seconds, 0.0))

    final_status = "completed" if not list(PENDING_DIR.glob("*.json")) and not list(RUNNING_DIR.glob("*.json")) else "stopped"
    write_status(
        {
            "status": final_status,
            "started_at_utc": started_at,
            "updated_at_utc": now(),
            "completed_this_run": completed,
            "failed_this_run": failed,
            "results_jsonl": str(RESULTS_JSONL),
            **count_tasks(),
        }
    )
    log(f"runner finished status={final_status} completed={completed} failed={failed}")
    print(json.dumps(read_json(STATUS_PATH), ensure_ascii=False, indent=2))
    return 0 if failed == 0 else 1


def run_task(task: dict[str, Any], *, args: argparse.Namespace) -> dict[str, Any]:
    task_id = safe_id(str(task.get("task_id") or "task"))
    validation_profile = str(task.get("validation_profile") or "quick")
    if validation_profile not in VALIDATION_PROFILES:
        raise ValueError(f"invalid validation_profile: {validation_profile}")

    before_status = git_status()
    last_message_path = LOG_DIR / f"{task_id}_last_message.md"
    events_path = LOG_DIR / f"{task_id}_events.jsonl"
    prompt = build_prompt(task, validation_profile=validation_profile)
    command = [
        str(args.codex_bin),
        "exec",
        "-C",
        str(ROOT),
        "--sandbox",
        "workspace-write",
        "-c",
        'approval_policy="never"',
        "--output-last-message",
        str(last_message_path),
        "--json",
    ]
    if args.model:
        command.extend(["--model", str(args.model)])
    command.append("-")

    started = time.time()
    with events_path.open("w", encoding="utf-8") as events_handle:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            input=prompt,
            text=True,
            stdout=events_handle,
            stderr=subprocess.PIPE,
            timeout=7200,
            check=False,
        )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or f"codex exec exit {proc.returncode}")[-4000:])

    post_checks = run_post_checks(validation_profile=validation_profile)
    push_result = maybe_push(task, post_checks)
    return {
        "task_id": task_id,
        "title": task.get("title", ""),
        "status": "success",
        "created_at_utc": now(),
        "duration_seconds": round(time.time() - started, 3),
        "validation_profile": validation_profile,
        "allow_push": bool(task.get("allow_push", False)),
        "before_status": before_status,
        "after_status": git_status(),
        "last_message": str(last_message_path),
        "events": str(events_path),
        "post_checks": post_checks,
        "push": push_result,
    }


def build_prompt(task: dict[str, Any], *, validation_profile: str) -> str:
    return f"""Du bist ein autonomer Codex-Worker fuer /workspace/steuerreport.

Arbeitsauftrag:
{task.get("title", "")}

Details:
{task.get("task", "")}

Verbindliche Regeln:
- Lies zuerst AGENTS.md und docs/99_CHAT_HANDOFF_AKTUELL.md.
- Arbeite auf dem bestehenden Branch codex/next-roadmap-work.
- Fuehre den Auftrag selbststaendig so weit wie sicher moeglich aus.
- Frage nicht nach "weiter". Stoppe nur bei echten Blockern, fehlenden Belegen,
  riskanten Steuerentscheidungen, Secrets, Rohdaten oder nicht aufloesbaren Konflikten.
- Erfinde keine Anschaffungskosten, Preise, FX-Kurse, Cost Basis, Belege oder steuerliche Behandlung.
- Loesche keine Rohdaten. Committe/stage keine Dateien aus var/, keine CSV/XLSX/DB/SQLite-Dateien und keine .env.
- Dokumentiere relevante Ergebnisse deutsch in docs/ und aktualisiere docs/99_CHAT_HANDOFF_AKTUELL.md,
  wenn sich der Projektstand aendert.
- Code, Tests, Bezeichner und Kommentare bleiben Englisch, ausser lokaler Kontext ist bereits Deutsch.
- Fuehre passende Validierung aus. Gewuenschtes Profil: {validation_profile}.
- Erstelle nur dann Commits, wenn das Arbeitspaket lokal plausibel validiert ist und GitHub-sicher ist.
- Kein Force-Push. Kein Push, ausser die konkrete Task erlaubt das und alle Checks sind gruen.
- Antworte am Ende knapp mit: erledigt, geaenderte Dateien, Validierung, offene Blocker.
"""


def run_post_checks(*, validation_profile: str) -> dict[str, Any]:
    checks: list[list[str]] = [["git", "diff", "--check"]]
    if validation_profile in {"quick", "full"}:
        checks.extend(
            [
                [sys.executable, "-m", "ruff", "check", ".", "--no-cache"],
                ["node", "--check", "src/tax_engine/ui/static/app.js"],
            ]
        )
    if validation_profile == "full":
        checks.extend(
            [
                [sys.executable, "-m", "mypy", "src/", "--cache-dir=/tmp/steuerreport_mypy_cache"],
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "tests/unit",
                ],
                [
                    sys.executable,
                    "scripts/verify_integrity.py",
                    "--all-years",
                ],
            ]
        )
    results = [run_check(command) for command in checks]
    forbidden = run_check(["bash", "-lc", f"git diff --cached --name-only | rg '{FORBIDDEN_GIT_PATTERN}' || true"])
    unstaged_forbidden = run_check(
        ["bash", "-lc", "git status --ignored --short | rg '^(!!|\\?\\?) (var/|.*\\.(csv|xlsx|db|sqlite|sqlite3)$|\\.env$)' || true"]
    )
    ok = all(item["returncode"] == 0 for item in results) and not forbidden["stdout"].strip()
    return {
        "ok": ok,
        "checks": results,
        "forbidden_staged": forbidden,
        "forbidden_local_status": unstaged_forbidden,
    }


def maybe_push(task: dict[str, Any], post_checks: dict[str, Any]) -> dict[str, Any]:
    if not bool(task.get("allow_push", False)):
        return {"attempted": False, "reason": "allow_push false"}
    if not bool(post_checks.get("ok", False)):
        return {"attempted": False, "reason": "post checks not ok"}
    result = run_check(["git", "push"])
    return {"attempted": True, "returncode": result["returncode"], "stdout": result["stdout"], "stderr": result["stderr"]}


def run_check(command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=1800, check=False)
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
    }


def enqueue_task(task: dict[str, Any], *, overwrite: bool) -> bool:
    task_id = safe_id(str(task["task_id"]))
    validation_profile = str(task.get("validation_profile") or "quick")
    if validation_profile not in VALIDATION_PROFILES:
        raise ValueError(f"invalid validation_profile: {validation_profile}")
    payload = {
        "task_id": task_id,
        "title": str(task.get("title") or task_id),
        "task": str(task.get("task") or ""),
        "validation_profile": validation_profile,
        "allow_push": bool(task.get("allow_push", False)),
        "created_at_utc": now(),
    }
    target = PENDING_DIR / f"{task_id}.json"
    existing = [target, RUNNING_DIR / target.name, DONE_DIR / target.name, FAILED_DIR / target.name]
    if not overwrite and any(path.exists() for path in existing):
        return False
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def git_status() -> str:
    proc = subprocess.run(["git", "status", "--short", "--branch"], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def count_tasks() -> dict[str, int]:
    return {
        "pending": len(list(PENDING_DIR.glob("*.json"))),
        "running": len(list(RUNNING_DIR.glob("*.json"))),
        "done": len(list(DONE_DIR.glob("*.json"))),
        "failed": len(list(FAILED_DIR.glob("*.json"))),
    }


def ensure_dirs() -> None:
    for path in [PENDING_DIR, RUNNING_DIR, DONE_DIR, FAILED_DIR, LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_status(payload: dict[str, Any]) -> None:
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def log(message: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{now()} {message}\n")


def now() -> str:
    return datetime.now(UTC).isoformat()


def safe_id(value: str) -> str:
    out = []
    for char in value.lower().strip():
        if char.isalnum() or char in {"-", "_"}:
            out.append(char)
        elif char.isspace() or char in {":", "/", "."}:
            out.append("_")
    cleaned = "".join(out).strip("_")
    if not cleaned:
        raise ValueError("empty task_id")
    return cleaned[:120]


if __name__ == "__main__":
    raise SystemExit(main())
