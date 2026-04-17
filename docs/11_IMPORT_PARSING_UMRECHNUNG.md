# Import-Regeln: Dezimaltrennung und Umrechnungsfaktoren

## 1. Ziel
Importe müssen unabhängig vom Quellformat (CSV/XLSX/API) numerisch korrekt und reproduzierbar normalisiert werden.

## 2. Zahlenformate (kritisch)
Unterstützte Muster:
- Dezimalpunkt: `1234.56`
- Dezimalkomma: `1234,56`
- Tausendertrennzeichen: `1,234.56`, `1.234,56`, `1 234,56`
- Klammerwerte als negative Zahlen: `(1,234.50)` => `-1234.50`
- Scientific Notation: `1.23e-8`

Pflichtregeln:
- Parser erkennt Locale-Muster pro Datei/Spalte.
- Vor Speicherung wird auf kanonisches Decimal-Format normalisiert.
- Ambige Werte (z. B. `1,234`) werden als `unresolved_number_format` markiert.
- Erweiterte Parsing-Fälle müssen unterstützt werden: BOM, NBSP, Prozentwerte, optionale Vorzeichen.

## 3. Umrechnungsfaktoren
Beispiele:
- Token-Subunits (`wei`, `lamports`, satoshis) zu Standard-Units.
- Redenominations-/Migrationsfaktoren (falls Asset-Projekt Umstellung hatte).
- Gebühreneinheiten, die von Handelsmenge abweichen.

Pflichtregeln:
- Faktorquelle versionieren (`conversion_profile_version`).
- Pro Event speichern: `raw_value`, `factor`, `normalized_value`, `factor_source`.
- Keine stillen Default-Faktoren ohne Audit-Eintrag.
- Präzision wird feld-/asset-spezifisch über Profile gesteuert (kein globales Hardcoding).

## 4. Datums- und Zeitzonenbezug
- Parsing von `UTC`, `CET`, `CEST` und ISO-8601.
- Speicherung intern in UTC.
- Originalzeit und Originalzeitzone für Audit erhalten.
- Parsing-Fallback (verbindlich):
  1. ISO-8601
  2. Lokales Format aus Konfiguration
  3. Heuristik
  4. `unresolved_issue`

## 4.1 Quantisierung und Rundung
- Interne Rechnung arbeitet mit hoher Präzision (bis zu 18 Nachkommastellen dort, wo Asset-Profile dies verlangen).
- Steuerlicher Report-Output wird erst im finalen Render-Schritt auf 2 Nachkommastellen gerundet.
- Keine Zwischenrundung in Rechenketten, außer explizit durch Regelprofil vorgegeben.

## 5. Import-Validierung
Fehlerklassen:
- `number_format_error`
- `conversion_factor_missing`
- `timezone_parse_error`
- `schema_mismatch`

Bei kritischen Fehlern:
- Kein stilles Fortfahren.
- Event in Issue-Inbox mit exakter Feldreferenz.

## 6. UI/UX-Anforderungen beim Import
- Vorschau pro Spalte: erkannter Zahlentyp und Trennzeichen.
- Umschaltmöglichkeit für Dezimal-/Tausenderinterpretation vor finalem Import.
- Sichtbare Warnung bei angewandten Umrechnungsfaktoren.

## 7. API-Erweiterungen
- `POST /api/v1/import/detect-format`
  - Liefert Zahl-/Datumserkennung je Spalte.
- `POST /api/v1/import/normalize-preview`
  - Zeigt Normalisierung inkl. Umrechnungsfaktoren ohne Persistenz.
- `POST /api/v1/import/confirm`
  - Persistiert freigegebene Parser-/Faktorregeln für den Importlauf.

## 8. Verifikation
- Gleiches Inputfile + gleiches Parserprofil => identischer numerischer Output.
- Stichprobenprüfung auf kritische Assets (HNT/IOT/MOBILE/SOL/BNB).
- Unit-Tests für gemischte Locale-Dateien und Faktorumrechnungen.
