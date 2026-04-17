## Änderungstyp
- [ ] Feature
- [ ] Bugfix
- [ ] Refactor
- [ ] Docs
- [ ] Compliance/Ruleset

## KI-Compliance (Pflicht bei kritischen Modulen)
Betroffene kritische Module: `fifo`, `ruleset`, `fx_engine`, `integrity_manager`
- [ ] Logik manuell zeilenweise auditiert (kein Blackbox-Code)
- [ ] Logik und Tests wurden in getrennten KI-Kontexten erstellt
- [ ] Randfälle durch Tests abgedeckt (Liquidation, 0-Bestand, Precision-Loss)
- [ ] Golden-Case-Vergleich für betroffene Steuerjahre erfolgreich

## Tests
- [ ] Unit Tests aktualisiert/ergänzt
- [ ] Integrationstests aktualisiert/ergänzt
- [ ] Golden Hash Verification erfolgreich

## Determinismus und Integrität
- [ ] Fachliche Outputs unverändert oder bewusst versioniert
- [ ] `run_id`, `trace_id`, `execution_time` nicht in Golden-Hash einbezogen
- [ ] Ruleset-/Config-Änderungen dokumentiert

## Security
- [ ] Keine Secrets im Code/Logs
- [ ] Wallet-Adressen in Logs maskiert
- [ ] Supply-Chain-Änderungen dokumentiert (`uses` mit SHA-Pinning)

## Zusammenfassung
<!-- Kurzbeschreibung der Änderung und Motivation -->

## Risiken / Offene Punkte
<!-- Was könnte noch brechen? -->
