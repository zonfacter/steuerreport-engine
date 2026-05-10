# Zero-Cost Review Dashboard Actions

Stand: 2026-05-10

## Ergebnis

Die Zero-Cost-Review ist jetzt im Dashboard bedienbar. Das betrifft insbesondere das letzte offene Issue:

- `zero_cost_tax_lots:2022:USDT:c94a113e-1423-4ac1-8a72-9a12cd1156b1`

## UI-Funktion

Im Review-Tab `Issue Inbox` gibt es je Issue jetzt Aktionsbuttons:

- `Kontext`: lädt `GET /api/v1/review/issue-context/{issue_id}` und zeigt bei Zero-Cost-Issues die betroffenen Steuerzeilen.
- `Nullbasis bestätigen`: setzt nach Browser-Bestätigung `POST /api/v1/issues/update-status` mit `status=wont_fix`.

Bei `wont_fix` werden keine Rohdaten und keine Steuerzeilen verändert. Die Cost Basis `0` bleibt im Steuerreport sichtbar; nur das Review-Issue blockiert nicht mehr.

## Code

- `src/tax_engine/ui/static/index.html`
  - neues Panel `issueContextPanel`
  - neue Aktionsspalte in der Issue-Tabelle
- `src/tax_engine/ui/static/app.js`
  - `reloadIssues`
  - `selectIssue`
  - `loadIssueContext`
  - `renderIssueContext`
  - `confirmZeroBasisIssue`

## Validierung

```bash
node --check src/tax_engine/ui/static/app.js
python3 -m py_compile src/tax_engine/api/review.py
```

Beide Prüfungen liefen erfolgreich.

