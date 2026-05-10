# Chronologische Bestandsbruch-Analyse

Generiert: `2026-05-08T15:36:31.981728+00:00`
JSON: `var/chronological_balance_break_audit_after_solscan_safe_2026-05-08.json`

## Überblick

- Bewegungen: `39508`
- Assets: `60`
- Assets mit negativem Endbestand: `6`

## Asset-Befunde

### ZEUS

- Endbestand Modell: `-33814.395804`
- Events: `59`
- Erster Negativbestand: `2024-11-11T21:30:24+00:00` nach `6b4d5e69b10998fa68590a3f1efb129ff6090daa52874a1334faf6fb9cafe169`
- Auslösend: `solscan_wallet_discovery` / `swap_out_aggregated` / `out` / `-3017.109097`
- Schlimmster Stand: `-33814.395804` am `2024-11-23T05:33:36+00:00`

Jahres-Netto:
- `2024`: `-33814.395804`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `58254.361817`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-45633.650681`
- `solscan_wallet_discovery` / `swap_out_aggregated` / `out`: `-45633.650681`
- `solana_rpc` / `token_transfer` / `out`: `-24480.394198`
- `solana_rpc` / `swap_in_aggregated` / `in`: `11859.683062`
- `solscan_wallet_discovery` / `swap_in_aggregated` / `in`: `11819.254877`

### MOBILE

- Endbestand Modell: `-17496.101536`
- Events: `47`
- Erster Negativbestand: `2025-12-26T21:07:12+00:00` nach `64baa02e8a888b3c9edc01d2a62b3e091e44fa76314b29365e7d5bcf71619223`
- Auslösend: `solana_rpc` / `swap_out_aggregated` / `out` / `-64729.546356`
- Schlimmster Stand: `-17496.101536` am `2025-12-26T21:07:12+00:00`

Jahres-Netto:
- `2023`: `64729.546356`
- `2024`: `-16230.588289`
- `2025`: `-65995.059603`

Top Quellen-Netto:
- `solana_rpc` / `swap_out_aggregated` / `out`: `-449359.197079`
- `solana_rpc` / `swap_in_aggregated` / `in`: `408584.933292`
- `solscan_wallet_discovery` / `swap_out_aggregated` / `out`: `-360929.650723`
- `solscan_wallet_discovery` / `swap_in_aggregated` / `in`: `343855.386936`
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

- Endbestand Modell: `-22.323042230`
- Events: `16`
- Erster Negativbestand: `2025-03-23T13:46:29.121000+00:00` nach `bd7d775cd64759b5d390a276a8a8474b4597ef9cba554a121650fbf65de0fb34`
- Auslösend: `binance_api` / `convert_out` / `out` / `-22.32305193`
- Schlimmster Stand: `-22.323042620` am `2025-03-23T13:46:29.121000+00:00`

Jahres-Netto:
- `2025`: `-22.323042230`

Top Quellen-Netto:
- `binance_api` / `convert_out` / `out`: `-22.32305193`
- `blockpit` / `interest` / `in`: `0.000009700`

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

- Endbestand Modell: `1595931447081.3127190`
- Events: `2806`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `3421905036` am `2023-04-20T00:00:00+00:00`

Jahres-Netto:
- `2023`: `683909642952.5143050`
- `2024`: `845399996365.547577`
- `2025`: `66621836591.457937`
- `2026`: `-28828.20710`

Top Quellen-Netto:
- `heliumgeek` / `mining_reward` / `in`: `1595933017592`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-11393200.321693`
- `solscan_wallet_discovery` / `swap_out_aggregated` / `out`: `-11135574.390874`
- `solana_rpc` / `swap_in_aggregated` / `in`: `8779057.673155`
- `solscan_wallet_discovery` / `swap_in_aggregated` / `in`: `8715029.951983`
- `solana_rpc` / `token_transfer` / `in`: `4725849.956961`
- `solana_rpc` / `token_transfer` / `out`: `-2111707.308423`
- `heliumtracker` / `mining_reward` / `in`: `920501.267322`
- `blockpit` / `deposit` / `in`: `159999.915543`
- `blockpit` / `trade` / `out`: `-159999.915543`

### HNT

- Endbestand Modell: `10995657826.37368429143114379`
- Events: `27589`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.000` am `2021-02-09T18:45:43+00:00`

Jahres-Netto:
- `2021`: `1555.18551888262277023903392`
- `2022`: `1707.02982395880837215284314`
- `2023`: `142.807368980000001399402`
- `2024`: `-1237.68768522`
- `2025`: `10292883764.26984669`
- `2026`: `702771894.76881100`

Top Quellen-Netto:
- `heliumgeek` / `mining_reward` / `in`: `10995657317.12162`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-4650.43703630`
- `solscan_wallet_discovery` / `swap_out_aggregated` / `out`: `-4268.58566113`
- `binance` / `trade` / `out`: `-3205.826`
- `solana_rpc` / `swap_in_aggregated` / `in`: `2980.04789129`
- `binance` / `trade` / `in`: `2917.096`
- `pionex` / `trade` / `in`: `2310.29384864000000000000`
- `pionex` / `trade` / `out`: `-2309.30500000000000000000`
- `solscan_wallet_discovery` / `swap_in_aggregated` / `in`: `2156.18719421`
- `helium_legacy_cointracking` / `legacy_transfer` / `out`: `-1570.849923437360775624`

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

- Endbestand Modell: `963150.57416359902200000000`
- Events: `2452`
- Erster Negativbestand: `2023-05-08T04:43:46+00:00` nach `2b1f096e8e293a7969a03c79034a39e20a7f3d60b36f83a78de9d413d147afb9`
- Auslösend: `binance_api` / `withdrawal` / `out` / `-1.192`
- Schlimmster Stand: `-54.09693324` am `2023-06-10T16:49:21+00:00`

Jahres-Netto:
- `2021`: `0.001`
- `2023`: `7.457093714`
- `2024`: `963110.72188259100000000000`
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

### PEPE

- Endbestand Modell: `141633.43`
- Events: `19`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `2187.84` am `2024-03-11T03:12:43+00:00`

Jahres-Netto:
- `2024`: `39456.10`
- `2025`: `102177.33`

Top Quellen-Netto:
- `binance_api` / `asset_dividend` / `in`: `141633.43`

### JUP

- Endbestand Modell: `53685.17147692000000000000`
- Events: `746`
- Erster Negativbestand: `2024-03-12T04:47:59+00:00` nach `d169196f8933614907db0944a1ceae9cb6539bce569d4a62265102a63c2f2210`
- Auslösend: `pionex` / `fee` / `out` / `-0.01085231`
- Schlimmster Stand: `-16.24640098000000000000` am `2025-01-19T22:37:40+00:00`

Jahres-Netto:
- `2024`: `16838.34090502000000000000`
- `2025`: `36846.83057190`

Top Quellen-Netto:
- `solscan_wallet_discovery` / `swap_in_aggregated` / `in`: `79776.135914`
- `solana_rpc` / `swap_in_aggregated` / `in`: `79451.784276`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-66713.161665`
- `solscan_wallet_discovery` / `swap_out_aggregated` / `out`: `-66513.161665`
- `binance_api` / `trade` / `sell_base`: `-49464.60000000`
- `binance_api` / `trade` / `buy_base`: `42877.80000000`
- `solana_rpc` / `token_transfer` / `out`: `-30625.570394`
- `binance` / `deposit` / `in`: `23175.356052`
- `binance_api` / `deposit` / `in`: `23175.356052`
- `blockpit` / `withdrawal` / `out`: `-18495.180936`

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

### USDC

- Endbestand Modell: `7578.09889133`
- Events: `114`
- Erster Negativbestand: `2024-04-02T06:52:04+00:00` nach `f85b5b06a334aa03d78b893509652330f3cff962c9e1f7be88b6faea664d20c4`
- Auslösend: `solana_rpc` / `swap_out_aggregated` / `out` / `-1303.122096`
- Schlimmster Stand: `-1303.122096` am `2024-04-02T06:52:04+00:00`

Jahres-Netto:
- `2024`: `7470.813119`
- `2025`: `107.28577233`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `66980.700987`
- `solscan_wallet_discovery` / `swap_in_aggregated` / `in`: `66980.700987`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-59402.809250`
- `solscan_wallet_discovery` / `swap_out_aggregated` / `out`: `-59402.791881`
- `solana_rpc` / `token_transfer` / `out`: `-59081.015587`
- `solana_rpc` / `token_transfer` / `in`: `51503.124838`
- `binance_api` / `trade` / `buy_quote`: `-688.39393600`
- `bitget_tax_api` / `deposit` / `in`: `500`
- `bitget_tax_api` / `trade` / `out`: `-500`
- `binance_api` / `fiat_payment_in` / `in`: `463.02038333`

### USDT

- Endbestand Modell: `4200.77268363796511250000`
- Events: `2747`
- Erster Negativbestand: `2022-01-05T11:40:01+00:00` nach `1b4d889af78c6943b724fe3b6198b063533a04278511baf51a6f7207772c73b7`
- Auslösend: `pionex` / `trade` / `out` / `-346.92882000000000000000`
- Schlimmster Stand: `-6108.59557672347388750000` am `2024-04-02T06:52:26+00:00`

Jahres-Netto:
- `2021`: `197.26350632000000000000`
- `2022`: `-3036.59574436536000000000`
- `2023`: `-14.27771074170000000000`
- `2024`: `6716.17407544402011250000`
- `2025`: `338.208556981005`

Top Quellen-Netto:
- `binance_api` / `trade` / `sell_quote`: `75304.76031000`
- `binance_api` / `trade` / `buy_quote`: `-70220.53397000`
- `binance` / `trade` / `out`: `-46892.72026327`
- `binance` / `trade` / `in`: `45726.83467400`
- `solana_rpc` / `token_transfer` / `out`: `-34733.843023`
- `solana_rpc` / `swap_in_aggregated` / `in`: `31653.240947`
- `solscan_wallet_discovery` / `swap_in_aggregated` / `in`: `31474.919029`
- `pionex` / `trade` / `out`: `-25056.73396394677700000000`
- `solana_rpc` / `token_transfer` / `in`: `23866.833602`
- `solscan_wallet_discovery` / `swap_out_aggregated` / `out`: `-22774.239788`

### EUR

- Endbestand Modell: `3505.72963299`
- Events: `148`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `98.20` am `2021-03-05T05:45:57+00:00`

Jahres-Netto:
- `2021`: `1622.3129925`
- `2023`: `-0.00948603`
- `2024`: `10`
- `2025`: `1373.42612652`
- `2026`: `500`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `9612.5471437`
- `binance` / `fiat_withdrawal` / `out`: `-7035.49`
- `bitget_tax_api` / `fiat_recharge_in` / `in`: `4010`
- `bitget_tax_api` / `fiat_balance_user_out` / `out`: `-3000.14`
- `binance` / `trade` / `out`: `-2961.3823873`
- `binance` / `fiat_deposit` / `in`: `2426.2`
- `blockpit` / `deposit` / `in`: `1555`
- `binance` / `` / `in`: `1319.25`
- `bitget_tax_api` / `trade` / `out`: `-1009.85973348`
- `binance_api` / `fiat_payment_out` / `out`: `-792.0`

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
- `blockpit` / `interest` / `in`: `0.00435444`

### SHARKSYJJQANYXVFRPNBN9PJGKHWDHATNMYICWPNR1S

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

### ADA

- Endbestand Modell: `415.434814660`
- Events: `490`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.6` am `2021-04-05T10:12:32+00:00`

Jahres-Netto:
- `2021`: `10.6`
- `2023`: `0.318709130`
- `2024`: `0.10066553`
- `2025`: `404.41544000`

Top Quellen-Netto:
- `binance_api` / `trade` / `buy_base`: `404.80000000`
- `binance` / `trade` / `in`: `76.6`
- `binance` / `trade` / `out`: `-66`
- `binance_api` / `asset_dividend` / `in`: `0.419374660`
- `binance_api` / `trade` / `fee`: `-0.38456000`

### VET

- Endbestand Modell: `100`
- Events: `1`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `100` am `2021-05-10T17:50:48+00:00`

Jahres-Netto:
- `2021`: `100`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `100`

### XRP

- Endbestand Modell: `89.050452640000`
- Events: `35`
- Erster Negativbestand: `2025-03-09T19:00:30+00:00` nach `4744cb9ccb39354ec9ae9795b941bba5280acdbfefe04d755797130b38d5d167`
- Auslösend: `blockpit` / `fee` / `out` / `-0.0050823`
- Schlimmster Stand: `-5.067581700000` am `2025-07-13T21:38:44+00:00`

Jahres-Netto:
- `2025`: `89.050452640000`

Top Quellen-Netto:
- `binance_api` / `fiat_payment_in` / `in`: `94.11803434`
- `blockpit` / `withdrawal` / `out`: `-9.7578`
- `blockpit` / `deposit` / `in`: `9.6438`
- `blockpit` / `derivative loss` / `out`: `-7.304781149816`
- `bitget_tax_api` / `trade` / `in`: `5.0823`
- `bitget_tax_api` / `transfer` / `out`: `-5.0772216`
- `blockpit` / `derivative profit` / `in`: `3.176584424566`
- `blockpit` / `derivative fee` / `out`: `-0.825381074750`
- `blockpit` / `fee` / `out`: `-0.0050823`

### YFIDOWN

- Endbestand Modell: `57.67331`
- Events: `3`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `57.67331` am `2021-04-28T05:14:15+00:00`

Jahres-Netto:
- `2021`: `57.67331`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `57673.31`
- `binance` / `trade` / `out`: `-43211.72`
- `binance_api` / `dust_convert_out` / `out`: `-14403.91669`

### HOT

- Endbestand Modell: `6.959`
- Events: `4`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `6.959` am `2023-05-02T04:13:23+00:00`

Jahres-Netto:
- `2021`: `7`
- `2023`: `-0.041`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `6959`
- `binance` / `trade` / `out`: `-6952`
- `binance_api` / `dust_convert_out` / `out`: `-0.041`

### GTO

- Endbestand Modell: `1.8919`
- Events: `3`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1.8919` am `2021-03-29T16:48:07+00:00`

Jahres-Netto:
- `2021`: `1.8919`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `1891.9`
- `binance` / `trade` / `out`: `-1890`
- `binance_api` / `dust_convert_out` / `out`: `-0.0081`

### DSA1VHV1GOSIM1DV5K9H7S8HCJQZEFLSG6A4WNKQGJDU

- Endbestand Modell: `1`
- Events: `1`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2023-05-08T04:52:01+00:00`

Jahres-Netto:
- `2023`: `1`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `1`
