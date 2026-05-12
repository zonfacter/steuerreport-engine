#!/usr/bin/env python3
"""Download Fairspot CSV exports for direct Helium wallet counterparties."""

from __future__ import annotations

import csv
import json
import shutil
import time
import urllib.request
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-05-12"
OWN_WALLETS = {
    "133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j",
    "14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA",
}
DEFAULT_OUTPUT_DIR = Path("/root/.local/share/steuerreport/fairspot_wallet_exports")
FAIRSPOT_URL = "https://fairspot.nyc3.digitaloceanspaces.com/accounting-csv/helium-{}-all.csv"


def existing_seed_paths() -> list[Path]:
    return [
        Path(f"/tmp/fairspot-helium-{wallet}-all.csv")
        for wallet in OWN_WALLETS
        if Path(f"/tmp/fairspot-helium-{wallet}-all.csv").exists()
    ]


def discover_direct_contacts(seed_paths: list[Path]) -> dict[str, dict[str, Any]]:
    contacts: dict[str, dict[str, Any]] = {}
    for path in seed_paths:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                payer = str(row.get("payer") or "").strip()
                payee = str(row.get("payee") or "").strip()
                if payer in OWN_WALLETS and payee and payee not in OWN_WALLETS:
                    add_contact(contacts, payee, "outgoing_from_own", row)
                if payee in OWN_WALLETS and payer and payer not in OWN_WALLETS:
                    add_contact(contacts, payer, "incoming_to_own", row)
    return contacts


def add_contact(contacts: dict[str, dict[str, Any]], wallet: str, direction: str, row: dict[str, Any]) -> None:
    item = contacts.setdefault(
        wallet,
        {
            "direct_count": 0,
            "incoming_to_own": 0,
            "outgoing_from_own": 0,
            "samples": [],
        },
    )
    item["direct_count"] += 1
    item[direction] += 1
    if len(item["samples"]) < 5:
        item["samples"].append(
            {
                "date": row.get("date", ""),
                "transaction_hash": row.get("transaction_hash", ""),
                "hnt_amount": row.get("hnt_amount", ""),
                "payer": row.get("payer", ""),
                "payee": row.get("payee", ""),
            }
        )


def copy_seed_if_available(wallet: str, target: Path) -> None:
    seed = Path(f"/tmp/fairspot-helium-{wallet}-all.csv")
    if seed.exists() and not target.exists():
        shutil.copy2(seed, target)


def download_wallet(wallet: str, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"helium-{wallet}-all.csv"
    copy_seed_if_available(wallet, target)
    status = "exists" if target.exists() else "downloaded"
    error = ""
    url = FAIRSPOT_URL.format(wallet)
    if not target.exists():
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                target.write_bytes(response.read())
            time.sleep(0.2)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            status = "error"
            error = f"{type(exc).__name__}: {exc}"
    rows = count_csv_rows(target) if target.exists() else 0
    return {
        "wallet": wallet,
        "url": url,
        "path": str(target),
        "status": "error" if error else status,
        "error": error,
        "size_bytes": target.stat().st_size if target.exists() else 0,
        "row_count": rows,
    }


def count_csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def main() -> int:
    seed_paths = existing_seed_paths()
    contacts = discover_direct_contacts(seed_paths)
    wallets = sorted(OWN_WALLETS | set(contacts))
    manifest_rows = []
    for wallet in wallets:
        row = download_wallet(wallet, DEFAULT_OUTPUT_DIR)
        row["direct_contact"] = contacts.get(wallet, {})
        row["is_own_wallet"] = wallet in OWN_WALLETS
        manifest_rows.append(row)
    manifest = {
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "fairspot_direct_wallet_cache_20260512",
        "output_dir": str(DEFAULT_OUTPUT_DIR),
        "wallet_count": len(wallets),
        "error_count": sum(1 for row in manifest_rows if row["status"] == "error"),
        "wallets": manifest_rows,
    }
    manifest_path = DEFAULT_OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path), **{k: manifest[k] for k in ("wallet_count", "error_count")}}, indent=2))
    return 0 if manifest["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
