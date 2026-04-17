# Etappe 1 Masterplan: Ingestion & Smart Cleaning

## 1. Zielbild
Diese Etappe bildet die robuste Eingangsschicht für CEX-, DEX- und Spezialfälle (Helium/Jupiter/Bot-Trading) und erzeugt auditierbare, steuerlich klassifizierte Normalformen.

## 2. Universal Reward & Staking Engine
Plattform-agnostische Eventtypen:
- `INCOME_STAKING`
- `INCOME_MINING`
- `LIQUID_STAKING_SWAP`
- `FEE_DISPOSAL`
- `LOCK_EVENT`
- `UNLOCK_EVENT`
- `LOSS_ADJUSTMENT`
- `INVENTORY_ADJUSTMENT`

Regel:
- Jede Klassifikation ist regelversionsgebunden (`ruleset_version`) und mit `confidence` + `reason_codes` zu speichern.

## 2.1 Modulare Ruleset-Entkopplung
- Core-Engine (deterministisch) und Ruleset-Provider (variabel) sind strikt getrennt.
- Jede Klassifikation/Bewertung läuft über `ruleset_id` + `ruleset_version`.
- Side-by-Side-Berechnungen für identische Daten mit mehreren Rulesets sind unterstützt.

## 3. Helium-Migration-Bridge (L1 -> Solana, veHNT)
### 3.1 Lock-&-Sync Handler
- Locking von HNT wird als Verwahr-/Sperrereignis modelliert, nicht als Veräußerung.
- Einführung eines logischen `locked_depot` für gesperrte Bestände.
- Bei Unlock/Remap wird der ursprüngliche Anschaffungszeitpunkt fortgeführt.

### 3.2 veHNT-Sonderfall
- veHNT als nicht-handelbares Governance-Recht mit internem Buchwertmodell.
- Kein fiktiver Marktwertansatz bei reinem Lock/Unlock-Mechanismus.

### 3.3 Rewards während Sperrzeit
- Claims (IOT/MOBILE/HNT) als Zuflussereignisse mit EUR-Bewertung zum Zuflusszeitpunkt.
- Bei wirtschaftlicher Verfügbarkeit ohne Claim: Jahresendprüfung und regelbasierte Abgrenzung.

## 4. Binance Bot-Handling und BNB-Fee-Logik
- Deduplizierung und Batch-Normalisierung für hochfrequente Bot-Ereignisse.
- Gebühren in BNB als separater Veräußerungsvorgang (`FEE_DISPOSAL`) erfassen.
- Gebührenwirkung:
  - BNB-Bestand reduzieren,
  - Gewinn/Verlust aus BNB-Veräußerung berechnen,
  - Gebührenanteil in Kosten-/Erlöslogik der Haupttransaktion berücksichtigen.

## 5. Differenz-Management (Plausibilitäts-Tresor)
### 5.1 Auto-Discovery
- Soll-/Ist-Abgleich: berechneter Bestand vs. externer Bestandsnachweis.

### 5.2 Korrekturpfade
- Fehlmenge: `LOSS_ADJUSTMENT` (Ausbuchung mit Begründung).
- Überschuss: `INVENTORY_ADJUSTMENT` (sichere Behandlung per Regelprofil).

### 5.3 Pflichtfelder
- `adjustment_reason`
- `evidence_source`
- `approved_by`
- `approved_at_utc`

## 6. Audit-Trace-Dokument (Pflicht)
Das System erzeugt ein erklärendes Begleitdokument mit:
- Mapping-Historie für Migrations-/Lock-Fälle,
- Adjustment-Log mit Differenzhöhe und Begründung,
- Fee-Logik-Nachweis (z. B. BNB als separate Veräußerung),
- Regel- und Konfigurationsbezug (`run_id`, `config_hash`, `ruleset_version`).
- Integritätsbezug (`report_integrity_id`, `data_hash`, `ruleset_hash`, `config_hash`).

## 6.1 Data- und Calculation-Fingerprints
- Pro Importevent wird eine `unique_event_id` (Input-Fingerprint) gebildet.
- Pro Run wird eine `report_integrity_id` (Calculation-Fingerprint) gebildet.
- Finalisierte Reports werden bei relevanten Änderungen als `DIRTY`/`OUTDATED` markiert.

## 7. Gewerbe-Ampel (Hinweismodul, keine automatische Rechtsentscheidung)
- Ampelstatus: `green`, `yellow`, `red` basierend auf konfigurierbaren Indikatoren.
- Indikatoren:
  - Umfang/Regelmäßigkeit Mining,
  - Trading-Volumen/Bot-Intensität,
  - Infrastruktur-/Organisationsgrad.
- Ergebnis:
  - Hinweis auf möglichen Prüfbedarf `Anlage G/EÜR`.
  - Keine autonome Endentscheidung, nur Fachhinweis + Review-Pflicht.

## 8. Datenmodell-Erweiterungen
### Tabelle `reward_details`
- `event_id`
- `tax_category`
- `eur_value_at_ingress`
- `is_reinvest`
- `valuation_profile_version`

### Tabelle `adjustments`
- `id`, `event_ref`, `asset`, `qty_delta`, `valuation_eur`, `adjustment_type`
- `reason`, `evidence_source`, `approved_by`, `approved_at_utc`

### Tabelle `classification_audit`
- `event_id`, `classifier_version`, `confidence`, `reason_codes`, `final_label`

## 9. API-Erweiterungen
- `POST /api/v1/ingest/classify`
  - Klassifiziert normalisierte Events plattform-agnostisch.
- `POST /api/v1/helium/migration/bridge`
  - Verknüpft Legacy- und Solana-Ereignisse in einer Lock-/Unlock-Kette.
- `POST /api/v1/reconcile/adjustments`
  - Legt Differenzbuchungen mit Pflichtbegründung an.
- `GET /api/v1/audit/trace-document/{run_id}`
  - Liefert das vollständige Audit-Trace-Dokument.
- `GET /api/v1/compliance/business-indicator/{run_id}`
  - Liefert Gewerbe-Ampel mit Begründungsparametern.
- `GET /api/v1/integrity/report/{run_id}`
  - Liefert Integritätsmetadaten und Report-Fingerprint.

## 10. Verifikation (Abnahme)
- Helium-Migration löst keine fiktiven Veräußerungen aus.
- Haltedauer bleibt über Lock/Unlock und Depotwechsel korrekt erhalten.
- BNB-Fee-Verkäufe werden vollständig erkannt und bilanziert.
- Jede Differenzbuchung ist genehmigt und auditierbar.
- Klassifizierungen sind reproduzierbar bei identischer Regelversion.

## 11. Gewerbe-Ampel Kriterien (konkret)
### 11.1 Ampelzustände
- `green` (private Vermögensverwaltung):
  - Mining/Staking-Zuflüsse im Jahr unter konfigurierter Grenze (Default-Hinweiswert 256 EUR).
  - Überwiegend längere Haltedauern.
  - Keine Hinweise auf professionellen Marktauftritt.
- `yellow` (Beobachtungsphase):
  - Grenze bei Mining/Staking überschritten oder hohe Transaktionsfrequenz.
  - Bot-Nutzung erkennbar, aber ohne eindeutige gewerbliche Struktur.
- `red` (Gewerbeverdacht):
  - Nachhaltige, intensive Aktivität mit Gewinnorientierung und professionellen Merkmalen.
  - Deutliche Hochfrequenz-/Umschlagskennzahlen.

### 11.2 Berechnungsmetriken
- `mining_income_eur_ytd`: Summe aller relevanten Reward-Zuflüsse in EUR.
- `trades_per_year`: Anzahl steuerrelevanter Trades im Kalenderjahr.
- `turnover_velocity`: Verhältnis kurzfristiger Käufe/Verkäufe im definierten Zeitfenster.
- `holding_ratio_long`: Anteil Veräußerungen mit Haltedauer > 365 Tage.

### 11.3 Ausgabelogik
- Ergebnis enthält:
  - `classification_state` (`green|yellow|red`)
  - `confidence`
  - `reason_codes`
  - `advisory_text`
- Beispiel `advisory_text`:
  - "Achtung: Aufgrund hoher Bot-Aktivität und Umschlagsgeschwindigkeit wird steuerliche Prüfung bzgl. möglicher gewerblicher Einstufung empfohlen."

### 11.4 Governance
- Keine automatische Rechtsentscheidung.
- Jede rote Einstufung erzeugt ein Pflicht-Issue mit Review-Hinweis für Steuerberater.
