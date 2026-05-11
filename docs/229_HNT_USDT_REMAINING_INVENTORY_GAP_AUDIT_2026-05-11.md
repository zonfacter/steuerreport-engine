# HNT-/USDT-Restbestandsluecken-Audit

Stand: 2026-05-11

## Ergebnis

- Aktuelle Restzeilen: `14`
- Erloes dieser Restzeilen: `5442.131645572294372978223086 EUR`
- Keine Restzeile ist ein belegbarer Preisanker- oder FX-Backfill.
- HNT-Transfer-Matches fuer die Binance-Deposits existieren bereits; die Luecke liegt vor dem Legacy-Outflow.
- USDT-Reste bleiben Pionex-/Binance-Opening- bzw. Bot-Historie ohne Primaerbeleg.

## Aktuelle Jobs

| Jahr | Job | Tax-Lines | Derivate-Lines | Aktualisiert |
| ---: | --- | ---: | ---: | --- |
| 2020 | `0b3a4d22-6574-4e54-8685-92d40dbaf100` | 0 | 0 | 2026-05-11T20:33:22.138080+00:00 |
| 2021 | `01504a89-9b31-4e87-97f4-953f70164a9f` | 5494 | 43 | 2026-05-11T20:33:30.805075+00:00 |
| 2022 | `a2523d34-68b5-4983-b08f-c44dbf7816a8` | 6896 | 630 | 2026-05-11T20:33:39.930444+00:00 |
| 2023 | `210d8066-3bb0-4947-b45b-ceb2962e15d6` | 9099 | 0 | 2026-05-11T20:33:49.504534+00:00 |
| 2024 | `aeb1b44b-8b45-4dcb-8479-12c5b470c379` | 1680 | 36 | 2026-05-11T20:33:58.836379+00:00 |
| 2025 | `cc781fa5-1987-411a-ba69-e2653129cf88` | 465 | 957 | 2026-05-11T20:34:07.563410+00:00 |
| 2026 | `b59704da-a6b6-442d-b64d-b8024a74bab5` | 1 | 0 | 2026-05-11T20:34:16.355680+00:00 |

## Gruppierung

| Jahr | Asset | Klasse | Zeilen | Menge | Erloes EUR | Plattformen |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 2021 | `HNT` | `matched_transfer_source_cost_basis_gap` | 2 | 18.18741071559783055 | 360.0331781850617052490318998 | binance |
| 2021 | `HNT` | `missing_lot_source_inventory_gap` | 4 | 71.527745669999999928 | 1398.08775436293029859268152 | binance |
| 2022 | `HNT` | `matched_transfer_source_cost_basis_gap` | 5 | 439.688010219657251202 | 2300.134050729099355136509666 | pionex |
| 2022 | `USDT` | `missing_lot_source_inventory_gap` | 3 | 1569.8280684762 | 1383.876662295203014 | binance, pionex |

## Betroffene Zeilen

| Jahr | Line | Asset | Menge | Erloes EUR | Quelle | Lot-Quelle | Klasse |
| ---: | ---: | --- | ---: | ---: | --- | --- | --- |
| 2021 | 1340 | `HNT` | 16.233745669999999928 | 317.30625390293029859268152 | `binance/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2021 | 1341 | `HNT` | 14.142 | 276.42080478 | `binance/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2021 | 1344 | `HNT` | 17.406 | 340.21924254 | `binance/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2021 | 1345 | `HNT` | 23.746 | 464.14145314 | `binance/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2021 | 1407 | `HNT` | 14.651308409999999970498 | 290.1121724005967814158276469 | `binance/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2021 | 1577 | `HNT` | 3.536102305597830579502 | 69.92100578446492383320425294 | `binance/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 3439 | `HNT` | 74.356 | 355.6905058882184352 | `pionex/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 3456 | `HNT` | 84.528 | 414.0965341866616704 | `pionex/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 3572 | `HNT` | 208.192 | 1146.1874646034960896 | `pionex/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 3576 | `HNT` | 58.7 | 311.59419948832 | `pionex/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 3579 | `HNT` | 13.912010219657251202 | 72.56534656240315993650966628 | `pionex/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 412 | `USDT` | 75.1046222062 | 66.352680580511514 | `binance/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2022 | 442 | `USDT` | 168.7646835 | 148.757630271075 | `pionex/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2022 | 514 | `USDT` | 1325.95876277 | 1168.7663514436165 | `pionex/trade/out` | `leer` | `missing_lot_source_inventory_gap` |

## HNT-Transfer-Belege

- Match `ddec12db-878f-4285-b40a-16df945a301a` fuer Inbound `dd5353eedbee68d33a5c687e013b67f468dac6a769af6b56b60dfd7c1e40fa2f`:
  - Outbound `helium_legacy_cointracking` `legacy_transfer` 18.318453080375246 `HNT` am `2021-08-20T08:01:13+00:00`.
  - Binance-Inbound 18.30256046 `HNT` am `2021-08-20T08:04:08+00:00`.
  - Delta `0.015892620375246`, Zeitdifferenz `175` Sekunden.
  - Legacy-Transfer-Wert `value_usd=403.42` ist ein Transferwert, keine belegte Anschaffungskostenbasis.
- Match `728264aa-94fe-43ec-a49f-ed9a3a5af447` fuer Inbound `9dd85d203cebbe23d40ff09ddd91b30758c3d255c6f80dadbb27581ab152bcba`:
  - Outbound `helium_legacy_cointracking` `legacy_transfer` 450.0398803021218 `HNT` am `2022-07-12T06:59:57+00:00`.
  - Binance-Inbound 450 `HNT` am `2022-07-12T07:08:01+00:00`.
  - Delta `0.0398803021218`, Zeitdifferenz `484` Sekunden.
  - Legacy-Transfer-Wert `value_usd=3949.67` ist ein Transferwert, keine belegte Anschaffungskostenbasis.

## Mining-Reward-Kontext

- BMF 2025, Randnummern 7 bis 11, beschreibt Block-Rewards/Mining als Erwerb von Kryptowerten im Rahmen der Blockerstellung.
- BMF 2025, Randnummern 38 bis 44, ordnet Blockerstellung nicht als private Vermoegensverwaltung ein und behandelt den Zugang im Betriebsvermoegen mit Marktkurs/Anschaffungskostenlogik.
- BMF 2025, Randnummern 43, 51 und 91, stuetzen Marktkurs/Tageskurs und Abzug individueller bzw. fortgefuehrter Anschaffungskosten bei Betriebsvermoegen.
- Projektlogik: `mining_reward` wird als Reward/Business-Lot verarbeitet. Der Restbefund ist deshalb keine falsche Mining-Klassifikation, sondern fehlender belegter Vorbestand vor den konkreten Outflows.

## Lokale HeliumTracker-Quellenabdeckung

| Datei | CSV-Zeilen | CSV-HNT | Importiert | Store-Zeilen | Reward-Events | Store-HNT |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `heliumtracker-report-advanced-2021-12.csv` | 465 | 29.72700061 | ja | 198 | 168 | 29.72700061 |
| `heliumtracker-report-advanced-2022-10.csv` | 465 | 43.79330734 | ja | 326 | 295 | 43.79330734 |
| `heliumtracker-report-advanced-2022-11.csv` | 450 | 46.88791189 | ja | 317 | 287 | 46.88791189 |
| `heliumtracker-report-advanced-2022-12.csv` | 465 | 51.51530276 | ja | 328 | 297 | 51.51530276 |
| `heliumtracker-report-advanced-2022-2.csv` | 420 | 56.68281011 | ja | 460 | 405 | 56.68281011 |
| `heliumtracker-report-advanced-2022-3.csv` | 465 | 47.74723842 | ja | 493 | 433 | 47.74723842 |
| `heliumtracker-report-advanced-2022-4.csv` | 450 | 27.56826777 | ja | 414 | 359 | 27.56826777 |
| `heliumtracker-report-advanced-2022-5.csv` | 465 | 27.92735477 | ja | 268 | 239 | 27.92735477 |
| `heliumtracker-report-advanced-2022-6.csv` | 450 | 34.4279603 | ja | 278 | 253 | 34.4279603 |
| `heliumtracker-report-advanced-2022-7.csv` | 465 | 32.3470546 | ja | 292 | 265 | 32.3470546 |
| `heliumtracker-report-advanced-2022-8.csv` | 465 | 44.79597753 | ja | 333 | 302 | 44.79597753 |
| `heliumtracker-report-advanced-2022-9.csv` | 450 | 41.12615909 | ja | 326 | 298 | 41.12615909 |
| `heliumtracker-report-advanced-2023-1.csv` | 465 | 46.70469617 | ja | 308 | 277 | 46.70469617 |
| `heliumtracker-report-advanced-2023-10.csv` | 465 | 0 | ja | 247 | 0 | 0 |
| `heliumtracker-report-advanced-2023-11.csv` | 450 | 0 | ja | 271 | 0 | 0 |
| `heliumtracker-report-advanced-2023-12.csv` | 465 | 0 | ja | 121 | 0 | 0 |
| `heliumtracker-report-advanced-2023-2.csv` | 420 | 39.81611834 | ja | 271 | 244 | 39.81611834 |
| `heliumtracker-report-advanced-2023-3.csv` | 465 | 42.69473516 | ja | 270 | 259 | 42.69473516 |
| `heliumtracker-report-advanced-2023-5.csv` | 465 | 0 | ja | 303 | 0 | 0 |
| `heliumtracker-report-advanced-2023-6.csv` | 450 | 0 | ja | 299 | 0 | 0 |
| `heliumtracker-report-advanced-2023-7.csv` | 465 | 0 | ja | 310 | 0 | 0 |
| `heliumtracker-report-advanced-2023-8.csv` | 465 | 0 | ja | 310 | 0 | 0 |
| `heliumtracker-report-advanced-2023-9.csv` | 450 | 0 | ja | 294 | 0 | 0 |

## Lokale Excel-Pruefung Staking-Wallet

Die vom Nutzer vermutete Staking-Wallet-Spur ist lokal vorhanden. Rohdaten bleiben lokal; diese Sektion dokumentiert nur abgeleitete Pruefergebnisse.

### Binance-HNT-Deposit-Excel

| Datei | Lokale Kopien | Zeilen | HNT-Zeilen | HNT-Menge | Importiert |
| --- | ---: | ---: | ---: | ---: | --- |
| `BINANCE - HNT Transfer Staking Wallet - Deposit_History 07 bis 09-2021.xlsx` | 3 | 9 | 9 | 366.22656046 | ja |
| `BINANCE - HNT Transfer Staking Wallet - deposit_history 11-2021.xlsx` | 3 | 0 | 0 | 0 | ja |

### Heliumtracker-Transferliste 2021

- Datei: `usertransfer/legacy_daten/Heliumtracker/advance/Heliumtracker 2021.xlsx`
- Zeilen: `46`
- Abgaenge aus der Haupt-Wallet `133rkwoK...`: `30` mit `1204.55 HNT`.
- Davon zu Binance: `950.62 HNT`.
- Davon zur Staking-Wallet `14eKedP4...`: `221.1 HNT`.

Kritische Zeilen aus der Excel-Transferliste:

| Zeit | Ziel | Menge HNT | Empfaenger |
| --- | --- | ---: | --- |
| `2022-07-12 at 08:59AM` | `binance` | 450 | `138bCXPVf...mF7rjA8y` |
| `2021-08-20 at 10:01AM` | `binance` | 18.3 | `Binance` |
| `2021-08-14 at 07:15PM` | `staking_wallet_14e` | 100 | `14eKedP4g...puq2kYNA` |
| `2021-08-10 at 07:30PM` | `binance` | 79 | `Binance` |
| `2021-08-10 at 06:52PM` | `binance` | 28.26 | `Binance` |

### Daily-Hotspot-Rewards-Excel

- Datei: `usertransfer/legacy_daten/Heliumtracker/advance/daily_hotspot_rewards_2022-03-21T17_52_18.702901-04_00.xlsx`
- Zeilen: `941`
- HNT bis `2021-08-17`: `556.05098609`
- HNT bis `2021-08-20`: `559.34721516`
- HNT bis `2022-07-12`: `778.10454489`

Monatssummen 2021 aus der Excel-Datei:

| Monat | HNT |
| --- | ---: |
| `2021-05` | 95.96404917 |
| `2021-06` | 214.65062244 |
| `2021-07` | 206.1633087 |
| `2021-08` | 55.36233478 |
| `2021-09` | 73.81884348 |
| `2021-10` | 64.13861957 |
| `2021-11` | 37.92477809 |
| `2021-12` | 30.08198866 |

### Staking-Wallet in der Datenbank

- Importierte Quelle: `manual_legacy_import:helium_legacy_raw:helium-Staking Wallet 14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA-all-raw.csv`
- Events: `27`
- Inbound: `973.08856161 HNT`
- Outbound: `972.63568422 HNT`
- Saldo: `0.45287739 HNT`
- Nicht gematchte Self-Transfer-Kandidaten mit gleicher Helium-Transaktion: `9`

| Zeit | Out-Quelle | In-Quelle | Delta HNT | Match vorhanden |
| --- | --- | --- | ---: | --- |
| `2021-06-24T04:41:04+00:00` | `helium_legacy_cointracking` | `helium_legacy_raw` | 0.02936241610739 | nein |
| `2021-06-24T07:22:47+00:00` | `helium_legacy_cointracking` | `helium_legacy_raw` | 0.02983692839904 | nein |
| `2021-08-14T17:15:46+00:00` | `helium_legacy_cointracking` | `helium_legacy_raw` | 0.02125658612546 | nein |
| `2022-01-27T19:08:34+00:00` | `helium_legacy_cointracking` | `helium_legacy_raw` | 0.012350797949765 | nein |
| `2022-02-02T19:01:33+00:00` | `helium_legacy_cointracking` | `helium_legacy_raw` | 0.013539651837524 | nein |
| `2022-03-04T06:24:58+00:00` | `helium_legacy_cointracking` | `helium_legacy_raw` | 0.01565995525727 | nein |
| `2022-05-02T05:12:04+00:00` | `helium_legacy_cointracking` | `helium_legacy_raw` | 0.02566584535961 | nein |
| `2022-07-12T04:07:22+00:00` | `helium_legacy_raw` | `helium_legacy_cointracking` | 0 | nein |
| `2022-12-31T21:57:55+00:00` | `helium_legacy_raw` | `helium_legacy_cointracking` | 0 | nein |

### Binance-Historie 2021-08

- Datei: `usertransfer/legacy_daten/Heliumtracker/advance/Binance Export History Daten 2021 2022.xlsx`
- Gepruefte Rohzeilen: `5565`
- Der Auszug bestaetigt HNT-Deposits am `2021-08-06`, `2021-08-10` und `2021-08-20`; zwischen `2021-08-10` und den HNT-Verkaeufen am `2021-08-17` ist kein zusaetzlicher Binance-HNT-Deposit sichtbar.

| Zeit | Operation | HNT-Aenderung |
| --- | --- | ---: |
| `2021-08-06 19:03:34` | `Deposit` | 34.124 |
| `2021-08-06 19:07:32` | `Transaction Sold` | -113.097 |
| `2021-08-06 19:07:32` | `Transaction Sold` | -45.489 |
| `2021-08-10 16:56:06` | `Deposit` | 28.261 |
| `2021-08-10 16:57:47` | `Transaction Sold` | -8.34 |
| `2021-08-10 16:57:47` | `Transaction Sold` | -4.983 |
| `2021-08-10 16:57:47` | `Transaction Sold` | -15 |
| `2021-08-10 17:33:34` | `Deposit` | 79 |
| `2021-08-17 16:10:05` | `Transaction Sold` | -14.142 |
| `2021-08-17 16:10:05` | `Transaction Sold` | -17.406 |
| `2021-08-17 16:10:05` | `Transaction Sold` | -23.746 |
| `2021-08-17 16:10:05` | `Transaction Sold` | -0.425 |
| `2021-08-17 16:10:05` | `Transaction Sold` | -22.087 |
| `2021-08-17 16:10:05` | `Transaction Sold` | -1.209 |
| `2021-08-20 08:04:35` | `Deposit` | 18.30256046 |
| `2021-08-20 08:05:15` | `Transaction Sold` | -18.302 |

Abdeckungsschluss:

- Die im Workspace vorhandenen HeliumTracker-Dateien sind importiert; die HNT-Summen aus CSV und Store stimmen je Datei ueberein.
- Lokal vorhanden ist fuer `2021` nur `heliumtracker-report-advanced-2021-12.csv`; fuer die kritischen Binance-Verkaeufe am `2021-08-17` gibt es damit keine zusaetzliche lokale HeliumTracker-Quelle.
- Fuer `2022-02` bis `2022-07` sind HeliumTracker-Rewards importiert; sie reichen zusammen mit dem Legacy-Cointracking-Saldo aber nicht aus, um den `450.0398803021218`-HNT-Legacy-Outflow am `2022-07-12` belegbar zu decken.
- Die Excel-Dateien bestaetigen eine eigene Staking-Wallet `14eKed...`; dort fehlen aktuell Self-Transfer-Matches zur Haupt-Wallet `133...`.
- Diese Self-Transfer-Matches verbessern die Kettenbelegung, erzeugen aber keine Anschaffungskosten. Fuer die grossen 2022-Zufluesse in die Staking-Wallet bleibt die Herkunft vor der Staking-/Return-Wallet ungeklaert.
- Fuer `2021-08-17` zeigt die Excel-Spur keine zusaetzliche Binance-Einzahlung; die `100 HNT` am `2021-08-14` gingen zur Staking-Wallet und verliessen diese kurz danach wieder.

Quellen:

- BMF 2025: `https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Steuerarten/Einkommensteuer/2025-03-06-einzelfragen-kryptowerte-bmf-schreiben.pdf?__blob=publicationFile&v=3`
- BMF-Erlaeuterungsseite 2025: `https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Steuerarten/Einkommensteuer/2025-03-06-einzelfragen-kryptowerte.html`

## HNT-Bestandsschnitte

| Zeitpunkt | Kontext | Quelle | Events | Mining-Rewards HNT | In HNT | Out HNT | Saldo HNT |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `2021-08-17T16:10:05+00:00` | Vor den Binance-HNT-Verkaeufen ohne Lot-Quelle | `helium_legacy_cointracking` | 1471 | 555.1998127300000072746127 | 751.4291867300000072746127 | 736.763428275192399374 | 14.6657584548076079006127 |
| `2021-08-17T16:10:05+00:00` | Vor den Binance-HNT-Verkaeufen ohne Lot-Quelle | `helium_legacy_raw` | 7 | 0 | 356.48613564 | 356.36682102 | 0.11931462 |
| `2021-08-17T16:10:05+00:00` | Vor den Binance-HNT-Verkaeufen ohne Lot-Quelle | `heliumtracker` | 0 | 0 | 0 | 0 | 0 |
| `2021-08-17T16:10:05+00:00` | Vor den Binance-HNT-Verkaeufen ohne Lot-Quelle | `heliumgeek` | 0 | 0 | 0 | 0 | 0 |
| `2021-08-20T08:01:13+00:00` | Vor Legacy-Outflow zum Binance-Deposit 2021-08-20 | `helium_legacy_cointracking` | 1528 | 558.8505043200000073041147 | 755.0798783200000073041147 | 755.081881355567645374 | -0.0020030355676380698853 |
| `2021-08-20T08:01:13+00:00` | Vor Legacy-Outflow zum Binance-Deposit 2021-08-20 | `helium_legacy_raw` | 7 | 0 | 356.48613564 | 356.36682102 | 0.11931462 |
| `2021-08-20T08:01:13+00:00` | Vor Legacy-Outflow zum Binance-Deposit 2021-08-20 | `heliumtracker` | 0 | 0 | 0 | 0 | 0 |
| `2021-08-20T08:01:13+00:00` | Vor Legacy-Outflow zum Binance-Deposit 2021-08-20 | `heliumgeek` | 0 | 0 | 0 | 0 | 0 |
| `2022-07-12T06:59:57+00:00` | Vor Legacy-Outflow zum Binance-Deposit 2022-07-12 | `helium_legacy_cointracking` | 11997 | 999.45286711000001344810946 | 1616.98469222000001344810946 | 1583.12566892822612497 | 33.85902329177388847810946 |
| `2022-07-12T06:59:57+00:00` | Vor Legacy-Outflow zum Binance-Deposit 2022-07-12 | `helium_legacy_raw` | 19 | 0 | 898.93176298 | 898.70109472 | 0.23066826 |
| `2022-07-12T06:59:57+00:00` | Vor Legacy-Outflow zum Binance-Deposit 2022-07-12 | `heliumtracker` | 2228 | 238.59785864 | 238.59785864 | 30.837336935 | 207.760521705 |
| `2022-07-12T06:59:57+00:00` | Vor Legacy-Outflow zum Binance-Deposit 2022-07-12 | `heliumgeek` | 0 | 0 | 0 | 0 | 0 |

## Bewertung

- Eine automatische Bewertung der HNT-Deposits mit dem Legacy-Transferwert waere fachlich falsch, weil Transferwert nicht gleich Anschaffungskosten ist.
- Dass HNT im Legacy-Kontext aus Mining-Rewards stammt, hilft fachlich: Rewards koennen Anschaffungskosten tragen, wenn sie als bewertete Lots vorhanden sind.
- Fuer die konkreten Restzeilen reicht der belegte Legacy-Bestand vor den Outflows aber nicht aus; vorhandene Mining-Rewards wurden bereits vorher durch andere Outflows/Transfers verbraucht.
- Die 2021-HNT-Zeilen ohne Lot-Quelle liegen auf Binance-Verkaeufen am `2021-08-17`; fuer diese Verkaufsmenge gibt es im aktiven Datenstand keinen belegten vorherigen Binance-Deposit.
- Die Excel-Pruefung stuetzt diese Einordnung: Zwischen den bekannten Binance-Deposits am `2021-08-10` und den Verkaeufen am `2021-08-17` wurde kein weiterer Binance-HNT-Zufluss gefunden.
- Fuer den `2022-07-12`-Komplex ist die Luecke enger eingegrenzt: die Staking-Wallet erhielt kurz vorher `421.34562734 HNT` aus drei Legacy-Transfers und leitete `421.30245111 HNT` an die Haupt-Wallet zurueck; fuer diese drei Zufluesse fehlt weiterhin eine bewertete Primaerherkunft.
- Die 2022-USDT-Zeilen decken sich mit dem bereits dokumentierten Pionex-/Binance-Opening- und Bot-Historienproblem.
- Deshalb: keine neue automatische RAW-/FX-/Cost-Basis-Korrektur aus diesem Audit.

## Naechste sichere Aktion

- HNT: Primaerbelege fuer HNT-Anschaffung/Mining-Bestand vor den Legacy-Outflows nachreichen oder die historischen Nullbasis-Zeilen bewusst offen lassen.
- USDT: Pionex-Opening-/Bot-Historie oder explizite Review-Entscheidung verwenden; ohne Beleg keinen steuerwirksamen Zufluss importieren.

JSON: `var/hnt_usdt_remaining_inventory_gap_audit_2026-05-11.json`
