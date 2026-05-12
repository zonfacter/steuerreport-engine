# USDT 2022 Kreditkartenkauf-Belegaudit

Erstellt: `2026-05-12T19:38:48.210586+00:00`

## Anlass

Der Nutzer erinnert, dass USDT damals wahrscheinlich per Kreditkarte gekauft wurden. Dieser Audit prueft, ob dafuer lokal bereits ein belastbarer Import- oder Primaerbeleg fuer den verbleibenden 2022-USDT-Block vorhanden ist.

## Aktiver Restblock

- Offene 2022-USDT-Zeilen >= 50 EUR: `3`
- Offene Menge: `1569.8280684762 USDT`
- Betroffener Erloes: `1383.876662295203014 EUR`

## Ergebnis

- Die Erinnerung an einen Kreditkarten-/Fiat-Kauf ist als Suchhinweis plausibel.
- In der lokalen Readonly-Datenbank sind `fiat_crypto_purchase`-Events nur fuer `2021-02` bis `2021-04` vorhanden.
- Fuer `2021-12` oder `2022-01` gibt es lokal kein `fiat_crypto_purchase`-Event.
- Die lokale Binance-`Fiat-Buy-History`-XLSX ist vorhanden, enthaelt aber keine Datenzeilen.
- Damit gibt es derzeit keinen deterministischen automatischen Cost-Basis-Fix fuer die drei 2022-USDT-Restzeilen.

## Gefundene Fiat-Crypto-Kaeufe

- Anzahl Events: `8`
- USDT-In aus Fiat-Crypto-Kauf: `1438.22912 USDT`
- EUR-Out aus Fiat-Crypto-Kauf: `1304.73 EUR`

| Zeit UTC | Asset | Seite | Menge | Quelle | Row |
| --- | --- | --- | --- | --- | --- |
| 2021-02-06T21:18:15+00:00 | BNB | in | 1.625 | binance_selective:export 2021:transaction-related | 1 |
| 2021-02-06T21:18:15+00:00 | EUR | out | 98.1 | binance_selective:export 2021:transaction-related | 0 |
| 2021-02-23T10:57:37+00:00 | EUR | out | 98.1 | binance_selective:export 2021:transaction-related | 2 |
| 2021-02-23T10:57:37+00:00 | USDT | in | 118.600728 | binance_selective:export 2021:transaction-related | 3 |
| 2021-03-24T20:13:43+00:00 | EUR | out | 127.53 | binance_selective:export 2021:transaction-related | 4 |
| 2021-03-24T20:13:43+00:00 | USDT | in | 150.194365 | binance_selective:export 2021:transaction-related | 5 |
| 2021-04-19T15:17:37+00:00 | EUR | out | 981 | binance_selective:export 2021:transaction-related | 7 |
| 2021-04-19T15:17:37+00:00 | USDT | in | 1169.434027 | binance_selective:export 2021:transaction-related | 6 |

## Dec-2021/Jan-2022 Fiat-Kauf-Treffer

- Keine `fiat_crypto_purchase`-Events in `2021-12` oder `2022-01` gefunden.

## Binance-USDT/EUR im relevanten Fenster

- Binance-USDT/EUR-Events von `2021-12-01` bis `2022-01-31`: `83`
- Diese Events zeigen vor allem Trade-/Withdrawal-/Fee-Bewegungen, aber keinen importierten Kreditkartenkauf als Anschaffungskette.

| Monat | Asset | Seite | Summe |
| --- | --- | --- | --- |
| 2021-12 | USDT | in | 10748.5802 |
| 2021-12 | USDT | out | 10737.3096 |
| 2022-01 | USDT | in | 6910.8519 |
| 2022-01 | USDT | out | 6909.860843 |

## Lokale Fiat-Dateien

| Datei | Vorhanden | Datenzeilen | Sheets |
| --- | --- | --- | --- |
| usertransfer/Binance/export 2021/Binance-Fiat-Buy-History-202605061831(UTC+2)_c87830e5.xlsx | True | 0 | Sheet0:0 nonempty |
| usertransfer/Binance/export 2021/Binance-Fiat-Deposit-History-202605061832(UTC+2)_9311aa32.xlsx | True | 0 | Sheet0:0 nonempty |
| usertransfer/Binance/export 2021/Binance-Fiat-Withdraw-History-202605061833(UTC+2)_2416f4a2.xlsx | True | 0 | Sheet0:0 nonempty |

## Source-Coverage

| Quelle | Events | Von | Bis |
| --- | --- | --- | --- |
| binance_api_targeted_convert_fiat_2025_blockpit_reference_days | 12 | 2025-03-23T13:46:29.121000+00:00 | 2025-12-19T07:11:38+00:00 |
| binance_selective:export 2021:Binance-Fiat-Deposit-History-202605061832(UTC+2)_9311aa32.xlsx | 15 | 2021-03-05T05:45:57+00:00 | 2026-02-02T13:26:25+00:00 |
| binance_selective:export 2021:Binance-Fiat-Withdraw-History-202605061833(UTC+2)_2416f4a2.xlsx | 7 | 2021-03-27T13:16:45+00:00 | 2021-10-06T19:45:39+00:00 |
| binance_selective:export 2021:transaction-related | 8 | 2021-02-06T21:18:15+00:00 | 2021-04-19T15:17:37+00:00 |

## Suchbegriffe

| Suchbegriff | Treffer |
| --- | --- |
| card | 24 |
| credit | 0 |
| kredit | 0 |
| visa | 7 |
| mastercard | 0 |
| fiat_crypto_purchase | 8 |

## Naechste sichere Aktion

Benoetigt wird ein Primaerbeleg fuer den vermuteten Kauf: Binance `Buy Crypto` / `Fiat Order History` / Kartenkauf-Historie oder eine Kreditkarten-/Bankabrechnung fuer `2021-12` bis `2022-01` mit Zeit, EUR-Betrag, USDT-Menge und Gebuehren. Erst dann kann ein Import-/Review-Fix fuer die Anschaffungskosten sauber erstellt werden.

Kein automatischer Fix wurde abgeleitet, weil Nutzererinnerung allein keine Cost Basis, keinen FX-Kurs und keine steuerliche Behandlung belegt.
