# BNB 2021 CoinMarketCap-Preisbackfill

Stand: 2026-05-11

## Anlass

Nach dem Binance-Legacy-Market-Fix blieb ein Fast-Null-Treffer:

- Steuerjahr `2021`
- Line `468`
- Asset `BNB`
- Lot-Event `binance_api/dust_convert_in/in`
- `tx_id=55615425065`

Die Ursache war nicht mehr die Binance-Market-Quote-Logik, sondern ein fehlender
BNB/USD-Kurs fuer den Dust-Convert-Tag `2021-04-28`.

## Quelle

Verwendet wurde CoinMarketCap Public Historical Data:

- Asset: `BNB`
- CoinMarketCap-ID: `1839`
- Datum: `2021-04-28`
- USD-Close: `562.63256836`
- lokaler Cache-Source-String: `coinmarketcap_public_historical:bnb`

Technischer Abruf:

```text
https://api.coinmarketcap.com/data-api/v3/cryptocurrency/historical?id=1839&convertId=2781&timeStart=1619568000&timeEnd=1619740800
```

Der bestehende Projektpfad `scripts/coinmarketcap_price_backfill_usd.py` nutzt
diesen Endpunkt bereits fuer historische USD-Preisbackfills.

## Cache-Eintrag

In `fx_cache` wurde eingetragen:

```text
rate_date=2021-04-28
base_ccy=BNB
quote_ccy=USD
rate=562.63256836
source=coinmarketcap_public_historical:bnb
source_rate_date=2021-04-28
```

## Code-Fix

Code/Test:

- `src/tax_engine/queue/service.py`
- `tests/unit/api/test_process_endpoints.py`

Neue Funktion:

- `attach_cached_usd_prices_to_binance_dust_convert_in_events()`

Regel:

- Nur `source=binance_api`
- Nur `event_type=dust_convert_in`
- Nur `side=in`
- Nur wenn noch kein Preis-/Wertanker vorhanden ist
- Nur wenn fuer das Asset ein belegter Asset/USD-Kurs im lokalen `fx_cache`
  vorhanden ist

Damit wird fuer den BNB-Dust-Zufluss kein Preis erfunden, sondern der belegte
CoinMarketCap-Backfill genutzt.

## Neu gerechnete Jobs

| Jahr | Job | Tax-Lines | Derivate-Lines | Dust-Preisanker |
| ---: | --- | ---: | ---: | ---: |
| 2021 | `37d133d7-107f-4397-a8e4-d34f6d9e9066` | 5494 | 43 | 2 |
| 2022 | `57cc9a54-8002-4e4e-ae1b-801ca2883d1f` | 6896 | 630 | 2 |
| 2023 | `45c0f99e-8731-461c-bab7-75135a620eee` | 9099 | 0 | 2 |
| 2024 | `8cd9c465-b531-43e8-a496-334695e4c2de` | 1680 | 36 | 2 |
| 2025 | `acd47dd6-6a71-4a99-9e11-f05c5dd07674` | 465 | 957 | 2 |
| 2026 | `99e1c825-b686-4626-b6f6-d10ba5a32f74` | 1 | 0 | 2 |

## Korrigierte Line

2021 Line `468`, `BNB`:

```text
qty=0.27191796
cost_basis_eur=126.7575706906227312296000000
proceeds_eur=125.771557359007051887187500
gain_loss_eur=-0.9860133316156793424125000
```

Vorher war die Kostenbasis nur fee-gross:

```text
cost_basis_eur=0.005438359999999999999999999999
```

## Audit-Ergebnis nach Fix

Aktualisierter Bericht:

- `docs/224_VALUATION_ANOMALY_AUDIT_RESULTS_2026-05-11.md`

Kennzahlen:

- `priority_1_total=0`
- `fast_null_cost_basis=0`
- `fx_available_but_low_cost_basis=0`
- `same_tx_priced_counterflow_candidates=0`
- `high_gain_ratio=15`

Damit ist die harte technische Bewertungsfehlerklasse aus diesem Audit aktuell
abgeraumt. Die verbleibenden High-Gain-Treffer sind historische Beleg-/Bestands-
Themen, keine automatisch belegte Preisanker-Luecke.

## Validierung

Gruene Pruefungen:

```bash
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

API-Coverage-Gate:

- `81.08%`

AI-Readonly-Snapshot:

- `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`
- Groesse `501055488` Bytes
- Neuester 2024-Job im Snapshot:
  `8cd9c465-b531-43e8-a496-334695e4c2de`
- Neuester 2025-Job im Snapshot:
  `acd47dd6-6a71-4a99-9e11-f05c5dd07674`

Review-/Export-Gegenprobe:

- 2024 und 2025 job-spezifisch `allow_export=true`
- `issues_open=0`
- `issues_historical_open=3`
- `unmatched_total=0`
- 2024 PDF-Seiten: all `63`, tax `61`, derivatives `3`
- 2025 PDF-Seiten: all `52`, tax `18`, derivatives `36`
- `part=2` liefert in allen PDF-Scopes korrekt `report_part_not_found`
