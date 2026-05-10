# Solscan Wallet Deepdive Plan und Status 2026-05-08

Wallet: `wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB`

## Plan

1. Fehlende Solscan-Signaturen gegen lokale Imports klassifizieren.
2. Deterministischen Preview aus Solscan-Rohdaten erstellen.
3. Nur sichere, bekannte fungible Bewegungen importierbar machen.
4. Nach Import/Exclusion die chronologische Bestandspruefung erneut ausfuehren.
5. Restluecken dokumentieren und gezielt weiter abarbeiten.

## Umgesetzt

- Solscan-Wallet-Historie lokal gespeichert:
  - `2372` Account-Transactions
  - `2745` Account-Transfers
  - `2368` Transaction-Details
- Tabellen:
  - `solscan_transactions`
  - `solscan_account_transactions`
  - `solscan_account_transfers`
- Scripts:
  - `scripts/solscan_transaction_backfill.py`
  - `scripts/solscan_wallet_discovery.py`
  - `scripts/solscan_missing_event_preview.py`
  - `scripts/solscan_missing_event_import.py`

## Wichtige Korrektur

Die erste Missing-Erkennung filterte lokale `solana_rpc`-Signaturen nach `wallet_address`.
Das war zu eng, weil aeltere lokale Solana-Events nicht immer `wallet_address` tragen.

Ergebnis:

- Gegen `solana_rpc` + `wallet_address`: scheinbar `170` fehlende Signaturen.
- Gegen alle lokalen `solana_rpc`-Signaturen: tatsaechlich nur `8` fehlende Signaturen.
- `162` Signaturen waren also bereits lokal vorhanden, aber ohne passenden Wallet-Adressfilter.

Der Probeimport aus der zu engen Erkennung wurde nicht geloescht, sondern per `runtime.tax_event_overrides` ausgeschlossen:

- Quelle: `solscan_wallet_discovery_safe_wBrPoi_2026-05-08`
- Exkludiert: `274` Probeimport-Events
- Wieder aktiviert: `5` echte HNT-Eingangs-Events aus 2026

## Echte Restluecke

True-Missing-Preview:

- Datei: `docs/44_SOLSCAN_TRUE_MISSING_EVENT_PREVIEW_wBrPoi_2026-05-08.md`
- JSON: `var/solscan_missing_event_preview_true_missing_wBrPoi_2026-05-08.json`
- Fehlende Signaturen: `8`
- Vorgeschlagene Event-Zeilen: `7`

Klassen:

- `transfer_in_or_airdrop`: `5`
- `technical_account_or_metadata`: `2`
- `mixed_transfer`: `1`

Import-/Aktivierungsstand:

- `5` HNT-Eingangs-Events aus 2026 sind aktiv.
- `2` technische System-Events erzeugen keine Steuerbewegung.
- `1` mixed Transfer bleibt offen, weil HNT-Eingang und SOL-Out in derselben Signatur nicht blind importiert werden sollen.

## Auswirkung auf Bestandspruefung

Aktueller Audit nach korrigierter Solscan-Behandlung:

- Report: `docs/46_CHRONOLOGICAL_BALANCE_BREAK_AUDIT_AFTER_SOLSCAN_TRUE_MISSING_2026-05-08.md`
- JSON: `var/chronological_balance_break_audit_after_solscan_true_missing_2026-05-08.json`
- Bewegungen: `39234`
- Assets mit negativem Endbestand: `6`

Unveraenderte Hauptluecken:

- `USDT`: `-4499.90655736203488750000`
- `MOBILE`: `-421.837749`
- `VTHO`: `-42.39387934`
- `BNSOL`: `-22.323042230`
- `VSR`: `-2`
- `BUSD`: `-0.55168701480000000000`

Wichtig:

- Solscan klaert die grosse 2024/2025-USDT-Unterdeckung nicht durch fehlende Wallet-Signaturen.
- Die 2024-Solana-Aktivitaet war groesstenteils bereits vorhanden; die scheinbare Luecke kam vom zu engen Wallet-Adressvergleich.
- Die USDT-Unterdeckung bleibt weiterhin primaer bei Pionex/Binance/Transferkette zu klaeren.

## Naechste konkrete Schritte

1. Den einen `mixed_transfer` aus der True-Missing-Liste manuell pruefen.
2. Solscan-Daten nicht erneut als breite Quelle importieren, bevor ein Duplicate-Abgleich gegen alle `tx_id/signature` laeuft.
3. Fokus zurueck auf USDT-Unterdeckung:
   - Pionex Anfang 2022 Opening Balance/Bot-Startkapital.
   - Binance/Legacy-HNT -> USDT -> Pionex Transferkette.
   - Pionex FIAT-/USDT-Auszahlungen und Bot-Trading-Historie.
4. Fuer Solana kuenftig: Wallet-Discovery als Kontrollschicht verwenden, nicht als blinden Zweitimport.
