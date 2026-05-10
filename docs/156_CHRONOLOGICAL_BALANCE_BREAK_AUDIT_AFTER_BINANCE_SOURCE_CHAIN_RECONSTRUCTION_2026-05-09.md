# Chronologische Bestandsbruch-Analyse

Generiert: `2026-05-09T20:25:04.567295+00:00`
JSON: `var/chronological_balance_break_audit_after_binance_source_chain_reconstruction_2026-05-09.json`

## Überblick

- Bewegungen: `37845`
- Assets: `55`
- Assets mit negativem Endbestand: `0`

## Asset-Befunde

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

### DOGE

- Endbestand Modell: `2756.28509626`
- Events: `109`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `3` am `2021-02-17T18:13:26+00:00`

Jahres-Netto:
- `2021`: `22.25150592`
- `2022`: `1554.203`
- `2023`: `-0.2677641`
- `2025`: `1180.09835444`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `24683.6`
- `binance` / `trade` / `out`: `-24662.2`
- `binance_api` / `trade` / `buy_base`: `5906.00000000`
- `binance_api` / `trade` / `sell_base`: `-4720.00000000`
- `binance_2022_2023_blockpit_source_chain_reconstruction` / `trade` / `buy_base`: `2797`
- `binance_2022_2023_blockpit_source_chain_reconstruction` / `trade` / `buy_quote`: `-1240`
- `binance_api` / `trade` / `fee`: `-5.90600000`
- `binance_2022_2023_blockpit_source_chain_reconstruction` / `trade` / `fee`: `-2.797`
- `binance_account_statement` / `interest` / `in`: `0.85150592`
- `binance_api` / `dust_convert_out` / `out`: `-0.2677641`

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

### USDT

- Endbestand Modell: `1715.70671421101011250000`
- Events: `2051`
- Erster Negativbestand: `2022-01-05T15:36:46+00:00` nach `fe030531d67b4c88a2f56f81b84f438ee42b49096cc8b6a115b98e888071c449`
- Auslösend: `binance` / `trade` / `out` / `-186.270000`
- Schlimmster Stand: `-1569.91028184620000000000` am `2022-01-19T12:56:19+00:00`

Jahres-Netto:
- `2021`: `197.26431286000000000000`
- `2022`: `-107.70170036536000000000`
- `2023`: `-88.26629794170000000000`
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

### EUR

- Endbestand Modell: `1372.32963299`
- Events: `132`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `98.20` am `2021-03-05T05:45:57+00:00`

Jahres-Netto:
- `2021`: `1622.3129925`
- `2022`: `-100`
- `2023`: `-500.00948603`
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

- Endbestand Modell: `705.50501480143114379127906`
- Events: `27529`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.000` am `2021-02-09T18:45:43+00:00`

Jahres-Netto:
- `2021`: `145.18929968262277023903392`
- `2022`: `1106.03996395880837215284314`
- `2023`: `140.607037860000001399402`
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

### SOL

- Endbestand Modell: `10.52514844000000000000`
- Events: `1516`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.001` am `2021-04-28T05:18:42+00:00`

Jahres-Netto:
- `2021`: `0.001`
- `2023`: `62.769282274`
- `2024`: `-62.26199956900000000000`
- `2025`: `9.871305300`
- `2026`: `0.145560435`

Top Quellen-Netto:
- `solana_rpc` / `sol_transfer` / `in`: `498.696819928`
- `solana_rpc` / `sol_transfer` / `out`: `-498.298336418`
- `binance_api` / `trade` / `buy_base`: `72.94900000`
- `binance_api` / `withdrawal` / `out`: `-56.42100582`
- `binance_sol_2023_blockpit_reconstruction` / `trade` / `buy_base`: `55.33`
- `binance_api` / `trade` / `sell_base`: `-47.97800000`
- `binance_api` / `staking_conversion` / `out`: `-23.189761`
- `bitget_tax_api` / `transfer` / `out`: `-15.1554829`
- `bitget_tax_api` / `fiat_balance_success_user_in` / `in`: `15.1554`
- `binance_api` / `deposit` / `in`: `8.4700475`

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

- Endbestand Modell: `0.25845705`
- Events: `44`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.025` am `2021-02-06T21:23:58+00:00`

Jahres-Netto:
- `2021`: `0.03708294`
- `2023`: `0.00053484`
- `2025`: `0.22083927`

Top Quellen-Netto:
- `binance` / `trade` / `out`: `-4.14`
- `binance` / `trade` / `in`: `2.28`
- `binance` / `fiat_crypto_purchase` / `in`: `1.625`
- `binance_api` / `dust_convert_in` / `in`: `0.27419523`
- `binance_api` / `trade` / `buy_base`: `0.22200000`
- `binance_sol_2023_blockpit_reconstruction` / `trade` / `fee`: `-0.00157745`
- `binance_api` / `trade` / `fee`: `-0.00116073`

### DOCK

- Endbestand Modell: `0.25`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.25` am `2021-04-28T05:14:15+00:00`

Jahres-Netto:
- `2021`: `0.25`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `250`
- `binance_api` / `dust_convert_out` / `out`: `-249.75`

### USDC

- Endbestand Modell: `0.18978533`
- Events: `83`
- Erster Negativbestand: `2024-12-01T13:35:14+00:00` nach `212e7070015ff8cb1f9a0593afdfe7f7352a460a6bf7f990184d4c2291383e7f`
- Auslösend: `solana_rpc` / `swap_out_aggregated` / `out` / `-148.066735`
- Schlimmster Stand: `-0.000002` am `2024-12-01T13:35:14+00:00`

Jahres-Netto:
- `2024`: `0.093580`
- `2025`: `0.09620533`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `66980.700987`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-59402.809250`
- `solana_rpc` / `token_transfer` / `out`: `-59081.015587`
- `solana_rpc` / `token_transfer` / `in`: `51503.124838`
- `binance_api` / `trade` / `buy_quote`: `-688.39393600`
- `bitget_tax_api` / `deposit` / `in`: `500`
- `bitget_tax_api` / `trade` / `out`: `-500`
- `binance_api` / `fiat_payment_in` / `in`: `463.02038333`
- `binance_api` / `trade` / `sell_quote`: `225.56235000`

### WABI

- Endbestand Modell: `0.053`
- Events: `4`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.053` am `2021-04-28T05:14:15+00:00`

Jahres-Netto:
- `2021`: `0.053`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `53`
- `binance_api` / `dust_convert_out` / `out`: `-52.947`

### ETH

- Endbestand Modell: `0.04063986`
- Events: `37`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.00123828` am `2023-05-02T04:13:23+00:00`

Jahres-Netto:
- `2021`: `0.00124296`
- `2023`: `-0.00000468`
- `2025`: `0.03940158`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `1.23828496`
- `binance` / `trade` / `out`: `-1.237042`
- `binance_api` / `fiat_payment_in` / `in`: `0.03940158`
- `binance_api` / `dust_convert_out` / `out`: `-0.00000468`

### WRX

- Endbestand Modell: `0.014`
- Events: `3`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.014` am `2021-04-28T05:19:10+00:00`

Jahres-Netto:
- `2021`: `0.014`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `14`
- `binance` / `trade` / `out`: `-13`
- `binance_api` / `dust_convert_out` / `out`: `-0.986`

### BTC

- Endbestand Modell: `0.00252370400000000000`
- Events: `68`
- Erster Negativbestand: `2024-04-14T05:04:47.263000+00:00` nach `ff25f71c33c0b15f82f09e56284a8548d4bca517971c0dad4c3ce9178d0c3a4c`
- Auslösend: `bitget_tax_api` / `trade` / `out` / `-0.000542`
- Schlimmster Stand: `-0.00007630000000000000` am `2024-04-14T05:04:47.263000+00:00`

Jahres-Netto:
- `2021`: `0.000035940`
- `2022`: `0.00000213`
- `2023`: `0.00013133000000000000`
- `2024`: `-0.00024569600000000000`
- `2025`: `0.00260000`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `0.06605408`
- `binance` / `trade` / `out`: `-0.06601751`
- `binance_sol_2023_blockpit_reconstruction` / `trade` / `buy_quote`: `-0.03208291`
- `binance_2022_2023_blockpit_source_chain_reconstruction` / `trade` / `buy_base`: `0.0261892`
- `binance_api` / `deposit` / `in`: `0.01036997`
- `binance_2022_2023_blockpit_source_chain_reconstruction` / `trade` / `buy_quote`: `-0.00721984`
- `bitget_btc_2024_blockpit_reconstruction` / `deposit` / `in`: `0.0046913`
- `bitget_tax_api` / `trade` / `out`: `-0.004570`
- `binance_btc_2023_usdt_blockpit_reconstruction` / `trade` / `buy_base`: `0.00264`
- `binance_api` / `trade` / `buy_base`: `0.00260000`

### BUSD

- Endbestand Modell: `0.00211223520000000000`
- Events: `18`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `35.20000000000E-9` am `2022-10-15T13:42:51+00:00`

Jahres-Netto:
- `2022`: `0.07906062520000000000`
- `2023`: `-0.07694839000000000000`

Top Quellen-Netto:
- `binance_2022_2023_blockpit_source_chain_reconstruction` / `trade` / `buy_base`: `1116.78780198`
- `binance_2022_2023_blockpit_source_chain_reconstruction` / `trade` / `buy_quote`: `-1115.7370832`
- `pionex` / `trade` / `in`: `406.43612130000000000000`
- `pionex` / `trade` / `out`: `-406.23079100480000000000`
- `binance_api` / `dust_convert_out` / `out`: `-0.55379925`
- `binance_2022_2023_blockpit_source_chain_reconstruction` / `trade` / `fee`: `-0.49691953`
- `pionex` / `fee` / `out`: `-0.20321806`

### TRUMP

- Endbestand Modell: `0.00075605`
- Events: `26`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.00075600` am `2025-01-20T10:05:59.022000+00:00`

Jahres-Netto:
- `2025`: `0.00075605`

Top Quellen-Netto:
- `binance_api` / `trade` / `buy_base`: `153.28400000`
- `binance_api` / `trade` / `sell_base`: `-153.13000000`
- `binance_api` / `trade` / `fee`: `-0.15324400`
- `binance_api` / `interest` / `in`: `50E-9`

### MXC

- Endbestand Modell: `0.00002000000000000000`
- Events: `640`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.00002000000000000000` am `2023-06-09T16:19:26+00:00`

Jahres-Netto:
- `2022`: `12611.83794000000000000000`
- `2023`: `-12611.83792000000000000000`

Top Quellen-Netto:
- `pionex` / `trade` / `in`: `84231.56000000000000000000`
- `pionex` / `trade` / `out`: `-63659.10000000000000000000`
- `pionex` / `withdrawal` / `out`: `-20530.34420000`
- `pionex` / `fee` / `out`: `-42.11578000`

### MOBILE

- Endbestand Modell: `0.000000`
- Events: `39`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.000000` am `2023-08-01T06:43:43+00:00`

Jahres-Netto:
- `2023`: `0.000000`
- `2024`: `421.837749`
- `2025`: `-421.837749`

Top Quellen-Netto:
- `solana_rpc` / `swap_out_aggregated` / `out`: `-449359.197079`
- `solana_rpc` / `swap_in_aggregated` / `in`: `408584.933292`
- `solana_rpc` / `token_transfer` / `in`: `40774.263787`

### ZEUS

- Endbestand Modell: `0.000000`
- Events: `37`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.000000` am `2024-11-11T21:30:24+00:00`

Jahres-Netto:
- `2024`: `0.000000`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `58254.361817`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-45633.650681`
- `solana_rpc` / `token_transfer` / `out`: `-24480.394198`
- `solana_rpc` / `swap_in_aggregated` / `in`: `11859.683062`

### SHIB

- Endbestand Modell: `0.00E-18`
- Events: `21`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.00E-18` am `2024-03-12T04:44:43+00:00`

Jahres-Netto:
- `2022`: `0.00762500000000000000`
- `2024`: `-0.007625`

Top Quellen-Netto:
- `pionex` / `trade` / `in`: `6257044.75000000000000000000`
- `pionex` / `trade` / `out`: `-6253916.22000000000000000000`
- `pionex` / `fee` / `out`: `-3128.52237500`
- `pionex` / `dust_trade` / `out`: `-0.007625`

### BNSOL

- Endbestand Modell: `0.00E-6`
- Events: `17`
- Erster Negativbestand: `2025-03-23T13:46:29.121000+00:00` nach `bd7d775cd64759b5d390a276a8a8474b4597ef9cba554a121650fbf65de0fb34`
- Auslösend: `binance_api` / `convert_out` / `out` / `-22.32305193`
- Schlimmster Stand: `-390E-9` am `2025-03-23T13:46:29.121000+00:00`

Jahres-Netto:
- `2025`: `0.00E-6`

Top Quellen-Netto:
- `binance_api` / `convert_out` / `out`: `-22.32305193`
- `binance_api` / `staking_conversion` / `in`: `22.32304223`
- `binance_api` / `interest` / `in`: `0.00000970`

### EGLD

- Endbestand Modell: `0.00E-18`
- Events: `15`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.00E-18` am `2024-03-12T04:44:43+00:00`

Jahres-Netto:
- `2022`: `0.00007400000000000000`
- `2024`: `-0.000074`

Top Quellen-Netto:
- `pionex` / `trade` / `in`: `1.85200000000000000000`
- `pionex` / `trade` / `out`: `-1.85100000000000000000`
- `pionex` / `fee` / `out`: `-0.00092600`
- `pionex` / `dust_trade` / `out`: `-0.000074`

### 3NZ9JMVBMGAQOCYBIC2C7LQCJSCMGSAZ6VQQTDZCQMJH

- Endbestand Modell: `0.00E-6`
- Events: `9`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.00E-6` am `2024-12-05T05:22:33+00:00`

Jahres-Netto:
- `2024`: `0.00E-6`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `0.02505911`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-0.01335537`
- `solana_rpc` / `token_transfer` / `out`: `-0.01170374`

### DCUC8AMR83WZ27ZKQ2K9NS6R8ZRPF1J6CVAREBDZDMM

- Endbestand Modell: `0`
- Events: `4`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0` am `2024-03-26T20:05:33+00:00`

Jahres-Netto:
- `2024`: `0`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `2000000`
- `solana_rpc` / `token_transfer` / `out`: `-2000000`

### POPCAT

- Endbestand Modell: `0E-9`
- Events: `3`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0E-9` am `2024-11-17T05:48:52+00:00`

Jahres-Netto:
- `2024`: `0E-9`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `216.612334337`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-216.612334337`

### 25HAYBQFODHFWX9AY6RARBGVWGWDDNQCHSXS3JQ3MTDJ

- Endbestand Modell: `0.00000`
- Events: `3`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.00000` am `2024-11-17T05:49:19+00:00`

Jahres-Netto:
- `2024`: `0.00000`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `7445.66318`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-7445.66318`

### JUPSOL

- Endbestand Modell: `0E-9`
- Events: `3`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0E-9` am `2024-06-15T19:44:04+00:00`

Jahres-Netto:
- `2024`: `0E-9`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `1.461880894`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-1.461880894`

### COTI

- Endbestand Modell: `0`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0` am `2021-04-28T05:14:15+00:00`

Jahres-Netto:
- `2021`: `0`

Top Quellen-Netto:
- `binance` / `trade` / `in`: `100`
- `binance_api` / `dust_convert_out` / `out`: `-100`

### VTHO

- Endbestand Modell: `0.00E-6`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.00E-6` am `2023-05-02T04:13:23+00:00`

Jahres-Netto:
- `2023`: `0.00E-6`

Top Quellen-Netto:
- `binance_api_inferred` / `asset_dividend` / `in`: `42.39387934`
- `binance_api` / `dust_convert_out` / `out`: `-42.39387934`

### 7RPAXCSA3BIKAUOQTJ3DDSMKBLHEFQNBACPAUNBGC3KQ

- Endbestand Modell: `0`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0` am `2025-12-20T12:13:37+00:00`

Jahres-Netto:
- `2023`: `1`
- `2025`: `-1`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `1`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-1`

### DVOPSYDUOU8QQWRK4K1HIPN6WTKGK2PW1CFX8KUVVR4K

- Endbestand Modell: `0`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0` am `2024-04-25T10:47:12+00:00`

Jahres-Netto:
- `2023`: `1`
- `2024`: `-1`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `1`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-1`

### 5MFEM7LYTSGP2X3TVJXHXLENXSLRW6DQR3PSPJXVUETF

- Endbestand Modell: `0`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0` am `2025-12-26T21:07:02+00:00`

Jahres-Netto:
- `2023`: `1`
- `2025`: `-1`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `1`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-1`

### UPT

- Endbestand Modell: `0E-9`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0E-9` am `2024-11-22T15:59:42+00:00`

Jahres-Netto:
- `2024`: `0E-9`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `428.973805517`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-428.973805517`

### CHEYENNE

- Endbestand Modell: `0.000000`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.000000` am `2024-11-17T09:11:50+00:00`

Jahres-Netto:
- `2024`: `0.000000`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `1161.470294`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-1161.470294`
