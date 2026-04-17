# Wettbewerbs- und Komfort-Features

## 1. Steuer-Optimierung
- Unrealized Gains/Losses Dashboard (Jahresend-Sicht).
- Holding-Period-Assistent (Hinweis auf 365-Tage-Grenze).
- Lot-Optimierung (nur wenn rechtlich zulässig und regelkonform).

Technischer Impact:
- Simulationsmodus auf Basis `dry_run`.
- Vergleichsrechnungen mit identischer Datenbasis und unterschiedlichen Strategien.

## 2. Error Reconciliation und Datenintegrität
- Missing-Cost-Basis-Fixer (mit klarer Kennzeichnung geschätzter Werte).
- Spam-/Dust-Filter (insb. Solana/NFT-Airdrops).
- Auto-Merge von Transfers (Withdrawal/Deposit über Wallets/Exchanges).

Technischer Impact:
- Heuristik-Schicht mit Konfidenzscores.
- Pflicht-Review bei niedriger Konfidenz.

## 3. DeFi- und Chain-Intelligenz
- Smart-Contract-Labeling (Staking, LP, Lending/Borrowing, Farming).
- NFT-Ansicht mit Bewertungsbezug (falls Marktdaten vorhanden).
- Gas-Fee-Tracking als separate steuerliche Kategorie.

Technischer Impact:
- Ereignisklassifizierung über regelbasierte Matcher + Signaturbibliothek.
- Strikte Trennung zwischen Fakt, Annahme und Schätzung.

## 4. Compliance und Audit-Sicherheit
- Lückenloser Audit-Trail von Quelle bis Reportzeile.
- Referenzierbare Regeln je Steuerjahr (BMF-konforme Regeln als Zielbild).
- Vorbereitung für ausfüllunterstützte Steuer-Formularpfade.

Technischer Impact:
- Persistente Trace-IDs je Reportzeile.
- Versionierte Regelsets (`ruleset_version`) und Adapterversionen.

## 5. Portfolio-Funktionen
- Optionales Live-Balance-Modul via API-Anbindungen.
- Performance-Metriken (z. B. ROI, Allokation; Sharpe nur bei sauberer Datenbasis).

Technischer Impact:
- Klare Trennung von Steuerberechnung (vergangenheitsbezogen) und Portfolio-Tracking (zeitnah).

## 6. Must-Have Marketing Claims (nur wenn technisch gedeckt)
- "Zahle nie mehr Steuern als nötig." -> durch nachweisbare Optimierungssimulation.
- "Korrigiert fehlende Daten automatisch." -> nur mit Kennzeichnung und Review-Workflow.
- "Versteht komplexe DeFi-Transaktionen." -> durch belegbare Aggregations- und Klassifizierungsregeln.
- "Sicher bei jeder Betriebsprüfung." -> durch vollständige Rückverfolgbarkeit.

## 7. Priorisierte Umsetzung
1. Audit-Sicherheit und Datenintegrität.
2. Transfer-Reconciliation und Explainability.
3. DeFi-Klassifizierung.
4. Steuer-Optimierungsmodul.
5. Portfolio-Komfortfunktionen.
