# Solana SOL Swap-In Bewertung

Stand: 2026-05-11

## Anlass

Im 2025-Export fiel folgende Tax-Line auf:

```text
tax 101 SOL 0.28617728 2025-01-04T08:32:56+00:00 2025-01-22T17:34:36.028000+00:00 0 71.04 71.04 taxable
```

Die Zeile war nicht als echte Nullkosten-Zeile in `ai_open_zero_cost_tax_lines`
sichtbar, weil die Kostenbasis technisch nicht exakt Null war. Inhaltlich war
die Kostenbasis mit rund `0.0004 EUR` aber nur fee-gross und fuer einen
Solana-Swap-In plausibel falsch.

## Ursache

Betroffene Lot-Quelle:

```text
unique_event_id=6425cada61c73e54f87ff19b03e22f36a844c222ce24ba36c3a29604f0481668
timestamp_utc=2025-01-04T08:32:56+00:00
source=solana_rpc
event_type=sol_transfer
side=in
asset=SOL
quantity=0.289811571
defi_label=swap
tx_id=3m4rH8EDFqVMPB17WsdKSgkr7LtxkthKJwuU2gKvMR6ShPqx9QxCVSsjER6FePZnfmXpDeC6rrjMYfnWSUKpeiqe
```

Die Preisanker-Logik fuer Solana-Swap-Ins erkannte bisher:

- `swap_in_aggregated`
- `token_transfer` mit `defi_label=swap`

Sie erkannte aber keinen nativen `sol_transfer` mit `defi_label=swap`. Dadurch
wurde fuer den SOL-Erwerb kein SOL/USD-Preisanker aus dem FX-Cache angehaengt.

## Fix

Geaendert:

- `src/tax_engine/queue/service.py`
- `tests/unit/api/test_process_endpoints.py`

`attach_cached_usd_prices_to_swap_in_events()` behandelt jetzt auch
`sol_transfer` mit `defi_label=swap` und `side=in` als Solana-Swap-In. Normale
SOL-Transfers ohne Swap-Label bleiben unveraendert.

Der neue Regressionstest prueft einen nativen SOL-Swap-In am `2025-01-04` mit
SOL/USD-Preisanker `217.76`.

## Neuberechnung 2025

Neuer abgeschlossener Job:

```text
job_id=d2e5a9cc-d051-49df-b8a6-0b49a5e9d61d
tax_year=2025
status=completed
tax_lines=465
derivative_lines=957
derivative_processed_events=957
```

Korrigierte SOL-Splits fuer den Binance-Sell
`d2c5bc054f48be911051c06eb4074fbfce171b44ecd170ee65652aba148f69d8`:

| Line | Asset | Menge | Kostenbasis EUR | Erloes EUR | Ergebnis EUR |
| ---: | --- | ---: | ---: | ---: | ---: |
| 101 | SOL | 0.286177283 | 60.50927453911816737483725105 | 71.0361802286395714728000 | 10.52690568952140409796274895 |
| 102 | SOL | 3.37600000 | 824.819969011200000000000 | 838.005525588441600000000 | 13.185556577241600000000 |
| 103 | SOL | 4.315822717 | 1054.4362439851223304000000 | 1071.2924420338036285272000 | 16.8561980486812981272000 |

Die urspruenglich auffaellige Line 101 hat damit nicht mehr nur fee-grosse
Anschaffungskosten, sondern eine aus dem vorhandenen SOL/USD-FX-Cache abgeleitete
Kostenbasis.

## Readonly-Snapshot

Der AI-Readonly-Snapshot wurde neu gebaut:

```text
/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite
size_bytes=455602176
```

Readonly-Gegenprobe:

```text
latest_2025_job=d2e5a9cc-d051-49df-b8a6-0b49a5e9d61d
open_zero_cost_2025=0
```

## Export- und Gate-Validierung

Der neue 2025-Job bleibt technisch exportfaehig:

```text
report_files=11
all_rows=1442
tax_rows=485
derivative_rows=957
wiso_lines=409
all_pdf_pages=52
tax_pdf_pages=18
derivatives_pdf_pages=36
```

Alle PDF-Dateien bleiben unter der harten Grenze von `100` Seiten.

Job-spezifisches Review-Gate:

```text
allow_export=true
blocking_reasons=[]
warning_reasons=[]
issues_open=0
issues_open_total=3
issues_historical_open=3
issues_high_open=0
unmatched_total=0
final_export_allowed=true
```

## Validierung

Ausgefuehrt:

```text
python3 -m ruff check src/tax_engine/queue/service.py tests/unit/api/test_process_endpoints.py --no-cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_process_endpoints.py -q
python3 -m mypy src/ --cache-dir=/tmp/steuerreport_mypy_cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/verify_integrity.py --all-years
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/build_ai_readonly_db_snapshot.py
systemctl restart steuerreport-api.service
curl -fsS http://127.0.0.1:8000/api/v1/health
```

Ergebnis: alle ausgefuehrten Checks erfolgreich.
