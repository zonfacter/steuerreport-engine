# JUP Swap-In Price-Lot Fix

Stand: 2026-05-10

## Ausgangslage

- Offenes Review-Issue vor Fix: `zero_cost_tax_lots:2024:JUP`.
- Dossier vor Fix: `docs/186_JUP_2024_ZERO_COST_DOSSIER_2026-05-10.md`
- Befund:
  - `5` steuerpflichtige JUP-Zeilen mit `cost_basis_eur=0`.
  - Menge: `1912.104783 JUP`
  - Erloes: `1941.789576577914067123048912 EUR`
  - Kein aktiver JUP-Mengenbruch; JUP-Endbestand positiv.
- Ursache:
  - Die betroffenen FIFO-Lots stammten aus `solana_rpc` `swap_in_aggregated`-Events.
  - Diese Swap-In-Events hatten Mengen und Gegenassets, aber keinen `price_usd`, `price_eur` oder `value_usd_sum`.
  - JUP/USD-Preise waren im FX-Cache vorhanden, wurden aber fuer Swap-In-Lots noch nicht als Anschaffungspreis gesetzt.

## Umsetzung

- `src/tax_engine/queue/service.py`
  - Neue enge Vorverarbeitung `attach_cached_usd_prices_to_swap_in_events`.
  - Nur `solana_rpc` + `swap_in_aggregated` + `side=in` wird bepreist.
  - Normale Token-Transfers bleiben unveraendert.
  - Preisquelle ist der vorhandene FX-Cache des Zielassets, z. B. `JUP/USD`.
- `run_next_queued_job` speichert `swap_in_price_summary` im Processing Result.

## Ergebnis nach Neuberechnung 2024

- Neuer 2024-Job: `a7431b53-fab6-4f38-b41f-228ba122b9c2`
- `swap_in_price_summary.attached_price_count`: `13`
- `zero_cost_tax_lots:2024:JUP` ist nicht mehr im Review-Inbox.
- Aktualisiertes JUP-Dossier:
  - `docs/186_JUP_2024_ZERO_COST_DOSSIER_2026-05-10.md`
  - `0` Nullkosten-Zeilen.
- Offene Zero-Cost-Medium-Issues danach:
  - Nur noch `2022/USDT`: `3` Zeilen, `1377.09 EUR`.

## Tests

Ausgefuehrt:

```bash
PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_process_endpoints.py tests/unit/core/test_processor_fifo.py tests/unit/core/test_tax_domains.py
```

Ergebnis: `48 passed`, `1` Deprecation-Warnung aus Importlib.
