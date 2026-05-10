# Jupiter/Solscan 2025 Coverage Audit 2026-05-08

- Wallet: `wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB`
- Alte Preview 2025: `20` Zeilen / `9` Signaturen
- True-Missing 2025: `0` Zeilen
- Entscheidung: `no_2025_solscan_import_needed`
- JSON: `var/jupiter_2025_solscan_coverage_audit_2026-05-08.json`

## Ergebnis

Für 2025 ist aktuell kein weiterer Solscan/Jupiter-Import sinnvoll. Die alte Lückenliste war eine Folge des zu engen Wallet-Adressfilters; der spätere True-Missing-Abgleich enthält keine 2025er Zeilen.

Alle 9 alten 2025-Signaturen sind lokal als Rohdaten vorhanden. Effektiv werden die Solana-RPC-Zeilen genutzt; zusätzlich vorhandene Solscan-Discovery-Zeilen bleiben als Kontroll-/Belegschicht, werden aber nicht blind doppelt steuerwirksam importiert.

## Verarbeitungskorrektur

Der FIFO-Kern verarbeitet bekannte Solana-Mints jetzt kanonisch als Symbol. Damit laufen z.B. `JUPYI...DvCN` und `JUP` im Steuerkern nicht mehr getrennt. Die Rohdaten werden dadurch nicht verändert.

- 2025 verarbeitete Events: `5459`
- 2025 Tax-Lines: `486`
- 2025 Short-Sell-Verletzungen: `90`
- Bekannte Solana-Mint-Inventar-Keys nach Kanonisierung: `0`

## Alte 2025-Preview-Signaturen
- `2025-03-04T08:17:03+00:00` `GXeMopAkjrpdxA9gYNC8ZUBqgsRicqFBshPzke8SQCbP5GM24mNjJQhxpz3pTrzdKN6VDkD2QyB2bDrSQAf2J1u` preview_rows=2 raw=4 effective=2 classes={'dex_swap_or_route': 2}
- `2025-03-04T08:17:15+00:00` `3USY6VoQBJKGWDmHBmk8DCpAWEtpaT2WLp2DHzSQttaQghehZAT8jHhhQsm9VzPsJVruTXCKjHvWGqXUCLxDwN29` preview_rows=2 raw=4 effective=2 classes={'dex_swap_or_route': 2}
- `2025-03-09T19:04:42+00:00` `3cGd6SfAU4MowyGebJGqwjbfViTR4KSVdQMJ8SM9iqJ167Bt8yztq1BGwCuURTyp8wC3D1j1Cfkc5VhpRPPtuKkq` preview_rows=2 raw=4 effective=2 classes={'dex_swap_or_route': 2}
- `2025-06-03T19:43:41+00:00` `3NWnGUqk3cdoPNEsQwsrkYzznckSh8bjA6WJBJc2KpfLzE3aaHLrWbnBif3JMDBUzE6KnRTMJyuQCnLTiNHnZGBQ` preview_rows=2 raw=4 effective=2 classes={'dex_swap_or_route': 2}
- `2025-12-20T12:13:37+00:00` `4oFUuoh2rhCCA8KiG1evNgb3pmYkyLwhYoiusvEWUozfjWiSg85L11zhwqQiKEU2EbJ1zMAGmKbJkDJUMrfKDNgz` preview_rows=3 raw=2 effective=2 classes={'mixed_transfer': 3}
- `2025-12-20T12:13:46+00:00` `4n2gWMkU9CWAFJukFCf4mdMCQJtkbhqyhkAEQ2ife3jcwRB99mPPWL9vEzNYX9FwqEExcQ874DCzh3K1imqPpnR9` preview_rows=2 raw=4 effective=2 classes={'dex_swap_or_route': 2}
- `2025-12-20T12:13:50+00:00` `27KoLKddp5wYAvkJftuKL2EMrewvvNj91H83BB64LMUakFKXd32ArEVCv6Y6nq29L4c86y6joeXGUGB7wayNVMrj` preview_rows=2 raw=4 effective=2 classes={'dex_swap_or_route': 2}
- `2025-12-26T21:07:02+00:00` `2h9rkbgcgaXAnNtHYCupfwrNzTnaJ9TUpbKzHSuB3B9kLmxUrwfwrHHL8gWMQfvPJ82LksmDEkxQhNHbd9AWj9kb` preview_rows=3 raw=2 effective=2 classes={'mixed_transfer': 3}
- `2025-12-26T21:07:12+00:00` `5qwf2gg8mKkqP79moevSaWARcMkUSKDwsXrM2TTfNAt6necy8x1VPEj9G4LvWkPKYrr1cvyuDeCnJqHJzZ9iyZtf` preview_rows=2 raw=4 effective=2 classes={'dex_swap_or_route': 2}

## Naechste Konsequenz

Jupiter 2025 kann als kontrolliert gelten. Offen bleibt nicht ein fehlender Jup.ag-Solscan-Import, sondern die uebergeordnete Datenabdeckung: Pionex-Opening/Bot-Startkapital, Bitget-Supportexport und die kleinen Dust-Residuals VTHO/BUSD.
