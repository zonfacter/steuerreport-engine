# Chronologische Bestandsbruch-Analyse

Generiert: `2026-05-09T19:59:27.274241+00:00`
JSON: `var/chronological_balance_break_audit_after_active_source_filter_2026-05-09.json`

## Überblick

- Bewegungen: `37798`
- Assets: `55`
- Assets mit negativem Endbestand: `2`

## Asset-Befunde

### SOL

- Endbestand Modell: `-44.78296156000000000000`
- Events: `1511`
- Erster Negativbestand: `2023-05-08T04:43:46+00:00` nach `2b1f096e8e293a7969a03c79034a39e20a7f3d60b36f83a78de9d413d147afb9`
- Auslösend: `binance_api` / `withdrawal` / `out` / `-1.192`
- Schlimmster Stand: `-54.79988580100000000000` am `2025-01-04T08:31:40+00:00`

Jahres-Netto:
- `2021`: `0.001`
- `2023`: `7.461172274`
- `2024`: `-62.26199956900000000000`
- `2025`: `9.871305300`
- `2026`: `0.145560435`

Top Quellen-Netto:
- `solana_rpc` / `sol_transfer` / `in`: `498.696819928`
- `solana_rpc` / `sol_transfer` / `out`: `-498.298336418`
- `binance_api` / `trade` / `buy_base`: `72.94900000`
- `binance_api` / `withdrawal` / `out`: `-56.42100582`
- `binance_api` / `trade` / `sell_base`: `-47.97800000`
- `binance_api` / `staking_conversion` / `out`: `-23.189761`
- `bitget_tax_api` / `transfer` / `out`: `-15.1554829`
- `bitget_tax_api` / `fiat_balance_success_user_in` / `in`: `15.1554`
- `binance_api` / `deposit` / `in`: `8.4700475`
- `bitget_tax_api` / `transfer` / `in`: `7.0760475`

### BUSD

- Endbestand Modell: `-0.55168701480000000000`
- Events: `7`
- Erster Negativbestand: `2023-05-02T04:13:23+00:00` nach `bbdf8fcb5f2c87f9d1a826fbc4b2c16de49a42b06cda2ea373279da7aa01b148`
- Auslösend: `binance_api` / `dust_convert_out` / `out` / `-0.55379925`
- Schlimmster Stand: `-0.55168701480000000000` am `2023-05-02T04:13:23+00:00`

Jahres-Netto:
- `2022`: `35.20000000000E-9`
- `2023`: `-0.55168705000000000000`

Top Quellen-Netto:
- `pionex` / `trade` / `in`: `406.43612130000000000000`
- `pionex` / `trade` / `out`: `-406.23079100480000000000`
- `binance_api` / `dust_convert_out` / `out`: `-0.55379925`
- `pionex` / `fee` / `out`: `-0.20321806`

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

- Endbestand Modell: `2557579.8469670`
- Events: `2745`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `3421.905036` am `2023-04-20T00:00:00+00:00`

Jahres-Netto:
- `2023`: `1922990.4422270`
- `2024`: `561313.925059`
- `2025`: `87689.583231`
- `2026`: `-14414.10355`

Top Quellen-Netto:
- `solana_rpc` / `swap_out_aggregated` / `out`: `-11393200.321693`
- `solana_rpc` / `swap_in_aggregated` / `in`: `8779057.673155`
- `solana_rpc` / `token_transfer` / `in`: `4725849.956961`
- `solana_rpc` / `token_transfer` / `out`: `-2111707.308423`
- `heliumgeek` / `mining_reward` / `in`: `1707546.095357`
- `heliumtracker` / `mining_reward` / `in`: `920501.267322`
- `heliumtracker` / `mining_commission` / `out`: `-70467.5157120`

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

### JUP

- Endbestand Modell: `16572.53617481000000000000`
- Events: `627`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.46377402000000000000` am `2024-11-24T11:23:20+00:00`

Jahres-Netto:
- `2024`: `8427.76267702000000000000`
- `2025`: `8144.77349779`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `79451.784276`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-66713.161665`
- `binance_api` / `trade` / `sell_base`: `-49464.60000000`
- `binance_api` / `trade` / `buy_base`: `42877.80000000`
- `solana_rpc` / `token_transfer` / `out`: `-30625.570394`
- `binance_api` / `deposit` / `in`: `23175.356052`
- `solana_rpc` / `token_transfer` / `in`: `12356.392080`
- `bitget_tax_api` / `trade` / `in`: `5818.24`
- `binance_api` / `convert_in` / `in`: `5532.20028976`
- `binance_api` / `withdrawal` / `out`: `-5530.555703`

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

### USDT

- Endbestand Modell: `1789.69530141101011250000`
- Events: `2050`
- Erster Negativbestand: `2022-01-05T15:36:46+00:00` nach `fe030531d67b4c88a2f56f81b84f438ee42b49096cc8b6a115b98e888071c449`
- Auslösend: `binance` / `trade` / `out` / `-186.270000`
- Schlimmster Stand: `-1569.91028184620000000000` am `2022-01-19T12:56:19+00:00`

Jahres-Netto:
- `2021`: `197.26431286000000000000`
- `2022`: `-107.70170036536000000000`
- `2023`: `-14.27771074170000000000`
- `2024`: `12.22958516807011250000`
- `2025`: `1702.18081449`

Top Quellen-Netto:
- `binance_api` / `trade` / `sell_quote`: `75304.76031000`
- `binance_api` / `trade` / `buy_quote`: `-70220.53397000`
- `binance` / `trade` / `in`: `54321.88957400`
- `binance` / `trade` / `out`: `-52550.28606327`
- `solana_rpc` / `token_transfer` / `out`: `-34733.843023`
- `solana_rpc` / `swap_in_aggregated` / `in`: `31653.240947`
- `pionex` / `trade` / `out`: `-25056.73396394677700000000`
- `solana_rpc` / `token_transfer` / `in`: `23866.833602`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-22774.239788`
- `pionex` / `trade` / `in`: `21942.68846261340000000000`

### DOGE

- Endbestand Modell: `1202.08209626`
- Events: `102`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `3` am `2021-02-17T18:13:26+00:00`

Jahres-Netto:
- `2021`: `22.25150592`
- `2023`: `-0.2677641`
- `2025`: `1180.09835444`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `24683.6`
- `binance` / `trade` / `out`: `-24662.2`
- `binance_api` / `trade` / `buy_base`: `5906.00000000`
- `binance_api` / `trade` / `sell_base`: `-4720.00000000`
- `binance_api` / `trade` / `fee`: `-5.90600000`
- `binance_account_statement` / `interest` / `in`: `0.85150592`
- `binance_api` / `dust_convert_out` / `out`: `-0.2677641`
- `binance_api` / `interest` / `in`: `0.00435444`

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

### HNT

- Endbestand Modell: `707.34501480143114379127906`
- Events: `27524`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.000` am `2021-02-09T18:45:43+00:00`

Jahres-Netto:
- `2021`: `145.18929968262277023903392`
- `2022`: `1106.03996395880837215284314`
- `2023`: `142.447037860000001399402`
- `2024`: `-12.48595600`
- `2025`: `-693.07437189`
- `2026`: `19.22904119`

Top Quellen-Netto:
- `solana_rpc` / `swap_out_aggregated` / `out`: `-4650.43703630`
- `binance` / `trade` / `out`: `-3456.346000`
- `binance` / `trade` / `in`: `3046.956000`
- `solana_rpc` / `swap_in_aggregated` / `in`: `2980.04789129`
- `pionex` / `trade` / `in`: `2310.29384864000000000000`
- `pionex` / `trade` / `out`: `-2309.30500000000000000000`
- `helium_legacy_cointracking` / `legacy_transfer` / `out`: `-1570.849923437360775624`
- `helium_legacy_cointracking` / `mining_reward` / `in`: `1298.11054127000001756127906`
- `helium_legacy_cointracking` / `legacy_transfer` / `in`: `1144.99641461`
- `solana_rpc` / `token_transfer` / `in`: `1104.91292493`

### ADA

- Endbestand Modell: `415.495991900`
- Events: `766`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.61852377` am `2021-04-05T10:12:32+00:00`

Jahres-Netto:
- `2021`: `10.66103729`
- `2022`: `0.00013995`
- `2023`: `0.318709130`
- `2024`: `0.10066553`
- `2025`: `404.41544000`

Top Quellen-Netto:
- `binance_api` / `trade` / `buy_base`: `404.80000000`
- `binance` / `trade` / `in`: `76.6`
- `binance` / `trade` / `out`: `-66`
- `binance_api` / `asset_dividend` / `in`: `0.419374660`
- `binance_api` / `trade` / `fee`: `-0.38456000`
- `binance_account_statement` / `interest` / `in`: `0.06117724`

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

- Endbestand Modell: `94.12311274`
- Events: `3`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.0050784` am `2025-07-11T20:04:08.224000+00:00`

Jahres-Netto:
- `2025`: `94.12311274`

Top Quellen-Netto:
- `binance_api` / `fiat_payment_in` / `in`: `94.11803434`
- `bitget_tax_api` / `trade` / `in`: `5.0823`
- `bitget_tax_api` / `transfer` / `out`: `-5.0772216`

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

### HJGKKKPN9EKNQJRTNZAUJX8WCINDFLWTD5HLK3OAQNQN

- Endbestand Modell: `1`
- Events: `1`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2023-05-09T00:49:13+00:00`

Jahres-Netto:
- `2023`: `1`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `1`

### BPXYGGVFENQCQXWXYV5VINYCRCQZRSZ3WIAGEQ3MXX59

- Endbestand Modell: `1`
- Events: `1`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2023-06-02T04:28:57+00:00`

Jahres-Netto:
- `2023`: `1`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `1`

### 2DWZNYB3TCPSPHDP4MH7KWF2F4U6PAWFA1SINSFXNRQC

- Endbestand Modell: `1`
- Events: `1`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2023-06-29T03:20:08+00:00`

Jahres-Netto:
- `2023`: `1`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `1`

### 7F1ENCQZBKYCS92LGGMTSZEMUEPUNAFDNPT1KCUNHVMG

- Endbestand Modell: `1`
- Events: `1`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2023-08-02T06:43:13+00:00`

Jahres-Netto:
- `2023`: `1`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `1`

### 4T4TMHWGWBMXJEAK3FFRJMKDGUSMH9Q3NDH2JUKF2RGU

- Endbestand Modell: `1`
- Events: `1`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2023-08-19T07:55:38+00:00`

Jahres-Netto:
- `2023`: `1`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `1`

### EUKMXS2PC2U2EBJSHXH5MNEZNGFDYNJYJYFAEDN7TEAV

- Endbestand Modell: `1`
- Events: `1`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1` am `2023-12-17T00:57:32+00:00`

Jahres-Netto:
- `2023`: `1`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `1`

### CDT

- Endbestand Modell: `0.564`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.564` am `2021-04-28T05:14:15+00:00`

Jahres-Netto:
- `2021`: `0.564`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `564`
- `binance_api` / `dust_convert_out` / `out`: `-563.436`

### BNB

- Endbestand Modell: `0.26003450`
- Events: `41`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.025` am `2021-02-06T21:23:58+00:00`

Jahres-Netto:
- `2021`: `0.03708294`
- `2023`: `0.00211229`
- `2025`: `0.22083927`

Top Quellen-Netto:
- `binance` / `trade` / `out`: `-4.14`
- `binance` / `trade` / `in`: `2.28`
- `binance` / `fiat_crypto_purchase` / `in`: `1.625`
- `binance_api` / `dust_convert_in` / `in`: `0.27419523`
- `binance_api` / `trade` / `buy_base`: `0.22200000`
- `binance_api` / `trade` / `fee`: `-0.00116073`
