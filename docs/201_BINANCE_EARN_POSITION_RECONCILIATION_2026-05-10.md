# Binance Earn Position Reconciliation

Stand: 2026-05-10T16:22:31.492256+00:00

## Aktuelle Binance-Bestaende

| Asset | Gesamt | Aufteilung |
|---|---:|---|
| `DOGE` | `2380.09835444` | spot:balance_snapshot=2380.09835444 |
| `JUP` | `16619.9960595` | simple_earn_flexible:balance_snapshot=16619.9960595 |
| `LDJUP` | `15638.13281183` | spot:balance_snapshot=15638.13281183 |
| `SOL` | `11.38806924` | spot:balance_snapshot=1.39855608, simple_earn_locked:balance_snapshot=9.84095708, simple_earn_locked:earn_accrued_reward_snapshot=0.14855608 |
| `TRUMP` | `0.00075605` | spot:balance_snapshot=0.00075605 |

## Binance-Earn-Historie 2025-01-01 bis 2026-05-10

| Endpoint | Rows | Asset totals |
|---|---:|---|
| `simple_flexible_redemption` | `6` | BNSOL=22.32305193, DOGE=5900.09835444, JUP=18507.23806847, TRUMP=0.00151209 |
| `simple_flexible_rewards_realtime` | `172` | BNSOL=0.00000970, DOGE=0.00435444, JUP=72.26237433, TRUMP=50E-9 |
| `simple_flexible_rewards_rewards` | `0` | - |
| `simple_flexible_subscription` | `10` | BNSOL=22.32304223, DOGE=5900.094, JUP=35054.64490723, TRUMP=0.00151204 |
| `simple_locked_redemption` | `0` | - |
| `simple_locked_rewards` | `104` | SOL=0.14855608 |
| `simple_locked_subscription` | `1` | SOL=9.84095708 |

## Persistenz

- Produktpositions-Events upserted: `293`
- Neu: `293`
- Aktualisiert: `0`
- Tabelle: `product_position_events`
- API: `GET /api/v1/product-positions/events`
- Summary-API: `GET /api/v1/product-positions/summary?platform=binance`
- Live-Summary nach Import:
  - Gesamt: `293` Events
  - `non_taxable_principal_movement`: `17`
  - `reward_income_candidate`: `276`

## Bewertung

- `simple_locked_subscription` zeigt die aktive SOL-Locked-Position als Subscription-Historie.
- `simple_locked_rewards` deckt das aktuelle Binance-Reward-Feld fuer SOL rechnerisch ab.
- `simple_flexible_subscription` und `simple_flexible_redemption` zeigen JUP/DOGE/TRUMP/BNSOL Produktbewegungen, die fuer FIFO/Portfolio nicht als Verkauf/Kauf fehlinterpretiert werden duerfen.
- Die Produktpositions-Historie ist als eigene Datenbank-/API-Ebene umgesetzt.
- Reward-Dedupe ist nachgezogen:
  - `docs/202_BINANCE_EARN_REWARD_DEDUPE_2026-05-10.md`
  - `276/276` Reward-Kandidaten sind jetzt gegen `raw_events` belegt.
  - Davon wurden `11` fehlende 2026-Rewards kontrolliert als `binance_api`/`interest` importiert: `JUP=3.13961569`, `SOL=0.00593132`.
- Naechster technischer Schritt: Preis-/EUR-Backfill fuer die neu sichtbaren 2026-Rewards und danach erneuter Jahreslauf/Reconciliation.
