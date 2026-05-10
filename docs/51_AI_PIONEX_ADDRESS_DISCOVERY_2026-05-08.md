# AI Pionex Address Discovery - 2026-05-08

## Scope

Local llama.cpp review for the hypothesis that another Pionex deposit address or missing platform export explains the early 2022 Pionex-USDT gap.

## Inputs

- Candidate JSON: `/workspace/steuerreport/var/pionex_address_discovery_candidates_2026-05-08.json`
- Result JSON: `/workspace/steuerreport/var/ai_pionex_address_discovery_2026-05-08.json`
- Known Pionex TRON deposit address: `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ`
- Known Pionex sweep address: `TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU`
- Relevant transfer-like events scanned: `5493`
- Address groups sent to AI: `7`
- Focused events sent to AI: `260`

## LLM Status

- status: `success`
- model: `qwen3-coder-30b-a3b-llamacpp`
- endpoint: `http://192.168.2.203:11435`
- duration_seconds: `410.117`

## Summary

Die Analyse zeigt eine signifikante Lücke in den Pionex-USDT-Daten für Anfang 2022. Die bekannte Pionex-TRON-Adresse TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ hat nur 4 bekannte USDT-Ein- und Auszahlungen, was nicht ausreicht, um die gesamte USDT-Bewegung abzudecken. Es gibt keine früheren TRC20-Transaktionen, die auf eine andere Pionex-Adresse hinweisen. Die einzige plausible Erklärung für die Lücke ist eine weitere Pionex-Adresse, die nicht bisher identifiziert wurde.

## Confirmed Facts

- Die bekannte Pionex-TRON-Adresse TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ hat nur 4 bekannte USDT-Ein- und Auszahlungen
- Es gibt keine früheren TRC20-Transaktionen auf der bekannten Adresse
- Die Pionex-Plattform hat mindestens 1643.4055675662 USDT an fehlenden Transaktionen
- Die Pionex-Adresse hat keine früheren TRC20-Transaktionen
- Die Pionex-Plattform hat mindestens 1643.4055675662 USDT an fehlenden Transaktionen

## Unlikely Explanations

- Die Lücke könnte durch eine fehlerhafte Datenerfassung oder -verarbeitung entstanden sein, da die bekannte Adresse nur 4 Transaktionen aufweist, was nicht ausreicht, um die gesamte USDT-Bewegung abzudecken
- Es ist unwahrscheinlich, dass die Lücke durch eine fehlende Exportdatei der Pionex-Plattform erklärt werden kann, da die bekannte Adresse keine früheren TRC20-Transaktionen aufweist
- Die Lücke ist nicht durch eine fehlende oder falsche Datenerfassung auf der Binance-Seite zu erklären, da die Pionex-Plattform mindestens 1643.4055675662 USDT an fehlenden Transaktionen hat

## Ranked Next Checks

- `1` Suche nach weiteren Pionex-TRON-Adressen, die mit USDT-Transaktionen in der frühen 2022-Periode in Verbindung stehen könnten | target: `TRON-Blockchain` | reason: Die bekannte Adresse hat nur 4 Transaktionen, was nicht ausreicht, um die gesamte USDT-Bewegung abzudecken
- `2` Überprüfung der Pionex-Exportdateien auf fehlende USDT-Transaktionen | target: `Pionex-Exportdateien` | reason: Die Pionex-Plattform hat mindestens 1643.4055675662 USDT an fehlenden Transaktionen
- `3` Analyse der Pionex-Transaktionen auf mögliche fehlende oder falsche Datenerfassung | target: `Pionex-Transaktionen` | reason: Die Pionex-Plattform hat mindestens 1643.4055675662 USDT an fehlenden Transaktionen

## Candidate Pionex Addresses

- `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ` confidence `high`: Bereits bekannt und hat 4 bekannte USDT-Transaktionen

## Confidence

high
