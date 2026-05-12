# USDC 2024 Zero-Cost Dossier

Stand: 2026-05-10

## Ergebnis

- Status: `read_only_dossier`
- Job: `b7531c5c-6f24-45f2-9499-8e963c62de62`
- Nullkosten-Zeilen: `1`
- Menge: `0.000002 USDC`
- Erloes: `0.000001893578471013762814449849252 EUR`
- Erster aktiver USDC-Bruch: `2024-12-01T13:35:14+00:00` after `-0.000002` event `212e7070015ff8cb1f9a0593afdfe7f7352a460a6bf7f990184d4c2291383e7f`
- Schlechtester aktiver USDC-Stand: `-0.000002` bei `2024-12-01T13:35:14+00:00`
- Finaler USDC-Stand: `0.18978533`

## Betroffene Steuerzeilen

| Line | Zeit | Quelle | Menge | Erloes EUR | Balance vorher | Balance nach | TX |
|---:|---|---|---:|---:|---:|---:|---|
| 2325 | `2024-12-01T13:35:14+00:00` | `solana_rpc` `swap_out_aggregated` `out` | 0.000002 | 0.000001893578471013762814449849252 | 148.066733 | -0.000002 | `5TYVduwDC9aSasNRuigNNwd1xLJAVoXPauMziEDYe2rMENtwnqyvq8wrM6LXvUz4gZyqKcZgb2SUEN1qeJFbaiA` |

## Interpretation

- Die 1 Zeilen sind steuerpflichtige USDC-Verwendungen im Jahr 2024 mit Cost Basis 0.
- Erster aktiver USDC-Bruch: 2024-12-01T13:35:14+00:00 after -0.000002.
- Source-Verteilung: {'solana_rpc/swap_out_aggregated/out': 1}.
- Lot-Source-Verteilung: {'empty_lot': 1}.
- Kein automatischer steuerwirksamer Import empfohlen, solange keine Primaerquelle die Anschaffungskette belegt.

## Kritische Ledger-Kontexte

### Line 2325

- Platform-Hinweis: `global_acquisition_chain`
- Source Event: `212e7070015ff8cb1f9a0593afdfe7f7352a460a6bf7f990184d4c2291383e7f`
- Lot Source Event: `empty_lot`

- `2024-11-25T19:03:59+00:00` `solana_rpc` / `token_transfer` / `in` delta `9831.198542` before `0` after `9831.198542` tx `k4rarsS3E8dHgMv6H8fe9dm1S9M4yLDSY7VGpAsZFotDoAuDL5vUperbVJuA6gGZiDntfhMKhZW2zwwNG2sYLVk`
- `2024-11-26T21:01:42+00:00` `solana_rpc` / `token_transfer` / `in` delta `198.883427` before `9831.198542` after `10030.081969` tx `4VhMdLZ1M6m2Nju4vWMiuy772uYRvVv66Wiyu9ruvBfw9JssWNbD4Y8G9fiJza9NaL27RWiu2TzgcskNQdWnw5Ra`
- `2024-11-27T10:47:47+00:00` `solana_rpc` / `swap_out_aggregated` / `out` delta `-10030.038914` before `10030.081969` after `0.043055` tx `2xqB5wHqSYi4BLZ2fQNVFQeMXWCFMJXQHNYZvoYbLXayZh9A3ziv8zoRjSzse8112PV3GHVEiwTQGiqYiEdPsbDT`
- `2024-11-28T09:45:47+00:00` `solana_rpc` / `token_transfer` / `in` delta `457.307511` before `0.043055` after `457.350566` tx `YwnFmegtepjEVfXUp3brtneNL4qeutniA6vR3L5ep29RDmEx1T1yGvZUwzaU6AWqMUxK8BayheSAHkrwxjAJ521`
- `2024-11-28T09:47:00+00:00` `solana_rpc` / `token_transfer` / `out` delta `-440.000000` before `457.350566` after `17.350566` tx `5URaNab93fFuuLUTDoKuJNzu9wvjTftEPLGaeL7JsrZ1cUpbTrJA2GbyQo4hBfHrkoDpfZ7uyGgydcvj3NfaXM36`
- `2024-11-28T17:40:07+00:00` `solana_rpc` / `token_transfer` / `out` delta `-10.000000` before `17.350566` after `7.350566` tx `2WcTARE13qaVyftmP6M27fuK9NXEsP16Rx2j136EN4VfftmXfRffEfCmgH6P1adRiJ7bMdwtV1CAWbzj6RiZcZc1`
- `2024-11-30T05:42:55+00:00` `solana_rpc` / `token_transfer` / `in` delta `292.951914` before `7.350566` after `300.302480` tx `PSaNrRj3m5Y7bcTL6UD66vyVG181xKxjZ64kudbmBSuVVSzSVAhY3emL3YnVCWdDteoLyQs9Y3Ur8y9cA5vkz8f`
- `2024-12-01T13:03:29+00:00` `solana_rpc` / `swap_in_aggregated` / `in` delta `238.026920` before `300.302480` after `538.329400` tx `5NZMTSTimGXaCQ4knt8ZQErDSkTFpWLVbu9p346iAMnTu8BehPZFsd2tY6HyuVzGkLTJ6fK5cv71H9ZL6W3a5kZ5`
- `2024-12-01T13:11:43+00:00` `solana_rpc` / `token_transfer` / `out` delta `-500.000000` before `538.329400` after `38.329400` tx `55kPeMxERyWRUSX6gDUqTH5AY4CnbBDgLyUr2219kbcbSDqggU2VcZwJexJBtTkNDLWFR35nspTLchwNfQk7LYy3`
- `2024-12-01T13:12:52.190000+00:00` `bitget_tax_api` / `deposit` / `in` delta `500` before `38.329400` after `538.329400` tx `1247104369882030086`
- `2024-12-01T13:28:04.784000+00:00` `bitget_tax_api` / `trade` / `out` delta `-500` before `538.329400` after `38.329400` tx `1247108196190380043`
- `2024-12-01T13:34:26+00:00` `solana_rpc` / `token_transfer` / `in` delta `109.737333` before `38.329400` after `148.066733` tx `5WNWYh6akd5LYHGG36yXjEqdtsFX2934k2H3MjLLGLQ8wwUogVG5BDNtcBhGCXHySbFd4cWqzn1RJ7s2Lgru3fFT`
- `2024-12-01T13:35:14+00:00` `solana_rpc` / `swap_out_aggregated` / `out` delta `-148.066735` before `148.066733` after `-0.000002` tx `5TYVduwDC9aSasNRuigNNwd1xLJAVoXPauMziEDYe2rMENtwnqyvq8wrM6LXvUz4gZyqKcZgb2SUEN1qeJFbaiA`
- `2024-12-01T20:10:03+00:00` `solana_rpc` / `swap_in_aggregated` / `in` delta `9520.142066` before `-0.000002` after `9520.142064` tx `3W212vZDiHGzZKaJFQ7BQKgYCQTry1b2XtHh1fBwQbXdkdUPhuKPCgLzbMuzwLLXYNgedoCSiqCkkfG9TsBfooKm`
- `2024-12-01T21:34:35+00:00` `solana_rpc` / `swap_out_aggregated` / `out` delta `-9520.142065` before `9520.142064` after `-0.000001` tx `3b7Qt3PQPWXJnjhQYc9Ujr8wjmXcVcw5ZYhjTEWJkg57hzWLrKFf9M8AnXpCzdtUa31rtupxj1ZGziE73YGMpecn`
- `2024-12-02T08:20:52+00:00` `solana_rpc` / `swap_in_aggregated` / `in` delta `8991.983983` before `-0.000001` after `8991.983982` tx `3jwK3nEddhHhVNWW92MhHbaKGeuvHhWx95NurnprwW4a8KMdk2SLe8jsLRSvd2Knj1QV7tyZbj6fcFfisMpXFcjg`
- `2024-12-02T10:59:32+00:00` `solana_rpc` / `token_transfer` / `out` delta `-500.000000` before `8991.983982` after `8491.983982` tx `2DeeB1MEYtiPR7wMwtMrKQ7pamwa7krpwvsXmKi7hiZVSDYuyN9kYVcJ2QuEWx9h1omw159XwZhK2Edw9HJDaBTo`
- `2024-12-03T04:33:09+00:00` `solana_rpc` / `token_transfer` / `out` delta `-400.000000` before `8491.983982` after `8091.983982` tx `5RCBhNUWxQU1ygv8AvKHYUFYHZpeQFq8DXcWwKxmDgPTYWgrCfbDuXw6omqKpc7uxcF1vKUupRZ6xn8Hb6QsL44p`
- `2024-12-03T21:27:37+00:00` `solana_rpc` / `swap_out_aggregated` / `out` delta `-8091.983984` before `8091.983982` after `-0.000002` tx `brZs2zU6cEhxYuwWvi6HK81tzRQmBzaCGFP8hZafYPsYyUZ46d45218TEcdTP5t8JJLKzmz2jbxR9vpo66XU9LT`
- `2024-12-03T21:58:37+00:00` `solana_rpc` / `swap_in_aggregated` / `in` delta `7960.190049` before `-0.000002` after `7960.190047` tx `2hj9tdCPrGZa4Z8ASydpBQxTKwL3BCHUpuefTQyBvcu3wwdPqkHFCsVR1EdWgSCB7YZgzgGMtVM5f17L6TNGQcVc`
- `2024-12-03T22:02:26+00:00` `solana_rpc` / `swap_out_aggregated` / `out` delta `-1.255565` before `7960.190047` after `7958.934482` tx `5fy14gvcxaA3y8g9i8CYksVbV1FZSccNx7wzFYZqa17tkeToSyyYyVtSdnDh3KbqDz49nbrQp65eipA6WypUwrKE`

## Naechste Belegziele

- Primaerquelle fuer USDC-Zufluss/Erwerb vor dem ersten Bruch pruefen.
- Wenn es ein Swap ist: Gegenseite, Transferkette und Bewertungsanker pruefen.
- Wenn es ein Plattform-/Wallet-Kontext ist: Deposit-/Withdrawal-/Bridge-Historie vor dem Bruch pruefen.
- Ohne Beleg keine steuerwirksame Zuflussfiktion importieren.

JSON: `var/usdc_2024_zero_cost_dossier_2026-05-10.json`
