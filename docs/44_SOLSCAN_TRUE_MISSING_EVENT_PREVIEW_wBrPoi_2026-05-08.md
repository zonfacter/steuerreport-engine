# Solscan Missing Event Preview 2026-05-08

- Wallet: `wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB`
- Bekannte lokale Solana-RPC-Signaturen: `2368`
- Solscan Account-Transactions: `2372`
- Fehlende Signaturen: `8`
- Vorgeschlagene Event-Zeilen: `7`
- JSON: `var/solscan_missing_event_preview_true_missing_wBrPoi_2026-05-08.json`

## Klassen
- `mixed_transfer`: `1`
- `technical_account_or_metadata`: `2`
- `transfer_in_or_airdrop`: `5`

## Jahr/Klasse
- `2026`: mixed_transfer=1, technical_account_or_metadata=2, transfer_in_or_airdrop=5

## Bewertung
- Diese Datei ist ein Preview, noch kein Import.
- `dex_swap_or_route` wird als Netto-Bewegung je Token vorgeschlagen; komplexe Routen koennen mehrere In-/Out-Zeilen erzeugen.
- `technical_account_or_metadata` erzeugt keine steuerliche Event-Zeile.
- Vor dem produktiven Import sollte die Auswirkung auf negative Bestände per Dry-Run geprüft werden.

## Erste vorgeschlagene Zeilen
- `2026-05-07T14:53:43+00:00` `token_transfer` `in` `0.40107403 HNT` tx=`3okDViKxuvYdB8HefDcVJu1e2JykmufwMCafhSrxDzdqqPBxmFjGGfg6YoqJ3j3TVrkXLtGU1Q6xpFeXkZpWR55d`
- `2026-05-07T14:53:43+00:00` `token_transfer` `in` `0.30469981 HNT` tx=`5yvaY2k6bCrpghJM9fYYn3S4efxxrYUbaDC8AQSPZzp7HBDka7AsS49FQ65dUeW83RXXj3G2KfBaGSthrxz4oJLN`
- `2026-05-07T14:53:43+00:00` `sol_transfer` `out` `0.00242208 SOL` tx=`5yvaY2k6bCrpghJM9fYYn3S4efxxrYUbaDC8AQSPZzp7HBDka7AsS49FQ65dUeW83RXXj3G2KfBaGSthrxz4oJLN`
- `2026-05-07T14:53:43+00:00` `token_transfer` `in` `0.65457879 HNT` tx=`Rhax9L1jMNEfaniFUnCe9e9DuruCPpcbDZn4E4XUNgDCZQ6LCXmUDGCPsHaLd3rgNokbRHvR9GAbp4WDeUBGTZD`
- `2026-05-07T14:53:43+00:00` `token_transfer` `in` `1.70084235 HNT` tx=`ybVQpFSvjrXx9MFSdAPEdegBW8EHT92J2oxqMiUdwFCUQWAJ5N5PGqG6brvXcgUVPfAwVMXoJK4sXUPjaiQub4f`
- `2026-05-07T14:54:00+00:00` `token_transfer` `in` `0.88772284 HNT` tx=`44yqZvw1rCEEmEWiUqpRbUSdF9W5zmyV7rcWJrnwjc8Kg882hMi6eYNTk8gy4HvaiepNakUg5vGwijqY7bmvhqy3`
- `2026-05-07T14:54:00+00:00` `token_transfer` `in` `0.04536555 HNT` tx=`jjp7dnUeskNMDjoVdY3rXqmTHfwFigm4YjDFGnAYrVTKpVGA7fNPi24X5PvbuxmqRCanrz4SKjdsLoDLMKARZC2`
