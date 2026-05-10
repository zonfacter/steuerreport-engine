# Remaining Undercoverage Detail Audit - 2026-05-09

Generated: `2026-05-09T16:25:25.561126+00:00`

## Summary

Material transient undercoverage remains limited to `EUR` and `USDT` after reference exclusions, ignored-token handling and dust tolerance.

## EUR

- Events: `216`
- Final balance: `1572.92627741`
- First break: `2021-02-06T21:18:02+00:00` `blockpit` / `trade` / `out` delta `-98` after `-98`
- Worst balance: `-6950.40774346` at `2023-05-02T04:13:23+00:00`
- Yearly net: `{'2021': '-6350.3887714', '2022': '-100', '2023': '-500.01897206', '2024': '8592.71124993', '2025': '-569.94774696', '2026': '500.5705179'}`

### Top Source Nets

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
- `binance` / `` / `in`: `1319.25`
- `bitget_tax_api` / `trade` / `out`: `-1009.85973348`

### Top Daily Nets

- `2024-11-28`: `8572.71124993`
- `2021-08-06`: `-1896.61`
- `2021-08-17`: `-1565.21`
- `2021-09-05`: `-1418.08`
- `2021-10-06`: `-1319.94`
- `2021-04-19`: `-1000`
- `2025-10-12`: `998.8`
- `2025-10-13`: `-997.67948000`
- `2021-08-31`: `609.8`
- `2026-02-02`: `500.5705179`
- `2023-03-17`: `-500`
- `2021-08-10`: `-404.45`

### Critical Window

- `2021-02-06T21:18:02+00:00` `blockpit` / `trade` / `out` qty `98` delta `-98` after `-98` tx `blockpit-7628:out`
- `2021-02-06T21:18:02+00:00` `blockpit` / `fee` / `out` qty `2` delta `-2` after `-100` tx `blockpit-7628:fee`

### Interpretation

- The first EUR break is a Blockpit/Binance FIAT Payments trade and fee without a prior EUR fiat deposit in the effective chronology.
- This should be reconciled against Binance fiat deposit/withdrawal exports, Bitget fiat records, WISO/Blockpit references and bank evidence before creating an adjustment.

## USDT

- Events: `2757`
- Final balance: `14311.10139312996008054000`
- First break: `2022-01-19T12:56:19+00:00` `pionex` / `trade` / `out` delta `-2572.15382077000000000000` after `-125.52609184620000200000`
- Worst balance: `-125.52609184620000200000` at `2022-01-19T12:56:19+00:00`
- Yearly net: `{'2021': '1634.47897786000000000000', '2022': '1577.98662163463999800000', '2023': '-14.27771110170000000000', '2024': '3883.01794201790408254000', '2025': '7229.8955627191160'}`

### Top Source Nets

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
- `solana_rpc` / `swap_out_aggregated` / `out`: `-22774.239788`
- `pionex` / `trade` / `in`: `21942.68846261340000000000`

### Top Daily Nets

- `2025-01-19`: `16505.50211564`
- `2025-01-21`: `-16166.55164000`
- `2025-01-28`: `-8018.83198734`
- `2025-01-27`: `8018.55154748`
- `2025-01-29`: `7656.9244239700003`
- `2024-12-01`: `5538.522476906`
- `2024-12-08`: `4735.519657`
- `2021-12-23`: `-3704.0252`
- `2024-12-09`: `-3633.80138615`
- `2021-12-28`: `-3407.86439982000000000000`
- `2021-12-17`: `3393.2075`
- `2024-03-16`: `3000.066714`

### Critical Window

- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` qty `664.950000` delta `-664.950000` after `4483.79774279380000000000` tx `binance-txhist-jan2022:20220105T173646:2008:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` qty `30.151200` delta `-30.151200` after `4453.64654279380000000000` tx `binance-txhist-jan2022:20220105T173646:2004:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` qty `667.317000` delta `-667.317000` after `3786.32954279380000000000` tx `binance-txhist-jan2022:20220105T173646:2015:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` qty `999.633600` delta `-999.633600` after `2786.69594279380000000000` tx `binance-txhist-jan2022:20220105T173646:2007:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` qty `841.383400` delta `-841.383400` after `1945.31254279380000000000` tx `binance-txhist-jan2022:20220105T173646:2005:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` qty `396.932500` delta `-396.932500` after `1548.38004279380000000000` tx `binance-txhist-jan2022:20220105T173646:2006:Transaction Spend:USDT`
- `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` qty `186.270000` delta `-186.270000` after `1362.11004279380000000000` tx `binance-txhist-jan2022:20220105T173646:2016:Transaction Spend:USDT`
- `2022-01-05T23:58:17+00:00` `pionex` / `trade` / `in` qty `164.42666500000000000000` delta `164.42666500000000000000` after `1526.53670779380000000000` tx `s_7:52:in:USDT`
- `2022-01-05T23:58:17+00:00` `pionex` / `fee` / `out` qty `0.08221337` delta `-0.08221337` after `1526.45449442380000000000` tx `s_7:52:fee:USDT`
- `2022-01-06T00:05:38+00:00` `pionex` / `trade` / `out` qty `28.21883800000000000000` delta `-28.21883800000000000000` after `1498.23565642380000000000` tx `s_7:53:out:USDT`
- `2022-01-06T21:09:31+00:00` `pionex` / `trade` / `in` qty `32.48038600000000000000` delta `32.48038600000000000000` after `1530.71604242380000000000` tx `s_7:54:in:USDT`
- `2022-01-06T21:09:31+00:00` `pionex` / `fee` / `out` qty `0.01624022` delta `-0.01624022` after `1530.69980220380000000000` tx `s_7:54:fee:USDT`
- `2022-01-07T00:09:25+00:00` `pionex` / `trade` / `in` qty `4.04297200000000000000` delta `4.04297200000000000000` after `1534.74277420380000000000` tx `s_7:55:in:USDT`
- `2022-01-07T00:09:25+00:00` `pionex` / `fee` / `out` qty `0.00202149` delta `-0.00202149` after `1534.74075271380000000000` tx `s_7:55:fee:USDT`
- `2022-01-12T12:55:37+00:00` `pionex` / `trade` / `out` qty `36.71461200000000000000` delta `-36.71461200000000000000` after `1498.02614071380000000000` tx `s_7:56:out:USDT`
- `2022-01-12T19:06:36+00:00` `pionex` / `trade` / `in` qty `16.47244900000000000000` delta `16.47244900000000000000` after `1514.49858971380000000000` tx `s_7:57:in:USDT`
- `2022-01-12T19:06:36+00:00` `pionex` / `fee` / `out` qty `0.00823623` delta `-0.00823623` after `1514.49035348380000000000` tx `s_7:57:fee:USDT`
- `2022-01-13T06:36:36+00:00` `pionex` / `trade` / `out` qty `12.07427200000000000000` delta `-12.07427200000000000000` after `1502.41608148380000000000` tx `s_7:58:out:USDT`
- `2022-01-13T10:57:57+00:00` `pionex` / `trade` / `in` qty `12.15623800000000000000` delta `12.15623800000000000000` after `1514.57231948380000000000` tx `s_7:59:in:USDT`
- `2022-01-13T10:57:57+00:00` `pionex` / `fee` / `out` qty `0.00607813` delta `-0.00607813` after `1514.56624135380000000000` tx `s_7:59:fee:USDT`
- `2022-01-18T10:30:41+00:00` `pionex` / `trade` / `in` qty `151.98727500000000000000` delta `151.98727500000000000000` after `1666.55351635380000000000` tx `s_7:60:in:USDT`
- `2022-01-18T10:30:41+00:00` `pionex` / `fee` / `out` qty `0.07599364` delta `-0.07599364` after `1666.47752271380000000000` tx `s_7:60:fee:USDT`
- `2022-01-18T10:32:14+00:00` `pionex` / `trade` / `out` qty `106.76336094000000000000` delta `-106.76336094000000000000` after `1559.71416177380000000000` tx `s_8:61:out:USDT`
- `2022-01-18T23:55:30+00:00` `pionex` / `trade` / `in` qty `107.14449546000000000000` delta `107.14449546000000000000` after `1666.85865723380000000000` tx `s_8:62:in:USDT`
- `2022-01-18T23:55:30+00:00` `pionex` / `fee` / `out` qty `0.05357227` delta `-0.05357227` after `1666.80508496380000000000` tx `s_8:62:fee:USDT`
- `2022-01-19T00:57:31+00:00` `pionex` / `trade` / `out` qty `158.17733910000000000000` delta `-158.17733910000000000000` after `1508.62774586380000000000` tx `s_8:63:out:USDT`
- `2022-01-19T11:22:49+00:00` `pionex` / `trade` / `in` qty `163.97883375000000000000` delta `163.97883375000000000000` after `1672.60657961380000000000` tx `s_8:64:in:USDT`
- `2022-01-19T11:22:49+00:00` `pionex` / `fee` / `out` qty `0.08198937` delta `-0.08198937` after `1672.52459024380000000000` tx `s_8:64:fee:USDT`
- `2022-01-19T11:34:54+00:00` `pionex` / `trade` / `out` qty `119.67176847000000000000` delta `-119.67176847000000000000` after `1552.85282177380000000000` tx `s_9:65:out:USDT`
- `2022-01-19T12:39:11+00:00` `pionex` / `trade` / `in` qty `120.46363312000000000000` delta `120.46363312000000000000` after `1673.31645489380000000000` tx `s_9:66:in:USDT`
- `2022-01-19T12:39:11+00:00` `pionex` / `fee` / `out` qty `0.06023180` delta `-0.06023180` after `1673.25622309380000000000` tx `s_9:66:fee:USDT`
- `2022-01-19T12:45:42+00:00` `pionex` / `trade` / `out` qty `479.99307717000000000000` delta `-479.99307717000000000000` after `1193.26314592380000000000` tx `s_10:67:out:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` qty `475.864400` delta `475.864400` after `1669.12754592380000000000` tx `binance-txhist-jan2022:20220119T144735:2049:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` qty `12.285000` delta `12.285000` after `1681.41254592380000000000` tx `binance-txhist-jan2022:20220119T144735:2051:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` qty `555.560000` delta `555.560000` after `2236.97254592380000000000` tx `binance-txhist-jan2022:20220119T144735:2054:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `trade` / `in` qty `203.733100` delta `203.733100` after `2440.70564592380000000000` tx `binance-txhist-jan2022:20220119T144735:2055:Transaction Revenue:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` qty `0.012285` delta `-0.012285` after `2440.69336092380000000000` tx `binance-txhist-jan2022:20220119T144735:2048:Transaction Fee:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` qty `0.475864` delta `-0.475864` after `2440.21749692380000000000` tx `binance-txhist-jan2022:20220119T144735:2050:Transaction Fee:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` qty `0.555560` delta `-0.555560` after `2439.66193692380000000000` tx `binance-txhist-jan2022:20220119T144735:2047:Transaction Fee:USDT`
- `2022-01-19T12:47:35+00:00` `binance` / `fee` / `out` qty `0.203733` delta `-0.203733` after `2439.45820392380000000000` tx `binance-txhist-jan2022:20220119T144735:2058:Transaction Fee:USDT`
- `2022-01-19T12:50:47+00:00` `blockpit` / `auto-balancing in` / `in` qty `8.169524999999998` delta `8.169524999999998` after `2447.62772892379999800000` tx `blockpit-7565:in`
- `2022-01-19T12:50:48+00:00` `binance_api` / `withdrawal` / `out` qty `1245.38419` delta `-1245.38419` after `1202.24353892379999800000` tx `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`
- `2022-01-19T12:50:48+00:00` `blockpit` / `fee` / `out` qty `1` delta `-1` after `1201.24353892379999800000` tx `blockpit-7564:fee`
- `2022-01-19T12:54:09+00:00` `pionex` / `deposit` / `in` qty `1245.38419000` delta `1245.38419000` after `2446.62772892379999800000` tx `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`
- `2022-01-19T12:56:19+00:00` `pionex` / `trade` / `out` qty `2572.15382077000000000000` delta `-2572.15382077000000000000` after `-125.52609184620000200000` tx `s_11:68:out:USDT`
- `2022-01-19T23:28:01+00:00` `pionex` / `trade` / `in` qty `348.69293954000000000000` delta `348.69293954000000000000` after `223.16684769379999800000` tx `s_10:69:in:USDT`
- `2022-01-19T23:28:01+00:00` `pionex` / `fee` / `out` qty `0.17434645` delta `-0.17434645` after `222.99250124379999800000` tx `s_10:69:fee:USDT`
- `2022-01-19T23:50:25+00:00` `pionex` / `trade` / `in` qty `1402.62272436000000000000` delta `1402.62272436000000000000` after `1625.61522560379999800000` tx `s_11:70:in:USDT`
- `2022-01-19T23:50:25+00:00` `pionex` / `fee` / `out` qty `0.70131096` delta `-0.70131096` after `1624.91391464379999800000` tx `s_11:70:fee:USDT`
- `2022-01-20T00:06:58+00:00` `pionex` / `trade` / `out` qty `513.25472484000000000000` delta `-513.25472484000000000000` after `1111.65918980379999800000` tx `s_11:71:out:USDT`
- `2022-01-20T00:09:50+00:00` `pionex` / `trade` / `out` qty `91.64680062000000000000` delta `-91.64680062000000000000` after `1020.01238918379999800000` tx `s_10:72:out:USDT`
- `2022-01-20T17:15:51+00:00` `pionex` / `trade` / `in` qty `512.27377344000000000000` delta `512.27377344000000000000` after `1532.28616262379999800000` tx `s_11:73:in:USDT`
- `2022-01-20T17:15:51+00:00` `pionex` / `fee` / `out` qty `0.25613710` delta `-0.25613710` after `1532.03002552379999800000` tx `s_11:73:fee:USDT`
- `2022-01-20T23:50:30+00:00` `pionex` / `trade` / `in` qty `138.01856018000000000000` delta `138.01856018000000000000` after `1670.04858570379999800000` tx `s_10:74:in:USDT`
- `2022-01-20T23:50:30+00:00` `pionex` / `fee` / `out` qty `0.06900932` delta `-0.06900932` after `1669.97957638379999800000` tx `s_10:74:fee:USDT`
- `2022-01-21T00:26:38+00:00` `pionex` / `trade` / `out` qty `26.43937640000000000000` delta `-26.43937640000000000000` after `1643.54019998379999800000` tx `s_10:75:out:USDT`
- `2022-01-21T20:22:14+00:00` `pionex` / `trade` / `in` qty `36.30961168000000000000` delta `36.30961168000000000000` after `1679.84981166379999800000` tx `s_10:76:in:USDT`
- `2022-01-21T20:22:14+00:00` `pionex` / `fee` / `out` qty `0.01815484` delta `-0.01815484` after `1679.83165682379999800000` tx `s_10:76:fee:USDT`
- `2022-01-24T22:07:11+00:00` `pionex` / `trade` / `out` qty `61.01250486000000000000` delta `-61.01250486000000000000` after `1618.81915196379999800000` tx `s_10:77:out:USDT`
- `2022-01-24T23:10:23+00:00` `pionex` / `trade` / `out` qty `68.07040812000000000000` delta `-68.07040812000000000000` after `1550.74874384379999800000` tx `s_11:78:out:USDT`
- `2022-01-24T23:20:26+00:00` `pionex` / `trade` / `in` qty `68.66596308000000000000` delta `68.66596308000000000000` after `1619.41470692379999800000` tx `s_11:79:in:USDT`
- `2022-01-24T23:20:26+00:00` `pionex` / `fee` / `out` qty `0.03433299` delta `-0.03433299` after `1619.38037393379999800000` tx `s_11:79:fee:USDT`
- `2022-01-24T23:59:11+00:00` `pionex` / `trade` / `in` qty `43.97724524000000000000` delta `43.97724524000000000000` after `1663.35761917379999800000` tx `s_10:80:in:USDT`
- `2022-01-24T23:59:11+00:00` `pionex` / `fee` / `out` qty `0.02198862` delta `-0.02198862` after `1663.33563055379999800000` tx `s_10:80:fee:USDT`
- `2022-01-25T00:10:57+00:00` `pionex` / `trade` / `out` qty `154.28591716000000000000` delta `-154.28591716000000000000` after `1509.04971339379999800000` tx `s_10:81:out:USDT`
- `2022-01-25T00:20:46+00:00` `pionex` / `trade` / `out` qty `151.49000724000000000000` delta `-151.49000724000000000000` after `1357.55970615379999800000` tx `s_11:82:out:USDT`
- `2022-01-25T03:59:29+00:00` `pionex` / `trade` / `in` qty `152.80873608000000000000` delta `152.80873608000000000000` after `1510.36844223379999800000` tx `s_11:83:in:USDT`
- `2022-01-25T03:59:29+00:00` `pionex` / `fee` / `out` qty `0.07640439` delta `-0.07640439` after `1510.29203784379999800000` tx `s_11:83:fee:USDT`
- `2022-01-25T23:45:49+00:00` `pionex` / `trade` / `in` qty `170.14218600000000000000` delta `170.14218600000000000000` after `1680.43422384379999800000` tx `s_10:84:in:USDT`
- `2022-01-25T23:45:49+00:00` `pionex` / `fee` / `out` qty `0.08507117` delta `-0.08507117` after `1680.34915267379999800000` tx `s_10:84:fee:USDT`
- `2022-01-26T00:57:55+00:00` `pionex` / `trade` / `out` qty `43.23706798000000000000` delta `-43.23706798000000000000` after `1637.11208469379999800000` tx `s_10:85:out:USDT`
- `2022-01-26T22:15:20+00:00` `pionex` / `trade` / `in` qty `42.39616288000000000000` delta `42.39616288000000000000` after `1679.50824757379999800000` tx `s_10:86:in:USDT`
- `2022-01-26T22:15:20+00:00` `pionex` / `fee` / `out` qty `0.02119813` delta `-0.02119813` after `1679.48704944379999800000` tx `s_10:86:fee:USDT`
- `2022-01-27T07:44:33+00:00` `pionex` / `trade` / `out` qty `70.47142078000000000000` delta `-70.47142078000000000000` after `1609.01562866379999800000` tx `s_10:87:out:USDT`
- `2022-01-27T15:09:00+00:00` `pionex` / `trade` / `out` qty `24.23489640000000000000` delta `-24.23489640000000000000` after `1584.78073226379999800000` tx `s_11:88:out:USDT`
- `2022-01-27T15:16:47+00:00` `pionex` / `trade` / `in` qty `24.44759460000000000000` delta `24.44759460000000000000` after `1609.22832686379999800000` tx `s_11:89:in:USDT`
- `2022-01-27T15:16:47+00:00` `pionex` / `fee` / `out` qty `0.01222380` delta `-0.01222380` after `1609.21610306379999800000` tx `s_11:89:fee:USDT`
- `2022-01-27T21:09:14+00:00` `pionex` / `trade` / `in` qty `59.76046958000000000000` delta `59.76046958000000000000` after `1668.97657264379999800000` tx `s_10:90:in:USDT`
- `2022-01-27T21:09:14+00:00` `pionex` / `fee` / `out` qty `0.02988025` delta `-0.02988025` after `1668.94669239379999800000` tx `s_10:90:fee:USDT`
- `2022-01-28T00:11:39+00:00` `pionex` / `trade` / `out` qty `56.99131580000000000000` delta `-56.99131580000000000000` after `1611.95537659379999800000` tx `s_10:91:out:USDT`
- ... truncated, total critical-window events: `110`

### Interpretation

- The remaining USDT break is Pionex-local and small compared with the later positive final balance.
- The next evidence target is Pionex bot/opening balance or internal transfer state immediately before 2022-01-19 12:56:19 UTC.
