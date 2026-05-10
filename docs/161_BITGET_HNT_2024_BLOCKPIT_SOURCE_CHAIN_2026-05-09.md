# Bitget HNT 2024 Blockpit Source Chain - 2026-05-09

## Ergebnis

- Modus: `execute`
- Ausgewaehlte Zeilen: `12`
- Importierte Events: `12`
- Duplikate: `0`
- Bestehende Rekonstruktionszeilen: `0`

## Rekonstruktionszeilen

- `2024-03-07T15:54:40+00:00` `deposit` `in` `55 USDT` tx `bitget-hnt-2024-source-chain:1149662750789283849`
- `2024-03-07T15:55:54+00:00` trade `4.993 HNT` gegen `45.6265333 USDT` fee `0.004993 HNT` tx `bitget-hnt-2024-source-chain:1149663063353012237-1149663063353012239`
- `2024-03-07T16:03:55+00:00` `deposit` `in` `700 USDT` tx `bitget-hnt-2024-source-chain:1149665078305042434`
- `2024-03-07T16:06:58+00:00` `automatic_withdrawal` `out` `200.82362842 USDT` tx `bitget-hnt-2024-source-chain:1149665846282104838`
- `2024-03-07T16:10:15+00:00` `automatic_withdrawal` `out` `508.54983828 USDT` tx `bitget-hnt-2024-source-chain:1149666673075892227`
- `2024-03-07T19:55:15+00:00` `automatic_deposit` `in` `6.561432 HNT` tx `bitget-hnt-2024-source-chain:1149723296817426454`
- `2024-03-07T19:55:15+00:00` `automatic_deposit` `in` `141.77680602 USDT` tx `bitget-hnt-2024-source-chain:1149723296540602374`
- `2024-03-07T19:55:23+00:00` `automatic_deposit` `in` `192.44331057 USDT` tx `bitget-hnt-2024-source-chain:1149723331042947074`
- `2024-03-07T19:57:13+00:00` `automatic_withdrawal` `out` `334.22011659 USDT` tx `bitget-hnt-2024-source-chain:1149723792982618118`
- `2024-03-11T11:47:34+00:00` trade `0.951 HNT` gegen `8.550441 USDT` fee `0.000951 HNT` tx `bitget-hnt-2024-source-chain:1151050117659963402-1151050117659963403`
- `2024-03-11T18:27:50+00:00` `automatic_deposit` `in` `343.23812096 USDT` tx `bitget-hnt-2024-source-chain:1151150847725088768`
- `2024-03-11T18:32:09+00:00` `automatic_withdrawal` `out` `343.41417068 USDT` tx `bitget-hnt-2024-source-chain:1151151935480082439`

## Bewertung

- Bitget Tax API starts HNT with sell rows on 2024-04-02, but Blockpit's Bitget API reference contains a preceding internal source chain.
- The selected rows explain 12.499488 HNT before the first sell: 4.993 HNT buy minus fee, 6.561432 HNT automatic deposit, and 0.951 HNT buy minus fee.
- The USDT deposits/automatic withdrawals around those buys are imported with the HNT rows so the gap is not shifted into USDT.
- The already imported Bitget BTC->USDT reconstruction is not duplicated.
