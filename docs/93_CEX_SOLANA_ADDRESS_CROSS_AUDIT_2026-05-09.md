# CEX/Solana Address Cross Audit - 2026-05-09

## Zweck

Abgleich bekannter Binance-/Bitget-Transferadressen gegen lokale Solscan-Transfers und Solana-RPC-Token-Transfer-Owner.

## Summary

- `raw_event_count`: `54810`
- `cex_transfer_event_count`: `215`
- `known_address_count`: `8`
- `solscan_account_transfer_count`: `2745`
- `solana_rpc_counterparty_count`: `1381`

## CEX-Transferquellen

- `binance:deposit`: `81`
- `bitget:deposit`: `40`
- `binance:withdrawal`: `32`
- `bitget:withdrawal`: `28`
- `binance:fiat_deposit`: `15`
- `bitget:automatic_deposit`: `9`
- `binance:fiat_withdrawal`: `7`
- `bitget:automatic_withdrawal`: `3`

## Adressbuch

- Rollen: `{'cex_deposit_address': 63, 'user_or_external_destination_address': 13, 'cex_hot_or_source_address': 2}`
- `138bCXPVfSq7yyTfoDUrVwztPmUr4WGyA7TED9Y41djmF7rjA8y` exchanges `['binance']` events `51` roles `{'cex_deposit_address': 51}` fields `{'Address': 32, 'address': 19}` period `2021-07-27T18:03:02+00:00`..`2022-07-12T07:08:01+00:00`
- `EnbD7GwdYtWgPv5ReEKgCVpExuZsFxiYqjeEM4SgEvhn` exchanges `['binance', 'bitget']` events `12` roles `{'cex_deposit_address': 10, 'user_or_external_destination_address': 2}` fields `{'address': 5, 'Address': 5, 'toAddress': 2}` period `2024-01-12T05:09:33+00:00`..`2025-06-15T07:47:02+00:00`
- `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ` exchanges `['binance']` events `4` roles `{'user_or_external_destination_address': 4}` fields `{'address': 4}` period `2021-12-25T16:19:40+00:00`..`2022-02-25T21:31:55+00:00`
- `wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB` exchanges `['binance']` events `4` roles `{'user_or_external_destination_address': 4}` fields `{'address': 4}` period `2023-05-08T04:43:46+00:00`..`2025-03-23T13:47:35+00:00`
- `133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j` exchanges `['binance']` events `2` roles `{'user_or_external_destination_address': 2}` fields `{'address': 2}` period `2021-06-22T08:57:27+00:00`..`2022-10-14T19:37:01+00:00`
- `1KsYCTB1KgzLUz752NkEj9tnXUguaxaWox` exchanges `['binance']` events `2` roles `{'cex_deposit_address': 2}` fields `{'Address': 1, 'address': 1}` period `2023-06-09T18:30:41+00:00`..`2023-06-09T18:30:41+00:00`
- `A77HErqtfN1hLLpvZ9pCtu66FEtM8BveoaKbbMoZ4RiR` exchanges `['bitget']` events `2` roles `{'cex_hot_or_source_address': 2}` fields `{'fromAddress': 2}` period `2025-06-15T07:30:36.015000+00:00`..`2025-06-15T07:45:46.005000+00:00`
- `0x9516b4e20a2a3d0c9ceebd4fb8238db0e05e84d7` exchanges `['binance']` events `1` roles `{'user_or_external_destination_address': 1}` fields `{'address': 1}` period `2025-01-29T05:54:45+00:00`..`2025-01-29T05:54:45+00:00`

## Solscan Direct/Signature Matches

- Count: `113`
- Match types: `{'address': 106, 'signature_or_owner': 5, 'address_and_signature_or_owner': 2}`
- Flow: `{'out': 107, 'in': 6}`
- Symbols: `{'SOL': 108, 'JUP': 3, 'USDT': 1, 'HNT': 1}`
- Known address roles: `{'user_or_external_destination_address': 420, 'cex_deposit_address': 20, 'cex_hot_or_source_address': 4}`
- CEX target counterparties: `{'A77HErqtfN1hLLpvZ9pCtu66FEtM8BveoaKbbMoZ4RiR': 2, 'EnbD7GwdYtWgPv5ReEKgCVpExuZsFxiYqjeEM4SgEvhn': 2}`

## Solana RPC Owner Matches

- Count: `54`
- Match types: `{'signature_or_owner': 31, 'address': 23}`
- Sides: `{'in': 34, 'out': 20}`
- Symbols: `{'USDC': 14, 'USDT': 13, 'JUP': 12, 'ZEUS': 11, 'IOT': 4}`

## Top Discovered Counterparty Clusters

- `orc1TYY5L4B4ZWDEMayTqu99ikPM9bQo9fqzoaCPP5Q` transfers `290` period `2023-04-25T04:17:52+00:00`..`2026-03-12T19:47:21+00:00` totals `{'HNT': '110.96210232', 'IOT': '1707546.095357'}`
- `4po3YMfioHkNP4mL4N46UWJvBoQDS2HFjzGm1ifrUWuZ` transfers `259` period `2023-04-25T04:17:52+00:00`..`2025-01-29T17:39:46+00:00` totals `{'IOT': '1707546.095357'}`
- `6fvj6rSwTeCkY7i45jYZYpZEhKmPRSTmA29hUDiMSFtU` transfers `75` period `2024-01-18T01:28:25+00:00`..`2025-12-26T21:12:56+00:00` totals `{'IOT': '20344.527612'}`
- `wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB` transfers `53` period `2023-06-29T03:19:47+00:00`..`2025-04-24T20:38:17+00:00` totals `{'IOT': '975744.263563', 'JUP': '4924.846532', 'USDC': '113426.262102', 'USDT': '19228.531027', 'ZEUS': '64475.681009'}`
- `BDs6RPnpJNzmuMNv1z8cDh9cxKFgCxEVDaCfoHZWyvqJ` transfers `31` period `2025-03-02T18:00:50+00:00`..`2026-03-12T19:47:21+00:00` totals `{'HNT': '110.96210232'}`
- `71Y96vbVWYkoVQUgVsd8LSBRRDrgp5pf1sKznM5KuaA7` transfers `27` period `2024-01-18T01:28:39+00:00`..`2024-04-25T10:45:21+00:00` totals `{'MOBILE': '1817.111472'}`
- `72DdMdgLxdSHNRds6vQAZRKq16vSmA8t1QmgkPNnsAPs` transfers `18` period `2024-02-21T07:10:49+00:00`..`2024-03-30T06:28:02+00:00` totals `{'HNT': '30.72377460', 'IOT': '252571.308687', 'USDT': '957.136026'}`
- `71WDyyCsZwyEYDV91Qrb212rdg6woCHYQhFnmZUBxiJ6` transfers `17` period `2024-02-21T07:10:49+00:00`..`2024-03-30T06:28:02+00:00` totals `{'HNT': '107.47899170', 'IOT': '291294.154042', 'USDT': '957.136026'}`
- `8LQyC3HJcsEqRfeAQUQkW2WgVAoXpf2RvfWV2qwpyH7B` transfers `17` period `2024-02-21T07:10:49+00:00`..`2024-03-12T18:22:29+00:00` totals `{'HNT': '4.47105669', 'IOT': '364135.048718'}`
- `WzWUoCmtVv7eqAbU3BfKPU3fhLP6CXR8NCJH78UK9VS` transfers `14` period `2024-04-02T06:46:27+00:00`..`2024-12-06T12:09:15+00:00` totals `{'USDC': '7583.017066'}`
- `A7AjQhocZZvQXQJ5ducRF7gkconjNZfMNCjKguShoe8G` transfers `13` period `2025-12-26T21:12:57+00:00`..`2025-12-26T21:13:31+00:00` totals `{'HNT': '0.53173068'}`
- `EcDs7cZxDHnGtjBuL6E1QC5smfPaBVWbdTShCXyor6H3` transfers `13` period `2024-09-07T19:40:56+00:00`..`2025-01-04T08:32:56+00:00` totals `{'IOT': '835655.976107', 'JUP': '3137.501512', 'USDC': '12528.996814', 'USDT': '5580'}`
- `E8tu7mHJZutXFqCoVocFzeYAMgtDzJirzHaFyHGATos8` transfers `13` period `2024-02-21T07:10:49+00:00`..`2024-03-05T21:51:09+00:00` totals `{'IOT': '291294.154042'}`
- `DFZcDnmEYNUK1khquZzx5dQYiEyjJ3N5STqaDVLZ88ZU` transfers `8` period `2024-11-30T05:42:55+00:00`..`2024-12-06T12:09:15+00:00` totals `{'3NZ9JM...QMJH': '0.01055081', 'USDC': '2710.625177'}`
- `2n6fxuD6PA5NYgEnXXYMh2iWD1JBJ1LGf76kFJAayZmX` transfers `8` period `2024-06-15T19:43:10+00:00`..`2024-11-17T05:29:07+00:00` totals `{'JUP': '998.155415', 'USDC': '800', 'USDT': '8643.066469'}`
- `7o5My3hAKCvZR1iFHf6ZVDXVirbBhU4RcNrPw3ixtJKt` transfers `8` period `2024-02-26T17:33:22+00:00`..`2024-03-05T21:38:02+00:00` totals `{'IOT': '151422.579383'}`
- `8yLTsYZFRT6HbvtKK7vCEDGFHzHH3HtxNguEpuA1MrdA` transfers `7` period `2024-09-18T11:58:52+00:00`..`2024-11-22T16:00:29+00:00` totals `{'ZEUS': '53697.089620'}`
- `g7dD1FHSemkUQrX1Eak37wzvDjscgBW2pFCENwjLdMX` transfers `7` period `2024-03-05T21:35:13+00:00`..`2024-11-12T05:23:40+00:00` totals `{'IOT': '1800148.506648', 'JUP': '500.000000', 'USDT': '11331.780901'}`
- `BvquGcdP4bVHfb6RxBxUSaS2kwm36FPHMadACfYKMp6t` transfers `7` period `2024-03-05T21:33:41+00:00`..`2024-08-29T11:25:56+00:00` totals `{'HNT': '318.06600744', 'IOT': '1116610.538644'}`
- `9KXNt6J3ZoDwRbuy1johwQxmEznFPxo9ye73hNgCc91q` transfers `7` period `2024-03-05T21:24:25+00:00`..`2024-03-30T06:28:02+00:00` totals `{'HNT': '136.93620778', 'IOT': '9444.707707', 'USDT': '957.136026'}`

## Bewertung

- Direkte Solscan-zu-CEX-Matches gefunden: 113.
- Solana-RPC-Owner/Token-Account-Matches gegen bekannte CEX-Adressen gefunden: 54.
- Der Audit trennt direkte Adressmatches, Signaturmatches und Owner-Matches, weil Solana-Token-Accounts nicht immer die eigentliche Gegenpartei-Adresse sind.
- Groesster wiederkehrender Solana-Counterparty-Cluster: orc1TYY5L4B4ZWDEMayTqu99ikPM9bQo9fqzoaCPP5Q mit 290 Transfers von 2023-04-25T04:17:52+00:00 bis 2026-03-12T19:47:21+00:00.
- Naechster Schritt: bekannte CEX-Adresscluster als Evidence-Layer markieren und nur sicher gematchte Blockpit-Referenzen als reference_import_only pruefen.
