# Solana RPC Provider Strategie (Free Tier & Fallback)

## Ziel
Stabile Wallet-Imports trotz Rate-Limits, temporärer Node-Ausfälle und unterschiedlicher RPC-Implementierungen.

## Provider-Klassen
1. Primär: Key-basierte Anbieter-Endpunkte (registriert, Free Tier)
2. Sekundär: öffentliche Mainnet-Endpunkte
3. Tertiär: zusätzliche Public-Fallbacks ohne SLA

## Empfohlene Anbieter mit Free-Tier (laut Anbieterangaben)
- Tatum
- Alchemy
- Helius
- QuickNode
- GetBlock
- Chainstack
- PublicNode (ohne Key nutzbar, Fokus auf öffentliche Endpunkte)

Hinweis: Free-Tier-Limits und Konditionen ändern sich regelmäßig. Die Limits müssen periodisch geprüft und in `known_limitations.md` dokumentiert werden.

## Empfohlene Endpoint-Reihenfolge (Mainnet)
1. Eigener Anbieter-Endpunkt mit API-Key, bevorzugt als Header-Secret (z. B. Tatum/Helius/Alchemy/QuickNode/GetBlock/Chainstack)
2. `https://api.mainnet.solana.com`
3. `https://api.mainnet-beta.solana.com`
4. `https://solana-rpc.publicnode.com`
5. `https://solana.publicnode.dev`
6. `https://solana.api.pocket.network`
7. `https://solana.rpc.subquery.network/public`

## Tatum Gateway
- Endpoint: `https://solana-mainnet.gateway.tatum.io`
- Authentifizierung: `x-api-key` Header, nicht als URL-Bestandteil speichern.
- Lokale Ablage: API-Keys liegen außerhalb des Repositories, z. B. in `/etc/steuerreport/steuerreport.env` mit Dateirechten `600`.
- Systemd-Einbindung: `EnvironmentFile=/etc/steuerreport/steuerreport.env`.
- Sicherheitsregel: Keys dürfen nicht in Audit-Logs, UI-Feldern, Screenshots, Git-Commits oder Source-File-Namen erscheinen.
- Live-Status Stand 2026-04-27: `getBlockHeight` und paginierter Wallet-Import wurden erfolgreich getestet.

## Verifizierte No-Account Endpunkte (Stand: 2026-04-19)
- Erfolgreich getestet mit JSON-RPC `getBlockHeight`:
  - `https://api.mainnet-beta.solana.com`
  - `https://api.mainnet.solana.com`
  - `https://solana-rpc.publicnode.com`
  - `https://solana.publicnode.dev`
  - `https://solana.api.pocket.network`
- Im Test nicht funktionsfähig:
  - `https://rpc.ankr.com/solana` (403/API-Key erforderlich)
  - `https://solana.drpc.org` (Free-Tier blockt Standard-Methoden)
  - `https://solana.api.onfinality.io/public` (429 ohne API-Key im Test)
  - `https://llamarpc.com` (kein direkter Solana JSON-RPC Endpoint)
  - `https://solana.rpc.subquery.network/public` (500 Backendfehler)

## Betriebsregeln
- Bei `HTTP 429` oder `HTTP 403`: automatischer Endpoint-Wechsel.
- Bei RPC-Fehlercodes wie `-32005`, `-32004`, `-32603`: als retry-fähig behandeln und zum nächsten Endpoint wechseln.
- Kurzes Backoff (`50ms`) zwischen Retry-Versuchen, um Burst-Limits nicht zu verstärken.
- `getTransaction` immer mit Parameter-Fallback testen:
  1. `jsonParsed` + `maxSupportedTransactionVersion`
  2. `jsonParsed` ohne Version
  3. `json`

## Datenschutz & Compliance
- Public RPCs sehen Quell-IP und Abfragemuster.
- Für produktive Nutzung (insb. dauerhafte API-Imports) bevorzugt dedizierte Key-RPCs einsetzen.
- Keine API-Keys in Logs, Config-Exports oder Audit-Trail-Klartext speichern.

## Monitoring
- Metriken pro Endpoint erfassen:
  - Erfolgsquote
  - Rate-Limit-Quote (`429`)
  - Durchschnittslatenz
  - Null-/Invalid-Payload-Quote bei `getTransaction`
- Bei schlechter Erfolgsquote automatisch auf nächsten Endpoint priorisieren.

## Runtime-Konfiguration
- Primärendpunkt via `SOLANA_RPC_URL`
- Fallbacks via `SOLANA_RPC_FALLBACK_URLS` (CSV)
- Health-Probe via `POST /api/v1/connectors/solana/rpc-probe`
- Provider-Keys via Environment-Variablen, z. B. `TATUM_API_KEY`.
