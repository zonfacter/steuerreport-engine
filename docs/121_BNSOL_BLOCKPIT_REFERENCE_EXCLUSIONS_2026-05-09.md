# BNSOL Blockpit Reference Exclusions - 2026-05-09

## Zweck

Blockpit-BNSOL-Referenzzeilen ausschliessen, wenn Binance-API-Primary fuer Staking/Earn/Convert vorhanden ist.

- Kandidaten: `17`
- Eingetragen/aktualisiert: `17`
- Unveraendert: `0`

## Beispiele

- `2025-03-23T23:59:59+00:00` `interest` `in` qty `390E-9` tx `blockpit-1464:in` raw `BNSOL001-REALTIME-BNSOL-1742774399000`
- `2025-03-23T13:46:29+00:00` `trade` `out` qty `22.32305193` tx `blockpit-1467:out` raw `1958518736382069622`
- `2025-03-22T23:59:59+00:00` `interest` `in` qty `680E-9` tx `blockpit-1468:in` raw `BNSOL001-REALTIME-BNSOL-1742687999000`
- `2025-03-21T23:59:59+00:00` `interest` `in` qty `690E-9` tx `blockpit-1469:in` raw `BNSOL001-REALTIME-BNSOL-1742601599000`
- `2025-03-20T23:59:59+00:00` `interest` `in` qty `690E-9` tx `blockpit-1470:in` raw `BNSOL001-REALTIME-BNSOL-1742515199000`
- `2025-03-19T23:59:59+00:00` `interest` `in` qty `690E-9` tx `blockpit-1471:in` raw `BNSOL001-REALTIME-BNSOL-1742428799000`
- `2025-03-18T23:59:59+00:00` `interest` `in` qty `690E-9` tx `blockpit-1472:in` raw `BNSOL001-REALTIME-BNSOL-1742342399000`
- `2025-03-17T23:59:59+00:00` `interest` `in` qty `700E-9` tx `blockpit-1473:in` raw `BNSOL001-REALTIME-BNSOL-1742255999000`
- `2025-03-16T23:59:59+00:00` `interest` `in` qty `700E-9` tx `blockpit-1475:in` raw `BNSOL001-REALTIME-BNSOL-1742169599000`
- `2025-03-16T11:35:38+00:00` `auto-balancing in` `in` qty `22.32304257` tx `blockpit-1477:in` raw ``
- `2025-03-15T23:59:59+00:00` `interest` `in` qty `700E-9` tx `blockpit-1478:in` raw `BNSOL001-REALTIME-BNSOL-1742083199000`
- `2025-03-14T23:59:59+00:00` `interest` `in` qty `710E-9` tx `blockpit-1479:in` raw `BNSOL001-REALTIME-BNSOL-1741996799000`
- `2025-03-13T23:59:59+00:00` `interest` `in` qty `720E-9` tx `blockpit-1480:in` raw `BNSOL001-REALTIME-BNSOL-1741910399000`
- `2025-03-12T23:59:59+00:00` `interest` `in` qty `720E-9` tx `blockpit-1481:in` raw `BNSOL001-REALTIME-BNSOL-1741823999000`
- `2025-03-11T23:59:59+00:00` `interest` `in` qty `740E-9` tx `blockpit-1482:in` raw `BNSOL001-REALTIME-BNSOL-1741737599000`
- `2025-03-10T23:59:59+00:00` `interest` `in` qty `720E-9` tx `blockpit-1483:in` raw `BNSOL001-REALTIME-BNSOL-1741651199000`
- `2025-03-09T23:59:59+00:00` `interest` `in` qty `160E-9` tx `blockpit-1486:in` raw `BNSOL001-REALTIME-BNSOL-1741564799000`

## Bewertung

- This is intentionally limited to Blockpit/Binance BNSOL rows.
- Binance API primary rows cover staking conversion, daily BNSOL earn rewards and conversion out.
- Excluding Blockpit rows removes duplicate BNSOL micro-undercoverage without deleting evidence.
