# Spam Token Ignored Candidates - 2026-05-09

## Zweck

Offensichtliche Spam-/Drop-Artefakte aus Portfolio- und Bewertungsansichten ausblenden, ohne RAW-Belege zu löschen.

- Eingetragen/aktualisiert: `3`
- Unveraendert: `0`

## Ignored Tokens

- `CM8VSESV7MBHAFD5UDXH84QFGXMAVWJCVVHOPB1DZIF4`: Solana spam mint: unsolicited 1,000,000,000 token mint with promotional whitelist memo; raw evidence retained. Evidence: `tx 5wjYFMr8L1q8vDao9YAk9ScWkdzPwcdkYdQnCMpqSVmRaDnHFrQG5KdwRk6XLgZGfXtvvb7MgEfyTNURrYqv7KzQ`
- `BONKBOX`: Blockpit manual auto-balancing spam token without transaction id or primary evidence; excluded from portfolio valuation. Evidence: `blockpit-486:in, 2025-07-06, 1,000,000,000 BONKBOX`
- `JUPDROP`: Repeated Solana drop/spam-style token entries and manual auto-balancing; excluded from portfolio valuation pending contrary primary evidence. Evidence: `Blockpit JUPDROP deposits/auto-balancing 2024-2025`

## Bewertung

- Ignored tokens remain in RAW evidence but are excluded from dashboard/portfolio/audit valuation paths that honor runtime.ignored_tokens.
- This run only marks obvious spam/drop artifacts; real or traded assets such as PYTH, JUP, SHARK, IOT, SOL and BTC are not ignored.
- If contrary primary evidence is found, remove the token from runtime.ignored_tokens instead of deleting RAW rows.
