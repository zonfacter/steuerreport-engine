# Helium-Steuerkonzept (HNT, IOT, MOBILE) für DE-Workflow

## 1. Zweck und Geltungsbereich
Dieses Dokument definiert die technische Umsetzung für Helium-Transaktionen im Steuerreport-System.

Wichtige Leitplanke:
- Das System trifft keine endgültige Rechtsentscheidung "privat vs. gewerblich" autonom.
- Es liefert eine regelbasierte Einstufung mit Konfidenz und erzwingt Review bei Grenzfällen.

## 2. Fachlogik: Zufluss, Anschaffung, Veräußerung
- Rewards (HNT/IOT/MOBILE) werden zum Zuflusszeitpunkt in EUR bewertet.
- Der Zuflusswert wird doppelt geführt:
  - als Einnahme im Zuflusszeitpunkt,
  - als Anschaffungskostenbasis für spätere Veräußerung.
- Swap (z. B. IOT -> HNT) wird als Veräußerung von Asset A und Anschaffung von Asset B behandelt.

## 2.1 Event-Typen für Staking/Migration
- `STAKING_LOCK`: Sperrung/Locking, grundsätzlich kein Steuerevent.
- `STAKING_REWARD_CLAIM`: steuerlich relevanter Zufluss bei Claim/Verfügbarkeit.
- `VIRTUAL_ACCRUAL`: regelbasierte Jahresendabgrenzung bei wirtschaftlicher Verfügbarkeit ohne Claim.

## 3. Einstufung privat/gewerblich (regelbasiert, review-pflichtig)
- Rule-Engine mit versionierten Regeln (`ruleset_version`) für Steuerjahr und Jurisdiktion.
- Eingangsindikatoren (konfigurierbar):
  - Anzahl aktiver Hotspots,
  - Betriebsaufwand/Infrastruktur,
  - Regelmäßigkeit/Volumen,
  - dokumentierte Gewinnerzielungsabsicht.
- Output: `classification_candidate` + `confidence` + `reason_codes`.
- Bei `confidence < threshold`: Issue erzeugen und manuelle Entscheidung erzwingen.

## 4. Bewertungslogik bei illiquiden Token
- Preisquellen-Reihenfolge konfigurierbar (z. B. Primärfeed, Sekundärfeed, Fallback).
- Bei illiquiden Assets:
  - Tageskurs/Intervallkurs gemäß Regelprofil,
  - Kennzeichnung `valuation_method` und `price_confidence`.
- Fehlende Preise werden nicht geraten:
  - Event als `unresolved_price_gap` markieren,
  - Aufnahme in Issue-Inbox.

## 5. Data Credits (DC)
- DC werden standardmäßig als nicht-handelbares Verbrauchsobjekt geführt.
- Buchungslogik über Regelprofil steuerbar:
  - als Gebühr/Verbrauch,
  - ohne Aufnahme als handelbares Portfolio-Asset.
- Jede DC-Behandlung muss im Audit-Trail mit Regel-ID dokumentiert sein.

## 6. Elster-/Formular-Mapping (technische Sicht)
- Keine harten Zeilennummern im Code.
- Stattdessen: versionierte Mapping-Profile pro Steuerjahr (`elster_mapping_version`).
- Zielstruktur:
  - Bereich Veräußerungsgeschäfte,
  - Bereich Leistungen (Rewards),
  - Summenfelder für Anlage-Übertrag.
- PDF-Export bleibt auf max. 100 Seiten pro Datei gesplittet.

## 7. UI-Anforderungen für Helium-Fälle
- Kommentarzwang bei manueller Klassifikationsänderung.
- Merge/Split/Ignore für problematische Reward- und Dust-Einträge.
- Sichtbare Begründung je Entscheidung (Regelcode, Preisquelle, Zeitkorrektur).
- Zeitkorrektur-Dialog für UTC/CET/CEST inkl. Vorher/Nachher.

## 8. API-Erweiterungen für Helium
- `POST /api/v1/helium/rewards/revalue`
  - Revaluierung von Rewards mit ausgewähltem Preisprofil.
- `GET /api/v1/helium/classification/status`
  - Kandidatenstatus privat/gewerblich inkl. Konfidenz und Reason Codes.
- `POST /api/v1/helium/classification/override`
  - Manuelle Festlegung mit Pflichtkommentar und Audit-Event.
- `GET /api/v1/compliance/elster/preview`
  - Vorschau der Summen je Formularbereich und Mapping-Version.

## 9. Datenmodell-Erweiterungen
- `helium_reward_facts`
  - `event_id`, `token`, `claim_timestamp_utc`, `qty`, `eur_value`, `valuation_method`, `price_source`, `price_confidence`.
- `classification_decisions`
  - `run_id`, `candidate`, `confidence`, `reason_codes`, `final_decision`, `decision_comment`.
- `form_mappings`
  - `tax_year`, `elster_mapping_version`, `field_key`, `mapping_rule`.

## 10. Verifikation (Pflichttests)
- Reward-Zufluss korrekt als Einnahme + Cost Basis.
- Swap-Logik (Veräußerung/Kauf) konsistent mit FIFO/Derivate-Trennung.
- Illiquid-Preisfälle erzeugen `unresolved` statt stiller Schätzung.
- Klassifikations-Overrides sind vollständig auditierbar.
- Elster-Mapping reproduzierbar per `run_id`, `config_hash`, `ruleset_version`, `elster_mapping_version`.
- `STAKING_LOCK` löst keine fiktive Veräußerung aus.
- `VIRTUAL_ACCRUAL` wird nur bei aktivem Regelprofil erzeugt und ist mit `confidence` + `reason_code` dokumentiert.

## 11. Verbesserungen gegenüber Basisplanung
- Event-Sourcing strikt umgesetzt: `raw_events` unveränderlich, Eingriffe nur als Overrides.
- Reproduzierbarkeit erweitert: zusätzlich `elster_mapping_version` und `valuation_profile_version` speichern.
- Sensible Regeln (z. B. `VIRTUAL_ACCRUAL`) sind konfigurierbar und review-pflichtig.
- OptimizationEngine-Anbindung:
  - Hinweise auf Haltefristnähe,
  - potenzielle Verlustrealisierung,
  - Kennzeichnung rechtlicher Unsicherheit bei Empfehlung.
