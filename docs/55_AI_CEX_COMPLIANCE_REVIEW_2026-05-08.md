# AI CEX Compliance Review - 2026-05-08

- Coverage JSON: `/workspace/steuerreport/var/cex_compliance_coverage_2026-05-08.json`
- AI JSON: `/workspace/steuerreport/var/ai_cex_compliance_review_2026-05-08.json`
- Status: `success`
- Modell: `qwen3.6-35b-a3b-iq4xs`
- Endpoint: `http://192.168.2.203:11435`
- Dauer Sekunden: `43.252`
- Usage: `{"completion_tokens": 1174, "prompt_tokens": 5467, "total_tokens": 6641, "prompt_tokens_details": {"cached_tokens": 0}}`

## Zusammenfassung

Die Coverage zeigt kritische Lücken bei der Pionex-Opening-Balance (2022) und unklarer Bitget-Datenherkunft (2025). Binance ist primärdatentechnisch stabil, aber 2021 ist der kritische Startpunkt. Jupiter-Daten sind lückenhaft und erfordern On-Chain-Validierung. Keine automatischen Buchungen durchführen.

## Priorisierte Luecken

- `1` `pionex` `2022` risk `high`: Fehlende Opening-Balance/Bot-Startkapital-Nachweis für USDT-Unterdeckung Anfang 2022 | evidence: Status 'opening_balance_required'; bekannte USDT-Unterdeckung; 4 Deposits matchen Binance-Withdrawals, aber Startbestand ist nicht belegt.
- `2` `bitget` `2025` risk `high`: Unvollständige Historie durch API-Limits; Derivate-Events müssen separat plausibilisiert werden | evidence: Status 'api_limited', 'support_required'; 940 Referenz-Events von Blockpit (keine Primärdaten); Support-Anfrage ausstehend.
- `3` `binance` `2021` risk `medium`: Startkette für Pionex-Zuflüsse muss final verifiziert werden | evidence: Status 'manual_review'; 1331 Events; kritisch für die Zuordnung von Startbeständen und frühen Transfers.
- `4` `jupiter` `2025` risk `medium`: Geringe Event-Anzahl; Abgleich mit Wallet-Bestand und Perps erforderlich | evidence: Nur 18 Events; Status 'manual_review'; On-Chain-Daten müssen gegen Solscan/Jup-Export geprüft werden.

## Datenanforderungen

- `pionex` `2021-12-31 bis 2022-01-01` `Opening Balance / Bot Startkapital Nachweis`: Um die bekannte USDT-Unterdeckung Anfang 2022 zu erklären und die steuerliche Basis korrekt zu bestimmen.
- `bitget` `2025 (gesamtes Jahr)` `Vollständige Spot/Bot/Grid/Internal-Transfer Historie`: API-Limits haben zu Datenverlust geführt; Support-Antwort ist kritisch für die Vollständigkeitsprüfung.
- `jupiter` `2025` `Solscan Wallet Export & Jupiter Perps Export`: Abgleich der wenigen RPC-Ereignisse mit der tatsächlichen Wallet-Historie und Perps-Positionen.

## Risiko je Steuerjahr

- `2022` risk `high`: Pionex Opening-Balance nicht belegt; Risiko der Fehlbewertung des Startkapitals und damit der steuerlichen Bemessungsgrundlage.
- `2025` risk `high`: Bitget-Daten unvollständig (API-Limits) und stark von Referenzdaten (Blockpit) abhängig; Derivate-Events müssen separat geprüft werden.
- `2021` risk `medium`: Binäre Abhängigkeit für Pionex-Zuflüsse; manuelle Prüfung erforderlich, um Zuordnungen zu validieren.

## Sichere Automatisierung

- Zeitzone-Korrekturen anwenden (bereits 11 Fälle identifiziert).
- Binance-Primärdaten (API/CSV) für 2023-2026 als Grundlage nutzen.
- Jupiter-Swaps gegen Solscan-Transfers abgleichen, um Duplikate oder Auslassungen zu finden.

## Nicht automatisch anwenden

- Keine Pionex-Opening-Balance für 2022 automatisch setzen oder schätzen.
- Keine Bitget-Bot-Trade-Details aus Blockpit als Primärdaten übernehmen, ohne Support-Nachweis.
- Keine manuellen Korrekturen an RAW-Daten vornehmen; nur Overrides dokumentieren.
