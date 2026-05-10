# Solscan Missing Event Preview 2026-05-08

- Wallet: `wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB`
- Bekannte lokale Solana-RPC-Signaturen: `2206`
- Solscan Account-Transactions: `2372`
- Fehlende Signaturen: `170`
- Vorgeschlagene Event-Zeilen: `347`
- JSON: `var/solscan_missing_event_preview_wBrPoi_2026-05-08.json`

## Klassen
- `dex_swap_or_route`: `152`
- `mixed_transfer`: `11`
- `technical_account_or_metadata`: `2`
- `transfer_in_or_airdrop`: `5`

## Jahr/Klasse
- `2023`: dex_swap_or_route=7, mixed_transfer=5
- `2024`: dex_swap_or_route=137, mixed_transfer=3
- `2025`: dex_swap_or_route=7, mixed_transfer=2
- `2026`: dex_swap_or_route=1, mixed_transfer=1, technical_account_or_metadata=2, transfer_in_or_airdrop=5

## Bewertung
- Diese Datei ist ein Preview, noch kein Import.
- `dex_swap_or_route` wird als Netto-Bewegung je Token vorgeschlagen; komplexe Routen koennen mehrere In-/Out-Zeilen erzeugen.
- `technical_account_or_metadata` erzeugt keine steuerliche Event-Zeile.
- Vor dem produktiven Import sollte die Auswirkung auf negative Bestände per Dry-Run geprüft werden.

## Erste vorgeschlagene Zeilen
- `2023-04-26T14:42:15+00:00` `swap_out_aggregated` `out` `424.8894859 HNT` tx=`ZU1XDg1ftKL9RSvv5qWuHaUE76YEfHuWVoWRTpPdo15h8unXbwfE4CBhdjV6jSbEKjvtx6sTNAGTUvat3Ks8XFk`
- `2023-04-26T14:42:15+00:00` `swap_in_aggregated` `in` `347279.588497 IOT` tx=`ZU1XDg1ftKL9RSvv5qWuHaUE76YEfHuWVoWRTpPdo15h8unXbwfE4CBhdjV6jSbEKjvtx6sTNAGTUvat3Ks8XFk`
- `2023-04-26T14:56:02+00:00` `swap_in_aggregated` `in` `514.50311342 HNT` tx=`3hJhdTxRiyyd9XbdxwNsWyEy8BYXLHDL1GiQTp7B1hS1vTrc3fpJpVgp8tBufSDCZoojLg5utfoZzNS2TQWd6Cew`
- `2023-04-26T14:56:02+00:00` `swap_out_aggregated` `out` `409144.989078 IOT` tx=`3hJhdTxRiyyd9XbdxwNsWyEy8BYXLHDL1GiQTp7B1hS1vTrc3fpJpVgp8tBufSDCZoojLg5utfoZzNS2TQWd6Cew`
- `2023-04-26T15:01:18+00:00` `swap_out_aggregated` `out` `939.39259932 HNT` tx=`9gNh4JNVkZhTX9DwwUGeZBBXLK8iDUXjDY3J3eC1kYLCS7D2QyaJ7BgJFkSrJrVaHJkwMRgpFe1UA4pa8wNbj35`
- `2023-04-26T15:01:18+00:00` `swap_in_aggregated` `in` `733904.811832 IOT` tx=`9gNh4JNVkZhTX9DwwUGeZBBXLK8iDUXjDY3J3eC1kYLCS7D2QyaJ7BgJFkSrJrVaHJkwMRgpFe1UA4pa8wNbj35`
- `2023-04-26T15:15:37+00:00` `swap_in_aggregated` `in` `924.33312667 HNT` tx=`5vwXTJV95QjZsfCohbQVT2Wdf9uZjyrAe1ZUWon4aNMTqvGzPkTPPmmqHHwbsuFeXKXYqcSpWkVeZNrGzCSn91r4`
- `2023-04-26T15:15:37+00:00` `swap_out_aggregated` `out` `733904.811832 IOT` tx=`5vwXTJV95QjZsfCohbQVT2Wdf9uZjyrAe1ZUWon4aNMTqvGzPkTPPmmqHHwbsuFeXKXYqcSpWkVeZNrGzCSn91r4`
- `2023-05-08T04:52:01+00:00` `token_transfer` `in` `1 Dsa1VH...Gjdu` tx=`4471HtUnUgPzhybxwPsGVfXmi8wHGrZioz6kiG4Gq5goy7QLv7s7RKEdkNaQKaRknwiEAtyoTerJzLKLyS5YfwDV`
- `2023-05-08T04:52:01+00:00` `token_transfer` `out` `74 HNT` tx=`4471HtUnUgPzhybxwPsGVfXmi8wHGrZioz6kiG4Gq5goy7QLv7s7RKEdkNaQKaRknwiEAtyoTerJzLKLyS5YfwDV`
- `2023-05-08T04:52:01+00:00` `sol_transfer` `out` `0.01615416 SOL` tx=`4471HtUnUgPzhybxwPsGVfXmi8wHGrZioz6kiG4Gq5goy7QLv7s7RKEdkNaQKaRknwiEAtyoTerJzLKLyS5YfwDV`
- `2023-05-14T06:34:59+00:00` `token_transfer` `in` `1 7rpaXC...C3KQ` tx=`5YfsjV8iKP8rcTJQMCJtJYanEM6TePU4ERPmd2neHpcpfheJTv9c5eboLEq5SqeTSRKwsejRU4FM7ejVd9i7BAvy`
- `2023-05-14T06:34:59+00:00` `token_transfer` `out` `34687.714944 IOT` tx=`5YfsjV8iKP8rcTJQMCJtJYanEM6TePU4ERPmd2neHpcpfheJTv9c5eboLEq5SqeTSRKwsejRU4FM7ejVd9i7BAvy`
- `2023-05-14T06:34:59+00:00` `sol_transfer` `out` `0.01615416 SOL` tx=`5YfsjV8iKP8rcTJQMCJtJYanEM6TePU4ERPmd2neHpcpfheJTv9c5eboLEq5SqeTSRKwsejRU4FM7ejVd9i7BAvy`
- `2023-07-15T09:48:46+00:00` `token_transfer` `in` `23.86069708 HNT` tx=`2HfWUAgCHDrY2yujo6a6ZzsYejDzXQbZzPfV3oE2RhUPTDbNThrtiD2VkATnwHFBfvBjGh7B4AhVF4u6wa8Dgnhq`
- `2023-07-15T09:48:46+00:00` `token_transfer` `out` `93921.338428 IOT` tx=`2HfWUAgCHDrY2yujo6a6ZzsYejDzXQbZzPfV3oE2RhUPTDbNThrtiD2VkATnwHFBfvBjGh7B4AhVF4u6wa8Dgnhq`
- `2023-07-30T06:59:13+00:00` `swap_out_aggregated` `out` `53760.356821 IOT` tx=`5LbqXnxbEfXmPegwuURc4CAjHa7RsufqEpreUssrA8ip9ydzGKUiPaDGJp6DJTu8iGzys8bSDejMHYf9p3AD9hyX`
- `2023-07-30T06:59:13+00:00` `swap_in_aggregated` `in` `64729.546356 MOBILE` tx=`5LbqXnxbEfXmPegwuURc4CAjHa7RsufqEpreUssrA8ip9ydzGKUiPaDGJp6DJTu8iGzys8bSDejMHYf9p3AD9hyX`
- `2023-07-30T06:59:13+00:00` `swap_out_aggregated` `out` `0.00407856 SOL` tx=`5LbqXnxbEfXmPegwuURc4CAjHa7RsufqEpreUssrA8ip9ydzGKUiPaDGJp6DJTu8iGzys8bSDejMHYf9p3AD9hyX`
- `2023-08-01T06:35:02+00:00` `token_transfer` `in` `1 DvoPSy...vR4K` tx=`qhWcN51yoSr2pEyvwqD54g4cDC834osrV6Zj6TrNxTaFSnG3ewoq1xudzpmXFbmSRqNDMMQyPzFRB472Rbyrojh`
- `2023-08-01T06:35:02+00:00` `token_transfer` `out` `800 HNT` tx=`qhWcN51yoSr2pEyvwqD54g4cDC834osrV6Zj6TrNxTaFSnG3ewoq1xudzpmXFbmSRqNDMMQyPzFRB472Rbyrojh`
- `2023-08-01T06:35:02+00:00` `sol_transfer` `out` `0.02330056 SOL` tx=`qhWcN51yoSr2pEyvwqD54g4cDC834osrV6Zj6TrNxTaFSnG3ewoq1xudzpmXFbmSRqNDMMQyPzFRB472Rbyrojh`
- `2023-08-01T06:43:43+00:00` `token_transfer` `in` `1 5MFem7...UeTF` tx=`3dC6TFS8frjSp4Pg7qp3LuKcW6iSttuqW72WCvKYeVYsp5PXahzxw2g4eq3M3HaAeXAZXGkzQbyEVQCcQZhya3er`
- `2023-08-01T06:43:43+00:00` `token_transfer` `out` `64729.546356 MOBILE` tx=`3dC6TFS8frjSp4Pg7qp3LuKcW6iSttuqW72WCvKYeVYsp5PXahzxw2g4eq3M3HaAeXAZXGkzQbyEVQCcQZhya3er`
- `2023-08-01T06:43:43+00:00` `sol_transfer` `out` `0.02330056 SOL` tx=`3dC6TFS8frjSp4Pg7qp3LuKcW6iSttuqW72WCvKYeVYsp5PXahzxw2g4eq3M3HaAeXAZXGkzQbyEVQCcQZhya3er`
- `2023-09-30T06:28:50+00:00` `swap_in_aggregated` `in` `28.56369341 HNT` tx=`3zCES1wbtM3CugrocGYLGuY1V6k7Afch4oiuDhjWn9NueXYerohNZD5SCcNcx11SNRMaoVmj4kradtMfHjPYYUQ6`
- `2023-09-30T06:28:50+00:00` `swap_out_aggregated` `out` `103799.879735 IOT` tx=`3zCES1wbtM3CugrocGYLGuY1V6k7Afch4oiuDhjWn9NueXYerohNZD5SCcNcx11SNRMaoVmj4kradtMfHjPYYUQ6`
- `2023-11-11T06:57:33+00:00` `swap_out_aggregated` `out` `102.75751716 HNT` tx=`AhswTzgXWrFZAgXQ3J7K8k7ixnSdGZ8CiPHU1tLj3DbRTRhhiVbPptAmzQag5nLXBP2GC8S7eJyDKFmRio63fPP`
- `2023-11-11T06:57:33+00:00` `swap_in_aggregated` `in` `361446.32805 IOT` tx=`AhswTzgXWrFZAgXQ3J7K8k7ixnSdGZ8CiPHU1tLj3DbRTRhhiVbPptAmzQag5nLXBP2GC8S7eJyDKFmRio63fPP`
- `2024-02-15T07:28:32+00:00` `swap_out_aggregated` `out` `42097 IOT` tx=`JZnqBEz2UTMcE8th89Ru7dL1e7QaULMUWbGRwCoFeWLk22fqxKzcykfeGZcoj1naeUq97eosHxnT27dYtes7TqK`
