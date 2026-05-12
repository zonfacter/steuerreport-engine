# PDF-/Steuerrecht-Readiness 2025/2026

Stand: 2026-05-10

## Gepruefte Quellen

- BMF-Schreiben `06.03.2025`, `IV C 1 - S 2256/00042/064/043`: `https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Steuerarten/Einkommensteuer/2025-03-06-einzelfragen-kryptowerte-bmf-schreiben.html`
- EU-Kommission DAC8: `https://taxation-customs.ec.europa.eu/taxation/tax-transparency-cooperation/administrative-co-operation-and-mutual-assistance/directive-administrative-cooperation-dac/dac8_en`
- EUR-Lex Richtlinie `(EU) 2023/2226`: `https://eur-lex.europa.eu/eli/dir/2023/2226/oj/eng`
- Lokale Regelableitung: `docs/19_BMF_2025_STEUERREGELN_UND_PFLICHTEN.md`
- Lokaler DAC8/CARF-Kontext: `docs/20_DAC8_CARF_REGELWERK.md`

## Live-Stand

| Jahr | Job | Tax Lines | Derivate | PDF-Dateien | Review-Gate | Hinweise |
|---:|---|---:|---:|---:|---|---|
| 2025 | `0f671359-c095-4ba2-b664-353875ff09af` | 474 | 0 | 1 | `allow_export=true` | 22 offene Bewertungs-/Plausibilitaets-Hinweise im Summenlauf, keine Gate-Blocker |
| 2026 | `816353c8-edee-428e-ad92-a571dfb1f356` | 1 | 0 | 1 | `allow_export=true` | 1 offenes Bewertungs-/Plausibilitaets-Hinweis im Summenlauf, keine Gate-Blocker |

Aktuelle Exportdateien:

- `var/report_exports_current_2026-05-10/2025_8c0b81a8-7c60-4df8-9090-8dfeeecf86c4/`
- `var/report_exports_current_2026-05-10/2026_81949598-7ec7-4a9d-8f9d-77f40f6bf07e/`
- PDF-Live-Test:
  - `var/pdf_audit_2026-05-10/steuerreport_2025_all_part1_after_restart.pdf`: 19 Seiten
  - `var/pdf_audit_2026-05-10/steuerreport_2026_all_part1_after_restart.pdf`: 2 Seiten

## Umgesetzte PDF-Korrektur

Code: `src/tax_engine/api/reporting.py`

- PDF nutzt jetzt Querformat statt enger A4-Hochformat-Tabelle.
- Jede PDF-Datei enthaelt eine Deck-/Summenseite mit:
  - Steuerjahr, Job-ID, Scope, Ruleset, FIFO/EUR-Hinweis,
  - §22-Leistungen/Rewards,
  - §23 private Veraeusserungen,
  - Termingeschaefte,
  - EÜR-/Gewerbe-Summen,
  - Integritaets-ID, Config-Hash, Data-Hash,
  - fuer 2026 einen DAC8/CARF/KStTG-Hinweis als Melde-/Plausibilitaetskontext.
- Detailtabellen sind breiter und gerundete EUR-Werte sind lesbarer.
- Harte PDF-Grenze bleibt erhalten: maximal `100` Seiten je Datei. Wegen der neuen Summenseite werden pro Datei nur noch `99 * 28` Detailzeilen geplant.

## Steuerrechtliche Plausibilitaet

Aktuell fachlich abgedeckt:

- Deutsche Jahres-Rulesets `DE-2025-v1.0` und `DE-2026-v1.0`.
- §23-FIFO mit 12-Monats-Haltefrist.
- §23-Freigrenze ab 2024 mit `1000.00 EUR`.
- §22 Nr. 3 Leistungen/Rewards getrennt von privaten Veraeusserungen mit `256.00 EUR` Freigrenze als eigener Parameter.
- Mining/Staking/Reward-Zufluesse erzeugen FIFO-Lots mit Zuflusswert.
- Derivate/Termingeschaefte laufen in separaten Zeilen/Summen und werden nicht in §23-Spot vermischt.
- Mining-/Reward-nahe Zufluesse werden als gewerblicher Vorgang in `EÜR/Gewerbe` gefuehrt; `anlage_so.leistungen_income_eur` ist fuer 2025/2026 nach Neuberechnung `0`.
- Interne Transfers sollen keine Veraeusserung ausloesen und werden ueber Transferketten/Review-Kontext plausibilisiert.
- DAC8/CARF wird fuer 2026 als Transparenz-/Meldekontext behandelt, nicht als materielles Steuerrecht.

Nicht als garantiert fertig bewerten:

- Die PDF ist jetzt lesbarer, aber nicht der alleinige Vollnachweis. Vollstaendige Event-IDs, lange Dezimalwerte, Rohdatenbezug und Hashes bleiben primaer in JSON/CSV.
- Der Report ersetzt keine Steuerberater-/Finanzamtspruefung. Er ist eine technische Berechnung nach aktuellem Ruleset.
- 2025 enthaelt weiterhin `22` unresolved valuation events im Summenlauf; 2026 enthaelt `1`. Diese blockieren das Gate aktuell nicht, sollten aber vor einer finalen Abgabe als Liste sichtbar gemacht werden.
- 2025/2026 sollten noch gegen Jahresendbestand, bekannte CEX-Reports und DAC8/CARF-nahe Providerdaten abgeglichen werden, sobald diese verfuegbar sind.

## Aktuelle Bewertung 2025/2026

- `2025`: technisch exportfaehig, aber vor Abgabe noch fachliche Detailpruefung empfohlen. Schwerpunkt: die `22` Bewertungs-Hinweise, Binance/Jup/Bitget-Abgleich, Jahresendbestand.
- `2026`: technisch exportfaehig; steuerlich ist das Jahr noch laufend. DAC8/CARF ist fuer die spaetere Kontrolllogik relevant, die erste externe Meldedatenlage fuer Reportingjahr 2026 kommt erst 2027.

## Naechste sinnvolle Arbeiten

1. Endpoint/Report fuer `unresolved_valuation_events` pro Jahr mit betroffenen Events, Quelle und Asset bauen.
2. PDF um Anhang "Offene Hinweise und Review-Entscheidungen" erweitern, damit Medium-/Low-Issues nicht nur im Dashboard stehen.
3. Jahresendbestand-Report je Plattform/Wallet fuer 2025 und 2026 ergaenzen.
4. WISO-CSV separat gegen echte WISO-Importlogik testen; aktueller Export ist strukturiert, aber nicht als amtlich zertifizierter WISO-Import garantiert.
5. DAC8/CARF-Referenzimport vorbereiten, sobald Providerdaten/Schema praktisch verfuegbar sind; nicht mit Rohdaten ueberschreiben.

## Validierung

- `python3 -m py_compile src/tax_engine/api/reporting.py src/tax_engine/api/processing.py`
- `PYTHONPATH=src python3 -m pytest -q tests/unit/api/test_api_coverage_gate.py::test_report_export_integrity_snapshot_and_compliance_paths tests/unit/api/test_api_coverage_gate.py::test_report_helpers_and_review_gate_empty_completed_job_paths tests/unit/api/test_process_endpoints.py`
- Ergebnis: `34 passed`, `1` Importlib-Deprecation-Warnung.
- Port `8000` neu gestartet und `/api/v1/health` erfolgreich geprueft.
