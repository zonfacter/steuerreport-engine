# Dashboard Pionex Decision Preview UI - 2026-05-09

## Ergebnis

Die read-only Entscheidungs-Vorschau fuer den offenen Pionex/USDT-Kandidaten ist jetzt im Dashboard bedienbar.

## UI-Verhalten

- Bereich: `Steuer` -> `Review Gates`.
- Die Pionex/USDT-Karte im `gateActionPanel` ist jetzt klickbar.
- Klick laedt:
  - aktuellen Kandidatenstatus,
  - Gate-Wirkung,
  - moegliche Entscheidungen,
  - Safety Notes,
  - vorbereiteten `approve_non_tax_inventory_normalization` Payload.
- Es gibt bewusst keinen Button, der die Freigabe ausfuehrt.
- Die Vorschau ist rein lesend.

## Technische Umsetzung

- HTML: `src/tax_engine/ui/static/index.html`
  - neues Panel `gateDecisionPreview`.
- JS: `src/tax_engine/ui/static/app.js`
  - `loadGateDecisionPreview(candidateId)`
  - `renderGateDecisionPreview(preview)`
  - Kandidatenkarten rufen den Preview-Endpunkt auf.

## Live-Pruefung

- `GET /api/v1/review/balance-adjustment-candidates/pionex-usdt-opening-balance-2021-12-28/decision-preview`
  - `status=success`
  - `current_status=needs_evidence`
  - Template-Entscheidung `approve_non_tax_inventory_normalization`
- `/app` enthaelt `gateDecisionPreview`.
- `/ui/static/app.js` enthaelt `loadGateDecisionPreview`.

## Test

- `node --check src/tax_engine/ui/static/app.js`
