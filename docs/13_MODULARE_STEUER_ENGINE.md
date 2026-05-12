# Modulare Steuer-Engine (Core vs. Ruleset)

## 1. Zielsetzung
Die Steuerlogik wird als pluggable System umgesetzt, nicht als statischer Codepfad.

Ziel:
- Gesetzesänderungen über Rulesets einspielen, ohne Core-Infrastruktur zu ändern.
- Side-by-Side-Berechnungen für Vergleichsszenarien ermöglichen.

## 2. Architekturmodell
### 2.1 Core Engine (deterministisch)
Verantwortlich für:
- FIFO-Zuordnung,
- Bestandsführung,
- FX-Umrechnung,
- Datenvalidierung,
- Audit-Trail.

### 2.2 Ruleset Provider (variabel)
Verantwortlich für:
- steuerliche Einordnung,
- Grenzwerte/Freigrenzen,
- Haltedauerregeln,
- Spezialregeln (z. B. Staking/Mining-Kategorien).

## 3. Datenmodell `TaxRuleset`
Jedes Ruleset ist versioniert (JSON + signierte Metadaten oder Python-Strategieklasse mit serialisiertem Manifest).

Pflichtfelder:
- `ruleset_id` (String)
- `ruleset_version` (String)
- `jurisdiction` (String, ISO-Ländercode)
- `valid_from` / `valid_to` (ISO-Date)
- `exemption_limit_so` (Decimal, §23-Freigrenze private Veräußerungsgeschäfte)
- `other_services_exemption_limit` (Decimal, §22-Nr.-3-Freigrenze für sonstige Leistungen wie Mining/Staking/Rewards)
- `holding_period_months` (Integer)
- `staking_extension` (Boolean)
- `mining_tax_category` (Enum: `INCOME` | `BUSINESS`)
- `status` (Enum: `draft` | `approved` | `deprecated`)

## 4. Strategy Pattern und RuleContext
- Core ruft pro Event einen `RuleContext` auf.
- Ruleset-Implementierung entscheidet den Steuerstatus.

```python
class TaxStrategy(ABC):
    @abstractmethod
    def calculate_tax_status(self, acquisition_date, sell_date, amount, context):
        raise NotImplementedError
```

## 5. Versionierungsanforderungen
- Unveränderlichkeit: Finalisierte Reports verweisen auf immutable Ruleset-Artefakte.
- Side-by-Side: Gleiches Jahr muss mit mehreren Rulesets berechenbar sein.
- Audit: Jede Exportzeile trägt `ruleset_id` und `ruleset_version`.

## 6. UI-Integration
- Regeln-Verwaltung mit Anzeige von Version, Status und Gültigkeitszeitraum.
- Warnung bei Transaktionen außerhalb bestätigter Ruleset-Abdeckung.
- Vergleichsansicht für "Was-wäre-wenn" zwischen zwei Rulesets.

## 7. API-Anforderungen
- `GET /api/v1/rulesets`
- `POST /api/v1/rulesets`
- `GET /api/v1/rulesets/{ruleset_id}/{ruleset_version}`
- `POST /api/v1/process/run` mit expliziter Auswahl von `ruleset_id` und `ruleset_version`
- `POST /api/v1/process/compare-rulesets`

## 8. Governance
- Ruleset-Freigabe per 4-Augen-Prinzip (`approved_by`, `approved_at`).
- Jede Änderung erzeugt neue Version, niemals in-place edit bei freigegebenen Versionen.
- Änderungsprotokoll (`ruleset_changelog`) ist verpflichtend.

## 9. Verifikation
- Determinismus bleibt bei identischem Ruleset garantiert.
- Unterschiedliche Rulesets erzeugen reproduzierbar unterschiedliche Ergebnisse.
- Export enthält vollständige Ruleset-Referenzen pro Zeile.
