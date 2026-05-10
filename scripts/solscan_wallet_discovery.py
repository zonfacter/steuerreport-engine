from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from tax_engine.admin import resolve_secret_value
from tax_engine.ingestion.store import STORE

BASE_URL = "https://pro-api.solscan.io/v2.0"


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover and cache a full Solscan wallet history.")
    parser.add_argument("--wallet-address", required=True)
    parser.add_argument("--max-pages", type=int, default=10000)
    parser.add_argument("--transaction-limit", type=int, default=40, choices=(10, 20, 30, 40))
    parser.add_argument("--transfer-page-size", type=int, default=100, choices=(10, 20, 30, 40, 60, 100))
    parser.add_argument("--workers", type=int, default=8, help="Workers for detail backfill after discovery")
    parser.add_argument("--sleep", type=float, default=0.02)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-transfers", action="store_true")
    parser.add_argument("--skip-details", action="store_true")
    args = parser.parse_args()

    api_key = resolve_secret_value("secret.solscan.api_key").strip()
    if not api_key:
        raise SystemExit("secret.solscan.api_key is empty")

    wallet = args.wallet_address.strip()
    tx_stats = discover_account_transactions(
        wallet_address=wallet,
        api_key=api_key,
        max_pages=max(1, args.max_pages),
        limit=args.transaction_limit,
        sleep=max(0.0, args.sleep),
        retries=max(0, args.retries),
        timeout=max(1.0, args.timeout),
        resume=args.resume,
    )
    transfer_stats = {"pages": 0, "stored": 0, "last_page_count": 0}
    if not args.skip_transfers:
        transfer_stats = discover_account_transfers(
            wallet_address=wallet,
            api_key=api_key,
            max_pages=max(1, args.max_pages),
            page_size=args.transfer_page_size,
            sleep=max(0.0, args.sleep),
            retries=max(0, args.retries),
            timeout=max(1.0, args.timeout),
            resume=args.resume,
        )

    known_imported = set(STORE.list_distinct_transaction_ids(source="solana_rpc", limit=1000000))
    discovered = set(STORE.list_solscan_account_signatures(wallet, limit=1000000))
    detail_cached = {row["signature"] for row in STORE.list_solscan_transactions(limit=1000000)}
    missing_from_import = sorted(discovered - known_imported)
    missing_detail = sorted(discovered - detail_cached)

    detail_stats = {"candidate_count": len(missing_detail), "fetched": 0, "success": 0, "errors": 0}
    if missing_detail and not args.skip_details:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        from solscan_transaction_backfill import _fetch_store_detail, _merge_stats

        workers = max(1, min(int(args.workers), 32))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(
                    _fetch_store_detail,
                    signature=signature,
                    wallet_address=wallet,
                    api_key=api_key,
                    retries=3,
                    timeout=90,
                    sleep=max(0.0, args.sleep),
                )
                for signature in missing_detail
            ]
            for future in as_completed(futures):
                _merge_stats(detail_stats, future.result())

    final_detail_cached = {row["signature"] for row in STORE.list_solscan_transactions(limit=1000000)}
    print(
        json.dumps(
            {
                "wallet_address": wallet,
                "account_transactions": tx_stats,
                "account_transfers": transfer_stats,
                "known_imported_solana_rpc": len(known_imported),
                "discovered_signatures": len(discovered),
                "missing_from_current_import": len(missing_from_import),
                "missing_detail_before_backfill": len(missing_detail),
                "detail_backfill": detail_stats,
                "missing_detail_after_backfill": len(discovered - final_detail_cached),
                "first_missing_from_current_import": missing_from_import[:20],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def discover_account_transactions(
    *,
    wallet_address: str,
    api_key: str,
    max_pages: int,
    limit: int,
    sleep: float,
    retries: int,
    timeout: float,
    resume: bool,
) -> dict[str, Any]:
    cursor_key = f"runtime.solscan.discovery.{wallet_address}.account_transactions.before"
    before = ""
    if resume:
        before = _setting_value(cursor_key)
    stored = 0
    pages = 0
    seen_cursors: set[str] = set()
    while pages < max_pages:
        params = {"address": wallet_address, "limit": limit}
        if before:
            params["before"] = before
        body = _get_json("/account/transactions", params=params, api_key=api_key, retries=retries, timeout=timeout)
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or not data:
            return {"pages": pages, "stored": stored, "last_page_count": 0, "last_before": before}
        pages += 1
        for item in data:
            if not isinstance(item, dict):
                continue
            signature = str(item.get("tx_hash") or "").strip()
            if not signature:
                continue
            STORE.upsert_solscan_account_transaction(
                wallet_address=wallet_address,
                signature=signature,
                slot=_int_or_none(item.get("slot")),
                block_time_utc=_block_time_utc(item),
                status=str(item.get("status") or ""),
                raw_json=json.dumps(item, ensure_ascii=False, sort_keys=True),
            )
            stored += 1
        next_before = str(data[-1].get("tx_hash") or "").strip() if isinstance(data[-1], dict) else ""
        if not next_before or next_before in seen_cursors:
            return {"pages": pages, "stored": stored, "last_page_count": len(data), "last_before": before}
        seen_cursors.add(next_before)
        before = next_before
        STORE.upsert_setting(cursor_key, before, False)
        if len(data) < limit:
            STORE.upsert_setting(f"runtime.solscan.discovery.{wallet_address}.account_transactions.complete", "true", False)
            return {"pages": pages, "stored": stored, "last_page_count": len(data), "last_before": before}
        if sleep > 0:
            time.sleep(sleep)
    return {"pages": pages, "stored": stored, "last_page_count": limit, "last_before": before}


def discover_account_transfers(
    *,
    wallet_address: str,
    api_key: str,
    max_pages: int,
    page_size: int,
    sleep: float,
    retries: int,
    timeout: float,
    resume: bool,
) -> dict[str, Any]:
    cursor_key = f"runtime.solscan.discovery.{wallet_address}.account_transfers.next_page"
    stored = 0
    pages = 0
    start_page = 1
    if resume:
        try:
            start_page = max(1, int(_setting_value(cursor_key) or "1"))
        except ValueError:
            start_page = 1
    for page in range(start_page, max_pages + 1):
        params = {
            "address": wallet_address,
            "page": page,
            "page_size": page_size,
            "sort_by": "block_time",
            "sort_order": "desc",
            "exclude_amount_zero": "true",
        }
        body = _get_json("/account/transfer", params=params, api_key=api_key, retries=retries, timeout=timeout)
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or not data:
            return {"pages": pages, "stored": stored, "last_page_count": 0}
        pages += 1
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            signature = str(item.get("trans_id") or "").strip()
            transfer_id = _transfer_id(wallet_address, page, index, item)
            STORE.upsert_solscan_account_transfer(
                transfer_id=transfer_id,
                wallet_address=wallet_address,
                signature=signature,
                block_time_utc=_block_time_utc(item),
                flow=str(item.get("flow") or ""),
                activity_type=str(item.get("activity_type") or ""),
                token_address=str(item.get("token_address") or ""),
                token_decimals=_int_or_none(item.get("token_decimals")),
                amount=str(item.get("amount") or ""),
                value_usd=str(item.get("value") or ""),
                from_address=str(item.get("from_address") or ""),
                to_address=str(item.get("to_address") or ""),
                raw_json=json.dumps(item, ensure_ascii=False, sort_keys=True),
            )
            stored += 1
        if len(data) < page_size:
            STORE.upsert_setting(f"runtime.solscan.discovery.{wallet_address}.account_transfers.complete", "true", False)
            return {"pages": pages, "stored": stored, "last_page_count": len(data)}
        STORE.upsert_setting(cursor_key, str(page + 1), False)
        if sleep > 0:
            time.sleep(sleep)
    return {"pages": pages, "stored": stored, "last_page_count": page_size}


def _get_json(path: str, *, params: dict[str, Any], api_key: str, retries: int, timeout: float) -> dict[str, Any]:
    url = f"{BASE_URL}{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"token": api_key, "accept": "application/json"})
    last_error = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body_text = response.read().decode("utf-8", errors="replace")
            break
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            if exc.code not in {429, 500, 502, 503, 504} or attempt >= retries:
                break
            last_error = f"HTTP {exc.code}"
        except (TimeoutError, urllib.error.URLError) as exc:
            last_error = str(exc)
            if attempt >= retries:
                raise RuntimeError(f"Solscan request failed for {path}: {last_error}") from exc
        time.sleep(min(3.0, 0.75 * (attempt + 1)))
    else:
        raise RuntimeError(f"Solscan request failed for {path}: {last_error or 'request failed'}")
    body = json.loads(body_text)
    if not isinstance(body, dict) or body.get("success") is not True:
        raise RuntimeError(f"Solscan request failed for {path}: {body}")
    return body


def _block_time_utc(item: dict[str, Any]) -> str:
    raw = item.get("block_time") or item.get("blockTime")
    if isinstance(raw, (int, float)) and raw > 0:
        return datetime.fromtimestamp(raw, UTC).isoformat()
    if isinstance(raw, str) and raw.isdigit():
        return datetime.fromtimestamp(int(raw), UTC).isoformat()
    text_time = str(item.get("time") or "")
    return text_time.replace(".000Z", "+00:00").replace("Z", "+00:00")


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _setting_value(key: str) -> str:
    row = STORE.get_setting(key)
    if not row:
        return ""
    return str(row.get("value_json") or "").strip()


def _transfer_id(wallet_address: str, page: int, index: int, item: dict[str, Any]) -> str:
    payload = {
        "wallet_address": wallet_address,
        "page": page,
        "index": index,
        "trans_id": item.get("trans_id"),
        "activity_type": item.get("activity_type"),
        "from_address": item.get("from_address"),
        "to_address": item.get("to_address"),
        "token_address": item.get("token_address"),
        "amount": item.get("amount"),
        "block_time": item.get("block_time"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    main()
