# Current Zero-Cost Root-Cause Audit - 2026-05-10

## Ergebnis

- Quelle: Live-DB `/root/.local/share/steuerreport/steuerreport.db`.
- Scope: aktuellste completed Processing-Jobs je Steuerjahr.
- Zweck: Current-State-Abgleich nach KI-Queue und FIFO-Tail-Trace.

## Aktuelle Nullkosten-Zusammenfassung

| Jahr | Asset | Zeilen | Menge | Erlös EUR |
|---:|---|---:|---:|---:|
| 2021 | `BNB` | 2 | 1.625 | 0.0031290949999999997 |
| 2021 | `HNT` | 8 | 91.34915638559784 | 1790.0592436079921 |
| 2021 | `UNKNOWN` | 3 | 6.340749 | 11.506435555656026 |
| 2022 | `HNT` | 5 | 439.68801021965726 | 2300.1340507290993 |
| 2022 | `USDT` | 3 | 1569.8280684762 | 1383.876662295203 |
| 2024 | `USDC` | 1 | 2e-06 | 1.893578471013763e-06 |

## USDT 2022

- Aktuelle Nullkosten-Menge: `1569.8280684762 USDT`.
- Betroffener Erlös: `1383.876662295203014 EUR`.
- Bekannte Pionex-Deposits bis `2022-01-19T12:56:19+00:00`: `1445.38419 USDT`.
- Bewertung: Die betroffenen Zeilen sind FIFO-Tail-Splits. Es fehlen keine einzelnen Sale-Events, sondern USDT-Lots vor den Pionex/Binance-Verwendungen.
- Der harte Belegblocker bleibt das Pionex-Start-/Botkapital bzw. eine Primärhistorie vor dem ersten Januar-2022-Bruch. Ohne Beleg keine steuerwirksame Zuflussfiktion setzen.

| Line | Zeit | Menge | Erlös EUR | Source Event |
|---:|---|---:|---:|---|
| 412 | `2022-01-05T15:36:46+00:00` | 75.10462220620000000000 | 66.3526805805115140000000000 | `fe030531d67b4c88a2f56f81b84f438ee42b49096cc8b6a115b98e888071c449` |
| 442 | `2022-01-19T12:45:42+00:00` | 168.76468350000000000000 | 148.7576302710750000000000000 | `a20292c0e922503226ea223723d3863a9325cd51f5cf1bd53734dd0f387b2513` |
| 514 | `2022-01-19T12:56:19+00:00` | 1325.95876277000000000000 | 1168.766351443616500000000000 | `b5422e7c322b53d701869335a500c9b7e48334f50b6e8410978e247e608e0399` |

## JUP 2024

- Aktuelle Nullkosten-Menge: `0 JUP`.
- Betroffener Erlös: `0 EUR`.
- Status nach Override: `resolved_current_state`.
- Bewertung: Die frueher offenen JUP-Nullkosten-Zeilen sind im aktuellen Steuerlauf verschwunden.
- Der Fix war ein enger Ausschluss des DCA/Program-Funding-Transfers `5344f1f97c15fec9aff2fb8c2590bed1fb0b4bda8fef6bfce2371121085f74db`; spaetere DCA-Swaps bleiben steuerwirksam.
- Die Solana-RPC-Zeitlinie zeigt einen massiven negativen JUP-Lauf ab dem DCA/Program-Transfer am `2024-08-29`.
- Erster negativer Solana-RPC-JUP-Lauf: `2024-08-29T11:23:43+00:00` nach `token_transfer` `out` `4632.733027` JUP, Running `-2511.978233`.
- Fachlich war das kein Preisproblem, sondern ein Klassifikations-/Bestandsproblem: DCA-/Program-Transfers duerfen nicht blind wie normale steuerpflichtige Verkaeufe behandelt werden, wenn sie nur Token in ein Programm verschieben und spaeter DCA-Swaps separat sichtbar werden.

| Line | Zeit | Menge | Erlös EUR | Source Event |
|---:|---|---:|---:|---|

## JUP Solana-RPC-Timeline Aug-Nov 2024

| Zeit | Typ | Seite | Menge | Delta | Running | TX |
|---|---|---|---:|---:|---:|---|
| `2024-08-04T06:06:54+00:00` | `swap_in_aggregated` | `in` | 900.000000 | 900 | 900 | `3YZ3XD4Sejz4EQTpE9Pc5emD1okgZhV2naVjUAAhfoBXqHFUY9Bfpeb9AFvYUNnMeM2hdnjsneECM1NFSdZbxxzc` |
| `2024-08-04T06:07:50+00:00` | `swap_in_aggregated` | `in` | 1326.010000 | 1326.01 | 2226.01 | `iX8fdkTW4gGsktX7Jd5CsQ4uePgjK94B4fq2RqidKcgDmSVdLu4wvTfzDHpUwcboQPWsrZQUYNJtNceXrVc6CWy` |
| `2024-08-23T20:13:31+00:00` | `swap_out_aggregated` | `out` | 750.000000 | -750 | 1476.01 | `5g3EfxaSJqT6BDhYeUsu9CMWHkFNojFCNNBSwXYBMxEDWtG7TcKZCpSrQRzaPEqmFnAijLaXZgEQS2d9oy5gWHFV` |
| `2024-08-24T10:27:31+00:00` | `swap_out_aggregated` | `out` | 185.000000 | -185 | 1291.01 | `iJqr9pZLv1uAfP9U15LMwkvVC4cbAvMktUPbsV9prBmtH9uT35GQKmdNC3WJcJxvTr1fzJYHgqBMHXDT13yhxUp` |
| `2024-08-28T08:28:10+00:00` | `swap_in_aggregated` | `in` | 829.744794 | 829.744794 | 2120.754794 | `3YZnL6HqS9tBM481J5nqt89xKdEGRrKAwhASYcJedqt1wHEZtMcHymGLZJp2giyVXJC6p3KEx1wAaSHgd4TkRpTL` |
| `2024-08-29T11:23:43+00:00` | `token_transfer` | `out` | 4632.733027 | -4632.733027 | -2511.978233 | `2vFy89bkfixVG1uMX1xXeyXXGfwLsJDn4AGKZY3UczDJADMd6dj6GWgX3jKoWrJWQxP9st8Nqo1sDuCwxc7sHQUH` |
| `2024-08-29T11:25:59+00:00` | `token_transfer` | `in` | 1853.093212 | 1853.093212 | -658.885021 | `5Am8K42uLTqji9t9UFeVnRscyqTt46zKrxdAvLoagzRkHngq3aQxsvwrCENCRvZaQ4MznzZvRH6cvyCjzm1hCQPV` |
| `2024-09-09T21:06:32+00:00` | `token_transfer` | `out` | 181.526895 | -181.526895 | -840.411916 | `3oQf7M6kNpnc6528JRt18KN3Ti47K8SXEQBBguxX1GvyBzdBrESbQLig7CVt1XYFoN8zSQ4yEMY2XRPCCgZ24zZ1` |
| `2024-09-14T04:54:38+00:00` | `token_transfer` | `out` | 525.214429 | -525.214429 | -1365.626345 | `3E36HNHFEVL9wmFcb3SJppHdxooPkaWTK4woQvN4WDtQdhkSQ5FZAi6ng12vTLoBL7roTfHfWwesJvCkCb5nr2kf` |
| `2024-09-20T09:02:40+00:00` | `token_transfer` | `out` | 1030.760188 | -1030.760188 | -2396.386533 | `4ktBTn2eLEFzkZSey4q4A5EERJE3KrZwYDWycz78142B6q9dSWFDWS3sw8vKrmDJMxGA6Wo1cor8DAMtp9ekHuSz` |
| `2024-09-26T17:44:27+00:00` | `token_transfer` | `out` | 500.000000 | -500 | -2896.386533 | `qM2ezJBGTaCkvzNyNtLqjW6ZZLVNsQP15ottTDv1WkvJF2AJvFQWEkSdQWi3RSx9X82GmVRSeDTx96KG7nrU3ZJ` |
| `2024-10-07T17:53:59+00:00` | `swap_out_aggregated` | `out` | 251.751173 | -251.751173 | -3148.137706 | `1eVJ41tebhpCXtMd65swYzk1H8mficGutPMcVxkGUriUeTdg6pmEkReftvqnuwjcYDmTBtvgK3566RqUEoKbuyT` |
| `2024-10-23T13:02:49+00:00` | `token_transfer` | `out` | 900.000000 | -900 | -4048.137706 | `PPsdXcECydsAH9AopWvz741cpvWnmeoWm8hZTePwZjH9sYEyaxCQTcahaJxnaGN2rTFez5VGKYDLy6rvk4r6M6Q` |
| `2024-11-09T12:24:16+00:00` | `swap_out_aggregated` | `out` | 575.436548 | -575.436548 | -4623.574254 | `4tV4aKtPK5SZWZyJxTfhmzwKhTVsa685PyyHW9LBR5BUsXKPRVzybqtQSwuFpwmSVZsrYCJT6fRiN42HefFbT9qX` |
| `2024-11-17T05:25:59+00:00` | `swap_out_aggregated` | `out` | 256.191875 | -256.191875 | -4879.766129 | `rQ4BM4GVNFkaY4DWCwVRL6AECDi86kG71XNGRpJWe8CTaYnXh11sGjvGT4EtQyfjoD6EdXSuqE7YBF6KWUs78uM` |
| `2024-11-17T09:11:50+00:00` | `swap_in_aggregated` | `in` | 55.78179 | 55.78179 | -4823.984339 | `3gSdRJiFcupJwPTJnNoQB88nxHErimLxpvA1aiKhSovd8jC4NsmxiyUrt6YP5hKxzbeWbUSWMMxH5FUZdL5Z6efj` |
| `2024-11-18T04:52:51+00:00` | `swap_in_aggregated` | `in` | 2311.92000 | 2311.92 | -2512.064339 | `3kcS9q81Fho5tSrYC1PpSnmWNX3JcUFSBazwDUxk4HroWwWiynCreqouqkjp9waJiQoXLR72QjxdpkoxFNUPAyB3` |
| `2024-11-18T04:54:41+00:00` | `swap_in_aggregated` | `in` | 1287.036271 | 1287.036271 | -1225.028068 | `2AY4kewUPMxPkYg9hYArNU1nZDMiyPJzHCTHqZ6bTSVoWWZPBvYHo8enwuEbfoRM9ZYmFXpp74BVEMgmq26y1pj5` |
| `2024-11-19T21:14:21+00:00` | `swap_out_aggregated` | `out` | 5812.211205 | -5812.211205 | -7037.239273 | `5duFfJZsX7bxDHUZCpWAgciVAgLEQSvnFTkMWfRRYpEdxnGarvwaB4bBdZ87tkLQdPRvnJRmFgfvD69Uhfsc1aLe` |
| `2024-11-20T22:05:59+00:00` | `swap_in_aggregated` | `in` | 140.000000 | 140 | -6897.239273 | `5eWNeB87nrmA17yaUZbsHDpjpLmCBadcydgM8xYixyXnCJJf1RJ2n9cKKe4ZmjYEhDmTff2x1WukkNbjtUAfuhqf` |
| `2024-11-21T20:12:13+00:00` | `token_transfer` | `in` | 400.000000 | 400 | -6497.239273 | `3pbTvwBBiNhkX3KcRfrxpEwmyMYJASZPMQ2fT6qm1DpUWFeYgQPAFfxpwaKjz8g3GNmS8s2DcK7kJXQg1S6wB2aV` |
| `2024-11-22T15:25:20+00:00` | `swap_out_aggregated` | `out` | 646.471986 | -646.471986 | -7143.711259 | `2xTqz6wvXHYVmAG7JoeZpSypCjt9LhYh6mJgk5xcwyzoMu24XxCQaqZyCUDity9twPiX2nhS5yJqFLpH4oWPgdnn` |
| `2024-11-23T05:43:01+00:00` | `swap_in_aggregated` | `in` | 8524.295277 | 8524.295277 | 1380.584018 | `41bSt8kpXZpmj3YBwfoL4uoPZevKxCTeuVVj3Er9GkeHab8iC59aFgXE4v95oYi649sSyym7n9sDhdbDEfDEruyP` |
| `2024-11-24T11:23:20+00:00` | `swap_out_aggregated` | `out` | 8525.295277 | -8525.295277 | -7144.711259 | `2FvedBDXxtqv52wCwfAsnVwtR9cS6pV4zsEaBJy3dtxvPYBWRZChofqZ2SC8sV1YveSSmA6s2zuLnb9diMqo2Jmg` |
| `2024-11-24T20:22:36+00:00` | `swap_in_aggregated` | `in` | 1 | 1 | -7143.711259 | `2muNLLNF7cn5Ytn1Ff8x7Ank9qcz1W9z1KnS496jYUAAVt98eNxqxpQ8cuhXB8N1PQVde4ZyzqupwooVY2X9T8TS` |

## Naechste Umsetzung

1. USDT 2022: weiter als dokumentierten Review-Blocker bzw. explizite Nullbasis-Entscheidung fuehren, bis Pionex Primaerbeleg liefert.
2. HNT 2021/2022: Legacy-/Mining-/Reward-Anschaffungskette offen halten; steuerlich abgeschlossene Jahre nicht ueberfokussieren, aber Belege nicht loeschen.
3. Nach jedem weiteren Fix: Snapshot fuer lokale KI neu bauen und KI-Queue erneut auf die offenen Current-State-Issues ansetzen.

JSON: `var/current_zero_cost_root_cause_audit_2026-05-10.json`
