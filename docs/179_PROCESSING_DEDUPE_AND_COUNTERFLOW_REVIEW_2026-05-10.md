# Processing-Dedupe und Counterflow-Review

Stand: 2026-05-10

## Ergebnis

Die High-Blocker sind wieder weg. Port `8000` meldet nach den Neulaeufen:

- `allow_export=true`
- `issues_total=4`
- `issues_high_open=0`
- `unmatched_total=0`
- `balance_adjustment_candidates_open=0`

Offen bleiben nur Medium-Nullbasis-Issues:

- `2022/USDT`: `3` Zeilen, `1377.09 EUR` Erloes
- `2024/IOT`: `11` Zeilen, `1692.24 EUR` Erloes
- `2024/USDC`: `6` Zeilen, `2843.31 EUR` Erloes
- `2024/JUP`: `5` Zeilen, `1941.79 EUR` Erloes

## Technische Aenderungen

Code:

- `src/tax_engine/queue/service.py`
  - `drop_exact_pionex_duplicate_events()` entfernt Pionex-Exportdubletten nur zur Verarbeitung. Rohdaten bleiben unveraendert.
  - `drop_solscan_duplicates_when_solana_rpc_is_active()` entfernt `solscan_wallet_discovery`-Duplikate, wenn ein passendes `solana_rpc`-Primaerevent aktiv ist.
  - `attach_reference_usd_value_anchors()` nutzt zusaetzlich Solscan-Detail-Counterflows:
    - zuerst USDC/USDT-Stable-Gegenfluss,
    - danach WSOL/SOL-Gegenfluss mal vorhandenen SOL/USD-Tageskurs.

Tests:

- `tests/unit/api/test_process_endpoints.py::test_attach_reference_usd_value_anchors_from_solscan_to_solana_rpc`
- `tests/unit/api/test_process_endpoints.py::test_attach_reference_usd_value_anchors_from_solscan_stable_counterflow`
- `tests/unit/api/test_process_endpoints.py::test_attach_reference_usd_value_anchors_from_solscan_wsol_counterflow`
- `tests/unit/api/test_process_endpoints.py::test_drop_solscan_duplicate_when_solana_rpc_is_active`
- `tests/unit/api/test_process_endpoints.py::test_drop_exact_pionex_duplicate_events_keeps_first_copy`
- `tests/unit/core/test_processor_fifo.py::test_raw_value_usd_sum_with_fx_sets_eur_cost_basis`
- `tests/unit/api/test_issue_endpoints.py::test_review_gates_block_on_material_zero_cost_tax_lots`

Ergebnis: `7 passed`.

## Neue Jobs

- 2022: `c94a113e-1423-4ac1-8a72-9a12cd1156b1`
  - Pionex-Dubletten entfernt: `1719`
  - Anlage SO steuerpflichtige private Veraeusserungen netto: `1627.868685771598639700000000 EUR`
- 2024: `42cf80fc-2d66-4e9e-af73-bcaf563e5dc3`
  - Pionex-Dubletten entfernt: `1719`
  - Solscan-Duplikate entfernt: `264`
  - Counterflow-/Bewertungsanker angehaengt: `339`, davon `75` aus Solscan-Transaktions-Counterflow
  - Anlage SO steuerpflichtige private Veraeusserungen netto: `6549.677590135332735746180487 EUR`

## Bewertung

Die Pionex-Dubletten waren real und material: `3520` aktive Pionex-Zeilen enthielten `1719` exakte Dubletten-Gruppen. Die Korrektur passiert bewusst nur im Processing, damit die Importhistorie auditierbar bleibt.

Die verbleibenden Medium-Issues sind keine API-/Preisfehler mehr, sondern fachliche Anschaffungsketten-Pruefungen. Sie blockieren nach aktueller Gate-Policy den Export nicht, sollten aber vor einer finalen Abgabe einzeln bewertet oder bestaetigt werden.
