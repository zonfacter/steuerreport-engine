# Fairspot HNT Legacy Transfer Trace

Stand: 2026-05-11

## Ergebnis

- Fairspot stellt fuer Legacy-Helium-Wallets statische CSVs bereit.
- Die CSVs enthalten `payer`, `payee`, `transaction_hash`, HNT-Menge, HNT-Fee und Helium-Oracle-USD-Werte.
- Die fehlende 2022-HNT-Kette laesst sich bis zur Counterparty-Wallet `14aDLshY...` nachvollziehen.
- `14aDLshY...` wirkt in den Fairspot-Daten wie eine stark genutzte Sammel-/Pool-/Service-Wallet; das ist eine Dateninferenz, kein steuerliches Urteil.
- Fuer `2021-08-17` ergibt sich kein zusaetzlicher Binance-Zufluss.

## Quellen

- Fairspot-Seite: `https://www.fairspot.host/hnt-export-mining-tax`
- Fairspot-CSV-Pattern: `https://fairspot.nyc3.digitaloceanspaces.com/accounting-csv/helium-{wallet}-all.csv`

## Wallets

- Haupt-Wallet: `133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j`
- Staking-Wallet: `14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA`
- Counterparty/Payout-Wallet: `14aDLshY7p2MJrCgbYrWFZZfjB1MBSqHboo2cJCPCVR9Meorh7w`

## Kritische Transaktionen

| Datum | Tx | Typ | HNT | Fee HNT | USD | Payer | Payee |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| `2021-08-14 17:15:46` | `n7pUrLCjNgmbd95CzofzUJAzMz6zlAZJqRmzYk_um7M` | `payment_v2` | 100 | 0.021256586125461836 | 1646.55 | `133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j` | `14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA` |
| `2021-08-14 18:42:22` | `LFebJjnxaKi5MkKKVWmCjGsBKNHzKbR83wnkms_BQV4` | `payment_v1` | 100.40763734 | 0.021256586125461836 | 1653.26 | `14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA` | `14aDLshY7p2MJrCgbYrWFZZfjB1MBSqHboo2cJCPCVR9Meorh7w` |
| `2022-07-12 01:04:31` | `q4_AgR7s3njJdUfMZkdUiUt_zDIvnjA-kavtXKu5bHE` | `payment_v1` | 254.95946999 | 0.04053001681995698 | 2201.72 | `14aDLshY7p2MJrCgbYrWFZZfjB1MBSqHboo2cJCPCVR9Meorh7w` | `14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA` |
| `2022-07-12 01:07:51` | `48Jt0OydVHYIZrwqPX0348Rkwk5cy9yLjyxnQlv7TKo` | `payment_v1` | 100.36710733 | 0.04050925925925925 | 867.17 | `14aDLshY7p2MJrCgbYrWFZZfjB1MBSqHboo2cJCPCVR9Meorh7w` | `14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA` |
| `2022-07-12 01:08:41` | `7ABuG00VMpdR9jG9BevdWXZWY7CuQ3ZhgHrov7XeRGE` | `payment_v1` | 66.01905002 | 0.04050925925925925 | 570.4 | `14aDLshY7p2MJrCgbYrWFZZfjB1MBSqHboo2cJCPCVR9Meorh7w` | `14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA` |
| `2022-07-12 04:07:22` | `8FHBnG2SF9IoQ3J_d5c9KuAkFVs-_mwERFe_Ix4eJbA` | `payment_v1` | 421.30245111 | 0.040270386883359696 | 3661.64 | `14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA` | `133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j` |

## Staking-Counterparty-Saldo

| Scope | Zeilen | An Counterparty HNT | Fees HNT | Von Counterparty HNT | Netto Rueckfluss minus Sendung/Fee HNT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bis `2022-07-12 01:08:41` | 11 | 477.39864361 | 0.182363194919347751 | 421.34562734 | -56.235379464919347751 |
| Alle Fairspot-Zeilen | 18 | 477.39864361 | 0.182363194919347751 | 495.50242597 | 17.921419165080652249 |

## Alle direkten Staking-Wallet-/Counterparty-Zeilen

| Datum | Richtung | Tx | HNT | Fee HNT | USD |
| --- | --- | --- | ---: | ---: | ---: |
| `2021-06-24 04:46:12` | `out` | `8seUfYbb24LtOCs6ywjDmq5KeSutpZEM6Ik4bBeotts` | 99.5 | 0.02936241610738255 | 1186.04 |
| `2021-06-24 07:46:50` | `out` | `rGqIaeFQfJ_JcnYeeyjKkJ18JDtTU6PNL9654WY1yc4` | 155.5 | 0.030430681082115017 | 1788.49 |
| `2021-07-17 04:48:26` | `out` | `GEwQc-qm2jBcW2hoMlCgupbEEGO58X0fGGIUiR9GIc0` | 0.95918368 | 0.03401360544217687 | 9.87 |
| `2021-08-14 18:42:22` | `out` | `LFebJjnxaKi5MkKKVWmCjGsBKNHzKbR83wnkms_BQV4` | 100.40763734 | 0.021256586125461836 | 1653.26 |
| `2022-01-27 19:17:41` | `out` | `MlnudV0DEM21qk9GmZtZYrnsvpoTROZymsYZrQJ7tZU` | 39.98517905 | 0.012323943661971828 | 1135.58 |
| `2022-02-02 19:07:39` | `out` | `rr90g4oRPOsVrXUkH7YwgRSn-myEmG8-3NzNisAQvTI` | 10.99050073 | 0.013555383423702555 | 283.77 |
| `2022-03-04 06:33:07` | `out` | `iz0CLP84W4ujGS_Pl_gwAwXUgVpyp5wD4DSCQYM6BYw` | 15.08390025 | 0.01565995525727069 | 337.13 |
| `2022-05-02 05:46:51` | `out` | `NY0qEx7-fr35JEwW-qGbmnrw86ypSbQNbHplGyV6oLM` | 54.97224256 | 0.025760623819266405 | 746.89 |
| `2022-07-12 01:04:31` | `in` | `q4_AgR7s3njJdUfMZkdUiUt_zDIvnjA-kavtXKu5bHE` | 254.95946999 | 0 | 2201.72 |
| `2022-07-12 01:07:51` | `in` | `48Jt0OydVHYIZrwqPX0348Rkwk5cy9yLjyxnQlv7TKo` | 100.36710733 | 0 | 867.17 |
| `2022-07-12 01:08:41` | `in` | `7ABuG00VMpdR9jG9BevdWXZWY7CuQ3ZhgHrov7XeRGE` | 66.01905002 | 0 | 570.4 |
| `2022-12-25 08:42:34` | `in` | `zeNks7l6xqipT1hfVeiXi96L81pUlI65_QM_qaKVPl8` | 0.36782278 | 0 | 0.7 |
| `2022-12-25 08:42:34` | `in` | `fFy-RzjbZl1teOX0NeN5tL3wQROu5Od2PQAX4uDOVss` | 6.59498249 | 0 | 12.53 |
| `2022-12-25 08:43:35` | `in` | `yG-trfGaFExES3jq44pN0nm4OAgLNALmu24bQZE2FmE` | 2.16237208 | 0 | 4.11 |
| `2022-12-25 08:45:37` | `in` | `GTETgQC6o_rXoVAq8RlfaZmt3J5ERZWkuaWgGgiqsNU` | 2.52591341 | 0 | 4.8 |
| `2022-12-25 08:52:03` | `in` | `NNCS31PAXWma9TSZ1yyApLF6oMk2FFJw0-k6oGqWpNI` | 2.16594282 | 0 | 4.12 |
| `2022-12-25 08:52:03` | `in` | `ryergUNUXBoaBb5grwxIn2KZvczPxfl3oScE7Mvhypo` | 57.97808732 | 0 | 110.16 |
| `2022-12-29 15:14:41` | `in` | `OA5eErBzkbnhv1lvb_McJRQqUzLYP3zKGEGKtU-_7lI` | 2.36167773 | 0 | 3.99 |

## Counterparty-Kontext

- Payment-Zeilen der Counterparty bis zum Rueckfluss: `24699`
- Eingehende Payment-Zeilen an die Counterparty bis zum Rueckfluss: `21583`
- Einzigartige Payer an die Counterparty bis zum Rueckfluss: `5502`
- Diese Breite spricht gegen eine einfache zweite eigene Wallet und eher fuer Pool-/Service-/Sammelwallet-Kontext.

## Bewertung

- Die Fairspot-Daten belegen, dass der 2022-Binance-Deposit ueber `14eKed...` und `133rkwo...` aus einem Rueckfluss von `14aDLshY...` stammt.
- Bis zum Rueckfluss am `2022-07-12` hatte `14eKed...` netto noch weniger von `14aDLshY...` zurueckerhalten als vorher an diese Wallet gesendet.
- Daraus folgt technisch: Die 2022-HNT-Luecke ist wahrscheinlich kein komplett neuer unbelegter Zufluss, sondern eine nicht modellierte Staking-/Custody-Rueckgabe-Kette.
- Nicht automatisch ableiten: Anschaffungskosten, steuerliche Reward-Aufteilung oder Eigentumsstatus von `14aDLshY...`.

## Naechste sichere Aktion

- Einen separaten Korrekturpfad fuer `14eKed...` <-> `14aDLshY...` als Staking-/Custody-Kette bauen.
- Dabei zuerst nur Transfer-/Continuity-Belege persistieren, wenn die Chain-Regeln mehrere Outbounds gegen spaetere Rueckfluesse sauber tragen.
- Falls die Rueckfluesse fachlich als Staking-Rewards statt Rueckgabe von Principal behandelt werden sollen, muss das als Review-Entscheidung mit Fairspot-Oracle-USD-Werten dokumentiert werden.

JSON: `var/fairspot_hnt_legacy_transfer_trace_2026-05-11.json`
