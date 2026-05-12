# Binance Dust / Blockpit Reference Exclusions - 2026-05-09

## Zweck

Gezielte Exclusion von Blockpit-Referenzzeilen, wenn dieselbe Dust-Convert-Bewegung bereits aus Binance API als Primaerdatensatz vorhanden ist.

- Kandidaten: `3`
- Eingetragen/aktualisiert: `3`
- Unveraendert: `0`

## Exclusions

- `VTHO` 2023-05-02T04:13:23+00:00 qty `42.39387934`: `blockpit-7068:out` -> primary `binance_api:136251331484`
- `BUSD` 2023-05-02T04:13:23+00:00 qty `0.55379925`: `blockpit-7074:out` -> primary `binance_api:136251331484`
- `GFT` 2021-03-29T16:48:07+00:00 qty `0.0081`: `blockpit-7619:out` -> primary `binance_api:47394524243`
  - Blockpit labels the dust row as GFT while Binance primary and trade history use legacy GTO.

## Bewertung

- Only Blockpit reference rows are excluded; Binance API primary rows stay tax-effective.
- This removes duplicate dust-convert movements without deleting evidence.
- VTHO may still need a separate acquisition/reward evidence decision after duplicate removal.
