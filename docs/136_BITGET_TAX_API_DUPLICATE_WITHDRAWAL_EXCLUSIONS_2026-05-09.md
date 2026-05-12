# Bitget Tax API Duplicate Withdrawal Exclusions - 2026-05-09

## Ergebnis

- Modus: `execute`
- Matches: `2`
- Import: `{'excluded_event_count': 2, 'unchanged_exclusions': 0}`

## Matches

- `2025-06-15T07:30:36.015000+00:00` `JUP` tax net `4680.175116` fee `2.421894` api gross `4682.59701` tax `1318046255164071941` api `1318045704815505408` tx `46XuA2HVzr9DpksJj9jTu2vDaFMg2eZK7Akiq6D6UnJ53NbndJaS88zsy6Naim25VC4RHTBgkvbtDd3nDFEck7xw`
- `2025-06-15T07:45:46.005000+00:00` `SOL` tax net `7.0700475` fee `0.006` api gross `7.0760475` tax `1318050071942963200` api `1318049559880003584` tx `5C1y93cUomwwrcarubiTgewuNA9hiUHY2JAc5LYrZQYMjmtj6cFdYvjoM8mEr5cLzuo1iXeDs9W8vi8oJ1iCnbG3`

## Bewertung

- Bitget API bleibt aktiv, weil diese Quelle Bruttobetrag, Zieladresse und Onchain-Trade-ID enthaelt.
- Bitget Tax API Withdrawal ist fuer diese Matches ein doppelter Nettobeleg plus Fee-Feld.
- Bitget Tax API Transfer-In bleibt aktiv, weil diese internen Bewegungen fuer Plattform-Salden relevant sein koennen.
