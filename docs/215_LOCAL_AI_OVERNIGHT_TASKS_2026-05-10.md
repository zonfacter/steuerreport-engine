# Local AI Overnight Tasks - 2026-05-10

## Ziel

Die Punkte ab dem aktuellen Arbeitsstand werden als read-only Analyseauftraege an die lokale KI delegiert, damit die Sitzung beendet werden kann und die KI weiterarbeitet.

## Laufender Dienst

- systemd Unit: `steuerreport-ai-readonly-queue.service`
- Queue Script: `scripts/ai_readonly_task_queue.py`
- Status:

```bash
python3 scripts/ai_readonly_task_queue.py status
systemctl status steuerreport-ai-readonly-queue.service --no-pager
tail -n 80 var/ai_readonly_queue/runner.log
tail -n 80 var/ai_readonly_queue/systemd.log
```

## Snapshot

- Read-only DB: `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`
- Snapshot-Doku: `docs/204_AI_READONLY_DB_SNAPSHOT.md`
- Snapshot wurde vor dem Lauf neu gebaut.

## Neue Queue-Auftraege

| Task ID | Zweck |
|---|---|
| `2025_end_to_end_readiness_20260510` | Steuerjahr 2025 end-to-end auf Risiken, Summen, Bestandsketten, Derivate, Mining/Rewards und CEX/Jupiter/Solana-Abdeckung pruefen. |
| `2025_binance_earn_staking_rewards_20260510` | Binance Earn/Staking/Rewards 2025, BNSOL/SOL/JUP und Reward-Klassifikation pruefen. |
| `2025_bitget_api_blockpit_cex_check_20260510` | Bitget 2025 API/Blockpit/CEX-Abgleich, Derivate/Liquidationen/Bot-Datenluecken pruefen. |
| `2025_jupiter_solana_wallet_swaps_20260510` | Jupiter/Solana Wallet Swaps 2025, Transferketten, Gegenwerte, Nullkosten-/Negativrisiken pruefen. |
| `2025_year_end_holdings_reconciliation_20260510` | Virtuelle Jahresendbestaende 2025 plausibilisieren und Assets mit unrealistischen Restmengen markieren. |
| `exports_pdf_wiso_readiness_2025_2026_20260510` | PDF/WISO-Export-Readiness 2025/2026 inklusive Mining/Rewards und Derivate pruefen. |
| `mining_rewards_business_private_split_20260510` | Gewerbe/Privat-Split fuer Mining/Rewards und spaetere Veraeusserungen pruefen. |
| `db_audit_hygiene_snapshot_export_plan_20260510` | DB-/Audit-Hygiene, Backup/Snapshot/final-current Exportordner und Handoff-Konsolidierung planen. |

## Ergebnisorte

- Ergebnisindex: `var/ai_readonly_queue/results.jsonl`
- Einzelberichte: `var/ai_db_countercheck_*.md`
- Einzel-JSON: `var/ai_db_countercheck_*.json`
- Queue-Dateien:
  - pending: `var/ai_readonly_queue/pending/`
  - running: `var/ai_readonly_queue/running/`
  - done: `var/ai_readonly_queue/done/`
  - failed: `var/ai_readonly_queue/failed/`

## Erwarteter naechster Cloud-Schritt

1. Queue-Status lesen.
2. Neue `result_md` Dateien aus `results.jsonl` pruefen.
3. KI-Funde gegen Live-DB/API validieren.
4. Nur belegte technische Fixes umsetzen.
5. Danach Exporte/Snapshots neu bauen und Gate erneut pruefen.
