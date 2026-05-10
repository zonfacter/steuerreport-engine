# Binance 2022/2023 Blockpit Source Chain Reconstruction - 2026-05-09

## Ergebnis

- Modus: `execute`
- Ausgewaehlte Trades: `12`
- Importierte Events: `12`
- Duplikate: `0`
- Bestehende Rekonstruktionszeilen: `0`

## Rekonstruktionszeilen

- `2022-11-14T06:13:40+00:00` tx `binance-source-chain-reconstruction:N01288537375393490944111444`: `100.02920059 BUSD` gegen `98 EUR` fee `2 EUR`
- `2022-11-14T06:14:27+00:00` tx `binance-source-chain-reconstruction:85361646`: `1241 DOGE` gegen `99.95014 BUSD` fee `1.241 DOGE`
- `2022-12-02T18:16:38+00:00` tx `binance-source-chain-reconstruction:59571809`: `0.0072292 BTC` gegen `1240 DOGE` fee `0.00000723 BTC`
- `2022-12-17T08:38:05+00:00` tx `binance-source-chain-reconstruction:59817964`: `906 DOGE` gegen `0.00420384 BTC` fee `0.906 DOGE`
- `2022-12-17T08:38:05+00:00` tx `binance-source-chain-reconstruction:59817965`: `650 DOGE` gegen `0.003016 BTC` fee `0.65 DOGE`
- `2023-03-17T07:51:14+00:00` tx `binance-source-chain-reconstruction:N01333135634309321728031744`: `519.83907139 BUSD` gegen `490 EUR` fee `10 EUR`
- `2023-03-17T07:53:36+00:00` tx `binance-source-chain-reconstruction:6019749`: `29.01 HNT` gegen `48.33066 BUSD` fee `0 `
- `2023-03-17T07:53:38+00:00` tx `binance-source-chain-reconstruction:6019751`: `7.19 HNT` gegen `11.97854 BUSD` fee `0 `
- `2023-03-17T07:53:46+00:00` tx `binance-source-chain-reconstruction:6019758`: `275.87 HNT` gegen `459.59942 BUSD` fee `0 `
- `2023-03-17T08:25:50+00:00` tx `binance-source-chain-reconstruction:6026452`: `14.91186 BUSD` gegen `9.42 HNT` fee `0.01491186 BUSD`
- `2023-03-17T08:25:50+00:00` tx `binance-source-chain-reconstruction:6026453`: `482.00767 BUSD` gegen `304.49 HNT` fee `0.48200767 BUSD`
- `2023-03-17T08:26:35+00:00` tx `binance-source-chain-reconstruction:953994324`: `0.01896 BTC` gegen `495.8783232 BUSD` fee `0 `

## Bewertung

- The earlier BTC and BUSD gaps are explained by one closed Binance source chain in Blockpit's Binance API reference data.
- The full sequence starts with EUR->BUSD, continues through DOGE/HNT spot trades, and ends with BUSD->BTC before the SOL buys.
- The full chain is imported together because isolated rows would shift the gap between BTC, BUSD and DOGE/HNT.
- The chain leaves the BUSD dust conversion amount effectively covered without creating new negative intermediate balances in the pre-import simulation.
