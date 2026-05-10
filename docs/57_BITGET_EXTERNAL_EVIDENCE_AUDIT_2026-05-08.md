# Bitget External Evidence Audit - 2026-05-08

## Ergebnis

Externe Quellen koennen die Bitget-Bot-Trade-Luecke nur teilweise stuetzen.
Persoenliche Bot-Fills, interne Umbuchungen, konkrete Fees, Funding, Liquidationen und realisierte PnL bleiben Primaerdaten, die Bitget liefern muss.
Oeffentliche Marktdaten wurden gesichert, aber sie duerfen nur zur Preis-/Zeitpunkt-Plausibilisierung genutzt werden.

## Betroffene Daten im Bestand

- Bitget-Events: `2066`
- Zeitraum: `2024-04-02T16:59:41.727000+00:00` bis `2025-07-13T21:38:44+00:00`
- Jahre: `{"2024": 60, "2025": 2006}`
- Assets: `USDT:1185, SOL:745, JUP:60, XRP:34, HNT:27, EUR:8, BTC:5, USDC:2`
- Symbole: `JUPUSDT:1418, HNTUSDT:308, XRPUSDT:192, SOLUSDT:170, BTCUSDT:110`

## Gesicherte externe Public-Market-Daten

- Rohdatenordner: `/workspace/steuerreport/var/external_evidence/bitget_public_market_2026-05-08`
- Fetch-Zeitraum: `2024-03-30T00:00:00+00:00` bis `2025-07-16T00:00:00+00:00`

| Symbol | Spot Rows | Futures Rows | Funding Rows | Aussagekraft |
|---|---:|---:|---:|---|
| `JUPUSDT` | 471 | 450 | 0 | Preis-/Funding-Plausibilitaet, keine persoenlichen Fills |
| `HNTUSDT` | 471 | 317 | 0 | Preis-/Funding-Plausibilitaet, keine persoenlichen Fills |
| `XRPUSDT` | 471 | 450 | 0 | Preis-/Funding-Plausibilitaet, keine persoenlichen Fills |
| `SOLUSDT` | 471 | 450 | 0 | Preis-/Funding-Plausibilitaet, keine persoenlichen Fills |
| `BTCUSDT` | 471 | 450 | 0 | Preis-/Funding-Plausibilitaet, keine persoenlichen Fills |

## Gesicherte On-Chain-Transferbelege

- Gefundene/fetchbare Solana-Signaturen aus Bitget-Events: `2`

| Signatur | Asset | Bitget-Zeit | Status | Chain-Zeit | Aussagekraft |
|---|---|---|---|---|---|
| `46XuA2HVzr...DFEck7xw` | `JUP` | `2025-06-15T07:30:36.015000+00:00` | `confirmed_on_solana_rpc` | `2025-06-15T07:30:12+00:00` | externer Transferbeleg, kein Bot-Fill |
| `5C1y93cUom...J1iCnbG3` | `SOL` | `2025-06-15T07:45:46.005000+00:00` | `confirmed_on_solana_rpc` | `2025-06-15T07:45:21+00:00` | externer Transferbeleg, kein Bot-Fill |

## Quellenbewertung

### Bitget account export / support
- Status: `support_requested`
- Prioritaet: `highest`
- Kann belegen: personal fund flows, personal order/fill history if Bitget provides it, account statements
- Kann nicht belegen: -
- URL: https://www.bitget.site/support/articles/12560603824169

### Bitget private API
- Status: `limited_by_retention`
- Prioritaet: `high`
- Kann belegen: recent private orders/fills/account bills inside API retention windows
- Kann nicht belegen: older bot fills if API retention has expired
- URL: https://www.bitget.com/api-doc/uta/trade/Get-Order-History

### Bitget public market candles
- Status: `collected_now`
- Prioritaet: `supporting`
- Kann belegen: market existed, daily high/low/open/close range, price plausibility
- Kann nicht belegen: personal bot fill, fee, funding, liquidation attribution, internal transfer
- URL: https://www.bitget.com/api-doc/spot/market/Get-History-Candle-Data

### Bitget public futures funding rates
- Status: `collected_now_where_available`
- Prioritaet: `supporting`
- Kann belegen: public funding-rate environment for a futures symbol
- Kann nicht belegen: personal funding paid/received, position size, position holding interval
- URL: https://www.bitget.com/api-doc/classic/contract/market/Get-History-Funding-Rate

### On-chain explorers
- Status: `usable_for_external_flows`
- Prioritaet: `high_for_transfers`
- Kann belegen: deposits to Bitget, withdrawals from Bitget if address/txid known
- Kann nicht belegen: trades inside Bitget, bot internal rebalancing
- URL: https://tronscan.org/ and chain-specific explorers

### Tax-tool caches such as Blockpit/CoinTracking/Koinly/Coinpanda
- Status: `reference_only`
- Prioritaet: `supporting`
- Kann belegen: what the tool had imported at export time, reference event list
- Kann nicht belegen: primary Bitget truth unless raw Bitget records are included and matchable
- URL: https://coinpanda.io/integrations/bitget/

### Tardis.dev / commercial market-data archives
- Status: `optional_market_reference`
- Prioritaet: `low_for_tax_facts`
- Kann belegen: historical public trades/order book/candles
- Kann nicht belegen: which trades belonged to this account or bot
- URL: https://docs.tardis.dev/historical-data-details/bitget

## Schlussfolgerung

Fuer einen belastbaren Steuerreport ist Bitget selbst die Primaerquelle.
Falls Bitget alte Bot-Details nicht mehr liefert, ist der naechstbeste Weg ein Rekonstruktionsbericht aus:

- verifizierten externen Ein-/Auszahlungen,
- vorhandenen Bitget-Tax-/Derivate-/Account-Bill-Events,
- Salden vor/nach Bot-Phasen,
- Funding, Fees, Liquidation und realisierter PnL, soweit belegt,
- Public-Market-Candles nur als Preisrahmen.

Die Public-Market-Daten duerfen nicht genutzt werden, um fehlende einzelne Bot-Trades zu erfinden.
