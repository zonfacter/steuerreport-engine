# JUP 2025 Solscan Stable-Counterflow-Bewertung

Stand: 2026-05-10

## Ergebnis

Das 2025/JUP-High-Issue aus dem Nullbasis-Gate ist technisch behoben.

- Vorheriger Gate-Stand nach nur `solscan_wallet_discovery`-Ankern: `2025/JUP high`, `25` steuerpflichtige Nullbasis-Zeilen, `5920.71 EUR` Erloes.
- Neuer 2025-Lauf: `dc4aae2c-338d-430a-914a-eaa2eb80d904`.
- Bewertungsanker im Lauf: `327` insgesamt, davon `63` aus `solscan_transaction_counterflow`.
- Neuer 2025 Anlage-SO-Stand:
  - Leistungen: `747.7890097989682380400235705 EUR`
  - Private Veraeusserungen steuerpflichtig netto: `14389.70577854374306336500091 EUR`
  - Steuerpflichtige Gewinne: `18624.42398808396222274566428 EUR`
  - Steuerpflichtige Verluste: `-4234.718209540219159380663366 EUR`
- Live Review-Gate Port `8000`: `allow_export=true`, `issues_total=2`, `issues_high_open=0`, keine Blocker.

## Umsetzung

Code:

- `src/tax_engine/queue/service.py`
  - `attach_reference_usd_value_anchors()` nutzt weiter zuerst direkte `solscan_wallet_discovery`-Referenzen.
  - Neuer Fallback: Wenn ein aktives `solana_rpc`-Event keinen Wert hat, wird die gecachte Solscan-Detailtransaktion gelesen.
  - Voraussetzung: Wallet-Tokenaenderung passt nach `wallet_address`, Token-Mint, Richtung und Menge zum Rohereignis.
  - Dann wird der groesste stabile Gegenfluss aus USDC/USDT in derselben Transaktion als `value_usd_sum` gesetzt.
  - Referenzmarker: `valuation_reference_source=solscan_transaction_counterflow`, `valuation_reference_tx_id=<signature>`.

Tests:

- `tests/unit/api/test_process_endpoints.py::test_attach_reference_usd_value_anchors_from_solscan_to_solana_rpc`
- `tests/unit/api/test_process_endpoints.py::test_attach_reference_usd_value_anchors_from_solscan_stable_counterflow`
- `tests/unit/core/test_processor_fifo.py::test_raw_value_usd_sum_with_fx_sets_eur_cost_basis`
- `tests/unit/api/test_issue_endpoints.py::test_review_gates_block_on_material_zero_cost_tax_lots`

Ergebnis: `4 passed`.

## Noch offen

Das Gate blockiert nicht mehr, aber zwei Medium-Issues bleiben fachlich offen:

- `2022/USDT`: `3` steuerpflichtige Nullbasis-Zeilen, `1377.09 EUR` Erloes.
- `2024/USDC`: `6` steuerpflichtige Nullbasis-Zeilen, `2843.31 EUR` Erloes.

Diese sind unterhalb der High-Schwelle, sollten aber vor einer wirklich finalen Abgabe fachlich geprueft oder explizit bestaetigt werden.
