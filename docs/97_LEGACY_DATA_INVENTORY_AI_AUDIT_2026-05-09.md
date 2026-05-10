# Legacy Data Inventory + AI Audit - 2026-05-09

## Zweck

Inventur von `/workspace/steuerreport/usertransfer/legacy_daten/` mit aktiver lokaler KI-Vorauswertung. Ziel ist, Primaerdaten, Referenzen, Belege und Duplikatrisiken fuer die Rekonstruktion ab 2021 zu trennen.

## Summary

- Dateien: `180`
- Kategorien: `{'cointracking_tax_or_export': 51, 'heliumtracker_rewards': 44, 'bank_barclays_evidence': 31, 'bank_kontist_evidence': 28, 'binance_export': 10, 'helium_legacy_cointracking': 6, 'hardware_invoice_evidence': 5, 'helium_legacy_raw': 3, 'blockpit_manual_template': 1, 'solscan_export': 1}`
- Endungen: `{'.pdf': 88, '.csv': 54, '.xlsx': 34, '.zip': 2, '.gz': 1, '.xlsm': 1}`
- Lesbare Tabellendateien: `85`
- Exakte Duplikatgruppen: `25`
- Gleiche Dateinamen-Gruppen: `22`

## Kandidaten

- Primaer/Match: `19`
- Referenz/Crosscheck: `64`
- Evidence-only: `91`
- Manuell pruefen: `6`

## Primaer-/Match-Kandidaten Top

- `usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-2023 cointracking.xlsm` rows `12366` category `helium_legacy_cointracking` dates `{'min': '1999-01-02T00:00:00+00:00', 'max': '2025-10-01T00:00:00+00:00'}` assets `{'top_values': {'HNT2': 5697}}`
- `usertransfer/legacy_daten/Export fuer Steuer/Cointracking/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2022-cointracking.csv` rows `11934` category `helium_legacy_cointracking` dates `{'columns_checked': ['date'], 'best_column': 'date', 'min': '2022-01-01T00:08:54+00:00', 'max': '2022-12-12T23:24:30+00:00', 'count': 4763}` assets `{'columns_checked': ['buyCurrency', 'sellCurrency', 'feeCurrency'], 'top_values': {'HNT2': 11945}}`
- `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2022-raw.csv` rows `11934` category `helium_legacy_raw` dates `{'columns_checked': ['date'], 'best_column': 'date', 'min': '2022-01-01T00:08:54+00:00', 'max': '2022-12-12T23:24:30+00:00', 'count': 4763}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-2023 cointracking.xlsx` rows `5681` category `helium_legacy_cointracking` dates `{'min': '2021-01-06T04:03:19+00:00', 'max': '2021-12-12T23:30:55+00:00'}` assets `{'top_values': {'HNT2': 5697}}`
- `usertransfer/legacy_daten/Export fuer Steuer/Cointracking/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-cointracking (1).csv` rows `5672` category `helium_legacy_cointracking` dates `{'columns_checked': ['date'], 'best_column': 'date', 'min': '2021-01-06T04:03:19+00:00', 'max': '2021-12-12T23:30:55+00:00', 'count': 2063}` assets `{'columns_checked': ['buyCurrency', 'sellCurrency', 'feeCurrency'], 'top_values': {'HNT2': 5697}}`
- `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-raw.csv` rows `5672` category `helium_legacy_raw` dates `{'columns_checked': ['date'], 'best_column': 'date', 'min': '2021-01-06T04:03:19+00:00', 'max': '2021-12-12T23:30:55+00:00', 'count': 2063}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Export fuer Steuer/Cointracking/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2023-cointracking.csv` rows `4283` category `helium_legacy_cointracking` dates `{'columns_checked': ['date'], 'best_column': 'date', 'min': '2023-01-01T00:05:25+00:00', 'max': '2023-12-04T23:49:28+00:00', 'count': 1898}` assets `{'columns_checked': ['buyCurrency', 'sellCurrency', 'feeCurrency'], 'top_values': {'HNT2': 4283}}`
- `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2023-raw.csv` rows `4283` category `helium_legacy_raw` dates `{'columns_checked': ['date'], 'best_column': 'date', 'min': '2023-01-01T00:05:25+00:00', 'max': '2023-12-04T23:49:28+00:00', 'count': 1898}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - PIVOT.xlsx` rows `3656` category `binance_export` dates `{'min': '2021-01-03T07:41:49+00:00', 'max': '2022-01-01T17:23:34+00:00'}` assets `{'top_values': {'ADA': 554, 'USDT': 468, 'HNT': 342, 'DOGE': 156, 'BNB': 118, 'EUR': 115, 'ETH': 56, 'BTC': 51, 'BTT': 10, 'WABI': 7, 'NFT': 6, 'LDDOGE': 5, 'HOT': 5, 'GTO': 4, 'WRX': 4, 'YFIDOWN': 4, 'SOL': 4, 'CDT': 3, 'DOCK': 3, 'WIN': 3}}`
- `usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - Skalierung angepasst.xlsx` rows `2013` category `binance_export` dates `{'min': '2021-01-03T07:41:00+00:00', 'max': '2022-01-01T17:23:00+00:00'}` assets `{'top_values': {'ADA': 554, 'USDT': 468, 'HNT': 342, 'DOGE': 156, 'BNB': 118, 'EUR': 115, 'ETH': 56, 'BTC': 51, 'BTT': 10, 'WABI': 7, 'NFT': 6, 'LDDOGE': 5, 'HOT': 5, 'GTO': 4, 'WRX': 4, 'YFIDOWN': 4, 'SOL': 4, 'CDT': 3, 'DOCK': 3, 'WIN': 3}}`
- `usertransfer/legacy_daten/Steuer-2022/export-solscan.csv` rows `1000` category `solscan_export` dates `{'columns_checked': ['Time'], 'min': '', 'max': '', 'count': 0}` assets `{'columns_checked': ['TokenAddress'], 'top_values': {'SOL': 247}}`
- `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Trade History-2022-04-04 10_41_01.xlsx` rows `329` category `binance_export` dates `{'min': '2021-02-06T21:23:58+00:00', 'max': '2021-05-15T23:59:49+00:00'}` assets `{'top_values': {'BNB': 104, 'USDT': 87, 'HNT': 59, 'DOGE': 23, 'ETH': 18, 'EUR': 17, 'BTC': 6, 'WABI': 3, 'HOT': 2, 'BTT': 2, 'VET': 1, 'SOL': 1, 'DOCK': 1, 'YFIDOWN': 1, 'CDT': 1, 'WRX': 1, 'ADA': 1, 'GTO': 1}}`
- `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Trade History-2022-04-04 10_41_52.xlsx` rows `50` category `binance_export` dates `{'min': '2021-06-03T05:46:27+00:00', 'max': '2021-11-15T00:29:26+00:00'}` assets `{'top_values': {'USDT': 24, 'HNT': 13, 'EUR': 10, 'ETH': 3}}`
- `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Trade History-2022-04-04 10_42_16.xlsx` rows `34` category `binance_export` dates `{'min': '2021-11-14T08:04:50+00:00', 'max': '2021-12-28T06:42:23+00:00'}` assets `{'top_values': {'USDT': 18, 'HNT': 16}}`
- `usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-all-cointracking.csv` rows `24` category `helium_legacy_cointracking` dates `{'columns_checked': ['date'], 'min': '', 'max': '', 'count': 0}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - HNT Transfer Staking Wallet - Deposit_History 07 bis 09-2021.xlsx` rows `9` category `binance_export` dates `{'min': '2021-07-27T18:03:02+00:00', 'max': '2021-09-28T17:54:45+00:00'}` assets `{'top_values': {'HNT': 9}}`
- `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - HNT Transfer Staking Wallet - deposit_history 11-2021.xlsx` rows `4` category `binance_export` dates `{'min': '2021-11-13T07:19:30+00:00', 'max': '2021-12-13T13:19:15+00:00'}` assets `{'top_values': {'HNT': 4}}`
- `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - EINZAHLUNG - Export Deposit History.xlsx` rows `3` category `binance_export` dates `{'min': '2021-03-05T07:45:57+00:00', 'max': '2021-03-23T07:26:28+00:00'}` assets `{'top_values': {'EUR': 3}}`
- `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Withdraw History.xlsx` rows `1` category `binance_export` dates `{'min': '2021-03-27T15:16:45+00:00', 'max': '2021-03-27T15:16:45+00:00'}` assets `{'top_values': {'EUR': 1}}`

## Referenz-/Crosscheck-Kandidaten Top

- `usertransfer/legacy_daten/Heliumtracker/Auswertung 2022-2024.xlsx` rows `15594` category `heliumtracker_rewards` dates `{'min': '2021-01-12T00:00:00+00:00', 'max': '2024-12-10T00:00:00+00:00'}` assets `{'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/Binance Export History Daten 2021 2022.xlsx` rows `5617` category `heliumtracker_rewards` dates `{'min': '2021-01-03T07:41:49+00:00', 'max': '2023-01-01T16:11:22+00:00'}` assets `{'top_values': {'ADA': 1583, 'BTTC': 1028, 'LDADA': 703, 'HNT': 586, 'USDT': 531, 'DOGE': 223, 'VET': 150, 'EUR': 123, 'BNB': 118, 'WIN': 100, 'VTHO': 87, 'LDDOGE': 68, 'LDVET': 61, 'ETH': 56, 'BTC': 55, 'NFT': 15, 'LDWIN': 14, 'BTT': 13, 'LDHNT': 8, 'WABI': 7}}`
- `usertransfer/legacy_daten/Cointracking/20220404-14621975-umsatz (1).CSV` rows `1825` category `cointracking_tax_or_export` dates `{'columns_checked': ['Buchungstag', 'Valutadatum'], 'best_column': 'Buchungstag', 'min': '2021-01-11T00:00:00+00:00', 'max': '2022-04-04T00:00:00+00:00', 'count': 1825}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Cointracking/20220404-14621975-umsatz (2).CSV` rows `1825` category `cointracking_tax_or_export` dates `{'columns_checked': ['Buchungstag', 'Valutadatum'], 'best_column': 'Buchungstag', 'min': '2021-01-11T00:00:00+00:00', 'max': '2022-04-04T00:00:00+00:00', 'count': 1825}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/daily_hotspot_rewards_2022-03-21T17_52_18.702901-04_00.xlsx` rows `1295` category `heliumtracker_rewards` dates `{'min': '2021-01-06T00:00:00+00:00', 'max': '2021-12-12T00:00:00+00:00'}` assets `{'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2021-10.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2021-01-10T00:00:00+00:00', 'max': '2021-12-10T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2021-12.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2021-01-12T00:00:00+00:00', 'max': '2021-12-12T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2021-5.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2021-01-05T00:00:00+00:00', 'max': '2021-12-05T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2021-7.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2021-01-07T00:00:00+00:00', 'max': '2021-12-07T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2021-8.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2021-01-08T00:00:00+00:00', 'max': '2021-12-08T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2022-10.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2022-01-10T00:00:00+00:00', 'max': '2022-12-10T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2022-12.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2022-01-12T00:00:00+00:00', 'max': '2022-12-12T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2022-3.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2022-01-03T00:00:00+00:00', 'max': '2022-12-03T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2022-5.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2022-01-05T00:00:00+00:00', 'max': '2022-12-05T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2022-7.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2022-01-07T00:00:00+00:00', 'max': '2022-12-07T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2022-8.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2022-01-08T00:00:00+00:00', 'max': '2022-12-08T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2023-1.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2023-01-01T00:00:00+00:00', 'max': '2023-12-01T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2023-10.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2023-01-10T00:00:00+00:00', 'max': '2023-12-10T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2023-12.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2023-01-12T00:00:00+00:00', 'max': '2023-12-12T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2023-3.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2023-01-03T00:00:00+00:00', 'max': '2023-12-03T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2023-5.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2023-01-05T00:00:00+00:00', 'max': '2023-12-05T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2023-7.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2023-01-07T00:00:00+00:00', 'max': '2023-12-07T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2023-8.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2023-01-08T00:00:00+00:00', 'max': '2023-12-08T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2024-1.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2024-01-01T00:00:00+00:00', 'max': '2024-12-01T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2024-10.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2024-01-10T00:00:00+00:00', 'max': '2024-12-10T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2024-3.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2024-01-03T00:00:00+00:00', 'max': '2024-12-03T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2024-5.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2024-01-05T00:00:00+00:00', 'max': '2024-12-05T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2024-7.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2024-01-07T00:00:00+00:00', 'max': '2024-12-07T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2024-8.csv` rows `465` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2024-01-08T00:00:00+00:00', 'max': '2024-12-08T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`
- `usertransfer/legacy_daten/Heliumtracker/advance/heliumtracker-report-advanced-2021-11.csv` rows `450` category `heliumtracker_rewards` dates `{'columns_checked': ['Date'], 'best_column': 'Date', 'min': '2021-01-11T00:00:00+00:00', 'max': '2021-12-11T00:00:00+00:00', 'count': 180}` assets `{'columns_checked': [], 'top_values': {}}`

## Duplikate

- Exact: `['usertransfer/legacy_daten/Cointracking/CoinTracking - Abschlussbericht.pdf', 'usertransfer/legacy_daten/Steuer-2021/CoinTracking/CoinTracking - Abschlussbericht.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/CoinTracking - Auszug für die Steuererklärung - 2021.pdf', 'usertransfer/legacy_daten/Steuer-2021/CoinTracking/CoinTracking - Auszug für die Steuererklärung - 2021.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/CoinTracking - Detaillierter Bericht.xlsx', 'usertransfer/legacy_daten/Steuer-2021/CoinTracking/CoinTracking - Detaillierter Bericht.xlsx']`
- Exact: `['usertransfer/legacy_daten/Cointracking/CoinTracking - Einkommensbericht.pdf', 'usertransfer/legacy_daten/Steuer-2021/CoinTracking/CoinTracking - Einkommensbericht.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/CoinTracking - Gebührenbericht.pdf', 'usertransfer/legacy_daten/Steuer-2021/CoinTracking/CoinTracking - Gebührenbericht.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Export Deposit History.xlsx', 'usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - EINZAHLUNG - Export Deposit History.xlsx']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Export Trade History-2022-04-04 10_41_52.xlsx', 'usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Trade History-2022-04-04 10_41_52.xlsx']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Export Trade History-2022-04-04 10_42_16.xlsx', 'usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Trade History-2022-04-04 10_42_16.xlsx']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Export Withdraw History.xlsx', 'usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Withdraw History.xlsx']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-01-07.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-01-07.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-01-07.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-02-07.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-02-07.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-02-07.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-03-07.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-03-07.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-03-07.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-04-07.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-04-07.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-04-07.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-05-07.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-05-07.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-05-07.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-06-07.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-06-07.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-06-07.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-07-07.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-07-07.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-07-07.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-08-08.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-08-08.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-08-08.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-09-07.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-09-07.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-09-07.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-10-07.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-10-07.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-10-07.pdf']`
- Exact: `['usertransfer/legacy_daten/Cointracking/Kontoauszug_2013410958_2021-11-07.pdf', 'usertransfer/legacy_daten/Kontoauszuege Barclays/Kontoauszug_2013410958_2021-11-07.pdf', 'usertransfer/legacy_daten/Steuer-2021/Barclays-Kontoauszüge/Kontoauszug_2013410958_2021-11-07.pdf']`

## Lokale KI

- Status: `invalid_empty_content`
- Modell: `qwen3.6-35b-a3b-iq4xs`
- Endpoint: `http://192.168.2.203:11435`
- Dauer Sekunden: `112.221854`
- Usage: `{'completion_tokens': 1800, 'prompt_tokens': 26317, 'total_tokens': 28117, 'prompt_tokens_details': {'cached_tokens': 0}}`

```text
Local model returned no visible content. Reasoning output was intentionally ignored.
```

## Bewertung

- Inventar enthaelt 180 Dateien; wichtigste Kategorien: {'cointracking_tax_or_export': 51, 'heliumtracker_rewards': 44, 'bank_barclays_evidence': 31, 'bank_kontist_evidence': 28, 'binance_export': 10, 'helium_legacy_cointracking': 6, 'hardware_invoice_evidence': 5, 'helium_legacy_raw': 3, 'blockpit_manual_template': 1, 'solscan_export': 1}.
- Primaer-/Match-Kandidaten: 19; Referenz-/Crosscheck-Kandidaten: 64.
- Bankauszuege und Hardware-Rechnungen sind Belege fuer Fiat-/Anschaffungsketten, aber keine direkten Krypto-Events.
- Lokale KI-Review Status: invalid_empty_content.

## Naechste Aktionen

- Nicht blind importieren: zuerst gegen vorhandene RAW-Events per Hash/Zeitraum/TxID matchen.
- Helium Legacy raw + CoinTracking 2021-2023 als Primaer-/TXID-Abgleich nutzen, Heliumtracker als Reward-Referenz.
- Binance-Alt-Exports mit vorhandenen Binance/Binance-API Events deduplizieren, besonders 2021/2022.
- Bank-/Rechnungs-PDFs als Belegindex fuer Fiat- und Hardware-Anschaffungsketten erfassen, nicht als Krypto-Ledger.
