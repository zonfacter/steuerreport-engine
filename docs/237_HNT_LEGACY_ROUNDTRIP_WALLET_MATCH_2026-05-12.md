# HNT Legacy Roundtrip Wallet Match

Stand: 2026-05-12

## Ergebnis

- Applied: `True`
- Aktion: `created`
- Methode: `fairspot_roundtrip_14o7_self_custody`
- Persistierter Match: `bee0a64c-e73c-4084-9cd7-8fd48e46e8f2`

## Menge

- Fairspot-Abgang an `14o7...`: `100 HNT`
- Rueckfluss von `14o7...`: `99.75 HNT`
- Nicht zurueckgekehrte Transferdifferenz: `0.25 HNT`
- Netzwerkfee im Projekt-Out-Event: `0.03130590339893 HNT`
- Out-Event minus Rueckfluss: `0.28130590339893 HNT`

## Events

| Richtung | Zeit | Event | Tx | Menge HNT | Fee HNT | Von | An |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| Out | `2021-06-23T20:26:18+00:00` | `7946d3580ddf0a4d5c27af9a4a961cc2361d09e52fd5814d02c23c5ac77acdb5` | `Kk7ZTefj1fQOZ-1rPwt4aIOXpTmckgt8JA28IJ6XF_8+133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j` | 100.03130590339893 | 0.03130590339892665 | `133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j` | `14o7quYAMQZFE8UCNPN89yK9fwtxMW8wvht8MQZkSiSgizeqSme` |
| In | `2021-07-08T18:30:29+00:00` | `67cbdab2e2f2a75cdb15d83eefc5f01baec731e2ddc47a670e79fd654773d06b` | `tLOGE2C0v-CGYSJfvKU6KvI7oQq4OALrz3rh6SbC8Qs+133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j` | 99.75 |  | `14o7quYAMQZFE8UCNPN89yK9fwtxMW8wvht8MQZkSiSgizeqSme` | `133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j` |

## Zero-Cost HNT vor Apply

- 2021 HNT-Zeilen >= 50 EUR: `3`
- Menge: `40.9633640723911826493873 HNT`
- Erloes: `805.2140123327466767853450105 EUR`

## Ergebnis nach 2021-Neulauf

- Neuer 2021-Job: `e26811e1-becc-477f-a83c-fdf60cea327b`
- Tax Lines: `5454`
- Derivative Lines: `43`
- 2021 HNT-Zero-Cost-Zeilen >= 50 EUR: `0`
- Menge: `0 HNT`
- Erloes: `0 EUR`

## Einordnung

- Der Match erzeugt keine neuen Anschaffungskosten und verwendet keine Fairspot-USD-Werte als Preisanker.
- Er markiert nur den belegten Rueckfluss von 99.75 HNT als Lot-Continuity aus dem vorherigen 100-HNT-Abgang.
- Die nicht zurueckgekehrten 0.25 HNT und die Netzwerkfee werden nicht als Rueckfluss behandelt.

JSON: `var/hnt_legacy_roundtrip_wallet_match_2026-05-12.json`
