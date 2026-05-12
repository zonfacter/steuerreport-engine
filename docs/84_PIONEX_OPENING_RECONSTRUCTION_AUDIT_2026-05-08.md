# Pionex Opening Reconstruction Audit 2026-05-08

- JSON: `var/pionex_opening_reconstruction_audit_2026-05-08.json`
- Pionex-Export-Verzeichnis: `usertransfer/pionex`
- Pionex Events: `1801`
- Bewegungen: `1801`

## Ergebnis

- Erforderliches USDT-Opening, damit Pionex-only nie negativ wird: `1643.40556756620000000000`
- Erster USDT-Bruch: `2021-12-28T00:49:12+00:00 trade/out -16.02000000000000000000 USDT balance_after=-13.53043343000000000000 tx=s_3:13:out:USDT`
- Schlimmster USDT-Stand: `2022-01-19T23:28:01+00:00 fee/out -0.17434645 USDT balance_after=-1643.40556756620000000000 tx=s_10:69:fee:USDT`
- Status: `replacement_reconstruction_possible_but_not_primary_evidence`

Das ist eine belastbare Ersatzrekonstruktion aus den vorhandenen Exporten, aber weiterhin kein primaerer Konto-Snapshot. Deshalb bleibt der bestehende Review-Kandidat fachlich entscheidungspflichtig und `tax_effective=false`.

## Export-Dateien

- `usertransfer/pionex/deposit-withdraw.csv` (941 Bytes)
- `usertransfer/pionex/dust-collector.csv` (196 Bytes)
- `usertransfer/pionex/for-cointracker.csv` (66196 Bytes)
- `usertransfer/pionex/for-cointracking.csv` (82487 Bytes)
- `usertransfer/pionex/others.csv` (46 Bytes)
- `usertransfer/pionex/position_futures.csv` (90 Bytes)
- `usertransfer/pionex/raw-trading-details.csv` (1820151 Bytes)
- `usertransfer/pionex/staking.csv` (92 Bytes)
- `usertransfer/pionex/structured-products.csv` (86 Bytes)
- `usertransfer/pionex/trading.csv` (82678 Bytes)

## Pionex Deposits/Withdrawals und externe Tx-Matches

- `2021-12-25T16:23:04+00:00` `deposit` `in` `200.00000000 USDT` tx=`b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182` externe_matches=`2`
- `2022-01-19T12:54:09+00:00` `deposit` `in` `1245.38419000 USDT` tx=`b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa` externe_matches=`1`
- `2022-02-23T05:41:40+00:00` `deposit` `in` `696.82747400 USDT` tx=`a08ff362825ec9a4ce35a3f4803cf1dba32cf1deaae4fc58281001b6a0692566` externe_matches=`1`
- `2022-02-25T21:35:15+00:00` `deposit` `in` `983.69132300 USDT` tx=`9542656804be81094930fd1ddb83710f82c54fda18b2691c1ffd57b95d89a132` externe_matches=`1`
- `2023-06-09T16:19:26+00:00` `withdrawal` `out` `20530.34420000 MXC` tx=`0x049701b4cddcd5bd5a2f5d3339922d8f4d771543bf51d608738da5f117db2014` externe_matches=`0`
- `2024-11-22T16:14:05+00:00` `withdrawal` `out` `0.08995500 SOL` tx=`4yH7iwag7grZqxEpkWmNFYqKnRypzuPPkMXmwmuWTyUqXGTzwRdrXagsP9BitUftzanhC38FSWV5G8RZijG4JGy9` externe_matches=`1`

## USDT-Netto bis zum schlimmsten Bruch

- `trade` / `out`: `-4792.24756236960000000000 USDT`
- `trade` / `in`: `2053.17733315340000000000 USDT`
- `deposit` / `in`: `1445.38419000 USDT`
- `fee` / `out`: `-1.02658881 USDT`

## Tagesende USDT bis zum schlimmsten Bruch

- `2021-12-25`: Endbestand `122.15978780000000000000`, Minimum `0`
- `2021-12-26`: Endbestand `136.13382990000000000000`, Minimum `102.52201490000000000000`
- `2021-12-27`: Endbestand `86.48627457000000000000`, Minimum `36.93330257000000000000`
- `2021-12-28`: Endbestand `121.74147475000000000000`, Minimum `-13.58519725000000000000`
- `2021-12-29`: Endbestand `108.03767472000000000000`, Minimum `-7.39850725000000000000`
- `2021-12-30`: Endbestand `115.06998944000000000000`, Minimum `63.43920772000000000000`
- `2021-12-31`: Endbestand `124.93443059000000000000`, Minimum `83.21355244000000000000`
- `2022-01-01`: Endbestand `108.21530955000000000000`, Minimum `51.29142259000000000000`
- `2022-01-02`: Endbestand `28.43383383930000000000`, Minimum `21.16532600960000000000`
- `2022-01-03`: Endbestand `37.06292084800000000000`, Minimum `28.43240226930000000000`
- `2022-01-04`: Endbestand `37.15936387510000000000`, Minimum `20.30882057230000000000`
- `2022-01-05`: Endbestand `16.72975815380000000000`, Minimum `-147.69690684620000000000`
- `2022-01-06`: Endbestand `20.97506593380000000000`, Minimum `-11.48907984620000000000`
- `2022-01-07`: Endbestand `25.01601644380000000000`, Minimum `20.97506593380000000000`
- `2022-01-12`: Endbestand `4.76561721380000000000`, Minimum `-11.70683178620000000000`
- `2022-01-13`: Endbestand `4.84150508380000000000`, Minimum `-7.30865478620000000000`
- `2022-01-18`: Endbestand `157.08034869380000000000`, Minimum `4.76551144380000000000`
- `2022-01-19`: Endbestand `-1294.71262802620000000000`, Minimum `-1643.40556756620000000000`

## Bot-/Tax-ID-Gruppen bis zum schlimmsten Bruch

- tax_id `s_11` `MXC_USDT`: net `-2572.15382077000000000000 USDT`, movements `1`, `2022-01-19T12:56:19+00:00`..`2022-01-19T12:56:19+00:00`
- tax_id `-` `-`: net `1445.38419000 USDT`, movements `2`, `2021-12-25T16:23:04+00:00`..`2022-01-19T12:54:09+00:00`
- tax_id `s_10` `MXC_USDT`: net `-131.47448408000000000000 USDT`, movements `3`, `2022-01-19T12:45:42+00:00`..`2022-01-19T23:28:01+00:00`
- tax_id `s_7` `EGLD_USDT`: net `-42.56134008000000000000 USDT`, movements `16`, `2022-01-05T11:40:01+00:00`..`2022-01-18T10:30:41+00:00`
- tax_id `s_8` `MXC_USDT`: net `6.04706753000000000000 USDT`, movements `6`, `2022-01-18T10:32:14+00:00`..`2022-01-19T11:22:49+00:00`
- tax_id `s_6` `SHIB_USDT`: net `-4.36603271920000000000 USDT`, movements `11`, `2022-01-02T07:59:56+00:00`..`2022-01-05T11:39:12+00:00`
- tax_id `s_1` `HNT_USDT`: net `4.02497752000000000000 USDT`, movements `27`, `2021-12-25T16:25:25+00:00`..`2022-01-02T06:49:37+00:00`
- tax_id `s_5` `SHIB_USDT`: net `-0.89749458700000000000 USDT`, movements `11`, `2022-01-02T06:54:57+00:00`..`2022-01-05T11:39:22+00:00`
- tax_id `s_9` `MXC_USDT`: net `0.73163285000000000000 USDT`, movements `3`, `2022-01-19T11:34:54+00:00`..`2022-01-19T12:39:11+00:00`
- tax_id `s_2` `HNT_USDT`: net `0.55340703000000000000 USDT`, movements `7`, `2021-12-25T16:35:00+00:00`..`2021-12-27T06:37:46+00:00`
- tax_id `s_4` `HNT_USDT`: net `-0.07185967000000000000 USDT`, movements `3`, `2022-01-02T06:52:26+00:00`..`2022-01-02T07:58:22+00:00`
- tax_id `s_3` `HNT_USDT`: net `0.07112895000000000000 USDT`, movements `20`, `2021-12-27T06:39:05+00:00`..`2022-01-02T06:53:36+00:00`

## Erste USDT-Bewegungen

- `2021-12-25T16:23:04+00:00` `deposit` `in` `200.00000000 USDT` tx=`b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182` tax_id=``
- `2021-12-25T16:25:25+00:00` `trade` `out` `-105.04272100000000000000 USDT` tx=`s_1:0:out:USDT` tax_id=`s_1`
- `2021-12-25T16:35:00+00:00` `trade` `out` `-18.64692000000000000000 USDT` tx=`s_2:1:out:USDT` tax_id=`s_2`
- `2021-12-25T16:35:01+00:00` `trade` `in` `8.65800000000000000000 USDT` tx=`s_2:2:in:USDT` tax_id=`s_2`
- `2021-12-25T16:35:01+00:00` `fee` `out` `-0.00432900 USDT` tx=`s_2:2:fee:USDT` tax_id=`s_2`
- `2021-12-25T22:40:52+00:00` `fee` `out` `-0.01860720 USDT` tx=`s_1:3:fee:USDT` tax_id=`s_1`
- `2021-12-25T22:40:52+00:00` `trade` `in` `37.21436500000000000000 USDT` tx=`s_1:3:in:USDT` tax_id=`s_1`
- `2021-12-26T02:37:41+00:00` `trade` `in` `8.43600000000000000000 USDT` tx=`s_2:4:in:USDT` tax_id=`s_2`
- `2021-12-26T02:37:41+00:00` `fee` `out` `-0.00421800 USDT` tx=`s_2:4:fee:USDT` tax_id=`s_2`
- `2021-12-26T04:09:02+00:00` `trade` `out` `-28.05274900000000000000 USDT` tx=`s_1:5:out:USDT` tax_id=`s_1`
- `2021-12-26T23:15:21+00:00` `fee` `out` `-0.01680590 USDT` tx=`s_1:6:fee:USDT` tax_id=`s_1`
- `2021-12-26T23:15:21+00:00` `trade` `in` `33.61181500000000000000 USDT` tx=`s_1:6:in:USDT` tax_id=`s_1`
- `2021-12-27T00:14:41+00:00` `trade` `out` `-67.92007600000000000000 USDT` tx=`s_1:7:out:USDT` tax_id=`s_1`
- `2021-12-27T06:37:46+00:00` `trade` `in` `2.11593200000000000000 USDT` tx=`s_2:8:in:USDT` tax_id=`s_2`
- `2021-12-27T06:37:46+00:00` `fee` `out` `-0.00105797 USDT` tx=`s_2:8:fee:USDT` tax_id=`s_2`
- `2021-12-27T06:39:05+00:00` `trade` `out` `-33.37424600000000000000 USDT` tx=`s_3:9:out:USDT` tax_id=`s_3`
- `2021-12-27T23:52:20+00:00` `fee` `out` `-0.02107936 USDT` tx=`s_1:10:fee:USDT` tax_id=`s_1`
- `2021-12-27T23:52:20+00:00` `trade` `in` `42.15867100000000000000 USDT` tx=`s_1:10:in:USDT` tax_id=`s_1`
- `2021-12-27T23:53:22+00:00` `trade` `in` `7.39800000000000000000 USDT` tx=`s_3:11:in:USDT` tax_id=`s_3`
- `2021-12-27T23:53:22+00:00` `fee` `out` `-0.00369900 USDT` tx=`s_3:11:fee:USDT` tax_id=`s_3`
- `2021-12-28T00:12:17+00:00` `trade` `out` `-83.99670800000000000000 USDT` tx=`s_1:12:out:USDT` tax_id=`s_1`
- `2021-12-28T00:49:12+00:00` `trade` `out` `-16.02000000000000000000 USDT` tx=`s_3:13:out:USDT` tax_id=`s_3`
- `2021-12-28T23:52:02+00:00` `fee` `out` `-0.05476382 USDT` tx=`s_1:14:fee:USDT` tax_id=`s_1`
- `2021-12-28T23:52:02+00:00` `trade` `in` `109.52757800000000000000 USDT` tx=`s_1:14:in:USDT` tax_id=`s_1`
- `2021-12-28T23:59:30+00:00` `fee` `out` `-0.01290600 USDT` tx=`s_3:15:fee:USDT` tax_id=`s_3`
- `2021-12-28T23:59:30+00:00` `trade` `in` `25.81200000000000000000 USDT` tx=`s_3:15:in:USDT` tax_id=`s_3`
- `2021-12-29T00:07:06+00:00` `trade` `out` `-107.30598200000000000000 USDT` tx=`s_1:16:out:USDT` tax_id=`s_1`
- `2021-12-29T00:14:44+00:00` `trade` `out` `-21.83400000000000000000 USDT` tx=`s_3:17:out:USDT` tax_id=`s_3`
- `2021-12-29T23:21:43+00:00` `trade` `in` `18.07200000000000000000 USDT` tx=`s_3:18:in:USDT` tax_id=`s_3`
- `2021-12-29T23:21:43+00:00` `fee` `out` `-0.00903600 USDT` tx=`s_3:18:fee:USDT` tax_id=`s_3`
- `2021-12-29T23:46:45+00:00` `fee` `out` `-0.04871103 USDT` tx=`s_1:19:fee:USDT` tax_id=`s_1`
- `2021-12-29T23:46:45+00:00` `trade` `in` `97.42192900000000000000 USDT` tx=`s_1:19:in:USDT` tax_id=`s_1`
- `2021-12-30T00:05:29+00:00` `trade` `out` `-36.60646700000000000000 USDT` tx=`s_1:20:out:USDT` tax_id=`s_1`
- `2021-12-30T00:05:43+00:00` `trade` `out` `-7.99200000000000000000 USDT` tx=`s_3:21:out:USDT` tax_id=`s_3`
- `2021-12-30T14:19:02+00:00` `trade` `in` `9.46800000000000000000 USDT` tx=`s_3:22:in:USDT` tax_id=`s_3`
- `2021-12-30T14:19:02+00:00` `fee` `out` `-0.00473400 USDT` tx=`s_3:22:fee:USDT` tax_id=`s_3`
- `2021-12-30T22:44:51+00:00` `trade` `in` `42.18861000000000000000 USDT` tx=`s_1:23:in:USDT` tax_id=`s_1`
- `2021-12-30T22:44:51+00:00` `fee` `out` `-0.02109428 USDT` tx=`s_1:23:fee:USDT` tax_id=`s_1`
- `2021-12-31T01:24:12+00:00` `trade` `out` `-26.43435100000000000000 USDT` tx=`s_1:24:out:USDT` tax_id=`s_1`
- `2021-12-31T08:37:53+00:00` `trade` `out` `-5.41800000000000000000 USDT` tx=`s_3:25:out:USDT` tax_id=`s_3`

## Schlussfolgerung

- `Der exportierte Trade-/Deposit-Strom ist intern konsistent und die aktuellen API-Balances passen eng zum CSV-Modell, aber es gibt keinen expliziten Pionex-Kontosnapshot vor den ersten Bot-Trades.`
- Empfohlene Review-Aktion: `Kandidat tax_effective=false lassen, bis eine Pionex-Abrechnung vorliegt oder die Ersatzrekonstruktion fachlich freigegeben wird.`
