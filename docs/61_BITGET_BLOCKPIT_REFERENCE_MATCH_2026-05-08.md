# Bitget Blockpit Reference Match - 2026-05-08

## Summary

- JSON: `/workspace/steuerreport/var/bitget_blockpit_reference_match_2026-05-08.json`
- Sicht: `Raw/reviewed counts are before tax_event_overrides so duplicate reference rows remain visible. Effective counts are after existing tax_event_overrides and represent rows still active for tax processing.`
- Tax-Overrides angewendet in effektiver Sicht: `5019`
- Raw/reviewed Primary rows: `405`
- Raw/reviewed Blockpit reference rows: `580`
- Raw/reviewed matched: `405`
- Raw/reviewed unmatched: `175`
- Effective Primary rows: `405`
- Effective Blockpit reference rows: `0`
- Effective matched reference rows: `0`
- Effective unmatched reference rows: `0`
- Match basis counts: `{'tx_id_base': 231, 'tx_id_base_fee_component': 172, 'time_amount_asset': 2}`
- Effective unmatched type counts: `{}`

## Effective Matched Reference Duplicates

| Ref Zeit | Prim Zeit | Amount | Ref Comment | Prim Business | Basis | Ref Event | Prim Event |
|---|---|---:|---|---|---|---|---|
| - | - | - | - | - | - | - | - |

## Effective Unmatched Reference Rows

Diese Zeilen sind nach aktuellen Overrides noch wirksam und konnten in diesem Matching nicht 1:1 gegen Bitget-Primary belegt werden.

- Keine.

## Raw/Reviewed Abgleich

- Raw/reviewed matched Blockpit rows: `405`
- Davon nicht mehr effektiv: `405`
- Raw/reviewed unmatched Blockpit rows: `175`
- Davon nicht mehr effektiv: `175`

Der Raw/reviewed Abgleich bleibt im JSON erhalten, damit bereits ausgeschlossene Blockpit-Referenzen weiterhin nachvollziehbar sind.

## Empfehlung

Only effective matched Blockpit rows are current exclusion candidates. Raw matched rows that are no longer effective are already excluded or otherwise overridden. Effective unmatched rows must remain under review.

Dieses Matching-Script schreibt selbst keine Overrides. Die geprüften Kandidaten wurden separat über `scripts/apply_bitget_blockpit_reference_exclusions.py` als `reference_import_only` ausgeschlossen.
