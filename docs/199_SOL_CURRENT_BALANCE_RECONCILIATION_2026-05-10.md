# SOL Current Balance Reconciliation

Stand: 2026-05-10 14:42 UTC

## Ergebnis

Die vorherige Dashboard-Anzeige war nicht belastbar:

- `441.289269218 SOL` war falsch, weil Lot-Aging nicht die vollstaendige Processing-Pipeline genutzt hat.
- `179.244813777 SOL` war ebenfalls noch falsch, weil nicht gematchte Nicht-Stable-Transfer-Outs nicht als Lot-Verbrauch in die FIFO-Bestaende eingingen und Bitget-Internevents als Anschaffung behandelt wurden.
- Nach Code-Fix zeigt Port `8000` jetzt fuer `2026-12-31T23:59:59Z`:
  - Gesamt: `3.975449536 SOL`
  - Privat: `3.829842364 SOL`
  - Betriebsvermoegen: `0.145607172 SOL`

Das ist weiterhin kein endgueltig bestaetigter Realbestand. Gegen die live verifizierten Quellen bleibt eine Differenz offen.

## Live-/API-Abgleich

| Quelle | Status | SOL |
|---|---:|---:|
| Solana Wallet `wBrPoi...JbV2oB` live RPC | verifiziert | `0.236270174` |
| Binance Spot | verifiziert via Secret-Store | `1.39855608` |
| Binance Locked Earn/Staking Principal | verifiziert via Secret-Store | `9.84095708` |
| Binance Locked Earn/Staking accrued Reward-Feld | verifiziert via Secret-Store | `0.14855608` |
| Bitget API aktueller Bestand | verifiziert via Secret-Store | `0` |
| Pionex API aktueller Bestand | verifiziert via Secret-Store | `0` |
| FIFO-Modell Port 8000 | berechnet | `3.975449536` |

Verifiziert ueber Solana + Binance Spot + Binance Locked Earn Principal + Bitget + Pionex: `11.475783334 SOL`.
Wenn das Binance-Reward-Feld als aktuell zurechenbarer Anspruch mitgezaehlt wird: `11.624339414 SOL`.

Offene Differenz gegen das FIFO-Modell:

- Ohne accrued Reward-Feld: FIFO-Modell ist `7.500333798 SOL` zu niedrig.
- Mit accrued Reward-Feld: FIFO-Modell ist `7.648889878 SOL` zu niedrig.

Korrektur zum vorherigen Stand: Die API-Keys sind im Secret-Store vorhanden und funktionieren. Die vorherigen Fehler (`API-key format invalid`, `Apikey does not exist`) kamen aus einem Pfad, der nicht sauber ueber die gespeicherten Secrets lief.
Zweite Korrektur: Binance Spot allein reicht nicht; aktive Simple-Earn/Locked-Staking-Positionen liegen auf separaten Binance-Endpunkten und werden jetzt im Balance-Preview separat ausgewiesen.

## Offene FIFO-Lots nach Fix

| Bereich | Quelle | Eventtyp | Menge SOL | Hinweis |
|---|---|---|---:|---|
| private | `binance_api` | `trade` | `1.932808951` | Binance-Kaeufe/Trades, spaetere Disposal-/Withdrawal-Kette noch nicht belegt |
| private | `solana_rpc` | `sol_transfer` | `0.999914003` | Hauptlot aus Solana/Jupiter-Kontext plus Dust; Swap-Counterflow noch nicht vollstaendig als Verbrauch nachgewiesen |
| private | `binance_api` | `fiat_payment_in` | `0.897119410` | EUR-Fiatkauf vom `2025-12-19`, spaetere Veraeusserung/Transfer fehlt im Modell |
| business | `binance_api` | `asset_dividend` | `0.142624760` | 2026 Reward-/Dividend-Lots, aktuell steuerlich Betriebsvermoegen |
| business | `solana_rpc` | `sol_transfer` | `0.002982412` | 2026 Staking-/Reward-Kontext |

## Code-Fixes in diesem Schritt

- `src/tax_engine/api/dashboard.py`: Lot-Aging nutzt jetzt dieselbe bereinigte Processing-Eventbasis wie der Steuerlauf.
- `src/tax_engine/core/processor.py`: Nicht gematchte Transfer-Outs verbrauchen FIFO-Lots auch bei Nicht-Stables, erzeugen aber ohne Verkauf keinen steuerpflichtigen Disposal.
- `src/tax_engine/core/processor.py`: `fiat_balance_success_user_in/out` wird als interner Transfer behandelt, nicht als Anschaffung.
- `tests/unit/core/test_processor_fifo.py`: Tests fuer nicht gematchten Nicht-Stable-Transfer-Out und Bitget-Internevent ergaenzt.

## Bewertung

Die falschen hohen SOL-Werte sind deutlich reduziert, aber noch nicht vollstaendig reconciled. Es darf daher keine Aussage "du haeltst 3.975 SOL" in den Steuerreport uebernommen werden. Die aktuelle fachliche Aussage lautet:

> Das FIFO-Modell hat `3.975449536 SOL` offene Lots. Live verifiziert sind mindestens `11.475783334 SOL` ueber Solana-Wallet, Binance Spot, Binance Locked Earn Principal, Bitget und Pionex. Das Modell ist damit nicht mehr zu hoch, sondern um mindestens `7.500333798 SOL` zu niedrig. Die Binance-Staking-/Earn-Historie muss deshalb als historische Anschaffungs-/Transferkette in den Steuerlauf integriert werden.

## Naechste Schritte

1. Binance Locked-Earn/SOL-Position `Sol*120` historisch importieren bzw. gegen `stakingHistory`, Purchase-Zeit, Reward-Zufluesse und BNSOL/SOL-Konvertierungen abgleichen.
2. Die verifizierten aktuellen CEX-Bestaende als Reconciliation-Anker verwenden, aber nicht als Ersatz fuer fehlende historische Transaktionen.
3. Danach weiter die Restgruppen pruefen: Binance `trade` `1.932808951 SOL`, Binance `fiat_payment_in` `0.897119410 SOL`, Solana/Jupiter `sol_transfer` `0.999914003 SOL`.
4. Erst danach alle Steuerjahre erneut laufen lassen; `docs/190_CURRENT_TAX_RUNS_2026-05-10.md` ist durch diesen FIFO-Fix fachlich ueberholt.

## Validierung

- `python3 -m py_compile src/tax_engine/core/processor.py src/tax_engine/api/dashboard.py`
- `PYTHONPATH=src python3 -m pytest -q tests/unit/core/test_processor_fifo.py tests/unit/core/test_tax_domains.py tests/unit/api/test_process_endpoints.py::test_portfolio_lot_aging_shows_split_lots` -> `25 passed`
- `systemctl restart steuerreport-api.service`
- Secret-Store-Fix:
  - `src/tax_engine/connectors/models.py`: CEX-Credentials im Request optional.
  - `src/tax_engine/api/connectors.py`: fehlende CEX-Credentials werden ueber `secret.cex.<connector>.*` geladen.
  - `PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_cex_connector_endpoints.py tests/unit/api/test_admin_endpoints.py::test_admin_cex_credentials_load_returns_saved_secret_values tests/unit/connectors/test_cex_service.py` -> `29 passed`
  - `src/tax_engine/connectors/service.py`: Binance Balance-Preview zaehlt jetzt `simple_earn_flexible` und `simple_earn_locked` Positionen separat.
- Port `8000` Livecheck:
  - `GET /api/v1/portfolio/lot-aging?...&asset=SOL` -> `3.975449536 SOL`
  - `GET /api/v1/portfolio/lot-aging?...&asset=SOL&domain=private` -> `3.829842364 SOL`
  - `GET /api/v1/portfolio/lot-aging?...&asset=SOL&domain=business` -> `0.145607172 SOL`
  - `POST /api/v1/connectors/cex/verify` ohne Keys im Body -> Binance, Bitget, Pionex jeweils `success`
  - `POST /api/v1/connectors/cex/balances-preview` ohne Keys im Body -> Binance Spot `1.39855608 SOL`, Binance Locked Earn Principal `9.84095708 SOL`, Binance accrued Reward-Feld `0.14855608 SOL`, Bitget `0 SOL`, Pionex `0 SOL`
