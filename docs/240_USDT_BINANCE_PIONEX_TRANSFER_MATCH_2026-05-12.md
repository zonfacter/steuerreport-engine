# USDT Binance -> Pionex Transfer-Match

Stand: 2026-05-12

## Ergebnis

- Applied: `True`
- Methode: `txid_verified_binance_pionex_usdt_trc20`
- Kandidaten: `2`
- Erstellt: `2`

## Bewertung

- Die TX-ID beweist nur den Binance->Pionex-Transfer, nicht die urspruengliche Anschaffung der USDT.
- Der Match erzeugt keine neuen Anschaffungskosten und keinen neuen Preisanker.
- Der 2022-01-19-Transfer kommt nach dem Pionex-MXC-BUY um 12:45:42 UTC; dafuer bleibt vorheriger Pionex-Bestand oder ein fehlender Beleg erforderlich.

## Matches

| Label | TXID | Menge USDT | Out UTC | In UTC | Delta Sekunden | Aktion | Match |
| --- | --- | ---: | --- | --- | ---: | --- | --- |
| 2021-12-25 Binance -> Pionex 200 USDT | `b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182` | 200 | `2021-12-25T16:19:40+00:00` | `2021-12-25T16:23:04+00:00` | 204 | `created` | `ec1bca59-973d-46a3-9b1a-01fa78311712` |
| 2022-01-19 Binance -> Pionex 1245.38419 USDT | `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa` | 1245.38419 | `2022-01-19T12:50:48+00:00` | `2022-01-19T12:54:09+00:00` | 201 | `created` | `954e170d-a35d-4e60-afba-f637f0f0007a` |

## Onchain-Beleg

### 2021-12-25 Binance -> Pionex 200 USDT

- Tronscan: https://tronscan.org/#/transaction/b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182
- TXID: `b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182`
- Betrag: `200 USDT`
- Binance Out: `2021-12-25T16:19:40+00:00`
- Pionex In: `2021-12-25T16:23:04+00:00`
- Binance Raw `completeTime`: `2021-12-25 16:22:42`
- Pionex Raw `date(UTC+0)`: `2021-12-25 16:23:04`
- Binance Zieladresse / Pionex Deposit-Adresse: `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ`
- Binance Hot-Wallet laut Binance-Rohfeld `info`: `TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr`

### 2022-01-19 Binance -> Pionex 1245.38419 USDT

- Tronscan: https://tronscan.org/#/transaction/b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa
- TXID: `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa`
- Betrag: `1245.38419 USDT`
- Binance Out: `2022-01-19T12:50:48+00:00`
- Pionex In: `2022-01-19T12:54:09+00:00`
- Binance Raw `completeTime`: `2022-01-19 12:52:45`
- Pionex Raw `date(UTC+0)`: `2022-01-19 12:54:09`
- Binance Zieladresse / Pionex Deposit-Adresse: `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ`
- Binance Hot-Wallet laut Binance-Rohfeld `info`: `TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr`

## Wichtig

Diese Transfer-Matches koennen die belegte Lot-Kontinuitaet zwischen Binance und Pionex verbessern. Sie loesen aber nicht automatisch die offene Anschaffungskette, wenn die verbrauchten USDT schon vor dem Transfer auf Pionex vorhanden gewesen sein muessen oder wenn auf Binance fuer den Abgang selbst noch Anschaffungskosten fehlen.

JSON: `var/usdt_binance_pionex_transfer_match_2026-05-12.json`
