# Mining-/Reward-Zufluesse als Gewerbe/EUER

Stand: 2026-05-10

## Entscheidung

Mining-/Reward-nahe Zufluesse werden in diesem Projekt als gewerblicher Vorgang behandelt und muessen im Steuerreport getrennt von privaten §22-/§23-Positionen sichtbar sein.

## Umsetzung

Code:

- `src/tax_engine/rulesets/registry.py`
  - Standard-Jahresrulesets `DE-2020-v1.0` bis `DE-2026-v1.0` nutzen jetzt `mining_tax_category=BUSINESS`.
- `src/tax_engine/core/tax_domains.py`
  - Wenn das Ruleset `BUSINESS` vorgibt, werden Reward-like Zufluesse in `euer.betriebseinnahmen_mining_staking_eur` gefuehrt.
  - `anlage_so.leistungen_income_eur` bleibt fuer nicht gewerblich klassifizierte sonstige Leistungen reserviert.
- `src/tax_engine/api/reporting.py`
  - PDF-Summenseite benennt §22 jetzt als nicht gewerbliche sonstige Leistungen.
  - PDF-Summenseite weist `EÜR/Gewerbe Mining-/Reward-Einnahmen` separat aus.

## Neue Steuerlaeufe

Der Gesamtlauf `2020..2026` wurde neu gerechnet.

| Jahr | Job | §22 Leistungen EUR | EÜR/Gewerbe Mining-/Reward-Einnahmen EUR | EÜR/Gewerbe Betriebsergebnis EUR |
|---:|---|---:|---:|---:|
| 2020 | `62964cd6-7884-4aaf-869d-3766fb55e5bc` | `0` | `0` | `0` |
| 2021 | `69c34b41-29da-4a7e-9333-24fc964a566d` | `0` | `12035.69168383139309885257935` | `12035.69168383139309885257935` |
| 2022 | `984ede24-56da-4c3b-be21-ac076876a4ec` | `0` | `9761.711828427325809098030511` | `9761.711828427325809098030511` |
| 2023 | `486c2e57-4ea2-4dd3-8585-9b35b4d51e64` | `0` | `1591.789580302749903677688467` | `1591.789580302749903677688467` |
| 2024 | `202e4d5a-dfd7-42a7-bb8c-0baa36145641` | `0` | `2291.938703634026589700257328` | `2291.938703634026589700257328` |
| 2025 | `0f671359-c095-4ba2-b664-353875ff09af` | `0` | `747.7890097989682380400235705` | `747.7890097989682380400235705` |
| 2026 | `816353c8-edee-428e-ad92-a571dfb1f356` | `0` | `26.62449231868769297855626282` | `26.62449231868769297855626282` |

## Wirkung auf WISO/PDF/JSON

- JSON/CSV-Vollreport enthalten die EÜR-/Gewerbe-Summen als `tax_domain_summary`-Zeilen.
- PDF zeigt die EÜR-/Gewerbe-Summe auf der Deck-/Summenseite.
- WISO-CSV ist weiterhin ein Capital-Gains/Anlage-SO-naher Export. Gewerbliche EÜR-Werte muessen separat aus dem Vollreport/PDF/CSV uebernommen bzw. spaeter als eigener EÜR-Export gebaut werden.

## Validierung

- `python3 -m py_compile src/tax_engine/rulesets/registry.py src/tax_engine/core/tax_domains.py src/tax_engine/api/reporting.py`
- `PYTHONPATH=src python3 -m pytest -q tests/unit/rulesets/test_registry.py tests/unit/core/test_tax_domains.py tests/unit/api/test_process_endpoints.py tests/unit/api/test_api_coverage_gate.py`
- Ergebnis: `48 passed`, `1` Importlib-Deprecation-Warnung.
- `PYTHONPATH=src python3 scripts/run_current_tax_years_20260510.py`
- Ergebnis: alle Jahre `2020..2026` completed.
- `docs/190_CURRENT_TAX_RUNS_2026-05-10.md` enthaelt jetzt eigene Spalten fuer `§22 Leistungen`, `EÜR Mining/Reward` und `EÜR Ergebnis`.

## Noch offen

- Eigener EÜR-/Gewerbe-CSV-Export waere sinnvoll, damit WISO/Steuersoftware die gewerblichen Mining-/Reward-Summen nicht manuell aus PDF/JSON uebernehmen muss.
- Unresolved valuation events bleiben separat zu pruefen: 2025 `22`, 2026 `1`.
