#!/usr/bin/env python3
"""Document remaining 2022 USDT zero-cost rows after HNT closure."""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-05-12"
DEFAULT_DB = Path("/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite")
OUT_JSON = ROOT / "var" / "usdt_2022_remaining_after_hnt_closure_2026-05-12.json"
OUT_MD = ROOT / "docs" / "238_USDT_2022_REMAINING_AFTER_HNT_CLOSURE_2026-05-12.md"

PIONEX_DIRS = (
    ROOT / "usertransfer" / "pionex",
    ROOT / "usertransfer" / "pionex_txn_2021-12-31_2022-12-30_gen_2026-05-05",
)
PIONEX_FILES = (
    "deposit-withdraw.csv",
    "trading.csv",
    "raw-trading-details.csv",
    "for-cointracker.csv",
    "for-cointracking.csv",
    "others.csv",
    "staking.csv",
    "structured-products.csv",
    "position_futures.csv",
    "dust-collector.csv",
)


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Any) -> str:
    value_dec = dec(value)
    text = format(value_dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def load_json(text: str) -> dict[str, Any]:
    try:
        loaded = json.loads(text or "{}")
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def latest_jobs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return rows(
        conn,
        """
        SELECT pq.tax_year, pq.job_id, pq.updated_at_utc, pq.result_json,
               count(dl.id) AS derivative_line_count
        FROM ai_latest_completed_jobs_per_year pq
        LEFT JOIN derivative_lines dl ON dl.job_id = pq.job_id
        WHERE tax_year BETWEEN 2021 AND 2022
        GROUP BY pq.tax_year, pq.job_id, pq.updated_at_utc, pq.result_json
        ORDER BY tax_year
        """,
    )


def remaining_lines(conn: sqlite3.Connection) -> list[dict[str, str]]:
    output = []
    for row in rows(
        conn,
        """
        SELECT tax_year, line_no, asset, qty, buy_timestamp_utc, sell_timestamp_utc,
               cost_basis_eur, proceeds_eur, gain_loss_eur, source_event_id, lot_source_event_id
        FROM ai_open_zero_cost_tax_lines
        WHERE asset IN ('HNT', 'USDT')
          AND CAST(proceeds_eur AS REAL) >= 50
        ORDER BY tax_year, asset, line_no
        """,
    ):
        output.append({key: str(value or "") for key, value in row.items()})
    return output


def raw_event(conn: sqlite3.Connection, event_id: str) -> dict[str, Any]:
    row = rows(
        conn,
        """
        SELECT re.unique_event_id, re.row_index, sf.source_name, re.payload_json
        FROM raw_events re
        JOIN source_files sf ON sf.source_file_id = re.source_file_id
        WHERE re.unique_event_id = ?
        """,
        (event_id,),
    )[0]
    payload = load_json(str(row["payload_json"]))
    return {
        "event_id": str(row["unique_event_id"]),
        "source_name": str(row["source_name"]),
        "row_index": int(row["row_index"] or 0),
        "timestamp_utc": str(payload.get("timestamp_utc") or ""),
        "source": str(payload.get("source") or ""),
        "event_type": str(payload.get("event_type") or ""),
        "side": str(payload.get("side") or ""),
        "asset": str(payload.get("asset") or ""),
        "quantity": str(payload.get("quantity") or ""),
        "price": str(payload.get("price") or ""),
        "tx_id": str(payload.get("tx_id") or ""),
        "raw_symbol": str((payload.get("raw_row") or {}).get("symbol") or ""),
        "raw_side": str((payload.get("raw_row") or {}).get("side") or ""),
        "raw_operation": str((payload.get("raw_row") or {}).get("operation") or ""),
    }


def binance_jan5_summary(conn: sqlite3.Connection) -> dict[str, str]:
    movements = rows(
        conn,
        """
        SELECT json_extract(payload_json, '$.side') AS side,
               json_extract(payload_json, '$.event_type') AS event_type,
               json_extract(payload_json, '$.quantity') AS quantity
        FROM raw_events
        WHERE json_extract(payload_json, '$.asset') = 'USDT'
          AND json_extract(payload_json, '$.source') LIKE 'binance%'
          AND json_extract(payload_json, '$.timestamp_utc') BETWEEN '2022-01-05T00:00:00+00:00'
              AND '2022-01-05T23:59:59+00:00'
        """,
    )
    in_total = Decimal("0")
    out_total = Decimal("0")
    fees = Decimal("0")
    for row in movements:
        qty = dec(row.get("quantity"))
        side = str(row.get("side") or "")
        event_type = str(row.get("event_type") or "")
        if side == "in":
            in_total += qty
        elif event_type == "fee":
            fees += qty
            out_total += qty
        else:
            out_total += qty
    return {
        "in_usdt": plain(in_total),
        "out_usdt": plain(out_total),
        "fee_usdt": plain(fees),
        "net_usdt": plain(in_total - out_total),
        "row_count": str(len(movements)),
    }


def pionex_file_summary() -> list[dict[str, str]]:
    output = []
    for folder in PIONEX_DIRS:
        for name in PIONEX_FILES:
            path = folder / name
            if not path.exists():
                continue
            count = 0
            early_usdt_rows = 0
            fields: list[str] = []
            with path.open(newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                fields = list(reader.fieldnames or [])
                for row in reader:
                    count += 1
                    text = json.dumps(row, ensure_ascii=False).lower()
                    if "usdt" in text and ("2021-" in text or "2022-01" in text or "12/" in text or "01/" in text):
                        early_usdt_rows += 1
            output.append(
                {
                    "folder": str(folder.relative_to(ROOT)),
                    "file": name,
                    "rows": str(count),
                    "early_usdt_rows": str(early_usdt_rows),
                    "fields": ", ".join(fields),
                }
            )
    return output


def source_coverage(conn: sqlite3.Connection) -> list[dict[str, str]]:
    return [
        {key: str(value or "") for key, value in row.items()}
        for row in rows(
            conn,
            """
            SELECT sf.source_name, count(*) AS rows
            FROM source_files sf
            JOIN raw_events re ON re.source_file_id = sf.source_file_id
            WHERE sf.source_name LIKE '%pionex%' OR sf.source_name LIKE '%Pionex%'
            GROUP BY sf.source_name
            ORDER BY sf.source_name
            """,
        )
    ]


def build_audit(db_path: Path = DEFAULT_DB) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        remaining = remaining_lines(conn)
        events = [raw_event(conn, row["source_event_id"]) for row in remaining]
        jobs = latest_jobs(conn)
        return {
            "created_at_utc": datetime.now(UTC).isoformat(),
            "db_path": str(db_path),
            "latest_jobs": [
                {
                    "tax_year": int(row["tax_year"]),
                    "job_id": str(row["job_id"]),
                    "updated_at_utc": str(row["updated_at_utc"]),
                    "tax_line_count": str(load_json(str(row["result_json"])).get("tax_line_count") or ""),
                    "derivative_line_count": str(row["derivative_line_count"] or "0"),
                }
                for row in jobs
            ],
            "remaining_lines": remaining,
            "source_events": events,
            "binance_2022_01_05": binance_jan5_summary(conn),
            "pionex_file_summary": pionex_file_summary(),
            "pionex_imported_sources": source_coverage(conn),
            "conclusion": {
                "status": "no_deterministic_auto_fix",
                "reason": (
                    "Die drei verbliebenen Zeilen sind echte USDT-Verwendungen. Lokal sichtbar sind "
                    "Binance-HNT/USDT-Gegenbewegungen und Pionex-MXC_USDT-Trades, aber kein separater "
                    "Opening-/Bot-/Strategy-Kapitalbeleg fuer die fehlende USDT-Herkunft."
                ),
                "next_safe_step": (
                    "USDT 2022 nur mit Pionex Opening Balance, Bot/Grid-Statement, Strategy Account Statement "
                    "oder expliziter Review-Entscheidung weiter behandeln."
                ),
            },
        }
    finally:
        conn.close()


def table(headers: list[str], body: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(str(value) for value in row) + " |" for row in body],
    ]


def render_doc(audit: dict[str, Any]) -> str:
    remaining = audit["remaining_lines"]
    line_by_event = {row["source_event_id"]: row["line_no"] for row in remaining}
    binance_line = next(
        (line_by_event.get(event["event_id"], "?") for event in audit["source_events"] if event["source"] == "binance"),
        "?",
    )
    pionex_lines = [
        line_by_event.get(event["event_id"], "?") for event in audit["source_events"] if event["source"] == "pionex"
    ]
    total_qty = sum((dec(row["qty"]) for row in remaining), Decimal("0"))
    total_proceeds = sum((dec(row["proceeds_eur"]) for row in remaining), Decimal("0"))
    lines = [
        "# USDT 2022 Restblock nach HNT-Schliessung",
        "",
        f"Stand: {RUN_DATE}",
        "",
        "## Ergebnis",
        "",
        f"- Verbleibende HNT/USDT-Zero-Cost-Zeilen >= 50 EUR: `{len(remaining)}`",
        "- Asset: `USDT 2022`",
        f"- Menge: `{plain(total_qty)} USDT`",
        f"- Erloes: `{plain(total_proceeds)} EUR`",
        "- HNT ist nach dem Roundtrip-Match nicht mehr im >=50-EUR-Restblock enthalten.",
        "- Es wurde kein automatischer Preis-, FX- oder Cost-Basis-Fix abgeleitet.",
        "",
        "## Aktuelle Jobs",
        "",
    ]
    lines.extend(
        table(
            ["Jahr", "Job", "Tax Lines", "Derivative Lines", "Aktualisiert"],
            [
                [
                    str(row["tax_year"]),
                    f"`{row['job_id']}`",
                    row["tax_line_count"],
                    row["derivative_line_count"],
                    row["updated_at_utc"],
                ]
                for row in audit["latest_jobs"]
            ],
        )
    )
    lines.extend(["", "## Offene Zeilen", ""])
    lines.extend(
        table(
            ["Line", "Asset", "Menge", "Zeit", "Erloes EUR", "Quelle"],
            [
                [
                    row["line_no"],
                    row["asset"],
                    row["qty"],
                    row["sell_timestamp_utc"],
                    row["proceeds_eur"],
                    row["source_event_id"][:12] + "...",
                ]
                for row in remaining
            ],
        )
    )
    lines.extend(["", "## Raw-Event-Kontext", ""])
    lines.extend(
        table(
            ["Line/Event", "Quelle", "Typ", "Side", "Menge", "Tx/Raw", "Roh-Kontext"],
            [
                [
                    event["event_id"][:12] + "...",
                    event["source"],
                    event["event_type"],
                    event["side"],
                    event["quantity"],
                    event["tx_id"],
                    event["raw_symbol"] or event["raw_operation"],
                ]
                for event in audit["source_events"]
            ],
        )
    )
    b = audit["binance_2022_01_05"]
    lines.extend(
        [
            "",
            "## Binance 2022-01-05",
            "",
            f"- USDT-In aus sichtbaren Binance-Bewegungen: `{b['in_usdt']} USDT`",
            f"- USDT-Out inkl. Fees: `{b['out_usdt']} USDT`",
            f"- Fees: `{b['fee_usdt']} USDT`",
            f"- Tagesnetto: `{b['net_usdt']} USDT`",
            "- Der 2022-01-05-Rest ist damit kein reiner Sortier- oder Dezimalfehler.",
        ]
    )
    lines.extend(["", "## Lokale Pionex-Dateien", ""])
    lines.extend(
        table(
            ["Ordner", "Datei", "Zeilen", "Fruehe USDT-Zeilen"],
            [
                [row["folder"], row["file"], row["rows"], row["early_usdt_rows"]]
                for row in audit["pionex_file_summary"]
            ],
        )
    )
    lines.extend(["", "## Importierte Pionex-Quellen", ""])
    lines.extend(
        table(
            ["Quelle", "Rows"],
            [[row["source_name"], row["rows"]] for row in audit["pionex_imported_sources"]],
        )
    )
    lines.extend(
        [
            "",
            "## Einordnung",
            "",
            f"- Line `{binance_line}` ist Binance-USDT-Verbrauch am `2022-01-05`; am selben Tag sind HNT/USDT-Verkaeufe sichtbar, aber die spaeteren USDT-Spends uebersteigen den belegten Tagesbestand.",
            f"- Lines `{', '.join(pionex_lines)}` sind Pionex-`MXC_USDT`-BUY-Kontext; das erklaert die USDT-Verwendung, aber nicht die vorherige USDT-Herkunft.",
            "- `raw-trading-details.csv` liefert mehr Fill-Details, aber keine separate Opening-Balance oder Strategy-/Bot-Kapitalbuchung.",
            "- Nebenlisten `others`, `staking`, `structured-products`, `position_futures` sind fuer den fruehen USDT-Block leer.",
            "- Naechster sicherer Schritt bleibt ein Primaerbeleg: Pionex Opening Balance, Bot/Grid-/Strategy-Statement oder eine explizite Review-Entscheidung.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    audit = build_audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(audit, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    OUT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "doc": str(OUT_MD)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
