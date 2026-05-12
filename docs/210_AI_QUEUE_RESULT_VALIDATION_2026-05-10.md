# AI Queue Result Validation - 2026-05-10

## Ergebnisueberblick

Die lokale KI hat alle 5 Queue-Auftraege erfolgreich abgeschlossen.

- Ergebnisindex: `var/ai_readonly_queue/results.jsonl`
- HNT 2021: `var/ai_db_countercheck_2026-05-10_180842.md`
- JUP 2024: `var/ai_db_countercheck_2026-05-10_181252.md`
- HNT 2022: `var/ai_db_countercheck_2026-05-10_181632.md`
- Low-Value: `var/ai_db_countercheck_2026-05-10_182004.md`
- USDT 2022: `var/ai_db_countercheck_2026-05-10_182551.md`

## Validierte Punkte

### HNT 2021

KI-Aussage: kritischer Evidenz-Gap, keine deterministischen Fixes.

Validierung:

- Korrekt fuer 6 Zeilen ohne `lot_source_event_id`.
- Teilweise unvollstaendig fuer 2 Zeilen mit `lot_source_event_id=dd5353eedbee68d33a5c687e013b67f468dac6a769af6b56b60dfd7c1e40fa2f`.
- Dieses Lot ist ein Binance-HNT-Deposit:
  - `2021-08-20T08:04:08+00:00`
  - Quelle `binance_api`
  - Menge `18.30256046 HNT`
  - TX `s5UTv0W7IKEjmQllRvKtELqfAnVuBFoDmSBHyyQf0R4`
- Passender Transfer-Match existiert:
  - Match `ddec12db-878f-4285-b40a-16df945a301a`
  - Methode `txid_verified_hnt_legacy_to_binance`

Bewertung:

- Transferkette Legacy -> Binance ist belegt.
- Anschaffungskosten bleiben offen, solange die vorgelagerte HNT-Entstehung nicht als Mining/Reward oder Kauf belegt ist.
- Kein automatischer Cost-Basis-Fix.

### HNT 2022

KI-Aussage: `lot_source_event_id` fehle in `product_position_events`, Transfer-Match fehle.

Validierung:

- Als Aussage zu `product_position_events` technisch richtig, aber fuer HNT-Transferlots nicht massgeblich.
- In `raw_events` existiert das Lot:
  - Event `9dd85d203cebbe23d40ff09ddd91b30758c3d255c6f80dadbb27581ab152bcba`
  - `2022-07-12T07:08:01+00:00`
  - Quelle `binance_api`
  - Typ `deposit`
  - Menge `450 HNT`
  - TX `a12e2NxK6qfyqeZ01gc1Mj_qBCRZfAei-W1J6pWgEFE`
- Passender Transfer-Match existiert:
  - Match `728264aa-94fe-43ec-a49f-ed9a3a5af447`
  - Methode `txid_verified_hnt_legacy_to_binance`

Bewertung:

- Die KI hat hier eine falsche Schlussfolgerung gezogen, weil sie `product_position_events` zu stark gewichtet hat.
- Der Binance-Deposit und Legacy-Transfer sind belegt.
- Offen bleibt die vorgelagerte HNT-Kostenbasis/Reward-Einordnung.
- Kein automatischer Cost-Basis-Fix ohne Herkunftsnachweis.

### USDT 2022

KI-Aussage: fehlende Buy-/Deposit-Events, moeglicher Stablecoin-Cost-Basis-Bruch.

Validierung:

- Grundrichtung korrekt: Es geht um fehlende/erschoepfte USDT-Lots.
- Wichtige Praezisierung: Die drei Zero-Cost-Zeilen sind Tail-Splits von Verkaufs-Events, bei denen vorherige Teilmengen bereits eine Cost Basis hatten.
- Beispiel `fe0305...`:
  - Line 410: `82.4945748119 USDT`, Cost Basis vorhanden.
  - Line 411: `28.6708029819 USDT`, Cost Basis vorhanden.
  - Line 412: `75.1046222062 USDT`, Cost Basis `0`.
- Beispiel `a20292...`:
  - Lines 439-441 haben Cost Basis.
  - Line 442 ist Zero-Cost-Rest.
- Beispiel `b5422...`:
  - Lines 512-513 haben Cost Basis.
  - Line 514 ist Zero-Cost-Rest.

Bewertung:

- Das ist eher ein FIFO-Bestands-/Opening-Problem als ein einzelnes fehlendes USDT-Event.
- Die vorhandenen Pionex/Binance-USDT-Fluesse vor Januar 2022 muessen gegen die FIFO-Lotbildung geprueft werden.
- Kein manueller Stablecoin-1:1-Fix ohne belegte Quelle.

### JUP 2024

KI-Aussage: Airdrop nicht belegt; DCA/Transfer nicht sicher als Cost Basis nutzbar.

Validierung:

- Korrekt: Fuer die drei Zero-Cost-Zeilen gibt es keine `lot_source_event_id`.
- Praezisierung: Auch hier sind es Tail-Splits von Swap-Out-Events, bei denen andere Teilmengen Cost Basis haben.
- Beispiel `6f655c...`:
  - Lines 1494-1497 haben Cost Basis.
  - Line 1498 ist Zero-Cost-Rest `1745.251226 JUP`.
- Beispiel `856a7...`:
  - Lines 1520-1521 haben Cost Basis.
  - Line 1522 ist Zero-Cost-Rest `106.471986 JUP`.
- Beispiel `79935...`:
  - Line 1577 hat Cost Basis.
  - Line 1578 ist Zero-Cost-Rest `1 JUP`.

Bewertung:

- Kein sicherer Airdrop-Nachweis aus den KI-Ergebnissen.
- Kein sicherer DCA-Match als Cost-Basis-Quelle.
- Es handelt sich um Restmengen, fuer die die FIFO-Lotbasis nicht vollstaendig verfuegbar ist.

### Low-Value Noise

KI-Aussage: kleine Restposten separat behandeln.

Validierung:

- Sinnvoll als Arbeitsmodus.
- Groessere Low-Value-Themen sind nicht alle klein:
  - IOT 2024 `302.75 EUR`
  - IOT 2023 `83.87 EUR`
  - CBDC 2024 `91.52 EUR`
  - 25HAYB...MTDJ 2024 `74.01 EUR`
- DOGE 2021 `0.05 EUR`, USDC 2024 `0.00 EUR` und BNB 2021 `0.00 EUR` sind echte Dust-/Rundungskandidaten.

Bewertung:

- Dust separat behandeln.
- IOT/CBDC/25HAYB nicht als reine Rundung wegklassifizieren.

## Naechste sichere Schritte

1. HNT 2021/2022:
   - Legacy-HNT-Origin fuer die betroffenen Binance-Deposits pruefen.
   - Entscheiden, ob Mining/Reward-Nachweis vorhanden ist oder als Evidenz-Gap dokumentiert bleibt.

2. USDT 2022:
   - FIFO-Lotbildung fuer die drei Tail-Splits pruefen.
   - Fokus auf Opening-/Pionex-/Binance-USDT-Bestand vor `2022-01-05`.

3. JUP 2024:
   - Kein DCA- oder Airdrop-Fix automatisch setzen.
   - Source-Events mit Tail-Splits pruefen, warum die vorhandenen JUP-Lots vor den letzten Restmengen erschoepft sind.

4. Low-Value:
   - Dust/Rundung getrennt dokumentieren.
   - IOT/CBDC/25HAYB als echte Review-Gaps weiterfuehren.

## Fazit

Die lokale KI war hilfreich fuer Priorisierung und SQL-Spuren, hat aber bei HNT 2022 eine falsche Schlussfolgerung gezogen, weil sie eine nicht massgebliche Tabelle (`product_position_events`) als Beleg fuer "fehlt" genutzt hat. Die validierte Linie bleibt:

- Keine Cost Basis erfinden.
- Transferketten als belegt dokumentieren, wo `transfer_matches` vorhanden sind.
- Zero-Cost-Tail-Splits gezielt in FIFO/Opening-Bestandslogik pruefen.
