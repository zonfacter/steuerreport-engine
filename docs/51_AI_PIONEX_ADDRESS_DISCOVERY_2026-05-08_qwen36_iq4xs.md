# AI Pionex Address Discovery - 2026-05-08

## Scope

Local llama.cpp review for the hypothesis that another Pionex deposit address or missing platform export explains the early 2022 Pionex-USDT gap.

## Inputs

- Candidate JSON: `/workspace/steuerreport/var/pionex_address_discovery_candidates_2026-05-08.json`
- Result JSON: `/workspace/steuerreport/var/ai_pionex_address_discovery_2026-05-08_qwen36_iq4xs.json`
- Known Pionex TRON deposit address: `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ`
- Known Pionex sweep address: `TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU`
- Relevant transfer-like events scanned: `5493`
- Address groups sent to AI: `7`
- Focused events sent to AI: `260`

## LLM Status

- status: `success`
- model: `qwen3.6-35b-a3b-iq4xs`
- endpoint: `http://192.168.2.203:11436`
- duration_seconds: `282.218`

## Summary

Die bekannte TRON-Adresse TMHP... zeigt exakte 1:1 Ueberweisungen an TWD..., was eine direkte Zuordnung zu Pionex-Deposits bestaetigt. Der 'Opening Gap' von ca. -1643 USDT ist jedoch zu gross, um durch unentdeckte Deposits auf dieser spezifischen Adresse erklaert zu werden (max. 4 Deposits nachgewiesen). Es besteht eine hohe Plausibilitaet fuer weitere, nicht erfasste Pionex-TRC20-Adressen oder fehlende Exportdaten aus dem Jahr 2021/2022.

## Confirmed Facts

- Die Adresse TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ ist eine reine Durchgangsadresse fuer Pionex-TRC20-Deposits.
- Alle 4 nachgewiesenen Deposits (Summe 3125.90 USDT) wurden sofort an TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU weitergeleitet.
- Es gibt keine historischen TRC20-Transfers vor dem 25.12.2021 auf TMHP....
- Der bilanzielle Gap von -1643.40 USDT kann nicht durch nachtraegliche Entdeckung von Transfers auf der bekannten Adresse geschlossen werden.

## Unlikely Explanations

- Der Gap resultiert aus vergessenen manuellen Eintraegen auf der bekannten Adresse TMHP..., da die API-Daten vollstaendig erscheinen.
- Der Gap ist auf interne Pionex-Buecherungsfehler zurueckzufuehren, da die On-Chain-Fluesse (In/Out) auf der bekannten Adresse perfekt balanciert sind.

## Ranked Next Checks

- `1` Pruefung auf weitere Pionex TRC20 Deposit-Adressen | target: `Pionex API Exporte (Deposit History) 2021-2022 oder Blockchain-Screening nach Adressen, die von TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr (Binance Hotwallet) an Pionex gesendet wurden.` | reason: Da TMHP... nur 4 Deposits abdeckt, ist es wahrscheinlich, dass Pionex mehrere TRC20-Adressen fuer Deposits nutzte. Der Gap von ~1643 USDT koennte auf einer zweiten, unentdeckten Adresse liegen.
- `2` Vergleich mit Pionex 'Deposit/Withdrawal' CSV-Exporten | target: `Rohdaten-Exporte von Pionex fuer den Zeitraum 01.01.2022 bis 01.03.2022.` | reason: Die API-Daten koennen unvollstaendig sein. Ein manueller Export zeigt alle von Pionex generierten Adressen und Transaktionen.
- `3` Pruefung von 'Internal Transfers' innerhalb von Pionex | target: `Pionex Support-Anfrage oder interne Logs (falls verfuegbar).` | reason: Manche Plattformen verbuchen Deposits erst, wenn sie auf ein Haupt-Wallet gebuehrt wurden. Wenn die 'Opening Balance' vor der ersten gebuehrten Transaktion gesetzt wurde, koennte dies eine Diskrepanz erzeugen.

## Candidate Pionex Addresses

- `TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr` confidence `low`: Dies ist die Absenderadresse (Binance Hotwallet), keine Pionex-Adresse. Pionex-Adressen sind die Empfänger.
- `TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU` confidence `medium`: Dies ist die bekannte Sweep-Adresse. Es ist moeglich, dass es weitere Sweep-Adressen gibt, die nicht in den Daten enthalten sind, aber der Fokus sollte auf Deposit-Adressen liegen.

## Confidence

medium
