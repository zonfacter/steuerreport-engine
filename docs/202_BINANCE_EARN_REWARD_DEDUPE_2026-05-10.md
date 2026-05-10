# Binance Earn Reward Dedupe

Stand: 2026-05-10T16:27:58.941181+00:00

## Ziel

Die Tabelle `product_position_events` enthaelt Binance-Earn-Rewards zunaechst nur als Kandidaten. Dieses Audit prueft, welche Kandidaten bereits als steuerlich relevante Rohereignisse in `raw_events` vorhanden sind.

## Match-Regel

- Asset gleich, Betrag exakt gleich, Zeitdifferenz maximal `3600` Sekunden.
- Rohereignisse werden nach Review-Actions gelesen, damit bereits ausgeschlossene Referenzen nicht erneut zaehlen.
- Kein automatischer Import in diesem Schritt; Ergebnis ist ein Beleg- und Entscheidungsprotokoll.

## Ergebnis

- Reward-Kandidaten: `276`
- Bereits in `raw_events` gefunden: `276`
- Noch offen: `0`

### Gefundene Rewards nach Quelle

| Quelle/Event-Type | Anzahl |
|---|---:|
| `binance_api:asset_dividend` | `35` |
| `binance_api:interest` | `11` |
| `blockpit:interest` | `230` |

### Gefundene Reward-Mengen

| Asset | Menge |
|---|---:|
| `BNSOL` | `0.000009700` |
| `DOGE` | `0.00435444` |
| `JUP` | `72.26237433` |
| `SOL` | `0.14855608` |
| `TRUMP` | `50E-9` |

### Offene Reward-Mengen

| Asset | Menge |
|---|---:|

### Offene Rewards nach Jahr/Asset

| Jahr | Asset | Anzahl | Menge |
|---|---|---:|---:|

## Naechste Umsetzung

- Kandidaten mit Match bleiben reine Produktpositions-Referenz und duerfen nicht erneut als Einkommen importiert werden.
- Offene Kandidaten sind nach dem kontrollierten Import bei `0`.
- Preis-/USD-Backfill fuer die importierten 2026-Reward-Tage wurde ausgefuehrt:
  - `PYTHONPATH=src python3 scripts/crypto_price_backfill_usd.py --start-date 2026-05-03 --end-date 2026-05-10 --assets JUP,SOL --provider auto --max-requests 20 --sleep-seconds 0 --timeout-seconds 30`
  - Ergebnis: `15` Tagespreise aus `coingecko_history` gecached.
- Fuer Principal-Bewegungen bleibt `tax_treatment=non_taxable_principal_movement`; sie duerfen FIFO nicht als Kauf/Verkauf veraendern.
