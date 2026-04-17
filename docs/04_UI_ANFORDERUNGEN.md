# UI-Anforderungen (Review-First Oberfläche)

## 1. Ziel der Oberfläche
Die Oberfläche dient primär der fachlichen Validierung, Nachvollziehbarkeit und Korrektur. Sie ist nicht nur ein Reporting-Dashboard.

## 2. Kernmodule

### 2.1 Import Hub
- Unterstützung für `CSV`, `XLSX`, `JSON` sowie API-basierte Importe.
- Drag-and-Drop Upload mit Dateivorschau.
- Auto-Erkennung der Quelle über Header-Fingerprint, Spaltenmuster und Datumsformate.
- Import-Profile je Quelle und Schema-Version.

### 2.2 Reconciliation Workspace
- Ansicht für `unmatched transfers` mit Paarbildung per UI.
- Anzeige von Konfidenz-Score und Begründung (Zeitdifferenz, Mengenabweichung, Fee-Toleranz).
- Aktionen: Bestätigen, Ablehnen, manuell verknüpfen.

### 2.3 Interactive Ledger
- Tabellenansicht für große Datenmengen (Virtual Windowing, serverseitige Pagination/Filter).
- Aktionen auf Zeilenebene:
  - Merge von Transaktionen (reversibel).
  - Split von Transaktionen (reversibel).
  - Ignore/Unignore (z. B. Spam-Token), mit Pflichtbegründung.
  - Kommentar hinzufügen.

### 2.4 Issue Inbox
- Zentrale Liste offener Probleme:
  - fehlende Kurse,
  - Short-Sell-Unterdeckung,
  - Zeitzonenkonflikte,
  - nicht auflösbare Transfers,
  - Parser-/Schema-Fehler.
- Statusworkflow: `open`, `in_review`, `resolved`, `won_t_fix`.

### 2.5 Audit-Ansicht
- Drilldown je Steuerzeile mit vollständiger Herleitung:
  - verbrauchte Lots,
  - FX-Quelle,
  - Gebühren,
  - Haltedauer,
  - Regelversion.
- Zeitstrahlansicht für Änderungen durch Overrides.

## 3. Zeitzonen- und Zeitkorrektur-UX
- Interne Verarbeitung in UTC.
- UI zeigt Originalzeit + interpretierte Zeit + korrigierte Zeit.
- Korrekturassistent für `UTC`, `CET`, `CEST` mit Vorher/Nachher-Vergleich.
- Jede Korrektur als auditierbarer Override mit Begründung.

## 4. Kommentar- und Kollaborationslogik
- Kommentare auf Ebene von Event, Match, Issue, Run und Report.
- Kommentarverlauf mit Zeitstempel und Autor.
- Verknüpfung von Kommentar mit konkreter Aktion (z. B. Merge, Ignore, Zeitkorrektur).

## 5. Import von Blockpit/Blockbit und Alternativen
- Priorität 1: strukturierte Datenquellen (CSV/JSON/API).
- PDF-Import (z. B. 1200+ Seiten) nur als Fallback mit niedriger Konfidenz.
- Bei PDF-Import zwingende manuelle Review-Pflicht für kritische Felder.
- Alternative Datenwege: direkte Exchange-Exporte, Wallet-Exports, Chain-Daten, Anbieter-API (falls verfügbar).

## 6. Nicht-funktionale UI-Anforderungen
- Performance: flüssige Bedienung bei 30k+ Zeilen.
- Stabilität: keine blockierende UI bei laufender Berechnung.
- Transparenz: jeder Automatik-Entscheid ist erklärbar.
- Nachvollziehbarkeit: jede Nutzeraktion ist revisionsfähig.

## 7. Depot-Separation UI
- Silo-Dashboard mit Bestand, Cost Basis und unrealisierter PnL je Depot.
- Anzeige, ob Depot als `hard_silo` markiert ist.
- Transfer-Bestätigungsdialog für steuerneutrale Eigenüberträge.
- Einsicht in Transfer-Kette und übernommene Anschaffungsdaten.
