from __future__ import annotations

from pathlib import Path

from tax_engine.api.app import BulkFolderImportRequest, import_bulk_folder
from tax_engine.ingestion.store import STORE


def _reset_store() -> None:
    STORE.reset_for_tests()


def test_bulk_folder_import_inserts_and_deduplicates(tmp_path: Path) -> None:
    _reset_store()
    folder = tmp_path / "imports"
    folder.mkdir(parents=True, exist_ok=True)

    content = (
        "Date (UTC);Integration Name;Label;Outgoing Asset;Outgoing Amount;Incoming Asset;Incoming Amount;"
        "Fee Asset (optional);Fee Amount (optional);Comment (optional);Trx. ID (optional);Source Type;Source Name\n"
        "30.12.2025 23:59:59;Binance;Swap;SOL;1.5;JUP;100;SOL;0.01;;bp-1;API;Binance\n"
    )
    (folder / "2025_blockpit_export.csv").write_text(content, encoding="utf-8")
    (folder / "unknown_data.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    first = import_bulk_folder(
        BulkFolderImportRequest(
            folder_path=str(folder),
            recursive=True,
            dry_run=False,
            max_files=20,
            max_rows_per_file=10000,
        )
    )
    assert first.status == "success"
    assert first.data["processed_files"] == 1
    assert first.data["inserted_events"] == 3
    assert first.data["duplicate_events"] == 0
    assert any(item.get("code") == "connector_not_detected" for item in first.warnings)

    second = import_bulk_folder(
        BulkFolderImportRequest(
            folder_path=str(folder),
            recursive=True,
            dry_run=False,
            max_files=20,
            max_rows_per_file=10000,
        )
    )
    assert second.status == "success"
    assert second.data["processed_files"] == 1
    assert second.data["inserted_events"] == 0
    assert second.data["duplicate_events"] == 3

