# Pionex Deposit/Withdraw Match - 2026-05-08

## Scope

User provided the Pionex `deposit-withdraw.csv` content again. This check records how it is represented in the current data model and what it means for the remaining USDT balance breaks.

## Source rows

The active Pionex transfer file contains 6 rows:

| UTC date | type | amount | coin | network | txid |
|---|---:|---:|---|---|---|
| 2021-12-25 16:23:04 | DEPOSIT | 200.00000000 | USDT | TRC20 | b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182 |
| 2022-01-19 12:54:09 | DEPOSIT | 1245.38419000 | USDT | TRC20 | b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa |
| 2022-02-23 05:41:40 | DEPOSIT | 696.82747400 | USDT | TRC20 | a08ff362825ec9a4ce35a3f4803cf1dba32cf1deaae4fc58281001b6a0692566 |
| 2022-02-25 21:35:15 | DEPOSIT | 983.69132300 | USDT | TRC20 | 9542656804be81094930fd1ddb83710f82c54fda18b2691c1ffd57b95d89a132 |
| 2023-06-09 16:19:26 | WITHDRAW | 20530.34420000 | MXC |  | 0x049701b4cddcd5bd5a2f5d3339922d8f4d771543bf51d608738da5f117db2014 |
| 2024-11-22 16:14:05 | WITHDRAW | 0.08995500 | SOL | Mainnet | 4yH7iwag7grZqxEpkWmNFYqKnRypzuPPkMXmwmuWTyUqXGTzwRdrXagsP9BitUftzanhC38FSWV5G8RZijG4JGy9 |

## Binance match result

All 4 USDT deposits are matched to Binance API withdrawals by exact TXID and amount:

| Binance withdrawal UTC | Pionex deposit UTC | coin | amount | match |
|---|---|---|---:|---|
| 2021-12-25 16:19:40 | 2021-12-25 16:23:04 | USDT | 200.00000000 | exact TXID and amount |
| 2022-01-19 12:50:48 | 2022-01-19 12:54:09 | USDT | 1245.38419000 | exact TXID and amount |
| 2022-02-23 05:38:09 | 2022-02-23 05:41:40 | USDT | 696.82747400 | exact TXID and amount |
| 2022-02-25 21:31:55 | 2022-02-25 21:35:15 | USDT | 983.69132300 | exact TXID and amount |

This confirms the external funding chain for these deposits. It does not create additional unexplained USDT because the same value leaves Binance and enters Pionex.

## Pionex USDT balance consequence

For the Pionex-only USDT ledger:

- first active Pionex USDT deposit: `2021-12-25T16:23:04Z`, `+200 USDT`
- first local negative USDT point: `2021-12-28T00:49:12Z`, after a `16.02 USDT` trade out, balance `-13.53043343 USDT`
- larger break: `2022-01-05T11:40:01Z`, after a `346.92882 USDT` trade out, balance `-147.6146934762 USDT`
- before the second deposit on `2022-01-19T12:54:09Z`, Pionex USDT is already negative by `-316.4615903462 USDT`
- after the second deposit, another large trade out at `2022-01-19T12:56:19Z` pushes the local USDT balance to about `-1643.2312211162 USDT`
- worst local Pionex-USDT balance found: `-1643.4055675662 USDT`
- final local Pionex-USDT balance in the model: `+0.8913798065261125 USDT`

## Interpretation

The pasted transfer file is already represented and the four USDT deposits are cleanly explainable from Binance.

The remaining Pionex USDT issue is therefore not a missing external USDT deposit in this file. The most likely causes are:

1. Pionex trading started with an opening inventory or bot allocation not exported as a normal deposit.
2. The bot export represents filled grid legs, but not the initial quote/base allocation used by the bot.
3. The account already held base assets or quote balance before the first exported trade rows.
4. Same-second/fill-order modelling can slightly affect local chronology, but it cannot explain a worst gap of about `1643 USDT`.

For the Pionex-only ledger, a documented opening balance adjustment of about `1643.4055675662 USDT` before the first Pionex trade would be sufficient to prevent USDT from going negative. This should not be added automatically as a final tax fact; it should be opened as a review item and linked to Pionex bot/account-start evidence if available.

## Next action

Create a review candidate for a Pionex opening allocation/start balance, not a duplicate import of the derived CoinTracking or CoinTracker files. Those derived files contain the same economic events and would duplicate trades.
