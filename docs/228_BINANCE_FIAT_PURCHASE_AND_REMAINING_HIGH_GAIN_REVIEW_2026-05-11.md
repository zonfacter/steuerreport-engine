# Binance-Fiatkauf und verbleibende High-Gain-Pruefung

Stand: 2026-05-11

## Anlass

Nach dem BNB-Dust-Preisbackfill waren die harten technischen Bewertungsfehler
bereits geschlossen:

- `fast_null_cost_basis=0`
- `fx_available_but_low_cost_basis=0`
- `same_tx_priced_counterflow_candidates=0`

Im Suchfilter `high_gain_ratio` blieb aber noch ein BNB-Fall aus einem
Fiat-Krypto-Kauf sichtbar.

## Deterministischer BNB-Fix

Betroffener Verkauf:

- 2021 Line `1`
- Asset `BNB`
- Menge `1.6`
- Kaufzeit `2021-02-06T21:18:15+00:00`
- Verkaufzeit `2021-02-06T21:23:58+00:00`

Rohbeleg im Binance-Account-Statement:

- `EUR` out: `98.1`
- `BNB` in: `1.625`
- gemeinsamer Remark / Gruppenbezug:
  `2ae01da3bd9f4522a103b8c54f0eb1c6`

Code/Test:

- `src/tax_engine/queue/service.py`
- `tests/unit/api/test_process_endpoints.py`

Neue Funktion:

- `attach_binance_fiat_purchase_value_anchors()`

Regel:

- Nur `source=binance`
- Nur `event_type=fiat_crypto_purchase`
- Nur Inflow eines Nicht-EUR-Assets
- Nur wenn ein EUR-Outflow mit demselben Binance-Account-Statement-Gruppenbezug
  existiert
- Nur wenn die Gruppe genau einen Krypto-Inflow enthaelt, damit ein EUR-Abfluss
  nicht mehrfach verteilt wird
- Setzt `value_eur` aus dem vorhandenen EUR-Gegenfluss

Es wurde kein Preis erfunden. Verwendet wurde der belegte EUR-Abfluss aus
derselben Binance-Account-Statement-Buchung.

Korrigiertes Ergebnis fuer 2021 Line `1`:

```text
cost_basis_eur=96.59076923076923076923076923
proceeds_eur=94.120963316925600000000
gain_loss_eur=-2.46980591384363076923076923
```

## Neu gerechnete Jobs

| Jahr | Job | Tax-Lines | Derivate-Lines | Fiat-Kauf-Anker |
| ---: | --- | ---: | ---: | ---: |
| 2021 | `01504a89-9b31-4e87-97f4-953f70164a9f` | 5494 | 43 | 4 |
| 2022 | `a2523d34-68b5-4983-b08f-c44dbf7816a8` | 6896 | 630 | 4 |
| 2023 | `210d8066-3bb0-4947-b45b-ceb2962e15d6` | 9099 | 0 | 4 |
| 2024 | `aeb1b44b-8b45-4dcb-8479-12c5b470c379` | 1680 | 36 | 4 |
| 2025 | `cc781fa5-1987-411a-ba69-e2653129cf88` | 465 | 957 | 4 |
| 2026 | `b59704da-a6b6-442d-b64d-b8024a74bab5` | 1 | 0 | 4 |

## Audit-Ergebnis nach Fix

Aktualisierter Bericht:

- `docs/224_VALUATION_ANOMALY_AUDIT_RESULTS_2026-05-11.md`

Kennzahlen:

- `priority_1_total=0`
- `fast_null_cost_basis=0`
- `fx_available_but_low_cost_basis=0`
- `same_tx_priced_counterflow_candidates=0`
- `high_gain_ratio=14`

## Verbleibende High-Gain-Reste

Die verbleibenden `14` Treffer sind keine automatisch belegten Preisankerfehler:

| Gruppe | Anzahl | Bewertung |
| --- | ---: | --- |
| 2022 `HNT`, Lot aus `binance_api deposit` | 5 | HNT-Deposit hat Transfer-Match aus Helium-Legacy, aber vor dem Legacy-Outflow fehlen ausreichend bewertete HNT-Lots. |
| 2021 `HNT`, Lot leer | 4 | Short-/Bestandsluecke im historischen HNT-Bestand; kein konkreter Preisanker ableitbar. |
| 2021 `HNT`, Lot aus `binance_api deposit` | 2 | Transfer-Match vorhanden, aber Herkunftslot vor dem Outflow nicht ausreichend bewertet. |
| 2022 `USDT`, Lot leer | 3 | Short-/Bestandsluecke im historischen USDT-Bestand; kein konkreter Preisanker ableitbar. |

Gepruefte HNT-Belege:

- `a12e2NxK6qfyqeZ01gc1Mj_qBCRZfAei-W1J6pWgEFE`
  - `helium_legacy_cointracking legacy_transfer out`
  - `binance_api deposit in`
  - Transfer-Match existiert bereits.
- `s5UTv0W7IKEjmQllRvKtELqfAnVuBFoDmSBHyyQf0R4`
  - `helium_legacy_cointracking legacy_transfer out`
  - `binance_api deposit in`
  - Transfer-Match existiert bereits.

Schlussfolgerung:

- Keine weitere automatische Preisanker-Korrektur aus dem aktuellen Audit.
- Naechster sinnvoller Schritt waere eine separate historische HNT-/USDT-
  Bestandslueckenanalyse, nicht ein weiterer Kurs-Backfill.

## Validierung

Ausgefuehrt nach dem Fix:

```text
python3 -m ruff check . --no-cache
python3 -m mypy src/ --cache-dir=/tmp/steuerreport_mypy_cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_process_endpoints.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit
COVERAGE_FILE=/tmp/steuerreport-api-coverage PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -p no:cacheprovider tests/unit/api --cov=src/tax_engine/api --cov-fail-under=80 -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/verify_integrity.py --all-years
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/build_ai_readonly_db_snapshot.py
systemctl restart steuerreport-api.service
curl -fsS http://127.0.0.1:8000/api/v1/health
```

Ergebnis:

- `ruff` komplett gruen.
- `mypy` gruen.
- `tests/unit/api/test_process_endpoints.py` gruen.
- `tests/unit` gruen.
- API-Coverage-Gate `81.08%`, gruen.
- `verify_integrity --all-years` gruen.
- AI-Readonly-Snapshot neu gebaut:
  `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`,
  Groesse `523128832` Bytes.
- API-Service Port `8000` neu gestartet, `/api/v1/health` gruen.
- `/app` rendert erfolgreich.

Review-/Export-Gegenprobe:

- 2024 Job `aeb1b44b-8b45-4dcb-8479-12c5b470c379`:
  `allow_export=true`, `issues_open=0`, `issues_historical_open=3`,
  `unmatched_total=0`.
- 2025 Job `cc781fa5-1987-411a-ba69-e2653129cf88`:
  `allow_export=true`, `issues_open=0`, `issues_historical_open=3`,
  `unmatched_total=0`.
- 2024 PDF-Seiten: all `63`, tax `61`, derivatives `3`.
- 2025 PDF-Seiten: all `52`, tax `18`, derivatives `36`.
- `part=2` liefert in allen PDF-Scopes den Standard-Response-Code
  `report_part_not_found`.
