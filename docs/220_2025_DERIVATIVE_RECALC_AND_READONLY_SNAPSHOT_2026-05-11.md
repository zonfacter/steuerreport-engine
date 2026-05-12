# 2025 Derivate-Neuberechnung und AI-Readonly-Snapshot

Stand: 2026-05-11

## Anlass

Nach dem Fix in `src/tax_engine/core/derivatives.py` musste das Steuerjahr `2025`
neu berechnet werden, damit die Bitget-Derivate nicht nur im Code simulierbar,
sondern auch in `derivative_lines` persistiert sichtbar sind.

## Neuberechnung

Ausgefuehrt wurde gezielt nur `2025` ueber die Processing-API-Funktionen:

```text
tax_year=2025
ruleset_id=DE-2025-v1.0
job_id=b7c013f5-d176-4875-bdbe-df614bee4800
status=completed
```

Ergebnis des neuen Jobs:

| Kennzahl | Wert |
| --- | ---: |
| Tax-Lines | 465 |
| Derivate-Lines | 957 |
| Derivate processed_events | 957 |
| Standalone Cash Settlements | 957 |
| Open Positions Remaining | 0 |
| Unmatched Closes | 0 |
| Termingeschaefte netto EUR | -1708.50463884 |
| Derivate Verlustsumme EUR | 3647.91700648 |

Die Zahl `957` ist niedriger als die vorherige reine Raw-Event-Simulation
`1047`, weil der echte Processing-Lauf Referenz-/Blockpit-Quellen sowie
Overrides und Integrationsfilter anwendet.

## Readonly-Snapshot

Danach wurde die AI-Readonly-DB neu gebaut:

```text
/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite
```

Snapshot-Ergebnis:

```text
size_bytes=455090176
```

Gegenprobe in der Readonly-DB:

| Jahr | Job | Tax-Lines | Derivate-Lines |
| ---: | --- | ---: | ---: |
| 2025 | `b7c013f5-d176-4875-bdbe-df614bee4800` | 465 | 957 |

Derivate nach Typ:

| Typ | Zeilen | Gain/Loss EUR |
| --- | ---: | ---: |
| close | 409 | -788.371769 |
| fee | 546 | -514.762065 |
| liquidation | 2 | -405.370804 |

Summe:

```text
gain_loss_eur=-1708.50463884
negative_loss_abs_eur=3647.91700648
```

## Review-Gate

Review-Gate nach Neuberechnung:

```text
allow_export=true
issues_open=0
issues_open_total=3
issues_historical_open=3
issues_high_open=0
unmatched_total=0
```

Die drei sichtbaren offenen Issues sind historische Altjahr-Issues und blockieren
den aktuellen Export nicht:

- `2021/HNT`
- `2022/USDT`
- `2022/HNT`

## Validierung

Ausgefuehrt:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/verify_integrity.py --all-years
curl -fsS http://127.0.0.1:8000/api/v1/health
```

Ergebnis:

- `verify_integrity.py --all-years`: gruen
- `steuerreport-api.service`: neu gestartet und `active`
- `/api/v1/health`: `status=success`

## Hinweis

Die technische Erfassung der Bitget-Cash-Settlements ist jetzt im 2025-Job
persistiert. Das ist weiterhin keine steuerberaterliche Endfreigabe, sondern ein
deterministischer technischer Rechenstand mit dokumentiertem Ruleset.
