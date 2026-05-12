# All-Token Current Balance Reconciliation

Stand: 2026-05-10 15:00 UTC

## Umfang

Live-Quellen:

- Binance via Secret-Store: Spot + Simple Earn Flexible + Simple Earn Locked
- Bitget via Secret-Store
- Pionex via Secret-Store
- Solana Wallet `wBrPoi...JbV2oB` via RPC

Modellquelle:

- Port `8000`: `GET /api/v1/portfolio/lot-aging?as_of_utc=2026-12-31T23:59:59Z`

## Ergebnis

Die anderen Tokens waren noch nicht sauber final abgeglichen. Der aktuelle Lauf zeigt drei Klassen:

1. Echte Reconciliation-Gaps: Modellbestand und Livebestand weichen fachlich ab.
2. Binance-Earn/Produktpositionen: muessen historisch in den Steuerlauf integriert werden, nicht nur als Live-Snapshot.
3. Solana-Mint-Alias-Probleme: dieselbe Mint wird im Modell als Kurzadresse, live aber als Symbol angezeigt. Die ersten zentralen Aliases (`CBDC`, `SHARK`) sind umgesetzt.

## Hohe Abweichungen

| Asset | FIFO-Modell | Live verifiziert | Modell minus Live | Erste Bewertung |
|---|---:|---:|---:|---|
| `JUP` | `1816.84176164` | `16620.058257276835` | `-14803.216495636835` | Binance Simple Earn/Flexible und LDJUP/JUP-Kontext pruefen |
| `LDJUP` | `0` | `15638.13281183` | `-15638.13281183` | Binance Produkt-/Derivative-Token, nicht blind mit JUP mergen |
| `SOL` | `3.975449536` | `11.624339414` | `-7.648889878` | Binance Locked Earn/Staking fehlt historisch im FIFO |
| `ADA` | `415.880551900` | `854.01136460` | `-438.130812700` | Binance Livebestand hoeher als FIFO |
| `DOGE` | `4004.98809626` | `2380.09835444` | `1624.88974182` | FIFO hoeher als Live, spaetere Disposal-/Transferkette pruefen |
| `USDT` | `1702.27119503` | `0.8958693321034125` | `1701.3753256978965875` | FIFO hoeher als Live, historischer Stable-Gap bleibt relevant |
| `USDC` | `463.02137333` | `0.18978733` | `462.83158600` | FIFO hoeher als Live |
| `SHARK` | `1641.002014` | `963.536668` | `677.465346` | Alias jetzt normalisiert; verbleibende Mengendifferenz echt pruefen |
| `HNT` | `139.88341487` | `71.6878967500000000` | `68.1955181200000000` | FIFO hoeher als Live, Legacy/Solana-Kontext pruefen |
| `BTC` | `0.026890670` | `0.0056533904850000` | `0.0212372795150000` | FIFO hoeher als Live |
| `ETH` | `0.04063986` | `0.04729447` | `-0.00665461` | Live hoeher als FIFO |
| `BNB` | `0.26119523` | `0.24819450` | `0.01300073` | kleine Differenz |
| `XRP` | `94.12311274` | `106.37033860` | `-12.24722586` | Live hoeher als FIFO |
| `TRX` | `0` | `103.32031325` | `-103.32031325` | Livebestand fehlt im FIFO |
| `XLM` | `0` | `100.22698372` | `-100.22698372` | Livebestand fehlt im FIFO |
| `PEPE` | `243810.76` | `102177.59` | `141633.17` | FIFO hoeher als Live |

## Alias-/Anzeige-Probleme, nicht sofort steuerlich buchen

| Modellanzeige | Liveanzeige | Modell | Live | Bewertung |
|---|---|---:|---:|---|
| `CBDC` | `CBDC` | `4202343.53` | `4202343.53` | nach zentralem Alias-Fix deckungsgleich |
| `SHARK` | `SHARK` | `1641.002014` | `963.536668` | nach Alias-Fix noch echte Mengendifferenz |
| `EUKMXS...TEAV` | `EUKMXS...TEAV` | `1` | `107000059` | wahrscheinlich Spam-/Mint-Sonderfall, nicht steuerlich auto-korrigieren |
| `4T4TMH...2RGU` | `4T4TMH...2RGU` | `1` | `88044724` | wahrscheinlich Spam-/Mint-Sonderfall, nicht steuerlich auto-korrigieren |
| `HJGKKK...QNQN` | `HJGKKK...QNQN` | `1` | `32434` | wahrscheinlich Spam-/Mint-Sonderfall, nicht steuerlich auto-korrigieren |
| `CM8VSE...ZIF4` | `CM8VSE...ZIF4` | `1000000000` | `1000000000` | deckungsgleich |

## Live-Bestaende je Quelle, Beispiele

Binance:

- `SOL`: Spot `1.39855608`, Locked Earn Principal `9.84095708`, accrued Reward-Feld `0.14855608`
- `JUP`: Simple Earn Flexible `16619.96448226`
- `LDJUP`: Spot `15638.13281183`
- `ADA`: Spot `854.01136460`
- `DOGE`: Spot `2380.09835444`
- `BTC`: Spot `0.00565218`
- `ETH`: Spot `0.04729447`

Bitget:

- `BTC`: `0.000000304`
- `HNT`: `0.00062275`
- `USDT`: `0.000000006884`
- `EUR`: `0.00026652`

Pionex:

- `BTC`: `0.000000906485`
- `JUP`: `0.093774016835`
- `USDT`: `0.8958683252194125`
- `MXC`: `0.00002`

Solana Wallet:

- Native `SOL`: `0.236270174`
- `HNT`: `71.687274`
- `CBDC`/`2KFZCK...FV2J`: `4202343.53`
- `USDC`: `0.00099`
- `USDT`: `0.000001`
- `JUP`: `0.000001`
- diverse Spam-/unknown SPL Tokens

## Naechste Umsetzung

1. Weitere Spam-/Mint-Sonderfaelle pruefen und entweder als Ignored Token oder expliziter Alias dokumentieren.
2. Binance Earn/Staking historisch importieren:
   - Simple Earn Flexible Positionen
   - Simple Earn Locked Positionen
   - RewardsRecord
   - Produkt-/Token-Uebergaenge wie `LDJUP` vs `JUP`
3. Danach erneuter All-Token-Abgleich.
4. Erst danach steuerliche Jahreslaeufe neu erzeugen.

## Binance-Earn-Audit nachgezogen

Reproduzierbarer Detailreport:

- `docs/201_BINANCE_EARN_POSITION_RECONCILIATION_2026-05-10.md`
- `var/binance_earn_position_reconciliation_2026-05-10.json`

Kernergebnis aus Binance API:

| Bereich | Rows | Summe |
|---|---:|---|
| `simple_locked_subscription` | `1` | `SOL=9.84095708` |
| `simple_locked_rewards` | `104` | `SOL=0.14855608` |
| `simple_flexible_subscription` | `10` | `JUP=35054.64490723`, `DOGE=5900.094`, `BNSOL=22.32304223`, `TRUMP=0.00151204` |
| `simple_flexible_redemption` | `6` | `JUP=18507.23806847`, `DOGE=5900.09835444`, `BNSOL=22.32305193`, `TRUMP=0.00151209` |
| `simple_flexible_rewards_realtime` | `172` | `JUP=72.26237433`, `DOGE=0.00435444`, `BNSOL=0.00000970`, `TRUMP=0.00000005` |

Bewertung: Diese Produktbewegungen duerfen nicht pauschal als steuerlicher Verkauf/Kauf gebucht werden. Sie brauchen eine eigene Produktpositions-Historie; nur Reward-Zufluesse sind steuerlich als Zufluss-/Betriebseinnahmen-Kandidaten zu behandeln.

## Validierung

- Binance/Bitget/Pionex CEX-Calls ohne Keys im Body laufen ueber Secret-Store.
- Binance Balance Preview enthaelt jetzt Spot + Simple Earn Flexible + Simple Earn Locked.
- Solana Wallet Snapshot wurde live abgefragt.
- Connector-Tests nach Binance-Earn-Fix: `29 passed`.
- Alias-Fix:
  - `src/tax_engine/connectors/token_metadata.py`: `CBDC` und `SHARK` als bekannte Mints ergaenzt.
  - Port `8000` nach Restart: `CBDC 4202343.53`, `SHARK 1641.002014`; die Kurzadressen `2KFZCK...FV2J` und `SHARKS...NR1S` erscheinen nicht mehr im Lot-Aging.
  - Test: `test_portfolio_lot_aging_uses_known_solana_mint_symbols`.
- Binance-Earn-Audit:
  - Script: `scripts/binance_earn_position_reconciliation_20260510.py`
  - `python3 -m py_compile scripts/binance_earn_position_reconciliation_20260510.py`
  - `PYTHONPATH=src python3 scripts/binance_earn_position_reconciliation_20260510.py`
  - Persistiert `293` Events in `product_position_events`.
  - Live API: `GET /api/v1/product-positions/summary?platform=binance` -> `17` Principal-Bewegungen, `276` Reward-Kandidaten.
- Binance-Earn-Reward-Dedupe:
  - Script: `scripts/binance_earn_reward_candidate_dedupe_20260510.py`
  - Report: `docs/202_BINANCE_EARN_REWARD_DEDUPE_2026-05-10.md`
  - Ergebnis nach kontrolliertem Nachimport: `276/276` Reward-Kandidaten in `raw_events` belegt, offene Kandidaten `0`.
  - Fehlende 2026-Rewards wurden importiert: `11` Events, `JUP=3.13961569`, `SOL=0.00593132`.
  - Preisbackfill fuer `JUP,SOL` 2026-05-03 bis 2026-05-10: `15` Tagespreise aus `coingecko_history`.
  - Steuerjahre 2020-2026 danach neu berechnet: `docs/190_CURRENT_TAX_RUNS_2026-05-10.md`.
