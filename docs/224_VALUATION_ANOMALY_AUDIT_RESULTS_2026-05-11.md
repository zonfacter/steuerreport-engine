# Bewertungsanomalie-Audit

Stand: 2026-05-11

## Scope

Ausgewertet wurden die neuesten abgeschlossenen Jobs je Steuerjahr `2020` bis `2026`.

| Jahr | Job | Tax-Lines | Derivate-Lines | Aktualisiert |
| ---: | --- | ---: | ---: | --- |
| 2020 | `0b3a4d22-6574-4e54-8685-92d40dbaf100` | 0 | 0 | 2026-05-11T20:33:22.138080+00:00 |
| 2021 | `155b1abc-cd34-44d1-9497-f072afd8cf1c` | 5434 | 43 | 2026-05-11T21:18:51.763033+00:00 |
| 2022 | `d1c40860-d286-4ff7-a7e7-1a173f99ad4e` | 11765 | 630 | 2026-05-11T21:29:04.737184+00:00 |
| 2023 | `210d8066-3bb0-4947-b45b-ceb2962e15d6` | 9099 | 0 | 2026-05-11T20:33:49.504534+00:00 |
| 2024 | `aeb1b44b-8b45-4dcb-8479-12c5b470c379` | 1680 | 36 | 2026-05-11T20:33:58.836379+00:00 |
| 2025 | `cc781fa5-1987-411a-ba69-e2653129cf88` | 465 | 957 | 2026-05-11T20:34:07.563410+00:00 |
| 2026 | `b59704da-a6b6-442d-b64d-b8024a74bab5` | 1 | 0 | 2026-05-11T20:34:16.355680+00:00 |

## Zusammenfassung

- Tax-Lines im Scope: `28444`
- Fast-Null-Kostenbasis: `0`
- FX vorhanden, aber niedrige Kostenbasis: `0`
- Gleicher `tx_id` mit bepreistem Gegenfluss: `0`
- Hohe Gewinnquote: `6`
- Solana-Swap-In-Raw-Events ohne Raw-Preisanker: `310`
- Prioritaet-1-Treffer ueber alle Klassen: `0`

Hinweis: Raw-Events werden nicht zwingend mit Laufzeit-Preisankern zurueckgeschrieben.
Raw-Swap-Treffer sind deshalb nur dann hoch priorisiert, wenn die daraus entstandenen
Tax-Lines ebenfalls auffaellig sind.

## Fast-Null-Kostenbasis

| Prio | Jahr | Line | Asset | Kostenbasis | Erloes | Quote | Lot-Event | Swap | Gegenfluss |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| - | - | - | - | - | - | - | - | - | - |

## Gleicher TX mit bepreistem Gegenfluss

| Prio | Jahr | Line | Asset | Kostenbasis | Erloes | Quote | Lot-Event | Swap | Gegenfluss |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| - | - | - | - | - | - | - | - | - | - |

## FX vorhanden, aber niedrige Kostenbasis

| Prio | Jahr | Line | Asset | Kostenbasis | Erloes | Quote | Lot-Event | Swap | Gegenfluss |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| - | - | - | - | - | - | - | - | - | - |

## Hohe Gewinnquote

| Prio | Jahr | Line | Asset | Kostenbasis | Erloes | Quote | Lot-Event | Swap | Gegenfluss |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| priority_2 | 2022 | 514 | `USDT` | 0 | 1168.7663514436165 | 0 | `//` | nein | nein |
| priority_2 | 2021 | 1285 | `HNT` | 0 | 445.1808341476849715363131107 | 0 | `//` | nein | nein |
| priority_2 | 2021 | 1347 | `HNT` | 0 | 290.1121724005967814158276469 | 0 | `binance_api/deposit/in` | nein | nein |
| priority_2 | 2022 | 442 | `USDT` | 0 | 148.757630271075 | 0 | `//` | nein | nein |
| priority_2 | 2021 | 1517 | `HNT` | 0 | 69.92100578446492383320425294 | 0 | `binance_api/deposit/in` | nein | nein |
| priority_2 | 2022 | 412 | `USDT` | 0 | 66.352680580511514 | 0 | `//` | nein | nein |

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

- Es gibt aktuell keine Treffer in den technischen Fehlerklassen
  Fast-Null-Kostenbasis, FX-vorhanden-aber-niedrig oder gleicher `tx_id` mit
  bepreistem Gegenfluss.
- Der Binance-Transaction-History-Stable-Counterflow-Fix hat die
  `priority_2`-High-Gain-Treffer von `8` auf `6` reduziert.
- Die restlichen `priority_2`-Treffer sind historische HNT-/USDT-Beleg- und
  Bestandsluecken, nicht automatisch belegte Preisanker-Luecken.
- `informational` bei Raw-Swaps bedeutet nicht automatisch Fehler, weil Preisanker zur Laufzeit entstehen koennen.
- Kein Treffer in diesem Bericht ist eine steuerberaterliche Endfreigabe.

## Naechster Schritt

Keine weitere automatische Preisanker-Korrektur aus diesem Audit ableiten.
Die verbleibenden `priority_2`-High-Gain-Zeilen sind separat in
`docs/229_HNT_USDT_REMAINING_INVENTORY_GAP_AUDIT_2026-05-11.md` eingeordnet:
HNT benoetigt fuer Teilreste Primaerbelege vor den Legacy-Outflows oder eine
separate fachliche Behandlung der Staking-/Custody-/Pool-Kette; USDT benoetigt
Pionex-Opening-/Bot-Historie oder eine explizite Review-Entscheidung.
