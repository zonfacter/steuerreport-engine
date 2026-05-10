# Platform Residual Review Audit - 2026-05-09

## Ergebnis

- Residuals ohne Pionex-USDT-Hardblocker: `4`
- Klassifikation: `{'documented_platform_context_residual': 1, 'documented_rounding_dust': 3}`
- Automatisch importieren: `False`
- Steuerwirksames Adjustment empfohlen: `False`

## Harter Blocker

- `pionex / USDT`: Opening-/Bot-Startbestand bleibt entscheidungspflichtig; siehe `docs/157_PIONEX_OPENING_DECISION_DOSSIER_2026-05-09.md`.

## Residuals

- `documented_platform_context_residual` `binance` `HNT` final `-1.62738672` worst `-1.62738672` threshold `2`
  - Grund: Blockpit reference rows for 2023-03-17 contain exactly the five HNT trades already imported. They buy 312.07 HNT and sell 313.91 HNT. With the pre-existing Binance HNT balance of 0.21261328, the platform-local residual is -1.62738672 HNT. The global HNT ledger remains positive, so this should not be corrected as a global taxable inventory inflow.
  - Empfehlung: Keep as documented platform-context residual; do not book a global asset inflow unless a primary source appears.
  - Report: `docs/163_BINANCE_HNT_RESIDUAL_AUDIT_2026-05-09.md`
- `documented_rounding_dust` `pionex` `HNT` final `-0.16629829` worst `-0.16876807` threshold `2`
  - Grund: Small Pionex HNT bot residual; should be decided together with Pionex opening review, not booked as a separate taxable inflow.
  - Empfehlung: Document as non-material platform-local dust/rounding; do not import a tax-effective adjustment.
  - Report: `docs/158_HNT_PLATFORM_CONTEXT_AUDIT_2026-05-09.md`
- `documented_rounding_dust` `solana_wallet` `USDC` final `0.000988` worst `-0.000002` threshold `0.01`
  - Grund: Worst platform-local residual 0.000002 USDC is within materiality threshold 0.01 USDC.
  - Empfehlung: Document as non-material platform-local dust/rounding; do not import a tax-effective adjustment.
  - Report: `docs/135_PLATFORM_BREAK_RESOLUTION_PLAN_2026-05-09.md`
- `documented_rounding_dust` `solana_wallet` `USDT` final `-0.000002` worst `-0.000003` threshold `0.01`
  - Grund: Worst platform-local residual 0.000003 USDT is within materiality threshold 0.01 USDT.
  - Empfehlung: Document as non-material platform-local dust/rounding; do not import a tax-effective adjustment.
  - Report: `docs/135_PLATFORM_BREAK_RESOLUTION_PLAN_2026-05-09.md`

## Bewertung

- Diese Residuals sind plattformlokale Rest-/Rundungs- oder Kontextfaelle.
- Sie werden nicht als neue steuerwirksame Zufluesse importiert.
- Final sauber bleibt weiterhin von Pionex-USDT und den Coverage-Entscheidungen abhaengig.
