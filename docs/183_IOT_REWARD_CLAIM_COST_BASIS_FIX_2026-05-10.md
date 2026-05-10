# IOT Reward-/Claim-Cost-Basis Fix

Stand: 2026-05-10

## Ausgangslage

- Offenes Review-Issue vor Fix: `zero_cost_tax_lots:2024:IOT`.
- Vorheriger Befund: IOT-Mengenbestand war nicht negativ, aber FIFO-Lots hatten `cost_basis_eur=0`.
- Ursache war zweigeteilt:
  - Reward-/Mining-Inflows wurden in der Steuerdomänen-Summary bewertet, aber im FIFO nicht als Anschaffungslots geführt.
  - Solana-IOT-Claims lagen als `token_transfer` mit `defi_label=claim` vor und wurden nicht mit dem vorhandenen IOT/USD-FX-Cache bepreist.

## Umsetzung

- `src/tax_engine/core/processor.py`
  - Reward-Inflows werden jetzt als FIFO-Anschaffungslots verarbeitet.
  - Transfers bleiben weiterhin Transfers; nur Reward-Klasse mit Buy-/In-Richtung erzeugt Lots.
- `src/tax_engine/queue/service.py`
  - Reward-Preisanker nutzt den vorhandenen FX-Cache jetzt auch fuer `defi_label=claim` und `defi_label=staking`.
  - Stable-/Solscan-Gegenflussanker bleiben unveraendert fuer Swap-Bewertung aktiv.
- `src/tax_engine/core/tax_domains.py`
  - HeliumGeek-Display-Mengen werden auch in der Steuerdomänen-Summary genutzt, damit Base-Unit-Felder nicht zu ueberhoehten EUR-Werten fuehren.

## Ergebnis nach Neuberechnung 2024

- Neuer 2024-Job: `f21e8665-dbce-4841-821a-49f86ed3e7f8`
- `reward_price_summary.attached_price_count`: `24426`
- `tax_domain_summary.anlage_so.leistungen_income_eur`: `2291.938703634026589700257328`
- Review-Gates:
  - Vorher: `4` offene Zero-Cost-Medium-Issues inkl. `2024/IOT`.
  - Nachher: `3` offene Zero-Cost-Medium-Issues.
  - `2024/IOT` ist geschlossen.
- Weiter offen:
  - `2022/USDT`: `3` Zeilen, `1377.09 EUR` Erloes.
  - `2024/USDC`: `6` Zeilen, `2843.31 EUR` Erloes.
  - `2024/JUP`: `5` Zeilen, `1941.79 EUR` Erloes.

## Tests

Ausgefuehrt:

```bash
PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_process_endpoints.py tests/unit/core/test_processor_fifo.py tests/unit/core/test_tax_domains.py
```

Ergebnis: `44 passed`, `1` Deprecation-Warnung aus Importlib.
