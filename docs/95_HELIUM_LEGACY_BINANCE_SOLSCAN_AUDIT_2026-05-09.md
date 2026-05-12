# Helium Legacy / Binance / Solscan Audit - 2026-05-09

## Zweck

Gezielte Pruefung, ob Binance ausserhalb der alten Helium-Blockchain sauber belegt ist, und wo Helium-Legacy/Solscan/Blockpit als Evidenzquellen stehen.

## Gesamtabdeckung

- Helium-bezogene Effective Events: `30895`
- Quellen: `{'helium_legacy_cointracking': 21889, 'heliumtracker': 7037, 'solana_rpc': 556, 'blockpit': 540, 'binance': 328, 'heliumgeek': 265, 'pionex': 204, 'helium_legacy_raw': 27, 'binance_api': 23, 'bitget_tax_api': 21, 'solscan_wallet_discovery': 5}`
- Jahre: `{'2022': 16007, '2023': 7494, '2021': 6248, '2024': 709, '2025': 396, '2026': 41}`
- Assets: `{'HNT': 27753, 'IOT': 3066, 'MOBILE': 76}`

## Binance HNT

- HNT-Deposit-Zeilen: `64` total rows `2849.93931748` HNT
- Eindeutige HNT-Deposit-TXIDs: `19` total unique `959.74309828` HNT
- Deposit-Zeitraum: `2021-07-27T18:03:02+00:00` bis `2022-07-12T07:08:01+00:00`
- Deposit-Adressen: `{'138bCXPVfSq7yyTfoDUrVwztPmUr4WGyA7TED9Y41djmF7rjA8y': 64}`
- HNT-Withdrawals: `2` total `550.009374` HNT
- HNT-Trade-Legs: `274` net `-409.39` HNT

## Binance Deposits vs Helium Legacy TXID

- Binance-HNT-Deposit-Zeilen: `64`
- Eindeutige Deposit-TXIDs: `19`
- Eindeutig per Legacy-TXID gematcht: `19`
- Eindeutig nicht per Legacy-TXID gematcht: `0`
- Gematchte eindeutige Menge: `959.74309828` HNT
- Nicht gematchte eindeutige Menge: `0` HNT

## Helium Legacy Raw

- Legacy-Raw-Transfers: `27`
- Wallets top: `{'14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA': 27, '14aDLshY7p2MJrCgbYrWFZZfjB1MBSqHboo2cJCPCVR9Meorh7w': 18, '133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j': 9}`
- Treffer direkte Binance-HNT-Deposit-Adresse: `0`

## HeliumGeek Einheitenpruefung

- Auffaellige Rows: `159`
- Payload-Totals: `{'HNT': '10995657317.12162', 'IOT': '1595933017592'}`
- Raw-Display-Totals: `{'HNT': '0', 'IOT': '1707546.095357'}`
- Bewertung: HeliumGeek payload.quantity appears to be stored in raw subunits for affected rows; raw display token columns contain human token amounts. Dashboard/core logic and the updated balance audit use the display columns.

## Solana / Solscan nach Migration

- Effective Solana-Helium Events: `561`
- Effective nach Quelle: `{'solana_rpc': 556, 'solscan_wallet_discovery': 5}`
- Effective nach Asset: `{'IOT': 430, 'HNT': 92, 'MOBILE': 39}`
- Cached Solscan Helium Transfers: `169`
- Cached Solscan nach Symbol: `{'HNT': 169}`

## Balance Status

- Negative Endbestaende gesamt: `3`
- `IOT` final `2522892.1320230`, erster negativer Bruch: `None`
- `SOL` final `963140.69038353704400000000`, erster negativer Bruch: `{'event_id': '834dd4b04416ebcbde6d4b5731d23466566e3001779d00222b40cb7654a5f754', 'timestamp': '2023-05-08T04:43:46+00:00', 'asset': 'SOL', 'source': 'blockpit', 'event_type': 'withdrawal', 'side': 'out', 'quantity': '1.192', 'delta': '-1.192', 'balance_before': '0.00329676', 'balance_after': '-1.18870324', 'tx_id': 'blockpit-7001:out', 'raw_integration': 'Binance', 'raw_label': 'Withdrawal', 'raw_comment': ''}`
- `HNT` final `2681.67191191143114379127906`, erster negativer Bruch: `None`
- `USDT` final `690.11952391396508054000`, erster negativer Bruch: `{'event_id': '3450aa41e7b74c69acf27e9104f44cb956c9847870d864a24e988ff3a9b446e8', 'timestamp': '2022-01-19T12:50:48+00:00', 'asset': 'USDT', 'source': 'binance_api', 'event_type': 'withdrawal', 'side': 'out', 'quantity': '1245.38419', 'delta': '-1245.38419', 'balance_before': '1001.24273238379999800000', 'balance_after': '-244.14145761620000200000', 'tx_id': 'b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa', 'raw_integration': '', 'raw_label': '', 'raw_comment': ''}`

## Bewertung

- Binance-HNT ist als CEX-Seite stark belegt: Deposits, Deposit-Adresse, Trades und API/CSV-Duplikate liegen lokal vor.
- Von 19 eindeutigen Binance-HNT-Deposit-Transaktionen wurden 19 per gleicher Legacy-Transaktions-ID in Helium-Legacy-Quellen gefunden.
- Nicht gematchte Binance-HNT-Deposits sind kein Binance-Problem, sondern ein Legacy-L1-Evidence-Gap: Binance kennt den Eingang, aber die lokale Legacy-Quelle enthaelt nicht jeden passenden On-Chain-Transfer.
- Solana/Solscan deckt die Post-Migration-Phase ab; das ersetzt nicht die alte Helium-L1-Historie vor Migration.
- HeliumGeek-Miningdaten haben ein Rohdaten-Einheitenproblem: payload.quantity ist bei betroffenen rows um Faktor 1e6 zu hoch. Die Dashboard-/Core-Logik und die aktualisierte Bestandsbruch-Auswertung verwenden die Display-Tokenmengen aus raw_row.

## Ergebnis

Nein, die harte Aussage `alles komplett sauber ausser Helium-Blockchain` waere noch zu stark. Die Binance-Seite ist fuer HNT gut belegt; die offene Stelle ist die vollstaendige unabhaengige Legacy-L1-Gegenpruefung und das HeliumGeek-Einheitenproblem. Solscan deckt erst die Solana-Phase nach Migration ab.
