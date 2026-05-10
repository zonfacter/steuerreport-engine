# MOBILE Solscan Value-Sum Price Fix - 2026-05-09

## Ergebnis

- Offener High-Issue `missing_price` fuer `MOBILE` am `2023-07-30T06:59:13+00:00` wurde fachlich aufgeloest.
- Betroffener Event: `9e9de7a0a36f34129ba33933c47dba9e39e7a70ef01957f808db60e2526c8135`.
- Transaktion: `5LbqXnxbEfXmPegwuURc4CAjHa7RsufqEpreUssrA8ip9ydzGKUiPaDGJp6DJTu8iGzys8bSDejMHYf9p3AD9hyX`.
- Ursache: Der Solscan-Import enthielt bereits `raw_row.value_usd_sum = 22.000764000000007`, aber Review/FX/Processor nutzten dieses Raw-Feld noch nicht als Bewertungsquelle.

## Umsetzung

- `src/tax_engine/api/dashboard.py`
  - `_estimate_event_values` akzeptiert jetzt Raw-Indexed-Transfer-Werte aus `raw_row.value_usd_sum` oder passend gefilterten `raw_transfers[].value_usd`.
- `src/tax_engine/fx/service.py`
  - FX-Enrichment wandelt `value_usd_sum` bei vorhandenem USD/EUR-Kurs in `value_eur` um.
- `src/tax_engine/core/processor.py`
  - FIFO-Prozessor kann `value_usd_sum` mit `fx_rate_usd_eur` in einen EUR-Einheitspreis ableiten.

## Live-Pruefung

- Port `8000` wurde neu gestartet.
- `/api/v1/issues/inbox`:
  - `issues_total=0`
  - `high_open=0`
  - `missing_price_open=0`
- `/api/v1/review/gates`:
  - `allow_export=false`
  - `issues_high_open=0`
  - `balance_adjustment_candidates_open=1`
  - einziger Blocker bleibt `pionex-usdt-opening-balance-2021-12-28` mit `needs_evidence`.

## Neuer 2023-Draft

- Neuer Job: `c8065ea8-d697-4721-8873-d091478b5341`
- Exportdateien:
  - `var/report_exports_current_2026-05-09/2023_c8065ea8-d697-4721-8873-d091478b5341_all.json`
  - `var/report_exports_current_2026-05-09/2023_c8065ea8-d697-4721-8873-d091478b5341_tax.csv`
  - `var/report_exports_current_2026-05-09/2023_c8065ea8-d697-4721-8873-d091478b5341_wiso.csv`
- Gesamtuebersicht aktualisiert:
  - `docs/168_CURRENT_TAX_DRAFT_RUNS_2026-05-09.md`
  - `var/current_tax_draft_summary_2026-05-09.json`

## Tests

- `python3 -m py_compile src/tax_engine/api/dashboard.py src/tax_engine/core/processor.py src/tax_engine/fx/service.py`
- `PYTHONPATH=src pytest -q tests/unit/api/test_issue_endpoints.py::test_solscan_indexed_swap_value_is_not_missing_price tests/unit/fx/test_fx_service.py::test_enrich_events_converts_raw_value_usd_sum tests/unit/core/test_processor_fifo.py::test_raw_value_usd_sum_with_fx_sets_unit_price_for_swap`
- `PYTHONPATH=src pytest -q tests/unit/api/test_issue_endpoints.py tests/unit/fx/test_fx_service.py tests/unit/core/test_processor_fifo.py`
