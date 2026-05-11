# Bewertungsanomalie-Audit

Stand: 2026-05-11

## Scope

Ausgewertet wurden die neuesten abgeschlossenen Jobs je Steuerjahr `2020` bis `2026`.

| Jahr | Job | Tax-Lines | Derivate-Lines | Aktualisiert |
| ---: | --- | ---: | ---: | --- |
| 2020 | `287cc41c-9055-42ca-8b5a-9d5578e07dc6` | 0 | 0 | 2026-05-10T19:38:15.619598+00:00 |
| 2021 | `5ab77c28-68f9-42f2-8a97-47f1d4f57f13` | 5812 | 0 | 2026-05-10T19:38:23.927746+00:00 |
| 2022 | `c4d8719c-4041-443a-b182-d9f6ccf06407` | 6896 | 0 | 2026-05-10T19:38:32.791187+00:00 |
| 2023 | `bf4e3974-5e7e-4bfe-9e15-6992ad4812bb` | 9099 | 0 | 2026-05-10T19:38:42.006834+00:00 |
| 2024 | `54225c56-f4e7-4ecd-a63a-26b499f2f336` | 1680 | 36 | 2026-05-11T19:41:52.497920+00:00 |
| 2025 | `1505480c-23b5-408c-9813-445425e1ef0c` | 465 | 957 | 2026-05-11T19:42:01.050148+00:00 |
| 2026 | `924d49e7-b215-480f-ae35-9dddc8d99648` | 1 | 0 | 2026-05-10T19:39:07.952392+00:00 |

## Zusammenfassung

- Tax-Lines im Scope: `23953`
- Fast-Null-Kostenbasis: `113`
- FX vorhanden, aber niedrige Kostenbasis: `18`
- Gleicher `tx_id` mit bepreistem Gegenfluss: `0`
- Hohe Gewinnquote: `98`
- Solana-Swap-In-Raw-Events ohne Raw-Preisanker: `310`
- Prioritaet-1-Treffer ueber alle Klassen: `0`

Hinweis: Raw-Events werden nicht zwingend mit Laufzeit-Preisankern zurueckgeschrieben.
Raw-Swap-Treffer sind deshalb nur dann hoch priorisiert, wenn die daraus entstandenen
Tax-Lines ebenfalls auffaellig sind.

## Fast-Null-Kostenbasis

| Prio | Jahr | Line | Asset | Kostenbasis | Erloes | Quote | Lot-Event | Swap | Gegenfluss |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| priority_2 | 2021 | 5620 | `UNKNOWN` | 0.06004482671812621530846738554 | 1640.59920467388 | 0.00003659932696972261901092005348 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 5616 | `UNKNOWN` | 0.05055533301318013081138412586 | 1381.31865252612 | 0.00003659932696972261901092005348 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 1110 | `UNKNOWN` | 0.1250854626513155382711684638 | 1338.6472294795272 | 0.00009344169240162652676775923015 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 3971 | `UNKNOWN` | 0.04722626820526780979317659537 | 1275.57385365564 | 0.00003702354675107446844263758273 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 806 | `UNKNOWN` | 0.000406278626756980731836662542 | 1074.7427978489364 | 0.0000003780240514941198107400108016 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 2270 | `UNKNOWN` | 0.05336457707035531200282835425 | 875.527664856075 | 0.00006095133165109949142579389374 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 3099 | `UNKNOWN` | 0.02073752994961993989747215839 | 865.55622735 | 0.00002395861677653255913285199286 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 953 | `UNKNOWN` | 0.0005584533865312851334629662365 | 801.0748048287272 | 0.0000006971301346204298156447251992 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 703 | `DOGE` | 0.01410683369500195118259224219 | 631.2149925198208 | 0.00002234869871941291396847565008 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 4969 | `UNKNOWN` | 0.02333663370330563903128866891 | 630.13265135523 | 0.00003703447782481260675632008571 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 5751 | `UNKNOWN` | 0.01990802875163514230157327205 | 609.9953965974 | 0.00003263635899989347040094203077 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 5771 | `UNKNOWN` | 0.01824902635566554710977549938 | 603.8530576848 | 0.00003022097201202084081847022526 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 3972 | `UNKNOWN` | 0.02046102955029167403217252961 | 552.6490935042 | 0.00003702354675107446844263758273 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 1111 | `UNKNOWN` | 0.05031090666017394378645925402 | 538.3818390406152000000000001 | 0.00009344837253393779400184942665 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 1707 | `UNKNOWN` | 0.02987310314342584408697189323 | 533.54728930932 | 0.00005598960718570371892994478113 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 5633 | `UNKNOWN` | 0.01717620480627187555241293972 | 526.290472730979 | 0.00003263635899989347040094203077 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 853 | `UNKNOWN` | 1.36768157523733427611808379 | 493.2768780311598 | 0.002772644808928058489700478669 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 878 | `UNKNOWN` | 1.291256864863001590949266396 | 484.138072492812 | 0.002667125223625483176716465258 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 870 | `UNKNOWN` | 1.291256864863001590949266396 | 484.0703689864392000000000001 | 0.002667498255608318387473784167 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 883 | `UNKNOWN` | 1.295902071571716457486300159 | 465.6703282686864 | 0.002782874477722780594290057586 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 1629 | `UNKNOWN` | 0.0262631139297960049496199399 | 463.67731168686 | 0.00005664092951680272339594555082 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 859 | `UNKNOWN` | 1.253763410714088739614636733 | 451.8992925989568 | 0.002774431009846159307849530027 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 4968 | `UNKNOWN` | 0.01662320400761534382181368216 | 448.725000063762 | 0.00003704541535518024190302898117 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 5770 | `UNKNOWN` | 0.01333837926359554534205409227 | 441.255183235884 | 0.00003022826647786974761084736023 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 1632 | `UNKNOWN` | 0.02442825727985363266749160332 | 431.28277534017 | 0.00005664092951680272339594555081 | `binance/buy/buy` | nein | nein |

## Gleicher TX mit bepreistem Gegenfluss

| Prio | Jahr | Line | Asset | Kostenbasis | Erloes | Quote | Lot-Event | Swap | Gegenfluss |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| - | - | - | - | - | - | - | - | - | - |

## FX vorhanden, aber niedrige Kostenbasis

| Prio | Jahr | Line | Asset | Kostenbasis | Erloes | Quote | Lot-Event | Swap | Gegenfluss |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| priority_2 | 2021 | 703 | `DOGE` | 0.01410683369500195118259224219 | 631.2149925198208 | 0.00002234869871941291396847565008 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 704 | `DOGE` | 1.007958879592704 | 301.9870044801792 | 0.003337755812796444326511658761 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 770 | `DOGE` | 0.562573530407296 | 283.5285617423872 | 0.001984186450035491758025080842 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 749 | `DOGE` | 0.37655746 | 150.413432 | 0.002503482933625236341924569609 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 385 | `HNT` | 0.0212520536 | 124.28374715848 | 0.0001709962411488970935413042271 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 8 | `HNT` | 0.002387858462 | 59.80264674417 | 0.00003992897625777384061321368675 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 156 | `HNT` | 0.0186472 | 55.46707232 | 0.0003361850413236304735255945811 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 701 | `DOGE` | 0.000913253864536365482233502538 | 42.7366615198208 | 0.00002136933096921499698704555866 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 7 | `HNT` | 0.001528161538 | 38.27199395583 | 0.00003992897625777384061321368675 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 760 | `DOGE` | 0.070441 | 37.492 | 0.001878827483196415235250186706 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 163 | `HNT` | 0.0124268755 | 36.9643915478 | 0.0003361850413236304735255945811 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 952 | `ETH` | 0.00002127582931322120368951893035 | 33.6866658115456 | 0.0000006315801460508220423309023174 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 157 | `HNT` | 0.0090279995 | 26.8542570022 | 0.0003361850413236304735255945811 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 757 | `DOGE` | 0.04759799 | 22.955636 | 0.002073477293332234402044012198 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 752 | `DOGE` | 0.04578665 | 20.00362 | 0.00228891820580474934036939314 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 698 | `DOGE` | 0.0003559461354636345177664974619 | 16.6568684801792 | 0.00002136933096921499698704555866 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 754 | `DOGE` | 0.02445309 | 10.969506 | 0.002229187895972708342563466395 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 394 | `HNT` | 0.0015372964 | 10.48477833754 | 0.0001466217358640592367759665697 | `binance/trade/in` | nein | nein |

## Hohe Gewinnquote

| Prio | Jahr | Line | Asset | Kostenbasis | Erloes | Quote | Lot-Event | Swap | Gegenfluss |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| priority_2 | 2021 | 5620 | `UNKNOWN` | 0.06004482671812621530846738554 | 1640.59920467388 | 0.00003659932696972261901092005348 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 5616 | `UNKNOWN` | 0.05055533301318013081138412586 | 1381.31865252612 | 0.00003659932696972261901092005348 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 1110 | `UNKNOWN` | 0.1250854626513155382711684638 | 1338.6472294795272 | 0.00009344169240162652676775923015 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 3971 | `UNKNOWN` | 0.04722626820526780979317659537 | 1275.57385365564 | 0.00003702354675107446844263758273 | `binance/buy/buy` | nein | nein |
| priority_2 | 2022 | 514 | `USDT` | 0 | 1168.7663514436165 | 0 | `//` | nein | nein |
| priority_2 | 2022 | 3572 | `HNT` | 0 | 1146.1874646034960896 | 0 | `binance_api/deposit/in` | nein | nein |
| priority_2 | 2021 | 806 | `UNKNOWN` | 0.000406278626756980731836662542 | 1074.7427978489364 | 0.0000003780240514941198107400108016 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 705 | `UNKNOWN` | 6.25064696282 | 932.2687949999999999999999999 | 0.006704769049810360755451436086 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 2270 | `UNKNOWN` | 0.05336457707035531200282835425 | 875.527664856075 | 0.00006095133165109949142579389374 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 3099 | `UNKNOWN` | 0.02073752994961993989747215839 | 865.55622735 | 0.00002395861677653255913285199286 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 953 | `UNKNOWN` | 0.0005584533865312851334629662365 | 801.0748048287272 | 0.0000006971301346204298156447251992 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 703 | `DOGE` | 0.01410683369500195118259224219 | 631.2149925198208 | 0.00002234869871941291396847565008 | `binance/trade/in` | nein | nein |
| priority_2 | 2021 | 4969 | `UNKNOWN` | 0.02333663370330563903128866891 | 630.13265135523 | 0.00003703447782481260675632008571 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 362 | `UNKNOWN` | 4.5867285373335 | 622.4121412621614 | 0.007369278703388209739516572494 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 5751 | `UNKNOWN` | 0.01990802875163514230157327205 | 609.9953965974 | 0.00003263635899989347040094203077 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 5771 | `UNKNOWN` | 0.01824902635566554710977549938 | 603.8530576848 | 0.00003022097201202084081847022526 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 3972 | `UNKNOWN` | 0.02046102955029167403217252961 | 552.6490935042 | 0.00003702354675107446844263758273 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 1111 | `UNKNOWN` | 0.05031090666017394378645925402 | 538.3818390406152000000000001 | 0.00009344837253393779400184942665 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 1707 | `UNKNOWN` | 0.02987310314342584408697189323 | 533.54728930932 | 0.00005598960718570371892994478113 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 5633 | `UNKNOWN` | 0.01717620480627187555241293972 | 526.290472730979 | 0.00003263635899989347040094203077 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 853 | `UNKNOWN` | 1.36768157523733427611808379 | 493.2768780311598 | 0.002772644808928058489700478669 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 878 | `UNKNOWN` | 1.291256864863001590949266396 | 484.138072492812 | 0.002667125223625483176716465258 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 870 | `UNKNOWN` | 1.291256864863001590949266396 | 484.0703689864392000000000001 | 0.002667498255608318387473784167 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 883 | `UNKNOWN` | 1.295902071571716457486300159 | 465.6703282686864 | 0.002782874477722780594290057586 | `binance/buy/buy` | nein | nein |
| priority_2 | 2021 | 1634 | `HNT` | 0 | 464.14145314 | 0 | `//` | nein | nein |

## Solana-Swap-In-Raw-Events ohne Raw-Preisanker

| Prio | Zeit | Event | Asset | Menge | Tax-Lines | Erloes | Min-Quote | FX | Gegenfluss |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| informational | 2023-04-26T14:42:15+00:00 | `281abc3614f6e358c70df142bc1b551287268f3b0f3f9ccc004072949c5d5fe9` | `IOT` | 347279.588497 | 0 | 0 | 0 | ja | ja |
| informational | 2023-04-26T14:56:02+00:00 | `4a8290259637c17301d14f323aac27b353f97997ef750af838d4795758edb7c3` | `HNT` | 514.50311342 | 0 | 0 | 0 | ja | ja |
| informational | 2023-04-26T15:01:18+00:00 | `3d0d2033d359ac66db285d61f10573339dd032409fb743975a125a16acd1e921` | `IOT` | 733904.811832 | 0 | 0 | 0 | ja | ja |
| informational | 2023-04-26T15:15:37+00:00 | `eb3030cd29031a60368c35b305b54fde6fcefe12f59fd300aa9c8ee21c3a2e75` | `HNT` | 924.33312667 | 0 | 0 | 0 | ja | ja |
| informational | 2023-05-08T04:52:01+00:00 | `061134f4ee81c87923d8583d621e56c438e98f5e6baeeb651545154f9718750c` | `DSA1VH...GJDU` | 1 | 0 | 0 | 0 | nein | ja |
| informational | 2023-05-14T06:34:59+00:00 | `9c701f84d14c9a1bfd36c3046daa7c1c2f87d01afef12a2a66f81ae608174982` | `7RPAXC...C3KQ` | 1 | 0 | 0 | 0 | nein | ja |
| informational | 2023-06-29T03:19:47+00:00 | `f0fe55cedb34a6a44af3eeed7702ced57bf428cf4d649dfd984145d84bf87ae7` | `SOL` | 4.051950048 | 0 | 0 | 0 | ja | ja |
| informational | 2023-07-15T09:48:46+00:00 | `2ea47a40bb2630c51e5487bcd60c0633af5313b8607456b4d55fa5d0138031c2` | `HNT` | 23.86069708 | 0 | 0 | 0 | ja | ja |
| informational | 2023-07-30T06:59:13+00:00 | `888138a3af18bfb461bfadd5f99daf3827b08e7a51130270caa061ec00dc2c22` | `MOBILE` | 64729.546356 | 0 | 0 | 0 | nein | ja |
| informational | 2023-08-01T06:35:02+00:00 | `62d8947c4aa9a44e4656bb7ca895de72c0f1ea780b488028e92e9cc12f7f8744` | `DVOPSY...VR4K` | 1 | 0 | 0 | 0 | nein | ja |
| informational | 2023-08-01T06:43:43+00:00 | `d044f54a7e7ee5753dab7d33ffbc9ad5295c0f65495f876365e9c1ab8ad0f0b6` | `5MFEM7...UETF` | 1 | 0 | 0 | 0 | nein | ja |
| informational | 2023-09-30T06:28:50+00:00 | `ce2a7c1d09e266417e79283b21663df357b1b5b51efc79a7926a533763ef046d` | `HNT` | 28.56369341 | 0 | 0 | 0 | ja | ja |
| informational | 2023-11-11T06:57:33+00:00 | `48f00a66a9c5a4831be836d2d8a13d5097376d7051419e339dbb26d1f19d4363` | `IOT` | 361446.328050 | 0 | 0 | 0 | ja | ja |
| informational | 2023-11-25T08:35:59+00:00 | `1cfd16fd9be9888c9afbf1f7d1b117147e5ae08aa6fdafc5bc768f5cdbb052be` | `SOL` | 0.994232384 | 0 | 0 | 0 | ja | ja |
| informational | 2023-12-06T11:01:46+00:00 | `527e41bc9f6541a4ac8bc516e6e6f012b663ac21842784f6975522ab158cf12d` | `SOL` | 2.413608078 | 0 | 0 | 0 | ja | ja |
| informational | 2024-02-15T07:28:32+00:00 | `917981b2a002a3da701063d5de4fe50aed1805cd4019a7ed8d1cf2d537c7081d` | `USDT` | 111.292574 | 0 | 0 | 0 | nein | ja |
| informational | 2024-02-15T07:35:47+00:00 | `feccacfa4757cf9ae9fec49cc92a79082d6c71a97127e4c61e67c5c378d596b5` | `USDT` | 109.053185 | 0 | 0 | 0 | nein | ja |
| informational | 2024-02-15T10:58:42+00:00 | `00a651fb5a458c76853517dbe424445bb0b15be9f41990befc5a41f03701a471` | `USDT` | 40.508923 | 0 | 0 | 0 | nein | ja |
| informational | 2024-02-15T13:34:23+00:00 | `97d054da70bfabacbc26397587dea937b75e80f763619909309a69634f7118cf` | `USDT` | 24.513173 | 0 | 0 | 0 | nein | ja |
| informational | 2024-02-16T17:33:14+00:00 | `1c108c4c20a7fa8e48504d93a7ff24301e6e4ed839624668aee4c0f5de8d8f0d` | `SOL` | 0.00512256 | 0 | 0 | 0 | ja | nein |
| informational | 2024-02-16T17:33:14+00:00 | `2649b4c0cc4a650354cbbb733f1eb5fb25349f05c64f7a37cff2ebe95ce72362` | `MOBILE` | 37445.235030 | 0 | 0 | 0 | ja | nein |
| informational | 2024-02-17T17:50:48+00:00 | `2fb53706c79f1266ce9d6593d238c7e97026e25dcc89bedf843a3726dac11ba7` | `MOBILE` | 1511.917285 | 0 | 0 | 0 | ja | nein |
| informational | 2024-02-21T07:10:49+00:00 | `5c5ac31e2828956b7ab9341571e63653a231067c3dce5536f50f18ae0d546299` | `SOL` | 0.00512256 | 0 | 0 | 0 | ja | nein |
| informational | 2024-02-21T07:10:49+00:00 | `a7c7a5a2c68baabbe9592bb144a5c990d39555e3ccdb3dcc1fc9b460aad38574` | `IOT` | 56730.971542 | 0 | 0 | 0 | ja | nein |
| informational | 2024-02-23T21:01:15+00:00 | `a36ee4c1f29d42ec319da02d0313d01edb2f9a442ef0f5ee2724f49ed338a5cf` | `USDT` | 902.309402 | 0 | 0 | 0 | nein | ja |
| informational | 2024-02-26T17:33:22+00:00 | `c146985504b37207cfc041dcbb83323bc09ff0e613e58b01a5a830881b2244a7` | `IOT` | 3147.95738 | 0 | 0 | 0 | ja | nein |
| informational | 2024-02-26T17:33:40+00:00 | `e2aeee5fc6f1f8817d54263c42ebc9f23650e384970722493602c97de0a34635` | `IOT` | 388813.488013 | 0 | 0 | 0 | ja | ja |
| informational | 2024-02-28T17:14:05+00:00 | `707d8a700c1389e4b3a52edd71aed7f426a07fa1a47e0b332298a8bf0cb7c332` | `USDT` | 99.255585 | 0 | 0 | 0 | nein | ja |
| informational | 2024-03-04T20:45:38+00:00 | `68d2b9c68aa0fd0050e3c0ba9de9d86b8ee921fcb368de1db7e6c9d0250db863` | `USDT` | 774.584420 | 0 | 0 | 0 | nein | ja |
| informational | 2024-03-05T21:21:38+00:00 | `5cf6f469b7674fa337b716e8c1769d17dabdee0d8117c0b1ebdf45bcf43924d5` | `IOT` | 699.210159 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:23:12+00:00 | `fd4b42fe5c221e7a070331767108feb54c078169644bf1a8e81869a030d6136c` | `IOT` | 69809.142285 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:23:46+00:00 | `43528250aed4c7971be12d894fdd2174731a850366554347b44411f90fdd4ae5` | `IOT` | 16754.194010 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:24:04+00:00 | `3c4076c6a6f6efb7052018659811f2ba9bac1bb52e7d6714e523fddcbb4a9c62` | `IOT` | 13989.751775 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:24:25+00:00 | `583a60c05e22b023594cb3154d96b612d4445b130513850b4276ca1b9ee4c13a` | `IOT` | 558.694395 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:24:36+00:00 | `2cd9e7696faa15d1c1bbde10f7bc80b848f4a26334c60ea52c9a6f78e86a42a2` | `IOT` | 537.206149 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:29:44+00:00 | `27a45f2c97d35482cb466d0be8a844b7e6507d1e121ae28fe49f15ff50ea46ad` | `IOT` | 535.452803 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:33:41+00:00 | `ead6f12b752329eb9b18a784fce5d8f1a58259319a4ee18d49d86d898e966dad` | `IOT` | 534.596133 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:34:33+00:00 | `05a6cb9fc97873775008e28ebfd071febbbf67e8b02c18b52f58deed8c6ecbfb` | `IOT` | 13343.524086 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:34:54+00:00 | `1005f6bc47681b490b82f3353121362a0552fe11fdb2edea5fc135f56b7b331c` | `IOT` | 64048.915605 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:35:13+00:00 | `74c0782932f1d78b8196345e08e7fe67fcb32fbfaab759d4e3453ac33044404c` | `IOT` | 12850.839734 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:35:16+00:00 | `9459c4b778bd0793e4aa986b02313e24d526969b87108e15228a2781a547a01a` | `IOT` | 12851.695404 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:36:39+00:00 | `170149029c4afc40341a76e336c115f55cafa6e5c2619f2233119a0282eb63a5` | `IOT` | 38354.056486 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:36:39+00:00 | `5a0a5a2345ac4019f1fece7b48c8747ff70fd651f2c6c29b5a6becd6d864a559` | `IOT` | 56132.613400 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:36:46+00:00 | `7c441e0ed9f1f550e57ed2776e5827598fee4269b0e9a161010b639bc0e7ab1b` | `IOT` | 13430.161704 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:37:07+00:00 | `0553c03fe2eb98affbe9522e93629857c0983a3b2cc3c6cb6be6e7ac2d4c1306` | `IOT` | 36878.900505 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:37:07+00:00 | `c28a147209ba7a54d6662aa3589f24dff9a76392391efadac871a185584295e6` | `IOT` | 38722.845355 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:37:35+00:00 | `3461a0196bb4f0b009118236b12c372f5832ff2396061ece0afc0b96275eeeb7` | `IOT` | 1878.981774 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:38:02+00:00 | `4c6c3fc274799f18f096cd1389f578b60b98522e5b5e383b25f2897d6852b709` | `IOT` | 665.503500 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:47:24+00:00 | `b7cad3ab3b817e4139340f113252a838352261307c1d942f695682cf20a3aaa1` | `IOT` | 8886.013312 | 0 | 0 | 0 | ja | nein |
| informational | 2024-03-05T21:51:09+00:00 | `401364077fc824a1730064b5306ed1a628c6e0591006f996dd5bd41b5112ed4f` | `SOL` | 0.00512256 | 0 | 0 | 0 | ja | nein |

## Bewertung

- `priority_1` ist direkt zu pruefen und bei eindeutigem Codepfad deterministisch zu fixen.
- `priority_2` ist nachgelagert zu pruefen, besonders wenn aktuelle Jahre oder hohe Summen betroffen sind.
- `informational` bei Raw-Swaps bedeutet nicht automatisch Fehler, weil Preisanker zur Laufzeit entstehen koennen.
- Kein Treffer in diesem Bericht ist eine steuerberaterliche Endfreigabe.

## Naechster Schritt

Die `priority_1`-Treffer werden einzeln gegen Rohereignis, FX-Cache und Gegenfluss geprueft.
Nur belegbare technische Luecken werden automatisch korrigiert.
