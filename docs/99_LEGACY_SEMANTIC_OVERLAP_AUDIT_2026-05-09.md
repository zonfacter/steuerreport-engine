# Legacy Semantic Overlap Audit - 2026-05-09

## Zweck

Semantischer Abgleich der Legacy-Dateien, die per Fingerprint als neu erschienen. Es wurde nichts importiert.

## Helium Raw vs bestehende Helium-TXIDs

- `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-raw.csv` unique_tx `5657` matched `5657` unmatched `0` ratio `1.000000` event_types `{'mining_reward': 5630, 'legacy_transfer': 27}` sides `{'in': 5632, 'out': 25}`
- `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2022-raw.csv` unique_tx `11893` matched `11893` unmatched `0` ratio `1.000000` event_types `{'mining_reward': 11879, 'legacy_transfer': 14}` sides `{'in': 11882, 'out': 11}`
- `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2023-raw.csv` unique_tx `4283` matched `4283` unmatched `0` ratio `1.000000` event_types `{'mining_reward': 4283}` sides `{'in': 4283}`

## Helium Workbooks vs bestehende Helium-TXIDs

- `usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-2023 cointracking.xlsx` unique_tx `5672` matched `5672` unmatched `0` ratio `1.000000`
- `usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-2023 cointracking.xlsm` unique_tx `5672` matched `5672` unmatched `0` ratio `1.000000`

## Binance Pivot/Skalierung

- `usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - PIVOT.xlsx` unique_keys `1906` matched `0` unmatched `1906` rows_with_tx_id `0` ratio `0.000000`
  - Eventtypen: `{'buy': 399, 'fee': 399, 'transaction related': 347, 'savings interest': 311, 'savings purchase': 308, 'sell': 80, 'small assets exchange bnb': 32, 'deposit': 25, 'savings principal redemption': 14, 'distribution': 6, 'withdraw': 3}`
- `usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - Skalierung angepasst.xlsx` unique_keys `1906` matched `0` unmatched `1906` rows_with_tx_id `0` ratio `0.000000`
  - Eventtypen: `{'buy': 399, 'fee': 399, 'transaction related': 347, 'savings interest': 311, 'savings purchase': 308, 'sell': 80, 'small assets exchange bnb': 32, 'deposit': 25, 'savings principal redemption': 14, 'distribution': 6, 'withdraw': 3}`

## Bewertung

- Helium raw overlap by base TXID: 21833/21833 matched existing Helium legacy TXIDs.
- Helium workbook overlap by base TXID: 11344/11344 matched existing Helium legacy TXIDs.
- Binance derived file `usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - PIVOT.xlsx` has 0 normalized rows with tx_id and semantic match ratio 0.000000.
- Binance derived file `usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - Skalierung angepasst.xlsx` has 0 normalized rows with tx_id and semantic match ratio 0.000000.
- If Helium raw matches by base TXID, it should be kept as evidence/validation unless replacing the CoinTracking layer deliberately.
- Binance Pivot/Skalierung files have weak/no tx_id coverage and should not be imported automatically as primary ledger rows.

## Entscheidung

- Helium raw ist primaer als Evidenz-/Validierungsschicht zu behandeln, solange CoinTracking-Helium bereits steuerwirksam ist.
- Binance Pivot/Skalierung nicht automatisch importieren; nur konkrete fehlende Earn/Savings/Distribution-Zeilen mit Primaerbeleg/API-Abgleich isolieren.
