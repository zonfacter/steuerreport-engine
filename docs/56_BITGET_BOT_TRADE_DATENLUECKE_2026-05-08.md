# Bitget Bot-Trade Datenluecke - 2026-05-08

## Ausgangslage

- Bitget-Support ist fuer alte Daten angefragt.
- Nutzerhinweis: Bitget haelt Bot-Trade-Details moeglicherweise nicht lange genug vor; die Detaildaten koennen eventuell nicht mehr beschafft werden.
- Es geht nicht um Blockpit als Ursache. Blockpit bleibt nur Referenzquelle, soweit Daten vorhanden sind.

## Grundsatz

Fehlende Bitget-Bot-Trade-Details werden nicht erfunden und nicht automatisch durch KI rekonstruiert.

Wenn Bitget die Detaildaten nicht mehr liefern kann, wird die Luecke explizit dokumentiert und nur ueber belegbare Ersatzspuren plausibilisiert:

- Ein- und Auszahlungen zu Bitget
- interne Transfers, soweit vorhanden
- Account-/Asset-Balance-Snapshots
- realisierte PnL-/Settlement-/Funding-/Fee-Events
- vorhandene Derivate-/Tax-API-Ereignisse
- vorhandene Blockpit/WISO-Referenzdaten nur als Such- und Vergleichshinweis

## Steuerliche Behandlung im Programm

Das Programm darf in diesem Fall:

1. Die Quelle als `support_requested` und bei negativer Antwort als `unavailable_source` markieren.
2. Einen Datenlueckenvermerk je Steuerjahr und Plattform erzeugen.
3. Saldenbrueche und Differenzen rechnerisch ausweisen.
4. Plausible Zeitraeume und betroffene Assets priorisieren.
5. Einen manuellen Review-Entwurf fuer ein begruendetes Adjustment vorbereiten.

Das Programm darf nicht:

1. einzelne Bot-Trades frei erzeugen,
2. Anschaffungskosten ohne Beleg setzen,
3. Gewinne oder Verluste aus fehlenden Details automatisch schaetzen,
4. Referenzdaten blind als Primaerquelle uebernehmen,
5. Liquidationen oder Hebelverluste ohne Einsatz-/Settlement-Bezug steuerwirksam buchen.

## Rekonstruktionslogik

Wenn Bot-Trade-Details fehlen, ist die belastbarste Ersatzlogik:

1. Startbestand vor Bot-Phase feststellen.
2. externe Zufluesse/Abfluesse abgrenzen.
3. Endbestand nach Bot-Phase feststellen.
4. bekannte Fees, Funding, Settlements und realisierte PnL einbeziehen.
5. Differenz als offene Datenluecke ausweisen.
6. Nur bei ausreichendem Nachweis ein manuelles Adjustment mit Kommentar und Belegstatus vorbereiten.

Formelhaft:

`Endbestand - Startbestand - externe Zufluesse + externe Abfluesse - bekannte PnL/Funding/Fee = offene Bot-Differenz`

Diese Differenz ist kein automatisch steuerwirksamer Trade, sondern ein Review-Befund.

## Naechste Umsetzung

- CEX-Coverage-Audit fuehrt Bitget ab jetzt mit:
  - `support_required`
  - `manual_review`
  - `unavailable_source_possible`
- Nach Support-Antwort:
  - wenn Daten kommen: Importer/Parser bauen oder vorhandenen Importpfad nutzen.
  - wenn Daten nicht kommen: Antwort als Beleg speichern und Bitget-Rekonstruktionsbericht erzeugen.

## Externe Evidenz 2026-05-08

Um moegliche Ersatz-/Plausibilitaetsquellen nicht nur theoretisch zu bewerten, wurde ein externer Evidenz-Audit ausgefuehrt:

- Script: `scripts/bitget_external_evidence_audit.py`
- Report: `docs/57_BITGET_EXTERNAL_EVIDENCE_AUDIT_2026-05-08.md`
- JSON: `var/bitget_external_evidence_audit_2026-05-08.json`
- Rohdaten: `var/external_evidence/bitget_public_market_2026-05-08/`

Gesichert wurden:

- Bitget Public Spot-Daily-Candles fuer `JUPUSDT`, `HNTUSDT`, `XRPUSDT`, `SOLUSDT`, `BTCUSDT`
- Bitget Public Futures-Daily-Candles fuer dieselben Symbole, soweit verfuegbar
- Solana-RPC-Belege fuer zwei Bitget-API-Withdrawals:
  - JUP Withdrawal `2025-06-15T07:30:36Z`, Chain-Zeit `2025-06-15T07:30:12Z`
  - SOL Withdrawal `2025-06-15T07:45:46Z`, Chain-Zeit `2025-06-15T07:45:21Z`

Bewertung:

- On-Chain-Transfers sind externe Primaerbelege fuer Ein-/Auszahlungen.
- Public-Market-Candles sind nur Preis-/Markt-Plausibilitaet.
- Public-Funding-Rate-Historie wurde versucht; fuer den betroffenen 2024/2025-Zeitraum lieferte der Public-Endpunkt keine passenden Zeilen.
- Kein externer Marktanbieter kann beweisen, welche oeffentlichen Trades zu diesem Bitget-Konto/Bot gehoerten.

## Rekonstruktionsstand 2026-05-08

Zusaetzlich wurde ein Bitget-Rekonstruktionsaudit aus den vorhandenen Events erstellt:

- Script: `scripts/bitget_reconstruction_audit.py`
- Report: `docs/58_BITGET_RECONSTRUCTION_AUDIT_2026-05-08.md`
- JSON: `var/bitget_reconstruction_audit_2026-05-08.json`

Wichtiger Befund:

- Nach Beruecksichtigung der in Bitget-Rohzeilen enthaltenen Fees ist USDT aus den verfuegbaren Primaerevents nahezu geschlossen:
  - Net Primary `-6.430858137166 USDT`
  - letzter gemeldeter Bitget-Balance-Wert praktisch `0`
- Viele Balance-Brueche entstehen durch Teilfills mit gleichem Timestamp und Account-/Strategy-/Derivate-Kontextwechsel, nicht automatisch durch fehlende externe Einzahlungen.
- Derivate-Open-/Close-/Loss-/Fee-Zeilen bleiben gesondert zu pruefen; sie duerfen nicht pauschal als Spot-Bestand interpretiert werden.

Fokussierte USDT-Strategy-Kette:

- Script: `scripts/bitget_usdt_strategy_chain.py`
- Report: `docs/59_BITGET_USDT_STRATEGY_CHAIN_2026-05-08.md`
- JSON: `var/bitget_usdt_strategy_chain_2026-05-08.json`

Kernbefund:

- `2025-01-29`: Bitget USDT Deposit `5009.09824537`
- interne Exchange-Transfers am `2025-01-29`, `2025-01-31`, `2025-02-01`
- Strategy-Paar am `2025-02-22`:
  - `-249.59902416 USDT` zu Strategy
  - `+248.38877526 USDT` von Strategy
  - netto `-1.21024890 USDT`
- `2025-02-27`: Risk-Capital-Transfer `-222.10227813 USDT`, zeitlich passend zum Derivate-/Liquidationsbereich.

Diese Kette stuetzt eine saldenbasierte Rekonstruktion, ersetzt aber keine fehlenden Bot-Fill-Details.

## Derivate-/Liquidationsfenster 2025-02-20 bis 2025-03-05

Der naechste Fokusbericht wurde erstellt:

- Script: `scripts/bitget_derivative_liquidation_audit.py`
- Report: `docs/60_BITGET_DERIVATIVE_LIQUIDATION_AUDIT_2026-05-08.md`
- JSON: `var/bitget_derivative_liquidation_audit_2026-05-08.json`

Befund:

- Fenster: `425` Bitget-nahe Zeilen
  - `405` Bitget-Tax-API-Primary
  - `20` Blockpit-Referenz
- Open-Long/Open-Short-Zeilen haben `gross_amount = 0`; steuer-/saldenwirksam ist dort nur die Fee.
- Close-Long/Close-Short-Zeilen tragen realisierte PnL plus Fee und sind saldenwirksam.
- Genau eine Primaer-Loss-/Liquidationszeile:
  - `2025-02-27T15:01:18.007Z`
  - `HNTUSDT`
  - `burst_long_loss_query`
  - Gross Loss `-396.16940001 USDT`
  - Fee `-7.21515168 USDT`
  - Balance Effect `-403.38455169 USDT`
- Direkt danach:
  - `2025-02-27T15:01:19.616Z`
  - `risk_captital_user_transfer`
  - `-222.10227813 USDT`
  - gemeldeter Balance danach `0`

Bewertung:

- Hebel-/Liquidationsverlust wird aus den Primaerzeilen als tatsaechlicher USDT-Balance-Effect betrachtet, nicht als Hebel-Notional.
- Die gehebelte Positionsgroesse wird nicht als steuerlicher Einsatz vervielfacht.
- Blockpit-Referenzzeilen duerfen in diesem Fenster nicht zusaetzlich zu Bitget-Primary addiert werden, solange sie gematcht/erklaerbar sind.
