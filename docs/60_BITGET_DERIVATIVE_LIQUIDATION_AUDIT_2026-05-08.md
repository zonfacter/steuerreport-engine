# Bitget Derivative Liquidation Audit - 2026-05-08

## Scope

- Zeitraum: `Bitget derivative/liquidation window 2025-02-20..2025-03-05`
- JSON: `/workspace/steuerreport/var/bitget_derivative_liquidation_audit_2026-05-08.json`
- Rows: `405`
- Primary: `405`
- Reference: `0`
- Sources: `{"bitget_tax_api": 405}`

## Primaer-Summen

- Net by class: `{"close_position_pnl_fee": "310.36085227", "funding_or_settlement_fee": "-0.85589026", "liquidation_loss": "-403.38455169", "open_position_fee_only": "-313.31898887", "risk_capital_transfer": "-222.10227813", "strategy_transfer": "-1.21024890"}`
- Net by symbol: `{"": "-1.21024890", "BTCUSDT": "-629.06029039", "HNTUSDT": "-557.11543831", "JUPUSDT": "568.15392062", "SOLUSDT": "-16.56127526", "XRPUSDT": "5.28222666"}`
- Net by day: `{"2025-02-20": "4.18475379", "2025-02-21": "143.18887837", "2025-02-22": "-126.72389879", "2025-02-23": "68.83118164", "2025-02-24": "418.45414217", "2025-02-25": "10.12785837", "2025-02-26": "-161.14993313", "2025-02-27": "-987.42408800"}`
- Gross by business: `{"burst_long_loss_query": "-396.16940001", "close_long": "664.98454785", "close_short": "-47.78238012", "contract_settle_fee": "-0.85589026", "open_long": "0", "open_short": "0", "risk_captital_user_transfer": "-222.10227813", "trans_from_strategy": "248.38877526", "trans_to_strategy": "-249.59902416"}`
- Fees by business: `{"burst_long_loss_query": "-7.21515168", "close_long": "-156.30382540", "close_short": "-150.53749006", "contract_settle_fee": "0", "open_long": "-162.81016825", "open_short": "-150.50882062", "risk_captital_user_transfer": "0", "trans_from_strategy": "0", "trans_to_strategy": "0"}`
- Blockpit reference fee quantity total: `0`

## Loss / Risk Capital

- LOSS `2025-02-27T15:01:18.007000+00:00` `HNTUSDT` gross `-396.16940001` fee `-7.21515168` effect `-403.38455169` balance `222.10227813` id `1279021787983282179`
- RISK `2025-02-27T15:01:19.616000+00:00` gross `-222.10227813` effect `-222.10227813` balance `0` id `1279021794731917356`

## Focus Timeline

| Zeit | Typ | Business | Symbol | Gross | Fee | Effect | Balance |
|---|---|---|---|---:|---:|---:|---:|
| `2025-02-22T00:00:10.203000+00:00` | `derivative fee` | `contract_settle_fee` | `JUPUSDT` | `0.14892067` | `0` | `0.14892067` | `778.03365835` |
| `2025-02-22T04:00:04.359000+00:00` | `derivative fee` | `contract_settle_fee` | `JUPUSDT` | `-0.30289587` | `0` | `-0.30289587` | `777.73076247` |
| `2025-02-22T05:27:27.419000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-14.7` | `-0.71919` | `-15.41919` | `762.31157247` |
| `2025-02-22T05:27:27.420000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-3.75` | `-0.1798425` | `-3.9298425` | `758.38172997` |
| `2025-02-22T05:27:27.420000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-1.63` | `-0.07817154` | `-1.70817154` | `756.67355843` |
| `2025-02-22T05:27:27.420000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-2.34` | `-0.11222172` | `-2.45222172` | `754.22133671` |
| `2025-02-22T05:27:27.420000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-1.97` | `-0.09447726` | `-2.06447726` | `752.15685945` |
| `2025-02-22T05:27:27.420000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-2.22` | `-0.10646676` | `-2.32646676` | `749.83039269` |
| `2025-02-22T05:27:27.420000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-1.8` | `-0.0863244` | `-1.8863244` | `747.94406829` |
| `2025-02-22T05:27:27.420000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-4.5` | `-0.215811` | `-4.715811` | `743.22825729` |
| `2025-02-22T05:27:27.420000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-1.99` | `-0.09543642` | `-2.08543642` | `741.14282087` |
| `2025-02-22T05:27:27.421000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-2.99` | `-0.14339442` | `-3.13339442` | `738.00942645` |
| `2025-02-22T05:27:27.421000+00:00` | `derivative close_short` | `close_short` | `JUPUSDT` | `-0.82` | `-0.03932556` | `-0.85932556` | `737.15010089` |
| `2025-02-22T05:31:15.652000+00:00` | `transfer` | `trans_to_strategy` | `` | `-249.59902416` | `0` | `-249.59902416` | `487.55107673` |
| `2025-02-22T06:48:16.170000+00:00` | `derivative open_long` | `open_long` | `BTCUSDT` | `0` | `-0.27181782` | `-0.27181782` | `487.27925891` |
| `2025-02-22T06:48:16.170000+00:00` | `derivative open_long` | `open_long` | `BTCUSDT` | `0` | `-3.74793868` | `-3.74793868` | `483.53132022` |
| `2025-02-22T06:50:09.075000+00:00` | `derivative close_long` | `close_long` | `BTCUSDT` | `-0.24594` | `-4.01960895` | `-4.26554895` | `479.26577127` |
| `2025-02-22T07:55:31.643000+00:00` | `derivative open_short` | `open_short` | `SOLUSDT` | `0` | `-1.7006418` | `-1.7006418` | `477.56512947` |
| `2025-02-22T08:00:13.380000+00:00` | `derivative fee` | `contract_settle_fee` | `SOLUSDT` | `-0.1927596` | `0` | `-0.1927596` | `477.37236987` |
| `2025-02-22T16:00:07.689000+00:00` | `derivative fee` | `contract_settle_fee` | `SOLUSDT` | `-0.18975389` | `0` | `-0.18975389` | `477.18261598` |
| `2025-02-22T17:09:10.529000+00:00` | `derivative close_short` | `close_short` | `SOLUSDT` | `-15.1164` | `-1.61694936` | `-16.73334936` | `460.44926662` |
| `2025-02-22T17:09:53.936000+00:00` | `transfer` | `trans_from_strategy` | `` | `248.38877526` | `0` | `248.38877526` | `708.83804188` |
| `2025-02-22T17:10:32.575000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.34359408` | `-0.34359408` | `708.4944478` |
| `2025-02-22T17:10:32.576000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.08589852` | `-0.08589852` | `708.40854928` |
| `2025-02-22T17:10:32.576000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.179955` | `-0.179955` | `708.22859428` |
| `2025-02-22T17:10:32.576000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.71982` | `-0.71982` | `707.50877428` |
| `2025-02-22T17:10:32.576000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.02831292` | `-0.02831292` | `707.48046136` |
| `2025-02-22T17:10:32.576000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.01871532` | `-0.01871532` | `707.46174604` |
| `2025-02-22T17:10:32.576000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.18811296` | `-0.18811296` | `707.27363308` |
| `2025-02-22T17:10:32.576000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.11565108` | `-0.11565108` | `707.157982` |
| `2025-02-22T17:10:32.576000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.0527868` | `-0.0527868` | `707.1051952` |
| `2025-02-22T17:10:32.576000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.18091476` | `-0.18091476` | `706.92428044` |
| `2025-02-22T17:10:32.576000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.0455886` | `-0.0455886` | `706.87869184` |
| `2025-02-22T17:10:32.577000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.17467632` | `-0.17467632` | `706.70401552` |
| `2025-02-22T17:10:32.577000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.10845288` | `-0.10845288` | `706.59556264` |
| `2025-02-22T17:10:32.577000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.03407148` | `-0.03407148` | `706.56149116` |
| `2025-02-22T17:10:32.577000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.10605348` | `-0.10605348` | `706.45543768` |
| `2025-02-22T17:10:32.577000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.03887028` | `-0.03887028` | `706.4165674` |
| `2025-02-22T17:11:47.326000+00:00` | `derivative open_long` | `open_long` | `JUPUSDT` | `0` | `-0.109641` | `-0.109641` | `706.3069264` |
| `2025-02-22T20:00:04.780000+00:00` | `derivative fee` | `contract_settle_fee` | `JUPUSDT` | `0.32615614` | `0` | `0.32615614` | `706.63308254` |
| `2025-02-22T21:10:31.177000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-3.50308408` | `-0.17262336` | `-3.67570744` | `702.95737509` |
| `2025-02-22T21:10:31.177000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-4.1767541` | `-0.20582016` | `-4.38257426` | `698.57480082` |
| `2025-02-22T21:10:31.177000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-4.96591041` | `-0.24470784` | `-5.21061825` | `693.36418257` |
| `2025-02-22T21:10:31.177000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-3.70518509` | `-0.1825824` | `-3.88776749` | `689.47641508` |
| `2025-02-22T21:10:31.177000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-0.82765173` | `-0.04078464` | `-0.86843637` | `688.6079787` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-1.02012888` | `-0.05026944` | `-1.07039832` | `687.53758038` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-2.16536791` | `-0.106704` | `-2.27207191` | `685.26550847` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-4.19600182` | `-0.20676864` | `-4.40277046` | `680.86273801` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-3.5223318` | `-0.17357184` | `-3.69590364` | `677.16683436` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-3.90728609` | `-0.19254144` | `-4.09982753` | `673.06700682` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-3.92653381` | `-0.19348992` | `-4.12002373` | `668.94698309` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-1.05862431` | `-0.0521664` | `-1.11079071` | `667.83619238` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-4.41735054` | `-0.21767616` | `-4.63502670` | `663.20116568` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-4.98515812` | `-0.24565632` | `-5.23081444` | `657.97035123` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-4.1093871` | `-0.20250048` | `-4.31188758` | `653.65846365` |
| `2025-02-22T21:10:31.178000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `-0.25984414` | `-0.01280448` | `-0.27264862` | `653.38581502` |
| `2025-02-22T21:10:31.225000+00:00` | `derivative open_short` | `open_short` | `JUPUSDT` | `0` | `-0.09057984` | `-0.09057984` | `653.29523518` |
| `2025-02-22T21:10:31.226000+00:00` | `derivative open_short` | `open_short` | `JUPUSDT` | `0` | `-0.11713728` | `-0.11713728` | `653.1780979` |
| `2025-02-22T21:10:31.226000+00:00` | `derivative open_short` | `open_short` | `JUPUSDT` | `0` | `-0.05833152` | `-0.05833152` | `653.11976638` |
| `2025-02-22T21:10:31.226000+00:00` | `derivative open_short` | `open_short` | `JUPUSDT` | `0` | `-0.71136` | `-0.71136` | `652.40840638` |
| `2025-02-22T21:10:31.226000+00:00` | `derivative open_short` | `open_short` | `JUPUSDT` | `0` | `-1.24756758` | `-1.24756758` | `651.1608388` |
| `2025-02-27T00:00:11.019000+00:00` | `derivative fee` | `contract_settle_fee` | `BTCUSDT` | `-1.03080266` | `0` | `-1.03080266` | `986.39328521` |
| `2025-02-27T00:00:12.996000+00:00` | `derivative fee` | `contract_settle_fee` | `JUPUSDT` | `0.03897363` | `0` | `0.03897363` | `986.43225884` |
| `2025-02-27T04:00:02.774000+00:00` | `derivative fee` | `contract_settle_fee` | `JUPUSDT` | `-0.30299766` | `0` | `-0.30299766` | `986.12926118` |
| `2025-02-27T05:08:37.114000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `3.19751272` | `-0.1938969` | `3.00361582` | `989.13287701` |
| `2025-02-27T05:08:37.114000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `3.15381272` | `-0.19387068` | `2.95994204` | `992.09281906` |
| `2025-02-27T05:08:37.115000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `3.15381272` | `-0.19387068` | `2.95994204` | `995.05276111` |
| `2025-02-27T05:08:37.115000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `1.7248541` | `-0.10602996` | `1.61882414` | `996.67158525` |
| `2025-02-27T05:08:37.115000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `4.92918556` | `-0.30300612` | `4.62617944` | `1001.29776469` |
| `2025-02-27T05:08:37.115000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `2.12900401` | `-0.1308738` | `1.99813021` | `1003.29589491` |
| `2025-02-27T05:08:37.115000+00:00` | `derivative close_long` | `close_long` | `JUPUSDT` | `11.41001812` | `-0.70139484` | `10.70862328` | `1014.0045182` |
| `2025-02-27T05:09:30.289000+00:00` | `derivative close_long` | `close_long` | `BTCUSDT` | `81.53308999` | `-5.86119019` | `75.67189980` | `1089.67641801` |
| `2025-02-27T05:10:01.840000+00:00` | `derivative open_long` | `open_long` | `BTCUSDT` | `0` | `-19.58274405` | `-19.58274405` | `1070.09367396` |
| `2025-02-27T05:10:45.063000+00:00` | `derivative open_long` | `open_long` | `HNTUSDT` | `0` | `-0.1267257` | `-0.1267257` | `1069.96694826` |
| `2025-02-27T05:10:45.063000+00:00` | `derivative open_long` | `open_long` | `HNTUSDT` | `0` | `-0.03598254` | `-0.03598254` | `1069.93096572` |
| `2025-02-27T05:10:45.063000+00:00` | `derivative open_long` | `open_long` | `HNTUSDT` | `0` | `-0.057726` | `-0.057726` | `1069.87323972` |
| `2025-02-27T05:10:45.063000+00:00` | `derivative open_long` | `open_long` | `HNTUSDT` | `0` | `-0.03599376` | `-0.03599376` | `1069.83724596` |
| `2025-02-27T05:10:45.063000+00:00` | `derivative open_long` | `open_long` | `HNTUSDT` | `0` | `-0.057744` | `-0.057744` | `1069.77950196` |
| `2025-02-27T05:10:45.064000+00:00` | `derivative open_long` | `open_long` | `HNTUSDT` | `0` | `-0.03600498` | `-0.03600498` | `1069.74349698` |
| `2025-02-27T05:10:45.064000+00:00` | `derivative open_long` | `open_long` | `HNTUSDT` | `0` | `-0.057762` | `-0.057762` | `1069.68573498` |

## Interpretation

- Open-long/open-short rows have gross amount 0 and balance effect equals fee only; they are not leveraged notional movements.
- Close-long/close-short rows carry realized PnL amount plus fee and are balance-relevant settlement rows.
- The 2025-02-27 loss row is a Bitget primary liquidation/loss-style row: burst_long_loss_query on HNTUSDT.
- The 2025-02-27 risk_captital_user_transfer row moves remaining USDT after the loss area and should be documented as transfer/risk-capital movement, not a synthetic trade.
- Blockpit rows in this window are reference-only and must not be added on top of Bitget primary rows unless unmatched.
