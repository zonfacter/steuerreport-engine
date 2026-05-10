# Bitget 2025 API Deep Probe - 2026-05-09

## Zweck

Der Nutzer hat klargestellt, dass `bitget` `2025` soweit moeglich per API gezogen werden soll. Dieser Lauf nutzt ausschliesslich die gespeicherten Bitget-Secrets aus den Admin-Settings und gibt keine Secrets aus.

## Lauf

- Modus: `execute`
- API-Key: `bg_4...d572`
- Credential-Check ok: `True`
- Zeitraum: `2025-01-01` bis `2025-12-31`
- Fenster: `30` Tage
- Fenster gesamt: `13`
- Fehlerfenster: `0`
- API-Zeilen: `1138`
- Neu importiert: `0`
- Duplikate: `1138`

## Quellen

- `bitget_tax_api`: `1136`
- `bitget_api`: `2`

## Eventtypen

- `derivative open_long`: `247`
- `derivative close_long`: `235`
- `derivative close_short`: `202`
- `derivative open_short`: `198`
- `derivative fee`: `162`
- `trade`: `60`
- `transfer`: `16`
- `withdrawal`: `5`
- `derivative loss`: `3`
- `fiat_recharge_in`: `3`
- `deposit`: `2`
- `fiat_balance_user_out`: `2`
- `fiat_balance_success_user_in`: `2`
- `derivative user_grants_issue`: `1`

## Warnungen

- `fills_fetch_failed`: `13`
- `bitget_spot_account_bills_history_limit`: `13`

## Fenster

- `2025-01-01T00:00:00+00:00` bis `2025-01-30T23:59:59.999000+00:00`: `success`, Zeilen `70`, inserted `0`, duplicates `70`
- `2025-01-31T00:00:00+00:00` bis `2025-03-01T23:59:59.999000+00:00`: `success`, Zeilen `899`, inserted `0`, duplicates `899`
- `2025-03-02T00:00:00+00:00` bis `2025-03-31T23:59:59.999000+00:00`: `success`, Zeilen `3`, inserted `0`, duplicates `3`
- `2025-04-01T00:00:00+00:00` bis `2025-04-30T23:59:59.999000+00:00`: `success`, Zeilen `62`, inserted `0`, duplicates `62`
- `2025-05-01T00:00:00+00:00` bis `2025-05-30T23:59:59.999000+00:00`: `success`, Zeilen `98`, inserted `0`, duplicates `98`
- `2025-05-31T00:00:00+00:00` bis `2025-06-29T23:59:59.999000+00:00`: `success`, Zeilen `5`, inserted `0`, duplicates `5`
- `2025-06-30T00:00:00+00:00` bis `2025-07-29T23:59:59.999000+00:00`: `success`, Zeilen `1`, inserted `0`, duplicates `1`
- `2025-07-30T00:00:00+00:00` bis `2025-08-28T23:59:59.999000+00:00`: `success`, Zeilen `0`, inserted `0`, duplicates `0`
- `2025-08-29T00:00:00+00:00` bis `2025-09-27T23:59:59.999000+00:00`: `success`, Zeilen `0`, inserted `0`, duplicates `0`
- `2025-09-28T00:00:00+00:00` bis `2025-10-27T23:59:59.999000+00:00`: `success`, Zeilen `0`, inserted `0`, duplicates `0`
- `2025-10-28T00:00:00+00:00` bis `2025-11-26T23:59:59.999000+00:00`: `success`, Zeilen `0`, inserted `0`, duplicates `0`
- `2025-11-27T00:00:00+00:00` bis `2025-12-26T23:59:59.999000+00:00`: `success`, Zeilen `0`, inserted `0`, duplicates `0`
- `2025-12-27T00:00:00+00:00` bis `2025-12-31T23:59:59.999000+00:00`: `success`, Zeilen `0`, inserted `0`, duplicates `0`

## Bewertung

- Die API-Zeilen waren bereits als Duplikate im Datenbestand vorhanden.
- Connector-Warnungen: fills_fetch_failed=13, bitget_spot_account_bills_history_limit=13.
- Spot Account Bills bleiben fuer alte 2025-Zeitfenster API-seitig limitiert; dafuer sind Web-/Support-Exporte oder belegte Rekonstruktion noetig.
