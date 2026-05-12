# Pionex USDT Platform Gap Current - 2026-05-09

## Ergebnis

- Aktive Pionex/USDT-Ledgerzeilen: `906`
- Finaler Pionex/USDT-Saldo: `0.8913798065261125`
- Erster negativer Stand: `2021-12-28T00:49:12+00:00` Ledger `pl-00007040` TX `s_3:13:out:USDT` nach `-13.53043343`
- Schlimmster Stand: `2022-01-19T12:56:19+00:00` Ledger `pl-00008275` TX `s_11:68:out:USDT` nach `-1643.2312211162`
- Opening noetig ab erstem Bruch: `13.53043343 USDT`
- Opening noetig, damit Pionex nie negativ wird: `1643.2312211162 USDT`
- Negative Segmente: `36`

## Bewertung

- Pionex USDT is a platform-local bot/opening-capital gap, not a single missing on-chain transfer.
- The first negative balance starts before the 2022-01-19 large deposit window.
- The worst point follows a Pionex trade-out shortly after the visible 1245.38419 USDT deposit.
- Do not create a tax-effective synthetic opening balance without Pionex evidence or an explicit review decision.

## Worst Window 2022-01-19

- `2022-01-19T12:45:42+00:00` `pl-00008256` `trade` delta `-479.99307717000000000000` before `163.5314868238` after `-316.4615903462` tx `s_10:67:out:USDT`
- `2022-01-19T12:54:09+00:00` `pl-00008273` `deposit` delta `1245.38419000` before `-316.4615903462` after `928.9225996538` tx `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`
- `2022-01-19T12:56:19+00:00` `pl-00008275` `trade` delta `-2572.15382077000000000000` before `928.9225996538` after `-1643.2312211162` tx `s_11:68:out:USDT`
- `2022-01-19T23:28:01+00:00` `pl-00008292` `trade` delta `348.69293954000000000000` before `-1643.2312211162` after `-1294.5382815762` tx `s_10:69:in:USDT`
- `2022-01-19T23:28:01+00:00` `pl-00008294` `fee` delta `-0.17434645` before `-1294.5382815762` after `-1294.7126280262` tx `s_10:69:fee:USDT`
- `2022-01-19T23:50:25+00:00` `pl-00008295` `trade` delta `1402.62272436000000000000` before `-1294.7126280262` after `107.9100963338` tx `s_11:70:in:USDT`
- `2022-01-19T23:50:25+00:00` `pl-00008297` `fee` delta `-0.70131096` before `107.9100963338` after `107.2087853738` tx `s_11:70:fee:USDT`

## Early Window 2021-12-25 bis 2021-12-29

- `2021-12-25T16:23:04+00:00` `pl-00006884` `deposit` delta `200.00000000` before `0` after `200` tx `b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182`
- `2021-12-25T16:25:25+00:00` `pl-00006886` `trade` delta `-105.04272100000000000000` before `200` after `94.957279` tx `s_1:0:out:USDT`
- `2021-12-25T16:35:00+00:00` `pl-00006889` `trade` delta `-18.64692000000000000000` before `94.957279` after `76.310359` tx `s_2:1:out:USDT`
- `2021-12-25T16:35:01+00:00` `pl-00006891` `trade` delta `8.65800000000000000000` before `76.310359` after `84.968359` tx `s_2:2:in:USDT`
- `2021-12-25T16:35:01+00:00` `pl-00006893` `fee` delta `-0.00432900` before `84.968359` after `84.96403` tx `s_2:2:fee:USDT`
- `2021-12-25T22:40:52+00:00` `pl-00006903` `trade` delta `37.21436500000000000000` before `84.96403` after `122.178395` tx `s_1:3:in:USDT`
- `2021-12-25T22:40:52+00:00` `pl-00006905` `fee` delta `-0.01860720` before `122.178395` after `122.1597878` tx `s_1:3:fee:USDT`
- `2021-12-26T02:37:41+00:00` `pl-00006917` `trade` delta `8.43600000000000000000` before `122.1597878` after `130.5957878` tx `s_2:4:in:USDT`
- `2021-12-26T02:37:41+00:00` `pl-00006919` `fee` delta `-0.00421800` before `130.5957878` after `130.5915698` tx `s_2:4:fee:USDT`
- `2021-12-26T04:09:02+00:00` `pl-00006924` `trade` delta `-28.05274900000000000000` before `130.5915698` after `102.5388208` tx `s_1:5:out:USDT`
- `2021-12-26T23:15:21+00:00` `pl-00006954` `trade` delta `33.61181500000000000000` before `102.5388208` after `136.1506358` tx `s_1:6:in:USDT`
- `2021-12-26T23:15:21+00:00` `pl-00006956` `fee` delta `-0.01680590` before `136.1506358` after `136.1338299` tx `s_1:6:fee:USDT`
- `2021-12-27T00:14:41+00:00` `pl-00006966` `trade` delta `-67.92007600000000000000` before `136.1338299` after `68.2137539` tx `s_1:7:out:USDT`
- `2021-12-27T06:37:46+00:00` `pl-00006978` `trade` delta `2.11593200000000000000` before `68.2137539` after `70.3296859` tx `s_2:8:in:USDT`
- `2021-12-27T06:37:46+00:00` `pl-00006980` `fee` delta `-0.00105797` before `70.3296859` after `70.32862793` tx `s_2:8:fee:USDT`
- `2021-12-27T06:39:05+00:00` `pl-00006982` `trade` delta `-33.37424600000000000000` before `70.32862793` after `36.95438193` tx `s_3:9:out:USDT`
- `2021-12-27T23:52:20+00:00` `pl-00007020` `trade` delta `42.15867100000000000000` before `36.95438193` after `79.11305293` tx `s_1:10:in:USDT`
- `2021-12-27T23:52:20+00:00` `pl-00007022` `fee` delta `-0.02107936` before `79.11305293` after `79.09197357` tx `s_1:10:fee:USDT`
- `2021-12-27T23:53:22+00:00` `pl-00007023` `trade` delta `7.39800000000000000000` before `79.09197357` after `86.48997357` tx `s_3:11:in:USDT`
- `2021-12-27T23:53:22+00:00` `pl-00007025` `fee` delta `-0.00369900` before `86.48997357` after `86.48627457` tx `s_3:11:fee:USDT`
- `2021-12-28T00:12:17+00:00` `pl-00007036` `trade` delta `-83.99670800000000000000` before `86.48627457` after `2.48956657` tx `s_1:12:out:USDT`
- `2021-12-28T00:49:12+00:00` `pl-00007040` `trade` delta `-16.02000000000000000000` before `2.48956657` after `-13.53043343` tx `s_3:13:out:USDT`
- `2021-12-28T23:52:02+00:00` `pl-00007088` `trade` delta `109.52757800000000000000` before `-13.53043343` after `95.99714457` tx `s_1:14:in:USDT`
- `2021-12-28T23:52:02+00:00` `pl-00007090` `fee` delta `-0.05476382` before `95.99714457` after `95.94238075` tx `s_1:14:fee:USDT`
- `2021-12-28T23:59:30+00:00` `pl-00007091` `trade` delta `25.81200000000000000000` before `95.94238075` after `121.75438075` tx `s_3:15:in:USDT`
- `2021-12-28T23:59:30+00:00` `pl-00007093` `fee` delta `-0.01290600` before `121.75438075` after `121.74147475` tx `s_3:15:fee:USDT`
- `2021-12-29T00:07:06+00:00` `pl-00007107` `trade` delta `-107.30598200000000000000` before `121.74147475` after `14.43549275` tx `s_1:16:out:USDT`
- `2021-12-29T00:14:44+00:00` `pl-00007110` `trade` delta `-21.83400000000000000000` before `14.43549275` after `-7.39850725` tx `s_3:17:out:USDT`
- `2021-12-29T23:21:43+00:00` `pl-00007145` `trade` delta `18.07200000000000000000` before `-7.39850725` after `10.67349275` tx `s_3:18:in:USDT`
- `2021-12-29T23:21:43+00:00` `pl-00007147` `fee` delta `-0.00903600` before `10.67349275` after `10.66445675` tx `s_3:18:fee:USDT`
- `2021-12-29T23:46:45+00:00` `pl-00007149` `trade` delta `97.42192900000000000000` before `10.66445675` after `108.08638575` tx `s_1:19:in:USDT`
- `2021-12-29T23:46:45+00:00` `pl-00007151` `fee` delta `-0.04871103` before `108.08638575` after `108.03767472` tx `s_1:19:fee:USDT`

## Sichtbare Deposits bis Worst

- `2021-12-25T16:23:04+00:00` `deposit` `200.00000000 USDT` tx `b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182`
- `2022-01-19T12:54:09+00:00` `deposit` `1245.38419000 USDT` tx `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`

## Jahresnetto

`{'2021': '124.93443059', '2022': '-110.69275736536', '2023': '-14.2415341617', '2024': '0.8912407435861125'}`
