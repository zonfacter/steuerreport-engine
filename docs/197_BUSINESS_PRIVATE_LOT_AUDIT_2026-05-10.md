# Betriebsvermoegen vs Privatvermoegen Lot-Audit

Stand: 2026-05-10

## Ergebnis

- Status: `read_only_audit`
- Offene Business-Assets: `11`
- Offene Private-Assets: `40`
- Assets mit gemischten offenen Lots: `8`
- Verkaeufe/Swaps aus Business-Origin-Lots: `28794`
- Shortfall-Hinweise in dieser Simulation: `13`

## Interpretation

- Mining-/Reward-Lots bleiben Betriebsvermoegen, bis eine Entnahme ins Privatvermoegen dokumentiert wird.
- Private Trading-Lots bleiben Privatvermoegen.
- Wenn ein Verkauf/Swap aus einem Business-Origin-Lot bedient wurde, sollte dieser Vorgang nicht als private §23-Zeile behandelt werden.
- Die Solana-Wallet ist nicht automatisch insgesamt Betriebsvermoegen; entscheidend ist die Herkunft der verbrauchten FIFO-Lots.
- Diese Auswertung ist read-only; die aktuelle Steuerlogik wurde dadurch noch nicht umgebucht.

## Fokus Solana/HNT/IOT

| Asset | Herkunft | Menge | Kostenbasis EUR | Lots | Aeltester Erwerb |
|---|---|---:|---:|---:|---|
| `ADA` | `business` | 0.4805519 | 0 | 759 | `2021-03-30T01:41:03+00:00` |
| `BNSOL` | `business` | 0.00000039 | 0 | 1 | `2025-03-23T23:59:59+00:00` |
| `BTTC` | `business` | 4209810.9 | 0 | 1217 | `2023-04-01T01:03:23+00:00` |
| `DOGE` | `business` | 0.00435444 | 0 | 1 | `2025-01-24T23:59:59+00:00` |
| `HNT` | `business` | 224.06014297 | 592.2845739211087873200505834 | 142 | `2025-02-01T00:00:00+00:00` |
| `HNT` | `private` | 977.91485394000001756127906 | 22.23604951511115098213257906 | 9 | `2025-01-29T05:58:45.618000+00:00` |
| `IOT` | `business` | 338468.922815 | 307.98503714482868853453457 | 81 | `2024-12-01T00:00:00+00:00` |
| `IOT` | `private` | 2336045.469342 | 2325.029901260139582989513243 | 5 | `2024-11-11T21:30:24+00:00` |
| `JUP` | `business` | 12.84176164 | 0 | 18 | `2025-12-14T23:59:59+00:00` |
| `JUP` | `private` | 19828.73089815 | 5062.03365579142022536328 | 32 | `2025-01-28T19:21:20.863000+00:00` |
| `PEPE` | `business` | 243810.76 | 0 | 20 | `2024-03-11T03:12:43+00:00` |
| `SHARKS...NR1S` | `business` | 963.536668 | 0 | 1 | `2026-01-02T04:18:08+00:00` |
| `SOL` | `business` | 0.145607172 | 0.3225585469155401813474446965 | 101 | `2026-01-02T04:18:08+00:00` |
| `SOL` | `private` | 179.099206605 | 17126.42374387961515171615983 | 74 | `2024-11-22T19:19:38+00:00` |
| `TRUMP` | `business` | 0.00000005 | 0 | 4 | `2025-01-21T23:59:59+00:00` |
| `USDT` | `private` | 1702.27119503 | 1496.0810407764888414 | 4 | `2025-04-22T10:22:51.484000+00:00` |

## Fokus Business-Origin-Verkaeufe/Swaps

| Jahr | Asset | Zeilen | Erloes EUR | Kostenbasis EUR | Gewinn/Verlust EUR |
|---:|---|---:|---:|---:|---:|
| 2021 | `HNT` | 2570 | 15486.83939122303783662833497 | 7430.978614250266812115821189 | 8055.860776972771024512513701 |
| 2021 | `USDT` | 7 | 0.00066522267 | 0.000665764204 | -0.000000541534 |
| 2022 | `HNT` | 14168 | 3402.968933603698417672671342 | 13487.40735754100812127573846 | -10084.43842393730970360306672 |
| 2023 | `HNT` | 9508 | 493.8663415098043655492428142 | 1367.909837349647668432769699 | -874.0434958398433028835268948 |
| 2023 | `IOT` | 535 | 171.1708972419718433804272628 | 329.710715143005425232 | -158.5398179010335818515727372 |
| 2024 | `IOT` | 1871 | 4481.684193707870058902205914 | 2872.215511622176227298826256 | 1609.46868208569383160337966 |
| 2024 | `MOBILE` | 15 | 5.931720603221108673243390954 | 4.3467382067821509228 | 1.584982396438957750443390956 |
| 2024 | `SOL` | 52 | -0.0000002510883811010609558323953675 | 0 | -0.0000002510883811010609558323953675 |
| 2024 | `USDT` | 1 | 0.0128444574297 | 0.0129442156386 | -0.0000997582089 |
| 2025 | `HNT` | 6 | 0 | 3.350640045613056 | -3.350640045613056 |
| 2025 | `JUP` | 5 | 4.81467347806439254203 | 0 | 4.81467347806439254203 |
| 2025 | `MOBILE` | 12 | 0.07907421059548574117890000004 | 1.5065786097128629312 | -1.427504399117377190021099999 |

## Offene Lots nach Herkunft

| Asset | Herkunft | Menge | Kostenbasis EUR | Lots | Aeltester Erwerb |
|---|---|---:|---:|---:|---|
| `2KFZCK...FV2J` | `private` | 4202343.53 | 0 | 1 | `2024-03-11T20:59:50+00:00` |
| `4T4TMH...2RGU` | `private` | 1 | 0 | 1 | `2023-08-19T07:55:38+00:00` |
| `7ATGF8...CFV1` | `private` | 10926642.83 | 0 | 1 | `2024-03-31T20:46:46+00:00` |
| `ADA` | `business` | 0.4805519 | 0 | 759 | `2021-03-30T01:41:03+00:00` |
| `ADA` | `private` | 415.4 | 250.619315596 | 4 | `2021-03-22T09:15:57+00:00` |
| `BNB` | `private` | 0.26119523 | 249.20018924649644 | 8 | `2021-04-28T05:14:45+00:00` |
| `BNSOL` | `business` | 0.00000039 | 0 | 1 | `2025-03-23T23:59:59+00:00` |
| `BPXYGG...XX59` | `private` | 1 | 0 | 1 | `2023-06-02T04:28:57+00:00` |
| `BTC` | `private` | 0.02689067 | 731.3691588043128602888286394 | 6 | `2022-12-02T18:16:38+00:00` |
| `BTT` | `private` | 1988.5 | 11.79579916551719529579472559 | 1 | `2021-05-01T16:30:45+00:00` |
| `BTTC` | `business` | 4209810.9 | 0 | 1217 | `2023-04-01T01:03:23+00:00` |
| `BUSD` | `private` | 1116.2340027652 | 1065.983028585747185546501978 | 4 | `2022-11-14T06:13:40+00:00` |
| `CDT` | `private` | 0.564 | 0.00056451324 | 1 | `2021-04-16T04:54:27+00:00` |
| `CM8VSE...ZIF4` | `private` | 1000000000 | 0 | 1 | `2023-07-30T06:59:36+00:00` |
| `DCUC8A...ZDMM` | `private` | 2000000 | 0 | 2 | `2024-03-26T20:05:16+00:00` |
| `DOCK` | `private` | 0.25 | 0.0002505475 | 1 | `2021-04-26T20:16:23+00:00` |
| `DOGE` | `business` | 0.00435444 | 0 | 1 | `2025-01-24T23:59:59+00:00` |
| `DOGE` | `private` | 4004.98374182 | 1390.3786664006825675 | 1 | `2025-01-24T13:00:17.397000+00:00` |
| `DSA1VH...GJDU` | `private` | 1 | 0 | 1 | `2023-05-08T04:52:01+00:00` |
| `EGLD` | `private` | 0.000926 | 0.1711188324088272846 | 1 | `2022-01-13T06:36:36+00:00` |
| `ETH` | `private` | 0.04063986 | 100.00000124214762972813276 | 2 | `2021-06-17T04:31:31+00:00` |
| `EUKMXS...TEAV` | `private` | 1 | 0 | 1 | `2023-12-17T00:57:32+00:00` |
| `EUR` | `private` | 6981.89377299 | 6984.86566676299 | 9 | `2021-08-17T16:25:48+00:00` |
| `GTO` | `private` | 1.8919 | 0.07382241797503 | 1 | `2021-03-20T07:51:39+00:00` |
| `HJGKKK...QNQN` | `private` | 1 | 0 | 1 | `2023-05-09T00:49:13+00:00` |
| `HNT` | `business` | 224.06014297 | 592.2845739211087873200505834 | 142 | `2025-02-01T00:00:00+00:00` |
| `HNT` | `private` | 977.91485394000001756127906 | 22.23604951511115098213257906 | 9 | `2025-01-29T05:58:45.618000+00:00` |
| `HOT` | `private` | 6.959 | 0.08980489680104 | 1 | `2021-05-09T18:31:18+00:00` |
| `IOT` | `business` | 338468.922815 | 307.98503714482868853453457 | 81 | `2024-12-01T00:00:00+00:00` |
| `IOT` | `private` | 2336045.469342 | 2325.029901260139582989513243 | 5 | `2024-11-11T21:30:24+00:00` |
| `JUP` | `business` | 12.84176164 | 0 | 18 | `2025-12-14T23:59:59+00:00` |
| `JUP` | `private` | 19828.73089815 | 5062.03365579142022536328 | 32 | `2025-01-28T19:21:20.863000+00:00` |
| `MXC` | `private` | 12649.96 | 924.716458061438975 | 105 | `2022-04-08T06:00:16+00:00` |
| `PEPE` | `business` | 243810.76 | 0 | 20 | `2024-03-11T03:12:43+00:00` |
| `SHARKS...NR1S` | `business` | 963.536668 | 0 | 1 | `2026-01-02T04:18:08+00:00` |
| `SHARKS...NR1S` | `private` | 677.465346 | 0 | 1 | `2024-05-03T05:11:35+00:00` |
| `SHIB` | `private` | 3128.522375 | 0.0908125074794795 | 1 | `2022-01-04T08:00:19+00:00` |
| `SOL` | `business` | 0.145607172 | 0.3225585469155401813474446965 | 101 | `2026-01-02T04:18:08+00:00` |
| `SOL` | `private` | 179.099206605 | 17126.42374387961515171615983 | 74 | `2024-11-22T19:19:38+00:00` |
| `TRUMP` | `business` | 0.00000005 | 0 | 4 | `2025-01-21T23:59:59+00:00` |
| `TRUMP` | `private` | 0.154 | 8.0375496432 | 1 | `2025-01-20T05:12:26.122000+00:00` |
| `UNKNOWN` | `private` | 34883.511342 | 25313.2140981063275560247481 | 74 | `2021-05-01T18:40:17+00:00` |
| `USDC` | `private` | 463.02137333 | 394.6979650531252 | 3 | `2025-06-03T19:43:41+00:00` |
| `USDT` | `private` | 1702.27119503 | 1496.0810407764888414 | 4 | `2025-04-22T10:22:51.484000+00:00` |
| `VET` | `private` | 200.01639287 | 0.105222 | 2 | `2021-05-10T17:50:48+00:00` |
| `WABI` | `private` | 0.053 | 0.00005350721 | 1 | `2021-04-16T04:53:40+00:00` |
| `WIN` | `private` | 28292.30730362 | 15.64218059079865653173059926 | 2 | `2021-05-01T18:40:17+00:00` |
| `WRX` | `private` | 0.014 | 0.00001525762 | 1 | `2021-04-05T10:14:20+00:00` |
| `XRP` | `private` | 99.20033434 | 196.0050822214957062 | 2 | `2025-03-09T19:00:30.468000+00:00` |
| `YFIDOWN` | `private` | 57.67331 | 0.116465447610014 | 1 | `2021-04-23T19:49:50+00:00` |
| `ZEUS` | `private` | 20420.324416 | 10373.98362988828252953427353 | 1 | `2024-11-22T16:00:29+00:00` |

## Gemischte offene Assets

- `ADA`: business, private
- `DOGE`: business, private
- `HNT`: business, private
- `IOT`: business, private
- `JUP`: business, private
- `SHARKS...NR1S`: business, private
- `SOL`: business, private
- `TRUMP`: business, private

## Business-Origin-Verkaeufe/Swaps nach Jahr

| Jahr | Zeilen | Erloes EUR | Kostenbasis EUR | Gewinn/Verlust EUR |
|---:|---:|---:|---:|---:|
| 2021 | 2605 | 15486.89499251889510542833497 | 7430.979280014470812115821189 | 8055.915712504424293312513701 |
| 2022 | 14168 | 3402.968933603698417672671342 | 13487.40735754100812127573846 | -10084.43842393730970360306672 |
| 2023 | 10044 | 665.0372387517762089296700766 | 1697.673785370934590918187667 | -1032.636546619158381988517601 |
| 2024 | 1939 | 4487.628758517432486474388352 | 2876.575194044596978221626256 | 1611.053564472835508252762098 |
| 2025 | 38 | 4.893747688659878283208900001 | 4.8572186553259189312 | 0.03652903333395935200890000016 |

## Beispiele Business-Origin-Verkaeufe/Swaps

- `2021-02-14T13:22:39+00:00` `USDT` qty `0.00011522` G/V `0` Lot `e59c95ee62d65a6b746f5a21567edaaef841cf29d6ffe7bf99d556ecb7a093a0` (binance_account_statement/interest) -> Sell `cd6d5ad668a0b45709b77b8fe2911f8aa13642ae63171f2a62f8729c96fa79c8` (binance/trade)
- `2021-02-16T17:25:07+00:00` `USDT` qty `0.00011522` G/V `-0.000000109459` Lot `f93205485ca1ba96d488cfc3812276c9eb49a1fd4db4463d6f3e2d7cc76556bc` (binance_account_statement/interest) -> Sell `1c57c0bf56c3e9529b0daef46108b384c0eb00dfa905d028c1885365223aa529` (binance/trade)
- `2021-02-16T17:25:07+00:00` `USDT` qty `0.00011522` G/V `0` Lot `2a6c8bae11fe9dd861b5e292dc0f0173fc87e243b2bbf8017b67ac01b3c12140` (binance_account_statement/interest) -> Sell `1c57c0bf56c3e9529b0daef46108b384c0eb00dfa905d028c1885365223aa529` (binance/trade)
- `2021-02-17T18:15:11+00:00` `USDT` qty `0.00011522` G/V `0` Lot `c2ea1fcee5bf403e44052362bf7e57b274484d627e56a2e25704649b05ebe9f6` (binance_account_statement/interest) -> Sell `25e2fee8d59ec84eef31eb155d654f27dec2b4d4e46433dc30d6100eed1952ba` (binance/trade)
- `2021-02-20T22:00:45+00:00` `USDT` qty `0.00011522` G/V `-0.000000432075` Lot `ff4ccc974c3ad90e38e20bf2c55bf00d1efa007efe2076118bb480379470ed59` (binance_account_statement/interest) -> Sell `ce2d12e5f2896814a17109b05306c6c1a13751aaca5a3754ac448d0cb3992782` (binance/trade)
- `2021-02-20T22:00:45+00:00` `USDT` qty `0.00011522` G/V `0` Lot `7595db7ad84a6c3531c2ab4999d764c4ba8464e250773c19e3eeb5fd502d89ae` (binance_account_statement/interest) -> Sell `ce2d12e5f2896814a17109b05306c6c1a13751aaca5a3754ac448d0cb3992782` (binance/trade)
- `2021-02-21T18:31:07+00:00` `USDT` qty `0.00011522` G/V `0` Lot `af7167da51e3b274ac1cb77621340fc5ff0f9d9ebfb88f9ae5ffc2e983e82140` (binance_account_statement/interest) -> Sell `8ed0cf651f154533533888b0043051f3c67c6cb3c597042ad04e45002f98f791` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `0.60218015` G/V `-1.32259180421690434145682649` Lot `b0eafb9c38bb7dc4c2654707270dd3bf7b05cf6eb8e41bd075103ba6d76b79a3` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `0.44532458` G/V `-0.978083783937971311009567228` Lot `e93025e29dad1ca698cfd9143e752b0a639fd6c67266359ed1edcbcee836dc1a` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `0.04670829` G/V `-0.102587243274269985290987214` Lot `2af40c8d4b98a7eee69c2916c5b3b6fbdae31c6d40c5119faa85fb06b5592092` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `1.07891407` G/V `-2.36966114946881498143347036` Lot `793b9de4cdf07907f25cb1415be5f903f681da3e5bed849dd4a7f88ab1546cfa` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `0.19602508` G/V `-0.430537546328890135097315528` Lot `b6a27e8ec11996c747271cb564b765bf748689f53aeb40415adced5cd426778c` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `0.3864945` G/V `-0.8488729794147321777364887` Lot `ed2522452f8f5465918c09f549af1993272c567260ffc6a644fd119724324d35` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `0.20923444` G/V `-0.26677466653083555768274394` Lot `6cb45c2e05a55dd049d50a7e6341e4dec278f41ac227e9b52e2ad28bb2e07e9c` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `0.22040413` G/V `-0.281016061613799952169107505` Lot `0a0d0495d12ed118aed78ca57d8b0bdd6a9edf648eb1edded4cc82fdde56faca` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `0.19169659` G/V `-0.244413844452893635763454215` Lot `629e618cbaf6d94f4480cb2e4fa15666c34967693b408b67f02d0a6f0a2b22da` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `0.53425446` G/V `-0.68117636565525075230728371` Lot `1ba39c7152fa6abd9669e1dd4e2cc8cb642c2e460a87745d07b13078a46535e8` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `0.05352665` G/V `-0.068246672030965595834218525` Lot `39fa760f2a1d8f583b8d09f8eaf4d31358263d5cb556f129aafec115609f0b77` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `1.23712072` G/V `-0.3050029341576668701051127` Lot `d9043936d413f58c46060e658386f32f216e245b759b570ff2aea194e4b876c9` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)
- `2021-08-06T19:07:32+00:00` `HNT` qty `1.27399837` G/V `-0.31409484513531138296423918` Lot `1c26dd9abb329efdd3291c97a2893c84c33fc7d7e2c8c7d163b15984b99218a0` (helium_legacy_cointracking/mining_reward) -> Sell `2ef50e2a84fe3ca10127f49100588b8a75959068db1f742fd90c43a17d3f67aa` (binance/trade)

## Grenzen dieser Auswertung

- Transfer-Outs verbrauchen zwar FIFO-Lots; Transfer-Ins auf einer anderen Plattform tragen die Herkunftsdomain aktuell noch nicht automatisch weiter.
- Es gibt noch keine Entnahme-Events. Ohne dokumentierte Entnahme bleibt ein Reward-/Mining-Lot in dieser Sicht Betriebsvermoegen.
- Shortfalls zeigen, dass einzelne historische Bewegungen weiterhin nicht vollstaendig gedeckt sind.

## Naechste technische Konsequenz

- Steuerlogik erweitern: Lots muessen eine Domain tragen (`business`/`private`).
- Transfer-Matching erweitern: Domain beim Transfer von Quelle zu Ziel fortschreiben.
- Tax-Lines aus Business-Lots muessen als EÜR-/Business-Verkaeufe oder separater Business-Disposal-Export erscheinen.
- Optional: Entnahme-Event modellieren, falls ein gewerblicher Reward bewusst ins Privatvermoegen ueberfuehrt wurde.

JSON: `var/business_private_lot_audit_2026-05-10.json`
