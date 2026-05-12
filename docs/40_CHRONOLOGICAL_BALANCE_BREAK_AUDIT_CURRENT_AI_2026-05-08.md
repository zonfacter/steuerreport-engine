# Chronologische Bestandsbruch-Analyse

Generiert: `2026-05-08T14:26:37.334858+00:00`
JSON: `var/chronological_balance_break_audit_current_ai_2026-05-08.json`

## Überblick

- Bewegungen: `39229`
- Assets: `60`
- Assets mit negativem Endbestand: `6`

## Asset-Befunde

### USDT

- Endbestand Modell: `-4499.90655736203488750000`
- Events: `2682`
- Erster Negativbestand: `2022-01-05T11:40:01+00:00` nach `1b4d889af78c6943b724fe3b6198b063533a04278511baf51a6f7207772c73b7`
- Auslösend: `pionex` / `trade` / `out` / `-346.92882000000000000000`
- Schlimmster Stand: `-4838.40737822047388750000` am `2024-12-04T18:30:59+00:00`

Jahres-Netto:
- `2021`: `197.26350632000000000000`
- `2022`: `-3036.59574436536000000000`
- `2023`: `-14.27771074170000000000`
- `2024`: `-1984.50516555597988750000`
- `2025`: `338.208556981005`

Top Quellen-Netto:
- `binance_api` / `trade` / `sell_quote`: `75304.76031000`
- `binance_api` / `trade` / `buy_quote`: `-70220.53397000`
- `binance` / `trade` / `out`: `-46892.72026327`
- `binance` / `trade` / `in`: `45726.83467400`
- `solana_rpc` / `token_transfer` / `out`: `-34733.843023`
- `solana_rpc` / `swap_in_aggregated` / `in`: `31653.240947`
- `pionex` / `trade` / `out`: `-25056.73396394677700000000`
- `solana_rpc` / `token_transfer` / `in`: `23866.833602`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-22774.239788`
- `pionex` / `trade` / `in`: `21942.68846261340000000000`

### MOBILE

- Endbestand Modell: `-421.837749`
- Events: `40`
- Erster Negativbestand: `2025-12-20T12:13:50+00:00` nach `8d7da30c8eaf7ebcd19f17a994b8f6bf815a71440e9e0b42f5a8a2adef48a392`
- Auslösend: `blockpit` / `trade` / `out` / `-421.837749`
- Schlimmster Stand: `-421.837749` am `2025-12-20T12:13:50+00:00`

Jahres-Netto:
- `2023`: `0.000000`
- `2024`: `421.837749`
- `2025`: `-843.675498`

Top Quellen-Netto:
- `solana_rpc` / `swap_out_aggregated` / `out`: `-449359.197079`
- `solana_rpc` / `swap_in_aggregated` / `in`: `408584.933292`
- `solana_rpc` / `token_transfer` / `in`: `40774.263787`
- `blockpit` / `trade` / `out`: `-421.837749`

### VTHO

- Endbestand Modell: `-42.39387934`
- Events: `1`
- Erster Negativbestand: `2023-05-02T04:13:23+00:00` nach `61f4964558fe99fefaf53cbb118095ae2953e13528b8a34ef8a167ba3c42ef8d`
- Auslösend: `binance_api` / `dust_convert_out` / `out` / `-42.39387934`
- Schlimmster Stand: `-42.39387934` am `2023-05-02T04:13:23+00:00`

Jahres-Netto:
- `2023`: `-42.39387934`

Top Quellen-Netto:
- `binance_api` / `dust_convert_out` / `out`: `-42.39387934`

### BNSOL

- Endbestand Modell: `-22.323042230`
- Events: `16`
- Erster Negativbestand: `2025-03-23T13:46:29.121000+00:00` nach `bd7d775cd64759b5d390a276a8a8474b4597ef9cba554a121650fbf65de0fb34`
- Auslösend: `binance_api` / `convert_out` / `out` / `-22.32305193`
- Schlimmster Stand: `-22.323042620` am `2025-03-23T13:46:29.121000+00:00`

Jahres-Netto:
- `2025`: `-22.323042230`

Top Quellen-Netto:
- `binance_api` / `convert_out` / `out`: `-22.32305193`
- `blockpit` / `interest` / `in`: `0.000009700`

### VSR

- Endbestand Modell: `-2`
- Events: `2`
- Erster Negativbestand: `2025-12-20T12:13:37+00:00` nach `8a9a7079da0bbde3394bd3c6057e6159dd487fbfae033d075441ceaa1681ce44`
- Auslösend: `blockpit` / `withdrawal` / `out` / `-1`
- Schlimmster Stand: `-2` am `2025-12-26T21:07:02+00:00`

Jahres-Netto:
- `2025`: `-2`

Top Quellen-Netto:
- `blockpit` / `withdrawal` / `out`: `-2`

### BUSD

- Endbestand Modell: `-0.55168701480000000000`
- Events: `7`
- Erster Negativbestand: `2023-01-14T08:14:03+00:00` nach `266f6a64a54bf3d60213ca7cf8cd651995d597291edb5487b90ff8dc6f374543`
- Auslösend: `pionex` / `fee` / `out` / `-0.12348780`
- Schlimmster Stand: `-0.55168701480000000000` am `2023-05-02T04:13:23+00:00`

Jahres-Netto:
- `2022`: `35.20000000000E-9`
- `2023`: `-0.55168705000000000000`

Top Quellen-Netto:
- `pionex` / `trade` / `in`: `406.43612130000000000000`
- `pionex` / `trade` / `out`: `-406.23079100480000000000`
- `binance_api` / `dust_convert_out` / `out`: `-0.55379925`
- `pionex` / `fee` / `out`: `-0.20321806`

### IOT

- Endbestand Modell: `1595933867625.7516100`
- Events: `2761`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `3421905036` am `2023-04-20T00:00:00+00:00`

Jahres-Netto:
- `2023`: `683909500931.8233920`
- `2024`: `845402447071.928218`
- `2025`: `66621934036.103550`
- `2026`: `-14414.10355`

Top Quellen-Netto:
- `heliumgeek` / `mining_reward` / `in`: `1595933017592`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-11393200.321693`
- `solana_rpc` / `swap_in_aggregated` / `in`: `8779057.673155`
- `solana_rpc` / `token_transfer` / `in`: `4725849.956961`
- `solana_rpc` / `token_transfer` / `out`: `-2111707.308423`
- `heliumtracker` / `mining_reward` / `in`: `920501.267322`
- `blockpit` / `deposit` / `in`: `159999.915543`
- `blockpit` / `trade` / `out`: `-159999.915543`
- `heliumtracker` / `mining_commission` / `out`: `-70467.5157120`

### HNT

- Endbestand Modell: `10995659935.08256765143114379`
- Events: `27558`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `0.000` am `2021-02-09T18:45:43+00:00`

Jahres-Netto:
- `2021`: `1555.18551888262277023903392`
- `2022`: `1707.02982395880837215284314`
- `2023`: `142.447037860000001399402`
- `2024`: `-12.48595600`
- `2025`: `10292884654.00812475`
- `2026`: `702771888.89801820`

Top Quellen-Netto:
- `heliumgeek` / `mining_reward` / `in`: `10995657317.12162`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-4650.43703630`
- `binance` / `trade` / `out`: `-3205.826`
- `solana_rpc` / `swap_in_aggregated` / `in`: `2980.04789129`
- `binance` / `trade` / `in`: `2917.096`
- `pionex` / `trade` / `in`: `2310.29384864000000000000`
- `pionex` / `trade` / `out`: `-2309.30500000000000000000`
- `helium_legacy_cointracking` / `legacy_transfer` / `out`: `-1570.849923437360775624`
- `binance` / `deposit` / `in`: `1424.96965874`
- `helium_legacy_cointracking` / `mining_reward` / `in`: `1298.11054127000001756127906`

### CM8VSESV7MBHAFD5UDXH84QFGXMAVWJCVVHOPB1DZIF4

- Endbestand Modell: `1000000000`
- Events: `1`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `1000000000` am `2023-07-30T06:59:36+00:00`

Jahres-Netto:
- `2023`: `1000000000`

Top Quellen-Netto:
- `solana_rpc` / `token_transfer` / `in`: `1000000000`

### 7ATGF8KQO4WJRD5ATGX7T1V2ZVVYKPJBFFNEVF1ICFV1

- Endbestand Modell: `11310642.83`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `384000` am `2024-03-30T17:25:05+00:00`

Jahres-Netto:
- `2024`: `11310642.83`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `10926642.83`
- `solana_rpc` / `token_transfer` / `in`: `384000`

### BTTC

- Endbestand Modell: `4209810.9`
- Events: `1217`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `29` am `2023-04-01T01:03:23+00:00`

Jahres-Netto:
- `2023`: `2689385.0`
- `2024`: `1520425.9`

Top Quellen-Netto:
- `binance_api` / `asset_dividend` / `in`: `4209810.9`

### 2KFZCKFXJ1US8YRQZA5VKTSXY3GPZFZVVHWJ91N8FV2J

- Endbestand Modell: `4202343.53`
- Events: `2`
- Erster Negativbestand: `` nach ``
- Auslösend: `` / `` / `` / ``
- Schlimmster Stand: `4202343.53` am `2024-03-11T22:04:53+00:00`

Jahres-Netto:
- `2024`: `4202343.53`

Top Quellen-Netto:
- `solana_rpc` / `swap_in_aggregated` / `in`: `18902619.55`
- `solana_rpc` / `swap_out_aggregated` / `out`: `-14700276.02`

## Lokale KI-Auswertung

- Modell: `qwen3-coder-30b-a3b-llamacpp`
- Endpoint: `http://192.168.2.203:11435`

### KI: USDT

```json
{
  "probable_cause": "Negative balance triggered by a large outgoing transaction (346.93 USDT) on 2022-01-05, likely due to a trade or withdrawal event without sufficient prior balance, possibly indicating a data gap or unrecorded income prior to this point.",
  "confidence": "medium",
  "evidence": [
    "First negative balance occurs at 2022-01-05T11:40:01Z with a trade event (pionex) resulting in a delta of -346.93 USDT.",
    "Balance before the event was 271.64 USDT, which is insufficient to cover the outgoing transaction.",
    "No prior recorded income or balance increase in the pionex context before this event.",
    "The balance drops to -75.29 USDT after the event, indicating a clear deficit.",
    "Subsequent events show continued outflows, suggesting no recovery or correction."
  ],
  "next_checks": [
    "Verify if there are any missing income or deposit events in pionex before 2022-01-05.",
    "Check for any external income sources (e.g., bank transfers, other exchanges) that may not be captured in pionex.",
    "Confirm if the 346.93 USDT transaction was a trade or withdrawal and if it was properly recorded in tax reporting."
  ],
  "safe_automatic_actions": [
    "Flag the event for manual review due to insufficient balance prior to transaction.",
    "Do not automatically delete or adjust the event without primary evidence of error."
  ],
  "needs_user_data": [
    "Confirmation of income or deposits in pionex before 2022-01-05.",
    "Details on the nature of the 346.93 USDT transaction (trade, withdrawal, etc.).",
    "Any external income or transfers that may not be reflected in the system."
  ]
}
```

### KI: MOBILE

```json
{
  "probable_cause": "Der negative Bestand entstand durch einen Trade-Verkauf von 421.837749 MOBILE-Token am 20.12.2025, der den Bestand auf -421.837749 setzte. Dieser Verkauf war der erste negative Bestand und entspricht einem Ausgangsereignis ohne vorherige Eingänge im betrachteten Zeitraum.",
  "confidence": "high",
  "evidence": [
    "Erster negativer Bestand tritt am 20.12.2025 auf (Trade-Event)",
    "Balance vor dem Trade: 0.000000",
    "Trade-Event: Verkauf von 421.837749 MOBILE-Token",
    "Keine vorherigen Eingänge im betrachteten Zeitraum"
  ],
  "next_checks": [
    "Prüfung der Quelle 'blockpit' auf mögliche Vorhandensein von Eingangsereignissen vor dem ersten Trade",
    "Analyse der Transaktionen des 'solana_rpc'-Sources vor dem Trade-Ereignis",
    "Überprüfung, ob der Trade auf eine vorherige Eingabe von MOBILE-Token basiert (z. B. via Swap-In)"
  ],
  "safe_automatic_actions": [
    "Keine automatischen Löschungen ohne zusätzliche Belege",
    "Keine automatische Zuordnung zu Steuereingängen ohne Nachweis"
  ],
  "needs_user_data": [
    "Nachweis über vorherige Eingänge von MOBILE-Token (z. B. via Swap-In oder Transfer)",
    "Informationen zur Herkunft des Trades (z. B. ob es sich um einen Handel mit einem Dritten handelte)"
  ]
}
```

### KI: VTHO

```json
{
  "probable_cause": "Der negative Bestand entstand durch eine 'dust_convert_out'-Transaktion auf Binance, bei der 42,39387934 VTHO in ein Dust-Convert-Ereignis umgewandelt wurden. Dies ist eine standardisierte Handlung bei Binance, bei der ungenutzte oder sehr kleine Token-Beträge in andere Assets umgewandelt werden, oft zu einem sehr geringen Wert.",
  "confidence": "high",
  "evidence": [
    "Ereignis ist eindeutig als 'dust_convert_out' klassifiziert.",
    "Zeitstempel und Transaktions-ID sind konsistent.",
    "Der Betrag entspricht exakt dem negativen Bestand.",
    "Keine weiteren Ereignisse vor diesem Datum im Zeitraum."
  ],
  "next_checks": [
    "Prüfung, ob VTHO vorherige Einnahmen hatte (z. B. via 'dust_convert_in').",
    "Überprüfung, ob der Account vor diesem Datum VTHO besessen hat."
  ],
  "safe_automatic_actions": [
    "Keine automatische Löschung notwendig, da es sich um eine legitime Binance-Operation handelt.",
    "Keine automatische Zuordnung zu Steuererklärung nötig, solange keine Einnahmen vorliegen."
  ],
  "needs_user_data": [
    "Bestätigung, ob der Account vor dem 02.05.2023 VTHO besessen hat.",
    "Nachweis, ob es vorherige Einnahmen oder Umrechnungen gab."
  ]
}
```

### KI: BNSOL

```json
{
  "probable_cause": "Der negative Bestand entstand durch eine Convert-Out-Transaktion auf Binance, bei der 22,32305193 BNSOL aus dem Konto abgehoben wurden. Vor der Transaktion lag der Bestand bei lediglich 0,000009310 BNSOL, was auf eine vorherige Ertragsgutschrift (Interest) hinweist. Die nachfolgende Ertragsgutschrift von 390E-9 BNSOL am gleichen Tag deckt den Verlust nicht vollständig.",
  "confidence": "0.85",
  "evidence": [
    "Convert-Out-Transaktion vom 23.03.2025 mit 22,32305193 BNSOL",
    "Vorheriger Bestand von 0,000009310 BNSOL durch Interest-Gutschriften",
    "Nachfolgende Interest-Gutschrift von 390E-9 BNSOL am gleichen Tag",
    "Keine weiteren Eingehenden Transaktionen vor der Convert-Out-Transaktion"
  ],
  "next_checks": [
    "Prüfung der Convert-Out-Transaktion auf mögliche Fehlinformationen oder Betrugsversuche",
    "Überprüfung der BNSOL-Verfügbarkeit vor der Convert-Out-Transaktion",
    "Analyse der BNSOL-Preisentwicklung in der Zeit vor der Transaktion"
  ],
  "safe_automatic_actions": [
    "Keine automatischen Löschungen ohne zusätzliche Prüfung",
    "Markierung als verdächtig für manuelle Überprüfung"
  ],
  "needs_user_data": [
    "Bestätigung der Convert-Out-Transaktion",
    "Informationen zur Herkunft der BNSOL vor der Convert-Out-Transaktion",
    "Nachweis der Berechtigung zur Ausführung der Transaktion"
  ]
}
```

### KI: VSR

```json
{
  "probable_cause": "Der negative Bestand entstand durch zwei aufeinanderfolgende Auszahlungen (Withdrawals) von VSR-Token in den Jahren 2025, wobei der erste Withdrawal am 20.12.2025 und der zweite am 26.12.2025 erfolgte. Beide Ereignisse stammen aus derselben Quelle (blockpit) und sind als 'Withdrawal' gekennzeichnet.",
  "confidence": "high",
  "evidence": [
    "Erster Withdrawal am 20.12.2025: balance_before=0, delta=-1, balance_after=-1",
    "Zweiter Withdrawal am 26.12.2025: balance_before=-1, delta=-1, balance_after=-2",
    "Beide Ereignisse stammen von blockpit und sind als Solana-Transaktionen gekennzeichnet",
    "Keine anderen Ereignisse im Zeitraum, die den Bestand positiv beeinflussten"
  ],
  "next_checks": [
    "Prüfung der zugrundeliegenden Transaktionen (tx_id) auf blockpit für weitere Details",
    "Überprüfung, ob die Transaktionen mit einem bekannten Konto oder einer bekannten Adresse verknüpft sind",
    "Analyse möglicher Einnahmen in anderen Assets oder Quellen innerhalb des gleichen Zeitraums"
  ],
  "safe_automatic_actions": [
    "Keine automatischen Löschungen oder Änderungen des Bestands",
    "Keine automatische Zuordnung zu Steuerdaten ohne zusätzliche Prüfung"
  ],
  "needs_user_data": [
    "Bestätigung, ob die beiden Withdrawals von demselben Konto oder derselben Adresse stammen",
    "Informationen zur Herkunft der VSR-Token (z. B. ob sie aus einem Swap, Staking oder einer anderen Quelle stammen)",
    "Weitere Transaktionen im gleichen Zeitraum, um mögliche Einnahmen zu identifizieren"
  ]
}
```

### KI: BUSD

```json
{
  "probable_cause": "Ein negativer Bestand entstand durch eine Kombination aus einer Gebühr auf pionex (2023-01-14) und einem Trade-Verlust auf pionex (2023-01-16), gefolgt von einem Dust-Convert-Out auf Binance (2023-05-02), wodurch der Bestand auf -0.55168701480000000000 BUSD fiel.",
  "confidence": "high",
  "evidence": [
    "Erste negative Balance durch Fee auf pionex am 14.01.2023 (0.12348780 BUSD)",
    "Trade-Verlust auf pionex am 16.01.2023 (246.85000000000000000000 BUSD)",
    "Dust-Convert-Out auf Binance am 02.05.2023 (0.55379925 BUSD) führte zu finaler negativer Balance",
    "Keine weiteren Einzahlungen oder Erhöhungen des Bestands nach dem ersten negativen Ereignis"
  ],
  "next_checks": [
    "Prüfung der Transaktionshistorie auf pionex für den Zeitraum 2023-01-14 bis 2023-01-16",
    "Überprüfung der Dust-Convert-Out-Transaktion auf Binance am 02.05.2023",
    "Analyse der Quellen der Trade-Transaktionen (Ein- und Ausgänge) auf pionex"
  ],
  "safe_automatic_actions": [
    "Keine automatischen Löschungen ohne zusätzliche Bestätigung",
    "Vermerk als potenzielle Steuerfallen für 2023"
  ],
  "needs_user_data": [
    "Bestätigung der Herkunft der Trade-Transaktionen",
    "Informationen zur Steuerbehandlung der Dust-Convert-Out-Transaktion",
    "Nachweis der Einzahlungen vor dem ersten negativen Bestand"
  ]
}
```
