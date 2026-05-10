# Pionex USDT Final Blocker Audit - 2026-05-09

## Ergebnis

- Status: `hard_blocker_primary_evidence_or_explicit_non_tax_decision_required`
- Pionex-Adresse: `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ`
- Bekannte TRC20-USDT-Eingaenge auf diese Adresse: `4`
- Bekannte TRC20-USDT-Eingaenge bis Worst: `1445.38419 USDT`
- Benoetigtes Opening zur negativen Chronologievermeidung: `1643.2312211162 USDT`
- Nicht durch sichtbare Deposits gedeckt: `197.8470311162 USDT`
- Binance-Withdrawals zur Pionex-Adresse: `4` / `3125.902987 USDT`
- Steuerwirksamer Auto-Import empfohlen: `False`

## Onchain-Befund

- Die Pionex-TRON-Adresse ist eine Durchgangsadresse: jeder sichtbare Eingang wurde kurz danach an eine Pionex-Sweep-Adresse weitergeleitet.
- Vor dem Worst-Zeitpunkt am `2022-01-19T12:56:19+00:00` gibt es auf der bekannten Adresse nur zwei USDT-Eingaenge.
- Es gibt keinen Onchain-Beleg fuer einen weiteren USDT-Eingang auf diese bekannte Adresse vor dem Worst-Zeitpunkt.

## Bekannte TRC20-Transfers

| Zeit UTC | Richtung | Betrag USDT | Von | An | TX |
|---|---:|---:|---|---|---|
| 2021-12-25T16:20:48+00:00 | in | 200 | `TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr` | `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ` | `b742f811bf6372301484d585166ebb0f334996185285c8fc91ced3830c724182` |
| 2021-12-25T16:24:21+00:00 | out | 200 | `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ` | `TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU` | `2eb9fa1ede88875ccf0b5adf46a516baff3c54417303738fc4147f8bab8e08ac` |
| 2022-01-19T12:51:36+00:00 | in | 1245.38419 | `TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr` | `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ` | `b930ad780ec33e9ece0a5945404674d89e0b9fa165ed9d02602fab57d6a217aa` |
| 2022-01-19T12:55:51+00:00 | out | 1245.38419 | `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ` | `TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU` | `182678a352539313e9c7af909585f3912dbd1268aaf3235272fa1faaab6e180d` |
| 2022-02-23T05:38:57+00:00 | in | 696.827474 | `TNXoiAJ3dct8Fjg4M9fkLFh9S2v9TXc32G` | `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ` | `a08ff362825ec9a4ce35a3f4803cf1dba32cf1deaae4fc58281001b6a0692566` |
| 2022-02-23T05:43:30+00:00 | out | 696.827474 | `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ` | `TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU` | `42e2446e9afabe998e891157f66931f008e3385c68b911ef7cedddf1f4919b85` |
| 2022-02-25T21:32:36+00:00 | in | 983.691323 | `TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr` | `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ` | `9542656804be81094930fd1ddb83710f82c54fda18b2691c1ffd57b95d89a132` |
| 2022-02-25T21:37:09+00:00 | out | 983.691323 | `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ` | `TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU` | `56cb651c8175b1fad0d8d8cfcbbbd21c391b3d513a61de0208b8178af3f44dd9` |

## Bewertung

- Die sichtbaren Binance- und TRON-Daten belegen die bekannten Pionex-Deposits, erklaeren aber nicht das fehlende Start-/Botkapital.
- Der Restblocker ist damit kein globaler USDT-Endbestandsfehler, sondern ein Pionex-plattformlokaler Startbestand-/Bot-Historien-Nachweis.
- Ohne Primaerbeleg sollte keine steuerwirksame Einnahme oder Anschaffung erfunden werden.
- Fuer einen final sauberen Report bleiben zwei belastbare Wege: Pionex-Support/Snapshot/Bot-Historie nachreichen oder explizit als nicht steuerwirksame Inventar-Normalisierung freigeben.

## Empfohlene naechste API-Entscheidung

```json
{
  "candidate_id": "pionex-usdt-opening-balance-2021-12-28",
  "decision": "request_more_evidence",
  "reviewer": "codex",
  "note": "Known Binance/TRON/Pionex exports prove only 1445.38419 USDT deposits before the 2022-01-19 worst point. Missing 197.8470311162 USDT remains unsupported by primary Pionex bot/start-balance evidence; keep as non-tax review blocker.",
  "evidence": {
    "final_blocker_audit": "docs/167_PIONEX_USDT_FINAL_BLOCKER_AUDIT_2026-05-09.md",
    "decision_dossier": "docs/157_PIONEX_OPENING_DECISION_DOSSIER_2026-05-09.md",
    "tron_summary": "var/tron_pionex_deposit_address_usdt_summary_2026-05-08.json",
    "binance_withdraw_summary": "var/binance_withdraw_address_summary_2026-05-08.json"
  }
}
```
