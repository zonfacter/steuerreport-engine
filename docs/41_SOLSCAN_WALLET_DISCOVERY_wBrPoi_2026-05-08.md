# Solscan Wallet Discovery wBrPoi 2026-05-08

- Wallet: `wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB`
- Solscan Account-Transactions gespeichert: `2372`
- Solscan Account-Transfers gespeichert: `2745`
- Bisheriger `solana_rpc`-Import fuer diese Wallet: `2206` Signaturen
- Fehlende Signaturen gegen bisherigen Import: `170`
- Davon mit Transfer-Zeilen in `account/transfer`: `168`
- Alle fehlenden Signaturen haben Solscan-Status: `{'Success': 170}`

## Verteilung fehlender Signaturen
- `2023`: `12`
- `2024`: `140`
- `2025`: `9`
- `2026`: `9`

## Top Programme in fehlenden Signaturen
- `jupiter`: `122`
- `spl-token`: `38`
- `phoenix_v1`: `30`
- `whirlpool`: `21`
- `lifinity_amm_v2`: `18`
- `amm_v3`: `17`
- `ComputeBudget`: `12`
- `system`: `10`
- `mpl_token_metadata`: `8`
- `openbook_v2`: `6`
- `lb_clmm`: `4`
- `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo`: `4`
- `treasury_management`: `2`
- `raydium_amm`: `2`
- `SaberStableSwap`: `1`

## Token-Adressen in fehlenden Transfer-Zeilen
- `JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN`: `105`
- `Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB`: `74`
- `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`: `60`
- `iotEVVZLEywoTn1QdwNPddxPWszn3zFhEot3MfL9fns`: `54`
- `hntyVP6YFm1Hg25TN9WGLqM12b8TQmcknKrdu1oxWux`: `46`
- `So11111111111111111111111111111111111111111`: `36`
- `ZEUS1aR7aX8DFFJf5QjWj2ftDDdNTroMNGo8YoQm3Gq`: `36`
- `mb1eu7TzEc71KxDpsmsKoucSSuuoGLv1drys1oP2jh6`: `10`
- `DvoPSyDUou8qQWRK4K1hipN6wtkGk2PW1CfX8kUVvR4K`: `3`
- `SHARKSYJjqaNyxVfrpnBN9pjgkhwDhatnMyicWPnr1s`: `3`
- `jupSoLaHXQiZZTSfEWMTRRgpnyFm8f6sZdosWBjx93v`: `3`
- `UrAE9vVdrWxncikcCRp7TgNqEsArFtP22iXzH7gpump`: `3`
- `7rpaXCsA3BiKAuoQtj3dDsmkbLhefqnbaCpAUNBGC3KQ`: `2`
- `5MFem7LyTSgP2x3TVJxhxLENxSLRW6DqR3PspJXVUeTF`: `2`
- `2KFZCkfxj1Us8YRQZa5vktSxy3GPzFZvVhWj91n8Fv2J`: `2`

## Bewertung
- Der bisherige Solana-Import ist nicht vollstaendig: Solscan findet `170` erfolgreiche Wallet-Signaturen, die noch nicht als `solana_rpc`-Events importiert sind.
- Schwerpunkt der Luecke ist `2024` mit `140` Signaturen, vor allem Jupiter-/DEX-Aktivitaeten.
- Diese Signaturen sind jetzt lokal in `solscan_account_transactions`, `solscan_account_transfers` und via `solscan_transactions` als Detaildaten gesichert.
- Naechster Schritt: fehlende Signaturen deterministisch in steuerrelevante Raw-Events umwandeln oder als nicht-steuerrelevante technische Wallet-Aktivitaet markieren.

## Erste fehlende Signaturen
- `2023-04-26T14:42:15+00:00` `ZU1XDg1ftKL9RSvv5qWuHaUE76YEfHuWVoWRTpPdo15h8unXbwfE4CBhdjV6jSbEKjvtx6sTNAGTUvat3Ks8XFk` programs=['jupiter']
- `2023-04-26T14:56:02+00:00` `3hJhdTxRiyyd9XbdxwNsWyEy8BYXLHDL1GiQTp7B1hS1vTrc3fpJpVgp8tBufSDCZoojLg5utfoZzNS2TQWd6Cew` programs=['jupiter']
- `2023-04-26T15:01:18+00:00` `9gNh4JNVkZhTX9DwwUGeZBBXLK8iDUXjDY3J3eC1kYLCS7D2QyaJ7BgJFkSrJrVaHJkwMRgpFe1UA4pa8wNbj35` programs=['jupiter']
- `2023-04-26T15:15:37+00:00` `5vwXTJV95QjZsfCohbQVT2Wdf9uZjyrAe1ZUWon4aNMTqvGzPkTPPmmqHHwbsuFeXKXYqcSpWkVeZNrGzCSn91r4` programs=['jupiter']
- `2023-05-08T04:52:01+00:00` `4471HtUnUgPzhybxwPsGVfXmi8wHGrZioz6kiG4Gq5goy7QLv7s7RKEdkNaQKaRknwiEAtyoTerJzLKLyS5YfwDV` programs=['spl-token', 'mpl_token_metadata', 'mpl_token_metadata']
- `2023-05-14T06:34:59+00:00` `5YfsjV8iKP8rcTJQMCJtJYanEM6TePU4ERPmd2neHpcpfheJTv9c5eboLEq5SqeTSRKwsejRU4FM7ejVd9i7BAvy` programs=['spl-token', 'mpl_token_metadata', 'mpl_token_metadata']
- `2023-07-15T09:48:46+00:00` `2HfWUAgCHDrY2yujo6a6ZzsYejDzXQbZzPfV3oE2RhUPTDbNThrtiD2VkATnwHFBfvBjGh7B4AhVF4u6wa8Dgnhq` programs=['treasury_management', 'spl-token']
- `2023-07-30T06:59:13+00:00` `5LbqXnxbEfXmPegwuURc4CAjHa7RsufqEpreUssrA8ip9ydzGKUiPaDGJp6DJTu8iGzys8bSDejMHYf9p3AD9hyX` programs=['treasury_management', 'spl-token', 'whirlpool', 'whirlpool']
- `2023-08-01T06:35:02+00:00` `qhWcN51yoSr2pEyvwqD54g4cDC834osrV6Zj6TrNxTaFSnG3ewoq1xudzpmXFbmSRqNDMMQyPzFRB472Rbyrojh` programs=['spl-token', 'mpl_token_metadata', 'mpl_token_metadata']
- `2023-08-01T06:43:43+00:00` `3dC6TFS8frjSp4Pg7qp3LuKcW6iSttuqW72WCvKYeVYsp5PXahzxw2g4eq3M3HaAeXAZXGkzQbyEVQCcQZhya3er` programs=['spl-token', 'mpl_token_metadata', 'mpl_token_metadata']
- `2023-09-30T06:28:50+00:00` `3zCES1wbtM3CugrocGYLGuY1V6k7Afch4oiuDhjWn9NueXYerohNZD5SCcNcx11SNRMaoVmj4kradtMfHjPYYUQ6` programs=['jupiter']
- `2023-11-11T06:57:33+00:00` `AhswTzgXWrFZAgXQ3J7K8k7ixnSdGZ8CiPHU1tLj3DbRTRhhiVbPptAmzQag5nLXBP2GC8S7eJyDKFmRio63fPP` programs=['jupiter']
- `2024-02-15T07:28:32+00:00` `JZnqBEz2UTMcE8th89Ru7dL1e7QaULMUWbGRwCoFeWLk22fqxKzcykfeGZcoj1naeUq97eosHxnT27dYtes7TqK` programs=['jupiter']
- `2024-02-15T07:35:47+00:00` `5RdvdtwqSqDihupB2jNrTFEXDABqBsYL6ir9cnz331f8yCAoX4aym4mKjUSmkK6b6tThoPX1XfwXZxgnA2bFjP7Y` programs=['jupiter']
- `2024-02-15T10:58:42+00:00` `3bEvx2EvmvRBq9PUeDbZbY4DtzyqpS18WcdC2fEBGXAP5TsLjdBDbV5CDUbiw4bbDQSmycjQvGcbM5mXGQJ2LA95` programs=['jupiter']
- `2024-02-15T13:34:23+00:00` `3PH5Uhz89j55phCAGUAhPAbBU7jGVDezQvhTgjPAtdm7rHAZZCbckS3AWo2nVtShDKdYGNMpHJfDPcjyvMsM9txb` programs=['jupiter']
- `2024-02-23T21:01:15+00:00` `5AvcbkMazFT2wT7Sjic1tX539miJAP2isCAUcDHxYSuZq1D53QPGZYbu9AonuBNxrZ29nAderiDZuS3q4MJjtm5x` programs=['jupiter']
- `2024-02-26T17:33:40+00:00` `37BwYoBEFJtB2osNxswfZnTGpPU4Qz9jAnA2T5Y3UXd5aFep6TtETLdPZkAxZkYMzjFr5kbs1KkbqJEVeykthLGa` programs=['jupiter']
- `2024-02-28T17:14:05+00:00` `HNvAtZpLjCjGiSKfMkxCvzZHH89rG9KzjqprChJomqh3wbEjZsEYMSa6SZrFkyrucyk8WxoA9NDERAEmbanpRsA` programs=['jupiter']
- `2024-03-04T20:45:38+00:00` `8sA2dex7fEtHwYDe9PrMyXQwXGf1tSqmkcgLLF8JqTRB8tVNZ2Ujwtu3EQ5rBVLSuRJinhti1exkM3aUMSMYuVd` programs=['jupiter']
- `2024-03-07T15:50:43+00:00` `4dbDVUjpoi5cNtrP6njRT4gnTacwmCUfXfPv4gHpw1CxC4dZoyazFzn3JteGK2Tkos2AxFiCuEfxEg4JjV4VdPaq` programs=['jupiter']
- `2024-03-07T16:01:57+00:00` `5qNKVpavLbwCM9pGVTfFn6XokMFgAMnX8D1KETCjukcLkxMkYxv28UDUnykidmboNzMWiuENs3yKKFFk2cUiMcUk` programs=['jupiter']
- `2024-03-10T00:01:07+00:00` `41TGXKfU1Fsz8uWoPp1vy1UesM3ALWwwg1DeYPJU4VhN6SYPyCVcqZ2YopYd36pPTX9ESDaCGS3qyeeGB7YaxWGE` programs=['jupiter']
- `2024-03-10T16:24:52+00:00` `7rZG16JJpx3cyir3qXunEkw3dGozyfLa99iTGJftv3XJVbUfizh4sBR555vRszTFmBeEUPXAS5KRQ21mKo286Xe` programs=['jupiter']
- `2024-03-11T08:59:59+00:00` `1KBC1BZdUJKzUC83fC8JN9ruS1gUmjV3DD4otKGcvV7auKNfm2QfAgzFizvnXVLq1Gw5KKmPGApeHwff5MM4TU3` programs=['jupiter']
