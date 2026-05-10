# AI Bitget 2025 Blockpit Review - 2026-05-09

## Lauf

- Dauer: `44.468s`
- LLM: `http://192.168.2.203:11435` / `qwen3.6-35b-a3b-iq4xs`
- Usage: `{'completion_tokens': 894, 'prompt_tokens': 9731, 'total_tokens': 10625, 'prompt_tokens_details': {'cached_tokens': 0}}`

## Summary

Der Bitget-2025-Stand zeigt 2923 effektive, nicht gematchte Referenzzeilen aus dem Blockpit-Export. Diese stammen primär aus Januar und Mai/Juni 2025 und bestehen zu ~70% aus 'derivative fee'. Da die API-Probe keine neuen Daten lieferte (nur Duplikate), sind diese Zeilen als Suchanker für manuelle Rekonstruktion (Support/On-Chain) zu nutzen, nicht als automatische Buchung. Traffic Light: Yellow.

- Ampel: `yellow`

## Confirmed Facts

- 2923 effektive Blockpit-Referenzzeilen 2025 sind nicht mit API-Daten gematcht.
- Hauptcluster: 'derivative fee' (2057 Zeilen), 'derivative loss' (399), 'derivative profit' (357).
- Zeitliche Verteilung: 2025-02 (1012), 2025-05 (846), 2025-06 (817) dominieren.
- Asset-Fokus: USDT (1322), SOL (1474).
- API-Probe ergab 0 neue Events, nur 1138 Duplikate; Spot-Bills sind limitiert.

## Risk Clusters

- {'cluster_id': 'CL_FEE_DERIV_2025_02', 'description': 'Häufung von Derivative Fees im Februar 2025', 'count': 1012, 'primary_asset': 'USDT', 'risk_level': 'high', 'action': 'Prüfung auf Funding Rates oder Settlement-Gebühren; Abgleich mit Support-Export.'}
- {'cluster_id': 'CL_FEE_DERIV_2025_05_06', 'description': 'Häufung von Derivative Fees in Mai/Juni 2025', 'count': 1663, 'primary_asset': 'USDT', 'risk_level': 'high', 'action': 'Prüfung auf Funding Rates oder Settlement-Gebühren; Abgleich mit Support-Export.'}
- {'cluster_id': 'CL_PNL_DERIV_2025', 'description': 'Offene Derivative PnL (Loss/Profit) ohne Trade-Match', 'count': 756, 'primary_asset': 'USDT', 'risk_level': 'medium', 'action': 'Verifizierung, ob PnL bereits in Trades gebucht ist oder separat zu erfassen ist.'}

## Recommended Next Steps

- Priorität 1: Bitget-Support-Export für Februar, Mai und Juni 2025 anfordern, um die 2923 Zeilen zu validieren.
- Priorität 2: On-Chain-Transfers für SOL und USDT in den betroffenen Monaten prüfen, um Ein-/Ausgänge zu bestätigen.
- Priorität 3: Manuelle Clusterung der 'derivative fee'-Zeilen nach 'Position Open', 'Position Close' und 'Settlement/Funding' zur korrekten steuerlichen Einordnung.
- Priorität 4: Keine automatische Buchung der 2923 Referenzzeilen als Primary-Events; sie dienen nur als Suchanker.

## Must Not Do

- Keine automatischen Buchungen der 2923 offenen Referenzzeilen vornehmen.
- Blockpit-Export nicht als Primärquelle für Steuerberechnung verwenden, solange API/Support-Belege fehlen.
- Keine neuen API-Requests starten, da die aktuelle Probe keine neuen Daten lieferte.
