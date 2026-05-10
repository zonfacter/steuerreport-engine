# Binance HNT Residual Audit - 2026-05-09

## Ergebnis

- Plattform: `binance`
- Asset: `HNT`
- Binance-HNT-Endsaldo lokal: `-1.62738672`
- Globaler HNT-Endsaldo: `1577.92535200143114379127906`
- Erster lokaler Negativbestand: `2023-03-17T08:25:50+00:00` tx `binance-source-chain-reconstruction:6026453`
- Vorbestand vor 2023-03-17-Rekonstruktion: `0.21261328`
- Netto der 2023-03-17-Rekonstruktion: `-1.84`

## Bewertung

- Automatisch steuerwirksam buchen: `False`
- Auto-Book sicher: `False`
- Empfohlener Status: `platform_context_or_small_residual_review`
- Grund: Blockpit reference rows for 2023-03-17 contain exactly the five HNT trades already imported. They buy 312.07 HNT and sell 313.91 HNT. With the pre-existing Binance HNT balance of 0.21261328, the platform-local residual is -1.62738672 HNT. The global HNT ledger remains positive, so this should not be corrected as a global taxable inventory inflow.

## Rekonstruktionszeilen

- `2023-03-17T07:53:36+00:00` `29.01 HNT` balance `0.21261328` -> `29.22261328` tx `binance-source-chain-reconstruction:6019749`
- `2023-03-17T07:53:38+00:00` `7.19 HNT` balance `29.22261328` -> `36.41261328` tx `binance-source-chain-reconstruction:6019751`
- `2023-03-17T07:53:46+00:00` `275.87 HNT` balance `36.41261328` -> `312.28261328` tx `binance-source-chain-reconstruction:6019758`
- `2023-03-17T08:25:50+00:00` `-9.42 HNT` balance `312.28261328` -> `302.86261328` tx `binance-source-chain-reconstruction:6026452`
- `2023-03-17T08:25:50+00:00` `-304.49 HNT` balance `302.86261328` -> `-1.62738672` tx `binance-source-chain-reconstruction:6026453`

## Gepruefte Blockpit-Binance-HNT-Referenzen 2023-03-17

- `2023-03-17T07:53:36+00:00` trx `6019749` in `29.01 HNT` out `48.33066 BUSD` fee `0`
- `2023-03-17T07:53:38+00:00` trx `6019751` in `7.19 HNT` out `11.97854 BUSD` fee `0`
- `2023-03-17T07:53:46+00:00` trx `6019758` in `275.87 HNT` out `459.59942 BUSD` fee `0`
- `2023-03-17T08:25:50+00:00` trx `6026452` in `14.91186 BUSD` out `9.42 HNT` fee `0.01491186 BUSD`
- `2023-03-17T08:25:50+00:00` trx `6026453` in `482.00767 BUSD` out `304.49 HNT` fee `0.48200767 BUSD`

## Naechste Aktion

- Nicht als globalen HNT-Zufluss buchen.
- Wenn kein weiterer Binance-/Helium-Beleg auftaucht, als dokumentierten Plattformkontext-/Kleinrest entscheiden.
