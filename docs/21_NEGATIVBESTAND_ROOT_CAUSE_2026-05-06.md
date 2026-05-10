# Negativbestand Root-Cause Report

Stand: 2026-05-06

Scope: Steuerjahre 2020-2025 nach Pionex-Importen und selektivem Binance-Export-Import aus `/workspace/steuerreport/usertransfer/Binance/export 2021/`.

## Kurzfazit

- Normale Issue-Inbox: `0`.
- Process-Preflight 2021-2025: jeweils `allow_run=true`, keine Blocker.
- USDT-Unterdeckung 2021 ist durch Binance-Fiat-/Kartenkaufdaten behoben; 2022+ ist jetzt als Pionex-Startbestands-/Vorperiodenproblem eingegrenzt.
- Binance-API-30-Tage-Abfrage fuer Capital/Dividends/Dust hat BNB bereinigt, aber neue kleine Dust-/Transfer-Cluster sichtbar gemacht.
- EUR-Fiat-Unterdeckung wurde bereinigt: doppelter 2021-Card-Withdraw ausgeschlossen und externe Kartenkauf-EUR-Legs aus `fiat_crypto_purchase` aus der Bestandskette entfernt. Crypto-In-Legs bleiben erhalten.
- Alle verbleibenden Negativbestand-Zeilen stehen auf `in_review`.
- Verbleibende Arbeit ist kein Preisproblem, sondern Datenvollstaendigkeit/Referenz-Deduplizierung/Fiat-Modellierung.

## Live-Stand Negativbestand

| Jahr | Zeilen | Status | Assets |
| --- | ---: | --- | --- |
| 2020 | 0 | - | - |
| 2021 | 0 | - | - |
| 2022 | 12 | alle `in_review` | `USDT` 12 |
| 2023 | 28 | alle `in_review` | `USDT` 12, `BUSD` 8, `VTHO` 8 |
| 2024 | 37 | alle `in_review` | `SOL` 1, `USDT` 12, `BUSD` 12, `VTHO` 12 |
| 2025 | 37 | alle `in_review` | `USDT` 12, `BUSD` 12, `MOBILE` 1, `VTHO` 12 |

## Binance-API Update

Stand: 2026-05-06

- Binance-Credentials sind als Secrets gespeichert und live verifiziert.
- Ein generischer Binance-Vollimport ab 2020 wurde abgebrochen, weil der Spot-Trade-Pfad `myTrades` wegen 24h-Fenstern und vieler Symbolkandidaten zu langsam ist.
- Stattdessen wurde ein stabiler 30-Tage-Import fuer Capital/Dividends/Dust ausgefuehrt:
  - `1934` Events gefunden
  - `109` neu eingefuegt
  - `1825` Duplikate
  - `asset_dividend` 1872, `deposit` 25, `withdrawal` 11, `dust_convert_out` 23, `dust_convert_in` 3
- Universal Transfers sind fuer historische Binance-Fenster nicht per API gekommen (`400`/Limitierung); diese bleiben Export- oder aktueller-Fenster-Kandidat.
- Ergebnis: BNB-Altbestand wurde bereinigt; neue kleine Cluster `BUSD`/`VTHO` stammen aus Binance-Dust-Conversions. `SOL` wurde durch Binance-API-Withdrawals sichtbarer und braucht Transferkettenabgleich mit Solana-RPC.
- Exakte Binance-API-vs-Blockpit-Referenzduplikate wurden ausgeschlossen:
  - `7` Integration-Konflikte per Resolve
  - `3` Blockpit Auto-Balancing-Outs fuer `CDT`, `COTI`, `WABI` wegen mengenidentischer Binance-Dust-Conversions

## Jupiter-Perps Update

Stand: 2026-05-06

- Quelle: `/workspace/steuerreport/usertransfer/jup/wBrPoiEEzKYwH6obgAmNAC2iskiNs4HvwoAwqJbV2oB.csv`.
- Neuer Connector `jupiter_perps` implementiert.
- `68` korrigierte Perps-v2-Events importiert; alte Jupiter-Perps-Importstaende wurden per `EXCLUDED/duplicate_import` ersetzt (`136` Events).
- Zeitraum: `2024-03-30T06:27:32Z` bis `2024-12-06T16:27:25Z`.
- Assets: `SOL` 50, `BTC` 18.
- Derivate-Smoke 2024:
  - `processed_events=68`
  - `derivative_line_count=36`
  - `open_positions_remaining=0`
  - `unmatched_closes=4`
  - `termingeschaefte.netto_eur=-8413.69`
  - `termingeschaefte.verlust_summe_abs_eur=20149.13`
- Interpretation: Der Export enthaelt echte Jupiter-Perps-Hebeltrades und fuehrt nun zu Termingeschaeftszeilen. Die v2-Paarung beseitigt kuenstliche offene Positionen; `4` unmatched closes deuten auf Positionen hin, die vor Exportbeginn bereits offen waren.

## Prioritaet 1: USDT ab 2022

Update nach Pionex-Gesamtexport 2026-05-06:
- Neue Quelle: `/workspace/steuerreport/usertransfer/pionex/`.
- `deposit-withdraw.csv` enthaelt den bisher inferierten `200 USDT`-Deposit vom `2021-12-25` nun als echte Pionex-Zeile; das inferierte Ersatz-Event wurde per Override ausgeschlossen.
- `trading.csv` enthaelt `597` aggregierte Trades, normalisiert zu `1791` Trade-/Fee-Legs. Die alten Pionex-Trading-Teilimporte wurden als `EXCLUDED/duplicate_import` markiert, damit keine Doppelzaehlung entsteht.
- `raw-trading-details.csv`, CoinTracker- und CoinTracking-Exports wurden nicht importiert, weil sie dieselben Bewegungen erneut darstellen.
- Effekt: 2021 ist in der Negativbestand-Pruefung jetzt sauber (`0` Zeilen). 2022 bleibt mit `12` USDT-Checkpoints offen/in_review.
- Erste sichtbare USDT-Unterdeckung nach dem neuen Pionex-Stand: `2022-01-05T11:40:01Z`, verursacht durch Pionex-USDT-Trade-Out bei noch nicht ausreichendem Pionex-Start-/Bot-Bestand.
- Nutzerhinweis: Der neue Pionex-CSV-Export war bereits maximal in die Vergangenheit. Ein aelterer CSV-Export ist daher nicht mehr als naechster Schritt einzuplanen.
- Konkreter erster Ausloeser: Pionex `BUY EGLD_USDT` am `2022-01-05T11:40:01Z`, `346.928820 USDT` Out, Tax-ID `s_7`; direkt davor rechnerisch ca. `271.6432022538 USDT`.
- Maximale rechnerische USDT-Luecke bis Ende 2022: `3873.7487919711 USDT` bei `2022-09-10T00:20:08Z`, Pionex `s_16:472:out:USDT`.
- Damit ist nicht mehr der `2021-12-25`-Deposit die offene Frage, sondern der Pionex-Startbestand/Bot-Grid-Kontext vor Anfang Januar 2022 oder ein belegter Opening-Balance-Adjustment.
- Nutzer-Erinnerung geprueft: Wahrscheinlicher Ablauf war Legacy-HNT -> Binance -> HNT/USDT-Trade -> USDT-Transfer zu Pionex.
  - Belegt: `2021-12-13T13:15:57Z` Legacy-HNT `11.011985972987041 HNT` an Binance-Adresse `138bCXPV...`, Binance-Deposit `11 HNT` um `2021-12-13T13:19:15Z`.
  - Belegt: Binance HNT->USDT-Verkaeufe, z.B. `2021-12-17T23:16:00Z` gesamt ca. `100.17 HNT` out und `3393.2075 USDT` in.
  - Belegt: Binance-USDT-Withdrawal zu Pionex-Adresse `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ`: `200 USDT` am `2021-12-25T16:19:40Z`, Pionex-Deposit `2021-12-25T16:23:04Z`; spaeter `1245.38419 USDT` am `2022-01-19`.
  - Geklaert durch Nutzerhinweis: `2022-01-02T07:11:07Z` Legacy-HNT `5.527633237150866 HNT` an `13m4dW...` war sehr wahrscheinlich die Adresse fuer Heliumtracker bzw. eine Dienstleistungszahlung. Diese Adresse ist damit kein Pionex-/Binance-Zuflusskandidat und erklaert die USDT-Luecke nicht.
  - Heliumtracker-API: Nutzerhinweis `2026-05-07`, API funktioniert nur mit aktivem Abo; aktuell nicht aktiv. Daher keine aktive API-Quelle fuer weitere Rekonstruktion. Der Secret-Speicherversuch hat keinen Key gespeichert (`stored False`).

Update 2026-05-06:
- Connector-Fix umgesetzt: Bitget Futures-Bills `/api/v2/mix/account/bill` nutzt jetzt die dokumentierten Product Types `USDT-FUTURES`, `COIN-FUTURES`, `USDC-FUTURES` und Limit `100`.
- Spot-Fills `/api/v2/spot/trade/fills` nutzt jetzt Limit `100`; aeltere Spot-Fills bleiben laut Bitget-API nur 90 Tage direkt abrufbar und muessen fuer aeltere Zeitraeume aus Web-Exports kommen.
- Live-Reimport 2024-11-01 bis 2025-04-30 in 30-Tage-Fenstern: `1059` Bitget-Zeilen gefunden, davon `965` neu eingefuegt und `94` Duplikate.
- Neue Bitget-Futures-Verteilung im kritischen Zeitraum: `USDT` 1011 Events, darunter `derivative open_long` 234, `derivative close_long` 220, `derivative close_short` 189, `derivative open_short` 179, `derivative fee` 133, `derivative loss` 2.
- Exakte USDT-Duplikate Blockpit vs. Bitget-Tax-API 2025 wurden per Review-Resolve bereinigt: `21` Konflikte, `24` Blockpit-Referenzevents als `EXCLUDED/reference_import_only`.
- Nettoeffekt: USDT 2025 verbessert sich durch Futures-Bills um ca. `1000 USDT`, bleibt aber deutlich negativ. Die Luecke ist dadurch nicht geloest.

Status:
- 2021 USDT ist behoben.
- 2022-USDT bleibt mit 12 Checkpoints offen/in_review.
- Erste 2022-Unterdeckung nach Pionex-Gesamtexport: `2022-01-05T11:40:01Z`.
- Belegter Binance-API-Withdrawal `200 USDT` vom `2021-12-25T16:19:40Z`, TX `b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182`, Zieladresse `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ`, ist jetzt durch den echten Pionex-CSV-Deposit belegt; das fruehere `pionex_inferred`-Event ist ausgeschlossen.
- Verbleibende Ursache: Pionex-Bot-/Spot-Trades laufen Anfang Januar 2022 gegen einen nicht vollstaendig belegten Startbestand. Benoetigt werden Opening Balances/Bot-Startkapital und ggf. Bot-Grid-Historie vor `2022-01-05`.
- 2024 hat noch `1` USDT-Checkpoint: `negative_balance:2024-12-10:USDT`, Saldo `-1827.2453212930398875 USDT`.
- 2025 hat noch `12` USDT-Checkpoints; erster 2025-Checkpoint nach Futures-Import: `negative_balance:2025-01-29:USDT`, Saldo `-5438.7185313449465875 USDT`.

Beobachtung:
- 2024-USDT enthaelt Binance, Solana-RPC, Pionex und Bitget.
- Rund um 2024-11-29 bis 2024-12-07 sind Bitget-Tax-API-Bewegungen sichtbar:
  - `2024-11-29` Deposit `800.000001 USDT` und `200 USDT`.
  - `2024-11-29` Automatic Withdrawal `1000.00980248 USDT`.
  - `2024-12-01` Automatic Deposits ca. `983.799306313 USDT`.
  - `2024-12-01` Withdrawal `1988.0082607 USDT`.
  - `2024-12-07` Deposit `600 USDT`, danach Transfer Out `600 USDT`.
- 2025-USDT zeigt viele parallele Blockpit- und Bitget-Tax-API-Zeilen mit nahezu identischen Zeitpunkten und Mengen.
- Beispiel 2025-04-22/23:
  - Blockpit und Bitget liefern beide Trade-In/Trade-Out-Zeilen.
  - Bitget liefert zusaetzlich `fiat_balance_success_user_in` `1127.2308 USDT` am `2025-04-23T07:18:44.890Z`.
- Es sind Derivate-/Fee-/Loss-Zeilen sichtbar, z.B. `2025-04-07` Blockpit `derivative loss` und mehrere `derivative fee`-Abgaenge.

Wahrscheinliche Ursache:
- Kombination aus fehlender Bitget-/Bot-/Derivate-Konto-Historie und doppelter Referenzzaehlung Blockpit vs. Bitget-Tax-API.
- Fuer 2025 ist Blockpit an mehreren Stellen eher Referenzquelle, waehrend Bitget-Tax-API die Primaerquelle sein kann.
- Nach Futures-Bill-Fix ist nicht mehr der technische Futures-Bill-Endpoint der Hauptblocker; es fehlt weiterhin frueherer Start-/Transfer-/Bot-Kontext ab `2022-01-19`.

Naechste benoetigte Quelle:
- Bitget Bot/Grid/Strategy Account Statements und interne Transfers, insbesondere vor und um `2025-01-29`.
- Bitget interne Transfers zwischen Spot/Futures/Bot/Funding fuer denselben Zeitraum.
- Falls Bitget keine Historie mehr liefert: vorhandene Blockpit-Zeilen gegen Bitget-Tax-API deduplizieren und nur eine Primaerquelle pro identischem Trade/Transfer behalten.

Empfohlene Bearbeitung:
- Naechster Schritt: Bitget Spot Account Bills `/api/v2/spot/account/bills` und ggf. Strategy/Bot-Exports pruefen. Diese koennen Transfers/Bot-Kontobewegungen enthalten, die in Tax-Spot und Futures-Bills noch fehlen.
- Danach erneut USDT 2024/2025 pruefen.
- Erst danach fehlende Transfers/Startsalden manuell modellieren.

## Erledigt: BNB 2021-2025

Status:
- Nach Binance-API-Importen und Pionex-Gesamtexport ist BNB aus der Negativbestand-Pruefung verschwunden.
- Live-Check nach Pionex-Import:
  - `2021`: `0` Negativbestand-Zeilen.
  - `2022`: nur noch `USDT`.
  - `2023-2025`: keine BNB-Zeilen.

Beobachtung:
- Binance 2021 zeigt:
  - `2021-02-06T21:18:15Z` Fiat/Krypto-Kauf `+1.625 BNB`.
  - `2021-02-06T21:23:58Z` Trade Out `-1.6 BNB`.
  - `2021-04-26T20:20:25Z` Trade In `+0.08 BNB`.
  - `2021-04-28T05:05:03Z` Trade Out `-0.07 BNB`.
  - `2021-04-28T05:14:45Z` mehrere Trade In: `+0.98`, `+0.08`, `+1.14 BNB`.
  - `2021-04-28T05:53:14Z` Trade Out `-2.47 BNB`.
- Nach zusaetzlichen Binance-API-Daten war der urspruengliche BNB-Fehlbetrag bereits deutlich kleiner.
- Der aktuelle effektive Eventbestand erzeugt keinen BNB-Negativbestand mehr.

Empfohlene Bearbeitung:
- Keine BNB-Spezialquelle mehr priorisieren, solange der Live-Check keine neuen BNB-Zeilen zeigt.

## Erledigt: EUR 2021-2025

Status:
- Ausgangslage nach selektivem Binance-Import: 2021-2023 ca. `-2026 EUR`, spaeter ebenfalls EUR-Unterdeckungen.
- Nach Ausschluss eines doppelten Card-Withdraws fiel 2021 auf ca. `-1001.67 EUR`.
- Die restliche Unterdeckung kam aus vier Binance-`fiat_crypto_purchase`-EUR-Legs:
  - `2021-02-06T21:18:15Z` `-98.10 EUR`
  - `2021-02-23T10:57:37Z` `-98.10 EUR`
  - `2021-03-24T20:13:43Z` `-127.53 EUR`
  - `2021-04-19T15:17:37Z` `-981.00 EUR`

Beobachtung:
- EUR wurde erst durch den selektiven Binance-Fiatimport voll sichtbar.
- Erste negative Stelle: `2021-02-06T21:18:15Z` durch Binance-Kartenkauf `-98.1 EUR`.
- Binance 2021 enthaelt spaeter Fiat-Deposits, Fiat-Withdrawals und EUR-Trades.
- Doppelte Binance-Card-Auszahlung `2021-03-27T13:16:45Z` / TX `aaeb9e8e0cd8401fbefce34c0223f435`: alte `Export Withdraw History`-Receive-Amount-Zeile `1024.65 EUR` ausgeschlossen; Fiat-Withdraw-Zeile `1035.00 EUR` inkl. Fee bleibt.

Interpretation:
- `fiat_crypto_purchase`-EUR-Legs stammen aus externen Karten-/Bankkaeufen und duerfen in der Bestandspruefung nicht als Verbrauch eines vorhandenen Binance-EUR-Lots modelliert werden.
- Die zugehoerigen Crypto-In-Legs bleiben fuer Anschaffung/Bewertung erhalten.

Ergebnis:
- 2021 Negativbestaende: `0`.
- EUR ist aus den Folgejahres-Negativbestaenden entfernt.
- 2021 Steuerlauf nach Bereinigung: Job `2e3a653f-bf7e-473f-9fec-aa6f146296e1` completed, `tax_lines=1112`, `derivative_lines=0`, FX `unresolved_count=0`.

## Prioritaet 4: MOBILE 2025

Status:
- Einzelcheckpoint: `negative_balance:2025-12-26:MOBILE`.
- Saldo: `-421.837749 MOBILE`, Wert ca. `-0.0838422 USD`.

Beobachtung:
- `2025-12-20T12:13:50Z` Blockpit Trade Out `-421.837749 MOBILE`.
- `2025-12-26T21:07:02Z` Blockpit Deposit In `+64729.546356 MOBILE`.
- `2025-12-26T21:07:12Z` Blockpit Trade Out `-64729.546356 MOBILE`.

Wahrscheinliche Ursache:
- Reihenfolgeproblem oder fehlender kleiner MOBILE-Zufluss vor `2025-12-20`.
- Materiell sehr klein.

Naechste benoetigte Quelle:
- Solana/Helium MOBILE-Zufluss vor `2025-12-20`, falls vorhanden.
- Sonst dokumentierter kleiner Adjustment oder Reihenfolgekorrektur.

## Empfohlene Reihenfolge ab jetzt

1. Pionex-USDT mit Beleg korrigieren: CSV ist maximal historisch, daher Opening-Balance/Bot-Startkapital/Bot-Grid-Statement oder dokumentierter manueller Adjustment. Rechnerisch waeren bis Ende 2022 `3873.7487919711 USDT` noetig, damit USDT nie negativ wird.
2. Danach Blockpit-vs-Bitget-Deduplizierung fuer USDT 2025 bauen/pruefen.
3. Bitget Bot/Futures/interne Transferhistorie fuer 2024-11 bis 2025-04 nachziehen, soweit API/Export verfuegbar.
   - Futures-Bills sind technisch repariert und importiert.
   - Offen: Spot Account Bills und Strategy/Bot-Statements.
4. SOL/BUSD/VTHO-Cluster pruefen:
   - BUSD/VTHO stammen aus Binance-Dust-Conversions und wirken materiell klein.
   - SOL braucht Transferkettenabgleich zwischen Binance-API und Solana-RPC.
5. EUR-Regel bei zukuenftigen Imports beibehalten: externe Fiat-Kaeufe nicht als negative Binance-EUR-Bestandsverbraeuche modellieren.
6. MOBILE als kleiner Einzelcase nach Solana/Helium-Beleg pruefen oder dokumentiert adjustieren.
