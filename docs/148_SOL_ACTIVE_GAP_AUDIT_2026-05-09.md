# SOL Active Gap Audit - 2026-05-09

## Ergebnis

- Aktiver globaler SOL-Endsaldo: `10.52514844000000000000`
- Erster SOL-Bruch: `None` `None` `None` delta `None` after `None` tx `None`
- Schlimmster SOL-Stand: `0.001` am `2021-04-28T05:18:42+00:00`
- Gematchte Binance -> Solana-Wallet SOL-Transfers: `3`

## Bewertung

- Die sichtbaren Binance-SOL-Withdrawals sind per gleicher TXID mit Solana-Wallet-Inflows gematcht.
- Nach der Binance-SOL-2023-Rekonstruktion zeigt SOL keinen aktiven Negativbestand mehr.
- Der Gegenwert der SOL-Kaeufe wurde korrekt als BTC-Abgang gebucht; dadurch ist jetzt BTC die naechste aktive Quellenluecke.

## Plattform-Breaks


## Gematchte Binance-Solana-Transfers

- TX `4eU6ZGkd7KG17ydAEzJegCNwB2twWu5Dp11EF3PU4K4AsjdhbwvDMibrKNJF1gFc2QEkWF4MqwiR4jBCbGvmgm7`
  - `2023-05-08T04:43:46+00:00` `binance` `-1.192` `withdrawal` `binance_api`
  - `2023-05-08T04:44:07+00:00` `solana_wallet` `1.192` `sol_transfer` `solana_rpc`
- TX `2kidZgDeFCoFL7mDSrYtKcQ63efh11wgpcFXfxumqcDo7rN9zV3Yz9JhBEjmmaQp9Wbr1fEc71Bg7dQvPs59wXuV`
  - `2023-06-10T16:49:21+00:00` `binance` `-54.10011` `withdrawal` `binance_api`
  - `2023-06-10T16:49:46+00:00` `solana_wallet` `54.10011` `sol_transfer` `solana_rpc`
- TX `3RDTPjSAE8R7b9EmgDnZ2GzfCVgzuxA8Rqmbae51FXfNZ6vymj31y5jn8fn7ZYpgMrMBNUCnZGacBgELSYCDjdsr`
  - `2024-11-24T07:18:58+00:00` `binance` `-1.12889582` `withdrawal` `binance_api`
  - `2024-11-24T07:19:30+00:00` `solana_wallet` `1.12889582` `sol_transfer` `solana_rpc`

## Naechster Schritt

- Falls SOL positiv bleibt: BTC-Deckung der rekonstruierten SOL-Kaeufe kontrolliert weiterverfolgen.
