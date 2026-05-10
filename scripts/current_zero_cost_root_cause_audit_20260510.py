from __future__ import annotations

import json
import sqlite3
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path.home() / ".local" / "share" / "steuerreport" / "steuerreport.db"
CREATED_DATE = "2026-05-10"
OUT_JSON = ROOT / "var" / f"current_zero_cost_root_cause_audit_{CREATED_DATE}.json"
OUT_MD = ROOT / "docs" / f"212_CURRENT_ZERO_COST_ROOT_CAUSE_AUDIT_{CREATED_DATE}.md"

JUP_MINT = "JUPYIWRYJFSKUPIHA7HKER8VUTAEFOSYBKEDZNSDVCN"


def dec(value: object) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def fmt(value: Decimal) -> str:
    return value.normalize().to_eng_string() if value else "0"


def rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def latest_jobs(conn: sqlite3.Connection) -> list[dict[str, object]]:
    return rows(
        conn,
        """
        WITH latest AS (
            SELECT tax_year, max(updated_at_utc) AS updated_at_utc
            FROM processing_queue
            WHERE status = 'completed'
            GROUP BY tax_year
        )
        SELECT pq.job_id, pq.tax_year, pq.ruleset_id, pq.updated_at_utc, pq.result_json
        FROM processing_queue pq
        JOIN latest l ON l.tax_year = pq.tax_year AND l.updated_at_utc = pq.updated_at_utc
        ORDER BY pq.tax_year
        """,
    )


def zero_cost_summary(conn: sqlite3.Connection) -> list[dict[str, object]]:
    return rows(
        conn,
        """
        WITH latest AS (
            SELECT tax_year, max(updated_at_utc) AS updated_at_utc
            FROM processing_queue
            WHERE status = 'completed'
            GROUP BY tax_year
        ),
        jobs AS (
            SELECT pq.*
            FROM processing_queue pq
            JOIN latest l ON l.tax_year = pq.tax_year AND l.updated_at_utc = pq.updated_at_utc
        )
        SELECT
            jobs.tax_year,
            tl.asset,
            count(*) AS lines,
            sum(cast(tl.qty AS REAL)) AS qty,
            sum(cast(tl.proceeds_eur AS REAL)) AS proceeds_eur
        FROM tax_lines tl
        JOIN jobs ON jobs.job_id = tl.job_id
        WHERE cast(tl.cost_basis_eur AS REAL) = 0
          AND cast(tl.qty AS REAL) > 0
          AND cast(tl.proceeds_eur AS REAL) > 0
        GROUP BY jobs.tax_year, tl.asset
        ORDER BY jobs.tax_year, tl.asset
        """,
    )


def zero_cost_lines(conn: sqlite3.Connection, tax_year: int, asset: str) -> list[dict[str, object]]:
    return rows(
        conn,
        """
        WITH latest AS (
            SELECT tax_year, max(updated_at_utc) AS updated_at_utc
            FROM processing_queue
            WHERE status = 'completed' AND tax_year = ?
            GROUP BY tax_year
        ),
        job AS (
            SELECT pq.job_id
            FROM processing_queue pq
            JOIN latest l ON l.tax_year = pq.tax_year AND l.updated_at_utc = pq.updated_at_utc
        )
        SELECT
            tl.line_no,
            tl.asset,
            tl.qty,
            tl.buy_timestamp_utc,
            tl.sell_timestamp_utc,
            tl.cost_basis_eur,
            tl.proceeds_eur,
            tl.gain_loss_eur,
            tl.source_event_id,
            tl.lot_source_event_id
        FROM tax_lines tl
        JOIN job ON job.job_id = tl.job_id
        WHERE tl.asset = ?
          AND cast(tl.cost_basis_eur AS REAL) = 0
          AND cast(tl.proceeds_eur AS REAL) > 0
        ORDER BY tl.sell_timestamp_utc, tl.line_no
        """,
        (tax_year, asset),
    )


def raw_event_details(conn: sqlite3.Connection, event_ids: list[str]) -> list[dict[str, object]]:
    if not event_ids:
        return []
    placeholders = ",".join("?" for _ in event_ids)
    return rows(
        conn,
        f"""
        SELECT
            json_extract(r.payload_json, '$.timestamp_utc') AS timestamp_utc,
            json_extract(r.payload_json, '$.source') AS source,
            json_extract(r.payload_json, '$.event_type') AS event_type,
            json_extract(r.payload_json, '$.side') AS side,
            json_extract(r.payload_json, '$.asset') AS asset,
            json_extract(r.payload_json, '$.quantity') AS quantity,
            json_extract(r.payload_json, '$.price_usd') AS price_usd,
            json_extract(r.payload_json, '$.value_usd_sum') AS value_usd_sum,
            json_extract(r.payload_json, '$.defi_label') AS defi_label,
            json_extract(r.payload_json, '$.tx_id') AS tx_id,
            r.unique_event_id,
            sf.source_name
        FROM raw_events r
        LEFT JOIN source_files sf ON sf.source_file_id = r.source_file_id
        WHERE r.unique_event_id IN ({placeholders})
        ORDER BY timestamp_utc, source
        """,
        tuple(event_ids),
    )


def jup_timeline(conn: sqlite3.Connection) -> list[dict[str, object]]:
    data = rows(
        conn,
        """
        SELECT
            json_extract(payload_json, '$.timestamp_utc') AS timestamp_utc,
            json_extract(payload_json, '$.event_type') AS event_type,
            json_extract(payload_json, '$.side') AS side,
            json_extract(payload_json, '$.quantity') AS quantity,
            json_extract(payload_json, '$.defi_label') AS defi_label,
            json_extract(payload_json, '$.tx_id') AS tx_id,
            unique_event_id
        FROM raw_events
        WHERE json_extract(payload_json, '$.source') = 'solana_rpc'
          AND json_extract(payload_json, '$.asset') = ?
          AND json_extract(payload_json, '$.timestamp_utc') BETWEEN '2024-08-01T00:00:00+00:00' AND '2024-11-25T23:59:59+00:00'
        ORDER BY timestamp_utc
        """,
        (JUP_MINT,),
    )
    running = Decimal("0")
    enriched: list[dict[str, object]] = []
    for item in data:
        qty = dec(item.get("quantity"))
        delta = qty if item.get("side") == "in" else -qty
        running += delta
        enriched.append({**item, "delta": fmt(delta), "running_qty": fmt(running)})
    return enriched


def usdt_pionex_deposits_until_worst(conn: sqlite3.Connection) -> list[dict[str, object]]:
    return rows(
        conn,
        """
        SELECT
            json_extract(r.payload_json, '$.timestamp_utc') AS timestamp_utc,
            json_extract(r.payload_json, '$.source') AS source,
            json_extract(r.payload_json, '$.event_type') AS event_type,
            json_extract(r.payload_json, '$.side') AS side,
            json_extract(r.payload_json, '$.asset') AS asset,
            json_extract(r.payload_json, '$.quantity') AS quantity,
            json_extract(r.payload_json, '$.tx_id') AS tx_id,
            r.unique_event_id,
            sf.source_name
        FROM raw_events r
        LEFT JOIN source_files sf ON sf.source_file_id = r.source_file_id
        WHERE json_extract(r.payload_json, '$.asset') = 'USDT'
          AND json_extract(r.payload_json, '$.timestamp_utc') <= '2022-01-19T12:56:19+00:00'
          AND (
              (json_extract(r.payload_json, '$.source') = 'pionex' AND json_extract(r.payload_json, '$.event_type') = 'deposit')
              OR (json_extract(r.payload_json, '$.source') = 'binance_api' AND json_extract(r.payload_json, '$.event_type') = 'withdrawal')
          )
        ORDER BY timestamp_utc, source
        """,
    )


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    jobs = latest_jobs(conn)
    summary = zero_cost_summary(conn)
    usdt_lines = zero_cost_lines(conn, 2022, "USDT")
    jup_lines = zero_cost_lines(conn, 2024, "JUP")
    focused_ids = [str(line["source_event_id"]) for line in usdt_lines + jup_lines if line.get("source_event_id")]
    focused_raw = raw_event_details(conn, focused_ids)
    jup_flow = jup_timeline(conn)
    usdt_deposits = usdt_pionex_deposits_until_worst(conn)

    output = {
        "created_date": CREATED_DATE,
        "db_path": str(DB_PATH),
        "latest_jobs": [
            {
                "tax_year": job["tax_year"],
                "job_id": job["job_id"],
                "ruleset_id": job["ruleset_id"],
                "updated_at_utc": job["updated_at_utc"],
            }
            for job in jobs
        ],
        "zero_cost_summary": summary,
        "focused": {
            "usdt_2022_lines": usdt_lines,
            "jup_2024_lines": jup_lines,
            "source_events": focused_raw,
            "jup_solana_rpc_aug_nov_timeline": jup_flow,
            "usdt_binance_pionex_deposits_until_2022_01_19_125619": usdt_deposits,
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    usdt_qty = sum(dec(line["qty"]) for line in usdt_lines)
    usdt_proceeds = sum(dec(line["proceeds_eur"]) for line in usdt_lines)
    jup_qty = sum(dec(line["qty"]) for line in jup_lines)
    jup_proceeds = sum(dec(line["proceeds_eur"]) for line in jup_lines)
    usdt_known_pionex_deposit_qty = sum(
        dec(item["quantity"])
        for item in usdt_deposits
        if item.get("source") == "pionex" and item.get("event_type") == "deposit"
    )

    first_negative = next((item for item in jup_flow if dec(item["running_qty"]) < 0), None)

    md: list[str] = [
        "# Current Zero-Cost Root-Cause Audit - 2026-05-10",
        "",
        "## Ergebnis",
        "",
        "- Quelle: Live-DB `/root/.local/share/steuerreport/steuerreport.db`.",
        "- Scope: aktuellste completed Processing-Jobs je Steuerjahr.",
        "- Zweck: Current-State-Abgleich nach KI-Queue und FIFO-Tail-Trace.",
        "",
        "## Aktuelle Nullkosten-Zusammenfassung",
        "",
        "| Jahr | Asset | Zeilen | Menge | Erlös EUR |",
        "|---:|---|---:|---:|---:|",
    ]
    for item in summary:
        md.append(
            f"| {item['tax_year']} | `{item['asset']}` | {item['lines']} | {item['qty']} | {item['proceeds_eur']} |"
        )

    md.extend(
        [
            "",
            "## USDT 2022",
            "",
            f"- Aktuelle Nullkosten-Menge: `{fmt(usdt_qty)} USDT`.",
            f"- Betroffener Erlös: `{fmt(usdt_proceeds)} EUR`.",
            f"- Bekannte Pionex-Deposits bis `2022-01-19T12:56:19+00:00`: `{fmt(usdt_known_pionex_deposit_qty)} USDT`.",
            "- Bewertung: Die betroffenen Zeilen sind FIFO-Tail-Splits. Es fehlen keine einzelnen Sale-Events, sondern USDT-Lots vor den Pionex/Binance-Verwendungen.",
            "- Der harte Belegblocker bleibt das Pionex-Start-/Botkapital bzw. eine Primärhistorie vor dem ersten Januar-2022-Bruch. Ohne Beleg keine steuerwirksame Zuflussfiktion setzen.",
            "",
            "| Line | Zeit | Menge | Erlös EUR | Source Event |",
            "|---:|---|---:|---:|---|",
        ]
    )
    for line in usdt_lines:
        md.append(
            f"| {line['line_no']} | `{line['sell_timestamp_utc']}` | {line['qty']} | {line['proceeds_eur']} | `{line['source_event_id']}` |"
        )

    if jup_qty == 0:
        jup_status_lines = [
            "- Status nach Override: `resolved_current_state`.",
            "- Bewertung: Die frueher offenen JUP-Nullkosten-Zeilen sind im aktuellen Steuerlauf verschwunden.",
            "- Der Fix war ein enger Ausschluss des DCA/Program-Funding-Transfers `5344f1f97c15fec9aff2fb8c2590bed1fb0b4bda8fef6bfce2371121085f74db`; spaetere DCA-Swaps bleiben steuerwirksam.",
        ]
    else:
        jup_status_lines = [
            "- Status: `open_current_state`.",
            "- Bewertung: Das ist aktuell wieder offen. Der fruehere Swap-In-Preisfix loest Preis-Nullen, aber nicht diese Mengenluecke.",
            "- Naechster sinnvoller Fix: sichere DCA/Program-Transfer-Kandidaten identifizieren und als nicht steuerwirksame Transferkette fuehren, nur soweit Tx-Kontext und Gegenfluss belastbar sind.",
        ]

    md.extend(
        [
            "",
            "## JUP 2024",
            "",
            f"- Aktuelle Nullkosten-Menge: `{fmt(jup_qty)} JUP`.",
            f"- Betroffener Erlös: `{fmt(jup_proceeds)} EUR`.",
            *jup_status_lines,
            "- Die Solana-RPC-Zeitlinie zeigt einen massiven negativen JUP-Lauf ab dem DCA/Program-Transfer am `2024-08-29`.",
        ]
    )
    if first_negative:
        md.append(
            f"- Erster negativer Solana-RPC-JUP-Lauf: `{first_negative['timestamp_utc']}` nach `{first_negative['event_type']}` `{first_negative['side']}` `{first_negative['quantity']}` JUP, Running `{first_negative['running_qty']}`."
        )
    md.extend(
        [
            "- Fachlich war das kein Preisproblem, sondern ein Klassifikations-/Bestandsproblem: DCA-/Program-Transfers duerfen nicht blind wie normale steuerpflichtige Verkaeufe behandelt werden, wenn sie nur Token in ein Programm verschieben und spaeter DCA-Swaps separat sichtbar werden.",
            "",
            "| Line | Zeit | Menge | Erlös EUR | Source Event |",
            "|---:|---|---:|---:|---|",
        ]
    )
    for line in jup_lines:
        md.append(
            f"| {line['line_no']} | `{line['sell_timestamp_utc']}` | {line['qty']} | {line['proceeds_eur']} | `{line['source_event_id']}` |"
        )

    md.extend(
        [
            "",
            "## JUP Solana-RPC-Timeline Aug-Nov 2024",
            "",
            "| Zeit | Typ | Seite | Menge | Delta | Running | TX |",
            "|---|---|---|---:|---:|---:|---|",
        ]
    )
    for item in jup_flow:
        md.append(
            f"| `{item['timestamp_utc']}` | `{item['event_type']}` | `{item['side']}` | {item['quantity']} | {item['delta']} | {item['running_qty']} | `{item['tx_id']}` |"
        )

    md.extend(
        [
            "",
            "## Naechste Umsetzung",
            "",
            "1. USDT 2022: weiter als dokumentierten Review-Blocker bzw. explizite Nullbasis-Entscheidung fuehren, bis Pionex Primaerbeleg liefert.",
            "2. HNT 2021/2022: Legacy-/Mining-/Reward-Anschaffungskette offen halten; steuerlich abgeschlossene Jahre nicht ueberfokussieren, aber Belege nicht loeschen.",
            "3. Nach jedem weiteren Fix: Snapshot fuer lokale KI neu bauen und KI-Queue erneut auf die offenen Current-State-Issues ansetzen.",
            "",
            f"JSON: `{OUT_JSON.relative_to(ROOT)}`",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps({"json": str(OUT_JSON), "markdown": str(OUT_MD), "zero_cost_groups": len(summary)}, indent=2))


if __name__ == "__main__":
    main()
