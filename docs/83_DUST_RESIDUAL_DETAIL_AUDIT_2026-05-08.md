# Dust Residual Detail Audit 2026-05-08

JSON: `var/dust_residual_detail_audit_2026-05-08.json`

## BUSD

- Events: `7`
- Endbestand: `-0.55168701480000000000`
- Quellen: `{'pionex': 6, 'binance_api': 1}`
- Eventtypen: `{'trade': 4, 'fee': 2, 'dust_convert_out': 1}`

| Zeit | Quelle | Typ | Side | Delta | Balance danach | TX |
|---|---|---|---|---:|---:|---|
| `2022-10-15T13:41:59+00:00` | `pionex` | `trade` | `in` | `159.46052130000000000000` | `159.46052130000000000000` | `s_0:562:in:BUSD` |
| `2022-10-15T13:41:59+00:00` | `pionex` | `fee` | `out` | `-0.07973026` | `159.38079104000000000000` | `s_0:562:fee:BUSD` |
| `2022-10-15T13:42:51+00:00` | `pionex` | `trade` | `out` | `-159.38079100480000000000` | `3.520000000000E-8` | `s_0:563:out:BUSD` |
| `2023-01-14T08:14:03+00:00` | `pionex` | `fee` | `out` | `-0.12348780` | `-0.12348776480000000000` | `s_0:588:fee:BUSD` |
| `2023-01-14T08:14:03+00:00` | `pionex` | `trade` | `in` | `246.97560000000000000000` | `246.85211223520000000000` | `s_0:588:in:BUSD` |
| `2023-01-16T18:44:40+00:00` | `pionex` | `trade` | `out` | `-246.85000000000000000000` | `0.00211223520000000000` | `s_0:589:out:BUSD` |
| `2023-05-02T04:13:23+00:00` | `binance_api` | `dust_convert_out` | `out` | `-0.55379925` | `-0.55168701480000000000` | `136251331484` |

Bewertung:

- Kleinbetrag aus Pionex-BUSD-Fees/Trades plus Binance Dust-Convert-Out. Der erste Bruch entsteht schon bei einer Pionex-Fee von `0.12348780 BUSD`; das passt zum bereits bekannten Pionex-Opening-/Startbestand-Thema.

## VTHO

- Events: `1`
- Endbestand: `-42.39387934`
- Quellen: `{'binance_api': 1}`
- Eventtypen: `{'dust_convert_out': 1}`

| Zeit | Quelle | Typ | Side | Delta | Balance danach | TX |
|---|---|---|---|---:|---:|---|
| `2023-05-02T04:13:23+00:00` | `binance_api` | `dust_convert_out` | `out` | `-42.39387934` | `-42.39387934` | `136251331484` |

Bewertung:

- Nur ein effektiver Ausgang aus Binance Dust-Convert. Kein korrespondierender Zufluss im aktuellen Datenbestand. Das spricht fuer fehlenden Alt-/Dust-Bestand oder eine nicht mehr exportierbare kleine Quelle, nicht fuer einen grossen systematischen Bruch.
