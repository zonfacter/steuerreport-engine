# Bitget Spot-Bewertung ueber BizOrderId

Stand: 2026-05-11

## Anlass

Das neue Bewertungsanomalie-Audit aus
`docs/224_VALUATION_ANOMALY_AUDIT_RESULTS_2026-05-11.md` fand nach dem
SOL-Fix weitere Prioritaet-1-Treffer in aktuellen Jahren:

- `2025/HNT` aus `bitget_tax_api`
- `2024/JUP` aus `bitget_tax_api`

Die Tax-Lines hatten materielle Erloese, aber nur fee-grosse Kostenbasis.

## Ursache

Bitget Tax API liefert Spot-Kaeufe und die zugehoerige Stablecoin-Gegenseite als
getrennte Raw-Events. Beide Seiten teilen nicht dieselbe `tx_id`, sondern dieselbe
`raw_row.bizOrderId`.

Beispiel HNT:

```text
HNT in:
unique_event_id=445446633a39941eef09286c62f7a8974bd3037f335a04b81c3bbb20c04a0ba0
timestamp_utc=2025-01-29T05:58:45.618000+00:00
source=bitget_tax_api
event_type=trade
side=in
asset=HNT
quantity=845.931
fee=0.845931 HNT
tx_id=1268376005322551306
raw_row.bizOrderId=1268376005262102633

USDT out:
unique_event_id=239f0bc2688100d8c6606fc488fe1b66e9fed6aca4afdb359e829caa93388b1b
timestamp_utc=2025-01-29T05:58:45.618000+00:00
source=bitget_tax_api
event_type=trade
side=out
asset=USDT
quantity=3112.180149
tx_id=1268376005326745601
raw_row.bizOrderId=1268376005262102633
```

Die bestehende Gegenflusslogik suchte gleiche `tx_id`. Dadurch wurde der
USDT-Gegenfluss nicht als Anschaffungskostenanker fuer den HNT-Inflow genutzt.

## Fix

Geaendert:

- `src/tax_engine/queue/service.py`
- `tests/unit/api/test_process_endpoints.py`
- `scripts/valuation_anomaly_audit_20260511.py`

Neue Funktion:

```text
attach_bitget_tax_api_spot_trade_value_anchors()
```

Regel:

- Nur `source=bitget_tax_api`
- Nur `event_type=trade`
- Nur Inflow eines Nicht-Stable-Assets
- Nur wenn ein Stablecoin-Outflow mit derselben `raw_row.bizOrderId` vorhanden ist
- Der Stablecoin-Outflow wird als `value_usd_sum` am Inflow angehaengt
- Die spaetere FX-Enrichment-Schicht wandelt `value_usd_sum` in EUR um

Keine Preise wurden erfunden. Verwendet wurde der vorhandene Stablecoin-Gegenfluss
aus demselben Bitget-BizOrder-Kontext.

## Neuberechnung

Neu gerechnete Jobs:

```text
2024 job_id=54225c56-f4e7-4ecd-a63a-26b499f2f336
tax_lines=1680
derivative_lines=36
bitget_spot_anchors_attached=25

2025 job_id=1505480c-23b5-408c-9813-445425e1ef0c
tax_lines=465
derivative_lines=957
bitget_spot_anchors_attached=25
```

## Korrigierte Beispiele

HNT 2025, Verkauf am `2025-03-09T19:04:42+00:00`:

| Line | Menge | Kostenbasis EUR | Erloes EUR | Ergebnis EUR |
| ---: | ---: | ---: | ---: | ---: |
| 377 | 679.6608229896572553151696 | 2405.908843731238530538445382 | 1747.101889630951191847321056 | -658.806954100287338691124326 |
| 378 | 43.875 | 155.22725219625 | 112.7828658276577873731294338 | -42.4443863685922126268705662 |
| 379 | 99.916 | 353.59322998168 | 256.8390386788890138615065643 | -96.7541913027909861384934357 |
| 380 | 12 | 42.44377392 | 30.84659578192349740119779387 | -11.59717813807650259880220613 |

JUP 2024:

| Line | Menge | Kostenbasis EUR | Erloes EUR | Ergebnis EUR |
| ---: | ---: | ---: | ---: | ---: |
| 1282 | 70.5 | 65.0175412035 | 74.73018256697157885204666665 | 9.71264136347157885204666665 |
| 1284 | 127.007492 | 117.488407101069524 | 134.6282704189103867415416482 | 17.1398633178408627415416482 |

## Audit-Ergebnis nach Fix

Das Bewertungsanomalie-Audit wurde erneut ausgefuehrt:

```text
latest_tax_lines=23953
fast_null_cost_basis=113
fx_available_but_low_cost_basis=18
same_tx_priced_counterflow_candidates=0
high_gain_ratio=98
solana_swap_in_raw_events_without_raw_anchor=310
priority_1_total=0
```

Damit sind nach der aktuellen Heuristik keine Prioritaet-1-Treffer in aktuellen
Jahren offen. Die verbleibenden Treffer sind Prioritaet 2, ueberwiegend alte
`2021`/`2022`-Themen wie `UNKNOWN`, `DOGE`, `HNT` und historische Zero-Cost- bzw.
Altbestandsfaelle. Diese duerfen nicht automatisch korrigiert werden, wenn kein
eindeutiger Beleg- oder Codepfad vorliegt.

## Export- und Gate-Validierung

Job-spezifische Review-Gates:

```text
2024 allow_export=true
2025 allow_export=true
blocking_reasons=[]
warning_reasons=[]
issues_open=0
issues_historical_open=3
unmatched_total=0
```

Export-Metriken:

| Jahr | Vollreport Zeilen | Tax-Zeilen | Derivate-Zeilen | PDF all | PDF tax | PDF Derivate |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024 | 1736 | 1700 | 36 | 63 | 61 | 3 |
| 2025 | 1442 | 485 | 957 | 52 | 18 | 36 |

Alle PDFs bleiben unter der harten Grenze von `100` Seiten je Datei.

## Readonly-Snapshot

Der AI-Readonly-Snapshot wurde neu gebaut:

```text
/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite
size_bytes=456892416
latest_2024_job=54225c56-f4e7-4ecd-a63a-26b499f2f336
latest_2025_job=1505480c-23b5-408c-9813-445425e1ef0c
```

Readonly-Hinweis:

- `ai_open_zero_cost_tax_lines` zeigt fuer `2025` keinen offenen Treffer.
- Fuer `2024` bleibt ein kleiner historischer/untergeordneter Zero-Cost-Treffer
  sichtbar; das job-spezifische Review-Gate bleibt trotzdem ohne Blocker.

## Validierung

Ausgefuehrt:

```text
python3 -m ruff check src/tax_engine/queue/service.py tests/unit/api/test_process_endpoints.py scripts/valuation_anomaly_audit_20260511.py --no-cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_process_endpoints.py
python3 -m mypy src/ --cache-dir=/tmp/steuerreport_mypy_cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/verify_integrity.py --all-years
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/build_ai_readonly_db_snapshot.py
systemctl restart steuerreport-api.service
curl -fsS http://127.0.0.1:8000/api/v1/health
```

Ergebnis: alle ausgefuehrten Checks erfolgreich.

## Naechste Arbeit

Der Plan ist nicht abgeschlossen. Naechster sinnvoller Schritt:

1. Prioritaet-2-Treffer nach Jahren gruppieren.
2. Historische `2021`/`2022`-Altbestandsfaelle gegen bereits dokumentierte
   Review-/Closed-Year-Regeln abgleichen.
3. Nur Treffer mit eindeutigem technischem Muster in weitere Fixes ueberfuehren.
