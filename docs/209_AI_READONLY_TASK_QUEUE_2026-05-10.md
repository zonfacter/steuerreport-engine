# AI Readonly Task Queue - 2026-05-10

## Zweck

Die lokale KI auf CT203 kann mehrere Analyseauftraege nacheinander abarbeiten.
Sie arbeitet nur gegen den read-only SQLite-Snapshot und speichert Ergebnisse dauerhaft.
Die Cloud-KI validiert die Ergebnisse anschliessend, bevor steuerlich wirksame Aenderungen uebernommen werden.

## Dateien

- Queue-Script: `scripts/ai_readonly_task_queue.py`
- DB-Gegencheck: `scripts/ai_db_countercheck.py`
- Snapshot-Build: `scripts/build_ai_readonly_db_snapshot.py`
- Queue-Verzeichnis: `var/ai_readonly_queue/`
- Status: `var/ai_readonly_queue/status.json`
- Ergebnisindex: `var/ai_readonly_queue/results.jsonl`
- Runner-Log: `var/ai_readonly_queue/runner.log`
- systemd-Log: `var/ai_readonly_queue/systemd.log`

## systemd

```bash
systemctl status steuerreport-ai-readonly-queue.service
systemctl start steuerreport-ai-readonly-queue.service
systemctl stop steuerreport-ai-readonly-queue.service
```

Unit:

```text
/etc/systemd/system/steuerreport-ai-readonly-queue.service
```

## Bedienung

Standardauftraege anlegen:

```bash
python3 scripts/ai_readonly_task_queue.py init-defaults
```

Eigenen Auftrag anlegen:

```bash
python3 scripts/ai_readonly_task_queue.py enqueue \
  --task-id "kurzer_eindeutiger_name" \
  --title "Lesbarer Titel" \
  --task "Konkreter read-only Analyseauftrag fuer die KI"
```

Status ansehen:

```bash
python3 scripts/ai_readonly_task_queue.py status
```

Manuell laufen lassen:

```bash
python3 scripts/ai_readonly_task_queue.py run --max-hours 16 --max-tasks 0
```

## Aktueller Start

- Standardauftraege angelegt: `5`
- Testlauf erfolgreich: `hnt_2021_cost_basis_chain`
- Ergebnis: `var/ai_db_countercheck_2026-05-10_180842.md`
- Langlauf als systemd-Dienst gestartet.
- Langlauf abgeschlossen:
  - `done=5`
  - `pending=0`
  - `running=0`
  - `failed=0`

## Dashboard

- API: `GET /api/v1/ai-readonly-queue/status`
- Anzeige: Cockpit -> `Lokale KI-Auftragsqueue`
- Sichtbar sind systemd-Status, Queue-Zaehler, aktueller Task und letzte Ergebnisdateien.

## Sicherheitsgrenzen

- Snapshot wird vor dem Lauf neu gebaut.
- Snapshot-Datei ist read-only (`0444`) und wird als `mode=ro&immutable=1` geoeffnet.
- KI darf nur SQL-SELECTs vorschlagen.
- Queue fuehrt nur sichere `SELECT`/`WITH SELECT` aus.
- Keine RAW-Daten, Overrides, Transfer-Matches oder Steuerjobs werden durch die KI geschrieben.
