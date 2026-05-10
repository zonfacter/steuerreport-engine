# Autonomous Completion / GitHub Sync Status 2026-05-10

## Ergebnis

- GitHub-Abgleich: GitHub Connector zeigt keine offenen Issues und einen offenen PR `#3` fuer Branch `codex/next-roadmap-work`.
- Lokaler Branch: `codex/next-roadmap-work`, Remote `origin/codex/next-roadmap-work`.
- Engineering-Gates lokal gruen:
  - `python3 -m ruff check . --no-cache`
  - `python3 -m mypy src/ --cache-dir=/tmp/steuerreport_mypy_cache`
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit`
  - `COVERAGE_FILE=/tmp/steuerreport-api-coverage PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -p no:cacheprovider tests/unit/api --cov=src/tax_engine/api --cov-fail-under=80 -q`
  - `node --check src/tax_engine/ui/static/app.js`
  - `python3 scripts/verify_integrity.py --all-years`
- API-Coverage: `81.08%`, Gate `>=80%` erreicht.
- Ruleset-Integrity:
  - `DE-2024.json` OK
  - `DE-2025.json` OK
  - `DE-2026.json` OK

## Fixes in diesem Abgleich

- Ruff-kompatible Script-Bootstrap-Konfiguration fuer `scripts/*.py` (`E402` per-file ignore), weil die Audit-/Import-Skripte projektlokal `src` in `sys.path` aufnehmen.
- `api.app` Re-Exports fuer Balance-Adjustment-Request-Klassen wiederhergestellt, damit bestehende API-Tests/Importe kompatibel bleiben.
- Mypy-Fixes fuer PDF-Reporting, Fingerprint-Serialisierung, Solscan-Mengen, Dashboard-Datumsfilter und Review-AI-Action-Bodies.
- Jahresanalyse-Test korrigiert: Token-Alias `FAKEUSDC...` wird korrekt unter `USDC` aggregiert und nicht mehr separat erwartet.
- Kleine Ruff-Fixes in Audit-Skripten: unbenutzte Variablen, eindeutiger Variablenname, `zip(..., strict=True)`.

## Aktueller Daten-Gate-Stand

Readonly-DB:

- `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`

Neueste abgeschlossene Jobs je Jahr:

| Jahr | Job |
| --- | --- |
| 2020 | `287cc41c-9055-42ca-8b5a-9d5578e07dc6` |
| 2021 | `5ab77c28-68f9-42f2-8a97-47f1d4f57f13` |
| 2022 | `c4d8719c-4041-443a-b182-d9f6ccf06407` |
| 2023 | `bf4e3974-5e7e-4bfe-9e15-6992ad4812bb` |
| 2024 | `0b0d5264-b38f-4726-81eb-bd54191a0064` |
| 2025 | `f4342b4b-a502-47cf-a5dc-255eda49d94c` |
| 2026 | `924d49e7-b215-480f-ae35-9dddc8d99648` |

Offene Zero-Cost-Zeilen in der aktuellen Readonly-DB:

| Jahr | Asset | Zeilen | Erloes EUR |
| --- | --- | ---: | ---: |
| 2021 | BNB | 2 | 0.003129095 |
| 2021 | HNT | 8 | 1790.05924360799 |
| 2021 | UNKNOWN | 3 | 11.506435555656 |
| 2022 | HNT | 5 | 2300.1340507291 |
| 2022 | USDT | 3 | 1383.8766622952 |
| 2024 | USDC | 1 | 0.00000189357847101376 |

Wichtig: Fuer den neuesten 2025-Job wurden in `ai_open_zero_cost_tax_lines` keine offenen Zero-Cost-Zeilen gefunden. Aeltere AI-Readonly-Reports, die `2025` als kritisch markieren, referenzieren teilweise denselben Job, bewerten aber Quellenabdeckung und Blockchain-Plausibilisierung als Risiko. Diese Befunde bleiben als Evidence-Gaps erhalten, sind aber kein aktuelles Zero-Cost-Export-Gate.

## GitHub-Sync-Hinweis

Nicht automatisch nach GitHub schieben:

- Rohdaten im Repo-Root (`*.csv`, `*.xlsx`) enthalten steuerliche Primaerdaten und bleiben lokal.
- `var/` enthaelt lokale Reports, Queue-Status und Datenbank-nahe Arbeitsartefakte und bleibt lokal.

Fuer GitHub geeignet:

- Code unter `src/`
- Tests unter `tests/`
- Projektdokumentation unter `docs/`
- Audit-/Import-Skripte unter `scripts/`
- Konfigurationen und README/pyproject

## Noch nicht fachlich final

Diese Punkte duerfen nicht als steuerlich final abgeschlossen bezeichnet werden:

- Altjahr-Zero-Cost-Reste 2021/2022.
- 2025 Quellenabdeckung muss weiter gegen Primaerbelege plausibilisiert werden, insbesondere Binance/Bitget/Blockpit-Herkunft und Jahresendbestaende.
- Die laufende `steuerreport-ai-readonly-queue.service` arbeitet noch weitere Readonly-Aufgaben ab.
