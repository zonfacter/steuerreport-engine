# Inferred VTHO Reward From Binance Dust - 2026-05-09

## Zweck

Eng begrenzte Rekonstruktion eines fehlenden VTHO-Zugangs aus einem belegten Binance-API-Dust-Convert.

- Modus: `execute`
- Duplikate: `0`
- Neue Kandidaten: `1`
- Asset/Menge: `42.39387934 VTHO`
- Timestamp: `2023-05-02T04:13:22+00:00`
- Evidence TX: `136251331484`
- Wert USD/EUR: `0.058370024102783203125` / `0.05323287828149725341796875`

## Bewertung

- The Binance API dust-convert outflow proves that 42.39387934 VTHO existed immediately before conversion.
- No primary incoming VTHO row is available in the local exports, so this row is explicitly marked as reviewed/inferred.
- The income value is derived from gross BNB consideration, using cached BNB/USD and USD/EUR rates for 2023-05-02.
- This is not a generic balancing row; it is tied to Binance transId 136251331484.

## Import Result

- `{'source_file_id': 'b63e45916ef4e46fc9073f36ce3c856808e24fb0a02773f0b2545c7406fe3ca0', 'source_created': True, 'inserted_events': 1, 'duplicate_events': 0}`
