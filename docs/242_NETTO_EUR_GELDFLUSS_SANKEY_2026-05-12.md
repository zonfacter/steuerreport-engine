# Netto-EUR-Geldfluss-Sankey

Stand: 2026-05-12

## Zweck

Das Dashboard hat eine neue Seite `Geldflüsse`. Sie visualisiert Geldflüsse als
Sankey-aehnliche Nettoansicht in EUR. Ziel ist nicht Handelsvolumen, sondern ein
operativer Blick auf saldierte Bewegungen:

- gematchte Transfers zwischen Plattformen
- externe Zu- und Abfluesse
- Netto-Asset-Aufbau oder Netto-Asset-Abbau je Plattform und Asset
- erkannte unbelegte Stablecoin-Startbestaende aus negativen laufenden
  Stablecoin-Salden

## Technische Umsetzung

- API: `GET /api/v1/dashboard/net-eur-flows`
- UI: Dashboard-Tab `Geldflüsse`
- Mindestfluss: im Tab als EUR-Schwelle einstellbar
- Jahresfilter: nutzt den vorhandenen Dashboard-Zeitraum

Die Berechnung nutzt die processing-effektiven Raw Events inklusive
Integrationsfilter, Duplicate-Drops, Review-Actions, Overrides und FX-Fallback.
Transfer-Matches werden separat als Plattform-zu-Plattform-Kante gezeigt und
nicht nochmals als externe Ein-/Auszahlung in die Darstellung eingerechnet.

## Einordnung

Die Ansicht ersetzt keine steuerliche Entscheidung und erzeugt keine
Anschaffungskosten. Besonders der Knoten `Unbelegter Startbestand` ist ein
technisches Warnsignal: Er zeigt, dass innerhalb des gewaehlten Zeitraums ein
Stablecoin-Saldo rechnerisch negativ wird. Bei Jahresfilterung kann das auch
einen aus Vorjahren mitgebrachten Anfangsbestand anzeigen.

## Validierung

- `python3 -m py_compile src/tax_engine/api/dashboard.py`
- `node --check src/tax_engine/ui/static/app.js`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_dashboard_net_eur_flows.py`
- Live-Probe fuer `2022` gegen lokale Daten:
  `GET /api/v1/dashboard/net-eur-flows?year=2022&min_value_eur=25&limit=12`

