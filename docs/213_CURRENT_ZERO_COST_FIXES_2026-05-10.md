# Current Zero-Cost Fixes - 2026-05-10

## Ergebnis

- Neu berechnet: Steuerjahre `2020` bis `2026`.
- Review-Gate: `allow_export=True`, Current-Issues offen `0`, Altjahr-Issues offen `3`, High-Issues offen `0`.
- Aktuelle Exporte: `var/report_exports_current_2026-05-10/`.
- Read-only-KI-Snapshot neu gebaut: `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`.

## Umgesetzte Fixes

### JUP 2024

- Ursache: Jupiter-DCA/Program-Funding-Transfer `5344f1f97c15fec9aff2fb8c2590bed1fb0b4bda8fef6bfce2371121085f74db` hat FIFO-Lots verbraucht, obwohl die spaeteren DCA-Swaps separat sichtbar und steuerwirksam sind.
- Entscheidung: enger Tax-Override `EXCLUDED` fuer genau diesen Program-Funding-Schritt.
- Ergebnis: JUP 2024 hat aktuell `0` Nullkosten-Zeilen.

### JUP 2025

- Ursache: Binance-Simple-Earn `interest` fuer JUP wurde nicht mit vorhandenen FX-Cache-Preisen bepreist.
- Code-Fix: `interest` wird in `attach_cached_usd_prices_to_reward_events` als reward-like bepreist.
- Ergebnis: JUP 2025 ist nicht mehr in den aktuellen Nullkosten-Zeilen.

### EUR 2025

- Ursache: Binance-Fiatkauf wurde auf der EUR-Seite als steuerbare Veräußerung ausgewertet.
- Code-Fix: `fiat_payment_in`/`fiat_payment_out` mit Asset `EUR` werden als Transfer klassifiziert; die Crypto-Seite bleibt Anschaffung.
- Ergebnis: EUR 2025 ist nicht mehr in den aktuellen Nullkosten-Zeilen.

### IOT 2024

- Ursache: ein Solana-RPC-`token_transfer` mit `defi_label=swap` wurde nicht wie ein Swap-Zufluss mit vorhandenem IOT/USD-FX-Cache bepreist.
- Code-Fix: Solana-`token_transfer`-Zufluesse mit `defi_label=swap` werden im Swap-In-Preisanker beruecksichtigt; normale Transfers bleiben ausgeschlossen.
- Ergebnis: IOT 2024 ist nicht mehr in den aktuellen Nullkosten-Zeilen.

### CBDC 2024

- Ursache: der CBDC-Swap-In hatte keinen eigenen Preis, aber im selben Solana-Tx lag ein bepreister MOBILE-Gegenabfluss vor.
- Code-Fix: unbepreiste Solana-Swap-In-Zufluesse koennen `value_usd_sum` aus bepreisten Gegenabfluessen derselben Transaktion ableiten.
- Ergebnis: CBDC 2024 ist nicht mehr in den aktuellen Nullkosten-Zeilen.

### IOT 2023

- Ursache 1: vorhandene Review-Zeitkorrekturen fuer HeliumGeek-April-IOT auf `2023-04-20` wurden im Queue-Worker erst nach den Preisankern angewendet.
- Code-Fix 1: Review-Actions laufen jetzt vor Preisankern und FX-Enrichment.
- Ursache 2: ein Solana-Helium-Distribution-Transfer kam mit `defi_label=unknown`, obwohl der Roh-Tx den Helium-Distributor `1atrmQs3...` enthaelt.
- Code-Fix 2: Solana-RPC-Token-Zufluesse fuer HNT/IOT/MOBILE aus dem bekannten Helium-Distributor werden eng als `claim` gelabelt und danach wie Reward-/Claim-Zufluesse bepreist.
- Ergebnis: IOT 2023 ist nicht mehr in den aktuellen Nullkosten-Zeilen.

### 25HAYB 2024

- Ursache: der Jupiter-/Solana-Swap-In fuer `25HAYB...MTDJ` hatte keinen eigenen Tokenpreis und der Gegenfluss lag nur im Roh-Routenblock der Transaktion.
- Code-Fix: unbepreiste Solana-Swap-In-Zufluesse koennen jetzt einen konservativen `value_usd_sum` aus dem groessten bepreisten Gegenfluss im Raw-Route-Block ableiten.
- Ergebnis: die 2024-Verkaufszeile `5945.66318 25HAYB...MTDJ` hat jetzt `77.355924270991... EUR` Kostenbasis bei `74.00590961138 EUR` Erloes. 25HAYB ist nicht mehr in den aktuellen Nullkosten-Zeilen.

## Verbleibende Current-State-Nullkosten

Die Runtime-Einstellung `runtime.review.closed_tax_years=[2020, 2021, 2022]` trennt abgeschlossene Altjahre vom aktuellen Review-Gate. Die folgenden Altjahr-Issues bleiben sichtbar und offen, zaehlen aber nicht als Current-Export-Blocker.

| Jahr | Asset | Zeilen | Menge | Erlös EUR | Bewertung |
|---:|---|---:|---:|---:|---|
| 2021 | BNB | 2 | 1.625 | 0.003129095 | Dust |
| 2021 | HNT | 8 | 91.3491563855978 | 1790.05924360799 | Altjahr/Legacy-Mining-Herkunft |
| 2021 | UNKNOWN | 3 | 6.340749 | 11.506435555656 | Altjahr/Legacy |
| 2022 | HNT | 5 | 439.688010219657 | 2300.1340507291 | Altjahr/Legacy-Mining-Herkunft |
| 2022 | USDT | 3 | 1569.8280684762 | 1383.8766622952 | Pionex Start-/Botkapital-Belegblocker |
| 2024 | USDC | 1 | 0.000002 | 0.000001893578471 | Dust |

## Validierung

Ausgefuehrt:

```bash
PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_process_endpoints.py tests/unit/core/test_processor_fifo.py
PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_issue_endpoints.py tests/unit/api/test_process_endpoints.py tests/unit/core/test_processor_fifo.py
PYTHONPATH=src python3 scripts/run_current_tax_years_20260510.py
python3 scripts/current_zero_cost_root_cause_audit_20260510.py
python3 scripts/build_ai_readonly_db_snapshot.py
```

Testergebnis aktuell: `93 passed`, eine bekannte Importlib-Deprecation-Warnung.
