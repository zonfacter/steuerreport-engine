# Tron Pionex Deposit Address Audit - 2026-05-08

## Scope

Question: if all directions of the on-chain transfers are visible, can we find whether additional earlier funds went directly to the Pionex account?

Known Pionex TRC20 deposit address derived from the Binance -> Pionex USDT deposits:

`TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ`

USDT contract on Tron:

`TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`

## Method

New reusable audit script:

`scripts/tron_trc20_address_audit.py`

Executed:

```bash
python3 scripts/tron_trc20_address_audit.py \
  --address TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ \
  --contract TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t \
  --raw-out var/tron_pionex_deposit_address_usdt_raw_2026-05-08.json \
  --summary-out var/tron_pionex_deposit_address_usdt_summary_2026-05-08.json

python3 scripts/tron_trc20_address_audit.py \
  --address TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ \
  --raw-out var/tron_pionex_deposit_address_all_trc20_raw_2026-05-08.json \
  --summary-out var/tron_pionex_deposit_address_all_trc20_summary_2026-05-08.json
```

Verification:

```bash
python3 -m py_compile scripts/tron_trc20_address_audit.py
```

## Result

All TRC20 transfers for the known Pionex deposit address:

- count: `8`
- first transfer: `2021-12-25T16:20:48+00:00`
- last transfer: `2022-02-25T21:37:09+00:00`
- token total: `USDT in 3125.902987`, `USDT out 3125.902987`

No earlier TRC20 transfer was returned for this address.

## Transfer list

| UTC timestamp | direction | amount | asset | from | to | tx |
|---|---:|---:|---|---|---|---|
| 2021-12-25T16:20:48+00:00 | in | 200.000000 | USDT | TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr | TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ | b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182 |
| 2021-12-25T16:24:21+00:00 | out | 200.000000 | USDT | TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ | TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU | 2eb9fa1ede88875ccf0b5adf46a516baff3c54417303738fc4147f8bab8e08ac |
| 2022-01-19T12:51:36+00:00 | in | 1245.384190 | USDT | TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr | TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ | b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa |
| 2022-01-19T12:55:51+00:00 | out | 1245.384190 | USDT | TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ | TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU | 182678a352539313e9c7af909585f3912dbd1268aaf3235272fa1faaab6e180d |
| 2022-02-23T05:38:57+00:00 | in | 696.827474 | USDT | TNXoiAJ3dct8Fjg4M9fkLFh9S2v9TXc32G | TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ | a08ff362825ec9a4ce35a3f4803cf1dba32cf1deaae4fc58281001b6a0692566 |
| 2022-02-23T05:43:30+00:00 | out | 696.827474 | USDT | TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ | TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU | 42e2446e9afabe998e891157f66931f008e3385c68b911ef7cedddf1f4919b85 |
| 2022-02-25T21:32:36+00:00 | in | 983.691323 | USDT | TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr | TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ | 9542656804be81094930fd1ddb83710f82c54fda18b2691c1ffd57b95d89a132 |
| 2022-02-25T21:37:09+00:00 | out | 983.691323 | USDT | TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ | TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU | 56cb651c8175b1fad0d8d8cfcbbbd21c391b3d513a61de0208b8178af3f44dd9 |

Tronscan transaction details identify the senders as Binance hot wallets for the known deposits:

- `TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr`: Binance-Hot 5
- `TNXoiAJ3dct8Fjg4M9fkLFh9S2v9TXc32G`: Binance-Hot 4

## Interpretation

This confirms both directions for the known Pionex TRC20 deposit address:

1. Binance hot wallet sends USDT to the user-specific Pionex deposit address.
2. The Pionex deposit address sweeps the exact same USDT amount shortly afterwards to `TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU`.

There are no additional earlier TRC20 deposits on this known address. Therefore, the Pionex opening-gap is not explained by an earlier direct TRC20 transfer to this address.

Remaining possibilities:

1. A different Pionex deposit address was used for older deposits.
2. The missing start value is an internal Pionex bot allocation/opening balance and not an on-chain deposit.
3. The missing funding came in via another network/asset and was converted internally before the exported trade history.
4. The Pionex export starts after an already existing bot inventory.

## Next check

Use the same script for any additional Pionex deposit address found in older screenshots, account statements, Pionex export files, email confirmations, or Binance withdrawal targets.
