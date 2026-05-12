# AGENTS.md

## Zweck

Diese Datei enthaelt verbindliche Arbeitsregeln fuer AI-/Coding-Agents in diesem Repository.

- Projektroot: `/workspace/steuerreport`
- Produkt: Deutsche Crypto-Steuerreport-Engine mit Dashboard
- Dokumentation: Deutsch
- Code, Bezeichner, Kommentare und Tests: Englisch, ausser vorhandener lokaler Kontext ist bereits Deutsch
- Aktiver Entwicklungsbranch: `codex/next-roadmap-work`
- Aktiver GitHub-PR: `#3`

Agents muessen diese Datei vor Aenderungen lesen. Danach ist der aktuelle Projektstand in
`docs/99_CHAT_HANDOFF_AKTUELL.md` zu lesen.

## Harte Produktregeln

- Steuerlogik gilt fuer deutsches Recht ab Steuerjahr `2020`.
- PDF-Export hat eine harte Grenze von maximal `100` Seiten pro PDF-Datei.
- Rohdaten duerfen niemals geloescht werden.
- Korrekturen erfolgen nur ueber dokumentierte Imports, Overrides, Review-Actions, Transfer-Matches oder Audit-Skripte.
- Anschaffungskosten, Preise, FX-Kurse, Cost Basis, Beleglage oder steuerliche Behandlung duerfen nicht erfunden werden.
- Ergebnisse duerfen nicht als steuerberaterlich final bezeichnet werden. Dieses Projekt liefert technische Berechnungen und Belegpakete.
- Historische offene Issues duerfen sichtbar bleiben, ohne den aktuellen Export zu blockieren, wenn das Runtime-Gate Jahre explizit als geschlossen markiert, zum Beispiel `runtime.review.closed_tax_years`.

## Daten Und Datenschutz

Lokale Primaerdaten und lokal generierte Arbeitsartefakte duerfen niemals committed oder gepusht werden.

In Git verboten:

- `*.csv`
- `*.xlsx`
- `var/`
- `*.db`
- `*.sqlite`
- `*.sqlite3`
- `.env`
- Exchange-Exports, Wallet-Exports, Finanzamt-/WISO-Abgaben, API-Antworten mit Personen- oder Accountdaten

Vor jedem Commit pruefen, dass keine Rohdaten oder generierten Arbeitsdaten gestaged sind:

```bash
git diff --cached --name-only | rg '\.(csv|xlsx|db|sqlite|sqlite3)$|^var/' || true
git status --ignored --short | rg '^(!!|\?\?) (var/|.*\.(csv|xlsx|db|sqlite|sqlite3)$)' || true
```

Wenn Primaerdaten fuer Analyse benoetigt werden, nur lokal verwenden und abgeleitete Erkenntnisse in `docs/` dokumentieren.

## Aktueller Betriebsstand

- Live-Dashboard nutzt Port `8000`.
- Workflows nicht auf Port `8001` umstellen.
- Aktueller Handoff: `docs/99_CHAT_HANDOFF_AKTUELL.md`.
- Aktueller Abschluss- und GitHub-Sync-Report: `docs/216_CURRENT_AUTONOMOUS_COMPLETION_AND_GITHUB_SYNC_2026-05-10.md`.
- AI-Readonly-Datenbank:
  `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`
- Statusbefehl fuer die AI-Readonly-Queue:

```bash
python3 scripts/ai_readonly_task_queue.py status
```

Die AI-Readonly-Queue dient zur Belegsuche und Planung. Ihre Ergebnisse sind nicht automatisch wahr. Wichtige Aussagen muessen vor Codeaenderungen oder Review-Status-Aenderungen gegen Datenbank oder Quelldateien geprueft werden.

## Git Und GitHub

- Auf `codex/next-roadmap-work` arbeiten, ausser der Nutzer nennt explizit einen anderen Branch.
- PR `#3` nach sinnvollen Commits aktuell halten.
- Pro validiertem Arbeitspaket bevorzugt einen zusammenhaengenden Commit erstellen.
- Kein Force-Push, ausser der Nutzer verlangt es explizit.
- Keine Rohdaten, `var/`, lokalen Datenbanken, lokalen Exporte oder Secrets committen.
- Fuer PR-/Issue-Status GitHub-Connector oder `gh` nutzen, wenn verfuegbar.
- Wenn `gh` nicht authentifiziert ist, GitHub-Connector fuer Metadaten und lokales `git` fuer Branch-/Remote-Status nutzen.

Vor Push:

```bash
git status --short --branch
git diff --check
git diff --cached --name-only | rg '\.(csv|xlsx|db|sqlite|sqlite3)$|^var/' || true
```

## Validierung

Waehrend der Entwicklung die kleinsten relevanten Tests ausfuehren. Vor Commits mit breitem Workflow-Umfang ausfuehren:

```bash
python3 -m ruff check . --no-cache
python3 -m mypy src/ --cache-dir=/tmp/steuerreport_mypy_cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit
COVERAGE_FILE=/tmp/steuerreport-api-coverage PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -p no:cacheprovider tests/unit/api --cov=src/tax_engine/api --cov-fail-under=80 -q
node --check src/tax_engine/ui/static/app.js
python3 scripts/verify_integrity.py --all-years
```

Wenn ein Gate nicht laufen kann, Grund dokumentieren und die naechstbeste risikoarme Ersatzpruefung ausfuehren.

## Architektur Und Code-Regeln

- Bestehende Projektmuster bevorzugen, keine unnoetigen neuen Abstraktionen.
- Steuerlogik deterministisch, auditierbar und Decimal-sicher halten.
- Pandas verwenden, wenn der umliegende Ingestion-/Audit-Workflow bereits Pandas nutzt.
- FIFO- und Derivate-Logik getrennt halten; Spot-Inventar und Derivate-PnL nicht vermischen.
- Deque-/FIFO-Verhalten erhalten, ausser die Steuermethode wird explizit geaendert.
- Raw-Event-Payloads unveraendert lassen. Abgeleiteten Zustand ueber normalisierte Zeilen, Review-Actions, Settings oder dokumentierte Overrides abbilden.
- API-Kompatibilitaets-Re-Exports in `tax_engine.api.app` erhalten, wenn Tests oder externe Aufrufer von dort importieren.
- Fuer Standalone-Skripte unter `scripts/` sind projektlokale Bootstrap-Imports mit `sys.path` erlaubt. Ruff `E402` ist fuer `scripts/*.py` ignoriert.
- Strukturierte Parser fuer CSV/XLSX/JSON verwenden. Keine bruechige String-Manipulation, wenn ein sinnvoller Parser existiert.
- Bei engen Steuer- oder Import-Fixes keine breiten Refactorings nebenbei machen.

## Datenbank Und Runtime-State

- Fuer Tests, die den Store zuruecksetzen, Testing-Umgebung setzen:

```bash
STEUERREPORT_ENV=testing STEUERREPORT_DB_PATH=/tmp/steuerreport/steuerreport_test.db
```

- Keine destruktiven DB-Operationen auf Live-/Projekt-Daten ausfuehren, ausser der Nutzer verlangt es explizit.
- Fuer Belegpruefungen bevorzugt die Readonly-SQLite-URI verwenden:

```bash
sqlite3 'file:/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite?mode=ro&immutable=1'
```

- Readonly-Snapshots nur ueber dokumentierte Skripte neu bauen.

## Dokumentationsregeln

- Groessere Erkenntnisse, Fixes und Entscheidungen unter `docs/` dokumentieren.
- `docs/99_CHAT_HANDOFF_AKTUELL.md` nach relevanter Arbeit aktuell halten.
- Neue Audit-/Statusdokumente mit naechster numerischer Praefixnummer und Datum anlegen, zum Beispiel:
  `docs/217_SHORT_TOPIC_2026-05-10.md`.
- Zusammenfassungen muessen unterscheiden zwischen:
  - deterministischem Fix
  - Belegluecke
  - unsicherer Aktion
  - verbleibender manueller Pruefung
- Alte Dokumente nicht loeschen, ausser der Nutzer verlangt es explizit. Ueberholte Befunde in neueren Dokumenten als ueberholt markieren.

## Review Und Steuerliche Sicherheit

Beim Bearbeiten steuerlicher Issues:

- Den neuesten abgeschlossenen Job fuer das betroffene Steuerjahr identifizieren.
- Pruefen, ob ein Issue current-year-blocking oder nur historisch sichtbar ist.
- Zero-Cost-Befunde gegen `ai_open_zero_cost_tax_lines` oder den aktuellen Processing-Output validieren.
- Bei Transfer-Chain-Fixes Event-IDs, Zeitstempel, Assets, Mengen, Quelldateien und Match-IDs dokumentieren.
- Bei Preis- oder FX-Backfills Quelle, Datum, Asset, Kurs und Begruendung dokumentieren.
- Bei manuellen Entscheidungen erforderliche Belege und Review-Begruendung erfassen.
- Review-Issues nie nur schliessen, weil sie stoeren. Nur schliessen, wenn Daten oder explizite Projektregeln das tragen.

## Frontend-Regeln

- Das Dashboard ist ein operatives Werkzeug, keine Landingpage.
- Wichtige Controls muessen im relevanten Dashboard-Bereich sichtbar sein, nicht nur versteckt in einem globalen Header.
- UI dicht, lesbar und review-orientiert halten.
- Keine dekorativen Redesigns, die Import, Export, Review oder Reconciliation nicht verbessern.
- JavaScript-Syntax pruefen mit:

```bash
node --check src/tax_engine/ui/static/app.js
```

## Agent-Workflow

Standardablauf:

1. `AGENTS.md` lesen.
2. `docs/99_CHAT_HANDOFF_AKTUELL.md` lesen.
3. `git status --short --branch` pruefen.
4. Bei Sync- oder Release-Arbeit aktuellen GitHub-PR-/Issue-Status pruefen.
5. Direkt arbeiten, wenn der Nutzerauftrag klar ist.
6. Nur fragen, wenn eine Entscheidung riskant ist, lokal nicht ermittelt werden kann oder explizites Steuer-/Belegurteil braucht.
7. Validieren.
8. Dokumentieren.
9. Nur GitHub-sicheren Umfang committen und pushen, wenn Sync verlangt ist oder klar zum Auftrag gehoert.

Nicht bei einem Plan stehenbleiben, wenn der Nutzer Ausfuehrung verlangt. Bei Blockern exakte Belege, Befehle und die naechste sichere Aktion hinterlassen.
