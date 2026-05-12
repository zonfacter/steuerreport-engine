# Pionex Interne Bilanz bis USDT-Bruch

Stand: 2026-05-12

## Scope

- Cutoff: `2022-01-19T12:56:19+00:00`
- Quelle: kanonische lokale Pionex-Dateien `usertransfer/pionex/deposit-withdraw.csv` und `usertransfer/pionex/trading.csv`.
- Zweck: Pruefen, ob die offene USDT-Luecke aus sichtbaren Pionex-Verkaeufen/Swaps anderer Assets entstanden sein kann.
- Keine steuerliche Cost-Basis-Aenderung und keine Preis-/FX-Schaetzung.

## Ergebnis

- Ausgewertete Bilanzbewegungen: `209`
- Assets mit negativem Mindestbestand: `USDT`
- Erforderlicher rechnerischer USDT-Startbestand: `1643.2312211162 USDT`
- Andere Assets werden in dieser kanonischen Pionex-Chronologie bis zum Cutoff nicht negativ.
- Damit ist kein sichtbarer interner Verkauf eines fehlenden Assets als Quelle der USDT-Luecke belegbar.

## USDT-Kernbefund

- Sichtbare USDT-Deposits bis Cutoff: `1445.38419 USDT`
- USDT-Endbestand aus sichtbaren Pionex-Bewegungen bis Cutoff: `-1643.2312211162 USDT`
- Schlechtester USDT-Stand: `-1643.2312211162 USDT`
- Schlechtester Zeitpunkt: `2022-01-19T12:56:19+00:00`
- Ausloesendes sichtbares Event: `trade_buy_quote_out` `MXC_USDT` `s_11`

## Asset-Bilanzen

| Asset | Deposits | Endbestand | Minimum | Benoetigter Startbestand | Minimum-Zeit | Minimum-Event |
| --- | --- | --- | --- | --- | --- | --- |
| EGLD | 0 | 0.000074 | 0.000074 | 0 | 2022-01-18T10:30:41+00:00 | trade_sell_base_out EGLD_USDT |
| HNT | 0 | 0.002556 | 0.002556 | 0 | 2022-01-02T07:58:22+00:00 | trade_sell_base_out HNT_USDT |
| MXC | 0 | 26015.95496 | 32.288715 | 0 | 2022-01-19T11:22:49+00:00 | trade_sell_base_out MXC_USDT |
| SHIB | 0 | 0.007625 | 0.007625 | 0 | 2022-01-05T11:39:22+00:00 | trade_sell_base_out SHIB_USDT |
| USDT | 1445.38419 | -1643.2312211162 | -1643.2312211162 | 1643.2312211162 | 2022-01-19T12:56:19+00:00 | trade_buy_quote_out MXC_USDT |

## Trading-Paare bis Cutoff

| Symbol | Base In | Base Out | Quote In | Quote Out | Net Quote vor Fees | Fees |
| --- | --- | --- | --- | --- | --- | --- |
| EGLD_USDT | 1.852 | 1.851 | 381.565985 | 423.936542 | -42.370557 | 0.19170908 |
| HNT_USDT | 18.888 | 18.876 | 726.542061 | 721.601136 | 4.940925 | 0.37271517 |
| MXC_USDT | 29970.08 | 3939.14 | 391.58696233 | 3436.75936645 | -3045.17240412 | 15.18083344 |
| SHIB_USDT | 6257044.75 | 6253916.22 | 204.7893852834 | 209.9505179196 | -5.1611326362 | 3128.62476967 |

## Einordnung

- Die sichtbaren HNT_USDT-Trades erzeugen nur einen kleinen USDT-Ueberschuss; sie erklaeren die grosse MXC_USDT-Luecke nicht.
- Der grosse Bruch liegt beim `MXC_USDT`-BUY `s_11` am `2022-01-19T12:56:19+00:00`.
- Aus den vorhandenen Pionex-Dateien folgt daher: Es fehlt kein sichtbarer Asset-Verkauf, sondern ein USDT-Opening-/Bot-/Strategy-Startbestand oder eine nicht exportierte interne Pionex-Kontobuchung.
- Ohne diesen Primaerbeleg darf weiterhin keine Anschaffungskostenbasis automatisch erzeugt werden.

JSON: `var/pionex_internal_balance_audit_2026-05-12.json`
