# Binance SOL Staking BNSOL Primary Import - 2026-05-08

## Befund

Der verbleibende `BNSOL`-Negativbestand kam aus einem Binance Convert-Out am `2025-03-23T13:46:29.121Z`:

- `22.32305193 BNSOL` out
- `5532.20028976 JUP` in
- Binance Convert Order: `1958518736382069622`

Die Herkunft des BNSOL war nicht durch die vorhandenen effektiven Events abgebildet. Blockpit enthielt zwar eine manuelle Auto-Balancing-Zeile, diese bleibt aber ausgeschlossen, weil sie keine Primaerquelle ist.

## Primaerquelle

Gezielte Binance-API-Probes:

- `var/binance_bnsol_simple_earn_record_probe_2026-05-08.json`
- `var/binance_sol_staking_history_probe_2026-05-08.json`
- `var/binance_bnsol_jan_mar2025_probe_2026-05-08.json`

Der relevante Primaerbeleg kam aus:

- Endpoint: `/sapi/v1/sol-staking/sol/history/stakingHistory`
- Zeit: `2025-02-28T09:35:47Z`
- `amount`: `23.189761 SOL`
- `distributeAsset`: `BNSOL`
- `distributeAmount`: `22.32304223 BNSOL`
- `exchangeRate`: `1.038826194`
- Status: `SUCCESS`

## Import

- Script: `scripts/import_binance_sol_staking_bnsol_primary.py`
- Import JSON: `var/binance_sol_staking_bnsol_primary_import_2026-05-08.json`
- Source: `binance_sol_staking_bnsol_primary_2025_api_2026-05-08`
- Normalisierte Events:
  - `staking_conversion` / `out` / `23.189761 SOL`
  - `staking_conversion` / `in` / `22.32304223 BNSOL`

## Bewertung

Das ist keine manuelle Korrektur und kein Opening-Balance-Adjustment. Es ist ein nachgezogener Binance-Primärimport fuer die SOL-zu-BNSOL-Konversion. Die spaeteren BNSOL-Rewards und die Simple-Earn Subscription/Redemption bestaetigen den Bestand zusaetzlich, werden aber nicht als Ersatz fuer die Herkunftsbuchung verwendet.
