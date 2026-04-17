# Depot-Trennung (Depot Separation) für FIFO

## 1. Ziel
Depot-Trennung ermöglicht zwei Betriebsmodi:
- `global_fifo`: ein Asset-Pool über alle Depots.
- `depot_separated_fifo`: je Depot eigener FIFO-Pool.

Nutzen:
- Schutz langfristiger Bestände in separaten Depots.
- Saubere steuerliche Trennung zwischen Trading-Depots und Langfrist-Depots.

## 2. Kernprinzip: Asset + Ort
Jede steuerrelevante Bewegung wird über zwei Dimensionen modelliert:
- `asset` (z. B. BTC)
- `depot_id` (z. B. Trade Republic, Phantom, Ledger)

Regel:
- Verkauf in Depot X darf im getrennten Modus nur Lots aus Depot X verbrauchen.

## 3. Datenmodell-Erweiterung

### Tabelle `depots`
- `id` (UUID)
- `name` (String)
- `type` (Enum: `CEX`, `DEX`, `COLD`)
- `is_separated` (Boolean)
- `is_hard_silo` (Boolean)
- `created_at` (Timestamp UTC)

### Tabelle `raw_events` (Erweiterung)
- `depot_id` (UUID, FK)
- `counterparty_depot_id` (UUID, optional)
- `portfolio_scope` (Enum: `global`, `exchange`, `wallet`, `depot`)

### Tabelle `tax_lots` (Erweiterung)
- `depot_id` (UUID, FK)
- `origin_depot_id` (UUID)
- `origin_timestamp` (Timestamp UTC)
- `transfer_chain_id` (UUID, optional)

## 4. Transfer-Matching zwischen Depots
Eigenüberträge sind die Brücke zwischen Silos.

Ablauf:
1. Abgang in Silo A reduziert Bestand in A (keine Veräußerung).
2. Anschaffungsdaten (Zeitpunkt, Cost Basis, Lot-ID) werden in Transfer-Metadaten konserviert.
3. Zugang in Silo B übernimmt exakt diese Anschaffungsdaten.

Pflichtvalidierung:
- `qty_out - transfer_fee ~= qty_in` innerhalb konfigurierter Toleranz.
- Bei Abweichung: `transfer_mismatch_issue` mit Severity.

## 5. Konfigurationsmodell
```json
{
  "calculation_mode": "depot_separated",
  "fifo_mode": "scoped",
  "separated_depots": ["trade_republic", "phantom_main"],
  "global_pools": ["binance", "bitget"],
  "transfer_tolerance": {
    "absolute": "0.00000001",
    "relative": "0.001"
  }
}
```

## 6. Engine-Logik (Silo-Selector)
```python
def get_next_available_lots(asset, depot_id, mode):
    if mode == "depot_separated":
        return query_lots(asset=asset, depot_id=depot_id, order="timestamp_asc")
    return query_lots(asset=asset, order="timestamp_asc")
```

## 7. Trade Republic als Hard Silo
Empfohlene Standardregel:
- Trade Republic als `is_hard_silo=true` führen.
- Ohne bestätigten Transfer keine Lot-Bewegung zwischen TR und On-Chain-Depots.

Vorteil:
- Hohe Datenstabilität als Referenz-Depot.
- Keine unbeabsichtigte Vermischung mit DeFi-Hochfrequenzereignissen.

## 8. UI-Erweiterungen (Silo-Dashboard)
- Silo-Ansicht mit Bestand, Cost Basis, unrealisierter PnL je Depot.
- Transfer-Warnung mit Bestätigungsdialog bei Eigenübertrag.
- Visualisierte Transfer-Kette (`A -> B -> C`) mit übernommenem Anschaffungsdatum.

## 9. API-Erweiterungen
- `GET /api/v1/depots`
- `POST /api/v1/depots`
- `PATCH /api/v1/depots/{depot_id}`
- `POST /api/v1/transfers/confirm-internal`
- `GET /api/v1/audit/transfer-chain/{transfer_chain_id}`

## 10. Verifikation (Pflicht)
- Gleiches Dataset mit `global` vs. `scoped` liefert nachvollziehbar unterschiedliche, aber deterministische Resultate.
- Keine Vermischung von Lots über Hard-Silo-Grenzen.
- Transfer-Invarianten immer geprüft und protokolliert.
- Haltedauer bleibt über Depotwechsel erhalten.

## 11. Verbesserungen gegenüber Basiskonzept
- `is_hard_silo` verhindert implizite Zusammenführung.
- `transfer_chain_id` erhöht Prüfungsfähigkeit erheblich.
- Doppelte Toleranz (`absolute` + `relative`) reduziert Fehlalarme bei Kleinstbeträgen.
