# Bitget 2025 Blockpit Global Match - 2026-05-09

## Summary

- JSON: `/workspace/steuerreport/var/bitget_2025_blockpit_global_match_2026-05-09.json`
- Scope: `Bitget 2025 Blockpit reference rows vs Bitget API primary rows`
- Sicht: `Raw/reviewed view is used for matching so reference rows remain visible. effective_* marks rows after review actions and tax_event_overrides, but before integration-mode filtering.`
- Primary-Zeilen: `1138`
- Blockpit-Referenzzeilen: `4708`
- Matches: `665`
- Unmatched: `4043`
- Effektive matched Referenzen: `371`
- Effektive unmatched Referenzen: `2923`
- Match-Basis: `{'time_amount_asset': 665}`

## Effektive unmatched Referenzen nach Typ

- `derivative fee`: `2057`
- `derivative loss`: `399`
- `derivative profit`: `357`
- `fee`: `60`
- `trade`: `32`
- `deposit`: `7`
- `withdrawal`: `6`
- `non-taxable in`: `3`
- `non-taxable out`: `2`

## Effektive unmatched Referenzen nach Monat

- `2025-02`: `1012`
- `2025-05`: `846`
- `2025-06`: `817`
- `2025-01`: `97`
- `2025-07`: `74`
- `2025-04`: `71`
- `2025-03`: `6`

## Effektive unmatched Referenzen nach Asset

- `SOL`: `1474`
- `USDT`: `1322`
- `XRP`: `65`
- `JUP`: `49`
- `HNT`: `11`
- `EUR`: `2`

## Erste offene Referenzzeilen

- `2025-01-29T05:56:22+00:00` `deposit` `USDT` `5009.09824537` comment `Deposit` event `de574c4d0ac299676dee00c7145c09ccf67acb24bc0977afda4e67263be6a7a3`
- `2025-01-29T05:58:45+00:00` `trade` `HNT` `989.722` comment `Merged Trade` event `46c16690decb958e7242ffdca1c9a34535075629f572db08cd8a0fe23eeb0656`
- `2025-01-29T05:58:45+00:00` `fee` `HNT` `-0.989722` comment `Merged Trade` event `495817e5643d8c0b5716d41dc1ca639ccd1398dd2d8cddd4fc2c643c18c16109`
- `2025-01-29T05:58:45+00:00` `trade` `USDT` `-3640.9995719999997` comment `Merged Trade` event `e85373100ca463dfb87070aac4a5f0fcdfe7a7565d4b22c0e4a9a53778805ba3`
- `2025-01-29T05:58:45+00:00` `fee` `HNT` `-0.989722` comment `Merged Trade` event `ffe3aaa7b5a0c1f7b9bc6d401ac1385cd1774ef44c362f583ea93a03e25417ae`
- `2025-01-29T05:59:03+00:00` `fee` `HNT` `-0.012` comment `Merged Trade` event `025298398379ea0d3c118913e0d0e50d894802fd06e634d7cd685291ea26e38b`
- `2025-01-29T05:59:03+00:00` `fee` `HNT` `-0.012` comment `Merged Trade` event `40b2557ed01688ba9900840d7024295e90d25d789356947bf6ccccc9da3b4a91`
- `2025-01-29T06:03:58+00:00` `derivative fee` `USDT` `-0.2926968` comment `Position Open Fee (JUPUSDT)` event `1587d822d123589486203da3e7129e7de9dacaf403a6f4608d957f9977346488`
- `2025-01-29T06:03:58+00:00` `derivative fee` `USDT` `-0.34325352` comment `Position Open Fee (JUPUSDT)` event `5bdb70ad9f3c3ade972b52b166f98ae265bff49d28539aa1e8b6a7b6818ed887`
- `2025-01-29T06:03:58+00:00` `derivative fee` `USDT` `-0.63994164` comment `Position Open Fee (JUPUSDT)` event `797a515d52d39607a871cbbb919ab334ab26283f535afc1bc6d5bfc2a1a26feb`
- `2025-01-29T06:03:58+00:00` `derivative fee` `USDT` `-0.00731742` comment `Position Open Fee (JUPUSDT)` event `7da272379565e0178b40d7bffd9931f6fa50ed8049ab5cf1bfeff8085df0fe8e`
- `2025-01-29T06:03:58+00:00` `derivative fee` `USDT` `-0.59337624` comment `Position Open Fee (JUPUSDT)` event `a132d4e6677b7aefd0575a59596ac55d4ce586aeeb6484b0bb3e5f793af0cc6a`
- `2025-01-29T06:03:58+00:00` `derivative fee` `USDT` `-0.31065774` comment `Position Open Fee (JUPUSDT)` event `c05ba1044ecfa8c0daf9ea6e97371ce641a7c13192ffde7aa4cf9df5393eca85`
- `2025-01-29T06:03:58+00:00` `derivative fee` `USDT` `-0.17894418` comment `Position Open Fee (JUPUSDT)` event `fea4e1b819d8763b09f14f3add12998efa1097df2f5f41241eb0a75f01375c0e`
- `2025-01-29T06:05:56+00:00` `derivative fee` `USDT` `-1.3504725` comment `Position Close Fee (JUPUSDT)` event `14bce7a1f9000164189d523751c8e4dd3a6dbade8ccbf558978f42c81e0093ef`
- `2025-01-29T06:05:56+00:00` `derivative fee` `USDT` `-0.11938584` comment `Position Close Fee (JUPUSDT)` event `255cc827c4c2bb1e08f16198c0191ddb3677259d73824ed4853c429627b68dbe`
- `2025-01-29T06:05:56+00:00` `derivative loss` `USDT` `-5.67` comment `PnL (JUPUSDT)` event `36f309cd8636acb10f4c22e01e81f5a9f81aa20f18e1f0681cb5f7e170137b4f`
- `2025-01-29T06:05:56+00:00` `derivative fee` `USDT` `-0.16740696` comment `Position Close Fee (JUPUSDT)` event `4515b3787da53a8544668e909304e0be216c7879288a0753ad217fb416c7cbeb`
- `2025-01-29T06:05:56+00:00` `derivative fee` `USDT` `-0.1433964` comment `Position Close Fee (JUPUSDT)` event `871efd9cf2adcfc4c43dd97000fdf497af995c73d37b1d61d3477fb6defcfb8f`
- `2025-01-29T06:05:56+00:00` `derivative loss` `USDT` `-0.6235` comment `PnL (JUPUSDT)` event `8955779a8a6a6fa5f4fcdabf2fa1078a4abc89487f72b3b5b64fa644f515f3fb`
- `2025-01-29T06:05:56+00:00` `derivative loss` `USDT` `-1.9488` comment `PnL (JUPUSDT)` event `c36aad02f2331d35e2ebaa38afb495466d44b2d20b8cac8bc4b18983845af92e`
- `2025-01-29T06:05:56+00:00` `derivative fee` `USDT` `-0.1433964` comment `Position Close Fee (JUPUSDT)` event `cf6dcd852b2f65d8e7ceba214dcd24292801b5b0cd17abb75e0c35291a4b58d2`
- `2025-01-29T06:05:56+00:00` `derivative fee` `USDT` `-0.44819712` comment `Position Close Fee (JUPUSDT)` event `f207d0be0f07a072160ceab02670261bb422b1a4796e41e133cc545c17c6ea0d`
- `2025-01-29T06:07:23+00:00` `derivative fee` `USDT` `-0.47586792` comment `Position Open Fee (JUPUSDT)` event `181f1a2877cb46d162ae8c2267661146ead0e6bcd1de2e043cf9b459cf030683`
- `2025-01-29T06:07:23+00:00` `derivative fee` `USDT` `-0.06912048` comment `Position Open Fee (JUPUSDT)` event `1e3f31222e39cb23bdc86626f187df7954bf2b6f395df74e91486acf5c94dbbe`
- `2025-01-29T06:07:23+00:00` `derivative fee` `USDT` `-0.18343512` comment `Position Open Fee (JUPUSDT)` event `2e66645e6a8212368bbaabed8e5506535353623a6d471399dad23818b88f6b46`
- `2025-01-29T06:07:23+00:00` `derivative fee` `USDT` `-0.17878278` comment `Position Open Fee (JUPUSDT)` event `5aac0bfb024e9a5c371f12295f1205b11e3416db1e3b8d8ac6545de1b874f16a`
- `2025-01-29T06:07:23+00:00` `derivative fee` `USDT` `-0.07906836` comment `Position Open Fee (JUPUSDT)` event `857cc99bcf48ff1188225248834094add572688ecd7f53c8b35940807eca29aa`
- `2025-01-29T06:07:23+00:00` `derivative fee` `USDT` `-0.245865` comment `Position Open Fee (JUPUSDT)` event `8680e1dcb4bb8a30537ce7df9d6e7ff4909f8520a8d879cf4572912e2c9f8cf4`
- `2025-01-29T06:07:23+00:00` `derivative fee` `USDT` `-0.96560568` comment `Position Open Fee (JUPUSDT)` event `b56b73fed6644def091778cf4091df8a4e5f68799595d6a4963e6fa1f1ea6820`
- `2025-01-29T06:07:23+00:00` `derivative fee` `USDT` `-0.00930468` comment `Position Open Fee (JUPUSDT)` event `dadffa986ade51f658d854a4af8bf3ddbcf5dea29962485b4eed0a2301d5e5ed`
- `2025-01-29T06:07:23+00:00` `derivative fee` `USDT` `-0.1262778` comment `Position Open Fee (JUPUSDT)` event `f33042b1ba50658de3f2f1bf3c5ad2d4b5cc67c394dd0fcde269743a5a45a537`
- `2025-01-29T08:00:08+00:00` `derivative fee` `USDT` `-0.197054875` comment `contract_main_settle_fee (JUPUSDT)` event `7df41d89a1c6e4f00ac2c84e9da3f8ed1e527e2f9b68db201b061196f3cb8818`
- `2025-01-29T13:02:30+00:00` `derivative fee` `USDT` `-0.807978` comment `Position Close Fee (JUPUSDT)` event `19333f0c6f31eacd016bbc0f2de2ce2158000bf4353a0f9df817845c44c8836c`
- `2025-01-29T13:02:30+00:00` `derivative fee` `USDT` `-0.6423555` comment `Position Close Fee (JUPUSDT)` event `4eb1ab6fe5420dda9368bf144966aaee5e728bb9fcdf99c94c85b1cde089d087`
- `2025-01-29T13:02:30+00:00` `derivative fee` `USDT` `-0.29490024` comment `Position Close Fee (JUPUSDT)` event `5a0ef1f6c33a05eb122e698fd78fb261082f2b58ef567197b8de23bc7be7df5d`
- `2025-01-29T13:02:30+00:00` `derivative loss` `USDT` `-11.362426488934` comment `PnL (JUPUSDT)` event `6687015385e3790085f0a4855c4a364f95e03dc5a1179c626233bb19434cb5d2`
- `2025-01-29T13:02:30+00:00` `derivative fee` `USDT` `-0.0064956` comment `Position Close Fee (JUPUSDT)` event `788c888fa40f1253c4c9b21da0cbb597c1b3753b73770a672fd8fe237b95018f`
- `2025-01-29T13:02:30+00:00` `derivative loss` `USDT` `-31.258449674524` comment `PnL (JUPUSDT)` event `7b10f946bf595d93109c66bb9f1869ea25c75e5777f8df53075b057e06984a11`
- `2025-01-29T13:02:30+00:00` `derivative fee` `USDT` `-0.23579028` comment `Position Close Fee (JUPUSDT)` event `8cdb97ac993dfd63342a57e0d9c2cb2ee4302d129752c7b5126ceef30d36a3c4`
- `2025-01-29T13:02:30+00:00` `derivative fee` `USDT` `-0.29295156` comment `Position Close Fee (JUPUSDT)` event `a346301fd0ef2259f288cebe58342315554ac1323d4544713dca9a2949b043fa`
- `2025-01-29T13:02:30+00:00` `derivative loss` `USDT` `-9.084935716923` comment `PnL (JUPUSDT)` event `dde3b8308f72f84c97152cabef7a14b6a4f1163ecd1c2025a1a10d2d126f4154`
- `2025-01-29T13:02:30+00:00` `derivative loss` `USDT` `-0.25027371121` comment `PnL (JUPUSDT)` event `e60250621b35e3937915acecc01f407bc6b234f8b235ee9ec2d35b8c448345b7`
- `2025-01-29T13:02:30+00:00` `derivative loss` `USDT` `-11.287344375571` comment `PnL (JUPUSDT)` event `e60eb021828b6e6bd0609b593ba30e22ebf3407aaf4c963d2a1d633f58faf7a1`
- `2025-01-29T13:03:05+00:00` `derivative fee` `USDT` `-0.5740641` comment `Position Open Fee (JUPUSDT)` event `694bd27b0dfac02c9bb7bcecac2fe28459da9bda4f1e52d9a5200483b477486b`
- `2025-01-29T13:03:05+00:00` `derivative fee` `USDT` `-0.02075712` comment `Position Open Fee (JUPUSDT)` event `aa575c5c2f7e72c0baef76443add62f854135602325788bbdea13fccf07b4f45`
- `2025-01-29T13:03:05+00:00` `derivative fee` `USDT` `-0.96196278` comment `Position Open Fee (JUPUSDT)` event `b8456941a00384662db67116aaa0dbc9e2e16dbf218a0449c7c9fd651cbfb44d`
- `2025-01-29T13:03:05+00:00` `derivative fee` `USDT` `-0.11935344` comment `Position Open Fee (JUPUSDT)` event `d918948da0eff14f2a6dd4d2a74c6ebd244bf5ca6ae92f95f2791b1b1ee2ced0`
- `2025-01-29T13:03:05+00:00` `derivative fee` `USDT` `-0.11611014` comment `Position Open Fee (JUPUSDT)` event `e9725383dd2b00678899408b9a94ba699cbfb2853baacec189642712d6005d83`
- `2025-01-29T13:03:05+00:00` `derivative fee` `USDT` `-0.38206074` comment `Position Open Fee (JUPUSDT)` event `f78c9d580bd731922cbeb1e4d8b590315d7ce80a81c06a8c12bab95824d7eed3`
- `2025-01-29T16:00:08+00:00` `derivative profit` `USDT` `0.18063170448` comment `contract_main_settle_fee (JUPUSDT)` event `9104d674ee3d843a8b18951abd92cf3b5993c557cfea6d3e9909928344615140`
- `2025-01-29T19:44:19+00:00` `derivative fee` `USDT` `-1.38142704` comment `Position Close Fee (JUPUSDT)` event `05102ec046e5b66969260d803edf76963e036723579dfab32883d4240be2d01e`
- `2025-01-29T19:44:19+00:00` `derivative loss` `USDT` `-46.1227` comment `PnL (JUPUSDT)` event `5583341c32698a8fea04e5ef1053cbfb1ba7dcf1b20b6c6e57e5853db6168249`
- `2025-01-29T19:44:19+00:00` `derivative fee` `USDT` `-0.58315152` comment `Position Close Fee (JUPUSDT)` event `ad2054c9631ed78109e2ba44daf3912bee6784a1e593146a2f0085788b9c6eb3`
- `2025-01-29T19:44:19+00:00` `derivative loss` `USDT` `-19.4701` comment `PnL (JUPUSDT)` event `bbc7048ebedb9016853e6e1539b1c14af333757dccd9aa52f2f804966dc0454b`
- `2025-01-29T19:44:19+00:00` `derivative fee` `USDT` `-0.03177216` comment `Position Close Fee (JUPUSDT)` event `c5661aa899fd2b612065c22d31017c09ce1dd3f6e8ced9568f2bd551eadffab3`
- `2025-01-29T20:00:06+00:00` `derivative profit` `USDT` `0.018255173328` comment `contract_main_settle_fee (JUPUSDT)` event `fd46a9d5dcdef635777efa8d5ac77bb5a793b3bdc86611d7bd929b140cb820b7`
- `2025-01-30T00:00:05+00:00` `derivative fee` `USDT` `-0.0142650144` comment `contract_main_settle_fee (JUPUSDT)` event `48caa54c83ac278f106b46c107e7a718429f9b24efb6f3bb6c0247e97046c5e8`
- `2025-01-30T04:00:05+00:00` `derivative profit` `USDT` `0.005001279696` comment `contract_main_settle_fee (JUPUSDT)` event `4cbe4e166dfd8796cf4ad8af1d969c9d617020d6619dd840a6765af169691d96`
- `2025-01-30T05:36:02+00:00` `fee` `USDT` `-0.599999634` comment `Merged Trade` event `0d8f11abecc7c790ad06c3d01a0942485011237daa2d3f35e14911a36b99b143`
- `2025-01-30T05:36:02+00:00` `trade` `HNT` `-140.283` comment `Merged Trade` event `46b3a3568607956ddb14b2bf5230ee40f1987b6f25e9639ae7a9781a6c716dda`
- `2025-01-30T05:36:02+00:00` `fee` `USDT` `-0.599999634` comment `Merged Trade` event `a669fc834be45fd9be9761900c62da635ef62474eba35e64b8346e4b8cbebb2d`
- `2025-01-30T05:36:02+00:00` `trade` `USDT` `599.999634` comment `Merged Trade` event `ef3d9b08555962cea19cc65056f894fa48b3ecfaa3b08d54a9df08cab441cc68`
- `2025-01-30T08:00:11+00:00` `derivative profit` `USDT` `0.018674541648` comment `contract_main_settle_fee (JUPUSDT)` event `df24fa83fc850df2baabedaa622fb5477ac3461331549b9c58e46e831ec10a55`
- `2025-01-30T16:06:55+00:00` `derivative fee` `USDT` `-0.32397162` comment `Position Open Fee (JUPUSDT)` event `357fde4165a9e990934c62489313010ea27da12c5342440d551336a86331ebda`
- `2025-01-30T16:06:55+00:00` `derivative fee` `USDT` `-0.65982` comment `Position Open Fee (JUPUSDT)` event `a05ffc5888ebe0d789bb9a7b6b7ee4607e62a0c4bda3b58419b3ffd5c71adde6`
- `2025-01-30T16:06:55+00:00` `derivative fee` `USDT` `-0.33584838` comment `Position Open Fee (JUPUSDT)` event `daf76e83f91249fd61c28b88aac96c5f4d7075df3563e3dda7fc258a1bb2f2da`
- `2025-01-30T16:06:55+00:00` `derivative fee` `USDT` `-0.50273712` comment `Position Open Fee (JUPUSDT)` event `ef52d4576a1814622017ede7ae59d661b294adb674147c2547f1953d33ad7d06`
- `2025-01-31T00:00:02+00:00` `derivative fee` `USDT` `-0.1325809` comment `contract_main_settle_fee (JUPUSDT)` event `faf6d28609453c6844e36ce6e49ead4fa03f4d68471cfcc97e999f55e0aedb0a`
- `2025-01-31T04:00:02+00:00` `derivative fee` `USDT` `-0.12690406` comment `contract_main_settle_fee (JUPUSDT)` event `b0d86c61e8c37b1c7358dcc68711a65f5e8ec6d2edbc4ec19bb794c8ed4d3d21`
- `2025-01-31T10:47:26+00:00` `derivative fee` `USDT` `-0.21004704` comment `Position Close Fee (JUPUSDT)` event `8b563dc83373732164f0bdd0be17aee5738c58752813a6cc9e36c1b7cd9d40e9`
- `2025-01-31T10:47:26+00:00` `derivative profit` `USDT` `13.1712` comment `PnL (JUPUSDT)` event `c12ec03ebcab396568df27b4587101f370f778349101f8246f3d49d389fd6fe7`
- `2025-01-31T18:22:30+00:00` `derivative fee` `USDT` `-0.2595054` comment `Position Open Fee (JUPUSDT)` event `1c72b2ec82c378c9b8ccc8867d1aa23813a2996802dca9c0b58ac586b6f987ed`
- `2025-01-31T18:22:30+00:00` `derivative fee` `USDT` `-0.2057055` comment `Position Open Fee (JUPUSDT)` event `46ee4b75f45634f684c1f1e80f511ab402024a29cd1293a9883251b80fb9d5f7`
- `2025-01-31T18:22:30+00:00` `derivative fee` `USDT` `-0.13418328` comment `Position Open Fee (JUPUSDT)` event `507f5a9a01bb4052014c59653a00d6e34d18866eb2c26ae6738a593fb94c3912`
- `2025-01-31T18:22:30+00:00` `derivative fee` `USDT` `-0.46710972` comment `Position Open Fee (JUPUSDT)` event `7b254700056bd0b8b8a4a5909d6194c794fa2ef53ad858d4a1ed3843f1a937c4`
- `2025-01-31T18:22:30+00:00` `derivative fee` `USDT` `-0.284823` comment `Position Open Fee (JUPUSDT)` event `a5c6f28cb00b1551dbbafeeb67955327ad8492cb3a56519ee37c46f10c2dccb7`
- `2025-01-31T18:22:30+00:00` `derivative fee` `USDT` `-0.74623626` comment `Position Open Fee (JUPUSDT)` event `ce908629984f26f861fe458826684e0fcf1714efee42c80d1965124f5a06493d`
- `2025-01-31T18:22:30+00:00` `derivative fee` `USDT` `-0.94932` comment `Position Open Fee (JUPUSDT)` event `e754b81fc0b2ded3ef635dd4e01c921070b7116eaaad4b05ef537928275bbcfe`
- `2025-01-31T18:22:30+00:00` `derivative fee` `USDT` `-0.12215742` comment `Position Open Fee (JUPUSDT)` event `f82fb463ae4f71c6d109159910210bea95875c0110068eaf2c08eb99d06a2b91`

## Bewertung

2923 aktuell effektive Bitget-Blockpit-Referenzzeilen 2025 bleiben ohne 1:1-API-Match. Sie duerfen nicht automatisch als Primary behandelt werden; sie sind aber gute Suchanker fuer Bitget-Supportexport, On-Chain-Transfers, PnL-/Funding-Summen und lokale KI-Priorisierung.
