# USDT 2022 Zero-Cost Dossier

Stand: 2026-05-10

## Ergebnis

- Status: `read_only_dossier`
- Job: `942afb62-85f5-4690-9b74-2e6195d5205f`
- Nullkosten-Zeilen: `3`
- Menge: `1569.34243684620000000000 USDT`
- Erloes: `1383.448602294939514000000000 EUR`
- Erster aktiver USDT-Bruch: `2022-01-05T15:36:46+00:00` after `-75.10462220620000000000` event `fe030531d67b4c88a2f56f81b84f438ee42b49096cc8b6a115b98e888071c449`
- Schlechtester aktiver USDT-Stand: `-1569.91028184620000000000` bei `2022-01-19T12:56:19+00:00`
- Finaler USDT-Stand: `1720.33575614902711250000`

## Betroffene Steuerzeilen

| Line | Zeit | Quelle | Menge | Erloes EUR | Balance vorher | Balance nach | TX |
|---:|---|---|---:|---:|---:|---:|---|
| 1679 | `2022-01-05T15:36:46+00:00` | `binance` `trade` `out` | 75.10462220620000000000 | 66.3526805805115140000000000 | 111.16537779380000000000 | -75.10462220620000000000 | `binance-txhist-jan2022:20220105T173646:2016:Transaction Spend:USDT` |
| 1709 | `2022-01-19T12:45:42+00:00` | `pionex` `trade` `out` | 168.84689687000000000000 | 148.8300972460615000000000000 | 236.04155809380000000000 | -243.95151907620000000000 | `s_10:67:out:USDT` |
| 2811 | `2022-01-19T12:56:19+00:00` | `pionex` `trade` `out` | 1325.39091777000000000000 | 1168.265824468366500000000000 | 1002.24353892380000000000 | -1569.91028184620000000000 | `s_11:68:out:USDT` |

## Interpretation

- Die 3 Zeilen sind steuerpflichtige USDT-Verwendungen im Jahr 2022 mit Cost Basis 0.
- Erster aktiver USDT-Bruch: 2022-01-05T15:36:46+00:00 after -75.10462220620000000000.
- Source-Verteilung: {'binance/trade/out': 1, 'pionex/trade/out': 2}.
- Lot-Source-Verteilung: {'empty_lot': 3}.
- Kein automatischer steuerwirksamer Import empfohlen, solange keine Primaerquelle die Anschaffungskette belegt.

## Kritische Ledger-Kontexte

### Line 1679

- Platform-Hinweis: `binance_2021_2022_acquisition_chain`
- Source Event: `fe030531d67b4c88a2f56f81b84f438ee42b49096cc8b6a115b98e888071c449`
- Lot Source Event: `empty_lot`

- `2022-01-05T08:39:37+00:00` `binance` / `fee` / `out` delta `-0.025039` before `3896.33217414510000000000` after `3896.30713514510000000000` tx `binance-txhist-jan2022:20220105T103937:1983:Transaction Fee:USDT`
- `2022-01-05T11:39:12+00:00` `pionex` / `trade` / `in` delta `133.56507760680000000000` before `3896.30713514510000000000` after `4029.87221275190000000000` tx `s_6:49:in:USDT`
- `2022-01-05T11:39:12+00:00` `pionex` / `fee` / `out` delta `-0.06678254` before `4029.87221275190000000000` after `4029.80543021190000000000` tx `s_6:49:fee:USDT`
- `2022-01-05T11:39:22+00:00` `pionex` / `trade` / `in` delta `28.67080298190000000000` before `4029.80543021190000000000` after `4058.47623319380000000000` tx `s_5:50:in:USDT`
- `2022-01-05T11:39:22+00:00` `pionex` / `fee` / `out` delta `-0.01433540` before `4058.47623319380000000000` after `4058.46189779380000000000` tx `s_5:50:fee:USDT`
- `2022-01-05T11:40:01+00:00` `pionex` / `trade` / `out` delta `-346.92882000000000000000` before `4058.46189779380000000000` after `3711.53307779380000000000` tx `s_7:51:out:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` delta `-664.950000` before `3711.53307779380000000000` after `3046.58307779380000000000` tx `binance-txhist-jan2022:20220105T173646:2008:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` delta `-30.151200` before `3046.58307779380000000000` after `3016.43187779380000000000` tx `binance-txhist-jan2022:20220105T173646:2004:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` delta `-667.317000` before `3016.43187779380000000000` after `2349.11487779380000000000` tx `binance-txhist-jan2022:20220105T173646:2015:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` delta `-999.633600` before `2349.11487779380000000000` after `1349.48127779380000000000` tx `binance-txhist-jan2022:20220105T173646:2007:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` delta `-841.383400` before `1349.48127779380000000000` after `508.09787779380000000000` tx `binance-txhist-jan2022:20220105T173646:2005:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` delta `-396.932500` before `508.09787779380000000000` after `111.16537779380000000000` tx `binance-txhist-jan2022:20220105T173646:2006:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` delta `-186.270000` before `111.16537779380000000000` after `-75.10462220620000000000` tx `binance-txhist-jan2022:20220105T173646:2016:Transaction Spend:USDT`
- `2022-01-05T23:58:17+00:00` `pionex` / `trade` / `in` delta `164.42666500000000000000` before `-75.10462220620000000000` after `89.32204279380000000000` tx `s_7:52:in:USDT`
- `2022-01-05T23:58:17+00:00` `pionex` / `fee` / `out` delta `-0.08221337` before `89.32204279380000000000` after `89.23982942380000000000` tx `s_7:52:fee:USDT`
- `2022-01-06T00:05:38+00:00` `pionex` / `trade` / `out` delta `-28.21883800000000000000` before `89.23982942380000000000` after `61.02099142380000000000` tx `s_7:53:out:USDT`
- `2022-01-06T21:09:31+00:00` `pionex` / `trade` / `in` delta `32.48038600000000000000` before `61.02099142380000000000` after `93.50137742380000000000` tx `s_7:54:in:USDT`
- `2022-01-06T21:09:31+00:00` `pionex` / `fee` / `out` delta `-0.01624022` before `93.50137742380000000000` after `93.48513720380000000000` tx `s_7:54:fee:USDT`
- `2022-01-07T00:09:25+00:00` `pionex` / `trade` / `in` delta `4.04297200000000000000` before `93.48513720380000000000` after `97.52810920380000000000` tx `s_7:55:in:USDT`
- `2022-01-07T00:09:25+00:00` `pionex` / `fee` / `out` delta `-0.00202149` before `97.52810920380000000000` after `97.52608771380000000000` tx `s_7:55:fee:USDT`
- `2022-01-12T12:55:37+00:00` `pionex` / `trade` / `out` delta `-36.71461200000000000000` before `97.52608771380000000000` after `60.81147571380000000000` tx `s_7:56:out:USDT`

### Line 1709

- Platform-Hinweis: `pionex_opening_or_bot_history`
- Source Event: `a20292c0e922503226ea223723d3863a9325cd51f5cf1bd53734dd0f387b2513`
- Lot Source Event: `empty_lot`

- `2022-01-13T10:57:57+00:00` `pionex` / `fee` / `out` delta `-0.00607813` before `77.35765448380000000000` after `77.35157635380000000000` tx `s_7:59:fee:USDT`
- `2022-01-18T10:30:41+00:00` `pionex` / `trade` / `in` delta `151.98727500000000000000` before `77.35157635380000000000` after `229.33885135380000000000` tx `s_7:60:in:USDT`
- `2022-01-18T10:30:41+00:00` `pionex` / `fee` / `out` delta `-0.07599364` before `229.33885135380000000000` after `229.26285771380000000000` tx `s_7:60:fee:USDT`
- `2022-01-18T10:32:14+00:00` `pionex` / `trade` / `out` delta `-106.76336094000000000000` before `229.26285771380000000000` after `122.49949677380000000000` tx `s_8:61:out:USDT`
- `2022-01-18T23:55:30+00:00` `pionex` / `trade` / `in` delta `107.14449546000000000000` before `122.49949677380000000000` after `229.64399223380000000000` tx `s_8:62:in:USDT`
- `2022-01-18T23:55:30+00:00` `pionex` / `fee` / `out` delta `-0.05357227` before `229.64399223380000000000` after `229.59041996380000000000` tx `s_8:62:fee:USDT`
- `2022-01-19T00:57:31+00:00` `pionex` / `trade` / `out` delta `-158.17733910000000000000` before `229.59041996380000000000` after `71.41308086380000000000` tx `s_8:63:out:USDT`
- `2022-01-19T11:22:49+00:00` `pionex` / `trade` / `in` delta `163.97883375000000000000` before `71.41308086380000000000` after `235.39191461380000000000` tx `s_8:64:in:USDT`
- `2022-01-19T11:22:49+00:00` `pionex` / `fee` / `out` delta `-0.08198937` before `235.39191461380000000000` after `235.30992524380000000000` tx `s_8:64:fee:USDT`
- `2022-01-19T11:34:54+00:00` `pionex` / `trade` / `out` delta `-119.67176847000000000000` before `235.30992524380000000000` after `115.63815677380000000000` tx `s_9:65:out:USDT`
- `2022-01-19T12:39:11+00:00` `pionex` / `trade` / `in` delta `120.46363312000000000000` before `115.63815677380000000000` after `236.10178989380000000000` tx `s_9:66:in:USDT`
- `2022-01-19T12:39:11+00:00` `pionex` / `fee` / `out` delta `-0.06023180` before `236.10178989380000000000` after `236.04155809380000000000` tx `s_9:66:fee:USDT`
- `2022-01-19T12:45:42+00:00` `pionex` / `trade` / `out` delta `-479.99307717000000000000` before `236.04155809380000000000` after `-243.95151907620000000000` tx `s_10:67:out:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` delta `475.864400` before `-243.95151907620000000000` after `231.91288092380000000000` tx `binance-txhist-jan2022:20220119T144735:2049:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` delta `12.285000` before `231.91288092380000000000` after `244.19788092380000000000` tx `binance-txhist-jan2022:20220119T144735:2051:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` delta `555.560000` before `244.19788092380000000000` after `799.75788092380000000000` tx `binance-txhist-jan2022:20220119T144735:2054:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` delta `203.733100` before `799.75788092380000000000` after `1003.49098092380000000000` tx `binance-txhist-jan2022:20220119T144735:2055:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` delta `-0.012285` before `1003.49098092380000000000` after `1003.47869592380000000000` tx `binance-txhist-jan2022:20220119T144735:2048:Transaction Fee:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` delta `-0.475864` before `1003.47869592380000000000` after `1003.00283192380000000000` tx `binance-txhist-jan2022:20220119T144735:2050:Transaction Fee:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` delta `-0.555560` before `1003.00283192380000000000` after `1002.44727192380000000000` tx `binance-txhist-jan2022:20220119T144735:2047:Transaction Fee:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` delta `-0.203733` before `1002.44727192380000000000` after `1002.24353892380000000000` tx `binance-txhist-jan2022:20220119T144735:2058:Transaction Fee:USDT`

### Line 2811

- Platform-Hinweis: `pionex_opening_or_bot_history`
- Source Event: `b5422e7c322b53d701869335a500c9b7e48334f50b6e8410978e247e608e0399`
- Lot Source Event: `empty_lot`

- `2022-01-19T12:39:11+00:00` `pionex` / `fee` / `out` delta `-0.06023180` before `236.10178989380000000000` after `236.04155809380000000000` tx `s_9:66:fee:USDT`
- `2022-01-19T12:45:42+00:00` `pionex` / `trade` / `out` delta `-479.99307717000000000000` before `236.04155809380000000000` after `-243.95151907620000000000` tx `s_10:67:out:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` delta `475.864400` before `-243.95151907620000000000` after `231.91288092380000000000` tx `binance-txhist-jan2022:20220119T144735:2049:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` delta `12.285000` before `231.91288092380000000000` after `244.19788092380000000000` tx `binance-txhist-jan2022:20220119T144735:2051:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` delta `555.560000` before `244.19788092380000000000` after `799.75788092380000000000` tx `binance-txhist-jan2022:20220119T144735:2054:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` delta `203.733100` before `799.75788092380000000000` after `1003.49098092380000000000` tx `binance-txhist-jan2022:20220119T144735:2055:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` delta `-0.012285` before `1003.49098092380000000000` after `1003.47869592380000000000` tx `binance-txhist-jan2022:20220119T144735:2048:Transaction Fee:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` delta `-0.475864` before `1003.47869592380000000000` after `1003.00283192380000000000` tx `binance-txhist-jan2022:20220119T144735:2050:Transaction Fee:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` delta `-0.555560` before `1003.00283192380000000000` after `1002.44727192380000000000` tx `binance-txhist-jan2022:20220119T144735:2047:Transaction Fee:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` delta `-0.203733` before `1002.44727192380000000000` after `1002.24353892380000000000` tx `binance-txhist-jan2022:20220119T144735:2058:Transaction Fee:USDT`
- `2022-01-19T12:50:48+00:00` `binance_api` / `withdrawal` / `out` delta `-1245.38419` before `1002.24353892380000000000` after `-243.14065107620000000000` tx `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`
- `2022-01-19T12:54:09+00:00` `pionex` / `deposit` / `in` delta `1245.38419000` before `-243.14065107620000000000` after `1002.24353892380000000000` tx `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`
- `2022-01-19T12:56:19+00:00` `pionex` / `trade` / `out` delta `-2572.15382077000000000000` before `1002.24353892380000000000` after `-1569.91028184620000000000` tx `s_11:68:out:USDT`
- `2022-01-19T23:28:01+00:00` `pionex` / `trade` / `in` delta `348.69293954000000000000` before `-1569.91028184620000000000` after `-1221.21734230620000000000` tx `s_10:69:in:USDT`
- `2022-01-19T23:28:01+00:00` `pionex` / `fee` / `out` delta `-0.17434645` before `-1221.21734230620000000000` after `-1221.39168875620000000000` tx `s_10:69:fee:USDT`
- `2022-01-19T23:50:25+00:00` `pionex` / `trade` / `in` delta `1402.62272436000000000000` before `-1221.39168875620000000000` after `181.23103560380000000000` tx `s_11:70:in:USDT`
- `2022-01-19T23:50:25+00:00` `pionex` / `fee` / `out` delta `-0.70131096` before `181.23103560380000000000` after `180.52972464380000000000` tx `s_11:70:fee:USDT`
- `2022-01-20T00:06:58+00:00` `pionex` / `trade` / `out` delta `-513.25472484000000000000` before `180.52972464380000000000` after `-332.72500019620000000000` tx `s_11:71:out:USDT`
- `2022-01-20T00:09:50+00:00` `pionex` / `trade` / `out` delta `-91.64680062000000000000` before `-332.72500019620000000000` after `-424.37180081620000000000` tx `s_10:72:out:USDT`
- `2022-01-20T17:15:51+00:00` `pionex` / `trade` / `in` delta `512.27377344000000000000` before `-424.37180081620000000000` after `87.90197262380000000000` tx `s_11:73:in:USDT`
- `2022-01-20T17:15:51+00:00` `pionex` / `fee` / `out` delta `-0.25613710` before `87.90197262380000000000` after `87.64583552380000000000` tx `s_11:73:fee:USDT`

## Naechste Belegziele

- Primaerquelle fuer USDT-Zufluss/Erwerb vor dem ersten Bruch pruefen.
- Wenn es ein Swap ist: Gegenseite, Transferkette und Bewertungsanker pruefen.
- Wenn es ein Plattform-/Wallet-Kontext ist: Deposit-/Withdrawal-/Bridge-Historie vor dem Bruch pruefen.
- Ohne Beleg keine steuerwirksame Zuflussfiktion importieren.

JSON: `var/usdt_2022_zero_cost_dossier_2026-05-10.json`
