# JUP 2025 Transfer Chain Fix

Stand: 2026-05-10

## Befund

Das Review-Gate meldete fuer 2025 ein High-Issue:

- `JUP`: `15` steuerpflichtige Zero-Cost-Zeilen
- Erloes: `8013.92 EUR`

Die betroffenen Binance-Sells lagen am `2025-01-19T22:39:56.226000+00:00` und verkauften `JUPUSDT` unmittelbar nach einem Transfer:

- Solana Wallet Outbound: `8427.293653 JUP`
- Timestamp: `2025-01-19T22:37:40+00:00`
- Event-ID: `66c83f0938ecfa7de8bc01ae923225d74645b48ead9e26133013c9074ce8bfd9`
- Binance API Inbound: `8427.293653 JUP`
- Timestamp: `2025-01-19T22:39:17+00:00`
- Event-ID: `5d8ab9f6e38c42111eef2e1485c4f2274121426f80c682f8a7d3a63044d04457`
- TX-ID: `5c7CXkmruCzSXVvQFeqRJxyaTYg5YZ5eUkvcbnqub7i6Xra9xvWEwYwPNNP42apa8QsST8W9AHt3fA17Av2rNfge`

## Umsetzung

Der Transfer wurde als geprüfter interner Transfer persistiert:

- Match-ID: `336bc837-6bad-440e-b1fe-e35f8d434dd2`
- Methode: `manual_verified_jup_2025_chain`
- Confidence: `0.9353`
- Zeitdifferenz: `97` Sekunden
- Mengendifferenz: `0.000000`

Die Core-Transfer-Erkennung wurde nicht breit auf alle `timestamp_utc`/`side=in|out`-Events erweitert, weil dies das bestehende Review-Gate mit tausenden historischen Transfer-Kandidaten aufbläht. Diese breitere Migration bleibt ein eigenes Thema.

## Ergebnis nach Neuberechnung

Jahreslauf:

- Job 2025: `2e43521d-bbe8-4810-95bb-ee85884494e3`
- Report: `docs/190_CURRENT_TAX_RUNS_2026-05-10.md`

Review-Gate danach:

- Offene Issues: `5`
- High-Issues: `1`
- Unmatched Transfers: `0`
- `JUP 2025` ist nicht mehr im Gate.

Rest in 2025:

- `JUP` Zero-Cost-Zeilen: `5`
- Rest-Erloes: `5.245082710504106 EUR`
- Diese Restzeilen stammen aus kleinen JUP-Rewards nach dem grossen Transfer und sind nicht mehr der urspruengliche Transferkettenfehler.
