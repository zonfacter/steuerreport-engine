from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any

from tax_engine.admin import resolve_secret_value
from tax_engine.ingestion.store import STORE

DETAIL_ENDPOINT = "https://pro-api.solscan.io/v2.0/transaction/detail"


def main() -> None:
    parser = argparse.ArgumentParser(description="Cache Solscan transaction details in SQLite.")
    parser.add_argument("--wallet-address", default="")
    parser.add_argument("--source", default="solana_rpc")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=0.08)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    api_key = resolve_secret_value("secret.solscan.api_key").strip()
    if not api_key:
        raise SystemExit("secret.solscan.api_key is empty")

    signatures = STORE.list_distinct_transaction_ids(
        source=args.source or None,
        wallet_address=args.wallet_address or None,
        limit=args.limit,
    )
    stats = {"candidate_count": len(signatures), "pending_count": 0, "fetched": 0, "skipped_cached": 0, "success": 0, "errors": 0}
    pending: list[str] = []
    for signature in signatures:
        if not args.force and STORE.get_solscan_transaction(signature) is not None:
            stats["skipped_cached"] += 1
            continue
        pending.append(signature)
    stats["pending_count"] = len(pending)

    workers = max(1, min(int(args.workers), 32))
    if workers == 1:
        for index, signature in enumerate(pending, start=1):
            _merge_stats(
                stats,
                _fetch_store_detail(
                    signature=signature,
                    wallet_address=args.wallet_address,
                    api_key=api_key,
                    retries=max(0, args.retries),
                    timeout=max(1.0, args.timeout),
                    sleep=max(0.0, args.sleep),
                ),
            )
            _maybe_print_progress(stats, processed=index, total=len(pending), every=args.progress_every)
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(
                    _fetch_store_detail,
                    signature=signature,
                    wallet_address=args.wallet_address,
                    api_key=api_key,
                    retries=max(0, args.retries),
                    timeout=max(1.0, args.timeout),
                    sleep=max(0.0, args.sleep),
                )
                for signature in pending
            ]
            for index, future in enumerate(as_completed(futures), start=1):
                _merge_stats(stats, future.result())
                _maybe_print_progress(stats, processed=index, total=len(pending), every=args.progress_every)
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))


def _fetch_store_detail(
    *,
    signature: str,
    wallet_address: str,
    api_key: str,
    retries: int,
    timeout: float,
    sleep: float,
) -> dict[str, int]:
    result = _fetch_detail(
        signature=signature,
        api_key=api_key,
        retries=retries,
        timeout=timeout,
    )
    if result.get("transient_error"):
        if sleep > 0:
            time.sleep(sleep)
        return {"fetched": 0, "success": 0, "errors": 1}
    summary = _summarize(signature=signature, wallet_address=wallet_address, result=result)
    STORE.upsert_solscan_transaction(
        signature=signature,
        wallet_address=wallet_address,
        endpoint=DETAIL_ENDPOINT,
        http_status=int(result["http_status"]),
        success=bool(summary.get("success")),
        block_time_utc=str(summary.get("block_time_utc") or ""),
        slot=summary.get("slot") if isinstance(summary.get("slot"), int) else None,
        raw_json=json.dumps(result["body"], ensure_ascii=False, sort_keys=True),
        summary_json=json.dumps(summary, ensure_ascii=False, sort_keys=True),
    )
    if sleep > 0:
        time.sleep(sleep)
    return {
        "fetched": 1,
        "success": 1 if summary.get("success") else 0,
        "errors": 0 if summary.get("success") else 1,
    }


def _merge_stats(stats: dict[str, int], result: dict[str, int]) -> None:
    for key in ("fetched", "success", "errors"):
        stats[key] += int(result.get(key) or 0)


def _maybe_print_progress(stats: dict[str, int], *, processed: int, total: int, every: int) -> None:
    safe_every = max(1, int(every))
    if processed == total or processed % safe_every == 0:
        print(
            json.dumps(
                {
                    "processed": processed,
                    "total": total,
                    "fetched": stats["fetched"],
                    "success": stats["success"],
                    "errors": stats["errors"],
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
            flush=True,
        )


def _fetch_detail(*, signature: str, api_key: str, retries: int = 2, timeout: float = 45.0) -> dict[str, Any]:
    url = f"{DETAIL_ENDPOINT}?{urllib.parse.urlencode({'tx': signature})}"
    request = urllib.request.Request(url, headers={"token": api_key, "accept": "application/json"})
    last_error = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body_text = response.read().decode("utf-8", errors="replace")
                status = int(response.status)
            break
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            status = int(exc.code)
            if status not in {429, 500, 502, 503, 504} or attempt >= retries:
                break
            last_error = f"HTTP {status}"
        except (TimeoutError, urllib.error.URLError) as exc:
            status = 0
            body_text = ""
            last_error = str(exc)
            if attempt >= retries:
                return {
                    "http_status": 0,
                    "body": {"success": False, "error_message": last_error},
                    "transient_error": True,
                }
        time.sleep(min(2.0, 0.5 * (attempt + 1)))
    else:
        return {
            "http_status": 0,
            "body": {"success": False, "error_message": last_error or "request failed"},
            "transient_error": True,
        }
    try:
        body: Any = json.loads(body_text)
    except json.JSONDecodeError:
        body = {"raw_text": body_text}
    transient_error = status in {429, 500, 502, 503, 504}
    return {"http_status": status, "body": body, "transient_error": transient_error}


def _summarize(*, signature: str, wallet_address: str, result: dict[str, Any]) -> dict[str, Any]:
    body = result.get("body")
    data = body.get("data") if isinstance(body, dict) and isinstance(body.get("data"), dict) else body
    success = bool(isinstance(body, dict) and body.get("success") is True and isinstance(data, dict))
    block_time = _block_time_utc(data if isinstance(data, dict) else {})
    return {
        "signature": signature,
        "wallet_address": wallet_address,
        "success": success,
        "http_status": int(result.get("http_status") or 0),
        "error_message": str(body.get("error_message") or "") if isinstance(body, dict) else "",
        "block_time_utc": block_time,
        "slot": _int_or_none((data or {}).get("slot")) if isinstance(data, dict) else None,
        "sol_balance_change_count": _len_any((data or {}).get("sol_bal_change")) if isinstance(data, dict) else 0,
        "token_balance_change_count": _len_any((data or {}).get("token_bal_change")) if isinstance(data, dict) else 0,
        "parsed_instruction_count": _len_any((data or {}).get("parsed_instructions")) if isinstance(data, dict) else 0,
        "fetched_at_utc": datetime.now(UTC).isoformat(),
    }


def _block_time_utc(data: dict[str, Any]) -> str:
    raw = data.get("block_time") or data.get("blockTime")
    if isinstance(raw, (int, float)) and raw > 0:
        return datetime.fromtimestamp(raw, UTC).isoformat()
    if isinstance(raw, str) and raw.isdigit():
        return datetime.fromtimestamp(int(raw), UTC).isoformat()
    return str(raw or "")


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _len_any(value: Any) -> int:
    return len(value) if isinstance(value, (list, dict)) else 0


if __name__ == "__main__":
    main()
