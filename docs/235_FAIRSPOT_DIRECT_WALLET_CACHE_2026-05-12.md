# Fairspot Direct Wallet Cache

Stand: 2026-05-12

## Anlass

Die offiziellen Helium-L1-Torrents haben aktuell keine nutzbaren Peers. Als pragmatische Zwischenloesung wurden die Fairspot-CSV-Exports fuer alle direkten Helium-Gegenwallets der bekannten eigenen Wallets lokal gesichert.

Fairspot-Pattern:

`https://fairspot.nyc3.digitaloceanspaces.com/accounting-csv/helium-{wallet}-all.csv`

## Scope

Eigene Wallets:

- Haupt-Wallet `133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j`
- Staking-Wallet `14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA`

Gecacht wurden:

- beide eigenen Wallets
- alle direkten Gegenwallets aus den vorhandenen Fairspot-Exports dieser eigenen Wallets

Bewusst nicht gecacht wurden alle weiteren Gegenparteien grosser Service-/Pool-Wallets, weil das sofort in tausende fremde Wallets ausufern wuerde und fuer die aktuelle Belegfrage nicht erforderlich ist.

## Speicherort

Rohdaten liegen ausserhalb des Git-Repos:

`/root/.local/share/steuerreport/fairspot_wallet_exports`

Manifest:

`/root/.local/share/steuerreport/fairspot_wallet_exports/manifest.json`

Diese CSV-Dateien duerfen nicht committed werden.

## Ergebnis

- Wallet-Dateien: `12`
- Downloadfehler: `0`

| Wallet | Eigene Wallet | Direkte Kontakte | In zu eigener Wallet | Out von eigener Wallet | Fairspot-Zeilen | Groesse Bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `133rkwoKCfxLTTt1zGjge7c2nGLUSY5sTuG2V61zi6ik269Tf4j` | ja | 0 | 0 | 0 | 21889 | 2717948 |
| `14eKedP4gCyefaMgjxPULPVecDq6gM5aEJYLDvbiRXZpuq2kYNA` | ja | 0 | 0 | 0 | 35 | 7385 |
| `138bCXPVfSq7yyTfoDUrVwztPmUr4WGyA7TED9Y41djmF7rjA8y` | nein | 19 | 0 | 19 | 37 | 7740 |
| `14aDLshY7p2MJrCgbYrWFZZfjB1MBSqHboo2cJCPCVR9Meorh7w` | nein | 18 | 10 | 8 | 41273 | 8527582 |
| `13m4dWjjQrFSGfhC3tawCpQRv7oXAJxBSaSXCtr7DWFcMG6p4E9` | nein | 5 | 0 | 5 | 20983 | 2604358 |
| `14o7quYAMQZFE8UCNPN89yK9fwtxMW8wvht8MQZkSiSgizeqSme` | nein | 2 | 1 | 1 | 11 | 1659 |
| `137tZvaxM4zjvfU9GcDzzmAsdMjkESCULx9XaVrGWKj989izPue` | nein | 1 | 0 | 1 | 2645 | 589253 |
| `13TFnZyGDy95neRAxnP5Y9FLHqW7Mu28U9VgmZz2hgNhi7qG3qF` | nein | 1 | 1 | 0 | 187503 | 43064761 |
| `14496bkcZrrF2BxmsRCmwBJYiqf16bSawKqoEo8od98s26EXZon` | nein | 1 | 0 | 1 | 17972 | 3974157 |
| `14JU4itCHRsdPaQJxvcvtLLCr8KCf6VAoN3aB5DcV8mXLhQq7C3` | nein | 1 | 0 | 1 | 5418 | 1235004 |
| `14YeKFGXE23yAdACj6hu5NWEcYzzKxptYbm5jHgzw9A1P1UQfMv` | nein | 1 | 1 | 0 | 227315 | 53131590 |
| `14ZyX7NDQdNVZ62d5gdknhtHErLFJ7qQqkMG9nhVtY1ZxSawZHQ` | nein | 1 | 0 | 1 | 3228 | 729266 |

## Skript

Reproduzierbar mit:

```bash
python3 scripts/fairspot_direct_wallet_cache_20260512.py
```

Das Skript schreibt nur in den lokalen Cache unter `/root/.local/share/steuerreport/fairspot_wallet_exports` und legt keine Rohdaten im Git-Repo ab.

## Naechste sichere Nutzung

1. Einzelne offene HNT-Transaktionen gegen diesen Cache suchen.
2. Nur Event-IDs, Zeitpunkte, Wallets, Mengen und abgeleitete Befunde dokumentieren.
3. Keine Anschaffungskosten aus Fairspot-Oracle-Werten oder Transferwerten ableiten.
4. Wenn ein Beleg steuerlich relevant wird, gegen eine Primaerquelle oder das offizielle Helium-L1-Archiv gegenpruefen.
