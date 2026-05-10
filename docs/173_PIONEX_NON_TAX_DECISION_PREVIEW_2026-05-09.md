# Pionex Non-Tax Decision Preview - 2026-05-09

## Ergebnis

- Diese Vorschau ist read-only und hat den Kandidaten nicht veraendert.
- Kandidat: `pionex-usdt-opening-balance-2021-12-28`
- Aktueller Status: `needs_evidence`
- Aktuelle Gate-Wirkung: finaler Export bleibt blockiert.
- Steuerwirksamkeit der moeglichen Freigabe: `False`
- Import-/RAW-Daten-Aenderung: keine.

## Entscheidungsoptionen

- `request_more_evidence` -> Status `needs_evidence`, blocks_final_export `True`, tax_effective `False`. Use while Pionex support evidence or written unavailability confirmation is still pending.
- `approve_non_tax_inventory_normalization` -> Status `approved_non_tax_inventory_normalization`, blocks_final_export `False`, tax_effective `False`. Use only after explicit reviewer/user decision that no taxable inflow should be invented.
- `reject_candidate` -> Status `rejected`, blocks_final_export `False`, tax_effective `False`. Use only if the candidate is proven wrong and should not block readiness.

## Vorbereiteter Freigabe-Payload

```json
{
  "candidate_id": "pionex-usdt-opening-balance-2021-12-28",
  "decision": "approve_non_tax_inventory_normalization",
  "reviewer": "manual-review",
  "note": "Explicit non-tax inventory normalization for Pionex/USDT opening context. Known Binance/TRON/Pionex exports prove only the visible deposits; remaining gap is treated as unsupported platform-local opening/bot-history context, not as a taxable inflow.",
  "evidence": {
    "evidence_package": "docs/172_PIONEX_EVIDENCE_REQUEST_PACKAGE_2026-05-09.md",
    "final_blocker_audit": "docs/167_PIONEX_USDT_FINAL_BLOCKER_AUDIT_2026-05-09.md",
    "decision_dossier": "docs/157_PIONEX_OPENING_DECISION_DOSSIER_2026-05-09.md",
    "known_transfer_csv": "var/pionex_usdt_known_transfers_for_support_2026-05-09.csv"
  }
}
```

## Safety Notes

- Preview is read-only and does not change the candidate.
- Approval does not create a tax-effective import or alter raw data.
- Approval should be backed by Pionex evidence, written non-availability confirmation, or explicit manual review acceptance.

## API

- Vorschau: `GET /api/v1/review/balance-adjustment-candidates/pionex-usdt-opening-balance-2021-12-28/decision-preview`
- Ausfuehrung nur bei expliziter Entscheidung: `POST /api/v1/review/balance-adjustment-candidates/decide`

## Dateien

- Preview JSON: `var/pionex_non_tax_decision_preview_2026-05-09.json`
- Evidence Package: `docs/172_PIONEX_EVIDENCE_REQUEST_PACKAGE_2026-05-09.md`
