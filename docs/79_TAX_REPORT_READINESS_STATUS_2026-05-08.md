# Tax Report Readiness Status - 2026-05-08

## Summary

- Status: `blocked_by_bitget_2025_support`
- RAW-Events: `55122`
- Effektive Events: `47811`
- Override-Count: `7311`
- Balance-Audit: `/workspace/steuerreport/var/chronological_balance_break_audit_current_after_jupiter_coverage_2026-05-08.json`
- CEX-Coverage: `/workspace/steuerreport/docs/54_CEX_COMPLIANCE_COVERAGE_2026-05-08.md`
- KI-Review: `/workspace/steuerreport/docs/55_AI_CEX_COMPLIANCE_REVIEW_2026-05-08.md`

## Entscheidung

- Draft-Report erzeugbar: `True`
- Als final sauber markierbar: `False`

Ein Entwurf ist technisch erzeugbar, aber ein final sauberer Report ist solange nicht erreicht, bis Pionex-Opening, Bitget-2025 und die zwei Dust-Residuals fachlich entschieden sind.

## Negative Endbestaende

- `VTHO`: `-42.39387934`
- `BUSD`: `-0.55168701480000000000`

## Offene Review-Kandidaten

- `binance-vtho-dust-residual-2023-05-02`: `VTHO` `42.39387934`, status `needs_evidence`, tax_effective `False`
- `mixed-busd-dust-residual-2023-05-02`: `BUSD` `0.55168701480000000000`, status `needs_review`, tax_effective `False`

## Coverage-Blocker

- `bitget` `2024`: `partial, api_limited, support_required, unavailable_source_possible`, Events `61`, Zeitraum `2024-04-02T16:59:41.727000+00:00..2024-12-07T16:39:27.510000+00:00`
- `bitget` `2025`: `partial, api_limited, support_required, unavailable_source_possible, manual_review`, Events `1986`, Zeitraum `2025-01-29T05:56:22.075000+00:00..2025-07-13T21:38:44+00:00`
- `jupiter` `2023`: `partial, manual_review`, Events `24`, Zeitraum `2023-04-26T14:42:15+00:00..2023-11-11T06:57:33+00:00`
- `jupiter` `2024`: `partial, manual_review`, Events `352`, Zeitraum `2024-02-15T07:28:32+00:00..2024-12-20T11:53:45+00:00`
- `jupiter` `2026`: `partial, manual_review`, Events `2`, Zeitraum `2026-01-02T04:16:35+00:00..2026-01-02T04:16:35+00:00`
- `pionex` `2021`: `partial, opening_balance_required`, Events `85`, Zeitraum `2021-12-25T16:23:04+00:00..2021-12-31T23:58:07+00:00`
- `pionex` `2022`: `partial, opening_balance_required`, Events `1776`, Zeitraum `2022-01-01T00:13:19+00:00..2022-12-28T05:55:39+00:00`

## Erledigte Coverage-Pruefungen

- `jupiter:2025`: `covered_by_solscan_true_missing_audit`, Report `/workspace/steuerreport/docs/80_JUPITER_2025_SOLSCAN_COVERAGE_AUDIT_2026-05-08.md`

## Naechste menschliche Entscheidungen

- Pionex: provide account/bot start evidence or approve documented replacement reconstruction.
- Bitget 2025: wait for support export or approve documented reconstruction limits.
- Dust residuals VTHO/BUSD: decide whether tiny review candidates may be made tax-effective or stay as unresolved residual notes.

## Nicht automatisch buchen

- Pionex opening balance candidate
- Dust residual candidates
- Bitget missing bot/trade details
