# HNT 2025 Bitget -> Solana Timestamp-Order Fix

- Datum: `2026-05-10`
- Code: `src/tax_engine/core/processor.py`
- Test: `tests/unit/core/test_processor_fifo.py`
- Match-ID: `7787227c-e348-45bc-a904-42755db8aa5d`

## Befund

Das offene Issue `2025/HNT` kam aus einem HNT-Swap auf Solana:

- Swap-Out: `2025-03-09T19:04:42+00:00`
- Menge: `859.9208492 HNT`
- Event: `6fe43ea7893891978082129e2bcac9f9128380e7f857bc0eddc8e619a76f5a5c`

Direkt davor existierte der passende Transfer von Bitget nach Solana:

- Bitget Tax API Withdrawal:
  - Event: `1ed5f455a115148a96e2eb90f2a5946016819a97585fb2e70b408a3fbd716d2f`
  - Zeit: `2025-03-09T19:00:22.011000+00:00`
  - Menge: `859.9208492 HNT`
  - Fee: `0.5174198 HNT`
  - `tx_id`: `1282705829779644421`
- Solscan Inbound:
  - Event: `d6fd2b5fffdcc4758c89496124abbebcd8ed3297707fcb8d238f881c4f4c6af3`
  - Zeit: `2025-03-09T18:59:51+00:00`
  - Menge: `859.9208492 HNT`
  - `counterflow_for_platform=bitget`
  - `counterflow_tx_id=1282705829779644421`

Die Zeitstempel sind um `31` Sekunden invertiert: On-Chain-Eingang vor CEX-Withdrawal-Abschlusszeit. Ohne spezielle Transfer-Reihenfolge wurde der Solana-Eingang zuerst als neuer Lot ohne Cost Basis verarbeitet.

## Korrektur

- Transfer-Match manuell verifiziert und gespeichert:
  - Outbound: Bitget Withdrawal
  - Inbound: Solscan HNT Inbound
  - Confidence: `0.9850`
  - Amount-Diff: `0`
  - Time-Diff: `31`
- FIFO-Prozessor verbessert:
  - Bei bestaetigten Transfer-Matches wird die Verarbeitungsreihenfolge innerhalb des Paares immer `outbound -> inbound`.
  - Die originalen RAW-Zeitstempel bleiben unveraendert.
  - Das verhindert Nullkosten-Lots bei CEX/On-Chain-Zeitstempel-Inversionen.

## Ergebnis

Einzellauf 2025 nach Match und Prozessorfix:

- Job: `fb2c8530-b47d-44be-85af-9e9d1bb4bd33`
- HNT-Zero-Cost-Zeilen: `0`

Gesamtlauf `2020..2026` danach:

- Aktueller Report: `docs/190_CURRENT_TAX_RUNS_2026-05-10.md`
- 2025 Job: `3ebf9a80-cdc5-43ba-85dc-b08fe9ed966a`
- Review-Gate `allow_export`: `True`
- High-Issues offen: `0`
- Issues offen: `5`
- `2025/HNT` ist nicht mehr offen.

## Offene Issues nach Fix

- `2021/HNT`: `8` Zero-Cost-Zeilen, `1790.06 EUR`
- `2022/USDT`: `3` Zero-Cost-Zeilen, `1383.88 EUR`
- `2022/HNT`: `5` Zero-Cost-Zeilen, `2300.13 EUR`
- `2024/JUP`: `4` Zero-Cost-Zeilen, `3412.26 EUR`
- `2024/ZEUS`: `1` Zero-Cost-Zeile, `1687.95 EUR`

## Validierung

- `PYTHONPATH=src python3 -m pytest -q tests/unit/core/test_processor_fifo.py`
  - Ergebnis: `21 passed`
- `python3 -m py_compile src/tax_engine/core/processor.py`
- `PYTHONPATH=src python3 scripts/run_current_tax_years_20260510.py`
- AI-Readonly-Snapshot neu gebaut:
  - `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`
