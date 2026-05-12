# Binance BTC Source Chain Candidate Audit - 2026-05-09

## Ergebnis

- Kandidaten: `9`
- Status: `{'blocked_by_counterasset_undercoverage': 7, 'safe_candidate': 2}`
- Importierbarer positiver BTC-Delta: `0.00263736 BTC`
- Blockierter positiver BTC-Delta: `0.01815838 BTC`

## Bewertung

- 1 BTC-Quelle(n) sind aus aktivem Bestand am jeweiligen Zeitpunkt plausibel importierbar.
- 7 BTC-Quelle(n) sind als Referenz belegt, wuerden aber neue Gegenasset-Unterdeckungen erzeugen.
- Damit darf die BTC-Luecke nicht pauschal mit allen Blockpit-Referenzen geschlossen werden.
- Der erste sichere Schritt ist ein enges Importpaket nur fuer die plausiblen USDT/VET/WIN/DOGE/BTC-Quellen, sofern die Gegenassets am Zeitpunkt gedeckt bleiben.

## Kandidaten

- `2021-03-29T16:48:07+00:00` tx `47394524243BTC` `0.00013263 BNB` <- `0.00000063 BTC` fee `0.00000265 BNB` net BTC `-0.00000063` status `safe_candidate` recommendation `reference_only`
- `2022-12-02T18:16:38+00:00` tx `59571809` `0.0072292 BTC` <- `1240 DOGE` fee `0.00000723 BTC` net BTC `0.00722197` status `blocked_by_counterasset_undercoverage` recommendation `do_not_import_until_counterasset_source_is_found_or_review_adjustment_is_approved`
  - blockiert `DOGE`: aktiv `22.25150592`, benoetigt `1240`, Luecke `1217.74849408`
- `2022-12-17T08:38:05+00:00` tx `59817964` `906 DOGE` <- `0.00420384 BTC` fee `0.906 DOGE` net BTC `-0.00420384` status `blocked_by_counterasset_undercoverage` recommendation `do_not_import_until_counterasset_source_is_found_or_review_adjustment_is_approved`
  - blockiert `BTC`: aktiv `0.00003594`, benoetigt `0.00420384`, Luecke `0.0041679`
- `2022-12-17T08:38:05+00:00` tx `59817965` `650 DOGE` <- `0.003016 BTC` fee `0.65 DOGE` net BTC `-0.003016` status `blocked_by_counterasset_undercoverage` recommendation `do_not_import_until_counterasset_source_is_found_or_review_adjustment_is_approved`
  - blockiert `BTC`: aktiv `0.00003594`, benoetigt `0.003016`, Luecke `0.00298006`
- `2023-03-17T08:26:35+00:00` tx `953994324` `0.01896 BTC` <- `495.8783232 BUSD` fee `0 ` net BTC `0.01896` status `blocked_by_counterasset_undercoverage` recommendation `do_not_import_until_counterasset_source_is_found_or_review_adjustment_is_approved`
  - blockiert `BUSD`: aktiv `0.0021122352`, benoetigt `495.8783232`, Luecke `495.8762109648`
- `2023-05-02T04:10:12+00:00` tx `3102730135` `0.00264 BTC` <- `73.9885872 USDT` fee `0.00000264 BTC` net BTC `0.00263736` status `safe_candidate` recommendation `can_import_as_narrow_btc_source_reconstruction`
- `2023-05-02T04:12:17+00:00` tx `1445383084970347602` `0.00007565 BTC` <- `100.01639287 VET` fee `0 ` net BTC `0.00007565` status `blocked_by_counterasset_undercoverage` recommendation `do_not_import_until_counterasset_source_is_found_or_review_adjustment_is_approved`
  - blockiert `VET`: aktiv `100`, benoetigt `100.01639287`, Luecke `0.01639287`
- `2023-05-02T04:12:36+00:00` tx `1445383248178874807` `0.00004088 BTC` <- `14156.61280211 WIN` fee `0 ` net BTC `0.00004088` status `blocked_by_counterasset_undercoverage` recommendation `do_not_import_until_counterasset_source_is_found_or_review_adjustment_is_approved`
  - blockiert `WIN`: aktiv `14143`, benoetigt `14156.61280211`, Luecke `13.61280211`
- `2023-05-04T04:24:52+00:00` tx `69593332` `1.2 SOL` <- `0.00092028 BTC` fee `0.00006138 BNB` net BTC `-0.00092028` status `blocked_by_counterasset_undercoverage` recommendation `do_not_import_until_counterasset_source_is_found_or_review_adjustment_is_approved`
  - blockiert `BTC`: aktiv `0.00028285`, benoetigt `0.00092028`, Luecke `0.00063743`

## Konsequenz

- Import nur fuer Kandidaten mit `can_import_as_narrow_btc_source_reconstruction`; blockierte Kandidaten bleiben Nachweis/Recherchepunkt.
- BUSD bleibt separat zu klaeren, weil der grosse `BUSD -> BTC`-Trade ohne BUSD-Quelle die Bilanz verfaelschen wuerde.
