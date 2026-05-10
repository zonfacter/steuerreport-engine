# Blockpit Solana Tail Reference Exclusions - 2026-05-08

## Ziel

Nach dem USDT-Counterflow blieben `MOBILE` und `VSR` als negative Endbestaende stehen. Die ausloesenden Zeilen waren Blockpit-Solana-Referenzen, fuer die im Datenbestand bereits Solana-/Solscan-Primaerereignisse mit derselben On-Chain-Signatur vorhanden sind.

## Umsetzung

- Script: `scripts/apply_blockpit_solana_tail_reference_exclusions.py`
- Evidence JSON: `var/blockpit_solana_tail_reference_exclusions_2026-05-08.json`
- RAW-Daten bleiben unveraendert.
- Steuerliche Wirkung erfolgt nur ueber `runtime.tax_event_overrides` mit `reference_import_only`.

## Gepruefte Signaturen

- `27KoLKddp5wYAvkJftuKL2EMrewvvNj91H83BB64LMUakFKXd32ArEVCv6Y6nq29L4c86y6joeXGUGB7wayNVMrj`
  - Blockpit: `MOBILE` out `421.837749`, `HNT` in `0.05654344`, SOL Fee
  - Primaer: Solana/Solscan Swap-Events zur gleichen Signatur
- `4oFUuoh2rhCCA8KiG1evNgb3pmYkyLwhYoiusvEWUozfjWiSg85L11zhwqQiKEU2EbJ1zMAGmKbJkDJUMrfKDNgz`
  - Blockpit: `VSR` out `1`, SOL Fee, SOL/IOT Referenzzeilen
  - Primaer: Solana Swap-Events zur gleichen Signatur
- `2h9rkbgcgaXAnNtHYCupfwrNzTnaJ9TUpbKzHSuB3B9kLmxUrwfwrHHL8gWMQfvPJ82LksmDEkxQhNHbd9AWj9kb`
  - Blockpit: `VSR` out `1`, SOL Fee, SOL/MOBILE Referenzzeilen
  - Primaer: Solana Swap-Events zur gleichen Signatur

## Ergebnis

Alle matchenden Blockpit-Zeilen dieser drei Signaturen wurden als Referenzimport ausgeschlossen. Damit werden die vorhandenen Primaer-On-Chain-Daten genutzt und die Blockpit-Doppelzaehlung entfernt.
