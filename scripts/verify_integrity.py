#!/usr/bin/env python3
import argparse
import json
from hashlib import sha256
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-years", action="store_true")
    parser.add_argument("--reference", default=None)
    args = parser.parse_args()

    golden_dir = Path("tests/fixtures/golden")
    if not golden_dir.exists() or not golden_dir.is_dir():
        print("Golden fixtures directory missing: tests/fixtures/golden")
        return 1
    reference_path = Path(args.reference) if args.reference else golden_dir / "hashes.json"
    if not reference_path.exists():
        print(f"Golden hash reference missing: {reference_path}")
        return 1
    try:
        expected_hashes = json.loads(reference_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {reference_path}: {exc}")
        return 1
    if not isinstance(expected_hashes, dict):
        print(f"Golden hash reference must be an object: {reference_path}")
        return 1

    expected_files = ["DE-2024.json", "DE-2025.json", "DE-2026.json"]
    missing = [name for name in expected_files if not (golden_dir / name).exists()]
    if missing:
        print(f"Golden fixtures missing files: {', '.join(missing)}")
        return 1

    for name in expected_files:
        file_path = golden_dir / name
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON in {file_path}: {exc}")
            return 1
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = sha256(canonical.encode("utf-8")).hexdigest()
        expected = str(expected_hashes.get(name, "")).strip()
        if not expected:
            print(f"Missing expected golden hash for {name} in {reference_path}")
            return 1
        if digest != expected:
            print(f"Golden hash drift for {name}: expected {expected}, got {digest}")
            return 1
        print(f"{name}: {digest} OK")

    print("Integrity verification executed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
