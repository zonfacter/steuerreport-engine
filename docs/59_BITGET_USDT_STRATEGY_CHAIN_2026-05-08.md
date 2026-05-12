# Bitget USDT Strategy Chain - 2026-05-08

## Zweck

Fokussierte USDT-Kette fuer Bitget 2025: Deposits, Withdrawals, interne Exchange-Transfers, Strategy-Transfers und Risk-Capital-Transfers.
Es werden keine fehlenden Bot-Fills erzeugt.

## Summary

- JSON: `/workspace/steuerreport/var/bitget_usdt_strategy_chain_2026-05-08.json`
- Zeilen: `14`
- Primaer: `12`
- Referenz: `2`
- Klassen: `{"transfer": 4, "internal_exchange_transfer": 3, "strategy_transfer": 2, "risk_capital_transfer": 2, "reference": 2, "deposit_or_auto_in": 1}`
- Net Primary Effect: `4383.01697203 USDT`
- Net je Klasse: `{"deposit_or_auto_in": "5009.09824537", "internal_exchange_transfer": "1923.38630773", "risk_capital_transfer": "-222.10227813", "strategy_transfer": "-1.21024890", "transfer": "-2326.15505404"}`

## Primaer-Timeline

| Zeit | Typ | Business | Effekt USDT | Gemeldeter Balance | Running Effekt | ID |
|---|---|---|---:|---:|---:|---|
| `2025-01-29T05:56:22.075000+00:00` | `deposit` | `Deposit` | `5009.09824537` | `5009.098245373884` | `5009.09824537` | `1268375403930660876` |
| `2025-01-29T06:02:42.882000+00:00` | `transfer` | `Transfer out` | `-1323.98667337` | `0.000000003884` | `3685.11157200` | `1268377000559587330` |
| `2025-01-29T06:02:42.931000+00:00` | `transfer` | `trans_from_exchange` | `1323.98667337` | `1330.41753171` | `5009.09824537` | `1268377000628355083` |
| `2025-01-31T18:24:42.447000+00:00` | `transfer` | `Transfer in` | `1032.58619277` | `1631.985827139884` | `6041.68443814` | `1269288504922288138` |
| `2025-01-31T18:24:42.471000+00:00` | `transfer` | `trans_to_exchange` | `-1032.58619277` | `0` | `5009.09824537` | `1269288504844255255` |
| `2025-02-01T11:50:28.450000+00:00` | `transfer` | `Transfer out` | `-1631.98582713` | `0.000000009884` | `3377.11241824` | `1269551680712683521` |
| `2025-02-01T11:50:28.504000+00:00` | `transfer` | `trans_from_exchange` | `1631.98582713` | `1631.98582713` | `5009.09824537` | `1269551680781451264` |
| `2025-02-22T05:31:15.652000+00:00` | `transfer` | `trans_to_strategy` | `-249.59902416` | `487.55107673` | `4759.49922121` | `1277066393580896266` |
| `2025-02-22T17:09:53.936000+00:00` | `transfer` | `trans_from_strategy` | `248.38877526` | `708.83804188` | `5007.88799647` | `1277242211607150609` |
| `2025-02-27T15:01:19.616000+00:00` | `transfer` | `risk_captital_user_transfer` | `-222.10227813` | `0` | `4785.78571834` | `1279021794731917356` |
| `2025-04-07T06:34:36.819000+00:00` | `transfer` | `risk_captital_user_transfer` | `0` | `0` | `4785.78571834` | `1293027402917249111` |
| `2025-05-10T10:04:15.476000+00:00` | `transfer` | `Transfer out` | `-402.76874631` | `0.000000006884` | `4383.01697203` | `1305038961337868289` |

## Referenzzeilen

- `2025-07-11T20:08:09+00:00` `blockpit` `withdrawal` effect `27.40478646` id ``
- `2025-07-11T20:09:15+00:00` `blockpit` `deposit` effect `27.72971604` id ``

## Interpretation

- The 2025 USDT chain shows external deposits and internal transfers into exchange/strategy contexts.
- Strategy transfer pair on 2025-02-22 is nearly matched: -249.59902416 to strategy and +248.38877526 from strategy, net -1.21024890 USDT.
- Risk capital transfer on 2025-02-27 moves -222.10227813 USDT and coincides with derivative loss/liquidation area in the broader Bitget audit.
- This chain supports a reconstruction, but it is not a replacement for missing bot fill details.
