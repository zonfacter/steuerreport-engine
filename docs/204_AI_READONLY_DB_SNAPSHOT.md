# AI Readonly DB Snapshot

- Quelle: `/root/.local/share/steuerreport/steuerreport.db`
- Snapshot: `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`
- Modus: Datei ist mit `0444` read-only gesetzt.
- Nicht enthalten: `settings`, `audit_trail`, `sqlite_sequence`.
- Zweck: lokale KI darf Daten analysieren, aber keine Produktivdaten oder Secrets veraendern.

## Read-only Verbindung

```bash
sqlite3 'file:/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite?mode=ro&immutable=1'
```

## Wichtige Views

- `ai_raw_events_flat`: Rohereignisse mit den wichtigsten JSON-Feldern als Spalten.
- `ai_tax_lines_flat`: Tax-Lines inklusive Steuerjahr/Job-Status.
- `ai_latest_completed_jobs`: abgeschlossene Jobs, chronologisch nach Steuerjahr.
- `ai_latest_completed_jobs_per_year`: genau der neueste abgeschlossene Job je Steuerjahr.
- `ai_open_zero_cost_tax_lines`: steuerpflichtige Zeilen aus den neuesten Jobs mit Erlös und Cost Basis 0.
- `ai_transfer_matches_flat`: Transfer-Matches inklusive Outbound-/Inbound-Payload.

## Kopierte Tabellen

- `derivative_lines`
- `fx_cache`
- `processing_queue`
- `product_position_events`
- `raw_events`
- `report_integrity`
- `report_snapshots`
- `ruleset_catalog`
- `solscan_account_transactions`
- `solscan_account_transfers`
- `solscan_transactions`
- `source_files`
- `tax_lines`
- `transfer_matches`
