# Pionex HNT und Stable-Pair Preisfix

Stand: 2026-05-10

## Ergebnis

Das nach dem frischen Gesamtlauf sichtbare HNT-Zero-Cost-Issue `2023/HNT` wurde als Software-Mappingfehler behoben.

Vorher:

- Issue: `zero_cost_tax_lots:2023:HNT:3a93ddf0-c817-41dd-ab5f-1f0ac591353f`
- `26` HNT-Zeilen
- `1804.97 EUR` Erlöse mit Cost Basis `0`

Nach dem Fix und erneuter Berechnung:

- `2023/HNT` ist nicht mehr in der Issue Inbox.
- Offenes Zero-Cost-Issue bleibt nur `2022/USDT`.
- Aktueller Gesamtlauf: `docs/190_CURRENT_TAX_RUNS_2026-05-10.md`

## Ursache

Die betroffenen HNT-Lots waren Pionex-HNT-Käufe aus 2022, zum Beispiel `HNT_USDT`.

Die Rohdaten enthielten:

- `asset=HNT`
- `price=4.91690625`
- `raw_row.symbol=HNT_USDT`

Aber die normalisierte Quote fehlte. Dadurch wurde der Pionex-Preis nicht sauber als USD-Stable-Quote in EUR umgerechnet.

Beim ersten Fix wurde sichtbar, dass eine zweite Schutzregel fehlte: Stablecoin-Legs wie `USDT` aus `BTCUSDT` dürfen niemals den BTC-Marktpreis als USDT-Stückpreis nutzen. Für Stablecoins zählt der USD/EUR-Kurs.

## Code

- `src/tax_engine/fx/service.py`
  - erkennt Stable-Quote jetzt auch aus `raw_row.symbol`, z. B. `HNT_USDT`.
  - erzeugt daraus `price_eur` über den USD/EUR-Kurs.
- `src/tax_engine/core/processor.py`
  - `_extract_unit_price_eur` überspringt fehlende Preisfelder jetzt korrekt, statt bei `0` zu stoppen.
  - Stable-Assets (`USDT`, `USDC`, usw.) verwenden in der FIFO-Bewertung zuerst den FX-Kurs, nicht den Marktpreis eines Handelspaars.

## Validierung

Gezielte Tests:

```bash
PYTHONPATH=src python3 -m pytest -q \
  tests/unit/core/test_processor_fifo.py::test_stable_asset_ignores_pair_market_price_for_unit_basis \
  tests/unit/core/test_processor_fifo.py::test_pionex_stable_quote_price_eur_creates_nonzero_hnt_lot_basis \
  tests/unit/fx/test_fx_service.py::test_enrich_events_infers_usd_quote_from_pionex_raw_symbol
```

Breiter Testlauf:

```bash
PYTHONPATH=src python3 -m pytest -q \
  tests/unit/fx/test_fx_service.py \
  tests/unit/core/test_processor_fifo.py \
  tests/unit/api/test_issue_endpoints.py \
  tests/unit/api/test_process_endpoints.py \
  tests/unit/core/test_tax_domains.py
```

Ergebnis: `86 passed`, `1` Importlib-Deprecation-Warnung.

## Aktueller Stand

Nach erneutem Lauf von `scripts/run_current_tax_years_20260510.py`:

- Steuerjahre: `2020..2026`
- Gesamt Tax Lines: `31837`
- Derivative Lines: `36`
- Review-Gate: `allow_export=True`
- Offene Issues: `1`
- Offenes Issue: `2022/USDT`, `3` Zeilen, `1383.45 EUR`

