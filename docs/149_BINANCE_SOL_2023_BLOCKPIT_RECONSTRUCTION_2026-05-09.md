# Binance SOL 2023 Blockpit Reconstruction - 2026-05-09

## Ergebnis

- Modus: `execute`
- Importierte Events: `4`
- Duplikate: `0`
- Bestehende Rekonstruktionszeilen: `0`

## Rekonstruktionszeilen

- `2023-05-04T04:24:52+00:00` `buy` `1.2 SOL` gegen `0.00092028 BTC` fee `0.00006138 BNB` reference `ef04828f55b9b59f38e855ab46522200d066bc034c95f8233ff474bbac18ed8a`
- `2023-06-10T16:45:04+00:00` `buy` `0.36 SOL` gegen `0.00020725 BTC` fee `0.00001692 BNB` reference `309d4bdad0c18c5dfa74a3160f9e1ba61b0ffe77f7e4d5d3967ee3f870937999`
- `2023-06-10T16:45:04+00:00` `buy` `21.89 SOL` gegen `0.01260207 BTC` fee `0.02189 SOL` reference `4a82efdc8a4bf041a13a8333d258f6123a8db6e1d06f46c3ba0acae2f5f83afd`
- `2023-06-10T16:45:04+00:00` `buy` `31.88 SOL` gegen `0.01835331 BTC` fee `0.00149915 BNB` reference `92b0168c781ebabe4a5ec6923e47cd32260e4056583c053081ac77b04f6b0ff4`

## Bewertung

- Active Binance SOL inventory turns negative before the 2023-05-08 and 2023-06-10 withdrawals.
- Blockpit contains Binance API reference spot buys immediately before those withdrawals.
- Only four SOL buy rows are imported as narrow reconstruction evidence; matching Blockpit withdrawal rows are not imported because Binance API withdrawals and Solana wallet counterflows already exist as active primary rows.
