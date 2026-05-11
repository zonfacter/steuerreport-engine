# Binance Transaction-History Stable-Counterflow-Fix

Stand: 2026-05-11

## Ergebnis

- Fix implementiert in `src/tax_engine/queue/service.py`.
- Test ergaenzt in `tests/unit/api/test_process_endpoints.py`.
- Betroffener neuer Job 2022: `d1c40860-d286-4ff7-a7e7-1a173f99ad4e`.
- `binance_transaction_history_anchor_summary` fuer 2022:
  - Gruppen: `2`
  - angehaengte Bewertungsanker: `9`
- Die 2022-HNT-Zero-Cost-Zeilen aus Binance-Transaction-History-HNT-Kaeufen sind nach Neuberechnung verschwunden.
- HNT-/USDT-Restzeilen sinken von `8` auf `6`.
- Rest-Erloes sinkt von `2501.557499756668497643145881 EUR` auf `2189.09067462794969078534501 EUR`.

## Fix

Neue Funktion:

`attach_binance_transaction_history_stable_counterflow_value_anchors()`

Die Funktion bewertet nur sehr eng begrenzte Binance-Transaction-History-Gruppen:

- `source=binance`
- `event_type=trade`
- `tx_id` beginnt mit `binance-txhist-`
- gleiche `source_file_id`
- gleicher Timestamp
- Stable-Outflows, zum Beispiel `USDT`, stehen genau einem Nicht-Stable-Inflow-Asset gegenueber
- mehrere Teilkaeufe desselben Assets werden proportional nach Menge auf den Stable-Gegenfluss verteilt

Damit wird kein Marktpreis erfunden. Verwendet wird nur der in derselben Binance-Transaction-History-Gruppe vorhandene Stable-Gegenfluss.

## Betroffener Fall

Vor dem Fix blieben 2022 zwei HNT-Zeilen aus Pionex-Verkaeufen mit Null-Kostenbasis sichtbar:

| Line | Asset | Menge | Erloes EUR | Lot-Quelle |
| ---: | --- | ---: | ---: | --- |
| 957 | `HNT` | 8.95 | 171.6573822489 | `binance/trade/in` |
| 2760 | `HNT` | 6.54564033217319698392122 | 140.8094428798188068578008705 | `binance/trade/in` |

Die Lot-Quellen waren Binance-Transaction-History-HNT-Kaeufe aus Januar 2022. In derselben importierten Binance-History lagen die zugehoerigen USDT-Spend-Zeilen mit identischem Timestamp, aber ohne bereits nutzbaren Bewertungsanker.

## Wirkung

- 2022 hat nach Neuberechnung keine HNT-Zero-Cost-Zeile ueber `50 EUR` Erloes mehr.
- Verbleibend im Restbestandsaudit:
  - 2021 HNT: `3` Zeilen, `805.2140123327466767853450105 EUR`
  - 2022 USDT: `3` Zeilen, `1383.876662295203014 EUR`
- Fuer USDT erzeugt dieser Fix bewusst keine Anschaffungskosten. Die USDT-Restluecke bleibt eine Pionex-/Binance-Opening- bzw. Bot-Historienfrage.

## Validierung

- `python3 -m ruff check src/tax_engine/queue/service.py tests/unit/api/test_process_endpoints.py --no-cache`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_process_endpoints.py -q`
- 2022 neu gerechnet: `d1c40860-d286-4ff7-a7e7-1a173f99ad4e`
- AI-Readonly-DB neu gebaut:
  `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`
- `scripts/hnt_usdt_remaining_inventory_gap_audit_20260511.py`
- `scripts/valuation_anomaly_audit_20260511.py`
