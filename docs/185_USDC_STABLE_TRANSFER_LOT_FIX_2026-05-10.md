# USDC Stable-Transfer-Lot Fix

Stand: 2026-05-10

## Ausgangslage

- Offenes Review-Issue vor Fix: `zero_cost_tax_lots:2024:USDC`.
- Dossier vor Fix: `docs/184_USDC_2024_ZERO_COST_DOSSIER_2026-05-10.md`
- Befund:
  - `6` steuerpflichtige USDC-Zeilen mit `cost_basis_eur=0`.
  - Menge: `3023.923486 USDC`
  - Erloes: `2843.308609417790648892983983 EUR`
  - USDC-Mengenbestand war praktisch gedeckt; einziger aktiver Bruch war Dust `-0.000002 USDC`.
- Ursache:
  - USDC-Zufluesse kamen als Stablecoin-Transfers/Deposits in die aktive Chronologie.
  - Transfers wurden korrekt nicht als steuerbare Veraeusserung behandelt, erzeugten aber auch keine FIFO-Lots.
  - Dadurch hatten spaetere USDC-Swaps/Trades zwar Erloese, aber keine Anschaffungskosten.

## Umsetzung

- `src/tax_engine/core/processor.py`
  - Eingehende Stablecoin-Transfers/Deposits (`USDT`, `USDC`, `BUSD`, etc.; ohne `EUR`) erzeugen jetzt FIFO-Lots mit USD/EUR-FX-Basis.
  - Ausgehende Stablecoin-Transfers verbrauchen FIFO-Lots nicht steuerbar und erzeugen keine Steuerzeile.
  - Nicht-Stable-Transfers bleiben unveraendert reine Transfers.
- Testabdeckung:
  - Stablecoin-Inbound erzeugt Cost Basis.
  - Stablecoin-Outbound verbraucht Lots ohne Steuerzeile.
  - Normale Binance-Wallet-Deposits wie `SOL` bleiben keine Anschaffung.

## Ergebnis nach Neuberechnung 2024

- Neuer 2024-Job: `b7531c5c-6f24-45f2-9499-8e963c62de62`
- `zero_cost_tax_lots:2024:USDC` ist nicht mehr im Review-Inbox.
- Rest im USDC-Dossier:
  - `1` Dust-Zeile
  - Menge: `0.000002 USDC`
  - Erloes: `0.000001893578471013762814449849252 EUR`
  - Dieser Rest liegt unter der Medium-Issue-Schwelle und ist kein aktiver Review-Blocker.
- Offene Zero-Cost-Medium-Issues danach:
  - `2022/USDT`: `3` Zeilen, `1377.09 EUR`
  - `2024/JUP`: `5` Zeilen, `1941.79 EUR`

## Tests

Ausgefuehrt:

```bash
PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_process_endpoints.py tests/unit/core/test_processor_fifo.py tests/unit/core/test_tax_domains.py
```

Ergebnis: `46 passed`, `1` Deprecation-Warnung aus Importlib.
