# Zero-Cost Medium Review

Stand: 2026-05-10

## Lauf

- Status: `success`
- Modell: `qwen3.6-35b-a3b-iq4xs`
- Endpoint: `http://192.168.2.203:11435`
- Reasoning Content vorhanden: `False`

## Deterministische Issues

### 2022 USDT

- Job: `c94a113e-1423-4ac1-8a72-9a12cd1156b1`
- Zeilen: `3`
- Erloes: `1377.093968129900714000000000 EUR`
- Source Counter: `{'pionex': 2, 'binance': 1}`
- Lot Source Counter: `{'empty_lot': 3}`
- Duplicate Signal: `2969` Gruppen, `3366` Ueberhang

- Line `106` qty `68.97554536620000000000` proceeds `60.9378250646767140000000000`: source `binance` `trade` `out` tx `binance-txhist-jan2022:20220105T173646:2016:Transaction Spend:USDT`; lot `` `` `` tx ``
- Line `136` qty `168.46032035000000000000` proceeds `148.4893493725075000000000000`: source `pionex` `trade` `out` tx `s_10:67:out:USDT`; lot `` `` `` tx ``
- Line `149` qty `1324.71132077000000000000` proceeds `1167.666793692716500000000000`: source `pionex` `trade` `out` tx `s_11:68:out:USDT`; lot `` `` `` tx ``

### 2024 IOT

- Job: `42cf80fc-2d66-4e9e-af73-bcaf563e5dc3`
- Zeilen: `11`
- Erloes: `1692.238950693946251124012164 EUR`
- Source Counter: `{'solana_rpc': 11}`
- Lot Source Counter: `{'empty_lot': 9, 'solana_rpc': 2}`
- Duplicate Signal: `68` Gruppen, `68` Ueberhang

- Line `7` qty `313825.029803` proceeds `621.5158229537168233334372205`: source `solana_rpc` `swap_out_aggregated` `out` tx `5AvcbkMazFT2wT7Sjic1tX539miJAP2isCAUcDHxYSuZq1D53QPGZYbu9AonuBNxrZ29nAderiDZuS3q4MJjtm5x`; lot `` `` `` tx ``
- Line `19` qty `15655.712506` proceeds `30.44623599191200975238305271`: source `solana_rpc` `swap_out_aggregated` `out` tx `8sA2dex7fEtHwYDe9PrMyXQwXGf1tSqmkcgLLF8JqTRB8tVNZ2Ujwtu3EQ5rBVLSuRJinhti1exkM3aUMSMYuVd`; lot `` `` `` tx ``
- Line `132` qty `35281.225763` proceeds `52.44400958430312292955434846`: source `solana_rpc` `swap_out_aggregated` `out` tx `5Tsb4AfVp8hshnFynUbrJwYBkXCTpS7kt7vHw3mAMN2YPkGsZvUpV6k3igMWtdDQbA2nPwz51t3mWUxsy325CB7n`; lot `` `` `` tx ``
- Line `143` qty `45887.216151` proceeds `62.95478085647984146399999998`: source `solana_rpc` `swap_out_aggregated` `out` tx `Uunh3ymvdtTsgqYUDxvztmcQdRZAAsD7S5nTr9LWAtMH1DPxsNbvNHPVRKDBiPdboFkA4dCXYM1Jr4ZaJk21m69`; lot `` `` `` tx ``
- Line `209` qty `29340.006228` proceeds `22.72849512663788331504580808`: source `solana_rpc` `swap_out_aggregated` `out` tx `43Kb4Xmrfws769oo6G17gp6w4Fk2VZkQ85cRrL75Jg6na9EyfhvJZjn21XdoZgaxHEfg1sPrULTxKtHNnmoEfCeS`; lot `solana_rpc` `swap_in_aggregated` `in` tx `2QWZM69Wj5pkTxzV2tCMRjsj17j7X1nWahuVyc8q9AnPBPcvmUsRuitJkCtTfwrQ52dBLexH5BYJPv6kqL6zFMGs`

### 2024 JUP

- Job: `42cf80fc-2d66-4e9e-af73-bcaf563e5dc3`
- Zeilen: `5`
- Erloes: `1941.789576577914067123048912 EUR`
- Source Counter: `{'solana_rpc': 5}`
- Lot Source Counter: `{'solana_rpc': 5}`
- Duplicate Signal: `345` Gruppen, `725` Ueberhang

- Line `230` qty `502.097492` proceeds `393.9187275987702960890839484`: source `solana_rpc` `swap_out_aggregated` `out` tx `5g3EfxaSJqT6BDhYeUsu9CMWHkFNojFCNNBSwXYBMxEDWtG7TcKZCpSrQRzaPEqmFnAijLaXZgEQS2d9oy5gWHFV`; lot `solana_rpc` `swap_in_aggregated` `in` tx `3DhM33sbb8EHPNJv7MMFwRpkQt4AEmgRWbdYSWhkHQKuHL4btyeSa2ccJd1pFwBZGPWJY7i2xp3ktBmxLNJEGAw8`
- Line `231` qty `185.000000` proceeds `152.8008463341682998400000000`: source `solana_rpc` `swap_out_aggregated` `out` tx `iJqr9pZLv1uAfP9U15LMwkvVC4cbAvMktUPbsV9prBmtH9uT35GQKmdNC3WJcJxvTr1fzJYHgqBMHXDT13yhxUp`; lot `solana_rpc` `swap_in_aggregated` `in` tx `3DhM33sbb8EHPNJv7MMFwRpkQt4AEmgRWbdYSWhkHQKuHL4btyeSa2ccJd1pFwBZGPWJY7i2xp3ktBmxLNJEGAw8`
- Line `324` qty `247.408121` proceeds `264.5239795042111174713478420`: source `solana_rpc` `swap_out_aggregated` `out` tx `5duFfJZsX7bxDHUZCpWAgciVAgLEQSvnFTkMWfRRYpEdxnGarvwaB4bBdZ87tkLQdPRvnJRmFgfvD69Uhfsc1aLe`; lot `solana_rpc` `swap_in_aggregated` `in` tx `5FJ2fWUBtDXQDY97JMSQWovAhrWTRzYh5naSshS651S3jTwBxEg3589ukiw7xLHBy3psUHixqtPAYLk4hBpe2ztU`
- Line `329` qty `55.78179` proceeds `59.64081136474986069859871874`: source `solana_rpc` `swap_out_aggregated` `out` tx `5duFfJZsX7bxDHUZCpWAgciVAgLEQSvnFTkMWfRRYpEdxnGarvwaB4bBdZ87tkLQdPRvnJRmFgfvD69Uhfsc1aLe`; lot `solana_rpc` `swap_in_aggregated` `in` tx `3gSdRJiFcupJwPTJnNoQB88nxHErimLxpvA1aiKhSovd8jC4NsmxiyUrt6YP5hKxzbeWbUSWMMxH5FUZdL5Z6efj`
- Line `543` qty `921.817380` proceeds `1070.905211776014493024018403`: source `solana_rpc` `swap_out_aggregated` `out` tx `3fC4SsqEzJAmVYgiJ1WKRx7Qqx6H94C68YKmx2GFzPXQscbiGSGBec6TUXa66Fo8V7bT9zDkgt11VMnHNWG762MF`; lot `solana_rpc` `swap_in_aggregated` `in` tx `32kFnCm62pUZhS8MXxHcbkmXUH9oiiAfzpL8HXXBAvqnHPLLp8TARwCxcHMCAD79GooSBPW3jpSQQdvf74oYMuPi`

### 2024 USDC

- Job: `42cf80fc-2d66-4e9e-af73-bcaf563e5dc3`
- Zeilen: `6`
- Erloes: `2843.308609417790648892983983 EUR`
- Source Counter: `{'solana_rpc': 5, 'bitget_tax_api': 1}`
- Lot Source Counter: `{'empty_lot': 6}`
- Duplicate Signal: `12` Gruppen, `12` Ueberhang

- Line `150` qty `1303.122096` proceeds `1212.320243350720000000000000`: source `solana_rpc` `swap_out_aggregated` `out` tx `YsJsUxnpGV3RWLe4iegQ3NAKFpFXujfAM9BNMs54otXdJn1L544jzSvjF9srhvz1mkZ6eWWUoGXynjW6qeDA5S2`; lot `` `` `` tx ``
- Line `478` qty `198.840372` proceeds `188.8148318420342132591490761`: source `solana_rpc` `swap_out_aggregated` `out` tx `2xqB5wHqSYi4BLZ2fQNVFQeMXWCFMJXQHNYZvoYbLXayZh9A3ziv8zoRjSzse8112PV3GHVEiwTQGiqYiEdPsbDT`; lot `` `` `` tx ``
- Line `486` qty `261.973080` proceeds `248.03349241320`: source `bitget_tax_api` `trade` `out` tx `1247108196190380043`; lot `` `` `` tx ``
- Line `488` qty `148.066735` proceeds `140.1879908346500000000000000`: source `solana_rpc` `swap_out_aggregated` `out` tx `5TYVduwDC9aSasNRuigNNwd1xLJAVoXPauMziEDYe2rMENtwnqyvq8wrM6LXvUz4gZyqKcZgb2SUEN1qeJFbaiA`; lot `` `` `` tx ``
- Line `520` qty `838.816347` proceeds `795.8436988028420373883764716`: source `solana_rpc` `swap_out_aggregated` `out` tx `2Wgf1DwaVKdHy8JxQZWDhhdnGZCVWtZpVvWRKH6JhiMB3dzLnmoXareFvsYU3kKUTNnKGHaek9BWPt19Qt9grBFZ`; lot `` `` `` tx ``

## Lokale KI-Auswertung

- `2022` `USDT` `0.95`: missing_acquisition_chain | Next: Prüfen, ob USDT-Käufe (Deposits oder Trades 'in') in den Quelldaten (Binance/Pionex) für 2021/2022 fehlen. Manuellen Import oder Korrektur der Rohdaten erforderlich. | Auto-Fix: `False`
- `2024` `IOT` `0.9`: missing_acquisition_chain | Next: Überprüfung der Solana-Transaktionshistorie auf vorherige 'swap_in' oder Deposit-Events für IOT. Falls vorhanden, manuelle Zuordnung oder Nachimport. | Auto-Fix: `False`
- `2024` `JUP` `0.85`: duplicate_or_reference_overlap | Next: Manuelle Prüfung, ob die 'interest' Events als separate Einkünfte oder als Teil des Lots zu behandeln sind. Sicherstellen, dass die Aufteilung des Lots (Splitting) korrekt dokumentiert ist und keine doppelten Verkäufe vorliegen. | Auto-Fix: `False`
- `2024` `USDC` `0.9`: missing_acquisition_chain | Next: Prüfen, ob USDC-Käufe (z.B. von anderen Chains oder Exchanges) importiert wurden. Falls nicht, manuelle Eingabe der Anschaffungskosten oder Nachweis der Herkunft (z.B. als Geschenk/Income zu versteuern, wenn keine Kostenbasis existiert). | Auto-Fix: `False`

## Hinweis

- Die lokale KI ist nur Zweitpruefung. Verbindlich bleiben Rohdaten, deterministische Ableitungen und manuelle Review-Entscheidungen.
