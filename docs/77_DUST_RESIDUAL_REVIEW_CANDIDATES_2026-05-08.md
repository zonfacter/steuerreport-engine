# Dust Residual Review Candidates - 2026-05-08

## Ausgangslage

Nach den Primaerimporten und Referenzausschluessen bleiben im chronologischen Balance-Audit nur noch zwei negative Endbestaende:

- `VTHO`: `-42.39387934`
- `BUSD`: `-0.55168701480000000000`

Aktueller Audit:

- Report: `docs/76_CHRONOLOGICAL_BALANCE_BREAK_AUDIT_AFTER_BINANCE_BNSOL_PRIMARY_2026-05-08.md`
- JSON: `var/chronological_balance_break_audit_current_2026-05-08_after_binance_bnsol_primary.json`

## Binance Dust Convert

Beide Restthemen beruehren Binance Dust Convert `transId 136251331484` am `2023-05-02T04:13:23Z`.

Primaerbeleg in `raw_events`:

- `dust_convert_in`: `0.00211229 BNB`
- `dust_convert_out`: `42.39387934 VTHO`
- `dust_convert_out`: `0.55379925 BUSD`
- weitere kleine Assets: `HOT`, `USDT`, `DOGE`, `EUR`, `ETH`

Die Gegenbuchung nach BNB ist vorhanden; die Herkunft der kleinen VTHO-/BUSD-Restbestaende ist im aktuellen Bestand nicht vollstaendig belegt.

## Gepruefte Zusatzquelle

Binance Asset-Dividend-History wurde fuer `2021-01-01` bis `2023-05-03` in 90-Tage-Fenstern abgefragt:

- JSON: `var/binance_asset_dividend_2021_2023_90d_probe_2026-05-08.json`
- Ergebnis: `318` Rows
- Assets: `BTTC`, `ADA`
- Keine `VTHO`- oder `BUSD`-Zufluesse gefunden.

## Review-Kandidaten

Script:

- `scripts/upsert_dust_residual_balance_candidates.py`

Gespeichert unter `runtime.balance_adjustment_candidates`, nicht steuerwirksam:

- `binance-vtho-dust-residual-2023-05-02`
  - Asset: `VTHO`
  - Betrag: `42.39387934`
  - Status: `needs_evidence`
  - `tax_effective`: `false`
- `mixed-busd-dust-residual-2023-05-02`
  - Asset: `BUSD`
  - Betrag: `0.55168701480000000000`
  - Status: `needs_review`
  - `tax_effective`: `false`

## Bewertung

Das sind keine automatisch gebuchten Korrekturen. Die Betraege sind klein und als Dust-/Altbestand-Nachweisfragen isoliert. Fuer einen finalen Steuerreport muss entschieden werden, ob ein weiterer Binance-Nachweis beschafft wird oder ob diese Kleinstbetraege als explizit dokumentierte Review-Entscheidung behandelt werden.
