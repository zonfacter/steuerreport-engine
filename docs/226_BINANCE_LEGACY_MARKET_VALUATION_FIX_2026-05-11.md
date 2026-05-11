# Binance-Legacy-Market-Bewertung

Stand: 2026-05-11

## Anlass

Das Bewertungsanomalie-Audit nach dem Bitget-Fix zeigte weiterhin
Fast-Null-Kostenbasen in historischen Binance-Legacy-Trades, vor allem `DOGE`,
`HNT` und `ETH` aus 2021.

Ursache war ein Import-/Processing-Mismatch:

- Normalisierte Binance-Legacy-Trades tragen `raw_row.Market`, `raw_row.Total`
  und `price`.
- `price` ist bei Maerkten wie `HNTBTC`, `DOGEBTC` oder `HOTETH` die
  Quote-Waehrung je Base-Asset, nicht EUR.
- Der Core-Prozessor behandelte das generische Feld `price` bisher als
  direkten EUR-Stueckpreis.

Dadurch wurden Crypto/Crypto-Trades nur mit Fast-Null-Werten bewertet, obwohl
der belegte Gegenwert im Rohdatensatz vorhanden war.

## Deterministischer Fix

Code:

- `src/tax_engine/queue/service.py`
- `tests/unit/api/test_process_endpoints.py`

Neue Laufzeit-Funktion:

- `attach_binance_market_quote_value_anchors()`

Regel:

- Nur `source=binance`, `event_type=trade`, `side in/out`.
- Nur wenn `raw_row.Market` und `raw_row.Total` vorhanden sind.
- Der Markt wird in Base/Quote zerlegt, zum Beispiel `HNTBTC` -> `HNT`/`BTC`.
- `raw_row.Total` wird als belegter Gesamtwert in der Quote-Waehrung verwendet.
- `EUR`-Quotes setzen `value_eur`.
- USD-Stable-Quotes setzen `value_usd_sum`.
- Crypto-Quotes wie `BTC`, `ETH`, `BNB` setzen `value_usd_sum` ueber vorhandene
  FX-Cache-Kurse der Quote-Waehrung.
- Das generische Feld `price` wird fuer diese abgeleiteten Laufzeit-Events
  neutralisiert und als `binance_market_quote_unit_price` erhalten, damit es
  nicht weiter als EUR-Stueckpreis gewinnt.

Es wurden keine Preise erfunden. Wenn ein notwendiger Quote/USD-Kurs fehlt,
wird kein Anker gesetzt.

Zusaetzlich bleibt aktiv:

- `drop_malformed_binance_market_summary_events()`
- Diese Regel entfernt 403 fehlerhafte Binance-Summary-Zeilen mit leerem Asset,
  deren korrekte normalisierte Legs bereits vorhanden sind.

## Neu gerechnete Jobs

| Jahr | Job | Tax-Lines | Derivate-Lines | Binance-Market-Anker | Fehlerhafte Summary-Zeilen |
| ---: | --- | ---: | ---: | ---: | ---: |
| 2021 | `3c7b4069-2065-4c5a-a77a-7e52eb545664` | 5494 | 43 | 826 | 403 |
| 2022 | `bee1a279-eb50-47ec-b6ea-96ebbd7a7f81` | 6896 | 630 | 826 | 403 |
| 2023 | `c7e8b073-1750-4703-bd01-e2f3c9e63405` | 9099 | 0 | 826 | 403 |
| 2024 | `690aca3b-59ae-45ee-91e5-e3b9a5812f0b` | 1680 | 36 | 826 | 403 |
| 2025 | `28e7f7e6-1ea8-4e4e-a4b0-93e4cc534480` | 465 | 957 | 826 | 403 |
| 2026 | `5c2d47e8-8dd8-400f-9fdb-86ac9af6c71a` | 1 | 0 | 826 | 403 |

Anker-Aufteilung je Job:

- `attached_eur_value_count=108`
- `attached_usd_value_count=718`
- `missing_quote_rate_count=0`

## Audit-Ergebnis nach Fix

Aktualisierter Bericht:

- `docs/224_VALUATION_ANOMALY_AUDIT_RESULTS_2026-05-11.md`

Aktuelle Kennzahlen:

- `priority_1_total=0`
- `fast_null_cost_basis=1`
- `fx_available_but_low_cost_basis=0`
- `same_tx_priced_counterflow_candidates=1`
- `high_gain_ratio=16`

Damit sind die vorherigen Binance-Legacy-DOGE/HNT/ETH-Fast-Null-Treffer aus der
technischen Fehlerklasse entfernt.

## Verbleibender Fast-Null-Treffer

Dieser Abschnitt ist durch `docs/227_BNB_2021_COINMARKETCAP_PRICE_BACKFILL_2026-05-11.md`
ueberholt.

Der nach diesem Fix noch verbleibende Fast-Null-Treffer war:

- 2021, Line `468`, `BNB`
- Lot-Event `binance_api/dust_convert_in/in`
- `tx_id=55615425065`

Bewertung:

- Der BNB-Zufluss stammt aus einem Binance-Dust-Convert mit vielen
  `userAssetDribbletDetails`.
- Es gibt keinen lokalen BNB/USD-FX-Cachekurs fuer `2021-04-28`.
- Der bepreiste Gegenfluss im gleichen `tx_id` deckt nur einen kleinen Teil der
  Dust-Assets ab.

Deshalb wurde dieser Punkt nicht automatisch korrigiert. Eine Korrektur braucht
entweder einen belegten BNB-Preisimport fuer den Tag oder eine vollstaendige
Bewertung der Dust-Ausgangsassets.

Der belegte BNB-Preisimport wurde danach ueber CoinMarketCap Public Historical
Data eingebracht:

- `BNB/USD 2021-04-28 = 562.63256836`
- Source: `coinmarketcap_public_historical:bnb`

Nach der anschliessenden Dust-Convert-Preisanker-Regel ist `fast_null_cost_basis=0`.

## Validierung

Gruene Pruefungen:

```bash
python3 -m ruff check src/tax_engine/queue/service.py tests/unit/api/test_process_endpoints.py --no-cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_process_endpoints.py::test_attach_binance_market_quote_value_anchors_from_crypto_quote tests/unit/api/test_process_endpoints.py::test_attach_binance_market_quote_value_anchors_from_eur_quote tests/unit/api/test_process_endpoints.py::test_drop_malformed_binance_market_summary_events tests/unit/api/test_process_endpoints.py::test_attach_bitget_tax_api_spot_trade_value_anchors_from_biz_order
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/valuation_anomaly_audit_20260511.py
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

Hinweis: Die erste breite Unit-/Coverage-Pruefung wurde versehentlich parallel
gegen denselben Test-Store gestartet und erzeugte Cross-Test-Kollisionen. Die
sequenziellen Wiederholungen waren gruen.

AI-Readonly-Snapshot:

- `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`
- Groesse `478978048` Bytes
- Neuester 2024-Job im Snapshot:
  `690aca3b-59ae-45ee-91e5-e3b9a5812f0b`
- Neuester 2025-Job im Snapshot:
  `28e7f7e6-1ea8-4e4e-a4b0-93e4cc534480`

Review-/Export-Gegenprobe:

- 2024 und 2025 job-spezifisch `allow_export=true`
- `issues_open=0`
- `issues_historical_open=3`
- `unmatched_total=0`
- 2024 PDF-Seiten: all `63`, tax `61`, derivatives `3`
- 2025 PDF-Seiten: all `52`, tax `18`, derivatives `36`
- `part=2` liefert in allen PDF-Scopes korrekt `report_part_not_found`
