# Aktivitaets-Plausibilitaetsaudit

Erstellt: `2026-05-08T10:39:28.783201+00:00`
Eventbasis: `review_actions + tax_event_overrides`
Gesamt-Events: `41623`

## Zusammenfassung

- `reference_dominated`: 134 Tage
- `derivative_dominated`: 69 Tage
- `suspicious_reward_unit`: 17 Tage
- `many_zero_quantity_events`: 17 Tage
- `timestamp_cluster`: 9 Tage
- `high_daily_event_count`: 7 Tage
- `failed_zero_solana_tx`: 5 Tage

## Top-Tage nach Aktivitaet

- `2025-02-01`: `917` Events, Derivate `908`, Referenz `548`, Primaer `369`, Failed-Solana-0 `0`, Flags: high_daily_event_count, derivative_dominated, reference_dominated, many_zero_quantity_events, timestamp_cluster, suspicious_reward_unit
- `2025-02-27`: `260` Events, Derivate `259`, Referenz `155`, Primaer `105`, Failed-Solana-0 `0`, Flags: high_daily_event_count, derivative_dominated, reference_dominated, many_zero_quantity_events, timestamp_cluster
- `2025-02-24`: `260` Events, Derivate `257`, Referenz `154`, Primaer `106`, Failed-Solana-0 `0`, Flags: high_daily_event_count, derivative_dominated, reference_dominated, many_zero_quantity_events, timestamp_cluster
- `2025-06-05`: `223` Events, Derivate `223`, Referenz `223`, Primaer `0`, Failed-Solana-0 `0`, Flags: high_daily_event_count, derivative_dominated, reference_dominated
- `2025-12-26`: `190` Events, Derivate `0`, Referenz `7`, Primaer `183`, Failed-Solana-0 `0`, Flags: high_daily_event_count, timestamp_cluster
- `2025-01-29`: `180` Events, Derivate `97`, Referenz `104`, Primaer `76`, Failed-Solana-0 `0`, Flags: high_daily_event_count, reference_dominated, many_zero_quantity_events, timestamp_cluster, suspicious_reward_unit
- `2025-02-22`: `151` Events, Derivate `147`, Referenz `90`, Primaer `61`, Failed-Solana-0 `0`, Flags: high_daily_event_count, derivative_dominated, reference_dominated, many_zero_quantity_events, timestamp_cluster
- `2025-02-21`: `128` Events, Derivate `128`, Referenz `74`, Primaer `54`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated, many_zero_quantity_events, timestamp_cluster
- `2025-05-30`: `107` Events, Derivate `107`, Referenz `107`, Primaer `0`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated
- `2025-01-20`: `99` Events, Derivate `0`, Referenz `1`, Primaer `98`, Failed-Solana-0 `0`, Flags: keine
- `2025-02-02`: `96` Events, Derivate `96`, Referenz `56`, Primaer `40`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated, many_zero_quantity_events
- `2025-05-23`: `80` Events, Derivate `77`, Referenz `79`, Primaer `1`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated
- `2025-06-12`: `75` Events, Derivate `50`, Referenz `61`, Primaer `14`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated
- `2025-04-04`: `71` Events, Derivate `6`, Referenz `36`, Primaer `35`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2025-02-23`: `70` Events, Derivate `67`, Referenz `42`, Primaer `28`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated, many_zero_quantity_events
- `2025-05-11`: `68` Events, Derivate `68`, Referenz `68`, Primaer `0`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated
- `2025-01-27`: `68` Events, Derivate `0`, Referenz `68`, Primaer `0`, Failed-Solana-0 `0`, Flags: reference_dominated
- `2025-01-31`: `66` Events, Derivate `64`, Referenz `38`, Primaer `28`, Failed-Solana-0 `0`, Flags: derivative_dominated, reference_dominated, many_zero_quantity_events
- `2025-01-04`: `65` Events, Derivate `0`, Referenz `31`, Primaer `34`, Failed-Solana-0 `4`, Flags: reference_dominated, failed_zero_solana_tx, timestamp_cluster, suspicious_reward_unit
- `2025-01-26`: `62` Events, Derivate `0`, Referenz `62`, Primaer `0`, Failed-Solana-0 `0`, Flags: reference_dominated

## Bewertung

- Hohe Aktivitaet bedeutet hier technische Import-Events, nicht automatisch manuelle Trades.
- Derivate/Futures sollten im Dashboard getrennt von Spot/Transfers und Referenzimporten angezeigt werden.
- Tage mit `suspicious_reward_unit` muessen fachlich geprueft werden, weil Rohunits sonst Bestand und Bewertung verfaelschen koennen.
- `failed_zero_solana_tx` sind fehlgeschlagene On-Chain-Versuche mit 0 SOL-Delta; diese sollten nicht wie echte Transfers/Trades bewertet werden.
