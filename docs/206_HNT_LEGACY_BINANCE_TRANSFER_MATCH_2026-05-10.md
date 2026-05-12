# HNT Legacy -> Binance Transfer-Match

- Erstellt: `2026-05-10T17:18:15.902230+00:00`
- Apply-Modus: `True`
- Kandidaten: `19`
- Neu anzulegen laut Audit: `19`
- Persistiert: `19`
- Bestehende Matches: `0`
- Konflikte: `0`

## Stand vor erneutem Rechenlauf

- Letzter 2021-Job: `1eb9d298-f95e-40c1-8cc6-c242c66162b8`
- HNT-Zero-Cost-Zeilen: `25`
- HNT-Zero-Cost-Menge: `343.44900880814716988557728`
- HNT-Zero-Cost-Erloes EUR: `7323.128519481877513947915078`

## Interpretation

- Alle Kandidaten beruhen auf identischer Helium-Legacy-Basis-TXID und einem Binance-HNT-Deposit.
- Die Mengenabweichungen liegen im erwartbaren Netzwerk-/Deposit-Delta; die Binance-Eingangsmenge wird als uebertragene Menge fortgefuehrt.
- Damit kann FIFO die urspruenglichen Mining-/Reward-Lots ueber den CEX-Transfer hinweg weitertragen.
- Persistiert wurden 19 neue Transfer-Matches.

## Stand nach Gesamtlauf 2020-2026

- Gesamtlauf: `scripts/run_current_tax_years_20260510.py`
- Aktueller Report: `docs/190_CURRENT_TAX_RUNS_2026-05-10.md`
- 2021-Job: `7a0883ae-e82f-4d6d-a090-300a52cf1875`
- Review-Gate `allow_export`: `True`
- High-Issues offen: `0`
- HNT 2021 nach Match: `8` Zero-Cost-Zeilen, `1790.06 EUR` Erloes, nur noch `medium`.
- Vorheriger Stand HNT 2021: `25` Zero-Cost-Zeilen, `7323.13 EUR` Erloes, `high`.
- Restbefund: Die verbleibenden HNT-Zeilen sind nicht mehr per gleicher Binance-Deposit-TXID belegbar. Am `2021-08-17` liegen Binance-Verkaeufe vor, aber kein entsprechender Binance-API-Deposit zwischen `2021-08-10` und `2021-08-17`; weitere Korrektur waere nur mit Opening-Lot, Primaerbeleg oder expliziter Review-Entscheidung sauber.
- AI-Readonly-Snapshot wurde nach dem Gesamtlauf aktualisiert: `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`

## Kandidaten

| TXID | Legacy Out | Binance In | Menge Out | Menge In | Delta | Sekunden | Aktion |
|---|---|---|---:|---:|---:|---:|---|
| `9WOmGxUyi6-196unX23DLEbVQJEtLEN9VQFfvGd5go8` | `d5efd947bd290986e6a1e135458eb6e237e566a55cfd03a8b1dece35e2c254c0` | `1f7b48b1c74209f37d26d62e3a8b0425c18ac5f0593d8b6291075aea0b633dbb` | 124.56891452991454 | 124.539 | 0.02991452991454 | 153 | `create` |
| `oecGPObDyTaubitJ-gjGhbpULDpsuuNgr-deaCwYxPc` | `d89e3d675ee69bd5d365f6e2e6cc91ff6f3c180c801a122dd4226dccbdf07394` | `812be9ffc30ba273b7797486c830137563992cff78f0efc8a2a65feac8459fb7` | 34.1492343186734 | 34.124 | 0.0252343186734 | 155 | `create` |
| `uJKF_6MQ9S_zhZRkeVQCl0ZQm5A4zG05AC1QSwbdJsI` | `d9b6dfdbbcafc2f050d9c6af54907dc2a36753b9a8aea9ee151b7e12cf7c5414` | `ff65d5410f99042978312039c72181cee8207b027c57bfaec10210b50833f8d8` | 28.285545014329028 | 28.261 | 0.024545014329028 | 188 | `create` |
| `IgwVzm8XJH3cLXe43jj6PbC5zb7RRdZhVxtUmTMXCkQ` | `21305620831e02e1501b3e8079755d42c95829f7e52071ae6062b5125997e4fe` | `8dd2e752f7977042967a58308b7fb78c335c6f4df43ce61704542c531029682f` | 79.02454501432904 | 79 | 0.02454501432904 | 190 | `create` |
| `s5UTv0W7IKEjmQllRvKtELqfAnVuBFoDmSBHyyQf0R4` | `c1af0c8a85387265082b910ed26066abb9204e6f4340ca15fa5972410f28a56d` | `dd5353eedbee68d33a5c687e013b67f468dac6a769af6b56b60dfd7c1e40fa2f` | 18.318453080375246 | 18.30256046 | 0.015892620375246 | 175 | `create` |
| `-zvgss0_7WYCTi7oqQ6_sNWoVonL9PEqtxccIKMNjuA` | `925cd8f8f8b2a5ad08aa422ecee5e489d0ed449f20c9410a64dc17b16cb26041` | `72b19f73949be7408e34ca7cfac9050e58258df3daeb90e3feb209a023c9b8a0` | 12.016199128949694 | 12 | 0.016199128949694 | 377 | `create` |
| `R2UoEb6ySvuEfQVstwMlUZK_knv7HO_ucFT2TZbZi9I` | `627f0db3fdea286f2137677bf10b4af8f486b06325c7ba80983979bbde2823d3` | `557afa419bd438bc7ba49477d2e43c324944df5080585804d9a44746c75c292d` | 10.014613778705638 | 10 | 0.014613778705638 | 146 | `create` |
| `dZ1tbrHdHX5OpgHnUvp9i8IwXOA-ldnGOEdAeg-SvAs` | `8d222309bcf499e0c6271c21b93259f1e1a7b6289f1f9bea209c9920887b1882` | `f3ba60cf4c6e5e7e11b29fc01753d2233c4d82d50483878004531d3ec6bdb860` | 50.01959028321952 | 50 | 0.01959028321952 | 378 | `create` |
| `Tn6lIVEoRStkHUtZ55zaUfKb34OcSFaxFazAtzp6Csc` | `644232fb5d417cb776a1c4ea4ffda289d0b266d4398e8c048f01c24f384166fb` | `936b75f0b16eb9ae991603e1241f782235bf10fc3237fd639c4f2a0a292f39c5` | 10.02057564783897 | 10 | 0.02057564783897 | 304 | `create` |
| `gkeZY5gZK8Ec43nElecA48NPuUYQ1QGMl65hetEbz64` | `d1a013f49ddc506d548d3d4754813bb5668ad0fc92abb371701461494d883c7b` | `b8278a7c79f38072542689d9e02ff2a4af6fd70661111b76dfaac0a3965a49c7` | 5.0199044585987265 | 5 | 0.0199044585987265 | 274 | `create` |
| `9PG_xLCqe2aQE5NjCK38QTgzkqQhbiSSkMEVTlqKCsg` | `cb29239263f286ed6a02b77d09792d78d9d0a727ab192246aa463ec220fd512e` | `7474e233c9f598cac57e5bd6285b6b9c09924ed5a1a910884269bca165d68853` | 4.13128299810105 | 4.11441056 | 0.01687243810105 | 250 | `create` |
| `U-F9DtdEsT5kQHQinbOA77EZ2a-xJVAy1dgg9UssFUw` | `e5880ba415ddf8f9f4c0e62a444323270d22e568a31275637f2f7b588a193320` | `cf703244ed7351f7c8d71e9775541ba2aa1ce6f207e7ea203ac22e5cad77d5c0` | 3.7503052663414063 | 3.73382087 | 0.0164843963414063 | 245 | `create` |
| `f1mpxs8gz_Jry0Ii5FqyIWw18newndSF3VdiLj8CWUE` | `48f00dbac8f098ea652c616c945241ec964db652ba56947a939a3422f3c7456b` | `5c034a592b4a8cebf00ce00e4287172113de43da0475621be1df290dc79d9658` | 1.4842662623210214 | 1.46830639 | 0.0159598723210214 | 217 | `create` |
| `yuiDuXiftCXAMhVgzk2FX8eAY9D38ANyNzEch6E-NCk` | `ed8b351600628dd6a9e1fbce11192ee07a25d7eaf285f386be9e4d49e9dad5d0` | `8815dcc1ace81d84176b50389e1e559e0da2ab8dee01e1521fbf49d489e9b6f5` | 75.0068754714609 | 75 | 0.0068754714609 | 421 | `create` |
| `i2HALMJU0zEMQS9OB-vL-JEHSFjaBUEJaqyDbc3iHb8` | `4f2a8ba0fd2625f39e4cdf8ef3b718f45a529f66b2504c079ed76be542b4c16f` | `02602144163aaa2348e4ae84c317675e20da0d9f928d38be23e7d65c98f779b4` | 3.006635319521442 | 3 | 0.006635319521442 | 582 | `create` |
| `eNJEfdS-gAr1cmdEMt6kqWdE9x0a3o380AxnVhqMFSc` | `584275b4595bbe0b92b4cc426312df059c3b57d2e851a0f6fec283d86bbf86e6` | `d150e83eb83904bc9691b2addd0d2d573f8d0e9bebdc135670a4cefd0f7874a7` | 10.00774850564534 | 10 | 0.00774850564534 | 326 | `create` |
| `dj72bxdhbOLfjlzHK9z-6c4SJ6YP0LY2NXkJPRHRBqw` | `444bb435f109aafeae640a8b3cb65dae09a58fe6f0304a275bc6cca5f227bd27` | `c64554a9ba1247e0234be59f8833014282a37eb2dad061a7b660a29241a4fe16` | 11.011985972987041 | 11 | 0.011985972987041 | 198 | `create` |
| `b_3pelYBDXuF24IR_hx6-dbVckt2j2SQnxbNHlL-4g0` | `759950f76df59630c2f222a82275aa7c2505b8ec9cfb71439648e96b9dec0da3` | `575e07c4e531c84a0af65628bf44f17229b6f602a6d2b8b078be52db6964dfaf` | 30.216623287801355 | 30.2 | 0.016623287801355 | 169 | `create` |
| `a12e2NxK6qfyqeZ01gc1Mj_qBCRZfAei-W1J6pWgEFE` | `b7f5434eecfe4cdf4ad7e390ddb5a39573cc6bcf4675cde5ce1c9281fc7efde5` | `9dd85d203cebbe23d40ff09ddd91b30758c3d255c6f80dadbb27581ab152bcba` | 450.0398803021218 | 450 | 0.0398803021218 | 484 | `create` |

JSON: `/workspace/steuerreport/var/hnt_legacy_binance_transfer_match_2026-05-10.json`
