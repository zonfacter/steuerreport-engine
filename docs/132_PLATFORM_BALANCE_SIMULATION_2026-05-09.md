# Platform Balance Simulation - 2026-05-09

## Ergebnis

- Ledger-Zeilen: `37868`
- Plattform/Asset-Konten: `77`
- Konten mit negativem Verlauf oder Endsaldo: `5`
- Dust-Grenze: `0.000001`

## Erste Bruchstellen

- `2021-12-28T00:49:12+00:00` `pionex` `USDT` delta `-16.02000000000000000000` saldo `-13.53043343` quelle `pionex` tx `s_3:13:out:USDT`
- `2022-09-09T04:17:39+00:00` `pionex` `HNT` delta `-74.35600000000000000000` saldo `-0.16876807` quelle `pionex` tx `s_0:468:out:HNT`
- `2023-03-17T08:25:50+00:00` `binance` `HNT` delta `-304.49` saldo `-1.62738672` quelle `binance_2022_2023_blockpit_source_chain_reconstruction` tx `binance-source-chain-reconstruction:6026453`
- `2024-12-01T13:35:14+00:00` `solana_wallet` `USDC` delta `-148.066735` saldo `-0.000002` quelle `solana_rpc` tx `5TYVduwDC9aSasNRuigNNwd1xLJAVoXPauMziEDYe2rMENtwnqyvq8wrM6LXvUz4gZyqKcZgb2SUEN1qeJFbaiA`
- `2024-12-04T18:30:59+00:00` `solana_wallet` `USDT` delta `-2764.708247` saldo `-0.000002` quelle `solana_rpc` tx `XWx5SFmBAFGyHBYFRq8qrfyoznbNsv5T4NJcnXrFN28s94teAGyv7k2t7bCJ4T8LBbpFPM5vqrT3CfvrMnXMTfW`

## Bewertung

- Diese Simulation trennt Plattformen bewusst. Ein negativer Plattform-Saldo bedeutet nicht automatisch fehlendes Gesamtportfolio, sondern markiert fehlende Transfers, fehlende CEX-Historie oder falsche Quellenzuordnung.
- Die Ausgabe ist die Arbeitsbasis fuer Pionex/Binance/Bitget/Solana/Helium-Abgleich und KI-Hypothesen.
