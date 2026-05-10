# USDT 2022 Zero-Cost Review-Entscheidungspaket

Stand: 2026-05-10

## Ergebnis

Das letzte offene Zero-Cost-Issue ist kein Preis-/Softwarefehler mehr, sondern eine fachliche Review-Entscheidung:

- Aktuelles Issue nach Gesamtlauf: `zero_cost_tax_lots:2022:USDT:942afb62-85f5-4690-9b74-2e6195d5205f`
- Urspruengliches Dossier-Issue: `zero_cost_tax_lots:2022:USDT:c94a113e-1423-4ac1-8a72-9a12cd1156b1`
- Jahr/Asset: `2022 / USDT`
- Betroffene steuerpflichtige Zeilen: `3`
- Menge aktuell: `1569.34243684620000000000 USDT`
- Erlöse aktuell: `1383.448602294939514000000000 EUR`
- Dossier: `docs/181_USDT_2022_ZERO_COST_DOSSIER_2026-05-10.md`

Die lokale KI-Prüfung kam ebenfalls zu dem Ergebnis, dass keine belastbare Auto-Korrektur möglich ist:

- Modell: `qwen3.6-35b-a3b-iq4xs`
- Ergebnisdatei: `var/usdt_2022_zero_cost_ai_review_2026-05-10.json`
- Bewertung: fehlende historische USDT-Anschaffungskette; `can_auto_fix=false`

## Betroffene Vorgänge

1. `2022-01-05T15:36:46Z`, Binance Trade-Out, `75.1046222062 USDT`, Erlös `66.352680580511514 EUR`
2. `2022-01-19T12:45:42Z`, Pionex Trade-Out, `168.84689687 USDT`, Erlös `148.8300972460615 EUR`
3. `2022-01-19T12:56:19Z`, Pionex Trade-Out, `1325.39091777 USDT`, Erlös `1168.2658244683665 EUR`

## API-Bearbeitung

Die API kann das Issue jetzt direkt kontextualisieren und entscheiden:

```http
GET /api/v1/review/issue-context/zero_cost_tax_lots:2022:USDT:942afb62-85f5-4690-9b74-2e6195d5205f
```

Für weitere Prüfung:

```json
{
  "issue_id": "zero_cost_tax_lots:2022:USDT:942afb62-85f5-4690-9b74-2e6195d5205f",
  "status": "in_review",
  "note": "USDT-Anschaffungskette 2021/2022 weiter pruefen; keine Auto-Korrektur ohne Primaerbeleg."
}
```

Für explizite Nullbasis-Entscheidung:

```json
{
  "issue_id": "zero_cost_tax_lots:2022:USDT:942afb62-85f5-4690-9b74-2e6195d5205f",
  "status": "wont_fix",
  "note": "Explizite Review-Entscheidung: Anschaffungskette nicht belegbar, Nullbasis bleibt im Steuerreport sichtbar dokumentiert."
}
```

Endpoint:

```http
POST /api/v1/issues/update-status
```

## Fachliche Bewertung

`wont_fix` bedeutet hier nicht, dass der Vorgang ignoriert wird. Die steuerpflichtigen Zeilen bleiben mit Cost Basis `0` im Steuerreport sichtbar. Nur das Review-Gate wird freigegeben, weil die fehlende Anschaffungskette bewusst dokumentiert und nicht künstlich ersetzt wird.

Eine automatische Buchung wäre fachlich schwächer, solange kein Primärbeleg für einen vorherigen USDT-Zufluss oder eine Pionex-/Binance-Opening-Balance vorliegt.
