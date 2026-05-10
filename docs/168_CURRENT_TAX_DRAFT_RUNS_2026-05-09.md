# Current Tax Runs - 2026-05-09

> Stand 2026-05-10: Dieser vorher final freigegebene Stand wurde durch das neue Nullbasis-Review-Gate fachlich ueberholt. Aktueller Gate-Status siehe `docs/177_ZERO_COST_TAX_LOT_GATE_2026-05-10.md`.

## Ergebnis

- Neu berechnete Steuerjahre: `7`
- Gesamt Tax Lines: `3320`
- Gesamt Derivative Lines: `36`
- Export-Gate: `True`
- Offene Balance-Review-Kandidaten: `0`

Die Laeufe sind nach aktuellem Review-Gate final exportfaehig. Alte Pionex-USDT-Kontextluecke ist als nicht steuerwirksame Bestandsnormalisierung dokumentiert und freigegeben.

## Jahresuebersicht

| Jahr | Job | Tax Lines | Derivate | Anlage SO netto EUR | Leistungen EUR | Termingeschaefte netto EUR | Derivate Verlustsumme EUR | Valuation offen | Short-Sell-Hinweise |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020 | `b9da157a-5d07-495e-9291-f4526e8c499e` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2021 | `66fe27cc-e418-4ea5-8097-98ab5b42cabb` | 1184 | 0 | -417.6895697009901493149258807 | 12035.69168383139309885257935 | 0 | 0 | 0 | 28 |
| 2022 | `1805e7af-5a85-40f9-b8a5-519b1728c5ca` | 1062 | 0 | 1627.8686857715986397 | 9761.711828427325809098030511 | 0 | 0 | 0 | 35 |
| 2023 | `c8065ea8-d697-4721-8873-d091478b5341` | 46 | 0 | -520.2114501355709852534179687 | 1591.789580302749903677688467 | 0 | 0 | 1138 | 43 |
| 2024 | `33e3a5fb-d8d1-42e1-bef5-c24da36e3e26` | 568 | 36 | 3027.572248861479533868824956 | 2291.938703634026589700257328 | -8413.69 | 20149.13 | 97 | 66 |
| 2025 | `d4cb13ef-42fd-4943-8554-db36dd895fd4` | 459 | 0 | 24340.62618522825396375739798 | 747.7890097989682380400235705 | 0 | 0 | 22 | 75 |
| 2026 | `1831aa17-fc4d-4a90-8dbf-330e1c2a64b7` | 1 | 0 | -0.000004999999999999999999999999999 | 26.62449231868769297855626282 | 0 | 0 | 1 | 76 |

## Offene Gate-Blocker


## Offene Balance-Kandidaten


## Export-Hinweis

- Exportdateien koennen ueber `GET /api/v1/report/files/{job_id}` gelistet werden.
- Einzelne Downloads laufen ueber `/api/v1/report/export?job_id=<job>&scope=<all|tax|derivatives>&fmt=<json|csv|pdf|wiso>`.
- WISO-CSV ist nach aktuellem Review-Gate final exportfaehig.
