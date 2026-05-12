# Chronologische Bestandsbruch-Analyse

Generiert: `2026-05-09T15:26:21.935214+00:00`
JSON: `var/chronological_balance_break_audit_after_solana_blockpit_reference_exclusions_2026-05-09.json`

## Überblick

- Bewegungen: `47045`
- Assets: `214`
- Assets mit negativem Endbestand: `0`

## Asset-Befunde

### PYTH

- Endbestand Modell: `88044724`
- Events: `95`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2024-01-01T22:09:50+00:00`

Jahres-Netto:
- `2024`: `88000006`
- `2025`: `44718`

Top Quellen-Netto:
- `blockpit` / `deposit` / `in`: `88000006`
- `blockpit` / `auto-balancing in` / `in`: `44718`

### CWIF

- Endbestand Modell: `11310642.83`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `384000` am `2024-03-30T17:25:05+00:00`

Jahres-Netto:
- `2024`: `11310642.83`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `10926642.83`
- `solana_rpc` / `token_transfer` / `in`: `384000`

### BTTC

- Endbestand Modell: `4209810.9`
- Events: `1217`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `29` am `2023-04-01T01:03:23+00:00`

Jahres-Netto:
- `2023`: `2689385.0`
- `2024`: `1520425.9`

Top Quellen-Netto:
- `binance_api` / `asset_dividend` / `in`: `4209810.9`

### CBDC

- Endbestand Modell: `4202343.53`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `4202343.53` am `2024-03-11T22:04:53+00:00`

Jahres-Netto:
- `2024`: `4202343.53`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `18902619.55`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-14700276.02`

### IOT

- Endbestand Modell: `2897413.9187490`
- Events: `2746`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `3421.905036` am `2023-04-20T00:00:00+00:00`

Jahres-Netto:
- `2023`: `1922990.4422270`
- `2024`: `561313.925059`
- `2025`: `427523.655013`
- `2026`: `-14414.10355`

Top Quellen-Netto:
- `solana_rpc` / `swap_out_aggregated` / `out`: `-11393200.321693`
- `solana_rpc` / `swap_in_aggregated` / `in`: `8779057.673155`
- `solana_rpc` / `token_transfer` / `in`: `4725849.956961`
- `solana_rpc` / `token_transfer` / `out`: `-2111707.308423`
- `heliumgeek` / `mining_reward` / `in`: `1707546.095357`
- `heliumtracker` / `mining_reward` / `in`: `920501.267322`
- `blockpit` / `auto-balancing in` / `in`: `339834.071782`
- `heliumtracker` / `mining_commission` / `out`: `-70467.5157120`

### SOL

- Endbestand Modell: `962998.24415816704400000000`
- Events: `3863`
- Erster Negativbestand: `2023-05-08T04:43:46+00:00` nach `834dd4b04416ebcbde6d4b5731d23466566e3001779d00222b40cb7654a5f754`
- Auslösend: `blockpit` / `withdrawal` / `out` / `-1.192`
- Schlimmster Stand: `-113.655084503` am `2024-03-12T17:25:45+00:00`

Jahres-Netto:
- `2021`: `0.001`
- `2023`: `7.461172274`
- `2024`: `962907.81190232500000000000`
- `2025`: `81.433369451044`
- `2026`: `1.536714117`

Top Quellen-Netto:
- `jupiter_perps` / `derivative open` / `open`: `481585.80`
- `jupiter_perps` / `derivative close` / `close`: `481585.79`
- `solana_rpc` / `sol_transfer` / `in`: `498.696819928`
- `solana_rpc` / `sol_transfer` / `out`: `-498.298336418`
- `blockpit` / `withdrawal` / `out`: `-397.890049214`
- `blockpit` / `trade` / `in`: `274.345172397`
- `blockpit` / `trade` / `out`: `-218.622905696`
- `blockpit` / `deposit` / `in`: `181.840409606`
- `binance_api` / `trade` / `buy_base`: `72.94900000`
- `blockpit` / `auto-balancing in` / `in`: `62.851376394`

### PEPE

- Endbestand Modell: `345988.35`
- Events: `67`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `2.73` am `2024-03-09T00:00:00+00:00`

Jahres-Netto:
- `2024`: `39456.36`
- `2025`: `306531.99`

Top Quellen-Netto:
- `blockpit` / `trade` / `out`: `-8912775`
- `blockpit` / `trade` / `in`: `8882016`
- `binance_api` / `asset_dividend` / `in`: `141633.43`
- `blockpit` / `bounty` / `in`: `102177.33`
- `binance_api` / `interest` / `in`: `102177.33`
- `blockpit` / `interest` / `in`: `39641.28`
- `blockpit` / `fee` / `out`: `-8882.02`

### BTC

- Endbestand Modell: `234297.24417954800000000100`
- Events: `93`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.00000277` am `2021-02-23T10:54:47+00:00`

Jahres-Netto:
- `2021`: `0.000035310`
- `2022`: `0.00000213`
- `2023`: `0.02098780000000000000`
- `2024`: `234297.21518430800000000100`
- `2025`: `0.00520000`
- `2026`: `0.00277`

Top Quellen-Netto:
- `jupiter_perps` / `derivative open` / `open`: `117148.61`
- `jupiter_perps` / `derivative close` / `close`: `117148.61`
- `binance` / `trade` / `in`: `0.06605408`
- `binance` / `trade` / `out`: `-0.06601751`
- `blockpit` / `trade` / `out`: `-0.043994379999999999`
- `blockpit` / `trade` / `in`: `0.03431573`
- `blockpit` / `deposit` / `in`: `0.015061274`
- `binance` / `deposit` / `in`: `0.01036997`
- `binance_api` / `deposit` / `in`: `0.01036997`
- `bitget_tax_api` / `trade` / `out`: `-0.004570`

### JUP

- Endbestand Modell: `76530.50784620999993000000`
- Events: `1361`
- Erster Negativbestand: `2024-03-12T04:47:59+00:00` nach `d169196f8933614907db0944a1ceae9cb6539bce569d4a62265102a63c2f2210`
- Auslösend: `pionex` / `fee` / `out` / `-0.01085231`
- Schlimmster Stand: `-0.01085231` am `2024-03-12T04:47:59+00:00`

Jahres-Netto:
- `2024`: `8427.77525701999993000000`
- `2025`: `68050.10715258`
- `2026`: `52.62543661`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `79451.784276`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-66713.161665`
- `blockpit` / `trade` / `in`: `59827.73028976`
- `blockpit` / `trade` / `out`: `-51621.58811042000007`
- `binance_api` / `trade` / `sell_base`: `-49464.60000000`
- `binance_api` / `trade` / `buy_base`: `42877.80000000`
- `blockpit` / `deposit` / `in`: `34237.472708`
- `solana_rpc` / `token_transfer` / `out`: `-30625.570394`
- `binance` / `deposit` / `in`: `23175.356052`
- `binance_api` / `deposit` / `in`: `23175.356052`

### WIN

- Endbestand Modell: `28292.30730362`
- Events: `73`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `14143` am `2021-05-05T04:59:31+00:00`

Jahres-Netto:
- `2021`: `14143`
- `2023`: `0.00E-6`
- `2024`: `14149.30730362`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `56570`
- `binance` / `trade` / `out`: `-42427`
- `blockpit` / `auto-balancing in` / `in`: `28298.61460724`
- `blockpit` / `trade` / `out`: `-14156.61280211`
- `blockpit` / `interest` / `in`: `7.30549849`

### HNT

- Endbestand Modell: `4299.70041335143114379127906`
- Events: `27646`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.000` am `2021-02-09T18:45:43+00:00`

Jahres-Netto:
- `2021`: `2409.56241081362897023903392`
- `2022`: `1280.49718020921237215284314`
- `2023`: `140.607037860000001399402`
- `2024`: `-398.86690628`
- `2025`: `848.6716495585898`
- `2026`: `19.22904119`

Top Quellen-Netto:
- `solana_rpc` / `swap_out_aggregated` / `out`: `-4650.43703630`
- `binance` / `trade` / `out`: `-3456.346000`
- `binance` / `trade` / `in`: `3046.956000`
- `solana_rpc` / `swap_in_aggregated` / `in`: `2980.04789129`
- `blockpit` / `deposit` / `in`: `2767.0916580514102`
- `pionex` / `trade` / `in`: `2310.29384864000000000000`
- `pionex` / `trade` / `out`: `-2309.30500000000000000000`
- `blockpit` / `withdrawal` / `out`: `-1896.8832552`
- `helium_legacy_cointracking` / `legacy_transfer` / `out`: `-1570.849923437360775624`
- `binance` / `deposit` / `in`: `1424.96965874`

### DOGE

- Endbestand Modell: `3582.18045070`
- Events: `121`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `3` am `2021-02-17T18:13:26+00:00`

Jahres-Netto:
- `2021`: `22.25150592`
- `2022`: `1554.203`
- `2023`: `-1557.5355282`
- `2024`: `3.0647641`
- `2025`: `2360.19670888`
- `2026`: `1200`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `24683.6`
- `binance` / `trade` / `out`: `-24662.2`
- `blockpit` / `trade` / `in`: `9903`
- `blockpit` / `trade` / `out`: `-7517.2677641`
- `binance_api` / `trade` / `buy_base`: `5906.00000000`
- `binance_api` / `trade` / `sell_base`: `-4720.00000000`
- `blockpit` / `fee` / `out`: `-8.703`
- `binance_api` / `trade` / `fee`: `-5.90600000`
- `blockpit` / `auto-balancing in` / `in`: `3.0647641`
- `binance_account_statement` / `interest` / `in`: `0.85150592`

### USDT

- Endbestand Modell: `2678.12859245396508054000`
- Events: `4921`
- Erster Negativbestand: `2022-01-19T12:50:48+00:00` nach `3450aa41e7b74c69acf27e9104f44cb956c9847870d864a24e988ff3a9b446e8`
- Auslösend: `binance_api` / `withdrawal` / `out` / `-1245.38419`
- Schlimmster Stand: `-1571.08462829620000200000` am `2022-01-19T23:28:01+00:00`

Jahres-Netto:
- `2021`: `1434.47897786000000000000`
- `2022`: `-1347.91636536536000200000`
- `2023`: `-14.27771110170000000000`
- `2024`: `3807.64790545790408254000`
- `2025`: `-1201.8042143968790`

Top Quellen-Netto:
- `blockpit` / `trade` / `in`: `81548.85066494999997`
- `blockpit` / `trade` / `out`: `-77641.5829141799997`
- `binance_api` / `trade` / `sell_quote`: `75304.76031000`
- `binance_api` / `trade` / `buy_quote`: `-70220.53397000`
- `binance` / `trade` / `in`: `54321.88957400`
- `binance` / `trade` / `out`: `-52550.28606327`
- `solana_rpc` / `token_transfer` / `out`: `-34733.843023`
- `solana_rpc` / `swap_in_aggregated` / `in`: `31653.240947`
- `pionex` / `trade` / `out`: `-25056.73396394677700000000`
- `solana_rpc` / `token_transfer` / `in`: `23866.833602`

### BTTOLD

- Endbestand Modell: `2497.5`
- Events: `3`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.0` am `2021-04-28T05:14:15+00:00`

Jahres-Netto:
- `2021`: `0.0`
- `2025`: `2497.5`

Top Quellen-Netto:
- `blockpit` / `auto-balancing in` / `in`: `4995.0`
- `blockpit` / `trade` / `out`: `-2497.5`

### BTT

- Endbestand Modell: `1989.000000000`
- Events: `1436`
- Erster Negativbestand: `2023-02-02T05:13:21+00:00` nach `261faa59ec34e49783f860bc90bad24a83e747deddc362986bebe384ead6a342`
- Auslösend: `blockpit` / `fee` / `out` / `-45945.9`
- Schlimmster Stand: `-43957.4` am `2023-02-02T05:13:21+00:00`

Jahres-Netto:
- `2021`: `1988.5`
- `2023`: `64409493.3`
- `2024`: `-56933727.000000002`
- `2025`: `-7475765.799999998`

Top Quellen-Netto:
- `blockpit` / `trade` / `out`: `-192919979`
- `blockpit` / `trade` / `in`: `181314207`
- `blockpit` / `auto-balancing in` / `in`: `14951532.099999998`
- `blockpit` / `auto-balancing out` / `out`: `-7475765.799999998`
- `blockpit` / `interest` / `in`: `4311320.4`
- `blockpit` / `fee` / `out`: `-181314.2`
- `binance` / `trade` / `in`: `129068`
- `binance` / `trade` / `out`: `-124582`
- `binance_api` / `dust_convert_out` / `out`: `-2497.5`

### EUR

- Endbestand Modell: `1572.92627741`
- Events: `216`
- Erster Negativbestand: `2021-02-06T21:18:02+00:00` nach `045981a004a46c697c23e7518be8d8b4dd1c0a810d3d399bc7d91ccd95a34a43`
- Auslösend: `blockpit` / `trade` / `out` / `-98`
- Schlimmster Stand: `-6950.40774346` am `2023-05-02T04:13:23+00:00`

Jahres-Netto:
- `2021`: `-6350.3887714`
- `2022`: `-100`
- `2023`: `-500.01897206`
- `2024`: `8592.71124993`
- `2025`: `-569.94774696`
- `2026`: `500.5705179`

Top Quellen-Netto:
- `blockpit` / `withdrawal` / `out`: `-10003.98`
- `binance` / `trade` / `in`: `9612.5471437`
- `blockpit` / `auto-balancing in` / `in`: `8572.71124993`
- `binance` / `fiat_withdrawal` / `out`: `-7035.49`
- `blockpit` / `deposit` / `in`: `6065`
- `blockpit` / `trade` / `out`: `-5084.08460551`
- `bitget_tax_api` / `fiat_recharge_in` / `in`: `4010`
- `bitget_tax_api` / `fiat_balance_user_out` / `out`: `-3000.14`
- `binance` / `trade` / `out`: `-2961.3823873`
- `binance` / `fiat_deposit` / `in`: `2426.2`

### ADA

- Endbestand Modell: `1219.962045690`
- Events: `1640`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.61852377` am `2021-04-05T10:12:32+00:00`

Jahres-Netto:
- `2021`: `10.66103729`
- `2022`: `0.00013995`
- `2023`: `0.642558540`
- `2024`: `11.50139690`
- `2025`: `797.15691301`
- `2026`: `400`

Top Quellen-Netto:
- `blockpit` / `trade` / `in`: `804.8`
- `binance_api` / `trade` / `buy_base`: `404.80000000`
- `binance` / `trade` / `in`: `76.6`
- `binance` / `trade` / `out`: `-66`
- `blockpit` / `auto-balancing in` / `in`: `23.39854777`
- `blockpit` / `trade` / `out`: `-12.1`
- `blockpit` / `auto-balancing out` / `out`: `-11.67396699`
- `blockpit` / `interest` / `in`: `0.42603300`
- `binance_api` / `asset_dividend` / `in`: `0.419374660`
- `blockpit` / `fee` / `out`: `-0.384560`

### SHARK

- Endbestand Modell: `963.536668`
- Events: `5`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.000000` am `2024-11-22T15:59:16+00:00`

Jahres-Netto:
- `2024`: `0.000000`
- `2026`: `963.536668`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `1354.930693`
- `solana_rpc` / `token_transfer` / `in`: `963.536668`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-677.465347`
- `solana_rpc` / `token_transfer` / `out`: `-677.465346`

### XRP

- Endbestand Modell: `183.178126880000`
- Events: `69`
- Erster Negativbestand: `2025-03-09T19:00:30+00:00` nach `4744cb9ccb39354ec9ae9795b941bba5280acdbfefe04d755797130b38d5d167`
- Auslösend: `blockpit` / `fee` / `out` / `-0.0050823`
- Schlimmster Stand: `-5.057941800000` am `2025-07-13T21:38:44+00:00`

Jahres-Netto:
- `2025`: `183.178126880000`

Top Quellen-Netto:
- `blockpit` / `trade` / `in`: `99.20033434`
- `binance_api` / `fiat_payment_in` / `in`: `94.11803434`
- `blockpit` / `withdrawal` / `out`: `-19.5156`
- `blockpit` / `deposit` / `in`: `19.2876`
- `blockpit` / `derivative loss` / `out`: `-14.609562299632`
- `blockpit` / `derivative profit` / `in`: `6.353168849132`
- `bitget_tax_api` / `trade` / `in`: `5.0823`
- `bitget_tax_api` / `transfer` / `out`: `-5.0772216`
- `blockpit` / `derivative fee` / `out`: `-1.650762149500`
- `blockpit` / `fee` / `out`: `-0.0101646`

### VET

- Endbestand Modell: `100.00000000`
- Events: `5`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `100` am `2021-05-10T17:50:48+00:00`

Jahres-Netto:
- `2021`: `100`
- `2023`: `0.00E-6`
- `2024`: `100.01639287`
- `2025`: `-100.01639287`

Top Quellen-Netto:
- `blockpit` / `auto-balancing in` / `in`: `200.03278574`
- `blockpit` / `trade` / `out`: `-100.01639287`
- `blockpit` / `auto-balancing out` / `out`: `-100.01639287`
- `binance` / `trade` / `in`: `100`

### YFIDOWN

- Endbestand Modell: `57.67331`
- Events: `5`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `57.67331` am `2021-04-28T05:14:15+00:00`

Jahres-Netto:
- `2021`: `57.67331`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `57673.31`
- `binance` / `trade` / `out`: `-43211.72`
- `blockpit` / `auto-balancing in` / `in`: `14403.91669`
- `binance_api` / `dust_convert_out` / `out`: `-14403.91669`
- `blockpit` / `trade` / `out`: `-14403.91669`

### PIXEL

- Endbestand Modell: `19`
- Events: `19`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2024-09-06T15:02:54+00:00`

Jahres-Netto:
- `2024`: `19`

Top Quellen-Netto:
- `blockpit` / `deposit` / `in`: `19`

### DWNO

- Endbestand Modell: `12`
- Events: `12`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2024-06-15T19:43:42+00:00`

Jahres-Netto:
- `2024`: `12`

Top Quellen-Netto:
- `blockpit` / `deposit` / `in`: `12`

### CLD

- Endbestand Modell: `10`
- Events: `10`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2024-06-24T20:25:37+00:00`

Jahres-Netto:
- `2024`: `10`

Top Quellen-Netto:
- `blockpit` / `deposit` / `in`: `10`

### FOFME

- Endbestand Modell: `8`
- Events: `8`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2024-09-09T23:59:42+00:00`

Jahres-Netto:
- `2024`: `8`

Top Quellen-Netto:
- `blockpit` / `deposit` / `in`: `8`

### HOT

- Endbestand Modell: `6.918`
- Events: `5`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `6.918` am `2023-05-02T04:13:23+00:00`

Jahres-Netto:
- `2021`: `7`
- `2023`: `-0.082`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `6959`
- `binance` / `trade` / `out`: `-6952`
- `binance_api` / `dust_convert_out` / `out`: `-0.041`
- `blockpit` / `trade` / `out`: `-0.041`

### A777CLU5WMULSDMWMNBKNNZFNVEMKMWN3XCOF1PWH2GC

- Endbestand Modell: `6`
- Events: `6`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2025-07-06T12:33:33+00:00`

Jahres-Netto:
- `2025`: `6`

Top Quellen-Netto:
- `blockpit` / `auto-balancing in` / `in`: `6`

### SA

- Endbestand Modell: `5`
- Events: `5`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2024-02-15T10:58:59+00:00`

Jahres-Netto:
- `2024`: `5`

Top Quellen-Netto:
- `blockpit` / `deposit` / `in`: `5`

### JFY

- Endbestand Modell: `5`
- Events: `5`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2024-03-05T21:31:19+00:00`

Jahres-Netto:
- `2024`: `5`

Top Quellen-Netto:
- `blockpit` / `deposit` / `in`: `5`

### F8XM2GWIPZAKH1T8HOROFWS27SNRWDJZQHTIR4UNXFWW

- Endbestand Modell: `3`
- Events: `3`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2024-12-13T02:22:12+00:00`

Jahres-Netto:
- `2024`: `3`

Top Quellen-Netto:
- `blockpit` / `deposit` / `in`: `3`
