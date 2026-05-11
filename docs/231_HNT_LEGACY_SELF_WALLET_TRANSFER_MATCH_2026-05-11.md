# HNT Legacy Self-Wallet Transfer Match

Stand: 2026-05-11

## Ergebnis

- Applied: `True`
- Kandidaten: `9`
- Neu zu erstellen: `9`
- Bereits vorhanden: `0`
- Konflikte: `0`
- Erstellt: `9`

## Scope

- Haupt-Wallet: `133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j`
- Staking-Wallet: `14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA`
- Gematcht werden nur HNT-Legacy-Transfers mit gleicher Helium-Transaktions-ID zwischen diesen bekannten eigenen Wallets.
- Die Fairspot-Counterparty `14aDLshY...` wird hier bewusst nicht gematcht, weil die Rueckgabe mehrteilig ist und steuerlich/fachlich separat entschieden werden muss.

## Kandidaten

| Zeitpunkt | Tx | Out HNT | In HNT | Delta | Aktion | Match |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `2021-06-24T04:41:04+00:00` | `QGHeiessdO0yjf2y7Xi7aWQ1gilyQg-tyzhlzHmc08s` | 100.02936241610739 | 100 | 0.02936241610739 | `create` | `9d00fab1-3d85-4cce-bf31-0531d68d6b96` |
| `2021-06-24T07:22:47+00:00` | `6oJUNJ_UiWqvJiqV5vDy8-rRRr4mM4FJxDe-dim4bew` | 156.51597256839904 | 156.48613564 | 0.02983692839904 | `create` | `ef71dd57-2ac2-43c1-ba4d-7334f363a8e8` |
| `2021-08-14T17:15:46+00:00` | `n7pUrLCjNgmbd95CzofzUJAzMz6zlAZJqRmzYk_um7M` | 100.02125658612546 | 100 | 0.02125658612546 | `create` | `bd71e298-af5e-4609-8908-3d452079efb8` |
| `2022-01-27T19:08:34+00:00` | `MTqvysNj4rcU7bOkTeNtVid-UcLRcNpwGu0zJhhGjCM` | 40.012350797949765 | 40 | 0.012350797949765 | `create` | `1f92bf3c-bdb6-40ac-a574-ef6cd2c85718` |
| `2022-02-02T19:01:33+00:00` | `cJBWTw4aQnNFkTDE3_87OnicnHltGSxIJe0hZ2ZV3DA` | 11.013539651837524 | 11 | 0.013539651837524 | `create` | `5ba13992-e902-407f-8ef5-195882f0388a` |
| `2022-03-04T06:24:58+00:00` | `03JT94YIqOh21iuHb-G6h8dVQDj5Zuk3k8RjBPPpMg8` | 15.11565995525727 | 15.1 | 0.01565995525727 | `create` | `f22455f3-7134-4322-86cd-b9b30d7678ac` |
| `2022-05-02T05:12:04+00:00` | `CL2HLh25_Na8bLu4rMwWcaeRMoovc7wljggzUZf6Sp0` | 55.02566584535961 | 55 | 0.02566584535961 | `create` | `28dc75b3-d20a-4eab-b3db-6bce2cd6951d` |
| `2022-07-12T04:07:22+00:00` | `8FHBnG2SF9IoQ3J_d5c9KuAkFVs-_mwERFe_Ix4eJbA` | 421.30245111 | 421.30245111 | 0 | `create` | `05ecb7cf-4c04-4d7c-94bd-124e6afc9e5a` |
| `2022-12-31T21:57:55+00:00` | `qnXqbdFwzq8h-0TLTcp5HjoeP0Dx3ipTD2p23vOdkGQ` | 73.9345895 | 73.9345895 | 0 | `create` | `2a0cde60-d491-4219-aa3b-fc7d8370a37b` |

## Zero-Cost HNT vor Apply

- 2021: `8` HNT-Zeilen, `91.349156385597830478 HNT`, Erloes `1790.05924360799200384171342 EUR`.
- 2022: `5` HNT-Zeilen, `439.688010219657251202 HNT`, Erloes `2300.134050729099355136509666 EUR`.

## Zero-Cost HNT nach Neuberechnung

- 2021: `3` HNT-Zeilen, `40.9633640723911826493873 HNT`, Erloes `805.2140123327466767853450105 EUR`.
- 2022: `5` HNT-Zeilen, `17.46753047183752349899927 HNT`, Erloes `351.9188545425587338155117614 EUR`.
- Der groesste Effekt betrifft die frueheren 2022-Pionex-Verkaeufe aus dem am `2022-07-12` zurueckgefuehrten Staking-Wallet-Bestand.

## Bewertung

- Diese Matches sind technische Continuity-Belege fuer eigene Wallets und erzeugen selbst keine neuen Anschaffungskosten.
- Erwarteter Effekt: spaetere Inbound-Events der Staking-Wallet koennen die vorherigen FIFO-Lots aus der Haupt-Wallet weitertragen.
- Nicht abgedeckt: `14e...` <-> `14a...` als Staking-/Custody-/Pool-Rueckgabe.

JSON: `var/hnt_legacy_self_wallet_transfer_match_2026-05-11.json`
