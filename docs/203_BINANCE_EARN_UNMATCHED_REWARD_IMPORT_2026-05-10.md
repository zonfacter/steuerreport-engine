# Binance Earn Unmatched Reward Import

Stand: 2026-05-10T16:28:44.032399+00:00

Quelle: `var/binance_earn_reward_dedupe_2026-05-10.json`

## Import

- Modus: `reported_existing_imports`
- Zeilen: `11`
- Eingefuegte Events: `0`
- Duplikate: `0`
- Bereits vorhandene Events: `11`
- Source file id: ``

## Mengen

| Asset | Anzahl | Menge |
|---|---:|---:|
| `JUP` | `7` | `3.13961569` |
| `SOL` | `4` | `0.00593132` |

## Steuerliche Einordnung

- Importiert wurden nur Reward-Kandidaten, die im Dedupe-Audit nicht bereits in `raw_events` vorhanden waren.
- Typ: `interest`, `side=in`, Quelle: `binance_api`.
- EUR-Bewertung/Preisanker bleibt Aufgabe des Preisbackfills; die Rohmenge ist jetzt steuerlich sichtbar und zugleich ueber `product_position_event_id` zum Produktpositionsbeleg rueckverfolgbar.
- Preisbackfill wurde anschliessend fuer `JUP,SOL` im Zeitraum `2026-05-03` bis `2026-05-10` ausgefuehrt; `15` Tagespreise wurden aus `coingecko_history` gecached.
