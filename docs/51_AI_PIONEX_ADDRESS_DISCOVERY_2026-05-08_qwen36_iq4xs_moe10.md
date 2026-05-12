# AI Pionex Address Discovery - 2026-05-08

## Scope

Local llama.cpp review for the hypothesis that another Pionex deposit address or missing platform export explains the early 2022 Pionex-USDT gap.

## Inputs

- Candidate JSON: `/workspace/steuerreport/var/pionex_address_discovery_candidates_2026-05-08.json`
- Result JSON: `/workspace/steuerreport/var/ai_pionex_address_discovery_2026-05-08_qwen36_iq4xs_moe10.json`
- Known Pionex TRON deposit address: `TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ`
- Known Pionex sweep address: `TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU`
- Relevant transfer-like events scanned: `5493`
- Address groups sent to AI: `7`
- Focused events sent to AI: `260`

## LLM Status

- status: `success`
- model: `qwen3.6-35b-a3b-iq4xs`
- endpoint: `http://192.168.2.203:11436`
- duration_seconds: `185.576`

## Summary

Die Analyse der bekannten TRON-Adresse (TMHP...) zeigt eine perfekte 1:1-Abdeckung der aus Binance-API extrahierten Auszahlungen durch Pionex-Einzahlungen. Es gibt keine Lücke auf der Blockchain-Ebene für diese spezifische Adresse. Die berichtete 'Unterdeckung' von ~1643 USDT resultiert wahrscheinlich aus einer Diskrepanz zwischen der API-Export-Datenbank (Binance) und den internen Pionex-Bücher (oder einem anderen Export), da die On-Chain-Daten für den bekannten Pfad balanciert sind. Eine weitere Pionex-Einzahlungsadresse oder ein fehlender Export für diesen spezifischen Zeitraum ist unwahrscheinlich, da die Zeitstempel der Binance-Auszahlungen mit den Pionex-Einzahlungen exakt korrelieren. Die Lücke deutet eher auf einen Datenintegrationsfehler in der Quelldatenbank hin oder betrifft einen anderen, nicht identifizierten Pionex-Konto-Bereich, der nicht über diese TRON-Adresse abgewickelt wurde.

## Confirmed Facts

- Die TRON-Adresse TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ hat genau 4 Einzahlungen und 4 Auszahlungen (Sweeps) im Zeitraum 2021-12-25 bis 2022-02-25.
- Die Summe der Einzahlungen (3125.902987 USDT) entspricht exakt der Summe der Auszahlungen (3125.902987 USDT).
- Alle 4 Einzahlungen stammen von TAzsQ9Gx8eqFNFSKbeXrbi45CuVPHzA8wr und TNXoiAJ3dct8Fjg4M9fkLFh9S2v9TXc32G.
- Alle 4 Auszahlungen gehen an TWDchZBmYvTQBeXD4w8rRUowDv5ka8kiFU.
- Die Zeitstempel der Binance-API-Auszahlungen (Withdrawal) stimmen mit den Zeitstempeln der Pionex-Einzahlungen (Deposit) auf der Blockchain überein (Differenz < 5 Minuten).
- Es gibt keine weiteren TRC20-Transfers für TMHP82UVnvYQTqoxEP98gVch5DqbzZYfCQ vor dem 25.12.2021.

## Unlikely Explanations

- Eine weitere Pionex-Einzahlungsadresse für denselben Binance-Auszahlungspfad ist unwahrscheinlich, da die On-Chain-Transfers der bekannten Adresse vollständig abgedeckt sind.
- Ein 'fehlender Export' der Binance-API für diese spezifischen Transaktionen ist ausgeschlossen, da die API-Daten mit den On-Chain-Daten übereinstimmen.
- Die Unterdeckung ist kein technischer Verlust auf der TRON-Blockchain für diese Adresse, da das Konto balanciert ist.

## Ranked Next Checks

- `1` Prüfung auf andere Pionex-Einzahlungsadressen (TRC20) im Zeitraum Jan-Feb 2022 | target: `Pionex Deposit History Export (CSV/Excel) oder direkte Blockchain-Suche nach anderen Pionex-Adressen` | reason: Die bekannte Adresse deckt nur ~3125 USDT ab. Wenn die Unterdeckung ~1643 USDT beträgt, könnte ein Teil der Mittel über eine andere Pionex-Adresse eingegangen sein, die nicht mit den Binance-Auszahlungen korreliert ist (z.B. interne Pionex-Transfers oder andere Quellen).
- `2` Vergleich der Pionex-Export-Datei mit der Binance-API-Export-Datei auf Zeitebene | target: `Rohdaten: Pionex 'deposit-withdraw.csv' vs. Binance 'deposit-withdraw.csv'` | reason: Die 'Unterdeckung' ist eine buchhalterische Diskrepanz. Es muss geklärt werden, ob Pionex mehr Einzahlungen verbucht hat als Binance Auszahlungen getätigt hat (oder umgekehrt), was auf doppelte Zählung oder fehlende API-Einträge hindeutet.
- `3` Prüfung auf USDT-Transfers auf anderen Chains (BSC, ERC20) | target: `Pionex Support-Anfrage oder API-Filter für BSC/ERC20` | reason: Falls Pionex USDT auch über andere Netzwerke akzeptiert hat, die nicht in der TRON-Analyse enthalten sind.

## Candidate Pionex Addresses


## Confidence

high
