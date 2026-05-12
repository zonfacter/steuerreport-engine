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
QUEUE_DIR = ROOT / "var" / "ai_readonly_queue"
PENDING_DIR = QUEUE_DIR / "pending"
RUNNING_DIR = QUEUE_DIR / "running"
DONE_DIR = QUEUE_DIR / "done"
FAILED_DIR = QUEUE_DIR / "failed"
RESULTS_JSONL = QUEUE_DIR / "results.jsonl"
STATUS_PATH = QUEUE_DIR / "status.json"
LOG_PATH = QUEUE_DIR / "runner.log"


DEFAULT_TASKS = [
    {
        "task_id": "hnt_2021_cost_basis_chain",
        "title": "HNT 2021 Cost-Basis-Kette",
        "task": (
            "Pruefe HNT 2021 Zero-Cost-Zeilen read-only anhand DB-Snapshot. "
            "Finde fuer jede betroffene tax_line die source_event_id, lot_source_event_id, "
            "Transfer-Matches, Legacy-HNT-Outbounds und ob eine Kostenbasis technisch ableitbar "
            "oder nur als Mining/Reward/Evidenz-Gap dokumentierbar ist."
        ),
    },
    {
        "task_id": "hnt_2022_cost_basis_chain",
        "title": "HNT 2022 Cost-Basis-Kette",
        "task": (
            "Pruefe HNT 2022 Zero-Cost-Zeilen, besonders lot_source_event_id "
            "9dd85d203cebbe23d40ff09ddd91b30758c3d255c6f80dadbb27581ab152bcba und "
            "transfer-chain:f1f8f745f1087b49. Klaere, welche vorgelagerten HNT-Events fehlen."
        ),
    },
    {
        "task_id": "usdt_2022_acquisition_gap",
        "title": "USDT 2022 Acquisition-Gap",
        "task": (
            "Pruefe die drei USDT 2022 Zero-Cost-Zeilen. Suche in raw_events, source_files, "
            "transfer_matches und zeitnahen Binance/Pionex Events nach moeglichen Deposit-/Buy-/Swap-Quellen. "
            "Trenne deterministische Treffer von Evidenz-Gaps."
        ),
    },
    {
        "task_id": "jup_2024_dca_airdrop_review",
        "title": "JUP 2024 DCA/Airdrop Review",
        "task": (
            "Pruefe JUP 2024 Zero-Cost-Zeilen und DCA/OpenDca/CloseDca-Kontext. "
            "Bewerte, ob Airdrop-Nullbasis belegbar ist, ob DCA-Rueckfluesse interne Transfers sind "
            "oder ob keine sichere Cost-Basis ableitbar ist."
        ),
    },
    {
        "task_id": "low_value_noise_review",
        "title": "Low-Value Noise Review",
        "task": (
            "Pruefe alle kleinen Zero-Cost-Restposten ausser HNT/USDT/JUP, z.B. DOGE, UNKNOWN, IOT, USDC, EUR. "
            "Erstelle eine Ampelliste: Rundung/Dust, echtes Missing Acquisition, ignorierbarer Report-Hinweis."
        ),
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Persistent read-only local-AI task queue.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-defaults", help="Create the standard open-issue analysis tasks.")

    enqueue = sub.add_parser("enqueue", help="Add one custom task.")
    enqueue.add_argument("--task-id", required=True)
    enqueue.add_argument("--title", required=True)
    enqueue.add_argument("--task", required=True)

    run = sub.add_parser("run", help="Run pending tasks.")
    run.add_argument("--max-hours", type=float, default=16.0)
    run.add_argument("--max-tasks", type=int, default=0, help="0 means unlimited until deadline/pending empty.")
    run.add_argument("--sleep-seconds", type=float, default=5.0)
    run.add_argument("--max-queries", type=int, default=10)
    run.add_argument("--row-limit", type=int, default=100)
    run.add_argument("--max-tokens", type=int, default=6000)

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
        task = {"task_id": args.task_id, "title": args.title, "task": args.task}
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

    build_snapshot()
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
    task_id = str(task.get("task_id") or "task")
    command = [
        sys.executable,
        str(ROOT / "scripts" / "ai_db_countercheck.py"),
        "--task",
        str(task.get("task") or task.get("title") or task_id),
        "--max-queries",
        str(args.max_queries),
        "--row-limit",
        str(args.row_limit),
        "--max-tokens",
        str(args.max_tokens),
    ]
    started = time.time()
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=1800, check=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or f"exit {proc.returncode}")[-2000:])
    output = json.loads(proc.stdout)
    return {
        "task_id": task_id,
        "title": task.get("title", ""),
        "status": "success",
        "created_at_utc": now(),
        "duration_seconds": round(time.time() - started, 3),
        "result_json": output.get("json"),
        "result_md": output.get("md"),
        "queries": output.get("queries"),
    }


def build_snapshot() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_ai_readonly_db_snapshot.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "snapshot build failed")[-2000:])
    log(f"snapshot built: {proc.stdout.strip()}")


def enqueue_task(task: dict[str, Any], *, overwrite: bool) -> bool:
    task_id = safe_id(str(task["task_id"]))
    payload = {
        "task_id": task_id,
        "title": str(task.get("title") or task_id),
        "task": str(task.get("task") or ""),
        "created_at_utc": now(),
    }
    target = PENDING_DIR / f"{task_id}.json"
    existing = [target, RUNNING_DIR / target.name, DONE_DIR / target.name, FAILED_DIR / target.name]
    if not overwrite and any(path.exists() for path in existing):
        return False
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def count_tasks() -> dict[str, int]:
    return {
        "pending": len(list(PENDING_DIR.glob("*.json"))),
        "running": len(list(RUNNING_DIR.glob("*.json"))),
        "done": len(list(DONE_DIR.glob("*.json"))),
        "failed": len(list(FAILED_DIR.glob("*.json"))),
    }


def ensure_dirs() -> None:
    for path in [PENDING_DIR, RUNNING_DIR, DONE_DIR, FAILED_DIR]:
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
