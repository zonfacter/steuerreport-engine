# Aktivitaets-Plausibilitaetsaudit

Erstellt: `2026-05-08T10:39:29.228333+00:00`
Eventbasis: `review_actions + tax_event_overrides`
Gesamt-Events: `41623`

## Zusammenfassung

- `reference_dominated`: 838 Tage
- `many_zero_quantity_events`: 147 Tage
- `derivative_dominated`: 69 Tage
- `suspicious_reward_unit`: 42 Tage
- `failed_zero_solana_tx`: 31 Tage
- `high_daily_event_count`: 10 Tage
- `timestamp_cluster`: 10 Tage

## Top-Tage nach Aktivitaet

- `2025-02-01`: `917` Events, Derivate `908`, Referenz `548`, Primaer `369`, Failed-Solana-0 `0`, Flags: high_daily_event_count, derivative_dominated, reference_dominated, many_zero_quantity_events, timestamp_cluster, suspicious_reward_unit
- `2024-11-22`: `369` Events, Derivate `7`, Referenz `0`, Primaer `369`, Failed-Solana-0 `269`, Flags: high_daily_event_count, many_zero_quantity_events, failed_zero_solana_tx, timestamp_cluster
- `2025-02-27`: `260` Events, Derivate `259`, Referenz `155`, Primaer `105`, Failed-Solana-0 `0`, Flags: high_daily_event_count, derivative_dominated, reference_dominated, many_zero_quantity_events, timestamp_cluster
- `2025-02-24`: `260` Events, Derivate `257`, Referenz `154`, Primaer `106`, Failed-Solana-0 `0`, Flags: high_daily_event_count, derivative_dominated, reference_dominated, many_zero_quantity_events, timestamp_cluster
- `2025-06-05`: `223` Events, Derivate `223`, Referenz `223`, Primaer `0`, Failed-Solana-0 `0`, Flags: high_daily_event_count, derivative_dominated, reference_dominated
- `2025-12-26`: `190` Events, Derivate `0`, Referenz `7`, Primaer `183`, Failed-Solana-0 `0`, Flags: high_daily_event_count, timestamp_cluster
- `2025-01-29`: `180` Events, Derivate `97`, Referenz `104`, Primaer `76`, Failed-Solana-0 `0`, Flags: high_daily_event_count, reference_dominated, many_zero_quantity_events, timestamp_cluster, suspicious_reward_unit
- `2024-12-05`: `178` Events, Derivate `23`, Referenz `0`, Primaer `178`, Failed-Solana-0 `57`, Flags: high_daily_event_count, many_zero_quantity_events, failed_zero_solana_tx
- `2024-03-05`: `159` Events, Derivate `0`, Referenz `0`, Primaer `159`, Failed-Solana-0 `91`, Flags: high_daily_event_count, many_zero_quantity_events, failed_zero_solana_tx
- `2025-02-22`: `151` Events, Derivate `147`, Referenz `90`, Primaer `61`, Failed-Solana-0 `0`, Flags: high_daily_event_count, derivative_dominated, reference_dominated, many_zero_quantity_events, timestamp_cluster
- `2025-02-21`: `128` Events, Derivate `128`, Referenz `74`, Primaer `54`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated, many_zero_quantity_events, timestamp_cluster
- `2025-05-30`: `107` Events, Derivate `107`, Referenz `107`, Primaer `0`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated
- `2025-01-20`: `99` Events, Derivate `0`, Referenz `1`, Primaer `98`, Failed-Solana-0 `0`, Flags: keine
- `2025-02-02`: `96` Events, Derivate `96`, Referenz `56`, Primaer `40`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated, many_zero_quantity_events
- `2025-05-23`: `80` Events, Derivate `77`, Referenz `79`, Primaer `1`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated
- `2024-04-02`: `79` Events, Derivate `9`, Referenz `0`, Primaer `79`, Failed-Solana-0 `14`, Flags: many_zero_quantity_events, failed_zero_solana_tx
- `2022-03-01`: `79` Events, Derivate `0`, Referenz `47`, Primaer `32`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2022-02-24`: `78` Events, Derivate `0`, Referenz `49`, Primaer `29`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2022-02-15`: `76` Events, Derivate `0`, Referenz `47`, Primaer `29`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2025-06-12`: `75` Events, Derivate `50`, Referenz `61`, Primaer `14`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated
- `2022-02-23`: `74` Events, Derivate `0`, Referenz `43`, Primaer `31`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2022-02-17`: `74` Events, Derivate `0`, Referenz `45`, Primaer `29`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2022-02-16`: `74` Events, Derivate `0`, Referenz `45`, Primaer `29`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2022-02-25`: `73` Events, Derivate `0`, Referenz `44`, Primaer `29`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2022-02-19`: `73` Events, Derivate `0`, Referenz `44`, Primaer `29`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2022-03-02`: `72` Events, Derivate `0`, Referenz `44`, Primaer `28`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2022-02-27`: `72` Events, Derivate `0`, Referenz `44`, Primaer `28`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2022-02-18`: `72` Events, Derivate `0`, Referenz `43`, Primaer `29`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2025-04-04`: `71` Events, Derivate `6`, Referenz `36`, Primaer `35`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2022-03-05`: `71` Events, Derivate `0`, Referenz `40`, Primaer `31`, Failed-Solana-0 `0`, Flags: reference_dominated

## Bewertung

- Hohe Aktivitaet bedeutet hier technische Import-Events, nicht automatisch manuelle Trades.
- Derivate/Futures sollten im Dashboard getrennt von Spot/Transfers und Referenzimporten angezeigt werden.
- Tage mit `suspicious_reward_unit` muessen fachlich geprueft werden, weil Rohunits sonst Bestand und Bewertung verfaelschen koennen.
- `failed_zero_solana_tx` sind fehlgeschlagene On-Chain-Versuche mit 0 SOL-Delta; diese sollten nicht wie echte Transfers/Trades bewertet werden.
