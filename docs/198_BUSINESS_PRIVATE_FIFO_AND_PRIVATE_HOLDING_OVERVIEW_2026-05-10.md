# Business-/Privat-FIFO und private Haltefrist-Übersicht

Stand: 2026-05-10 14:12 UTC

## Umsetzung

- FIFO-Lots tragen jetzt eine Herkunft: `business` oder `private`.
- Reward-/Mining-nahe Zuflüsse und explizite `BUSINESS`/`EUER` Overrides erzeugen Business-Lots.
- Verkäufe/Swaps aus Business-Lots werden als `tax_domain=euer_business_disposal` und `tax_status=business` markiert.
- Private Kauf-/Swap-Lots bleiben `tax_domain=private_veraeusserung`.
- Gematchte Transfers tragen die ursprüngliche Lot-Herkunft, den ursprünglichen Erwerbszeitpunkt und die ursprüngliche Cost Basis auf den Ziel-Transfer weiter.
- Das Lot-Aging kann nach `domain=private`, `domain=business` oder ohne Domain-Filter abgefragt werden.

## API / Dashboard

- Endpoint: `GET /api/v1/portfolio/lot-aging?as_of_utc=...&asset=...&domain=private`
- Dashboard: Bestände -> Lot Aging hat jetzt einen Bereichsfilter:
  - `Privat`
  - `Betriebsvermögen`
  - `Alle`
- Die Lot-Tabelle zeigt die neue Spalte `Bereich`.
- Die Asset-Zusammenfassung wird nach dem gewählten Bereich neu aggregiert, damit Gesamtmenge, steuerfrei, steuerpflichtig und Lot-Anzahl zusammenpassen.

## Neuer Gesamtlauf 2020-2026

- Script: `scripts/run_current_tax_years_20260510.py`
- Summary: `var/current_tax_summary_2026-05-10.json`
- Jobs/Exports: `var/current_tax_jobs_2026-05-10.jsonl`, `var/report_exports_current_2026-05-10/`
- Jahresübersicht: `docs/190_CURRENT_TAX_RUNS_2026-05-10.md`

| Jahr | Job | Anlage SO privat netto EUR | EÜR BV-Veräußerung netto EUR | EÜR Ergebnis EUR |
|---:|---|---:|---:|---:|
| 2020 | `ebfa221e-3a63-4508-9df5-26857affbb00` | 0 | 0 | 0 |
| 2021 | `7eca7e99-899c-4397-893c-72341fac395a` | 25589.86108601877668630073922 | 8055.915712504424293312513697 | 20091.60739633581739216509304 |
| 2022 | `3f28e472-06f1-43a5-b7f8-cf9cea5aa383` | -9788.606190760881971889011824 | -10084.43842393730970360306668 | -322.726595509983894505036169 |
| 2023 | `2becbdd1-ad2e-4b99-bb21-f45d6985131b` | -4501.887241509443459687292038 | -1032.636546619158381988517602 | 559.153033683591521689170865 |
| 2024 | `99d1a66a-9556-422d-9c01-34d763d1af56` | -1751.84514207395545202546904 | 1611.053564472835508252762095 | 3902.992268106862097953019423 |
| 2025 | `629171d6-d5f4-4e01-8aa7-6d4eb482eb28` | 9738.584749217347301097332569 | 0.037523227099415481468900001 | 747.8265330260676535214924705 |
| 2026 | `130f8123-fb30-4296-aa86-a58c836906c3` | 0 | 0 | 26.62449231868769297855626282 |

## Live-Prüfung Port 8000

Health:

- `GET /api/v1/health` -> `success`

Private SOL-Haltefrist zum `2026-12-31T23:59:59Z`:

- Request: `/api/v1/portfolio/lot-aging?as_of_utc=2026-12-31T23:59:59Z&domain=private&asset=SOL`
- `asset_count=1`
- `lot_count=74`
- `SOL total_qty=179.099206605`
- `SOL qty_exempt=179.099206605`
- `SOL qty_taxable=0`

Betriebsvermögen SOL zum selben Stichtag:

- Request: `/api/v1/portfolio/lot-aging?as_of_utc=2026-12-31T23:59:59Z&domain=business&asset=SOL`
- `asset_count=1`
- `lot_count=101`
- `SOL total_qty=0.145607172`
- `SOL qty_taxable=0.145607172`

Korrekturhinweis:

- Die erste Live-Prüfung der Lot-Aging-API zeigte fälschlich `441.289269218` private SOL.
- Ursache: Der Dashboard-Endpunkt nutzte noch nicht die vollständige Processing-Pipeline mit Integration-Filter, Pionex-/Solscan-Dedupe und Preisankerung.
- Behoben in `src/tax_engine/api/dashboard.py`: Lot-Aging nutzt jetzt `_list_processing_effective_raw_events()` und damit dieselbe Event-Basis wie der Steuerlauf.

## Offener Punkt

- Stand 2026-05-10 14:32 UTC: Die in diesem Dokument zuerst genannte SOL-Haltefrist (`179.099206605` privat) ist durch den nachfolgenden Transfer-Out-Fix ueberholt.
- Aktueller Port-8000-Stand nach Fix: Gesamt `3.975449536 SOL`, privat `3.829842364 SOL`, Betriebsvermoegen `0.145607172 SOL`.
- Auch dieser Stand ist noch kein bestaetigter Realbestand; Details siehe `docs/199_SOL_CURRENT_BALANCE_RECONCILIATION_2026-05-10.md`.
- Ein Medium-Issue bleibt offen: `zero_cost_tax_lots:2022:USDT:3f28e472-06f1-43a5-b7f8-cf9cea5aa383`.
- Dieser Punkt wurde bewusst offen gelassen, weil 2020-2022 steuerlich abgeschlossen sind.
- Die Business-/Privat-Trennung ist technisch aktiv; fachlich bleibt zu prüfen, ob einzelne historische Rewards bewusst entnommen wurden. Ohne Entnahme bleiben sie in dieser Systemlogik Betriebsvermögen.

## Validierung

- `python3 -m py_compile src/tax_engine/core/processor.py src/tax_engine/core/tax_domains.py src/tax_engine/db/store.py src/tax_engine/api/dashboard.py src/tax_engine/queue/service.py src/tax_engine/api/reporting.py`
- `node --check src/tax_engine/ui/static/app.js`
- `PYTHONPATH=src python3 -m pytest -q tests/unit/core/test_processor_fifo.py tests/unit/core/test_tax_domains.py tests/unit/api/test_process_endpoints.py::test_portfolio_lot_aging_shows_split_lots` -> `23 passed`
- `PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_process_endpoints.py tests/unit/api/test_api_coverage_gate.py tests/unit/api/test_issue_endpoints.py::test_review_gates_block_on_material_zero_cost_tax_lots` -> `39 passed`
