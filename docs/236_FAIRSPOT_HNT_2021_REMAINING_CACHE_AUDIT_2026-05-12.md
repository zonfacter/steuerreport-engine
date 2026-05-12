# Fairspot HNT 2021 Restzeilen Cache-Audit

Stand: 2026-05-12

## Ergebnis

- Der Fairspot-Cache wurde inklusive `rewards_v1`, `payment_v1`, `payment_v2` und Fees ausgewertet.
- Vor dem Binance-HNT-Verkauf am `2021-08-17` zeigt Fairspot fuer die Haupt-Wallet nur `20.0447256801337252586127 HNT` Restbestand.
- Vor dem `2021-08-20`-Abgang an die Binance-Adresse ist Fairspot-seitig genug Hauptwallet-Bestand sichtbar; ein Teil stammt aber aus Gegenwallet-Inbounds und ist nicht automatisch als bewertete Cost-Basis verwendbar.
- Es wurde kein automatischer Preis-, FX- oder Cost-Basis-Fix abgeleitet.

## Verbleibende 2021-HNT-Zero-Cost-Zeilen

| Line | HNT | Sale-Zeit | Erloes EUR | Source | Lot-Source |
| --- | --- | --- | --- | --- | --- |
| 1285 | 22.7759533567933520993873 | 2021-08-17T16:10:05+00:00 | 445.1808341476849715363131107 | ff96dbcac85f... |  |
| 1347 | 14.651308409999999970498 | 2021-08-20T08:05:15+00:00 | 290.1121724005967814158276469 | 6bc38135bade... | dd5353eedbee... |
| 1517 | 3.536102305597830579502 | 2021-08-31T21:11:14+00:00 | 69.92100578446492383320425294 | 4ef5e7042eba... | dd5353eedbee... |

## Fairspot-Bestandsschnitte

| Kontext | Wallet | Zeilen | Rewards HNT | In HNT | Out HNT | Fees HNT | Saldo HNT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Vor Binance-HNT-Verkauf ohne Lot-Quelle | 133rkwoK... | 1471 | 555.1998127300000072746127 | 196.229374 | 731.11113564 | 0.273325409866282016 | 20.0447256801337252586127 |
| Vor Binance-HNT-Verkauf ohne Lot-Quelle | 14eKedP4... | 7 | 0 | 356.48613564 | 356.36682102 | 0.115063288757136273 | 0.004251331242863727 |
| Nach Legacy-Outflow zum Binance-Deposit dd5353... | 133rkwoK... | 1528 | 558.8505043200000073041147 | 196.229374 | 749.4136961 | 0.289218030241529484 | 5.3769641897584778201147 |
| Nach Legacy-Outflow zum Binance-Deposit dd5353... | 14eKedP4... | 7 | 0 | 356.48613564 | 356.36682102 | 0.115063288757136273 | 0.004251331242863727 |

## Direkte Binance-Abgaenge vor 2021-08-17

| Zeit | Tx | HNT | Fee HNT |
| --- | --- | --- | --- |
| 2021-07-27 18:00:29 | 9WOmGxUyi6-196unX23DLEbVQJEtLEN9VQFfvGd5go8 | 124.539 | 0.02991452991452991 |
| 2021-08-06 19:00:43 | oecGPObDyTaubitJ-gjGhbpULDpsuuNgr-deaCwYxPc | 34.124 | 0.025234318673395813 |
| 2021-08-10 16:52:42 | uJKF_6MQ9S_zhZRkeVQCl0ZQm5A4zG05AC1QSwbdJsI | 28.261 | 0.02454501432902872 |
| 2021-08-10 17:30:08 | IgwVzm8XJH3cLXe43jj6PbC5zb7RRdZhVxtUmTMXCkQ | 79 | 0.02454501432902872 |

## Hauptwallet-Zahlungen 2021-08-01 bis 2021-08-20

| Zeit | Tx | HNT | Fee HNT | Von | An |
| --- | --- | --- | --- | --- | --- |
| 2021-08-06 19:00:43 | oecGPObDyTaubitJ-gjGhbpULDpsuuNgr-deaCwYxPc | 34.124 | 0.025234318673395813 | 133rkwoK... | 138bCXPV... |
| 2021-08-10 16:52:42 | uJKF_6MQ9S_zhZRkeVQCl0ZQm5A4zG05AC1QSwbdJsI | 28.261 | 0.02454501432902872 | 133rkwoK... | 138bCXPV... |
| 2021-08-10 17:30:08 | IgwVzm8XJH3cLXe43jj6PbC5zb7RRdZhVxtUmTMXCkQ | 79 | 0.02454501432902872 | 133rkwoK... | 138bCXPV... |
| 2021-08-14 17:15:46 | n7pUrLCjNgmbd95CzofzUJAzMz6zlAZJqRmzYk_um7M | 100 | 0.021256586125461836 | 133rkwoK... | 14eKedP4... |
| 2021-08-20 08:01:13 | s5UTv0W7IKEjmQllRvKtELqfAnVuBFoDmSBHyyQf0R4 | 18.30256046 | 0.015892620375247468 | 133rkwoK... | 138bCXPV... |

## Gegenwallet-Kontext

| Wallet-Kontext | Zahlungen | Inbound | Outbound | Unique In | Unique Out | In HNT | Out HNT | Saldo HNT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14o7... Roundtrip | 2 | 1 | 1 | 1 | 1 | 100 | 99.75 | 0.221826450937776705 |
| 14Ye... Service-/Pool-Indiz | 33646 | 28186 | 5460 | 5191 | 3044 | 23640123.13535006 | 8123862.87058677 | 15515900.516434960203816295 |

## Einordnung

- Line `1285` bleibt offen: Fairspot belegt keinen zusaetzlichen Binance-HNT-Zufluss zwischen den bekannten Deposits am `2021-08-10` und dem Verkauf am `2021-08-17`.
- Lines `1347` und `1517` bleiben fachlich eingegrenzt: der `dd5353...`-Deposit ist als Legacy-Abgang belegt, aber die vorgelagerte Bewertbarkeit haengt an der korrekten Behandlung der Gegenwallet-Inbounds.
- `14o7...` ist ein belegnaher Roundtrip: `100 HNT` gingen von der Hauptwallet dorthin, `99.75 HNT` kamen zurueck.
- `14Ye...` ist kein sauberer Eigenwallet-Nachweis: vor dem Transfer an die Hauptwallet hat diese Wallet tausende Zahlungsgegenparteien.
- Naechster sicherer Schritt ist daher kein Auto-Fix, sondern ein separater Review-/Importpfad nur fuer belegbare eigene Roundtrips oder nachgelieferte Primaerbelege.
