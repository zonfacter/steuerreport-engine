# CEX Compliance Coverage - 2026-05-08

## Scope

- Erstellt: `2026-05-08T21:25:34.350555+00:00`
- Roh-Events: `45364`
- Effektive Events nach Review/Overrides: `40272`
- JSON: `/workspace/steuerreport/var/cex_compliance_coverage_2026-05-08.json`

## Status-Legende

- `complete`: keine offensichtliche Luecke aus der Matrix
- `partial`: Primaerdaten vorhanden, Vollstaendigkeit nicht final belegt
- `api_limited`: API-/Historienlimit bekannt
- `csv_required`: Datei/Export erforderlich oder liegt nur unimportiert vor
- `support_required`: Support/Statement benoetigt
- `unavailable_source_possible`: Quelle koennte historisch nicht mehr beschaffbar sein
- `opening_balance_required`: Startbestand/Botkapital muss belegt werden
- `manual_review`: fachliche Pruefung erforderlich
- `reference_only`: nur Referenzquelle, keine Primaerquelle
- `no_data`: keine Daten erkannt

## Matrix

| Plattform | Jahr | Status | Events | Primaer | Referenz | Zeitraum | Top-Quellen | Hinweise |
|---|---:|---|---:|---:|---:|---|---|---|
| `binance` | 2020 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. |
| `binance` | 2021 | `partial, manual_review` | 1331 | 1331 | 0 | 2021-02-06..2021-12-28 | binance:1294, binance_api:37 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. / Fruehe Binance-Historie ist zentral fuer Startbestaende und Pionex-Zufluesse. |
| `binance` | 2022 | `partial` | 107 | 107 | 0 | 2022-01-02..2022-10-14 | binance:101, binance_api:6 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. |
| `binance` | 2023 | `partial` | 1545 | 1545 | 0 | 2023-04-01..2023-12-31 | binance_api:1544, binance:1 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. |
| `binance` | 2024 | `partial` | 241 | 241 | 0 | 2024-01-01..2024-11-24 | binance_api:240, binance:1 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. |
| `binance` | 2025 | `partial` | 459 | 459 | 0 | 2025-01-19..2025-12-31 | binance_api:442, binance:17 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. / Binance 2025 ist nach aktuellem Stand primaerdatengefuehrt; Blockpit-Referenzereignisse wurden gegen API/CSV belegt und ausgeschlossen. |
| `binance` | 2026 | `partial` | 101 | 101 | 0 | 2026-01-27..2026-05-06 | binance_api:100, binance:1 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. |
| `pionex` | 2020 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `pionex` | 2021 | `partial, opening_balance_required` | 85 | 85 | 0 | 2021-12-25..2021-12-31 | pionex:85 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. / Bekannte Pionex-USDT-Unterdeckung Anfang 2022; Opening-Balance/Bot-Startkapital bleibt Nachweisbedarf. |
| `pionex` | 2022 | `partial, opening_balance_required` | 1776 | 1776 | 0 | 2022-01-01..2022-12-28 | pionex:1677, binance:99 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. / Bekannte Pionex-USDT-Unterdeckung Anfang 2022; Opening-Balance/Bot-Startkapital bleibt Nachweisbedarf. |
| `pionex` | 2023 | `partial` | 22 | 22 | 0 | 2023-01-05..2023-06-09 | pionex:22 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. |
| `pionex` | 2024 | `partial` | 17 | 17 | 0 | 2024-03-12..2024-11-22 | pionex:17 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. |
| `pionex` | 2025 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `pionex` | 2026 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. / Pionex-Dateien vorhanden; pruefen, ob der Zeitraum wirklich importiert ist. |
| `bitget` | 2020 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `bitget` | 2021 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `bitget` | 2022 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `bitget` | 2023 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `bitget` | 2024 | `partial, api_limited, support_required, unavailable_source_possible` | 61 | 61 | 0 | 2024-04-02..2024-12-07 | bitget_tax_api:60, solscan_wallet_discovery:1 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. / Bitget-Support ist angefragt; alte Spot/Bot/Grid/Internal-Transfer-Details koennen API-/Retention-bedingt fehlen. |
| `bitget` | 2025 | `partial, api_limited, support_required, unavailable_source_possible, manual_review` | 1986 | 1046 | 940 | 2025-01-29..2025-07-13 | bitget_tax_api:1044, blockpit:940, bitget_api:2 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. / Bitget-Support ist angefragt; alte Spot/Bot/Grid/Internal-Transfer-Details koennen API-/Retention-bedingt fehlen. |
| `bitget` | 2026 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `jupiter` | 2020 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. |
| `jupiter` | 2021 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. |
| `jupiter` | 2022 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. |
| `jupiter` | 2023 | `partial, manual_review` | 24 | 24 | 0 | 2023-04-26..2023-11-11 | solana_rpc:24 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. / Jupiter/Jup.ag ist Wallet-/On-Chain-nahe; Solscan/Jup-Export und Perps muessen gegeneinander abgeglichen bleiben. |
| `jupiter` | 2024 | `partial, manual_review` | 352 | 352 | 0 | 2024-02-15..2024-12-20 | solana_rpc:284, jupiter_perps:68 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. / Jupiter/Jup.ag ist Wallet-/On-Chain-nahe; Solscan/Jup-Export und Perps muessen gegeneinander abgeglichen bleiben. |
| `jupiter` | 2025 | `partial, manual_review` | 18 | 18 | 0 | 2025-03-04..2025-12-26 | solana_rpc:18 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. / Jupiter/Jup.ag ist Wallet-/On-Chain-nahe; Solscan/Jup-Export und Perps muessen gegeneinander abgeglichen bleiben. |
| `jupiter` | 2026 | `partial, manual_review` | 2 | 2 | 0 | 2026-01-02..2026-01-02 | solana_rpc:2 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. / Jupiter/Jup.ag ist Wallet-/On-Chain-nahe; Solscan/Jup-Export und Perps muessen gegeneinander abgeglichen bleiben. |
| `coinbase` | 2020 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `coinbase` | 2021 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `coinbase` | 2022 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `coinbase` | 2023 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `coinbase` | 2024 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `coinbase` | 2025 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `coinbase` | 2026 | `no_data` | 0 | 0 | 0 | - | - | Keine importierten Events und keine abgelegten Quelldateien fuer dieses Jahr erkannt. |
| `wiso_blockpit` | 2020 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. |
| `wiso_blockpit` | 2021 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. |
| `wiso_blockpit` | 2022 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. |
| `wiso_blockpit` | 2023 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. |
| `wiso_blockpit` | 2024 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. |
| `wiso_blockpit` | 2025 | `partial` | 1435 | 291 | 1144 | 2025-01-04..2025-12-26 | blockpit:1144, binance_api:291 | Primaerdaten vorhanden; Vollstaendigkeit muss je Eventtyp/Zeitraum belegt bleiben. |
| `wiso_blockpit` | 2026 | `csv_required` | 0 | 0 | 0 | - | - | Quelldateien liegen in usertransfer, aber es wurden keine effektiven Events fuer dieses Jahr erkannt. |

## Referenzquellen

| Jahr | Events | Zeitraum | Top-Quellen |
|---:|---:|---|---|
| 2020 | 0 | - | - |
| 2021 | 0 | - | - |
| 2022 | 0 | - | - |
| 2023 | 0 | - | - |
| 2024 | 0 | - | - |
| 2025 | 1144 | 2025-01-04..2025-12-26 | blockpit:1144 |
| 2026 | 0 | - | - |

## Bekannte Fakten

- RAW-Daten werden nicht geloescht oder still korrigiert; nur Review/Overrides/Adjustments.
- Pionex TRC20 Deposit-Adresse TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ hat 4 bekannte USDT-Deposits und 4 Sweeps.
- Die 4 bekannten Pionex-USDT-Deposits matchen Binance-Withdrawals per TXID.
- Bekannte Pionex-only USDT-Unterdeckung Anfang 2022 bleibt Opening-Balance/Bot-Startkapital-Thema.
- Bitget alte Spot-/Bot-/Grid-/Internal-Transfer-Historie ist per API limitiert; Support ist angefragt.
- Wenn Bitget alte Bot-Trade-Details nicht mehr liefern kann, wird die Luecke als unavailable_source_possible dokumentiert und nur ueber belegbare Salden/Transfers/PnL plausibilisiert.
- Blockpit/WISO sind eingereichte oder externe Referenzen, aber keine primaere Wahrheit.
- Jupiter/Jup.ag ist wallet-/on-chain-nah und muss gegen Solscan/Jup-Export/Jupiter-Perps abgeglichen werden.

## Naechste Datenaufgaben

- `1` `pionex` `2022`: Pionex Opening-Balance/Bot-Startkapital Anfang 2022 belegen oder Adjustment-Review vorbereiten. (Status: `partial, opening_balance_required`)
- `2` `bitget` `2025`: Bitget-Supportantwort abwarten; falls Bot-Trade-Details nicht mehr lieferbar sind, Rekonstruktionsbericht ueber Salden/Transfers/PnL erzeugen. (Status: `partial, api_limited, support_required, unavailable_source_possible, manual_review`)
- `3` `binance` `2021`: Binance 2021 als Startkette fuer HNT/USDT/Pionex-Zufluesse final gegen Withdraw/Trade/Fiat-Dateien pruefen. (Status: `partial, manual_review`)
- `4` `jupiter` `2025`: Jup.ag Export, Solscan-Transfers und Jupiter-Perps fuer 2025 gegen Wallet-Bestand abgleichen. (Status: `partial, manual_review`)

## File-Inventar Kurzfassung

- `binance`: 22 platform/year-Dateizuordnungen
- `jupiter`: 4 platform/year-Dateizuordnungen
- `pionex`: 115 platform/year-Dateizuordnungen
- `wiso_blockpit`: 14 platform/year-Dateizuordnungen
