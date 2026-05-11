# Validierung lokaler KI-Ergebnisse: HNT 2021 und Pionex MXC/USDT

Stand: 2026-05-11

## Anlass

Die lokale KI hat zwei Readonly-Auftraege abgeschlossen:

- `remaining_2021_hnt_legacy_evidence_20260511`
- `remaining_2022_usdt_opening_bot_history_20260511`

Der Nutzer hat ergaenzt, dass der Pionex-MXC-Kontext passen kann, weil frueher MXC gehandelt wurde. Zusaetzlich wurde die offizielle Helium-Dokumentation zu Legacy-Blockchain-Daten genannt:

- `https://docs.helium.com/network-data/legacy-blockchain-data/`

## Helium Legacy Datenquelle

Die offizielle Helium-Dokumentation bestaetigt:

- Helium lief bis zur Solana-Migration auf einer eigenen L1-Blockchain.
- Die Migration zu Solana wurde am `2023-04-18` abgeschlossen.
- Fuer historische Helium-L1-Daten gibt es einen Snapshot im AWS-S3-Bucket
  `foundation-prod-etl-artifacts-v2` auf Requester-Pays-Basis.
- Zusaetzlich gibt es Torrent-Angebote:
  - Postgres Snapshot, ca. `3.1 TB`
  - Transactions & Blocks CSV Export, ca. `724 GB`

Bewertung fuer dieses Projekt:

- Das ist eine valide Primaer-/Archivquelle fuer spaetere HNT-Belegpruefungen.
- Wegen Groesse und Requester-Pays-Kosten ist es kein leichter Sofort-Fix.
- Fuer einzelne bekannte Transaktionen bleibt die vorhandene Fairspot-CSV-Spur praktisch nutzbar, muss aber bei strittigen Faellen gegen das offizielle Archiv oder eine andere belastbare Quelle gegengeprueft werden.

## Korrektur zur lokalen KI-Aussage HNT 2021

Die lokale KI schrieb sinngemaess, die Wallet `138bCXPV...` sei eine externe Ursprungs-Wallet.

Validierung gegen `ai_transfer_matches_flat` und Fairspot zeigt:

- Fuer Deposit `dd5353eedbee68d33a5c687e013b67f468dac6a769af6b56b60dfd7c1e40fa2f` existiert Match
  `ddec12db-878f-4285-b40a-16df945a301a`.
- Outbound:
  - Quelle: `helium_legacy_cointracking`
  - Zeit: `2021-08-20T08:01:13+00:00`
  - Menge: `18.318453080375246 HNT`
  - Tx: `s5UTv0W7IKEjmQllRvKtELqfAnVuBFoDmSBHyyQf0R4`
  - Payer laut Fairspot: `133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j`
  - Payee laut Fairspot: `138bCXPVfSq7yyTfoDUrVwztPmUr4WGyA7TED9Y41djmF7rjA8y`
- Inbound:
  - Quelle: `binance_api`
  - Zeit: `2021-08-20T08:04:08+00:00`
  - Menge: `18.30256046 HNT`
  - Tx: `s5UTv0W7IKEjmQllRvKtELqfAnVuBFoDmSBHyyQf0R4`

Einordnung:

- `138bCXPV...` ist in diesem Match der Binance-Payee bzw. die Binance-Deposit-Adresse, nicht die Ursprungs-Wallet.
- Die Transfer-Continuity fuer den Binance-Deposit ist technisch belegt.
- Die offene HNT-Frage bleibt die Anschaffungskosten-/Reward-Herkunft vor dem Outbound aus der eigenen Haupt-Wallet `133rkwo...`, nicht der Transfer zu Binance selbst.

## Pionex Lines 442 und 514

Validierung gegen `raw_events` bestaetigt den Nutzerhinweis:

| Line | Event | Zeit | Raw-Symbol | Raw-Side | Out | In | Fee |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 442 | `a20292c0e922503226ea223723d3863a9325cd51f5cf1bd53734dd0f387b2513` | `2022-01-19T12:45:42+00:00` | `MXC_USDT` | `BUY` | `479.99307717 USDT` | `4141.35 MXC` | `2.070675 MXC` |
| 514 | `b5422e7c322b53d701869335a500c9b7e48334f50b6e8410978e247e608e0399` | `2022-01-19T12:56:19+00:00` | `MXC_USDT` | `BUY` | `2572.15382077 USDT` | `21823.27 MXC` | `10.911635 MXC` |

Einordnung:

- Die lokale KI hat den BUY/MXC-Kontext richtig erkannt.
- Das ist kein Beleg dafuer, dass die USDT-Zeilen falsch sind: Beim Kauf von MXC gegen USDT wird USDT aus steuerlicher FIFO-Sicht veraendert/veraeussert.
- Die MXC-Lots selbst werden im aktuellen 2022-Job mit Kostenbasis weitergefuehrt und spaeteren MXC-Verkaeufen zugeordnet.
- Die offene Luecke ist die Herkunft/Cost-Basis des zuvor eingesetzten USDT-Bestands auf Pionex bzw. Binance, nicht die Existenz der MXC-Trades.

## Konsequenz

Keine automatische Korrektur aus den lokalen KI-Berichten ableiten.

Sichere naechste Aktionen:

1. `2022 USDT`: weiter als Pionex-/Binance-Opening- bzw. Bot-Historienluecke fuehren, bis ein Primaerbeleg fuer den USDT-Startbestand oder die Bot-Historie vorliegt.
2. `2021 HNT`: Transfer zu Binance ist belegt; offene Frage bleibt die Kostenbasis des HNT-Bestands vor den Legacy-Outflows. Wenn noetig, einzelne Transaktionen gegen das offizielle Helium-L1-Archiv pruefen.
3. Keine Cost Basis aus Fairspot-Oracle-USD-Werten oder Transferwerten ableiten.

## Verwendete lokale Belege

- `ai_transfer_matches_flat`
- `raw_events`
- `source_files`
- `/tmp/fairspot-helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-all.csv`
- `var/ai_db_countercheck_2026-05-11_214009.md`
- `var/ai_db_countercheck_2026-05-11_214218.md`
