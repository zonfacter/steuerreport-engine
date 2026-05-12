# AI Longrun Blocker Review 2026-05-08

- Started: `2026-05-08T21:52:19.229318+00:00`
- Endpoint: `http://192.168.2.203:11435`
- Model: `qwen3.6-35b-a3b-iq4xs`
- Dry run: `False`
- Status: `var/ai_longrun_blocker_review_status.json`
- JSONL: `var/ai_longrun_blocker_review_results.jsonl`

## Safety Boundary

- Read-only only.
- Keine RAW-Daten, Overrides oder Kandidaten veraendern.
- Keine Referenzdaten automatisch als Primary umdeuten.

## Task Queue

1. `bitget_2025_unavailable_source_dossier` - Bitget 2025 unavailable-source dossier
2. `bitget_2025_symbol_month_risk` - Bitget 2025 symbol/month risk map
3. `pionex_opening_reconstruction_argument` - Pionex opening reconstruction argument
4. `jupiter_remaining_years_plan` - Jupiter remaining years control plan
5. `dust_vtho_busd_decision_basis` - Dust VTHO/BUSD decision basis
6. `final_readiness_traffic_light` - Final readiness traffic light

## Bitget 2025 unavailable-source dossier

- Task: `bitget_2025_unavailable_source_dossier`
- Status: `success`
- Duration seconds: `53.013`
- Traffic light: `red`

### Summary

Das Dossier zu Bitget 2025 identifiziert eine signifikante Datenlücke bei historischen Bot- und Derivate-Transaktionen. Von 1986 effektiven Events sind 940 (ca. 47%) aktive Blockpit-Referenzen ohne Primary-Tx-ID-Match, konzentriert auf Mai-Juni 2025. Die API liefert keine alten Bot-Details mehr. Eine automatische Umdeutung von Blockpit zu Primary ist ausgeschlossen. Es bedarf einer dokumentierten 'unavailable_source'-Entscheidung oder eines Support-Exports.

### Confirmed Facts

- Bitget 2025 weist 1986 effektive Events auf, davon 1046 Primary und 940 aktive Blockpit-Referenzen (Quelle: docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md).
- Keine der 940 aktiven Blockpit-Referenzen hat einen Primary-Tx-ID-Match gegen Bitget-Primärdaten (Quelle: docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md).
- Die Blockpit-Referenzen sind dominiert von Derivate-Gebühren (607), Verlusten (156) und Gewinnen (122), sowie Trades (19) (Quelle: docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md).
- Die Primärdaten decken vorwiegend den Zeitraum Januar-Februar 2025 ab; Mai und Juni 2025 sind stark referenzdominiert (Quelle: docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md).
- Bitget-API liefert für alte Daten (2025/alte) Fehler '43111 param error time range illegal' (Quelle: docs/99_CHAT_HANDOFF_AKTUELL.md).
- Externe Evidenz (Solana RPC) bestätigt nur Withdrawals, nicht aber Bot-Fills (Quelle: docs/57_BITGET_EXTERNAL_EVIDENCE_AUDIT_2026-05-08.md).
- Der Status Bitget 2025 ist 'support_required, unavailable_source_possible' (Quelle: docs/79_TAX_REPORT_READINESS_STATUS_2026-05-08.md).

### Open Risks

- Fehlende Primary-Daten für ca. 940 Transaktionen (v.a. Mai/Juni 2025) führen zu unklarer steuerlicher Einordnung (Realisierte PnL vs. Gebühren vs. Nicht-Steuerbare).
- Risiko der Doppelbesteuerung oder Nicht-Besteuerung, falls Blockpit-Referenzen nicht korrekt als Referenz markiert oder durch fehlende Primärdaten ersetzt werden.
- Blockpit-Referenzen dürfen nicht automatisch als Primary umgedeutet werden, da keine Tx-ID-Übereinstimmung vorliegt (Quelle: docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md).
- Unklarer Status der 'unavailable_source'-Entscheidung: Es fehlt eine finale, dokumentierte Freigabe, dass Bitget-Daten nicht beschaffbar sind und eine Rekonstruktion nur auf Basis von Salden/Transfers erfolgt.

### Recommended Next Steps

- Supportanfrage an Bitget: Explizite Anforderung eines historischen Account/Bot/Trade Exports für den Zeitraum 2025-01-01 bis 2025-12-31, insbesondere für Mai und Juni 2025.
- Dokumentation der 'unavailable_source'-Entscheidung: Falls Bitget keine Daten liefert, muss eine formale, dokumentierte Entscheidung getroffen werden, dass die Blockpit-Referenzen als 'reference_only' behandelt werden und keine steuerlichen Buchungen auf Basis dieser Referenzen vorgenommen werden, sondern nur auf Basis der vorhandenen Primärdaten und Saldo-Rekonstruktion.
- Prüfung der 19 aktiven 'trade'-Referenzen: Manuelle Plausibilitätsprüfung gegen externe Marktdaten (falls verfügbar) oder Abgleich mit PnL-Statements, falls diese vorliegen.
- Keine automatischen Overrides: Keine Änderung des Status von Blockpit-Referenzen zu Primary ohne neue Evidenz.

### Must Not Do

- Keine Blockpit-Referenzen als Primary umdeuten (tax_effective=true setzen).
- Keine automatischen Buchungen für die 940 nicht gematchten Referenzzeilen vornehmen.
- Keine RAW-Daten löschen oder überschreiben.
- Keine neuen Kandidaten mit tax_effective=true setzen.

## Bitget 2025 symbol/month risk map

- Task: `bitget_2025_symbol_month_risk`
- Status: `success`
- Duration seconds: `67.137`
- Traffic light: `yellow`

### Summary

Analyse der offenen Bitget-Referenzen (Blockpit) fuer 2025. Es verbleiben 940 aktive Referenzzeilen ohne Primary-Tx-ID-Match, konzentriert auf Mai und Juni 2025. Die Datenqualität ist als 'Referenz' eingestuft; eine automatische Umdeutung zu Primary ist verboten. Der Status bleibt 'support_required'.

### Confirmed Facts

- Bitget 2025 hat 1986 effektive Events, davon 1046 Primary und 940 aktive Blockpit-Referenzen (Quelle: docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md).
- Keine der 940 aktiven Blockpit-Referenzen hat einen Tx-ID-Match mit Bitget-Primary-Daten (Quelle: docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md).
- Die Mehrheit der Referenzen entfaellt auf Derivate (Fees, PnL, Liquidationen) in den Monaten Mai (453) und Juni (408) (Quelle: docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md).
- Die Assets der Referenzen sind vorwiegend SOL (736), USDT (134), XRP (32) und JUP (32) (Quelle: docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md).
- Der Status fuer Bitget 2025 ist 'support_required' und 'unavailable_source_possible' (Quelle: docs/79_TAX_REPORT_READINESS_STATUS_2026-05-08.md).
- RAW-Daten wurden nicht geloescht; nur steuerliche Overrides verhindern Doppelzaehlungen (Quelle: docs/99_CHAT_HANDOFF_AKTUELL.md).

### Open Risks

- Fehlender Primarnachweis fuer 940 Transaktionen/Events in Bitget 2025, was die steuerliche Einordnung von Fees und PnL unsicher macht.
- Risiko der Doppelzaehlung, falls Blockpit-Referenzen fälschlicherweise als Primary gebucht werden.
- Abhaengigkeit von Bitget-Supportexporten oder einer dokumentierten 'unavailable_source'-Entscheidung zur Schliessung der Luecke.
- Keine automatische Buchung von PnL oder Fees aus den Referenzdaten ohne explizite Freigabe.

### Recommended Next Steps

- Bitget-Support kontaktieren und explizit nach historischen Bot-/Derivate-Exports fuer Mai/Juni 2025 fragen.
- Pruefen, ob die 940 Referenzzeilen manuell gegen externe Marktdaten (Candles) plausibilisiert werden koennen, um die Existenz der Trades zu bestaetigen (ohne sie als Primary zu buchen).
- Dokumentation der 'unavailable_source'-Entscheidung vorbereiten, falls kein Supportexport erfolgt.
- Keine automatischen Overrides fuer diese 940 Zeilen setzen; Status auf 'reference' belassen.

### Must Not Do

- Keine Blockpit-Referenzzeilen als Primary umdeuten (tax_effective=true setzen).
- Keine RAW-Daten aendern oder loeschen.
- Keine automatischen Buchungen fuer die offenen Referenzzeilen vornehmen.
- Keine Overrides setzen, die die Steuerhoehe aendern, ohne explizite Freigabe.

## Pionex opening reconstruction argument

- Task: `pionex_opening_reconstruction_argument`
- Status: `success`
- Duration seconds: `67.246`
- Traffic light: `yellow`

### Summary

Die Pionex-Opening-Ersatzrekonstruktion ist mathematisch konsistent und schließt die USDT-Unterdeckung, stellt jedoch keinen primären Nachweis (Kontosnapshot) dar. Der Kandidat bleibt als 'needs_evidence' markiert und nicht steuerwirksam.

### Confirmed Facts

- Erforderliches Opening zur Vermeidung negativer Bestände: 1643.40556756620000000000 USDT (Quelle: docs/84_PIONEX_OPENING_RECONSTRUCTION_AUDIT_2026-05-08.md)
- Schlimmster negativer Bestand vor Korrektur: -1643.40556756620000000000 USDT am 2022-01-19 (Quelle: docs/84_PIONEX_OPENING_RECONSTRUCTION_AUDIT_2026-05-08.md)
- Intern konsistenter Exportstrom, aber kein primärer Konto-Snapshot vor den ersten Bot-Trades (Quelle: docs/84_PIONEX_OPENING_RECONSTRUCTION_AUDIT_2026-05-08.md)
- Aktuelle API-Balances passen eng zum CSV-Modell (Differenz USDT: ~0.004 USDT) (Quelle: docs/99_CHAT_HANDOFF_AKTUELL.md)
- Virtuelle Simulation zeigt: Mit Kandidat gibt es keinen globalen USDT-Negativbestand mehr (Quelle: docs/99_CHAT_HANDOFF_AKTUELL.md)
- Kandidat-Status: tax_effective=false, needs_evidence (Quelle: docs/99_CHAT_HANDOFF_AKTUELL.md, docs/79_TAX_REPORT_READINESS_STATUS_2026-05-08.md)

### Open Risks

- Fehlender primärer Nachweis (Kontosnapshot/Statement) des Startkapitals vor 2021-12-25
- Abhängigkeit von der fachlichen Entscheidung des Steuerpflichtigen zur Akzeptanz der Ersatzrekonstruktion
- Restrisiko bei Dust-Residuals (VTHO, BUSD), die mit dem Opening-Problem korrelieren

### Recommended Next Steps

- Prüfung, ob ältere Pionex-Statements oder E-Mails mit Bestätigungen des Bot-Starts beschaffbar sind
- Fachliche Entscheidung des Steuerpflichtigen: Akzeptanz der rekonstruierten Opening-Balance als plausibel oder Ablehnung
- Bei Akzeptanz: Dokumentation der Entscheidung als 'documented replacement reconstruction' für die Steuererklärung
- Auflösung der Dust-Residuals (VTHO/BUSD) parallel zur Finalisierung des Opening-Themas

### Must Not Do

- Den Kandidaten nicht als tax_effective=true aktivieren
- Keine RAW-Daten ändern oder überschreiben
- Keine automatische Buchung ohne explizite Freigabe

## Jupiter remaining years control plan

- Task: `jupiter_remaining_years_plan`
- Status: `success`
- Duration seconds: `78.805`
- Traffic light: `yellow`

### Summary

Basierend auf dem abgeschlossenen Status von Jupiter 2025 (solscan-verifiziert, keine fehlenden On-Chain-Events) wird ein strikt read-only Pruefplan fuer die verbleibenden Jupiter-Jahre 2023, 2024 und 2026 abgeleitet. Diese Jahre stehen unter dem Status 'partial, manual_review' und weisen signifikante Diskrepanzen zwischen RPC-Daten, Perps-Daten und potenziellen Solscan-Luecken auf. Der Fokus liegt auf der Plausibilitaetspruefung von Perps-Transaktionen und der Identifikation von 'True-Missing'-Transaktionen, ohne Daten zu aendern.

### Confirmed Facts

- Jupiter 2025 ist als 'covered_by_solscan_true_missing_audit' markiert; kein weiterer Import noetig (Quelle: docs/80_JUPITER_2025_SOLSCAN_COVERAGE_AUDIT_2026-05-08.md).
- Jupiter 2023 hat 24 Events (solana_rpc), Zeitraum 2023-04-26 bis 2023-11-11 (Quelle: docs/54_CEX_COMPLIANCE_COVERAGE_2026-05-08.md).
- Jupiter 2024 hat 352 Events (284 solana_rpc, 68 jupiter_perps), Zeitraum 2024-02-15 bis 2024-12-20 (Quelle: docs/54_CEX_COMPLIANCE_COVERAGE_2026-05-08.md).
- Jupiter 2026 hat 2 Events (solana_rpc), Zeitraum 2026-01-02 (Quelle: docs/54_CEX_COMPLIANCE_COVERAGE_2026-05-08.md).
- Der FIFO-Kern verarbeitet bekannte Solana-Mints kanonisch; Rohdaten bleiben unveraendert (Quelle: docs/99_CHAT_HANDOFF_AKTUELL.md).

### Open Risks

- Jupiter 2023: Geringe Eventzahl (24); Risiko, dass manuelle Swaps oder Perps-Transaktionen fehlen, die nicht im RPC-Standard-Feed erscheinen.
- Jupiter 2024: Hohe Eventzahl (352) mit signifikanter Perps-Komponente (68 Events). Risiko von Doppelzaehlungen oder Fehlklassifizierung von Perps-Settlements als Spot-Transfers.
- Jupiter 2026: Sehr geringe Eventzahl; Risiko, dass Anfangsjahresaktivitaeten unvollstaendig erfasst sind.
- Fehlende Solscan-Abdeckung fuer 2023/2024/2026 im Vergleich zu 2025; keine automatische 'True-Missing'-Bestaetigung moeglich.

### Recommended Next Steps

- 1. Jupiter 2023 Solscan-Abgleich: Generiere einen Solscan-Export fuer die Wallet-Adresse im Zeitraum 2023-04-26 bis 2023-11-11. Vergleiche die Transaktions-IDs mit den 24 RPC-Events. Suche nach 'True-Missing'-Transaktionen (DEX Swaps, die nicht im RPC-Feed gelistet sind).
- 2. Jupiter 2024 Perps-Validierung: Extrahiere die 68 Jupiter-Perps-Events. Pruefe, ob diese korrekt als Derivate (PnL, Fees) und nicht als Spot-Bestandsaenderungen klassifiziert sind. Vergleiche die Perps-Transaktions-IDs mit Solscan, um On-Chain-Validitaet zu bestaetigen.
- 3. Jupiter 2024 RPC vs. Solscan Cross-Check: Fuehre einen 'True-Missing'-Audit fuer 2024 durch (aehnlich wie fuer 2025), um zu pruefen, ob alle RPC-basierten Swaps auch on-chain existieren und ob es On-Chain-Transaktionen gibt, die im RPC fehlen.
- 4. Jupiter 2026 Manuelle Pruefung: Da nur 2 Events vorliegen, pruefe manuell die Wallet-Aktivitaet im Januar 2026 gegen Solscan, um sicherzustellen, dass keine weiteren Transaktionen (z.B. Token-Approvals, kleine Swaps) uebersehen wurden.
- 5. Dokumentation: Erstelle fuer jedes Jahr einen kurzen 'Jupiter_Year_XX_Manual_Review.md' Report, der die Ergebnisse der Solscan/Perps-Abgleiche festhaelt. Dies ist die Voraussetzung, um das Jahr aus der Blockerliste zu nehmen.

### Must Not Do

- Keine RAW-Daten aendern oder loeschen.
- Keine neuen Importe ohne explizite Freigabe und Validierung der Duplizitaet.
- Keine automatische Umdeutung von Blockpit-Referenzen zu Primary-Daten fuer Jupiter.
- Keine steuerwirksamen Overrides fuer Perps-Transaktionen ohne manuelle Bestaetigung der PnL-Berechnung.

## Dust VTHO/BUSD decision basis

- Task: `dust_vtho_busd_decision_basis`
- Status: `success`
- Duration seconds: `61.269`
- Traffic light: `yellow`

### Summary

VTHO und BUSD sind als Mini-Residuals (Dust/Altbestandsreste) klassifiziert. VTHO resultiert aus einem isolierten Binance Dust-Convert-Out ohne nachgewiesenen Zufluss. BUSD zeigt einen negativen Endbestand, der durch Pionex-Gebühren und einen nachfolgenden Binance Dust-Convert-Out entsteht; der erste Bruch liegt jedoch im Pionex-Kontext (fehlender Opening-Balance-Nachweis). Beide Kandidaten sind aktuell als `tax_effective=false` gespeichert und blockieren den finalen Report-Status.

### Confirmed Facts

- VTHO-Endbestand: -42.39387934, verursacht durch einen einzigen Binance Dust-Convert-Out am 2023-05-02 (Quelle: docs/83_DUST_RESIDUAL_DETAIL_AUDIT_2026-05-08.md, var/dust_residual_detail_audit_2026-05-08.json).
- BUSD-Endbestand: -0.55168701480000000000, verursacht durch Pionex-Fees/Trades und einen Binance Dust-Convert-Out am 2023-05-02 (Quelle: docs/83_DUST_RESIDUAL_DETAIL_AUDIT_2026-05-08.md).
- Der erste BUSD-Negativbestand entsteht bei Pionex-Gebühren, was auf den fehlenden Pionex-Opening-Balance-Nachweis verweist (Quelle: docs/83_DUST_RESIDUAL_DETAIL_AUDIT_2026-05-08.md, docs/77_DUST_RESIDUAL_REVIEW_CANDIDATES_2026-05-08.md).
- Review-Kandidaten `binance-vtho-dust-residual-2023-05-02` und `mixed-busd-dust-residual-2023-05-02` existieren, sind aber nicht steuerwirksam (tax_effective=false) (Quelle: docs/79_TAX_REPORT_READINESS_STATUS_2026-05-08.md).
- Keine weiteren Zuflüsse für VTHO oder BUSD im aktuellen Datenbestand nachweisbar (Binance Asset-Dividend-Probe negativ) (Quelle: docs/99_CHAT_HANDOFF_AKTUELL.md).

### Open Risks

- Fehlender Nachweis der ursprünglichen Dust-Bestände (Zuflüsse vor 2023) für VTHO und BUSD.
- Fachliche Entscheidung fehlt: Ob die Restbeträge als vernachlässigbar (de minimis) behandelt oder als offene Lücke dokumentiert werden sollen.
- BUSD-Risiko ist eng mit dem Pionex-Opening-Balance-Blocker verknüpft; eine isolierte Lösung für BUSD ist ohne Pionex-Kontext schwierig.
- Report-Status bleibt 'blocked_by_pionex_opening_evidence' und 'Dust-Residuals' (Quelle: docs/79_TAX_REPORT_READINESS_STATUS_2026-05-08.md).

### Recommended Next Steps

- Prüfung, ob VTHO und BUSD-Beträge unter der deutschen steuerlichen Relevanzgrenze liegen oder als 'geringfügig' dokumentiert werden können.
- Entscheidung, ob die Review-Kandidaten manuell auf `tax_effective=true` gesetzt werden dürfen (nur bei expliziter Freigabe, dass keine weiteren Zuflüsse erwartet werden).
- Alternativ: Dokumentation der Restbeträge als 'unresolved dust residuals' im Steuer-Dossier, falls keine weiteren Belege beschafft werden.
- Weiterhin Pionex-Opening-Balance-Nachweis beschaffen, da dies die BUSD-Problematik ursächlich auflösen könnte.

### Must Not Do

- Keine automatische Buchung der Dust-Residuals als steuerwirksam ohne explizite Review-Entscheidung.
- Keine Erfindung von fehlenden Zufluss-Events für VTHO oder BUSD.
- Keine Umdeutung von Blockpit-Referenzen als Primary für diese Assets.
- Keine RAW-Datenänderung.

## Final readiness traffic light

- Task: `final_readiness_traffic_light`
- Status: `success`
- Duration seconds: `94.906`
- Traffic light: `yellow`

### Summary

Der Steuerreport ist technisch als Draft erzeugbar, aber final noch nicht freigegeben. Der Status ist durch fehlende Primärbeweise für Pionex-Startkapital, unklare Bitget-2025-Daten und offene Dust-Residuals blockiert. Alle negativen Bestände wurden durch Ersatzrekonstruktionen und Gap-Imports weitgehend geschlossen, erfordern aber fachliche Entscheidungen.

### Confirmed Facts

- {'point': 'Pionex USDT Opening Balance Rekonstruktion', 'status': 'yellow', 'next_step': 'Fachliche Entscheidung: Ersatzrekonstruktion (1643.40 USDT) akzeptieren oder Primärbeweis beschaffen. Aktuell tax_effective=false.', 'files': ['docs/84_PIONEX_OPENING_RECONSTRUCTION_AUDIT_2026-05-08.md', 'docs/65_PIONEX_USDT_OPENING_BALANCE_REVIEW_2026-05-08.md', 'var/pionex_opening_reconstruction_audit_2026-05-08.json']}
- {'point': 'Bitget 2025 Coverage', 'status': 'red', 'next_step': "Warten auf Support-Export oder dokumentierte Entscheidung 'unavailable_source'. Keine automatische Umdeutung von Blockpit-Referenzen zu Primary.", 'files': ['docs/85_BITGET_2025_REMAINING_REFERENCE_AUDIT_2026-05-08.md', 'docs/56_BITGET_BOT_TRADE_DATENLUECKE_2026-05-08.md', 'var/bitget_2025_remaining_reference_audit_2026-05-08.json']}
- {'point': 'Dust Residuals VTHO/BUSD', 'status': 'yellow', 'next_step': 'Entscheidung treffen: Kleiner Altbestand/Kandidat akzeptieren oder weitere Binance-Nachweise suchen. Aktuell tax_effective=false.', 'files': ['docs/77_DUST_RESIDUAL_REVIEW_CANDIDATES_2026-05-08.md', 'docs/83_DUST_RESIDUAL_DETAIL_AUDIT_2026-05-08.md', 'var/dust_residual_balance_candidates_2026-05-08.json']}
- {'point': 'USDT Global Balance Closure', 'status': 'green', 'next_step': 'Keine weiteren Schritte nötig. Globaler USDT-Bestand ist durch Pionex-Kandidat, Binance-Gap-Imports und Solscan-Counterflows nicht mehr negativ.', 'files': ['docs/66_USDT_GLOBAL_RESIDUAL_AFTER_PIONEX_CANDIDATE_2026-05-08.md', 'docs/67_BINANCE_TRANSACTION_HISTORY_JAN2022_GAP_IMPORT_2026-05-08.md', 'docs/69_BINANCE_TRANSACTION_HISTORY_FEB2022_GAP_IMPORT_2026-05-08.md', 'docs/71_SOLSCAN_BITGET_COUNTERFLOW_DEC2024_IMPORT_2026-05-08.md']}
- {'point': 'Jupiter 2025 Coverage', 'status': 'green', 'next_step': 'Keine weiteren Schritte nötig. Solscan-Coverage bestätigt, keine fehlenden Events.', 'files': ['docs/80_JUPITER_2025_SOLSCAN_COVERAGE_AUDIT_2026-05-08.md', 'var/jupiter_2025_solscan_coverage_audit_2026-05-08.json']}
- {'point': 'Dashboard & UI Fix', 'status': 'green', 'next_step': 'Keine weiteren Schritte nötig. Jahresfilter und Portfolio-History funktionieren korrekt.', 'files': ['docs/99_CHAT_HANDOFF_AKTUELL.md']}

### Open Risks

- Pionex: Fehlender Primärbeweis für Startkapital (Opening Balance). Ohne fachliche Freigabe der Ersatzrekonstruktion bleibt der Report 'blocked'.
- Bitget 2025: Hoher Anteil an Blockpit-Referenzen ohne Primary-Match. Risiko der Doppelzählung oder Fehlklassifizierung, falls Bitget keine Daten liefert.
- Dust Residuals: Negative Bestände bei VTHO und BUSD sind technisch geschlossen, aber steuerlich noch nicht final bewertungsreif.
- Jupiter 2023/2024/2026: Manuelle On-Chain-Prüfung noch offen, aber geringes Risiko aufgrund geringer Eventzahlen.

### Recommended Next Steps

- 1. Pionex Opening Balance: Nutzer konsultieren, ob Ersatzrekonstruktion akzeptiert wird oder Primärbeweis vorliegt. Bei Akzeptanz: Kandidat manuell auf tax_effective=true setzen (nur durch Mensch).
- 2. Bitget 2025: Support-Anfrage verfolgen. Falls keine Daten: Dokumentierte Entscheidung 'unavailable_source' erstellen und Referenzen als Risikoposition kennzeichnen.
- 3. Dust Residuals: Fachliche Entscheidung zu VTHO/BUSD treffen. Bei Akzeptanz als Restwert: Kandidaten auf tax_effective=true setzen.
- 4. Report Finalisierung: Nach oben genannten Entscheidungen den Report als 'final' markieren.

### Must Not Do

- Keine RAW-Daten ändern oder löschen.
- Keine Blockpit-Referenzen automatisch zu Primary umdeuten.
- Keine Balance-Adjustments (z.B. Pionex Opening) automatisch als steuerwirksam (tax_effective=true) aktivieren.
- Keine neuen Importe ohne explizite Freigabe und Duplikatsprüfung.
