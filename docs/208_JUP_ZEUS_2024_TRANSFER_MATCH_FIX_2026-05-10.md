# JUP/ZEUS 2024 Transfer-Match Fix

- Datum: `2026-05-10`
- Aktueller Gesamtlauf: `docs/190_CURRENT_TAX_RUNS_2026-05-10.md`
- Betroffen: `2024/JUP`, `2024/ZEUS`

## ZEUS

Zwei interne Solana-Programmbewegungen wurden als Transfer-Out und spaetere Rueckgabe erkannt:

| Out | In | Menge | Zeitdifferenz | Match-ID |
|---|---|---:|---:|---|
| `620be1419f9823b329c56be8bce6f598a094bb0369f57fe1084003d719fb5df8` | `f6e86d18eb119ddff3cfcf65e87b555c2aa20bfea2e4b08972fa839fd616eda5` | `1843.317972` | `12271` s | `f1103095-48b1-4954-bb7a-e2fbeb37f103` |
| `7f137658d735bedd7f8707f0ef58714493f686063f5a1bd743c509e11545b594` | `fae95aece0a2cd1ba52fe1dcaf76bf4129176e6dbfb90165f9f1639c7231773e` | `1688.000000` | `12273` s | `f7274552-d750-47ed-9ef8-7e98178f24b7` |

Ergebnis:

- 2024-Einzellauf nach Match: `ZEUS` Zero-Cost `0`.
- Gesamtlauf danach: `2024/ZEUS` ist nicht mehr offen.

## JUP

Zwei interne Solana-Transferpaare vor dem Maerz-Verkauf wurden gematcht:

| Out | In | Menge | Zeitdifferenz | Match-ID |
|---|---|---:|---:|---|
| `bf7ee87ca51e57e9087f23eb7e5eb2496904be8901813cb6f816086ff880ca48` | `a9860e21ca39ad2f67b114df6cd66f6ed278db201ab65f54fee0f0412aca69c4` | `147.000000` | `61` s | `87dcfbf3-0849-4c34-a22d-59bf53cf5d5a` |
| `cc8b77cb7a15b7db62130a508d13eace060b285a099e72313460f8fd15d8fdd2` | `ba89e3d4073bd1208aa9e975f995f5ec6ce3b911cef8bf2ab2d4871da66cabdf` | `1070.000000` | `95` s | `8e845587-70cc-4d6a-8b0f-bb02b2993ecb` |

Ergebnis:

- `2024/JUP` reduziert von `4` Zero-Cost-Zeilen / `3412.26 EUR` auf `3` Zero-Cost-Zeilen / `1979.51 EUR`.
- Die Maerz-Restmenge `1217 JUP` wurde damit geschlossen.

## JUP Restbefund

Die verbleibenden JUP-Zeilen liegen im November 2024. Ein wichtiger Befund ist eine Solana-DCA-/Order-Programmbewegung:

- `2024-08-29T11:23:43+00:00` JUP Out `4632.733027`
- Programmhinweis im Raw: `DCA265Vj8a9CEuX1eb1LWRnDT7uK6q1xMipnNyatn23M`
- `2024-08-29T11:25:59+00:00` JUP In `1853.093212`
- Raw-Log: `CloseDca`

Das ist kein sauberer 1:1-Transfer. Die Differenz duerfte aus DCA-/Orderausfuehrungen oder fehlenden Gegenbuchungen stammen. Deshalb wurde hier kein automatischer Transfer-Match gesetzt und keine Cost-Basis synthetisch erzeugt.

## Aktueller Stand nach Gesamtlauf

- Gesamtlauf: `scripts/run_current_tax_years_20260510.py`
- 2024 Job: `356890b8-99b7-4562-89d0-79f4aa21804c`
- Review-Gate `allow_export`: `True`
- High-Issues offen: `0`
- Issues offen: `4`

Offen:

- `2021/HNT`: `8` Zero-Cost-Zeilen, `1790.06 EUR`
- `2022/USDT`: `3` Zero-Cost-Zeilen, `1383.88 EUR`
- `2022/HNT`: `5` Zero-Cost-Zeilen, `2300.13 EUR`
- `2024/JUP`: `3` Zero-Cost-Zeilen, `1979.51 EUR`

## Validierung

- `PYTHONPATH=src python3 scripts/run_current_tax_years_20260510.py`
- AI-Readonly-Snapshot neu gebaut:
  - `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`
