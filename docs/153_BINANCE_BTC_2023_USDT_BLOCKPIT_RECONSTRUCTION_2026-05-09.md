# Binance BTC 2023 USDT Blockpit Reconstruction - 2026-05-09

## Ergebnis

- Modus: `execute`
- Importierte Events: `1`
- Duplikate: `0`
- Bestehende Rekonstruktionszeilen: `0`

## Rekonstruktionszeile

- `2023-05-02T04:10:12+00:00` `buy` `0.00264 BTC` gegen `73.9885872 USDT` fee `0.00000264 BTC` reference `2c7b321092f19acd0280eb378b8b3ee7e7b4e8359ec5b8ec0806a3053b1b6390`

## Bewertung

- The BTC source-chain candidate audit marks this Blockpit Binance API row as covered by active USDT balance at the event timestamp.
- Only this USDT->BTC trade is imported. BUSD, DOGE, VET and WIN references remain blocked because they need separate counterasset evidence first.
- This reduces the active BTC gap without shifting it into an uncovered counterasset.
