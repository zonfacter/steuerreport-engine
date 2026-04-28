# BMF 2025: Steuerregeln und Dokumentationspflichten

Quelle:
- Lokale Referenzdatei: `/workspace/steuerreport/2025-03-06-einzelfragen-kryptowerte-bmf-schreiben.pdf`
- Offizielle BMF-Veröffentlichung: BMF-Schreiben vom `06.03.2025`, GZ `IV C 1 - S 2256/00042/064/043`

Dieses Dokument ist die technische Übersetzung der BMF-2025-Leitplanken in Anforderungen an Datenmodell, Rulesets, Verarbeitung und Audit. Es ersetzt keine steuerliche Beratung; unklare Fälle werden im System als Review-Issue geführt.

## 1. Verbindliche Modellierungsregeln

### 1.1 Wallet-/Depot-Scope
- Jede Transaktion muss einem `wallet_id` oder `depot_id` zugeordnet werden.
- FIFO ist standardmäßig je `wallet/depot + asset` zu führen.
- Globale FIFO-Betrachtung ist nur als explizit gewählter Modus zulässig und muss im `config_hash` landen.
- Interne Transfers dürfen keine Veräußerung auslösen; sie müssen Anschaffungsdatum, Kostenbasis und Lot-Historie in das Ziel-Wallet weitertragen.

### 1.2 Core-Entitäten
Pflichtfelder für normalisierte Events:
- `unique_event_id`
- `source_file_id` oder API-/RPC-Source-ID
- `timestamp_utc` mit höchstmöglicher Präzision
- `wallet_id` / `depot_id`
- `platform`
- `protocol` / `is_dex`, falls relevant
- `event_type`
- `asset`, `quantity`, `side`
- Gegenasset und Gegenwert bei Trade/Swap
- `fee_asset`, `fee_quantity`, `fee_value_eur`
- `tx_hash` / `order_id` / `trade_id`
- Kursquelle und Kurszeitpunkt

Rohdaten bleiben unverändert in `raw_events` erhalten.

## 2. Ruleset-Trennung

Das Ruleset muss §23 und §22 getrennt abbilden:

| Parameter | Bedeutung |
|---|---|
| `exemption_limit_so` | Freigrenze private Veräußerungsgeschäfte (§23 EStG), ab VZ 2024: `1000.00` EUR |
| `other_services_exemption_limit` | Freigrenze sonstige Leistungen (§22 Nr. 3 EStG), Default: `256.00` EUR |
| `holding_period_months` | Standard-Haltefrist, Deutschland: `12` Monate |
| `staking_extension` | 10-Jahres-Erweiterung, Deutschland nach aktueller Projektlogik: `false` |
| `mining_tax_category` | Default-Klassifikation Mining: `INCOME` oder `BUSINESS` |

Die bisherigen Dashboard-/Compliance-Funktionen dürfen Mining-/Reward-Grenzen nicht gegen `exemption_limit_so` prüfen. Dafür ist `other_services_exemption_limit` zu verwenden.

## 3. Verbrauchsfolgeverfahren

Standard:
- FIFO je Wallet/Depot und Asset.
- Lot-Verbrauch wird dauerhaft gespeichert.
- Jede Tax-Line enthält die verbrauchten Lots als Audit-Trace.

Berechnung je verbrauchtem Lot:
- `holding_period_days`
- `cost_basis_eur`
- `proceeds_eur`
- `allocated_fees_eur`
- `gain_loss_eur`
- `tax_status`

Die Haltefrist ist taggenau zu prüfen. Steuerfreiheit entsteht nur, wenn das Veräußerungsdatum nach Ablauf der Jahresfrist liegt.

## 4. Bewertung und FX

Pflichten:
- Jeder EUR-Wert braucht `price_source`, `price_timestamp`, `fx_source` und `fx_timestamp`.
- Sekundengenaue Kurse sind bevorzugt.
- Tageskurse/Tagesendkurse sind zulässig, wenn die Bewertungsmethode je Veranlagungszeitraum konsistent ist.
- Fehlende Kurse erzeugen ein Review-Issue; automatische Schätzungen müssen klar als solche markiert werden.

Dashboard-Regel:
- `Wirtschaftlicher Wert` ist nicht gleich Portfolio-Wert.
- `Trading-Wert` ist nicht gleich Steuergewinn.
- `Portfolio-Wertentwicklung` basiert auf Beständen plus Preis-Cache und ist separat auszuweisen.

## 5. Einkünfte aus Leistungen

Als §22-nahe Zuflüsse zu behandeln und separat von §23 zu aggregieren:
- Mining
- Staking
- Lending
- Rewards
- Bounties
- Airdrops mit Gegenleistung oder sonstiger Leistungskomponente
- DeFi-Rewards

Technische Regeln:
- Zuflusswert in EUR zum Zufluss-/Claim-Zeitpunkt.
- Neuer FIFO-Lot mit Anschaffungskosten in Höhe des Zuflusswerts.
- Kalenderjahres-Summe gegen `other_services_exemption_limit` prüfen.
- Bei Gewerbehinweisen in EÜR-/Anlage-G-Domäne verschieben, nicht mit privater SO-Logik vermischen.

## 6. Private Veräußerungsgeschäfte

Für §23:
- Coin-zu-Coin-Swaps sind Veräußerung des hingegebenen Assets und Anschaffung des erhaltenen Assets.
- Verkäufe innerhalb der Haltefrist sind steuerrelevant.
- Gewinne/Verluste außerhalb der Haltefrist bleiben im Audit sichtbar, werden aber als steuerfrei markiert.
- Die §23-Freigrenze wird gegen `exemption_limit_so` geprüft.

## 7. Steuerreports externer Tools

Externe Reports, z. B. Blockpit, sind als eigene Quelle zu klassifizieren:
- `primary_import`: Rohdaten/API/Chain/CSV, die zur Berechnung verwendet werden.
- `reference_import`: Externer Steuerreport oder Kontrollreport.

`reference_import` darf nicht unbesehen denselben wirtschaftlichen Wert wie Primärdaten erzeugen. Die UI muss Quellen ein-/abschaltbar machen und Widersprüche als Review-Issue anzeigen.

## 8. Dokumentations- und Mitwirkungspflichten

Export-/Auditpflichten:
- vollständige Transaktionshistorie aller angebundenen Wallets/Accounts
- Wallet-Bestände zum 31.12.
- Kursquellen und FX-Quellen
- Gebühren je Vorgang
- Plattform, DEX/Protokoll, Wallet-Adressen
- Lot-Verbrauch je steuerlicher Zeile
- Integritäts-Hash je finalisiertem Report
- offene Lücken und manuelle Overrides mit Begründung

Für DEX/DeFi und ausländische Plattformen muss das System erhöhte Nachweispflichten markieren.

## 9. Umsetzungsfolgen für die Roadmap

Kurzfristig:
- Ruleset-Feld `other_services_exemption_limit` produktiv nutzen.
- Quellenfilter im Dashboard als steuerliches Review-Werkzeug ausbauen.
- Blockpit-Importe als `reference_import` markieren können.
- Jahresend-Snapshots in API und Export ergänzen.

Mittelfristig:
- Report-JSON-Schema mit allen BMF-Pflichtfeldern.
- Audit-Trace pro Tax-Line inklusive Kursquelle.
- Review-Issues für fehlende Wallets, Kurslücken, DEX/DeFi und widersprüchliche externe Reports.
