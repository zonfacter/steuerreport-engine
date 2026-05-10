# Solscan Bitget Counterflow Dec 2024 Import - 2026-05-08

## Zweck

Import einer bestaetigten Solscan-USDT-Gegenbuchung zum Bitget-Abgang vom `2024-12-01`.

## Import

- Quelle: `solscan_account_transfers`
- Source Name: `solscan_bitget_counterflow_dec2024_2026-05-08`
- Wallet: `wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB`
- Signatur: `mxDAzS4vybHXsuUscyeXTrAQwsjKz3pbs9hHpZp6Ld68iMjHetSWahTCVf1MG4Uakbme7ZsWGMcJPEUTkXPhNus`
- Zeit: `2024-12-01T13:32:32+00:00`
- Event: `token_transfer` `in` `1988.00826 USDT`
- Inserted Events: `1`
- Duplicate Events: `0`

## Bewertung

Die Zeile lag bereits in der Solscan-Transferdatenbank, war aber nicht als `raw_event` aktiv. Sie erklaert die fehlende On-Chain-Gegenbuchung zum Bitget-Withdrawal-Fenster und darf nicht als manueller Adjustment-Kandidat behandelt werden.
