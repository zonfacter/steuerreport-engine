# Binance 2021 Account Statement Income Audit - 2026-05-09

## Zweck

Isolierte Pruefung der Binance Legacy Account-Statement/Pivot-Datei. Es wurde nichts importiert.

## Quelle

- Datei: `/workspace/steuerreport/usertransfer/legacy_daten/Steuer-2021/Binance-export/BINANCE - TRADING - Export - PIVOT.xlsx`
- Sheet: `part-00000-3d734e3b-9531-4c31-9`
- Zeilen: `1924`

## Operationen

- By Operation: `{'Buy': 399, 'Fee': 399, 'Transaction Related': 347, 'Savings Interest': 311, 'Savings purchase': 308, 'Sell': 80, 'Small assets exchange BNB': 32, 'Deposit': 25, 'Savings Principal redemption': 14, 'Distribution': 6, 'Withdraw': 3}`
- Totals: `{'Buy:ADA': '76.6', 'Buy:BNB': '2.28', 'Buy:BTC': '0.06605408', 'Buy:BTT': '129068', 'Buy:CDT': '564', 'Buy:COTI': '100', 'Buy:DOCK': '250', 'Buy:DOGE': '24683.6', 'Buy:ETH': '1.23828496', 'Buy:EUR': '9612.5471437', 'Buy:GTO': '1891.9', 'Buy:HNT': '2897.086', 'Buy:HOT': '6959', 'Buy:SOL': '1', 'Buy:USDT': '6633.884045', 'Buy:VET': '100', 'Buy:WABI': '53', 'Buy:WIN': '56.57E+3', 'Buy:WRX': '14', 'Buy:YFIDOWN': '57673.31', 'Deposit:EUR': '1697.53', 'Deposit:HNT': '479.54309828', 'Distribution:NFT': '23302.344666', 'Fee:ADA': '-0.0666', 'Fee:BNB': '-0.03163004', 'Fee:BTC': '-0.00003395', 'Fee:BTT': '-83.744', 'Fee:CDT': '-0.564', 'Fee:DOCK': '-0.25', 'Fee:DOGE': '-22.1726', 'Fee:ETH': '-0.00123828', 'Fee:EUR': '-8.45350647', 'Fee:GTO': '-1.8919', 'Fee:HNT': '-2.431598', 'Fee:HOT': '-6.959', 'Fee:SOL': '-0.001', 'Fee:USDT': '-41.82887241', 'Fee:VET': '-0.1', 'Fee:WABI': '-0.053', 'Fee:WRX': '-0.014', 'Fee:YFIDOWN': '-57.67331', 'Savings Interest:ADA': '0.06117724', 'Savings Interest:DOGE': '0.85150592', 'Savings Interest:USDT': '0.00080654', 'Savings Principal redemption:ADA': '66.55192377', 'Savings Principal redemption:DOGE': '1330.48272574', 'Savings Principal redemption:LDADA': '-66.55192377', 'Savings Principal redemption:LDDOGE': '-1330.48272574', 'Savings Principal redemption:LDUSDT': '-129.17234121', 'Savings Principal redemption:USDT': '129.17234121', 'Savings purchase:ADA': '-77.14650101', 'Savings purchase:DOGE': '-1330.48272574', 'Savings purchase:USDT': '-129.17234121', 'Sell:HNT': '-717.846', 'Sell:USDT': '19160.598447', 'Small assets exchange BNB:BNB': '0.2666412', 'Small assets exchange BNB:BTC': '-630E-9', 'Small assets exchange BNB:BTT': '-2497.5', 'Small assets exchange BNB:CDT': '-563.436', 'Small assets exchange BNB:COTI': '-100', 'Small assets exchange BNB:DOCK': '-249.75', 'Small assets exchange BNB:EUR': '-0.0117639', 'Small assets exchange BNB:GTO': '-0.0081', 'Small assets exchange BNB:HNT': '-0.001251', 'Small assets exchange BNB:SOL': '-0.099', 'Small assets exchange BNB:USDT': '-0.014455', 'Small assets exchange BNB:WABI': '-52.947', 'Small assets exchange BNB:WRX': '-0.986', 'Small assets exchange BNB:YFIDOWN': '-14403.91669', 'Transaction Related:ADA': '-66', 'Transaction Related:BNB': '-2.515', 'Transaction Related:BTC': '-0.06601751', 'Transaction Related:BTT': '-124582', 'Transaction Related:DOGE': '-24662.2', 'Transaction Related:ETH': '-1.237042', 'Transaction Related:EUR': '-4266.1123873', 'Transaction Related:GTO': '-1.89E+3', 'Transaction Related:HNT': '-2469.23', 'Transaction Related:HOT': '-6952', 'Transaction Related:SOL': '-0.9', 'Transaction Related:USDT': '-25523.51896127', 'Transaction Related:WIN': '-42427', 'Transaction Related:WRX': '-13', 'Transaction Related:YFIDOWN': '-43211.72', 'Withdraw:EUR': '-1035', 'Withdraw:HNT': '-96.529374', 'Withdraw:USDT': '-201'}`

## Income-Kandidaten

- Zeilen: `317`
- Existing Match: `0`
- Unmatched: `317`
- Counts: `{'Savings Interest:ADA': 276, 'Savings Interest:DOGE': 28, 'Savings Interest:USDT': 7, 'Distribution:NFT': 6}`
- Totals by Asset: `{'ADA': '0.06117724', 'DOGE': '0.85150592', 'NFT': '23302.344666', 'USDT': '0.00080654'}`
- Zeitraum: `2021-02-14T01:36:41+00:00` bis `2022-01-01T03:11:05+00:00`

## Principal / Produktbewegungen

- Zeilen: `322`
- Counts: `{'Savings purchase:ADA': 273, 'Savings purchase:DOGE': 32, 'Savings Principal redemption:DOGE': 5, 'Savings Principal redemption:LDDOGE': 5, 'Savings purchase:USDT': 3, 'Savings Principal redemption:USDT': 1, 'Savings Principal redemption:LDUSDT': 1, 'Savings Principal redemption:LDADA': 1, 'Savings Principal redemption:ADA': 1}`
- Totals by Asset: `{'ADA': '-10.59457724', 'LDADA': '-66.55192377', 'LDDOGE': '-1330.48272574', 'LDUSDT': '-129.17234121'}`
- Empfehlung: `do_not_import_as_income; use only for balance/evidence unless missing inventory requires explicit internal transfer modelling`

## Bewertung

- Income-like Binance account statement rows: 317; matched existing by timestamp/asset/quantity: 0; unmatched: 317.
- Income totals are small but potentially taxable/relevant: {'ADA': '0.06117724', 'DOGE': '0.85150592', 'NFT': '23302.344666', 'USDT': '0.00080654'}.
- Savings purchase/redemption rows are principal/product-position movements and should not be booked as income.
- Because the account statement rows have no tx_id, import should only happen through a dedicated reviewed importer with stable synthetic IDs and source documentation.

## Entscheidung

- `Savings Interest` und `Distribution` sind Kandidaten fuer einen dedizierten, review-pflichtigen Binance-Account-Statement-Income-Import.
- `Savings purchase` und `Savings Principal redemption` bleiben vorerst nicht steuerwirksam; sie dokumentieren interne Produkt-/Principal-Bewegungen.
