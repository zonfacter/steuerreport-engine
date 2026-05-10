# Binance 2021 Account Statement Income Valuation Audit - 2026-05-09

## Zweck

Pruefung, ob die isolierten Binance-Account-Statement-Ertragszeilen vor einem steuerwirksamen Import bewertbar sind.

## Coverage

- Zeilen: `317`
- Bewertet: `311`
- Unbewertet: `6`
- Fehlende Asset-USD-Preise: `6`
- Fehlende USD/EUR-FX: `0`
- Bewerteter Gesamtwert USD: `0.23522767351087264937646165`
- Bewerteter Gesamtwert EUR: `0.1975450171228697628526430079`

## Asset Summary

- `ADA`: rows=276, priced=276, unpriced=0, qty=0.06117724, value_eur=0.08253755075581658713029944198
- `DOGE`: rows=28, priced=28, unpriced=0, qty=0.85150592, value_eur=0.1143417021630531757223435661
- `NFT`: rows=6, priced=0, unpriced=6, qty=23302.344666, value_eur=0
  - Missing dates sample: `['2021-06-19', '2021-07-23', '2021-08-26', '2021-10-11', '2021-10-28', '2021-12-06']`
- `USDT`: rows=7, priced=7, unpriced=0, qty=0.00080654, value_eur=0.000665764204

## Bewertung

- Valuation audit only checks rows prepared by the reviewed Binance 2021 income importer.
- USDT is valued as a USD stable asset and then converted with cached USD/EUR FX.
- Rows for these assets are not fully valued yet: NFT.
- The Binance symbol NFT likely needs explicit APENFT/NFT price mapping or manual evidence before import with EUR value.

## Import-Entscheidung

ADA, DOGE und USDT sind als bewertbare Kleinertraege technisch importfaehig; aktueller Importstatus siehe Report 101.
NFT/APENFT bleibt blockiert, bis Symbolmapping oder Preisbeleg geklaert ist.
