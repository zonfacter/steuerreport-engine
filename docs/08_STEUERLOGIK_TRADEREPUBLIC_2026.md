# Steuerlogik 2026: Trade Republic, Verlustverrechnung, Meldepflichten

## 1. Zweck
Dieses Dokument ergänzt die bestehende Architektur um steuerliche Trennung, Reporting und Prüfschritte für Trade Republic und Krypto-Fälle.

Wichtige Leitplanke:
- Inhalte werden als fachliche Regelannahmen geführt und müssen je Steuerjahr über `ruleset_version` gepflegt und fachlich freigegeben werden.

## 2. Zwei-Welten-Steuer (Trade Republic)
- Kapitalmarktprodukte (Aktien/ETF) als eigener Steuerbereich (`KAP_BUCKET`).
- Krypto-Transaktionen als separater Steuerbereich (`SO_BUCKET` / private Veräußerung bzw. Leistungen).
- Keine bucket-übergreifende Verrechnung ohne explizite Regelgrundlage.

Technische Anforderung:
- Jede Transaktion erhält `tax_bucket` und `bucket_reason_code`.
- Reporting getrennt nach Bucket, danach erst Zusammenführung auf Formularebene.

## 3. Verlustverrechnung und Topf-Logik
- Termingeschäfte (`DERIV_BUCKET`) getrennt von Spot-Veräußerungen (`SO_BUCKET`).
- Verlustverrechnung nur innerhalb zulässiger Bucket-Regeln der aktiven Regelversion.
- Regeländerungen (z. B. jahresabhängig) nur über versionierte Konfiguration.

Technische Anforderung:
- Engine-Modul `LossNettingManager` mit konfigurierbaren Matrix-Regeln:
  - `allowed_offset[from_bucket][to_bucket] = true|false`.
- Audit-Output: pro Verrechnungsvorgang Quelle, Ziel, Rechtsregel-ID.

## 4. Meldepflichten und Transparenz (DAC8/KStTG-Workflow)
- System muss "gemeldete Daten" und "selbst importierte Daten" gegenüberstellen können.
- Abweichungen werden als `compliance_mismatch` in die Issue-Inbox geschrieben.

Technische Anforderung:
- Optionales Modul `compliance_feed_import`.
- Vergleich auf Event-Ebene (Datum, Asset, Menge, Richtung, Plattform).

## 5. Trade Republic Integration
- Eigenes Importprofil `traderepublic_v1` (CSV/PDF-Fallback).
- Trade Republic als separates Depot/Wallet-Scope führen.
- Verknüpfung mit externen Wallets nur bei nachweislichem Transfer.

Technische Anforderung:
- `portfolio_scope` Pflichtfeld pro Event (`global`, `exchange`, `wallet`, `depot_id`).
- Konfigurationsschalter:
  - `fifo_mode = global`
  - `fifo_mode = scoped` (pro Depot/Börse/Wallet)

## 6. Freigrenzen-/Schwellen-Tracker
- Jahresgrenzen als regelsatzabhängige Parameter.
- Plattformübergreifende Aggregation für relevante Schwellen.

Technische Anforderung:
- Modul `ThresholdTracker` mit:
  - `threshold_key`, `tax_year`, `current_value`, `warning_levels`.
- UI-Hinweise: "nahe Schwelle" / "Schwelle überschritten".

## 7. Audit-Paket (Pflichtdokumente)
- Hauptreport (Gewinn/Verlust je Asset/Jahr).
- Loss Report (Liquidationen/Derivateverluste).
- Closing Inventory per 31.12. mit Cost Basis.
- Voller Audit-Trail (Rohdaten -> Regel -> Ergebnis).

## 8. Verbesserungen für Robustheit
- Referenz-Depot-Prüfung: Trade Republic-Daten als Kontrollstrecke mit niedriger Fehlerkomplexität.
- Parser-Konfidenzscore für PDF-Importe; bei niedriger Konfidenz Pflicht-Review.
- Stichprobenmodus für Betriebsprüfung:
  - Zufallsfall auswählen,
  - komplette Herleitung in Sekunden anzeigen.

## 9. API-Erweiterungen
- `POST /api/v1/import/traderepublic/parse`
  - Importiert und normalisiert Trade-Republic-Dateien.
- `POST /api/v1/process/run`
  - Erweiterung um `fifo_mode` (`global|scoped`) und `scope_strategy`.
- `GET /api/v1/compliance/mismatch`
  - Liefert Differenzen zwischen gemeldeten und verarbeiteten Daten.
- `GET /api/v1/audit/sample`
  - Liefert zufällige, prüfungsgeeignete Einzelnachweise.

## 10. Verifikation
- Bucket-Trennung korrekt (KAP/SO/DERIV).
- Keine unzulässige bucket-übergreifende Verrechnung.
- FIFO-Resultate in `global` vs. `scoped` deterministisch reproduzierbar.
- Trade-Republic-Referenzdaten stimmen mit offiziellen Summen überein.
