# Lokale KI Ergebnisse und Codex-Folgeauftrag

Stand: 2026-05-10

## Queue-Status

Die lokale Readonly-KI-Queue ist abgeschlossen.

- `done`: `13`
- `failed`: `2`
- `pending`: `0`
- `running`: `0`

Fehlgeschlagene Tasks waren Infrastruktur-/LLM-Fehler, keine fachlich abgeschlossenen
Befunde:

- `exports_pdf_wiso_readiness_2025_2026_20260510`: RemoteDisconnected
- `mining_rewards_business_private_split_20260510`: HTTP 503

## Verifizierte Punkte

Readonly-DB:

```text
/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite
```

Neueste abgeschlossene Jobs:

| Jahr | Job |
| --- | --- |
| 2020 | `287cc41c-9055-42ca-8b5a-9d5578e07dc6` |
| 2021 | `5ab77c28-68f9-42ca-8b5a-9d5578e07dc6` |
| 2022 | `c4d8719c-4041-443a-b182-d9f6ccf06407` |
| 2023 | `bf4e3974-5e7e-4bfe-9e15-6992ad4812bb` |
| 2024 | `0b0d5264-b38f-4726-81eb-bd54191a0064` |
| 2025 | `f4342b4b-a502-47cf-a5dc-255eda49d94c` |
| 2026 | `924d49e7-b215-480f-ae35-9dddc8d99648` |

Aktuelle offene Zero-Cost-Zeilen:

| Jahr | Asset | Zeilen | Proceeds EUR |
| --- | --- | ---: | ---: |
| 2021 | BNB | 2 | 0.00 |
| 2021 | HNT | 8 | 1790.06 |
| 2021 | UNKNOWN | 3 | 11.51 |
| 2022 | HNT | 5 | 2300.13 |
| 2022 | USDT | 3 | 1383.88 |
| 2024 | USDC | 1 | 0.00 |

Damit ist die KI-Aussage bestaetigt, dass `2025` aktuell keine offenen
Zero-Cost-Zeilen in `ai_open_zero_cost_tax_lines` hat.

## Korrigierte KI-Befunde

Ein KI-Bericht behauptete, es gebe keine direkten Bitget-API-Daten fuer `2025`.
Diese Aussage ist zu grob und wurde gegen die DB korrigiert:

- `ai_raw_events_flat` enthaelt `2025`-Events mit `source='bitget_tax_api'`.
- Gefundene Event-Typen enthalten unter anderem:
  - `derivative open_long`: `247`
  - `derivative close_long`: `235`
  - `derivative close_short`: `202`
  - `derivative open_short`: `198`
  - `derivative fee`: `162`
  - `trade`: `60`

Der belastbare Befund ist stattdessen:

- In `source_files` liegen grosse Bitget-/Futures-Dateien, zum Beispiel
  `bitget_api_futures_recheck_1738195197003_1740787196003` mit `917` Zeilen.
- In `derivative_lines` gibt es fuer den 2025-Job trotzdem `0` Zeilen.
- `derivative_lines` hat keine eigene `tax_year`-Spalte; Pruefung muss ueber
  Join mit `processing_queue` erfolgen.

## Belastbare Folgearbeit

Der naechste Codex-Auftrag soll die KI-Befunde nicht ungeprueft uebernehmen,
sondern sie deterministisch gegen DB, Import-Code und Tests abarbeiten.

Prioritaet:

1. Bitget 2025 Derivate-Pipeline klaeren:
   - Warum entstehen aus `bitget_tax_api` derivative Events keine `derivative_lines`
     fuer Job `f4342b4b-a502-47cf-a5dc-255eda49d94c`?
   - Liegt es an Ingestion, Normalisierung, DerivativesManager, Job-Filter oder
     Report-/Snapshot-Export?
2. AI-Readonly-Schema-/Query-Hygiene verbessern:
   - Audit-/KI-Queries duerfen nicht Spalten wie `raw_events.source` oder
     `derivative_lines.tax_year` voraussetzen.
   - Stattdessen `ai_raw_events_flat` oder JSON-Extraktion und Join mit
     `processing_queue` verwenden.
3. Fehlgeschlagene Readonly-KI-Tasks wiederholbar machen:
   - HTTP 503 und RemoteDisconnected sollen nicht den ganzen Lauf als fachlich
     erledigt erscheinen lassen.
   - Retry/backoff oder gezieltes Requeue fuer fehlgeschlagene Tasks pruefen.

## Angelegter Autopilot-Auftrag

Task-ID:

```text
verify_local_ai_bitget_derivatives_followup_20260510
```

Ziel:

- lokale KI-Ergebnisse pruefen,
- falsche/fragile SQL-Annahmen korrigieren,
- Bitget-2025-Derivate-Luecke analysieren,
- falls deterministisch moeglich Code/Test/Doku fixen,
- sonst exakten Blocker mit SQL-Belegen dokumentieren.

Der Task hat `validation_profile=quick` und `allow_push=false`.
