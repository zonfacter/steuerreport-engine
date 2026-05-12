# Bitget 2025 Derivate Pipeline Fix - 2026-05-10

## Scope

- Auftrag: lokale KI-Befunde gegen Readonly-DB verifizieren und Bitget-2025-Derivate klaeren.
- Readonly-DB: `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`
- Job: `f4342b4b-a502-47cf-a5dc-255eda49d94c`
- Steuerjahr: `2025`

## Verifizierte DB-Befunde

Der KI-Befund "keine Bitget-API-Daten 2025" ist falsch bzw. zu grob. Die
Readonly-DB enthaelt 2025 Bitget-Tax-API-Derivatevents:

```sql
SELECT source, event_type, side, COUNT(*) AS cnt
FROM ai_raw_events_flat
WHERE substr(timestamp_utc,1,4)='2025'
  AND source='bitget_tax_api'
  AND event_type LIKE 'derivative%'
GROUP BY source,event_type,side;
```

Ergebnis:

| Eventtyp | Seite | Zeilen |
| --- | --- | ---: |
| derivative open_long | in | 247 |
| derivative open_short | in | 198 |
| derivative close_long | in | 83 |
| derivative close_long | out | 152 |
| derivative close_short | in | 107 |
| derivative close_short | out | 95 |
| derivative fee | in | 52 |
| derivative fee | out | 110 |
| derivative loss | out | 3 |
| derivative user_grants_issue | in | 1 |

Gleichzeitig hat der 2025-Job keine gespeicherten `derivative_lines`:

```sql
SELECT pq.tax_year, pq.job_id, pq.status, COUNT(dl.id) AS derivative_lines
FROM processing_queue pq
LEFT JOIN derivative_lines dl ON dl.job_id=pq.job_id
WHERE pq.job_id='f4342b4b-a502-47cf-a5dc-255eda49d94c'
GROUP BY pq.tax_year,pq.job_id,pq.status;
```

Ergebnis: `tax_year=2025`, `status=completed`, `derivative_lines=0`.

Wichtig fuer kuenftige Audits: `raw_events` hat keine `source`-Spalte und
`derivative_lines` hat keine `tax_year`-Spalte. Belastbare Queries muessen
`ai_raw_events_flat` nutzen oder `derivative_lines` ueber `processing_queue`
auf das Steuerjahr joinen.

## Ursache

Deterministischer Codefehler:

- `src/tax_engine/core/derivatives.py` las Zeitstempel nur aus
  `timestamp`, `datetime`, `date` oder `time`.
- Die Bitget-Tax-API-Payloads im Bestand tragen aber `timestamp_utc`.
- Dadurch wurden Bitget-Derivatevents bereits vor der Klassifikation
  verworfen.

Zweiter deterministischer Modellfehler:

- Bitget-Futures-Bills enthalten fuer diese Daten keine stabile Position-ID.
- Die belegte Struktur aus `docs/60_BITGET_DERIVATIVE_LIQUIDATION_AUDIT_2026-05-08.md`:
  - `open_long/open_short`: `amount=0`, balance-relevant ist die Fee.
  - `close_long/close_short`: realisierter PnL plus Fee.
  - `contract_settle_fee`: Funding-/Settlement-Cashflow.
- Diese Zeilen duerfen nicht als offene Positionspaare mit erfundener Cost Basis
  behandelt werden, sondern als einzelne Cash-Settlement-Zeilen aus den
  vorhandenen Primaerwerten `raw_row.amount` und `raw_row.fee`.

## Umsetzung

Deterministischer Fix:

- Der DerivativesManager liest jetzt `timestamp_utc`.
- Bitget-`bitget_tax_api`-Derivatevents ohne explizite `position_id` werden eng
  als einzelne Cash-Settlement-Lines verarbeitet.
- `gain_loss_eur` entsteht nur aus vorhandenen Primaerfeldern:
  `raw_row.amount + raw_row.fee`.
- `derivative user_grants_issue` wird nicht als Derivateposition geoeffnet.

Keine Preise, FX-Kurse, Anschaffungskosten, Cost Basis oder steuerliche
Endbewertung wurden erfunden.

## Gegenprobe

Lokale Simulation auf den 2025-Bitget-Tax-API-Raw-Events aus der Readonly-DB:

```text
processed_events=1047
standalone_cash_settlements=1047
open_positions_remaining=0
unmatched_closes=0
line_count=1047
derivative_gain_loss_total_eur=-2110.92099932
derivative_loss_bucket_total_eur=4061.19773596
```

Diese Simulation ersetzt noch keinen neu gerechneten Processing-Job in der
Readonly-DB. Der aktuelle gespeicherte Job bleibt unveraendert bei
`derivative_lines=0`, bis der Steuerlauf neu ausgefuehrt und der Readonly-
Snapshot danach neu gebaut wird.

## Tests

Ergaenzt:

- `test_derivatives_manager_reads_timestamp_utc_payloads`
- `test_derivatives_manager_maps_bitget_futures_cash_settlements`

Validiert:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q \
  tests/unit/core/test_derivatives_manager.py \
  tests/unit/api/test_process_endpoints.py::test_worker_run_next_completes_queued_job \
  tests/unit/connectors/test_cex_service.py::test_fetch_cex_transactions_preview_bitget_maps_data

python3 -m ruff check src/tax_engine/core/derivatives.py \
  tests/unit/core/test_derivatives_manager.py --no-cache
```

## Verbleibende Blocker

- Der 2025-Job `f4342b4b-a502-47cf-a5dc-255eda49d94c` muss neu gerechnet werden,
  damit `derivative_lines` in der Projekt-DB persistiert werden.
- Danach muss die AI-Readonly-DB neu gebaut werden, bevor KI-/Audit-Queries den
  neuen Zustand sehen.
- Die technische Erfassung der Bitget-Cash-Settlements ist nicht identisch mit
  einer steuerberaterlich finalen Beurteilung.
