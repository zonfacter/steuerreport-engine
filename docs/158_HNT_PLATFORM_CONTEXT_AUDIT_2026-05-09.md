# HNT Platform Context Audit - 2026-05-09

## Ergebnis

- Globaler HNT-Endsaldo: `1577.92535200143114379127906`
- Plattformlokale negative HNT-Konten: `2`

## Bewertung

- HNT is not a global negative-final-balance problem after the current cleanup.
- Remaining HNT issues are platform-local allocation/context problems across Binance and Pionex.
- Binance HNT residual is small and was introduced by the closed Blockpit source-chain reconstruction; it likely needs transfer/context or a small dust decision, not a global inventory fix.
- The Solana-wallet HNT gap is closed by the Solscan counterflow import for the 2025 Bitget withdrawal.
- The Bitget HNT gap is closed by the Blockpit-Bitget source-chain reconstruction before the April 2024 sells.

## Negative Plattformkonten

- `binance` final `-1.62738672` worst `-1.62738672` first `2023-03-17T08:25:50+00:00` tx `binance-source-chain-reconstruction:6026453`
- `pionex` final `-0.16629829` worst `-0.16876807` first `2022-09-09T04:17:39+00:00` tx `s_0:468:out:HNT`

## Plattform-Summaries

- `binance` events `311` net `-1.62738672` range `2021-02-06T21:28:37+00:00`..`2023-03-17T08:25:50+00:00`
- `bitget` events `26` net `1.53230555` range `2024-03-07T15:55:54+00:00`..`2025-04-04T17:12:55.009000+00:00`
- `helium_legacy` events `21914` net `850.22799358143114379127906` range `2021-05-12T09:13:16+00:00`..`2023-04-18T15:56:54+00:00`
- `helium_mining` events `4987` net `656.57616369` range `2021-12-01T00:00:00+00:00`..`2026-04-01T00:00:00+00:00`
- `pionex` events `204` net `-0.16629829` range `2021-12-25T16:25:25+00:00`..`2023-01-14T08:14:03+00:00`
- `solana_wallet` events `93` net `71.38257419` range `2023-04-20T17:56:12+00:00`..`2026-05-07T14:54:00+00:00`

## Naechste Aktion

- Nicht global HNT korrigieren; global ist HNT positiv.
- Solana-HNT und Bitget-HNT sind durch belegte Gegenfluesse geschlossen.
- Binance-HNT als kleine Restdifferenz aus der rekonstruierten Kette separat behandeln, wenn kein Transferbeleg gefunden wird.
- Pionex-HNT als Bot-/Dust-Rest zusammen mit dem Pionex-USDT-Opening entscheiden.
