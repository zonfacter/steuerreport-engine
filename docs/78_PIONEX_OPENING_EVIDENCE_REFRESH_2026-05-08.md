# Pionex Opening Evidence Refresh - 2026-05-08

## Ziel

Der bestehende Pionex-USDT-Opening-Kandidat wurde gegen die vollstaendigen CSV-Exporte, die Pionex-API und die Pionex-only Modellbestaende nachgeschaerft.

## API-Probe

- JSON: `/workspace/steuerreport/var/pionex_api_history_probe_2026-05-08.json`
- Account Status: `ok`
- Aktuelle API-Balances: `{'BTC': '906.485E-9', 'JUP': '0.093774016835', 'MXC': '0.00002', 'USDT': '0.8958683252194125'}`
- Historische Fill-Preview `2021-12-25..2022-02-01`: `0` Rows
- Historische Fill-Preview `2022-01`: `0` Rows
- Historische Fill-Preview `2024-11`: `0` Rows

Die API ist erreichbar, liefert aber fuer die getesteten alten Handelsfenster keine historischen Fills. Damit ersetzt die API keinen Account-/Bot-Startnachweis.

## Pionex-Only Modell vs aktuelle API-Balance

| Asset | Modell final | API aktuell | Differenz API - Modell |
|---|---:|---:|---:|
| `BTC` | `910.00000000000E-9` | `906.485E-9` | `-3.51500000000E-9` |
| `BUSD` | `0.00211223520000000000` | `0` | `-0.00211223520000000000` |
| `EGLD` | `0.00E-18` | `0` | `0.00E-18` |
| `HNT` | `-0.16629829000000000000` | `0` | `0.16629829000000000000` |
| `JUP` | `0.09377402000000000000` | `0.093774016835` | `-3.16500000000E-9` |
| `MXC` | `0.00002000000000000000` | `0.00002` | `0.00E-18` |
| `SHIB` | `0.00E-18` | `0` | `0.00E-18` |
| `SOL` | `0.00E-18` | `0` | `0.00E-18` |
| `USDT` | `0.89137980652611250000` | `0.8958683252194125` | `0.00448851869330000000` |

Die Restbestaende aus dem CSV-Modell passen eng zu den aktuellen API-Balances. Das stuetzt den CSV-Import, beweist aber keinen historischen Startbestand.

## Erforderliches Pionex-only Startinventar nach Asset

| Asset | Minimal erforderlicher Startbestand | Ausloesender Tiefpunkt |
|---|---:|---|
| `BTC` | `120E-9` | `2023-03-10T09:10:58+00:00` `fee/out` `s_0:592:fee:BTC` |
| `BUSD` | `0.12348776480000000000` | `2023-01-14T08:14:03+00:00` `fee/out` `s_0:588:fee:BUSD` |
| `EGLD` | `0.00074550` | `2022-01-05T11:40:01+00:00` `fee/out` `s_7:51:fee:EGLD` |
| `HNT` | `0.16876807000000000000` | `2022-09-09T04:17:39+00:00` `trade/out` `s_0:468:out:HNT` |
| `JUP` | `0.01085231` | `2024-03-12T04:47:59+00:00` `fee/out` `s_0:594:fee:JUP` |
| `MXC` | `0.62965500` | `2022-01-18T10:32:14+00:00` `fee/out` `s_8:61:fee:MXC` |
| `USDT` | `1643.40556756620000000000` | `2022-01-19T23:28:01+00:00` `fee/out` `s_10:69:fee:USDT` |

## Bewertung

- Der grosse offene Punkt bleibt `USDT` mit `1643.40556756620000000000`.
- Kleine Pionex-only Minima in HNT/MXC/JUP/BUSD/BTC/EGLD wirken wie Bot-/Fee-Restchronologie und sind global weitgehend durch andere Quellen oder Dust-Review abgefedert.
- Kein weiterer Pionex-Import wurde durchgefuehrt; RAW-Daten bleiben unveraendert.
- Der bestehende Kandidat bleibt `tax_effective=false` und wurde nur mit Evidenz ergaenzt.

## Naechste Entscheidung

Fuer einen finalen Report braucht es entweder einen externen Nachweis fuer das Pionex-Bot-Startinventar oder eine explizite fachliche Entscheidung, diesen Review-Kandidaten als dokumentierte Ersatzrekonstruktion zu behandeln.
