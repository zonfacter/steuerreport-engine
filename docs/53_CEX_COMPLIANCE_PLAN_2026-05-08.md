# CEX Compliance Plan - 2026-05-08

## Ziel

Der Steuerreport soll fuer zentrale Plattformen nachvollziehbar belegen koennen:

- welche CEX-Daten pro Kalenderjahr importiert wurden,
- welche Zeitraeume und Eventarten abgedeckt sind,
- wo API-/Export-Limits greifen,
- welche offenen Luecken nicht geraten, sondern als Review-/Nachweisbedarf markiert werden,
- welche Daten primaer sind und welche nur Referenz-/Blockpit-/WISO-Vergleichsdaten sind.

## Grundregeln

1. RAW-Daten werden nicht geloescht oder still korrigiert.
2. Korrekturen laufen ueber Review-Actions, Overrides, Kommentare oder explizite Adjustments.
3. Primaerquellen haben Vorrang vor Referenzimporten.
4. CEX-Exports/API-Daten werden gegen On-Chain-Transfers abgeglichen, wo TXIDs/Adressen vorhanden sind.
5. Fehlende Daten werden als Status gefuehrt, nicht durch KI erfunden.
6. KI darf priorisieren und Hypothesen bilden, aber keine steuerlich wirksamen Fakten setzen.

## Plattform-Scope

Aktueller Scope:

- Binance
- Pionex
- Bitget
- Jupiter/Jup.ag
- Coinbase, falls Daten vorhanden
- Blockpit/WISO nur als Referenz, nicht als primaere Wahrheit

## Statusmodell

Pro Plattform und Kalenderjahr wird ein Status vergeben:

- `complete`: primaere Daten und Eventtypen plausibel abgedeckt
- `partial`: Daten vorhanden, aber Zeitraum/Eventtypen erkennbar unvollstaendig
- `api_limited`: API-Limit oder Historienlimit verhindert vollstaendige Abfrage
- `csv_required`: manueller CSV/Web-Export ist erforderlich
- `support_required`: Support-Anfrage fuer alte Daten erforderlich
- `opening_balance_required`: Startbestand/Bot-Startkapital erforderlich
- `manual_review`: datenfachliche Klaerung erforderlich
- `reference_only`: nur Referenzdaten vorhanden
- `no_data`: keine Daten im Bestand

## Arbeitspakete

1. Deterministische CEX-Coverage-Matrix erzeugen.
2. Pro Plattform/Jahr Source-Files, Eventzahl, Zeitraum, Eventtypen und Assets erfassen.
3. Bekannte Limits eintragen:
   - Bitget alte Spot-/Bot-/Grid-Historie: API limitiert, Support/Web-Exports erforderlich.
   - Pionex: Opening-Balance/Bot-Startkapital Anfang 2022 offen.
   - Binance: Spot/Convert/Earn/Fiat je Jahr gegen vorhandene Exporte/API pruefen.
4. On-Chain-Verifikationen verlinken:
   - Pionex TRC20-Adresse `TMHP82...` ist gegen Binance-Withdrawals belegt.
   - Solana/Jupiter Wallet `wBrPoi...` ist per Solscan/Exports geprueft.
5. Qwen3.6-Review auf Matrix laufen lassen.
6. Naechste Datenbeschaffungsliste erzeugen, sortiert nach Steuerwirkung und Jahr.

## Deliverables

- Script: `scripts/cex_compliance_coverage_audit.py`
- JSON: `var/cex_compliance_coverage_2026-05-08.json`
- Report: `docs/54_CEX_COMPLIANCE_COVERAGE_2026-05-08.md`
- KI-Review: `docs/55_AI_CEX_COMPLIANCE_REVIEW_2026-05-08.md`
