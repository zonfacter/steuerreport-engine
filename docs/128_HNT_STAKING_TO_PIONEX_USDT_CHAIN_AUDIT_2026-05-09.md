# HNT Staking/Legacy -> Binance -> USDT -> Pionex Chain Audit - 2026-05-09

## Ergebnis

- Hypothese: HNT staking/legacy rewards were transferred to Binance, sold to USDT, then USDT was sent to Pionex.
- Bekannte Binance-HNT-Deposit-Adresse: `138bCXPVfSq7yyTfoDUrVwztPmUr4WGyA7TED9Y41djmF7rjA8y`
- Pionex Deposit-Datei: `usertransfer/pionex/deposit-withdraw.csv`
- Pionex Deposit-Assets in dieser Datei: `['USDT']`

## Pionex Deposits

- `2021-12-25 16:23:04` `200.00000000 USDT` `TRC20` tx `b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182`
- `2022-01-19 12:54:09` `1245.38419000 USDT` `TRC20` tx `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`
- `2022-02-23 05:41:40` `696.82747400 USDT` `TRC20` tx `a08ff362825ec9a4ce35a3f4803cf1dba32cf1deaae4fc58281001b6a0692566`
- `2022-02-25 21:35:15` `983.69132300 USDT` `TRC20` tx `9542656804be81094930fd1ddb83710f82c54fda18b2691c1ffd57b95d89a132`

## Window Totals 2021-12-01 bis 2022-01-19

- `HNT|binance_api|deposit|in`: `11`
- `HNT|binance|deposit|in`: `22`
- `HNT|binance|fee|out`: `-0.129860`
- `HNT|binance|trade|in`: `420.540000`
- `HNT|binance|trade|out`: `-477.690000`
- `HNT|binance||in`: `11`
- `USDT|binance_api|withdrawal|out`: `-1445.38419`
- `USDT|binance|fee|out`: `-6.910853`
- `USDT|binance|trade|in`: `17659.432100`
- `USDT|binance|trade|out`: `-16194.875400`
- `USDT|pionex|deposit|in`: `1445.38419000`
- `USDT|pionex|fee|out`: `-1.72789977`
- `USDT|pionex|trade|in`: `3455.80005751340000000000`
- `USDT|pionex|trade|out`: `-4792.24756236960000000000`

## Belegkette

- `2021-12-13T13:15:57+00:00` `HNT` `helium_legacy_cointracking` / `legacy_transfer` / `out` qty `11.011985972987041` delta `-11.011985972987041` tx `dj72bxdhbOLfjlzHK9z-6c4SJ6YP0LY2NXkJPRHRBqw+133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j`
- `2021-12-13T13:19:15+00:00` `HNT` `binance` / `deposit` / `in` qty `11` delta `11` tx `dj72bxdhbOLfjlzHK9z-6c4SJ6YP0LY2NXkJPRHRBqw`
- `2021-12-13T13:19:15+00:00` `HNT` `binance` / `deposit` / `in` qty `11` delta `11` tx `dj72bxdhbOLfjlzHK9z-6c4SJ6YP0LY2NXkJPRHRBqw`
- `2021-12-13T13:19:15+00:00` `HNT` `binance_api` / `deposit` / `in` qty `11` delta `11` tx `dj72bxdhbOLfjlzHK9z-6c4SJ6YP0LY2NXkJPRHRBqw`
- `2021-12-17T23:16:00+00:00` `USDT` `binance` / `trade` / `in` qty `714.657` delta `714.657` tx `binance-trade-25:in:USDT`
- `2021-12-17T23:16:00+00:00` `USDT` `binance` / `trade` / `in` qty `626.78` delta `626.78` tx `binance-trade-29:in:USDT`
- `2021-12-17T23:16:00+00:00` `USDT` `binance` / `trade` / `in` qty `55.2081` delta `55.2081` tx `binance-trade-28:in:USDT`
- `2021-12-17T23:16:00+00:00` `USDT` `binance` / `trade` / `in` qty `40.9706` delta `40.9706` tx `binance-trade-26:in:USDT`
- `2021-12-17T23:16:00+00:00` `USDT` `binance` / `trade` / `in` qty `508.9158` delta `508.9158` tx `binance-trade-24:in:USDT`
- `2021-12-17T23:16:00+00:00` `USDT` `binance` / `trade` / `in` qty `1446.676` delta `1446.676` tx `binance-trade-27:in:USDT`
- `2021-12-17T23:16:00+00:00` `HNT` `binance` / `trade` / `out` qty `18.5` delta `-18.5` tx `binance-trade-29:out:HNT`
- `2021-12-17T23:16:00+00:00` `HNT` `binance` / `trade` / `out` qty `1.63` delta `-1.63` tx `binance-trade-28:out:HNT`
- `2021-12-17T23:16:00+00:00` `HNT` `binance` / `trade` / `out` qty `15.03` delta `-15.03` tx `binance-trade-24:out:HNT`
- `2021-12-17T23:16:00+00:00` `HNT` `binance` / `trade` / `out` qty `42.7` delta `-42.7` tx `binance-trade-27:out:HNT`
- `2021-12-17T23:16:00+00:00` `HNT` `binance` / `trade` / `out` qty `21.1` delta `-21.1` tx `binance-trade-25:out:HNT`
- `2021-12-17T23:16:00+00:00` `HNT` `binance` / `trade` / `out` qty `1.21` delta `-1.21` tx `binance-trade-26:out:HNT`
- `2021-12-20T14:36:04+00:00` `HNT` `binance` / `trade` / `in` qty `1` delta `1` tx `binance-trade-23:in:HNT`
- `2021-12-20T14:36:04+00:00` `USDT` `binance` / `trade` / `out` qty `31.24` delta `-31.24` tx `binance-trade-23:out:USDT`
- `2021-12-20T14:36:05+00:00` `HNT` `binance` / `trade` / `in` qty `44.57` delta `44.57` tx `binance-trade-22:in:HNT`
- `2021-12-20T14:36:05+00:00` `HNT` `binance` / `trade` / `in` qty `18` delta `18` tx `binance-trade-20:in:HNT`
- `2021-12-20T14:36:05+00:00` `HNT` `binance` / `trade` / `in` qty `6.36` delta `6.36` tx `binance-trade-17:in:HNT`
- `2021-12-20T14:36:05+00:00` `HNT` `binance` / `trade` / `in` qty `18.38` delta `18.38` tx `binance-trade-21:in:HNT`
- `2021-12-20T14:36:05+00:00` `HNT` `binance` / `trade` / `in` qty `15.16` delta `15.16` tx `binance-trade-18:in:HNT`
- `2021-12-20T14:36:05+00:00` `HNT` `binance` / `trade` / `in` qty `5.05` delta `5.05` tx `binance-trade-19:in:HNT`
- `2021-12-20T14:36:05+00:00` `USDT` `binance` / `trade` / `out` qty `574.1912` delta `-574.1912` tx `binance-trade-21:out:USDT`
- `2021-12-20T14:36:05+00:00` `USDT` `binance` / `trade` / `out` qty `1392.3668` delta `-1392.3668` tx `binance-trade-22:out:USDT`
- `2021-12-20T14:36:05+00:00` `USDT` `binance` / `trade` / `out` qty `157.762` delta `-157.762` tx `binance-trade-19:out:USDT`
- `2021-12-20T14:36:05+00:00` `USDT` `binance` / `trade` / `out` qty `198.6864` delta `-198.6864` tx `binance-trade-17:out:USDT`
- `2021-12-20T14:36:05+00:00` `USDT` `binance` / `trade` / `out` qty `562.32` delta `-562.32` tx `binance-trade-20:out:USDT`
- `2021-12-20T14:36:05+00:00` `USDT` `binance` / `trade` / `out` qty `473.5984` delta `-473.5984` tx `binance-trade-18:out:USDT`
- `2021-12-20T21:28:06+00:00` `USDT` `binance` / `trade` / `in` qty `1851.289` delta `1851.289` tx `binance-trade-16:in:USDT`
- `2021-12-20T21:28:06+00:00` `USDT` `binance` / `trade` / `in` qty `1558.711` delta `1558.711` tx `binance-trade-15:in:USDT`
- `2021-12-20T21:28:06+00:00` `HNT` `binance` / `trade` / `out` qty `45.71` delta `-45.71` tx `binance-trade-15:out:HNT`
- `2021-12-20T21:28:06+00:00` `HNT` `binance` / `trade` / `out` qty `54.29` delta `-54.29` tx `binance-trade-16:out:HNT`
- `2021-12-21T06:45:16+00:00` `USDT` `binance` / `trade` / `in` qty `297.8176` delta `297.8176` tx `binance-trade-14:in:USDT`
- `2021-12-21T06:45:16+00:00` `HNT` `binance` / `trade` / `out` qty `8.48` delta `-8.48` tx `binance-trade-14:out:HNT`
- `2021-12-23T18:22:53+00:00` `HNT` `binance` / `trade` / `in` qty `0.53` delta `0.53` tx `binance-trade-13:in:HNT`
- `2021-12-23T18:22:53+00:00` `USDT` `binance` / `trade` / `out` qty `21.4597` delta `-21.4597` tx `binance-trade-13:out:USDT`
- `2021-12-23T18:23:02+00:00` `HNT` `binance` / `trade` / `in` qty `90.95` delta `90.95` tx `binance-trade-12:in:HNT`
- `2021-12-23T18:23:02+00:00` `USDT` `binance` / `trade` / `out` qty `3682.5655` delta `-3682.5655` tx `binance-trade-12:out:USDT`
- `2021-12-25T07:30:13+00:00` `USDT` `binance` / `trade` / `in` qty `164.6931` delta `164.6931` tx `binance-trade-11:in:USDT`
- `2021-12-25T07:30:13+00:00` `USDT` `binance` / `trade` / `in` qty `596.1967` delta `596.1967` tx `binance-trade-10:in:USDT`
- `2021-12-25T07:30:13+00:00` `HNT` `binance` / `trade` / `out` qty `15.53` delta `-15.53` tx `binance-trade-10:out:HNT`
- `2021-12-25T07:30:13+00:00` `HNT` `binance` / `trade` / `out` qty `4.29` delta `-4.29` tx `binance-trade-11:out:HNT`
- `2021-12-25T07:30:17+00:00` `USDT` `binance` / `trade` / `in` qty `691.02` delta `691.02` tx `binance-trade-9:in:USDT`
- `2021-12-25T07:30:17+00:00` `HNT` `binance` / `trade` / `out` qty `18` delta `-18` tx `binance-trade-9:out:HNT`
- `2021-12-25T07:30:18+00:00` `USDT` `binance` / `trade` / `in` qty `302.1293` delta `302.1293` tx `binance-trade-8:in:USDT`
- `2021-12-25T07:30:18+00:00` `HNT` `binance` / `trade` / `out` qty `7.87` delta `-7.87` tx `binance-trade-8:out:HNT`
- `2021-12-25T16:19:40+00:00` `USDT` `binance_api` / `withdrawal` / `out` qty `200` delta `-200` tx `b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182`
- `2021-12-25T16:23:04+00:00` `USDT` `pionex` / `deposit` / `in` qty `200.00000000` delta `200.00000000` tx `b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182`
- `2021-12-25T16:25:25+00:00` `HNT` `pionex` / `trade` / `in` qty `2.78700000000000000000` delta `2.78700000000000000000` tx `s_1:0:in:HNT`
- `2021-12-25T16:25:25+00:00` `USDT` `pionex` / `trade` / `out` qty `105.04272100000000000000` delta `-105.04272100000000000000` tx `s_1:0:out:USDT`
- `2021-12-25T16:25:25+00:00` `HNT` `pionex` / `fee` / `out` qty `0.00139350` delta `-0.00139350` tx `s_1:0:fee:HNT`
- `2021-12-25T16:35:00+00:00` `HNT` `pionex` / `trade` / `in` qty `0.49700000000000000000` delta `0.49700000000000000000` tx `s_2:1:in:HNT`
- `2021-12-25T16:35:00+00:00` `USDT` `pionex` / `trade` / `out` qty `18.64692000000000000000` delta `-18.64692000000000000000` tx `s_2:1:out:USDT`
- `2021-12-25T16:35:00+00:00` `HNT` `pionex` / `fee` / `out` qty `0.00024850` delta `-0.00024850` tx `s_2:1:fee:HNT`
- `2021-12-25T16:35:01+00:00` `USDT` `pionex` / `trade` / `in` qty `8.65800000000000000000` delta `8.65800000000000000000` tx `s_2:2:in:USDT`
- `2021-12-25T16:35:01+00:00` `HNT` `pionex` / `trade` / `out` qty `0.22200000000000000000` delta `-0.22200000000000000000` tx `s_2:2:out:HNT`
- `2021-12-25T16:35:01+00:00` `USDT` `pionex` / `fee` / `out` qty `0.00432900` delta `-0.00432900` tx `s_2:2:fee:USDT`
- `2021-12-25T22:40:52+00:00` `USDT` `pionex` / `trade` / `in` qty `37.21436500000000000000` delta `37.21436500000000000000` tx `s_1:3:in:USDT`
- `2021-12-25T22:40:52+00:00` `HNT` `pionex` / `trade` / `out` qty `0.94000000000000000000` delta `-0.94000000000000000000` tx `s_1:3:out:HNT`
- `2021-12-25T22:40:52+00:00` `USDT` `pionex` / `fee` / `out` qty `0.01860720` delta `-0.01860720` tx `s_1:3:fee:USDT`

## Bewertung

- Direct HNT-to-Pionex deposit is not supported by the current Pionex deposit/withdraw CSV; Pionex deposits are USDT only in the early period.
- The chain HNT legacy/staking -> Binance is directly supported by matching HNT legacy transfer and Binance HNT deposit txid on 2021-12-13.
- The chain Binance HNT -> USDT is supported by Binance HNT trade-out and USDT trade-in rows, especially 2021-12-17 and 2021-12-25.
- The chain Binance USDT -> Pionex is directly supported by identical TXIDs for Binance withdrawals and Pionex deposits.
- This explains the source of visible Pionex funding, but it does not fully remove the remaining current global transient USDT gap of 125.5260918462 USDT.
