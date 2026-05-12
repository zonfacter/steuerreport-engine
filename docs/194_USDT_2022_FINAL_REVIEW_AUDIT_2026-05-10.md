# USDT 2022 Finaler Review-Audit

Stand: 2026-05-10

## Ergebnis

- Status: `final_read_only_review`
- Job: `942afb62-85f5-4690-9b74-2e6195d5205f`
- Offene Nullbasis-Zeilen: `3`
- Betroffene Menge: `1569.34243684620000000000 USDT`
- Erloes: `1383.448602294939514000000000 EUR`
- Erster aktiver Bruch: `2022-01-05T15:36:46+00:00` nach `-75.10462220620000000000 USDT`
- Schlechtester Stand: `-1569.91028184620000000000 USDT` bei `2022-01-19T12:56:19+00:00`
- Finaler USDT-Stand nach allen Daten: `1720.33575614902711250000 USDT`
- Plattform-Mengen: `{'binance': '75.10462220620000000000', 'pionex': '1494.23781464000000000000'}`

## Schlussfolgerung

- Die verbliebenen drei USDT-Zeilen sind keine Preis-/FX- oder Stable-Pair-Fehlbewertung.
- Die Pionex-HNT- und Stable-Pair-Korrekturen wurden bereits eingerechnet; HNT 2023, USDC 2024 und JUP 2024 sind geschlossen.
- Automatische steuerwirksame Rekonstruktion bleibt fachlich nicht sauber, weil ein Primaerbeleg fuer die konkrete USDT-Anschaffungskette fehlt.
- Das Issue kann technisch im Dashboard/API als Nullbasis bestaetigt werden; das ist eine Review-Entscheidung und keine RAW-Daten-Aenderung.

## Betroffene Zeilen

| Line | Zeit | Quelle | Menge | Erloes EUR | Balance vorher | Balance nach | Befund |
|---:|---|---|---:|---:|---:|---:|---|
| 1679 | `2022-01-05T15:36:46+00:00` | `binance` `trade` | 75.10462220620000000000 | 66.3526805805115140000000000 | 111.16537779380000000000 | -75.10462220620000000000 | Binance-USDT-Verwendung am 2022-01-05T15:36:46+00:00; im unmittelbaren Fenster liegen mehrere gleichzeitige HNT-Kaeufe/USDT-Spends. Der Bruch entsteht nach der letzten USDT-Verwendung und benoetigt eine vorherige USDT-Erwerbskette. |
| 1709 | `2022-01-19T12:45:42+00:00` | `pionex` `trade` | 168.84689687000000000000 | 148.8300972460615000000000000 | 236.04155809380000000000 | -243.95151907620000000000 | Pionex-MXC-Kauf wenige Minuten vor der belegten Binance-USDT-Auszahlung und Pionex-USDT-Einzahlung. Das spricht fuer Pionex-Opening-/Bot-Kontext oder nicht exportierte interne Historie. |
| 2811 | `2022-01-19T12:56:19+00:00` | `pionex` `trade` | 1325.39091777000000000000 | 1168.265824468366500000000000 | 1002.24353892380000000000 | -1569.91028184620000000000 | Pionex-MXC-Kauf nach der bekannten 1245.38419-USDT-Transferkette, aber der Kaufbedarf uebersteigt den belegten Bestand; mit naher Pionex-Deposit-Zeile. Rest erklaert sich nur mit Opening-/Bot-Historie. |

## Gepruefte Belege

- `Binance Transaction History Jan 2022`: `usertransfer/Binance/export 2021/Binance-Transaction-History-202605061835(UTC+2)_344d77e2.xlsx` -> liefert die HNT/USDT-Trades am 2022-01-05 und 2022-01-19, aber keine zusaetzliche vorherige USDT-Anschaffung fuer die Nullbasis-Reste.
- `Pionex Komplett-Export`: `usertransfer/pionex/` -> liefert MXC_USDT-Bot-/Trade-Zeilen und die bekannten Deposits; fuer den 2022-01-19-Rest fehlt weiterhin eine belegte Opening-/Bot-Historie.
- `Binance API/CSV Transferkette`: `raw_events/binance_api + usertransfer/Binance/export 2021/` -> belegt die 1245.38419-USDT-Auszahlung zu Pionex am 2022-01-19, deckt aber nicht den kompletten Pionex-Kaufbedarf.
- `Aktueller Gesamtlauf 2020..2026`: `docs/190_CURRENT_TAX_RUNS_2026-05-10.md` -> Review-Gate ist exportfaehig; nur dieses Medium-Issue bleibt offen.

## Saubere Entscheidungswege

- `offen lassen`: Report bleibt mit Medium-Issue dokumentiert; keine fachliche Nullbasis-Freigabe.
- `Nullbasis bestaetigen`: Issue per API/Dashboard auf wont_fix setzen; Steuerzeilen bleiben mit Cost Basis 0 sichtbar.
- `Primaerbeleg nachreichen`: Neue Quelle importieren und Job neu rechnen; nur dann waere eine echte Cost-Basis-Korrektur sauber.

## Review-Entscheidung 2026-05-10

- Entscheidung: `offen lassen`.
- Begruendung: Die Steuerjahre `2020`, `2021` und `2022` sind steuerlich bereits abgeschlossen; eine Korrektur ist nach aktuellem Kenntnisstand wahrscheinlich nicht mehr sinnvoll bzw. nicht mehr moeglich.
- Umsetzung: Das Issue wird nicht per API auf `wont_fix` gesetzt. Die Nullbasis-Zeilen bleiben sichtbar dokumentiert.
- Folge: Keine RAW-Aenderung, keine automatische steuerwirksame Zuflussfiktion, keine fachliche Nullbasis-Freigabe.

## Wichtig fuer den Report

- Keine RAW-Datei wurde veraendert.
- Keine automatische Zuflussfiktion wurde importiert.
- Eine Bestaetigung der Nullbasis ist nur eine Review-Freigabe, keine Aenderung der Steuerlogik.
- Bei neuen Pionex-/Binance-/Bitget-Exporten muss dieser Audit erneut ausgefuehrt und der 2022-Job neu gerechnet werden.

JSON: `var/usdt_2022_final_review_audit_2026-05-10.json`
