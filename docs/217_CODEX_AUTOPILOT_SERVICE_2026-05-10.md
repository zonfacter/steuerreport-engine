# Codex-Autopilot als Dienst

Stand: 2026-05-10

## Ziel

Der Autopilot soll das Projekt weiterbearbeiten, ohne dass im Terminal immer wieder
`weiter` geschrieben werden muss. Er ersetzt keine fachliche Steuerentscheidung und
keinen Beleg. Er arbeitet eine lokale Queue ab, validiert danach den Repo-Zustand und
schreibt Logs sowie Statusdateien unter `var/codex_autopilot_queue/`.

## Umsetzung

- Skript: `scripts/codex_autopilot_queue.py`
- systemd-Vorlage: `deploy/systemd/steuerreport-codex-autopilot.service`
- Queue:
  - `var/codex_autopilot_queue/pending/`
  - `var/codex_autopilot_queue/running/`
  - `var/codex_autopilot_queue/done/`
  - `var/codex_autopilot_queue/failed/`
- Status:
  - `var/codex_autopilot_queue/status.json`
  - `var/codex_autopilot_queue/results.jsonl`
  - `var/codex_autopilot_queue/runner.log`
  - `var/codex_autopilot_queue/logs/`

Der Worker nutzt `codex exec` im Modus `workspace-write` mit `-c approval_policy="never"`.
Er nutzt bewusst nicht `danger-full-access`.

## Sicherheit

Standardmaessig wird nicht gepusht. Push ist nur pro Task mit `--allow-push` erlaubt
und wird nur versucht, wenn die Post-Checks gruen sind.

Der Worker prueft nach jeder Codex-Ausfuehrung:

```bash
git diff --check
git diff --cached --name-only | rg '\.(csv|xlsx|db|sqlite|sqlite3)$|^var/|^\.env$' || true
git status --ignored --short | rg '^(!!|\?\?) (var/|.*\.(csv|xlsx|db|sqlite|sqlite3)$|\.env$)' || true
```

Verboten bleiben insbesondere:

- Rohdaten
- `var/`
- lokale Datenbanken
- CSV-/XLSX-Exporte
- `.env`
- Finanzamt-, WISO-, Exchange- oder Wallet-Primärdaten

## Bedienung

Status anzeigen:

```bash
python3 scripts/codex_autopilot_queue.py status
```

Konservativen Standardtask anlegen:

```bash
python3 scripts/codex_autopilot_queue.py init-defaults
```

Eigenen Task anlegen:

```bash
python3 scripts/codex_autopilot_queue.py enqueue \
  --task-id "dashboard_next_review_step" \
  --title "Naechsten Dashboard-Review-Schritt umsetzen" \
  --task "Lies AGENTS.md und docs/99_CHAT_HANDOFF_AKTUELL.md. Setze den naechsten sicheren Dashboard- oder Review-Schritt um und dokumentiere das Ergebnis." \
  --validation-profile quick
```

Queue einmal oder dauerhaft abarbeiten:

```bash
python3 scripts/codex_autopilot_queue.py run --max-hours 12 --max-tasks 0 --sleep-seconds 10
```

Ein Task mit Push-Erlaubnis:

```bash
python3 scripts/codex_autopilot_queue.py enqueue \
  --task-id "github_safe_sync" \
  --title "Validierten GitHub-Sync ausfuehren" \
  --task "Validiere den aktuellen GitHub-sicheren Projektstand, committe ein zusammenhaengendes Arbeitspaket und pushe den Branch nur wenn alle Checks gruen sind." \
  --validation-profile full \
  --allow-push
```

## systemd

Die Vorlage wird nicht automatisch installiert. Aktivierung:

```bash
sudo cp deploy/systemd/steuerreport-codex-autopilot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now steuerreport-codex-autopilot.service
```

Kontrolle:

```bash
systemctl status steuerreport-codex-autopilot.service --no-pager
journalctl -u steuerreport-codex-autopilot.service -n 120 --no-pager
tail -n 120 var/codex_autopilot_queue/runner.log
```

Stoppen:

```bash
sudo systemctl stop steuerreport-codex-autopilot.service
sudo systemctl disable steuerreport-codex-autopilot.service
```

## Grenzen

Der Autopilot soll selbststaendig Code, Tests, Dokumentation, lokale Validierung und
GitHub-sichere Commits vorbereiten. Er soll stoppen, wenn:

- ein Primaerbeleg fehlt,
- eine steuerliche Bewertung nicht deterministisch aus den Daten folgt,
- Rohdaten oder Secrets betroffen waeren,
- lokale Tests widerspruechliche Ergebnisse liefern,
- Merge-/Git-Konflikte auftreten,
- der Nutzer eine fachliche Entscheidung treffen muss.

Damit ist er fuer laengere Entwicklungslaeufe geeignet, aber nicht fuer unbeaufsichtigte
steuerliche Freigaben.
