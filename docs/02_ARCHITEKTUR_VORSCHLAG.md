# Architekturvorschlag (Frontend, Backend, Datenhaltung)

## 1. Frontend: Dashboard und interaktive Validierung
Technologie:
- React oder Vue.js
- Tabellen-Library: TanStack Table

Kernfunktionen:
- Datei-Upload: Drag-and-Drop für CSV/JSON-Exporte.
- Reconciliation-Ansicht: Gegenüberstellung von `unmatched transfers` mit manueller Paarbildung.
- Audit-Log-Ansicht: Schritt-für-Schritt-Nachvollzug, welche FIFO-Lots je Steuerzeile verbraucht wurden.
- Visualisierung: Bestandsverlauf und realisierte vs. unrealisierte PnL.

## 2. Backend: Rechenkern und Orchestrierung
Technologie:
- Python 3.11+
- FastAPI

Begründung:
- Kernlogik liegt bereits in Python (`Decimal`, Data Processing).
- FastAPI bietet gute Performance und automatische API-Dokumentation.

Laufzeitmodell:
- Rechenjobs asynchron starten.
- Fortschrittsmeldungen per WebSocket an das Frontend senden (z. B. "Asset 14/50").

## 3. API-Schnittstellen (modular)
- Hinweis: Kanonische Endpunktdefinitionen stehen in `05_API_ERWEITERUNG.md` unter `/api/v1`.
- `POST /api/v1/import/confirm`: Rohdaten entgegennehmen und validieren/persistieren.
- `GET /api/v1/review/unmatched`: Normalisierte und offene Reconciliation-Fälle bereitstellen.
- `POST /api/v1/review/reconcile`: Manuelle Overrides für Eigenüberträge speichern.
- `POST /api/v1/process/run`: FIFO-Engine und `DerivativesManager` ausführen.
- `GET /api/v1/report/export`: PDF-Export inkl. Splitting anstoßen.

## 4. Datenhaltung (Local-First)
Empfehlung:
- SQLite (Datei-basiert, Zero-Config, lokal, datenschutzfreundlich)

Vorgeschlagene Tabellen:
- `raw_events`: Unveränderte Originaldaten für Audit-Trail.
- `normalized_transactions`: Vereinheitlichtes Schema nach Ingestion.
- `tax_lots`: Von der Engine erzeugte FIFO-/Derivate-Ergebnisse.
- `settings`: Nutzerpräferenzen, Quell-Konfigurationen, verschlüsselte Secrets.

## 5. Deployment
Empfehlung:
- Docker Compose
  - Container 1: Frontend (Nginx)
  - Container 2: Backend (FastAPI)

Vorteile:
- Lokaler Betrieb mit einem Startkommando.
- SQLite-Datei bleibt lokal im Volume.
- Daten verlassen den Rechner nur bei externen Kursabfragen (falls aktiviert).

## 6. Zusammenfassung des Ziel-Stacks
- Frontend: React + Tailwind CSS + TanStack Table
- Backend: Python 3.11+ + FastAPI
- Datenbank: SQLite (SQLAlchemy oder SQLModel)
- Queue: einfache In-Memory Queue (für 30k Trades ausreichend)
- Reporting: WeasyPrint (HTML -> PDF)

## 7. Verbindliche Projektregeln (weiterhin gültig)
- Code in Englisch, Kommentare und Dokumentation in Deutsch.
- Keine Halluzinationen: unklare Fälle als `unresolved` markieren.
- Keine Hardcodings in der Fachlogik.
- `Decimal` für berechnungsrelevante Werte.
- PDF-Limit: maximal 100 Seiten pro Datei.
