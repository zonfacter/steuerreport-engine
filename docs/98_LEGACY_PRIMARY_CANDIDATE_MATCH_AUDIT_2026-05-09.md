# Legacy Primary Candidate Match Audit - 2026-05-09

## Zweck

Die Primaer-/Match-Kandidaten aus dem Legacy-Datenordner werden mit den bestehenden RAW-Events verglichen. Es wurde nichts importiert.

## Summary

- Bestehende RAW-Events: `54810`
- Kandidatendateien: `19`
- Neue Kandidaten nach Connector: `{'helium_legacy_raw': 21833, 'binance': 3814, 'helium_legacy_cointracking': 1636}`
- Duplikate nach Connector: `{'helium_legacy_cointracking': 31597, 'binance': 843, 'helium_legacy_raw': 0}`
- Neue Kandidaten nach Jahr: `{'2021': 11137, '2022': 11897, '2023': 4283}`
- Neue Kandidaten nach Asset: `{'HNT': 24153, 'ADA': 1108, 'USDT': 936, 'DOGE': 312, 'BNB': 236, 'EUR': 230, 'ETH': 112, 'BTC': 102, 'BTT': 20, 'WABI': 14, 'NFT': 12, 'LDDOGE': 10, 'HOT': 10, 'GTO': 8, 'WRX': 8, 'YFIDOWN': 8, 'SOL': 8, 'CDT': 6, 'DOCK': 6, 'WIN': 6, 'COTI': 4, 'VET': 4, 'LDUSDT': 2, 'LDADA': 2}`

## Dateien mit potenziell neuen Events

- `usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-2023 cointracking.xlsm` connector `helium_legacy_cointracking` new `818` duplicate `4854`
- `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2022-raw.csv` connector `helium_legacy_raw` new `11893` duplicate `0`
- `usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-2023 cointracking.xlsx` connector `helium_legacy_cointracking` new `818` duplicate `4854`
- `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-raw.csv` connector `helium_legacy_raw` new `5657` duplicate `0`
- `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2023-raw.csv` connector `helium_legacy_raw` new `4283` duplicate `0`
- `usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - PIVOT.xlsx` connector `binance` new `1908` duplicate `0`
- `usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - Skalierung angepasst.xlsx` connector `binance` new `1906` duplicate `0`

## Datei-Details

### `usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-2023 cointracking.xlsm`

- Connector: `helium_legacy_cointracking`
- Rohzeilen: `12366`, normalisiert: `5672`, unique: `5672`
- Bestehende Duplikate: `4854`, neue Kandidaten: `818`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-05-12T09:13:16+00:00', 'max': '2021-12-31T23:23:12+00:00'}`
- Assets: `{'HNT': 5672}`
- Eventtypen: `{'mining_reward': 5630, 'legacy_transfer': 27, 'legacy_network_fee': 15}`
- Neue Summary: `{'count': 818, 'years': {'2021': 818}, 'assets': {'HNT': 818}, 'event_types': {'mining_reward': 780, 'legacy_transfer': 25, 'legacy_network_fee': 13}, 'sides': {'in': 780, 'out': 38}, 'quantity_totals': {'HNT': '1059.2712364623872776'}}`

### `usertransfer/legacy_daten/Export fuer Steuer/Cointracking/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2022-cointracking.csv`

- Connector: `helium_legacy_cointracking`
- Rohzeilen: `11934`, normalisiert: `11934`, unique: `11934`
- Bestehende Duplikate: `11934`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '2022-01-01T00:08:54+00:00', 'max': '2022-12-31T23:33:54+00:00'}`
- Assets: `{'HNT': 11934}`
- Eventtypen: `{'mining_reward': 11881, 'legacy_network_fee': 39, 'legacy_transfer': 14}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

### `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2022-raw.csv`

- Connector: `helium_legacy_raw`
- Rohzeilen: `11934`, normalisiert: `11893`, unique: `11893`
- Bestehende Duplikate: `0`, neue Kandidaten: `11893`, interne Duplikate: `0`
- Zeitraum: `{'min': '2022-01-01T00:08:54+00:00', 'max': '2022-12-31T23:33:54+00:00'}`
- Assets: `{'HNT': 11893}`
- Eventtypen: `{'mining_reward': 11879, 'legacy_transfer': 14}`
- Neue Summary: `{'count': 11893, 'years': {'2022': 11893}, 'assets': {'HNT': 11893}, 'event_types': {'mining_reward': 11879, 'legacy_transfer': 14}, 'sides': {'in': 11882, 'out': 11}, 'quantity_totals': {'HNT': '1987.27300088000000577784314'}}`

### `usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-2023 cointracking.xlsx`

- Connector: `helium_legacy_cointracking`
- Rohzeilen: `5681`, normalisiert: `5672`, unique: `5672`
- Bestehende Duplikate: `4854`, neue Kandidaten: `818`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-05-12T09:13:16+00:00', 'max': '2021-12-31T23:23:12+00:00'}`
- Assets: `{'HNT': 5672}`
- Eventtypen: `{'mining_reward': 5630, 'legacy_transfer': 27, 'legacy_network_fee': 15}`
- Neue Summary: `{'count': 818, 'years': {'2021': 818}, 'assets': {'HNT': 818}, 'event_types': {'mining_reward': 780, 'legacy_transfer': 25, 'legacy_network_fee': 13}, 'sides': {'in': 780, 'out': 38}, 'quantity_totals': {'HNT': '1059.2712364623872776'}}`

### `usertransfer/legacy_daten/Export fuer Steuer/Cointracking/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-cointracking (1).csv`

- Connector: `helium_legacy_cointracking`
- Rohzeilen: `5672`, normalisiert: `5672`, unique: `5672`
- Bestehende Duplikate: `5672`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-05-12T09:13:16+00:00', 'max': '2021-12-31T23:23:12+00:00'}`
- Assets: `{'HNT': 5672}`
- Eventtypen: `{'mining_reward': 5630, 'legacy_transfer': 27, 'legacy_network_fee': 15}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

### `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2021-raw.csv`

- Connector: `helium_legacy_raw`
- Rohzeilen: `5672`, normalisiert: `5657`, unique: `5657`
- Bestehende Duplikate: `0`, neue Kandidaten: `5657`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-05-12T09:13:16+00:00', 'max': '2021-12-31T23:23:12+00:00'}`
- Assets: `{'HNT': 5657}`
- Eventtypen: `{'mining_reward': 5630, 'legacy_transfer': 27}`
- Neue Summary: `{'count': 5657, 'years': {'2021': 5657}, 'assets': {'HNT': 5657}, 'event_types': {'mining_reward': 5630, 'legacy_transfer': 27}, 'sides': {'in': 5632, 'out': 25}, 'quantity_totals': {'HNT': '1919.33711009000001038403392'}}`

### `usertransfer/legacy_daten/Export fuer Steuer/Cointracking/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2023-cointracking.csv`

- Connector: `helium_legacy_cointracking`
- Rohzeilen: `4283`, normalisiert: `4283`, unique: `4283`
- Bestehende Duplikate: `4283`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '2023-01-01T00:05:25+00:00', 'max': '2023-04-18T15:56:54+00:00'}`
- Assets: `{'HNT': 4283}`
- Eventtypen: `{'mining_reward': 4283}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

### `usertransfer/legacy_daten/Export fuer Steuer/raw/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-2023-raw.csv`

- Connector: `helium_legacy_raw`
- Rohzeilen: `4283`, normalisiert: `4283`, unique: `4283`
- Bestehende Duplikate: `0`, neue Kandidaten: `4283`, interne Duplikate: `0`
- Zeitraum: `{'min': '2023-01-01T00:05:25+00:00', 'max': '2023-04-18T15:56:54+00:00'}`
- Assets: `{'HNT': 4283}`
- Eventtypen: `{'mining_reward': 4283}`
- Neue Summary: `{'count': 4283, 'years': {'2023': 4283}, 'assets': {'HNT': 4283}, 'event_types': {'mining_reward': 4283}, 'sides': {'in': 4283}, 'quantity_totals': {'HNT': '106.662878830000001399402'}}`

### `usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - PIVOT.xlsx`

- Connector: `binance`
- Rohzeilen: `3656`, normalisiert: `1924`, unique: `1908`
- Bestehende Duplikate: `0`, neue Kandidaten: `1908`, interne Duplikate: `16`
- Zeitraum: `{'min': '2021-02-06T21:18:15+00:00', 'max': '2022-01-01T17:23:34+00:00'}`
- Assets: `{'ADA': 554, 'USDT': 468, 'HNT': 342, 'DOGE': 156, 'BNB': 118, 'EUR': 115, 'ETH': 56, 'BTC': 51, 'BTT': 10, 'WABI': 7, 'NFT': 6, 'LDDOGE': 5, 'HOT': 5, 'GTO': 4, 'WRX': 4, 'YFIDOWN': 4, 'SOL': 4, 'CDT': 3, 'DOCK': 3, 'WIN': 3, 'COTI': 2, 'VET': 2, 'LDUSDT': 1, 'LDADA': 1}`
- Eventtypen: `{'buy': 399, 'fee': 399, 'transaction related': 347, 'savings interest': 311, 'savings purchase': 308, 'sell': 80, 'small assets exchange bnb': 32, 'deposit': 25, 'savings principal redemption': 14, 'distribution': 6, 'withdraw': 3}`
- Neue Summary: `{'count': 1924, 'years': {'2021': 1922, '2022': 2}, 'assets': {'ADA': 554, 'USDT': 468, 'HNT': 342, 'DOGE': 156, 'BNB': 118, 'EUR': 115, 'ETH': 56, 'BTC': 51, 'BTT': 10, 'WABI': 7, 'NFT': 6, 'LDDOGE': 5, 'HOT': 5, 'GTO': 4, 'WRX': 4, 'YFIDOWN': 4, 'SOL': 4, 'CDT': 3, 'DOCK': 3, 'WIN': 3, 'COTI': 2, 'VET': 2, 'LDUSDT': 1, 'LDADA': 1}, 'event_types': {'buy': 399, 'fee': 399, 'transaction related': 347, 'savings interest': 311, 'savings purchase': 308, 'sell': 80, 'small assets exchange bnb': 32, 'deposit': 25, 'savings principal redemption': 14, 'distribution': 6, 'withdraw': 3}, 'sides': {'out': 1146, 'in': 778}, 'quantity_totals': {'BNB': '0.00001116', 'BTC': '0.00000199', 'BTT': '1904.756', 'DOGE': '0.07890592', 'ETH': '0.00000468', 'EUR': '6000.49948603', 'HNT': '90.59087528', 'HOT': '0.041', 'LDADA': '-66.55192377', 'LDDOGE': '-1330.48272574', 'LDUSDT': '-129.17234121', 'NFT': '23302.344666', 'USDT': '28.12100986', 'VET': '99.9', 'WIN': '14143'}}`

### `usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - Skalierung angepasst.xlsx`

- Connector: `binance`
- Rohzeilen: `2013`, normalisiert: `1924`, unique: `1906`
- Bestehende Duplikate: `0`, neue Kandidaten: `1906`, interne Duplikate: `18`
- Zeitraum: `{'min': '2021-02-06T21:18:00+00:00', 'max': '2022-01-01T17:23:00+00:00'}`
- Assets: `{'ADA': 554, 'USDT': 468, 'HNT': 342, 'DOGE': 156, 'BNB': 118, 'EUR': 115, 'ETH': 56, 'BTC': 51, 'BTT': 10, 'WABI': 7, 'NFT': 6, 'LDDOGE': 5, 'HOT': 5, 'GTO': 4, 'WRX': 4, 'YFIDOWN': 4, 'SOL': 4, 'CDT': 3, 'DOCK': 3, 'WIN': 3, 'COTI': 2, 'VET': 2, 'LDUSDT': 1, 'LDADA': 1}`
- Eventtypen: `{'buy': 399, 'fee': 399, 'transaction related': 347, 'savings interest': 311, 'savings purchase': 308, 'sell': 80, 'small assets exchange bnb': 32, 'deposit': 25, 'savings principal redemption': 14, 'distribution': 6, 'withdraw': 3}`
- Neue Summary: `{'count': 1924, 'years': {'2021': 1922, '2022': 2}, 'assets': {'ADA': 554, 'USDT': 468, 'HNT': 342, 'DOGE': 156, 'BNB': 118, 'EUR': 115, 'ETH': 56, 'BTC': 51, 'BTT': 10, 'WABI': 7, 'NFT': 6, 'LDDOGE': 5, 'HOT': 5, 'GTO': 4, 'WRX': 4, 'YFIDOWN': 4, 'SOL': 4, 'CDT': 3, 'DOCK': 3, 'WIN': 3, 'COTI': 2, 'VET': 2, 'LDUSDT': 1, 'LDADA': 1}, 'event_types': {'buy': 399, 'fee': 399, 'transaction related': 347, 'savings interest': 311, 'savings purchase': 308, 'sell': 80, 'small assets exchange bnb': 32, 'deposit': 25, 'savings principal redemption': 14, 'distribution': 6, 'withdraw': 3}, 'sides': {'out': 1146, 'in': 778}, 'quantity_totals': {'ADA': '61850180.38149819', 'BNB': '-130499998.69498884', 'BTC': '0.00000199', 'BTT': '190.4756E+9', 'CDT': '56399999.436', 'DOCK': '24999999.75', 'DOGE': '417583842.90306745', 'ETH': '0.00000468', 'EUR': '600505731635.44216963', 'GTO': '809999.9919', 'HNT': '9254572426.045151', 'HOT': '4.1E+6', 'LDADA': '-6655192377', 'LDDOGE': '-133048272574', 'LDUSDT': '-12917234121', 'NFT': '2.3302344666E+12', 'SOL': '99999999', 'USDT': '6172987252.391137', 'VET': '9999999999.9', 'WABI': '5299999.947', 'WIN': '1.4143E+12', 'WRX': '99999999'}}`

- `usertransfer/legacy_daten/Steuer-2022/export-solscan.csv` skipped `no_connector_mapping`
### `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Trade History-2022-04-04 10_41_01.xlsx`

- Connector: `binance`
- Rohzeilen: `329`, normalisiert: `658`, unique: `658`
- Bestehende Duplikate: `658`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-02-06T21:23:58+00:00', 'max': '2021-05-15T23:59:49+00:00'}`
- Assets: `{'USDT': 248, 'HNT': 171, 'DOGE': 67, 'EUR': 61, 'BTC': 44, 'ETH': 30, 'BTT': 7, 'BNB': 7, 'WIN': 3, 'ADA': 3, 'WABI': 3, 'HOT': 2, 'WRX': 2, 'SOL': 2, 'YFIDOWN': 2, 'GTO': 2, 'VET': 1, 'COTI': 1, 'DOCK': 1, 'CDT': 1}`
- Eventtypen: `{'trade': 658}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

### `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Trade History-2022-04-04 10_41_52.xlsx`

- Connector: `binance`
- Rohzeilen: `50`, normalisiert: `100`, unique: `100`
- Bestehende Duplikate: `100`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-06-03T05:46:27+00:00', 'max': '2021-11-15T00:29:26+00:00'}`
- Assets: `{'USDT': 45, 'HNT': 36, 'EUR': 12, 'ETH': 5, 'HOT': 1, 'DOGE': 1}`
- Eventtypen: `{'trade': 100}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

### `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Trade History-2022-04-04 10_42_16.xlsx`

- Connector: `binance`
- Rohzeilen: `34`, normalisiert: `68`, unique: `68`
- Bestehende Duplikate: `68`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-11-14T08:04:50+00:00', 'max': '2021-12-28T06:42:23+00:00'}`
- Assets: `{'USDT': 34, 'HNT': 34}`
- Eventtypen: `{'trade': 68}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

### `usertransfer/legacy_daten/Export fuer Steuer/helium-133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j-all-cointracking.csv`

- Connector: `helium_legacy_cointracking`
- Rohzeilen: `24`, normalisiert: `0`, unique: `0`
- Bestehende Duplikate: `0`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '', 'max': ''}`
- Assets: `{}`
- Eventtypen: `{}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

### `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - HNT Transfer Staking Wallet - Deposit_History 07 bis 09-2021.xlsx`

- Connector: `binance`
- Rohzeilen: `9`, normalisiert: `9`, unique: `9`
- Bestehende Duplikate: `9`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-07-27T18:03:02+00:00', 'max': '2021-09-28T17:54:45+00:00'}`
- Assets: `{'HNT': 9}`
- Eventtypen: `{'deposit': 9}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

### `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - HNT Transfer Staking Wallet - deposit_history 11-2021.xlsx`

- Connector: `binance`
- Rohzeilen: `4`, normalisiert: `4`, unique: `4`
- Bestehende Duplikate: `4`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-11-13T07:19:30+00:00', 'max': '2021-12-13T13:19:15+00:00'}`
- Assets: `{'HNT': 4}`
- Eventtypen: `{'deposit': 4}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

### `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - EINZAHLUNG - Export Deposit History.xlsx`

- Connector: `binance`
- Rohzeilen: `3`, normalisiert: `3`, unique: `3`
- Bestehende Duplikate: `3`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-03-05T05:45:57+00:00', 'max': '2021-03-23T05:26:28+00:00'}`
- Assets: `{'EUR': 3}`
- Eventtypen: `{'deposit': 3}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

### `usertransfer/legacy_daten/Steuer-2021/Binance exporte/BINANCE - Export Withdraw History.xlsx`

- Connector: `binance`
- Rohzeilen: `1`, normalisiert: `1`, unique: `1`
- Bestehende Duplikate: `1`, neue Kandidaten: `0`, interne Duplikate: `0`
- Zeitraum: `{'min': '2021-03-27T13:16:45+00:00', 'max': '2021-03-27T13:16:45+00:00'}`
- Assets: `{'EUR': 1}`
- Eventtypen: `{'withdrawal': 1}`
- Neue Summary: `{'count': 0, 'years': {}, 'assets': {}, 'event_types': {}, 'sides': {}, 'quantity_totals': {}}`

## Bewertung

- 7 Legacy-Primärdateien enthalten nach aktueller Fingerprint-Logik potenziell neue Events.
- Ein hoher New-Count bedeutet noch keinen Importfreigabe: alte Excel-Pivots und CoinTracking-Workbooks koennen abgeleitete Tabellen enthalten.
- CSV-Quellen mit Roh-/TXID-Bezug sind priorisiert; XLSX/Pivot-Dateien zuerst nur gegen bestehende Events und Summen abgleichen.
- Solscan-CSV wird separat behandelt, weil dafuer kein generischer Connector existiert und TokenAddress/Decimals korrekt gemappt werden muessen.

## Naechster Schritt

- Fuer Dateien mit neuen Kandidaten pro Quelle entscheiden: echte Primaerquelle, abgeleitete Pivot-/Steuerdatei oder reiner Crosscheck.
- Danach nur sicher primaere CSV/Export-Dateien per Import ausfuehren; XLSX-Pivots nicht automatisch steuerwirksam machen.
