# Chronologische Bestandsbruch-Analyse

Generiert: `2026-05-08T20:19:10.565864+00:00`
JSON: `var/chronological_balance_break_audit_current_2026-05-08_after_binance_earn.json`

## Überblick

- Bewegungen: `39195`
- Assets: `60`
- Assets mit negativem Endbestand: `6`

## Asset-Befunde

### USDT

- Endbestand Modell: `-4227.07018176603488750000`
- Events: `2662`
- Erster Negativbestand: `2022-01-05T11:40:01+00:00` nach `1b4d889af78c6943b724fe3b6198b063533a04278511baf51a6f7207772c73b7`
- Auslösend: `pionex` / `trade` / `out` / `-346.92882000000000000000`
- Schlimmster Stand: `-4838.40737822047388750000` am `2024-12-04T18:30:59+00:00`

Jahres-Netto:
- `2021`: `197.26350632000000000000`
- `2022`: `-3036.59574436536000000000`
- `2023`: `-14.27771074170000000000`
- `2024`: `-1984.50516555597988750000`
- `2025`: `611.044932577005`

Top Quellen-Netto:
- `binance_api` / `trade` / `sell_quote`: `75304.76031000`
- `binance_api` / `trade` / `buy_quote`: `-70220.53397000`
- `binance` / `trade` / `out`: `-46892.72026327`
- `binance` / `trade` / `in`: `45726.83467400`
- `solana_rpc` / `token_transfer` / `out`: `-34733.843023`
- `solana_rpc` / `swap_in_aggregated` / `in`: `31653.240947`
- `pionex` / `trade` / `out`: `-25056.73396394677700000000`
- `solana_rpc` / `token_transfer` / `in`: `23866.833602`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-22774.239788`
- `pionex` / `trade` / `in`: `21942.68846261340000000000`

### MOBILE

- Endbestand Modell: `-421.837749`
- Events: `40`
- Erster Negativbestand: `2025-12-20T12:13:50+00:00` nach `8d7da30c8eaf7ebcd19f17a994b8f6bf815a71440e9e0b42f5a8a2adef48a392`
- Auslösend: `blockpit` / `trade` / `out` / `-421.837749`
- Schlimmster Stand: `-421.837749` am `2025-12-20T12:13:50+00:00`

Jahres-Netto:
- `2023`: `0.000000`
- `2024`: `421.837749`
- `2025`: `-843.675498`

Top Quellen-Netto:
- `solana_rpc` / `swap_out_aggregated` / `out`: `-449359.197079`
- `solana_rpc` / `swap_in_aggregated` / `in`: `408584.933292`
- `solana_rpc` / `token_transfer` / `in`: `40774.263787`
- `blockpit` / `trade` / `out`: `-421.837749`

### VTHO

- Endbestand Modell: `-42.39387934`
- Events: `1`
- Erster Negativbestand: `2023-05-02T04:13:23+00:00` nach `61f4964558fe99fefaf53cbb118095ae2953e13528b8a34ef8a167ba3c42ef8d`
- Auslösend: `binance_api` / `dust_convert_out` / `out` / `-42.39387934`
- Schlimmster Stand: `-42.39387934` am `2023-05-02T04:13:23+00:00`

Jahres-Netto:
- `2023`: `-42.39387934`

Top Quellen-Netto:
- `binance_api` / `dust_convert_out` / `out`: `-42.39387934`

### BNSOL

- Endbestand Modell: `-22.32304223`
- Events: `16`
- Erster Negativbestand: `2025-03-23T13:46:29.121000+00:00` nach `bd7d775cd64759b5d390a276a8a8474b4597ef9cba554a121650fbf65de0fb34`
- Auslösend: `binance_api` / `convert_out` / `out` / `-22.32305193`
- Schlimmster Stand: `-22.32304262` am `2025-03-23T13:46:29.121000+00:00`

Jahres-Netto:
- `2025`: `-22.32304223`

Top Quellen-Netto:
- `binance_api` / `convert_out` / `out`: `-22.32305193`
- `binance_api` / `interest` / `in`: `0.00000970`

### VSR

- Endbestand Modell: `-2`
- Events: `2`
- Erster Negativbestand: `2025-12-20T12:13:37+00:00` nach `8a9a7079da0bbde3394bd3c6057e6159dd487fbfae033d075441ceaa1681ce44`
- Auslösend: `blockpit` / `withdrawal` / `out` / `-1`
- Schlimmster Stand: `-2` am `2025-12-26T21:07:02+00:00`

Jahres-Netto:
- `2025`: `-2`

Top Quellen-Netto:
- `blockpit` / `withdrawal` / `out`: `-2`

### BUSD

- Endbestand Modell: `-0.55168701480000000000`
- Events: `7`
- Erster Negativbestand: `2023-01-14T08:14:03+00:00` nach `266f6a64a54bf3d60213ca7cf8cd651995d597291edb5487b90ff8dc6f374543`
- Auslösend: `pionex` / `fee` / `out` / `-0.12348780`
- Schlimmster Stand: `-0.55168701480000000000` am `2023-05-02T04:13:23+00:00`

Jahres-Netto:
- `2022`: `35.20000000000E-9`
- `2023`: `-0.55168705000000000000`

Top Quellen-Netto:
- `pionex` / `trade` / `in`: `406.43612130000000000000`
- `pionex` / `trade` / `out`: `-406.23079100480000000000`
- `binance_api` / `dust_convert_out` / `out`: `-0.55379925`
- `pionex` / `fee` / `out`: `-0.20321806`

### IOT

- Endbestand Modell: `1595933867625.7516100`
- Events: `2761`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `3421905036` am `2023-04-20T00:00:00+00:00`

Jahres-Netto:
- `2023`: `683909500931.8233920`
- `2024`: `845402447071.928218`
- `2025`: `66621934036.103550`
- `2026`: `-14414.10355`

Top Quellen-Netto:
- `heliumgeek` / `mining_reward` / `in`: `1595933017592`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-11393200.321693`
- `solana_rpc` / `swap_in_aggregated` / `in`: `8779057.673155`
- `solana_rpc` / `token_transfer` / `in`: `4725849.956961`
- `solana_rpc` / `token_transfer` / `out`: `-2111707.308423`
- `heliumtracker` / `mining_reward` / `in`: `920501.267322`
- `blockpit` / `deposit` / `in`: `159999.915543`
- `blockpit` / `trade` / `out`: `-159999.915543`
- `heliumtracker` / `mining_commission` / `out`: `-70467.5157120`

### HNT

- Endbestand Modell: `10995659938.77215121143114379`
- Events: `27563`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.000` am `2021-02-09T18:45:43+00:00`

Jahres-Netto:
- `2021`: `1555.18551888262277023903392`
- `2022`: `1707.02982395880837215284314`
- `2023`: `142.447037860000001399402`
- `2024`: `-12.48595600`
- `2025`: `10292884654.00812475`
- `2026`: `702771892.58760176`

Top Quellen-Netto:
- `heliumgeek` / `mining_reward` / `in`: `10995657317.12162`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-4650.43703630`
- `binance` / `trade` / `out`: `-3205.826`
- `solana_rpc` / `swap_in_aggregated` / `in`: `2980.04789129`
- `binance` / `trade` / `in`: `2917.096`
- `pionex` / `trade` / `in`: `2310.29384864000000000000`
- `pionex` / `trade` / `out`: `-2309.30500000000000000000`
- `helium_legacy_cointracking` / `legacy_transfer` / `out`: `-1570.849923437360775624`
- `binance` / `deposit` / `in`: `1424.96965874`
- `helium_legacy_cointracking` / `mining_reward` / `in`: `1298.11054127000001756127906`

### CM8VSESV7MBHAFD5UDXH84QFGXMAVWJCVVHOPB1DZIF4

- Endbestand Modell: `1000000000`
- Events: `1`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1000000000` am `2023-07-30T06:59:36+00:00`

Jahres-Netto:
- `2023`: `1000000000`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `1000000000`

### 7ATGF8KQO4WJRD5ATGX7T1V2ZVVYKPJBFFNEVF1ICFV1

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

### 2KFZCKFXJ1US8YRQZA5VKTSXY3GPZFZVVHWJ91N8FV2J

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

### SOL

- Endbestand Modell: `963150.58435999902200000000`
- Events: `2448`
- Erster Negativbestand: `2023-05-08T04:43:46+00:00` nach `2b1f096e8e293a7969a03c79034a39e20a7f3d60b36f83a78de9d413d147afb9`
- Auslösend: `binance_api` / `withdrawal` / `out` / `-1.192`
- Schlimmster Stand: `-54.09693324` am `2023-06-10T16:49:21+00:00`

Jahres-Netto:
- `2021`: `0.001`
- `2023`: `7.461172274`
- `2024`: `963110.72800043100000000000`
- `2025`: `32.248626859022`
- `2026`: `0.145560435`

Top Quellen-Netto:
- `jupiter_perps` / `derivative open` / `open`: `481585.80`
- `jupiter_perps` / `derivative close` / `close`: `481585.79`
- `solana_rpc` / `sol_transfer` / `in`: `498.696819928`
- `solana_rpc` / `sol_transfer` / `out`: `-498.298336418`
- `binance_api` / `trade` / `buy_base`: `72.94900000`
- `binance_api` / `withdrawal` / `out`: `-56.42100582`
- `binance_api` / `trade` / `sell_base`: `-47.97800000`
- `blockpit` / `derivative loss` / `out`: `-16.576651880472`
- `bitget_tax_api` / `transfer` / `out`: `-15.1554829`
- `bitget_tax_api` / `fiat_balance_success_user_in` / `in`: `15.1554`

### PEPE

- Endbestand Modell: `243810.76`
- Events: `20`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `2187.84` am `2024-03-11T03:12:43+00:00`

Jahres-Netto:
- `2024`: `39456.10`
- `2025`: `204354.66`

Top Quellen-Netto:
- `binance_api` / `asset_dividend` / `in`: `141633.43`
- `binance_api` / `interest` / `in`: `102177.33`

### BTC

- Endbestand Modell: `234297.23880679400000000000`
- Events: `72`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.00000277` am `2021-02-23T10:54:47+00:00`

Jahres-Netto:
- `2021`: `0.000035940`
- `2023`: `0.02098685000000000000`
- `2024`: `234297.21518400400000000000`
- `2025`: `0.00260000`

Top Quellen-Netto:
- `jupiter_perps` / `derivative open` / `open`: `117148.61`
- `jupiter_perps` / `derivative close` / `close`: `117148.61`
- `binance` / `trade` / `in`: `0.06605408`
- `binance` / `trade` / `out`: `-0.06601751`
- `binance` / `deposit` / `in`: `0.01036997`
- `binance_api` / `deposit` / `in`: `0.01036997`
- `bitget_tax_api` / `trade` / `out`: `-0.004570`
- `binance_api` / `trade` / `buy_base`: `0.00260000`
- `pionex` / `trade` / `in`: `0.00024703000000000000`
- `pionex` / `trade` / `out`: `-0.00024600000000000000`

### JUP

- Endbestand Modell: `40424.56793981000000000000`
- Events: `672`
- Erster Negativbestand: `2024-03-12T04:47:59+00:00` nach `d169196f8933614907db0944a1ceae9cb6539bce569d4a62265102a63c2f2210`
- Auslösend: `pionex` / `fee` / `out` / `-0.01085231`
- Schlimmster Stand: `-8426.82462898000000000000` am `2025-01-19T22:37:40+00:00`

Jahres-Netto:
- `2024`: `8427.76267702000000000000`
- `2025`: `31996.80526279`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `79451.784276`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-66713.161665`
- `binance_api` / `trade` / `sell_base`: `-49464.60000000`
- `binance_api` / `trade` / `buy_base`: `42877.80000000`
- `solana_rpc` / `token_transfer` / `out`: `-30625.570394`
- `binance` / `deposit` / `in`: `23175.356052`
- `binance_api` / `deposit` / `in`: `23175.356052`
- `blockpit` / `withdrawal` / `out`: `-18495.180936`
- `binance` / `` / `in`: `14748.062399`
- `solana_rpc` / `token_transfer` / `in`: `12356.392080`

### WIN

- Endbestand Modell: `14143`
- Events: `3`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `14143` am `2021-05-05T04:59:31+00:00`

Jahres-Netto:
- `2021`: `14143`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `56570`
- `binance` / `trade` / `out`: `-42427`

### BTT

- Endbestand Modell: `1988.5`
- Events: `8`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `2.5` am `2021-04-28T05:14:15+00:00`

Jahres-Netto:
- `2021`: `1988.5`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `129068`
- `binance` / `trade` / `out`: `-124582`
- `binance_api` / `dust_convert_out` / `out`: `-2497.5`

### EUR

- Endbestand Modell: `1972.32963299`
- Events: `128`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `98.20` am `2021-03-05T05:45:57+00:00`

Jahres-Netto:
- `2021`: `1622.3129925`
- `2023`: `-0.00948603`
- `2024`: `10`
- `2025`: `-159.97387348`
- `2026`: `500`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `9612.5471437`
- `binance` / `fiat_withdrawal` / `out`: `-7035.49`
- `bitget_tax_api` / `fiat_recharge_in` / `in`: `4010`
- `bitget_tax_api` / `fiat_balance_user_out` / `out`: `-3000.14`
- `binance` / `trade` / `out`: `-2961.3823873`
- `binance` / `fiat_deposit` / `in`: `2426.2`
- `binance` / `` / `in`: `1319.25`
- `bitget_tax_api` / `trade` / `out`: `-1009.85973348`
- `binance_api` / `fiat_payment_out` / `out`: `-792.0`
- `binance_api` / `trade` / `buy_quote`: `-694.87414000`

### DOGE

- Endbestand Modell: `1201.23059034`
- Events: `74`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `3` am `2021-02-17T18:13:26+00:00`

Jahres-Netto:
- `2021`: `21.4`
- `2023`: `-0.2677641`
- `2025`: `1180.09835444`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `24683.6`
- `binance` / `trade` / `out`: `-24662.2`
- `binance_api` / `trade` / `buy_base`: `5906.00000000`
- `binance_api` / `trade` / `sell_base`: `-4720.00000000`
- `binance_api` / `trade` / `fee`: `-5.90600000`
- `binance_api` / `dust_convert_out` / `out`: `-0.2677641`
- `binance_api` / `interest` / `in`: `0.00435444`
