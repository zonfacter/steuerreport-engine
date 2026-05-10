# Binance BTC 2023 VET/WIN Blockpit Reconstruction - 2026-05-09

## Ergebnis

- Modus: `execute`
- Importierte Events: `4`
- Duplikate: `0`
- Bestehende Rekonstruktionszeilen: `0`

## Rekonstruktionszeilen

- `2023-05-02T04:12:16+00:00` `internal_balance_adjustment` `100.01639287 VET` reference `e4bd699f20bd9bd424a100e9f88aae4e6786a8802923cd9e3b88e494930367eb`
- `2023-05-02T04:12:17+00:00` trade `buy` `0.00007565 BTC` gegen `100.01639287 VET` reference `8dcccb77901b08ca24470d75a1716fd9be240c2fb52f589e49a2d9543699f92e`
- `2023-05-02T04:12:35+00:00` `internal_balance_adjustment` `14149.30730362 WIN` reference `b4085bf368d17fb19b863bbee292c965492a403b6c9d501142c7d2960f2d7daa`
- `2023-05-02T04:12:36+00:00` trade `buy` `0.00004088 BTC` gegen `14156.61280211 WIN` reference `6c8a5d5156ae9a027d72ceb30b937003d6da79564c91ceca619b5bf95d291484`

## Bewertung

- The prior BTC candidate audit blocked VET/WIN -> BTC because the small VET/WIN source amounts were not active.
- Blockpit Binance references contain matching Auto-Balancing In rows immediately before both trades.
- This package imports only those two auto-balancing source rows and the two BTC trades.
- The package adds a net 0.00011653 BTC before the June 2023 SOL buys and should not shift the gap into VET/WIN.
