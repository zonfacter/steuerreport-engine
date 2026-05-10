# Transient Balance Undercoverage Audit - 2026-05-09

## Überblick

- Bewegungen: `37845`
- Assets: `55`
- Assets mit zwischenzeitlicher Unterdeckung: `3`
- Dust-Toleranz: `0.000001`
- Ignorierte Dust-Unterdeckungen: `1`
- Separat dokumentierte Fiat-Cash-Unterdeckungen: `0`

## Top Findings

### USDT

- Final Balance: `1715.70671421101011250000`
- Events: `2051`
- Erster Bruch: `2022-01-05T15:36:46+00:00` `binance` / `trade` / `out` delta `-186.270000` after `-75.10462220620000000000`
- Schlimmster Stand: `-1569.91028184620000000000` am `2022-01-19T12:56:19+00:00`
- Jahres-Netto: `{'2021': '197.26431286000000000000', '2022': '-107.70170036536000000000', '2023': '-88.26629794170000000000', '2024': '12.22958516807011250000', '2025': '1702.18081449'}`
- Top Quellen: `[{'source': 'binance_api', 'event_type': 'trade', 'side': 'sell_quote', 'net': '75304.76031000'}, {'source': 'binance_api', 'event_type': 'trade', 'side': 'buy_quote', 'net': '-70220.53397000'}, {'source': 'binance', 'event_type': 'trade', 'side': 'in', 'net': '54321.88957400'}, {'source': 'binance', 'event_type': 'trade', 'side': 'out', 'net': '-52550.28606327'}, {'source': 'solana_rpc', 'event_type': 'token_transfer', 'side': 'out', 'net': '-34733.843023'}, {'source': 'solana_rpc', 'event_type': 'swap_in_aggregated', 'side': 'in', 'net': '31653.240947'}, {'source': 'pionex', 'event_type': 'trade', 'side': 'out', 'net': '-25056.73396394677700000000'}, {'source': 'solana_rpc', 'event_type': 'token_transfer', 'side': 'in', 'net': '23866.833602'}]`

### BTC

- Final Balance: `0.00252370400000000000`
- Events: `68`
- Erster Bruch: `2024-04-14T05:04:47.263000+00:00` `bitget_tax_api` / `trade` / `out` delta `-0.000542` after `-0.00007630000000000000`
- Schlimmster Stand: `-0.00007630000000000000` am `2024-04-14T05:04:47.263000+00:00`
- Jahres-Netto: `{'2021': '0.000035940', '2022': '0.00000213', '2023': '0.00013133000000000000', '2024': '-0.00024569600000000000', '2025': '0.00260000'}`
- Top Quellen: `[{'source': 'binance', 'event_type': 'trade', 'side': 'in', 'net': '0.06605408'}, {'source': 'binance', 'event_type': 'trade', 'side': 'out', 'net': '-0.06601751'}, {'source': 'binance_sol_2023_blockpit_reconstruction', 'event_type': 'trade', 'side': 'buy_quote', 'net': '-0.03208291'}, {'source': 'binance_2022_2023_blockpit_source_chain_reconstruction', 'event_type': 'trade', 'side': 'buy_base', 'net': '0.0261892'}, {'source': 'binance_api', 'event_type': 'deposit', 'side': 'in', 'net': '0.01036997'}, {'source': 'binance_2022_2023_blockpit_source_chain_reconstruction', 'event_type': 'trade', 'side': 'buy_quote', 'net': '-0.00721984'}, {'source': 'bitget_btc_2024_blockpit_reconstruction', 'event_type': 'deposit', 'side': 'in', 'net': '0.0046913'}, {'source': 'bitget_tax_api', 'event_type': 'trade', 'side': 'out', 'net': '-0.004570'}]`

### USDC

- Final Balance: `0.18978533`
- Events: `83`
- Erster Bruch: `2024-12-01T13:35:14+00:00` `solana_rpc` / `swap_out_aggregated` / `out` delta `-148.066735` after `-0.000002`
- Schlimmster Stand: `-0.000002` am `2024-12-01T13:35:14+00:00`
- Jahres-Netto: `{'2024': '0.093580', '2025': '0.09620533'}`
- Top Quellen: `[{'source': 'solana_rpc', 'event_type': 'swap_in_aggregated', 'side': 'in', 'net': '66980.700987'}, {'source': 'solana_rpc', 'event_type': 'swap_out_aggregated', 'side': 'out', 'net': '-59402.809250'}, {'source': 'solana_rpc', 'event_type': 'token_transfer', 'side': 'out', 'net': '-59081.015587'}, {'source': 'solana_rpc', 'event_type': 'token_transfer', 'side': 'in', 'net': '51503.124838'}, {'source': 'binance_api', 'event_type': 'trade', 'side': 'buy_quote', 'net': '-688.39393600'}, {'source': 'bitget_tax_api', 'event_type': 'deposit', 'side': 'in', 'net': '500'}, {'source': 'bitget_tax_api', 'event_type': 'trade', 'side': 'out', 'net': '-500'}, {'source': 'binance_api', 'event_type': 'fiat_payment_in', 'side': 'in', 'net': '463.02038333'}]`

## Fiat-Cash-Unterdeckungen

- Keine.

## Ignorierte Dust-Unterdeckungen

- `BNSOL` worst `-390E-9` am `2025-03-23T13:46:29.121000+00:00` (Toleranz `0.000001`)

## Bewertung

- Dieser Report ist ein Chronologie-Audit: Endbestände können positiv sein, obwohl die Reihenfolge oder fehlende Transfers temporär negativ wird.
- Fiat-Cash-Unterdeckungen werden separat dokumentiert, weil Kreditkarte/Apple Pay/Bankzahlungen externe Zahlungswege sind und keine Crypto-Asset-Deckung beweisen muessen.
- Unterdeckungen bis zur Dust-Toleranz werden dokumentiert, aber nicht als offener Fehler gezählt.
- Keine automatische Korrektur. Die Top-Fälle müssen je Asset gegen Primary-/Reference-Quellen entschieden werden.
