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
- UI: Dashboard-Tab `Geldflüsse`, fuer die Bedienoberflaeche bewusst nur nach
  Auswahl eines konkreten Jahres
- Mindestfluss: im Tab als EUR-Schwelle einstellbar
- Jahresfilter: nutzt den vorhandenen Dashboard-Zeitraum

Die Berechnung nutzt die processing-effektiven Raw Events inklusive
Integrationsfilter, Duplicate-Drops, Review-Actions, Overrides und FX-Fallback.
Transfer-Matches werden separat als Plattform-zu-Plattform-Kante gezeigt und
nicht nochmals als externe Ein-/Auszahlung in die Darstellung eingerechnet.

Quote-Stablecoin-Legs aus Handelspaaren wie `BTCUSDT` werden mit ihrer bereits
vorliegenden Quote-Menge bewertet. Die Quote-Menge darf nicht nochmals mit dem
Basispreis multipliziert werden, weil sonst aus zum Beispiel `246 USDT` bei
einem BTC-Preis von `53.421` faelschlich ein Millionenbetrag entsteht.

Die UI laedt die Geldfluss-API nicht mehr beim initialen Dashboard-Start und
verlangt ein konkretes Jahr. Das vermeidet schwer interpretierbare Allzeit-
Sankeys und verhindert lange All-Jahre-Berechnungen beim normalen Dashboard-
Laden.

## Portfolio-Folgefix

Nach dem Stablecoin-Fix war die Portfolio-Berechnung weiterhin fachlich falsch,
weil der Portfolio-Verlauf den alten effektiven Raw-Event-Pfad genutzt hat.
Dadurch liefen Referenzquellen wie Blockpit zusammen mit Primaerquellen in die
Balance-Simulation und konnten Bestände deutlich ueberhoehen, z.B. bei SOL.

Der Portfolio-Verlauf und Portfolio-Set-Verlauf nutzen jetzt ebenfalls die
processing-effektiven Events. Damit werden Integrationsfilter, Referenzquellen-
Ausschluss und Duplicate-Drops konsistent mit Steuerlauf und Geldfluss-Ansicht
angewendet.

Live-Pruefung nach API-Neustart:

- `2025`: Endwert von vorher ca. `75.914 USD` auf `5.390,50 USD`
  korrigiert.
- `2026`: Endwert von vorher ca. `66.218 USD` auf `6.310,52 USD`
  korrigiert.

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
- Live-Probe fuer `2022` gegen lokale Daten nach Stablecoin-Bewertungsfix:
  `GET /api/v1/dashboard/net-eur-flows?year=2022&min_value_eur=25&limit=12`
