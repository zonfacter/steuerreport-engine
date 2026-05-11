# HNT-/USDT-Restbestandsluecken-Audit

Stand: 2026-05-11

## Ergebnis

- Aktuelle Restzeilen: `14`
- Erloes dieser Restzeilen: `5442.131645572294372978223086 EUR`
- Keine Restzeile ist ein belegbarer Preisanker- oder FX-Backfill.
- HNT-Transfer-Matches fuer die Binance-Deposits existieren bereits; die Luecke liegt vor dem Legacy-Outflow.
- USDT-Reste bleiben Pionex-/Binance-Opening- bzw. Bot-Historie ohne Primaerbeleg.

## Aktuelle Jobs

| Jahr | Job | Tax-Lines | Derivate-Lines | Aktualisiert |
| ---: | --- | ---: | ---: | --- |
| 2020 | `0b3a4d22-6574-4e54-8685-92d40dbaf100` | 0 | 0 | 2026-05-11T20:33:22.138080+00:00 |
| 2021 | `01504a89-9b31-4e87-97f4-953f70164a9f` | 5494 | 43 | 2026-05-11T20:33:30.805075+00:00 |
| 2022 | `a2523d34-68b5-4983-b08f-c44dbf7816a8` | 6896 | 630 | 2026-05-11T20:33:39.930444+00:00 |
| 2023 | `210d8066-3bb0-4947-b45b-ceb2962e15d6` | 9099 | 0 | 2026-05-11T20:33:49.504534+00:00 |
| 2024 | `aeb1b44b-8b45-4dcb-8479-12c5b470c379` | 1680 | 36 | 2026-05-11T20:33:58.836379+00:00 |
| 2025 | `cc781fa5-1987-411a-ba69-e2653129cf88` | 465 | 957 | 2026-05-11T20:34:07.563410+00:00 |
| 2026 | `b59704da-a6b6-442d-b64d-b8024a74bab5` | 1 | 0 | 2026-05-11T20:34:16.355680+00:00 |

## Gruppierung

| Jahr | Asset | Klasse | Zeilen | Menge | Erloes EUR | Plattformen |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 2021 | `HNT` | `matched_transfer_source_cost_basis_gap` | 2 | 18.18741071559783055 | 360.0331781850617052490318998 | binance |
| 2021 | `HNT` | `missing_lot_source_inventory_gap` | 4 | 71.527745669999999928 | 1398.08775436293029859268152 | binance |
| 2022 | `HNT` | `matched_transfer_source_cost_basis_gap` | 5 | 439.688010219657251202 | 2300.134050729099355136509666 | pionex |
| 2022 | `USDT` | `missing_lot_source_inventory_gap` | 3 | 1569.8280684762 | 1383.876662295203014 | binance, pionex |

## Betroffene Zeilen

| Jahr | Line | Asset | Menge | Erloes EUR | Quelle | Lot-Quelle | Klasse |
| ---: | ---: | --- | ---: | ---: | --- | --- | --- |
| 2021 | 1340 | `HNT` | 16.233745669999999928 | 317.30625390293029859268152 | `binance/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2021 | 1341 | `HNT` | 14.142 | 276.42080478 | `binance/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2021 | 1344 | `HNT` | 17.406 | 340.21924254 | `binance/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2021 | 1345 | `HNT` | 23.746 | 464.14145314 | `binance/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2021 | 1407 | `HNT` | 14.651308409999999970498 | 290.1121724005967814158276469 | `binance/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2021 | 1577 | `HNT` | 3.536102305597830579502 | 69.92100578446492383320425294 | `binance/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 3439 | `HNT` | 74.356 | 355.6905058882184352 | `pionex/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 3456 | `HNT` | 84.528 | 414.0965341866616704 | `pionex/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 3572 | `HNT` | 208.192 | 1146.1874646034960896 | `pionex/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 3576 | `HNT` | 58.7 | 311.59419948832 | `pionex/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 3579 | `HNT` | 13.912010219657251202 | 72.56534656240315993650966628 | `pionex/trade/out` | `binance_api/deposit/in` | `matched_transfer_source_cost_basis_gap` |
| 2022 | 412 | `USDT` | 75.1046222062 | 66.352680580511514 | `binance/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2022 | 442 | `USDT` | 168.7646835 | 148.757630271075 | `pionex/trade/out` | `leer` | `missing_lot_source_inventory_gap` |
| 2022 | 514 | `USDT` | 1325.95876277 | 1168.7663514436165 | `pionex/trade/out` | `leer` | `missing_lot_source_inventory_gap` |

## HNT-Transfer-Belege

- Match `ddec12db-878f-4285-b40a-16df945a301a` fuer Inbound `dd5353eedbee68d33a5c687e013b67f468dac6a769af6b56b60dfd7c1e40fa2f`:
  - Outbound `helium_legacy_cointracking` `legacy_transfer` 18.318453080375246 `HNT` am `2021-08-20T08:01:13+00:00`.
  - Binance-Inbound 18.30256046 `HNT` am `2021-08-20T08:04:08+00:00`.
  - Delta `0.015892620375246`, Zeitdifferenz `175` Sekunden.
  - Legacy-Transfer-Wert `value_usd=403.42` ist ein Transferwert, keine belegte Anschaffungskostenbasis.
- Match `728264aa-94fe-43ec-a49f-ed9a3a5af447` fuer Inbound `9dd85d203cebbe23d40ff09ddd91b30758c3d255c6f80dadbb27581ab152bcba`:
  - Outbound `helium_legacy_cointracking` `legacy_transfer` 450.0398803021218 `HNT` am `2022-07-12T06:59:57+00:00`.
  - Binance-Inbound 450 `HNT` am `2022-07-12T07:08:01+00:00`.
  - Delta `0.0398803021218`, Zeitdifferenz `484` Sekunden.
  - Legacy-Transfer-Wert `value_usd=3949.67` ist ein Transferwert, keine belegte Anschaffungskostenbasis.

## Bewertung

- Eine automatische Bewertung der HNT-Deposits mit dem Legacy-Transferwert waere fachlich falsch, weil Transferwert nicht gleich Anschaffungskosten ist.
- Die 2021-HNT-Zeilen ohne Lot-Quelle liegen auf Binance-Verkaeufen am `2021-08-17`; fuer diese Verkaufsmenge gibt es im aktiven Datenstand keinen belegten vorherigen Binance-Deposit.
- Die 2022-USDT-Zeilen decken sich mit dem bereits dokumentierten Pionex-/Binance-Opening- und Bot-Historienproblem.
- Deshalb: keine neue automatische RAW-/FX-/Cost-Basis-Korrektur aus diesem Audit.

## Naechste sichere Aktion

- HNT: Primaerbelege fuer HNT-Anschaffung/Mining-Bestand vor den Legacy-Outflows nachreichen oder die historischen Nullbasis-Zeilen bewusst offen lassen.
- USDT: Pionex-Opening-/Bot-Historie oder explizite Review-Entscheidung verwenden; ohne Beleg keinen steuerwirksamen Zufluss importieren.

JSON: `var/hnt_usdt_remaining_inventory_gap_audit_2026-05-11.json`
