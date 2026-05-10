# DAC8/CARF-Regelwerk fuer Steuerreport-Kontext

Stand: 2026-05-04

Dieses Dokument ist die verifizierte Kontextbasis fuer DAC8/CARF in der Steuerreport-Engine. Es ersetzt kein Steuer- oder Rechtsgutachten, sondern definiert, welche Fakten die KI-/Review-Schicht als gesichert verwenden darf und welche Punkte als unsicher/landesspezifisch markiert werden muessen.

## 1. Primaerquellen

- EU-Kommission DAC8: `https://taxation-customs.ec.europa.eu/taxation/tax-transparency-cooperation/administrative-co-operation-and-mutual-assistance/directive-administrative-cooperation-dac/dac8_en`
- EUR-Lex Richtlinie (EU) 2023/2226: `https://eur-lex.europa.eu/eli/dir/2023/2226/oj/eng`
- OECD CARF Einfuehrung/Regeln: `https://www.oecd.org/en/publications/international-standards-for-automatic-exchange-of-information-in-tax-matters_896d79d1-en/full-report/component-5.html`
- OECD CARF FAQ: `https://www.oecd.org/content/dam/oecd/en/topics/policy-issues/tax-transparency-and-international-co-operation/faqs-crypto-asset-reporting-framework.pdf`
- BMF DAC8-Umsetzungsgesetz: `https://www.bundesfinanzministerium.de/Content/DE/Gesetzestexte/Gesetze_Gesetzesvorhaben/Abteilungen/Abteilung_IV/21_Legislaturperiode/2025-11-05-DAC8-G/0-Gesetz.html`
- KStTG konsolidierter Gesetzestext: `https://www.buzer.de/KStTG.htm` (BGBl. 2025 I Nr. 352; fuer Projektzwecke als konsolidierte Gesetzestext-Referenz genutzt)
- EU Implementing Regulation (EU) 2025/2263 fuer Formate: `https://eur-lex.europa.eu/eli/reg_impl/2025/2263/oj/eng`

Sekundaerquellen duerfen nur als Hinweis auf nationale Umsetzung/Fristen genutzt werden, nicht als alleinige Regelquelle.

## 2. Gesicherte Kernaussagen

### 2.1 DAC8

- DAC8 ist die achte Aenderung der EU-Richtlinie zur administrativen Zusammenarbeit im Bereich der direkten Steuern.
- DAC8 erweitert den automatischen Informationsaustausch auf Kryptowerte.
- EU-Mitgliedstaaten mussten DAC8 bis 31.12.2025 umsetzen.
- Anwendung ab 01.01.2026.
- Erstes Reportingjahr ist 2026.
- Reporting Crypto-Asset Service Provider erfassen ab 01.01.2026 meldepflichtige Nutzer- und Transaktionsdaten.
- Die Meldung an nationale Steuerbehoerden erfolgt im Kalenderjahr nach dem Reportingjahr.
- Der Austausch der Informationen fuer das erste Reportingjahr 2026 erfolgt 2027; EU-seitig ist die Frist innerhalb von neun Monaten nach Ende des Reportingjahres, also bis 30.09.2027.
- Nationale Umsetzungsfristen, technische Formate und Portale koennen davon abhaengige zusaetzliche Details enthalten.
- Deutschland hat DAC8 mit dem DAC8-Umsetzungsgesetz/Kryptowerte-Steuertransparenz-Gesetz (KStTG) umgesetzt; das BMF beschreibt dies als verfahrensrechtliche 1:1-Umsetzung der europaeischen Vorgaben ohne neue Besteuerungstatbestaende.

### 2.2 CARF

- CARF ist das OECD Crypto-Asset Reporting Framework.
- CARF ist ein internationaler Standard fuer Erhebung und automatischen Austausch von Informationen zu relevanten Krypto-Transaktionen.
- DAC8 basiert fuer Krypto-Reporting-Regeln auf CARF.
- CARF definiert:
  - meldepflichtige Kryptowerte,
  - meldepflichtige Dienstleister,
  - meldepflichtige Nutzer,
  - meldepflichtige Transaktionen,
  - Due-Diligence-Verfahren zur Identifikation und steuerlichen Ansässigkeit.
- CARF ist nicht identisch mit CRS. Es ist ein separater Krypto-Standard, der den CRS ergaenzt.

### 2.3 Deutschland/KStTG

- Das DAC8-Umsetzungsgesetz wurde am 22.12.2025 ausgefertigt und am 23.12.2025 im Bundesgesetzblatt bekannt gemacht (BGBl. 2025 I Nr. 352).
- Das KStTG gilt laut konsolidiertem Gesetzestext ab 24.12.2025; die DAC8-/Reporting-Pflichten sind fuer die fachliche Engine trotzdem zeitlich am Anwendungsbeginn 01.01.2026 und am Reportingjahr 2026 auszurichten.
- Anbieter im KStTG-Scope koennen Kryptowerte-Dienstleister oder Kryptowerte-Betreiber sein.
- Das BZSt ist zentrale Stelle fuer Registrierung/Meldung/Austausch, soweit das KStTG die Zustaendigkeit zuweist.
- Due-Diligence-Massnahmen fuer neue meldepflichtige Transaktionen sind vor Durchfuehrung abzuschliessen.
- Fuer bis 31.12.2025 bestehende Nutzerbeziehungen laeuft die Due-Diligence-Frist bis 01.01.2027.
- Das KStTG erweitert nach BMF-Darstellung keine materiellen Besteuerungstatbestaende. Fuer die Engine folgt daraus: KStTG/DAC8/CARF ist Kontroll-/Meldekontext, nicht Gewinnermittlungsrecht.

## 3. Meldepflichtige Akteure

Als Reporting Crypto-Asset Service Provider beziehungsweise Reporting Crypto-Asset Service Provider/Operator kommen insbesondere Dienstleister in Betracht, die fuer oder im Auftrag von Nutzern relevante Krypto-Services ausfuehren.

Fuer die Steuerreport-Engine gilt:

- Nutzer/Privatanleger sind nicht selbst automatisch DAC8/CARF-Reporting-Provider.
- Boersen, Broker, Custodians und vergleichbare Crypto-Asset Service Provider koennen Meldepflichtige sein.
- On-Chain-Self-Custody ohne meldepflichtigen Dienstleister erzeugt nicht automatisch einen DAC8/CARF-Datensatz.
- DeFi-Protokolle koennen nur dann DAC8/CARF-relevant werden, wenn ein meldepflichtiger Dienstleister oder Operator mit entsprechendem Nexus/Service involviert ist.

## 4. Meldepflichtige Assets

DAC8/CARF umfasst breit verstandene Kryptowerte.

Fuer die Steuerreport-Engine als Kontextregel:

- Kryptowaehrungen und Token koennen meldepflichtig sein.
- Stablecoins und E-Geld-/E-Money-nahe Token koennen in DAC8/CARF-Kontext relevant sein; konkrete Ausnahmen sind regelgebunden zu pruefen.
- Zentralbankdigitalwaehrungen und bestimmte nicht fuer Zahlung/Investment nutzbare Assets koennen ausgenommen sein.
- NFTs sind nicht pauschal ausgeschlossen; die Einordnung haengt von Nutzbarkeit, Ausgestaltung und den DAC8/CARF-Definitionen ab.

KI-Regel: Keine pauschale Aussage wie "NFTs sind nie meldepflichtig" oder "alle Token sind immer meldepflichtig".

## 5. Meldepflichtige Transaktionen

CARF/EU-DAC8-Kontext nennt insbesondere:

- Tausch Krypto gegen Fiat.
- Tausch Krypto gegen Krypto.
- Transfers von meldepflichtigen Kryptowerten.
- Je nach Kenntnis/Einordnung Kategorien wie Airdrops, Staking-Ertraege, Lending und weitere Transferarten.
- Retail-Payment-Transaktionen koennen unter CARF bei bestimmten Schwellen/Agenten-Konstellationen relevant sein.

Fuer den Steuerreport ist wichtig:

- DAC8/CARF-Meldungen sind Transparenz-/Informationsmeldungen, keine fertige deutsche Steuerberechnung.
- Reported Gross Proceeds, Acquisition Amounts oder aggregierte Transaktionswerte ersetzen nicht FIFO, Haltefrist, Anschaffungskosten, Gebuehrenbehandlung oder deutsche Einkunftsart.
- DAC8/CARF kann als Abgleichs-/Plausibilitaetsquelle genutzt werden, nicht als alleinige Wahrheit.

## 6. Dateninhalte fuer Abgleich

Typisch erwartbare Melde-/Abgleichsdaten:

- Nutzeridentifikation und steuerliche Ansässigkeit.
- Steueridentifikationsnummern, soweit erhoben/erforderlich.
- Transaktionsarten.
- Asset-Bezeichnungen/Codes.
- Aggregierte Werte/Mengen je Asset und Richtung.
- Fiat-Werte oder Bruttoerloese bei Fiat/Krypto-Transaktionen.
- Krypto/Krypto-Tauschwerte und Transferkategorien, soweit bekannt.
- Provider-/Jurisdiktionsinformationen.

Steuerreport-Regel:

- DAC8/CARF-Daten sollen als separate Referenzquelle importiert werden.
- Keine Rohdaten aus Wallet/Exchange durch DAC8/CARF-Referenzdaten ueberschreiben.
- Konflikte als `integration_conflict`, `external_reporting_mismatch` oder eigene Review-Issues darstellen.

## 7. Zeitliche Regeln

| Datum/Zeitraum | Bedeutung |
| --- | --- |
| Bis 31.12.2025 | EU-Mitgliedstaaten muessen DAC8 national umsetzen. |
| 23.12.2025 | Bekanntmachung des deutschen DAC8-Umsetzungsgesetzes im BGBl. 2025 I Nr. 352. |
| Ab 24.12.2025 | KStTG gilt laut konsolidiertem Gesetzestext; fachlicher Reporting-Start bleibt 01.01.2026. |
| Ab 01.01.2026 | DAC8-Anwendung; Provider erfassen meldepflichtige Daten fuer Reportingjahr 2026. |
| 2026 | Erstes Reportingjahr. |
| Bis 01.01.2027 | Deutsche KStTG-Frist fuer Due Diligence bei bis 31.12.2025 bestehenden Nutzerbeziehungen. |
| 2027 | Erste Meldungen/Informationsaustausch fuer Reportingjahr 2026. |
| Bis 30.09.2027 | EU-seitige Maximalfrist fuer Austausch innerhalb von neun Monaten nach Ende des Reportingjahres. |

KI-Regel:

- Korrekt ist: "Datensammlung ab 01.01.2026; erste Meldung/Austausch 2027".
- Wenn ein konkretes Datum genannt wird, muss es als EU-Austauschfrist `30.09.2027` oder als nationale Frist mit Quelle gekennzeichnet werden.
- Falsch/zu ungenau ist: "Boersen melden ab 01.01.2026 direkt ans Finanzamt" ohne Unterscheidung zwischen Datenerhebung und Meldung.

## 8. Konsequenzen fuer die Steuerreport-Engine

### 8.1 Neue Review-Kategorien

Empfohlene Issue-Typen:

- `external_reporting_mismatch`: DAC8/CARF-Referenzdaten widersprechen internen Events.
- `reported_not_imported`: Externe DAC8/CARF-Position ohne passende Rohtransaktion.
- `imported_not_reported`: Interne Position ohne erwartete DAC8/CARF-Referenz bei meldepflichtiger Quelle.
- `provider_scope_unclear`: Quelle koennte meldepflichtig sein, Scope/Nexus unklar.
- `reporting_year_boundary`: Stichtags-/Jahresgrenzen zwischen Steuerjahr und Reportingjahr unklar.

### 8.2 Neue Kontextfelder

Empfohlene Felder fuer `issue-context` und KI-Prompt:

- `regulatory_context.dac8_applicable_from = "2026-01-01"`
- `regulatory_context.de_ksttg_effective_from = "2025-12-24"`
- `regulatory_context.first_reporting_year = 2026`
- `regulatory_context.pre_existing_user_due_diligence_deadline_de = "2027-01-01"`
- `regulatory_context.first_exchange_deadline_eu = "2027-09-30"`
- `regulatory_context.framework = ["DAC8", "OECD-CARF", "KStTG"]`
- `regulatory_context.reporting_data_is_reference_only = true`
- `regulatory_context.no_tax_result_without_ruleset = true`

### 8.3 KI-/ML-Regeln

Die KI darf:

- DAC8/CARF als Anlass fuer Abgleich/Plausibilitaet nennen.
- Fehlende oder widerspruechliche Daten priorisieren.
- Review-Kommentare vorschlagen.
- Sichere API-Aktionen empfehlen: Status, Kommentar, Such-/Kontextabfragen.

Die KI darf nicht:

- Aus DAC8/CARF-Meldedaten automatisch steuerpflichtige Gewinne berechnen.
- Ohne bestaetigte Rohdaten Anschaffungskosten, Veräußerungserloese oder Haltefristen ersetzen.
- Reportingpflicht eines konkreten Providers ohne Quelle final behaupten.
- Nationale Fristen behaupten, wenn nur EU- oder OECD-Standard bekannt ist.

## 9. Prompt-Baustein fuer AI-Review

```text
Regulatorischer Kontext:
- DAC8 gilt in der EU ab 01.01.2026 und erweitert den automatischen Informationsaustausch auf Kryptowerte.
- Erstes Reportingjahr ist 2026.
- Reporting Crypto-Asset Service Provider sammeln ab 01.01.2026 meldepflichtige Daten.
- Erste Meldungen/Informationsaustausch fuer Reportingjahr 2026 erfolgen 2027; EU-seitig innerhalb von neun Monaten nach Jahresende, also bis 30.09.2027.
- DAC8 basiert auf dem OECD Crypto-Asset Reporting Framework (CARF).
- Deutschland hat DAC8 mit dem KStTG umgesetzt; das ist Kontroll-/Melderecht und fuehrt nach BMF-Darstellung keine neuen materiellen Besteuerungstatbestaende ein.
- Fuer bis 31.12.2025 bestehende Nutzerbeziehungen laeuft die deutsche KStTG-Due-Diligence-Frist bis 01.01.2027.
- CARF umfasst insbesondere Krypto/Fiat-Tausch, Krypto/Krypto-Tausch und Transfers relevanter Kryptowerte.
- DAC8/CARF-Daten sind Referenz-/Plausibilitaetsdaten und ersetzen keine deutsche Steuerberechnung, keine FIFO-Ermittlung und keine Haltefristpruefung.
```

## 10. Offene Punkte fuer spaetere Implementierung

- BZSt-Portale, Meldehandbuecher und technische Datensaetze als Primaerquelle ergaenzen, sobald veroeffentlicht/verifiziert.
- XML-/DIP-Schema fuer importierbare DAC8/CARF-Referenzdaten analysieren.
- Mapping von DAC8/CARF-Aggregaten auf interne `raw_events` nur als Referenzimport, nicht als steuerliche Primaerquelle.
- Separate Tests, die LLM-Antworten gegen die verifizierten Fristen pruefen und Fehler wie `31.12.2027`, `CARF == CRS` oder automatische Steuerberechnung aus Meldedaten markieren.
