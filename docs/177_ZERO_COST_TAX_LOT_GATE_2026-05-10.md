# Zero-Cost Tax Lot Gate - 2026-05-10

## Ergebnis

Der technische Final-Export wurde nach einer fachlichen Materialitaetspruefung wieder gesperrt.

Grund: Aktuelle Steuerlaeufe enthalten steuerpflichtige Verkaeufe mit `cost_basis_eur=0` und materiellem Erloes. Das ist kein Rohdatenimport und keine neue Buchung, sondern ein Review-Gate fuer fehlende oder bewusst zu bestaetigende Anschaffungskostenketten.

## Live-Gate

Live auf Port `8000` geprueft:

- `allow_export=false`
- `issues_total=3`
- `issues_open=3`
- `issues_high_open=1`
- `unmatched_total=0`
- `balance_adjustment_candidates_open=0`
- Blocker: `high_severity_issues_open`

Snapshot:

- `var/review_gate_snapshot_2026-05-10.json`

## Offene Nullbasis-Issues

| Jahr | Asset | Severity | Zeilen | Erloes EUR | Einordnung |
|---:|---|---|---:|---:|---|
| 2025 | JUP | high | 54 | 11228.97 | Muss vor finaler Freigabe geklaert werden. |
| 2024 | USDC | medium | 6 | 2843.31 | Review noetig, blockiert aktuell nicht allein. |
| 2022 | USDT | medium | 3 | 1377.09 | Altjahr-Kontext, dokumentieren oder bestaetigen. |

## JUP 2025 Detail

Der 2025er WISO-/Tax-Export zeigt bei JUP:

- JUP Tax Rows: `325`
- JUP Gesamt-Gewinn/Verlust: `12944.29 EUR`
- JUP Zeilen mit `cost_basis_eur=0` und Erloes: `54`
- Erloes dieser Nullbasis-Zeilen: `11228.97479440662808655316000 EUR`

Die groessten betroffenen Lots stammen aus 2024-12-09 bis 2024-12-20 und werden 2025-01-19/20 auf Binance verkauft. Beispiele:

- Lot `be03e71c...df06`: `4044.651153 JUP`, Erloesanteil `3880.61 EUR`
- Lot `c1d37d31...2398`: `3227.11444133 JUP`, Erloesanteil `3069.19 EUR`
- Lot `2020c645...06da`: `1547.517296 JUP`, Erloesanteil `1471.57 EUR`

Ein Teil der betroffenen `solana_rpc`-Lots hat fuer dieselbe Signatur Solscan-Referenzwerte:

- `cSc2hQ...D4a`: Solscan `value_usd_sum=4682.284012091743`
- `3Nq9j...rFQ`: Solscan `value_usd_sum=1110.2511949999998`
- `4cgan...EXX2`: Solscan `value_usd_sum=861.512081191200361`
- `66fLx...Hba`: Solscan `value_usd_sum=209.73427007910814`

Geschaetzter Effekt nur fuer die bereits verkauften, mit Solscan-Wert belegbaren JUP-Nullbasis-Lots: ca. `5943.69 EUR` zusaetzliche Cost Basis. Das ist nur ein Pruefwert, keine automatische Buchung.

## Derivate 2024 Detail

Der 2024er Derivate-Export bleibt rechnerisch konsistent:

- Derivative Rows: `36`
- Cost Basis: `31672.58 EUR`
- Proceeds: `24786.43 EUR`
- Fees: `1527.54 EUR`
- Netto: `-8413.69 EUR`
- Verlustsumme absolut: `20149.13 EUR`
- Unmatched Closes laut Processing-Summary: `4`

Die unmatched Derivate-Zeilen sind in `var/report_exports_final_2026-05-09/2024_33e3a5fb-d8d1-42e1-bef5-c24da36e3e26_derivatives.csv` sichtbar und sollten separat plausibilisiert werden, blockieren aber aktuell nicht das Gate, weil der neue High-Blocker JUP 2025 ist.

## Code-Aenderung

Ergaenzt:

- `src/tax_engine/api/review.py`
  - neue Nullbasis-Pruefung fuer aktuelle abgeschlossene Steuerlaeufe
  - gruppiert nach Steuerjahr und Asset
  - `>= 1000 EUR` Erloes erzeugt Issue
  - `>= 5000 EUR` Erloes erzeugt `high`
- `tests/unit/api/test_issue_endpoints.py`
  - Test: `test_review_gates_block_on_material_zero_cost_tax_lots`

Validierung:

```bash
python3 - <<'PY'
import ast
ast.parse(open('/workspace/steuerreport/src/tax_engine/api/review.py', encoding='utf-8').read())
print('syntax ok')
PY
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/steuerreport/src pytest -q -p no:cacheprovider /workspace/steuerreport/tests/unit/api/test_issue_endpoints.py::test_review_gates_block_on_material_zero_cost_tax_lots
```

## Konsequenz

Die Dateien in `var/report_exports_final_2026-05-09/` bleiben als historisch erzeugte Exporte erhalten, sind aber wegen des neuen fachlichen Gates nicht mehr als final freigegeben zu behandeln.

Naechster Schritt: JUP 2025 Anschaffungsketten klaeren. Primaer sinnvoll ist, die Solscan-Werte fuer identische Signaturen als Bewertungsanker kontrolliert zu nutzen oder die Nullbasis fachlich explizit zu bestaetigen.
