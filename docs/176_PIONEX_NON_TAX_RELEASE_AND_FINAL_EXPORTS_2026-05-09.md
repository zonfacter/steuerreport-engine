# Pionex Non-Tax Release And Final Exports - 2026-05-09

## Entscheidung

Der alte Pionex/USDT-Kontext wurde nach Nutzerbestaetigung als nicht steuerwirksame Bestandsnormalisierung freigegeben.

- Kandidat: `pionex-usdt-opening-balance-2021-12-28`
- Entscheidung: `approve_non_tax_inventory_normalization`
- Status: `approved_non_tax_inventory_normalization`
- Steuerwirksam: `false`
- Rohdaten geaendert: nein
- Import erzeugt: nein

Begruendung: Das Thema betrifft den alten 2021/2022-Startkontext. Es soll kein steuerpflichtiger Zufluss erfunden werden. Die vorhandenen Dossiers und das Pionex-Belegpaket bleiben als Pruefpfad erhalten.

## Gate-Status

Live auf Port `8000` geprueft:

- `allow_export=true`
- `issues_total=0`
- `issues_open=0`
- `issues_high_open=0`
- `unmatched_total=0`
- `balance_adjustment_candidates_open=0`
- `blocking_reasons=[]`

Snapshot:

- `var/review_gate_snapshot_2026-05-09.json`

## Aktualisierte Uebersicht

Aktualisiert:

- `docs/168_CURRENT_TAX_DRAFT_RUNS_2026-05-09.md`
- `var/current_tax_draft_summary_2026-05-09.json`

Der Inhalt zeigt jetzt `Export-Gate: True` und behandelt die Laeufe als final exportfaehig.

## Finale Exportdateien

Neu abgelegt:

- `var/report_exports_final_2026-05-09/`

Inhalt:

- `23` Dateien
- Jahres-JSON fuer `2020` bis `2026`
- Tax-CSV und WISO-CSV fuer `2020` bis `2026`
- Derivate-CSV fuer `2024`
- `report_file_indexes.jsonl`

Validierung:

- Alle Jahres-JSON-Dateien haben `draft_notice=null`.
- Keine Treffer fuer `ENTWURF`, `Draft_Status` oder `NOT_FINAL` im finalen Exportordner.
- WISO-Header fuer `2025` enthaelt keine Draft-Markierung.

## Hinweis

Die alten Entwurfsdateien in `var/report_exports_current_2026-05-09/` bleiben als Historie erhalten. Fuer den aktuellen final freigegebenen Stand ist `var/report_exports_final_2026-05-09/` massgeblich.
