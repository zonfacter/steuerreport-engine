# Bitget BTC 2024 Blockpit Reconstruction - 2026-05-09

## Ergebnis

- Modus: `execute`
- Importierte Events: `2`
- Duplikate: `0`
- Bestehende Rekonstruktionszeilen: `0`

## Rekonstruktionszeilen

- `2024-03-07T19:55:23+00:00` `deposit` `in` `0.0046913 BTC` tx `1149723330782900226` reference `5ad748422708de3e9af93735d7f1c1be19ba9e6311028487d9a24966def5c0bd`
- `2024-03-11T11:47:00+00:00` `trade` `sell` `0.000121 BTC` tx `1151049976081231876-1151049976081231877` reference `1f629f06d8033d4d04ee82c522f0f208d0c635abae91fb142311f4c0add4d3ea`

## Bewertung

- Bitget Tax API starts the BTC sequence with four BTC out legs on 2024-04-14, causing a platform-local negative BTC balance.
- Blockpit's Bitget API reference contains an earlier BTC deposit on 2024-03-07 and a small BTC sell on 2024-03-11.
- Only these two pre-break rows are imported as narrow reconstruction evidence; the 2024-04-14 Blockpit merged trade is not imported to avoid duplicating Bitget Tax API rows.
