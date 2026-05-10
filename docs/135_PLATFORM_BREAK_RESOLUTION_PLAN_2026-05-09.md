# Platform Break Resolution Plan - 2026-05-09

## Ergebnis

- Bruchstellen: `5`
- Status: `{'opening_balance_or_bot_history_needed': 1, 'nearby_transfer_context': 1, 'dust_or_rounding_review': 3}`
- Prioritaeten: `{'high': 1, 'medium': 1, 'low': 3}`

## Arbeitsliste

- `high` `opening_balance_or_bot_history_needed` `pionex` `USDT` final `0.8913798065261125` worst `-1643.2312211162` direct `0` nearby `0` first `2021-12-28T00:49:12+00:00`
  - Aktion: Pionex Start-/Bot-Historie oder Opening-Balance-Beleg beschaffen; ohne Beleg nicht finalisieren.
- `medium` `nearby_transfer_context` `binance` `HNT` final `-1.62738672` worst `-1.62738672` direct `0` nearby `10` first `2023-03-17T08:25:50+00:00`
  - Aktion: Nahe Transfer-Kandidaten pruefen; wahrscheinlich Plattform-/Fee- oder Doppelzeilen-Effekt.
- `low` `dust_or_rounding_review` `pionex` `HNT` final `-0.16629829` worst `-0.16876807` direct `0` nearby `0` first `2022-09-09T04:17:39+00:00`
  - Aktion: Als Dust/Rundung markieren, wenn TX-Beleg und finaler Kontostand plausibel sind.
- `low` `dust_or_rounding_review` `solana_wallet` `USDC` final `0.000988` worst `-0.000002` direct `0` nearby `2` first `2024-12-01T13:35:14+00:00`
  - Aktion: Als Dust/Rundung markieren, wenn TX-Beleg und finaler Kontostand plausibel sind.
- `low` `dust_or_rounding_review` `solana_wallet` `USDT` final `-0.000002` worst `-0.000003` direct `0` nearby `6` first `2024-12-04T18:30:59+00:00`
  - Aktion: Als Dust/Rundung markieren, wenn TX-Beleg und finaler Kontostand plausibel sind.

## Naechster Ablauf

1. High ohne Kandidat zuerst klaeren: Pionex USDT Opening/Bot-Historie, Bitget BTC 2024, Solana JUP Onchain-Gegenfluss.
2. Medium-Kontext pruefen: Binance SOL, Bitget HNT, Solana HNT.
3. Low/Dust erst nach den grossen Luecken final markieren.
