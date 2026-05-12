# Blockpit Reference Export Import - 2026-05-09

## Zweck

Der neue Blockpit-Export aus `/workspace/steuerreport/usertransfer/blockpit/` wird als Referenz- und Abgleichsquelle gesichert. Er kann Bitget-Historie enthalten, die bei Bitget selbst ueber normale API/GUI-Retention nicht mehr vollstaendig sichtbar ist.

## Lauf

- Modus: `execute`
- Datei: `/workspace/steuerreport/usertransfer/blockpit/blockpit 09052026 Transactions.csv`
- Rohzeilen: `7629`
- Normalisierte Zeilen: `9446`
- Normalizer-Warnungen: `0`
- Normalizer-Errors: `0`
- Neu importierte RAW-Events: `9446`
- Duplikate: `0`
- Source File ID: `4535608dcfcf9aaa83ff8fdc91d6ac6e9463a286cdbd2a8a4dcdf5651220c55d`

## Rohdaten: Jahre

- `2025`: `3056`
- `2023`: `2143`
- `2024`: `2107`
- `2026`: `241`
- `2021`: `63`
- `2022`: `19`

## Rohdaten: Integrationen

- `Binance`: `3312`
- `Bitget`: `2375`
- `Solana`: `1942`

## Bitget Rohdaten

- Jahr `2025`: `2304`
- Jahr `2024`: `71`

## Bitget 2025 Labels

- `Derivative Fee`: `1518`
- `Derivative Loss`: `385`
- `Derivative Profit`: `351`
- `Trade`: `25`
- `Deposit`: `9`
- `Withdrawal`: `7`
- `Auto-Balancing Out`: `3`
- `Non-Taxable Out`: `2`
- `Non-Taxable In`: `2`
- `Auto-Balancing In`: `2`

## Bitget 2025 normalisierte Eventtypen

- `derivative fee`: `1518`
- `derivative loss`: `385`
- `derivative profit`: `351`
- `trade`: `50`
- `fee`: `30`
- `deposit`: `9`
- `withdrawal`: `7`
- `non-taxable out`: `2`
- `non-taxable in`: `2`

## Bewertung

- Der Export wurde als Blockpit-Referenzdatenquelle behandelt. Blockpit ist im System standardmaessig reference und wird nicht automatisch als Primaerquelle in Steuerlaeufe uebernommen.
- Der Export enthaelt 2304 rohe Bitget-Zeilen fuer 2025.
- Die Bitget-2025-Zeilen koennen fuer Matching gegen Bitget-API, On-Chain-Transfers und Supportexporte genutzt werden.
- Importiert: 9446 neue RAW-Events, 0 Duplikate.
