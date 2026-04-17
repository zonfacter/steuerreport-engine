#!/usr/bin/env python3
"""Golden hash verification for deterministic regression safety."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_REFERENCE = Path("configs/golden_hashes.json")
DEFAULT_GOLDEN_DIR = Path("tests/fixtures/golden")


def canonical_sha256(payload: Any) -> str:
    """Build a deterministic hash from canonical JSON serialization."""
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def verify_hashes(reference_path: Path, golden_dir: Path) -> int:
    if not reference_path.exists():
        print(f"Missing reference hash file: {reference_path}")
        return 1
    if not golden_dir.exists():
        print(f"Golden fixtures directory missing: {golden_dir}")
        return 1

    reference = load_json(reference_path)
    exit_code = 0

    for tax_year, expected in reference.items():
        golden_file = golden_dir / f"{tax_year}.json"
        if not golden_file.exists():
            print(f"[FAIL] Missing fixture for {tax_year}: {golden_file}")
            exit_code = 1
            continue

        actual_hash = canonical_sha256(load_json(golden_file))
        expected_hash = expected["hash"]

        if actual_hash != expected_hash:
            print(
                f"[FAIL] {tax_year}: expected={expected_hash} actual={actual_hash} "
                f"(fixture={golden_file})"
            )
            exit_code = 1
            continue

        print(f"[OK] {tax_year}: {actual_hash}")

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-years", action="store_true")
    parser.add_argument("--reference", default=str(DEFAULT_REFERENCE))
    parser.add_argument("--golden-dir", default=str(DEFAULT_GOLDEN_DIR))
    args = parser.parse_args()

    _ = args.all_years  # kept for backward compatibility with CI command shape

    return verify_hashes(Path(args.reference), Path(args.golden_dir))


if __name__ == "__main__":
    raise SystemExit(main())
