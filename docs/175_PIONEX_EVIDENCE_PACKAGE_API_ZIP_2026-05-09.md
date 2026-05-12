# Pionex Evidence Package API + ZIP - 2026-05-09

## Ergebnis

Der offene Pionex/USDT Review-Blocker ist jetzt operativ ueber die API mit einem Belegpaket verbunden.

- Kandidat: `pionex-usdt-opening-balance-2021-12-28`
- Endpoint: `GET /api/v1/review/balance-adjustment-candidates/{candidate_id}/evidence-package`
- ZIP-Datei: `var/pionex_support_package_2026-05-09.zip`
- Zweck: Support-/Belegpaket fuer Pionex-Anfrage, keine steuerwirksame Buchung.

## Inhalt des Pakets

Das Paket enthaelt:

- `docs/172_PIONEX_EVIDENCE_REQUEST_PACKAGE_2026-05-09.md`
- `docs/167_PIONEX_USDT_FINAL_BLOCKER_AUDIT_2026-05-09.md`
- `var/pionex_evidence_request_package_2026-05-09.json`
- `var/pionex_usdt_known_transfers_for_support_2026-05-09.csv`
- `var/pionex_support_request_usdt_history_en_2026-05-09.txt`
- `var/pionex_support_request_usdt_history_de_2026-05-09.txt`

## API-Verhalten

Der Endpoint gibt zurueck:

- Kandidaten-ID und Kandidatenstatus
- ZIP-Pfad, Existenz und Dateigroesse
- alle Paketdateien mit Pfad, Existenz und Groesse
- englischen und deutschen Supporttext
- bekannte Pionex/TRON-USDT Transfers als strukturierte JSON-Liste

Der Review-Gate-Endpoint enthaelt zusaetzlich je Kandidat eine `evidence_package`-Aktion.

## Dashboard

Im Bereich `Steuer > Review Gates` kann die Pionex-Entscheidungsvorschau geoeffnet werden. Dort gibt es jetzt einen Button fuer das Pionex-Belegpaket. Dieser zeigt die Paketdateien, das ZIP, den Supporttext und die bekannten Transfers an.

## Validierung

Ausgefuehrt:

```bash
python3 -m py_compile src/tax_engine/api/review.py src/tax_engine/api/app.py
node --check src/tax_engine/ui/static/app.js
PYTHONPATH=src pytest -q tests/unit/api/test_issue_endpoints.py::test_pionex_balance_adjustment_candidate_evidence_package_builds_zip tests/unit/api/test_issue_endpoints.py::test_balance_adjustment_candidate_decision_preview_is_read_only tests/unit/api/test_issue_endpoints.py::test_review_gates_block_on_balance_adjustment_candidate_needing_evidence
```

Live auf Port `8000` geprueft:

- `/api/v1/review/gates`: weiter `allow_export=false`, einziger Blocker Pionex/USDT `needs_evidence`.
- `/api/v1/review/balance-adjustment-candidates/pionex-usdt-opening-balance-2021-12-28/evidence-package`: `status=success`, ZIP vorhanden, `known_transfer_count=8`.
