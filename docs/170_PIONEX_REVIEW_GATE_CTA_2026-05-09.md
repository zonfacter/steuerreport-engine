# Pionex Review-Gate CTA - 2026-05-09

## Ergebnis

- Das Review-Gate bleibt fuer finale Exporte korrekt gesperrt, solange `pionex-usdt-opening-balance-2021-12-28` auf `needs_evidence` steht.
- Die API unterscheidet jetzt klar zwischen finaler Freigabe und Entwurfsnutzung:
  - `final_export_allowed=false`
  - `draft_export_allowed=true`
  - `draft_label_required=true`
- Das Dashboard zeigt im Steuer-Tab einen konkreten CTA fuer den offenen Pionex/USDT-Kandidaten.

## API-Erweiterung

`GET /api/v1/review/gates` liefert je offenem Balance-Kandidaten jetzt:

- `required_evidence`: konkrete Belegliste
- `api_actions.provide_more_evidence`: Pfad zum Aktualisieren des Kandidaten
- `api_actions.approve_non_tax_inventory_normalization`: Pfad fuer explizite nicht steuerwirksame Freigabe
- `api_actions.reject_candidate`: Pfad fuer Ablehnung
- `draft_export_policy`: Regel, dass final gesperrt bleibt, Entwurf aber mit Hinweis geladen werden darf

Live-Pruefung Port `8000`:

- `issues_total=0`
- `issues_high_open=0`
- `unmatched_total=0`
- `balance_adjustment_candidates_open=1`
- Offener Kandidat: `pionex-usdt-opening-balance-2021-12-28`

## Dashboard

Im Steuer-Review-Gate-Panel wird jetzt angezeigt:

- welche Pionex-Belege fehlen
- dass Finalexport gesperrt bleibt
- ein Entwurfsreport-CTA, der Exportdateien zur Pruefung laedt, ohne die Gates freizugeben

## Tests

- `python3 -m py_compile src/tax_engine/api/review.py`
- `node --check src/tax_engine/ui/static/app.js`
- `PYTHONPATH=src pytest -q tests/unit/api/test_issue_endpoints.py::test_review_gates_block_on_balance_adjustment_candidate_needing_evidence`
