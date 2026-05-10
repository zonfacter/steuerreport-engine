# 25HAYB Route Value Fix - 2026-05-10

## Ergebnis

- Stand nach Fix: fuer 2024 verbleibt keine Nullkosten-Zeile fuer `25HAYB...MTDJ`.
- Betroffene Menge: `5945.66318`.
- Betroffener Erloes: `74.00590961138 EUR`.
- Neue Kostenbasis: `77.35592427099138228597657299 EUR`.
- Ergebnis der Veräußerung: `-3.35001465961138228597657294 EUR`.
- Source-Event Verkauf: `5285993c...` / Tx `5hcuqVLKfY94EnerNZDRe9pzSMjmGTKWg2iTb8xYsQZtU5Nki4XXbQE21WtLzGs8QfVoJ1vZSyMGMiBdDLxtYKBK`.
- Lot-Source Erwerb: `b9a8a16684b4c56d5e94e4fcb9ea3d5c14fe111e89eca51b50d995bb350d9a88`.

## Befund

- Die lokale KI hatte den Vorgang korrekt als Jupiter-/Solana-Route mit fehlendem Erwerbswert markiert.
- Der Erwerbs-Tx `3GbydY8fZb1Ge12wtxLohYKbjeLx2hN9Z8uf37uRZ9MrpdfbryyrAu4A4AqorGSrcuxCrcr1Unoahi3X2gk4KvsW` zeigt den Zufluss von `7445.66318` `25HAYB...MTDJ`.
- Im Roh-Tx ist ein Jupiter-Pre-/Flash-Fill-Kontext mit `100 JUP` sichtbar.
- Direkt davor liegen zwei Solana-RPC-`JUP`-Out-Transfers ueber jeweils `100 JUP`:
  - `2024-04-28T19:06:58+00:00` Tx `4ytwquixKvoJ1kytM4tsx14NQqMmkJvFiq1G6TjJoYNMasuKc3qwJa3LPbX88ymxWrqvw7Q2WkpKXCkpGd4YNpDQ`
  - `2024-04-28T19:07:49+00:00` Tx `5KyUaQhZe8v8tMtzHbV1rW46XV47ZfwhYpkDkRKP3MVG7JZKDoeNi9u2Ak5ZXRVnKkSVM5uSxbjzhmZTuyrjAnmD`
- Der zweite Out-Transfer erzeugt im Raw-Tx das Tokenkonto `22gU8W9...`, das im Erwerbs-Tx als Zielkonto fuer `25HAYB...MTDJ` auftaucht. Das ist ein starker, aber noch nicht als Transfer-Match modellierter Escrow-/Limit-Order-Hinweis.

## Bewertung

- Kein Ausschluss: Der spaetere Verkauf ist ein echter steuerlicher Vorgang.
- Kein Nullbasis-Auto-Accept: Der Erwerb wirkt wie ein Jupiter-Order-Fill, nicht wie ein Airdrop.
- Der Fix setzt keinen pauschalen Tokenpreis, sondern leitet den Wert aus dem bepreisten Gegenfluss im Raw-Route-Block ab.
- Aktueller JUP/USD-FX am `2024-04-28`: `1.011`.
- USD/EUR am `2024-04-28`: `0.93336`.
- Der aktuelle Lauf setzt fuer das gesamte Lot `7445.66318 25HAYB...MTDJ` den Raw-Route-Gegenwert an und weist fuer die verkaufte Teilmenge `5945.66318` eine Kostenbasis von `77.355924270991... EUR` aus.

## Technische Absicherung

- Implementierung: `attach_cached_usd_prices_to_swap_in_events` nutzt bei fehlendem Assetpreis den groessten bepreisten Raw-Route-Gegenfluss als `raw_priced_route_counterflow`.
- Unit-Test: `test_attach_cached_usd_prices_to_swap_in_events_uses_raw_route_counterflow`.
- Validierung: `61 passed` fuer `tests/unit/api/test_process_endpoints.py` und `tests/unit/core/test_processor_fifo.py`.

KI-Ergebnis: `var/ai_db_countercheck_2026-05-10_192346.md`
