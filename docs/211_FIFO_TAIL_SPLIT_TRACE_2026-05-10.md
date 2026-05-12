# FIFO Tail-Split Trace - 2026-05-10

- Created UTC: `2026-05-10T18:42:31.730054+00:00`
- Zweck: Pruefen, warum Zero-Cost-Restmengen entstehen, obwohl dasselbe Verkaufs-Event teilweise Cost Basis hat.

## USDT 2022

- Job: `3bf608f7-31c4-430c-855f-3a88dd123ed8`
- Zero-Cost-Zeilen: `3`
- Betroffene Source-Events: `3`

### Event `fe030531d67b4c88a2f56f81b84f438ee42b49096cc8b6a115b98e888071c449`

- Zeit: `2022-01-05T15:36:46+00:00`
- Verkaufte Menge: `186.27 USDT`
- FIFO-Lots vorher: `2` / `111.1653777938 USDT`
- Gematchte Lots: `2`
- Zero-Cost-Restmenge: `75.1046222062 USDT`
- FIFO-Lots danach: `0` / `0 USDT`

Tax-Lines fuer dieses Source-Event:

| Line | Menge | Cost Basis EUR | Erloes EUR | Lot Source |
|---:|---:|---:|---:|---|
| 410 | 82.49457481190000000000 | 72.8814820090692930000000000 | 72.8814820090692930000000000 | `2eb62c8f7170a51c138bbd652b4f2fd7c6f2f2794e85acf9123ad6e7949048b6` |
| 411 | 28.67080298190000000000 | 25.3297943104191930000000000 | 25.3297943104191930000000000 | `564124ea97b535a2dd9faf2845b89b51d5be5ec24c40573af56631ff5c16486c` |
| 412 | 75.10462220620000000000 | 0 | 66.3526805805115140000000000 | `empty` |

FIFO-Lots vor dem Event (erste 12):

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 82.4945748119 | 0.88347 | `2022-01-05T11:39:12+00:00` | `2eb62c8f7170a51c138bbd652b4f2fd7c6f2f2794e85acf9123ad6e7949048b6` |
| 28.6708029819 | 0.88347 | `2022-01-05T11:39:22+00:00` | `564124ea97b535a2dd9faf2845b89b51d5be5ec24c40573af56631ff5c16486c` |

Gematchte Lots:

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 82.4945748119 | 0.88347 | `2022-01-05T11:39:12+00:00` | `2eb62c8f7170a51c138bbd652b4f2fd7c6f2f2794e85acf9123ad6e7949048b6` |
| 28.6708029819 | 0.88347 | `2022-01-05T11:39:22+00:00` | `564124ea97b535a2dd9faf2845b89b51d5be5ec24c40573af56631ff5c16486c` |

### Event `a20292c0e922503226ea223723d3863a9325cd51f5cf1bd53734dd0f387b2513`

- Zeit: `2022-01-19T12:45:42+00:00`
- Verkaufte Menge: `479.99307717 USDT`
- FIFO-Lots vorher: `3` / `311.22839367 USDT`
- Gematchte Lots: `3`
- Zero-Cost-Restmenge: `168.7646835 USDT`
- FIFO-Lots danach: `0` / `0 USDT`

Tax-Lines fuer dieses Source-Event:

| Line | Menge | Cost Basis EUR | Erloes EUR | Lot Source |
|---:|---:|---:|---:|---|
| 439 | 26.78592680000000000000 | 23.5646512430320000000000000 | 23.6104551778600000000000000 | `ccbc3631c190eb2a28c05315e8cbbea3d07ef68ad319330ba748a621881e6f10` |
| 440 | 163.97883375000000000000 | 144.5391430089375000000000000 | 144.5391430089375000000000000 | `7dfb5cfa6163d6287862f188e656027cbd4a6cf4bf1fac3a4e999fe323f44e65` |
| 441 | 120.46363312000000000000 | 106.1826694136240000000000000 | 106.1826694136240000000000000 | `0e6e9a4ba67121beb317e576e1b50139aa769545cfb8976ace2f0c10d5222b4d` |
| 442 | 168.76468350000000000000 | 0 | 148.7576302710750000000000000 | `empty` |

FIFO-Lots vor dem Event (erste 12):

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 26.7859268 | 0.87974 | `2022-01-18T23:55:30+00:00` | `ccbc3631c190eb2a28c05315e8cbbea3d07ef68ad319330ba748a621881e6f10` |
| 163.97883375 | 0.88145 | `2022-01-19T11:22:49+00:00` | `7dfb5cfa6163d6287862f188e656027cbd4a6cf4bf1fac3a4e999fe323f44e65` |
| 120.46363312 | 0.88145 | `2022-01-19T12:39:11+00:00` | `0e6e9a4ba67121beb317e576e1b50139aa769545cfb8976ace2f0c10d5222b4d` |

Gematchte Lots:

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 26.7859268 | 0.87974 | `2022-01-18T23:55:30+00:00` | `ccbc3631c190eb2a28c05315e8cbbea3d07ef68ad319330ba748a621881e6f10` |
| 163.97883375 | 0.88145 | `2022-01-19T11:22:49+00:00` | `7dfb5cfa6163d6287862f188e656027cbd4a6cf4bf1fac3a4e999fe323f44e65` |
| 120.46363312 | 0.88145 | `2022-01-19T12:39:11+00:00` | `0e6e9a4ba67121beb317e576e1b50139aa769545cfb8976ace2f0c10d5222b4d` |

### Event `b5422e7c322b53d701869335a500c9b7e48334f50b6e8410978e247e608e0399`

- Zeit: `2022-01-19T12:56:19+00:00`
- Verkaufte Menge: `2572.15382077 USDT`
- FIFO-Lots vorher: `2` / `1246.195058 USDT`
- Gematchte Lots: `2`
- Zero-Cost-Restmenge: `1325.95876277 USDT`
- FIFO-Lots danach: `0` / `0 USDT`

Tax-Lines fuer dieses Source-Event:

| Line | Menge | Cost Basis EUR | Erloes EUR | Lot Source |
|---:|---:|---:|---:|---|
| 512 | 0.810868 | 0.71473959860 | 0.71473959860 | `833d7879a047e84198c8e407b8e43320278ba4098ba1a5b46e1df1dffb7550a7` |
| 513 | 1245.38419000 | 1097.7438942755000 | 1097.7438942755000 | `59feec35093a516eb72450330cdcaefed4a779b175fca223fc53d99f125ed18a` |
| 514 | 1325.95876277000000000000 | 0 | 1168.766351443616500000000000 | `empty` |

FIFO-Lots vor dem Event (erste 12):

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 0.810868 | 0.88145 | `2022-01-19T12:47:35+00:00` | `833d7879a047e84198c8e407b8e43320278ba4098ba1a5b46e1df1dffb7550a7` |
| 1245.38419 | 0.88145 | `2022-01-19T12:54:09+00:00` | `59feec35093a516eb72450330cdcaefed4a779b175fca223fc53d99f125ed18a` |

Gematchte Lots:

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 0.810868 | 0.88145 | `2022-01-19T12:47:35+00:00` | `833d7879a047e84198c8e407b8e43320278ba4098ba1a5b46e1df1dffb7550a7` |
| 1245.38419 | 0.88145 | `2022-01-19T12:54:09+00:00` | `59feec35093a516eb72450330cdcaefed4a779b175fca223fc53d99f125ed18a` |

## JUP 2024

- Job: `356890b8-99b7-4562-89d0-79f4aa21804c`
- Zero-Cost-Zeilen: `3`
- Betroffene Source-Events: `3`

### Event `6f655c8ee3801583412180d520fc51b7671a97a8345a1c7102c420e5c91a6b13`

- Zeit: `2024-11-19T21:14:21+00:00`
- Verkaufte Menge: `5812.211205 JUP`
- FIFO-Lots vorher: `4` / `4066.959979 JUP`
- Gematchte Lots: `4`
- Zero-Cost-Restmenge: `1745.251226 JUP`
- FIFO-Lots danach: `0` / `0 JUP`

Tax-Lines fuer dieses Source-Event:

| Line | Menge | Cost Basis EUR | Erloes EUR | Lot Source |
|---:|---:|---:|---:|---|
| 1494 | 412.221918 | 298.5176300071105050945783243 | 440.7397046931155340732017340 | `80aeffee3ae8a66f538e01afdef0bac70a8ff19ad83fd58f940158f00823c94d` |
| 1495 | 55.78179 | 59.033823731568 | 59.64081136474986069859871874 | `f52d10c6a0804c299af3f659aa37a874673cb20c71b93ee2ad7cb13553ee22e6` |
| 1496 | 2311.92000 | 2648.253856863506578357000000 | 2471.860164587627932812918872 | `4a5ed71ab43519c610ce03002d4dbd85351996b872de42cb1fe2667be1620469` |
| 1497 | 1287.036271 | 1475.720027544536431634000000 | 1376.074296975806648752109782 | `433f0bf9039ca625f998821bab905f28e72a15dbfc90c3aca355b2be2b62877e` |
| 1498 | 1745.251226 | 0 | 1865.988867585002696535170893 | `empty` |

FIFO-Lots vor dem Event (erste 12):

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 412.221918 | 0.7241672918690133917007739611 | `2024-08-28T08:28:10+00:00` | `80aeffee3ae8a66f538e01afdef0bac70a8ff19ad83fd58f940158f00823c94d` |
| 55.78179 | 1.0582992 | `2024-11-17T09:11:50+00:00` | `f52d10c6a0804c299af3f659aa37a874673cb20c71b93ee2ad7cb13553ee22e6` |
| 2311.92 | 1.145478155326960525605124745 | `2024-11-18T04:52:51+00:00` | `4a5ed71ab43519c610ce03002d4dbd85351996b872de42cb1fe2667be1620469` |
| 1287.036271 | 1.146603293781249177890496297 | `2024-11-18T04:54:41+00:00` | `433f0bf9039ca625f998821bab905f28e72a15dbfc90c3aca355b2be2b62877e` |

Gematchte Lots:

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 412.221918 | 0.7241672918690133917007739611 | `2024-08-28T08:28:10+00:00` | `80aeffee3ae8a66f538e01afdef0bac70a8ff19ad83fd58f940158f00823c94d` |
| 55.78179 | 1.0582992 | `2024-11-17T09:11:50+00:00` | `f52d10c6a0804c299af3f659aa37a874673cb20c71b93ee2ad7cb13553ee22e6` |
| 2311.92 | 1.145478155326960525605124745 | `2024-11-18T04:52:51+00:00` | `4a5ed71ab43519c610ce03002d4dbd85351996b872de42cb1fe2667be1620469` |
| 1287.036271 | 1.146603293781249177890496297 | `2024-11-18T04:54:41+00:00` | `433f0bf9039ca625f998821bab905f28e72a15dbfc90c3aca355b2be2b62877e` |

### Event `856a7af46c6f4737a8554310d8c0efb142a2b1bee0212724f61141884f6e0979`

- Zeit: `2024-11-22T15:25:20+00:00`
- Verkaufte Menge: `646.471986 JUP`
- FIFO-Lots vorher: `2` / `540 JUP`
- Gematchte Lots: `2`
- Zero-Cost-Restmenge: `106.471986 JUP`
- FIFO-Lots danach: `0` / `0 JUP`

Tax-Lines fuer dieses Source-Event:

| Line | Menge | Cost Basis EUR | Erloes EUR | Lot Source |
|---:|---:|---:|---:|---|
| 1520 | 140.000000 | 143.8544460523300662753000000 | 147.8738040281139604095698589 | `8fd71489db2c430b761fb64b257be7a1573cdada8b6eaba1919af946b5fcbff2` |
| 1521 | 400.000000 | 398.2684589778848842000000000 | 422.4965829374684583130567396 | `8286293acff038ca32dd47c5b28e3e0ed360036d14242f5806b07cb061dc24c0` |
| 1522 | 106.471986 | 0 | 112.4601256589149514223734020 | `empty` |

FIFO-Lots vor dem Event (erste 12):

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 140 | 1.027531757516643330537857143 | `2024-11-20T22:05:59+00:00` | `8fd71489db2c430b761fb64b257be7a1573cdada8b6eaba1919af946b5fcbff2` |
| 400 | 0.9956711474447122105 | `2024-11-21T20:12:13+00:00` | `8286293acff038ca32dd47c5b28e3e0ed360036d14242f5806b07cb061dc24c0` |

Gematchte Lots:

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 140 | 1.027531757516643330537857143 | `2024-11-20T22:05:59+00:00` | `8fd71489db2c430b761fb64b257be7a1573cdada8b6eaba1919af946b5fcbff2` |
| 400 | 0.9956711474447122105 | `2024-11-21T20:12:13+00:00` | `8286293acff038ca32dd47c5b28e3e0ed360036d14242f5806b07cb061dc24c0` |

### Event `79935c700666f033f384c1b6145a597297499eb20e7d7aef88b6856ed2002d98`

- Zeit: `2024-11-24T11:23:20+00:00`
- Verkaufte Menge: `8525.295277 JUP`
- FIFO-Lots vorher: `1` / `8524.295277 JUP`
- Gematchte Lots: `1`
- Zero-Cost-Restmenge: `1 JUP`
- FIFO-Lots danach: `0` / `0 JUP`

Tax-Lines fuer dieses Source-Event:

| Line | Menge | Cost Basis EUR | Erloes EUR | Lot Source |
|---:|---:|---:|---:|---|
| 1577 | 8524.295277 | 9506.593565094546553961000003 | 9067.045689438200038124453680 | `30cc738554ec504bf92ecc81de0c3224811af422ef6c17fc48ab43993f022c7d` |
| 1578 | 1.000000 | 0 | 1.063671000921640180546323616 | `empty` |

FIFO-Lots vor dem Event (erste 12):

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 8524.295277 | 1.115235131606122864009864355 | `2024-11-23T05:43:01+00:00` | `30cc738554ec504bf92ecc81de0c3224811af422ef6c17fc48ab43993f022c7d` |

Gematchte Lots:

| Menge | Unit Cost EUR | Zeit | Source Event |
|---:|---:|---|---|
| 8524.295277 | 1.115235131606122864009864355 | `2024-11-23T05:43:01+00:00` | `30cc738554ec504bf92ecc81de0c3224811af422ef6c17fc48ab43993f022c7d` |

## Bewertung

- Zero-Cost-Tail-Splits entstehen, wenn der FIFO-Pool fuer das Asset innerhalb eines Verkaufs-Events erschoepft wird.
- Ein Fix darf nicht am Verkaufs-Event ansetzen, sondern muss fehlende/ausgefilterte Inflows oder Transferlot-Fortschreibung vor diesem Zeitpunkt klaeren.
