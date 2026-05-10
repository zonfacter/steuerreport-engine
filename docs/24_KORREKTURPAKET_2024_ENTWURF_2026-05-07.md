# Korrekturpaket 2024 Entwurf

Erstellt: 2026-05-07T21:50:03.083493+00:00

Status: Entwurf, nicht final einreichen.

Grund: Der aktuelle Steuerlauf ist technisch erfolgreich, aber 2024 hat weiterhin Negativbestände. Dieses Paket dient als Arbeitsgrundlage für eine mögliche Änderung des Einkommensteuerbescheids 2024.

## Kurzfazit

- Eingereichter Referenzstand WISO/Blockpit Anlage SO gesamt: `2572.91 EUR`.
- Aktueller Steuerreport Anlage SO gesamt: `2764.73 EUR`.
- Delta Anlage SO aktuell minus eingereicht: `191.82 EUR`.
- Aktuelle Termingeschäfte netto: `-8413.69 EUR`.
- Aktuelle Termingeschäfte Verlustsumme absolut: `20149.13 EUR`.
- Aktueller Job: `bc5614a2-75c5-4a5e-8242-d16391556b05`.

## Eingereicht vs. aktuell

| Position | Eingereicht | Aktuell | Delta |
|---|---:|---:|---:|
| Anlage SO Leistungen/Rewards | 59.66 | 2291.81 | 2232.15 |
| Anlage SO private Veräußerungen netto | 2513.25 | 472.92 | -2040.33 |
| Anlage SO gesamt | 2572.91 | 2764.73 | 191.82 |
| Termingeschäfte netto | nicht im WISO-Referenz-CSV | -8413.69 | n/a |

## Offene Qualitätsmarker

- Negativbestände 2024: `37`.
- Nach Assets: `{"BUSD": 12, "SOL": 1, "USDT": 12, "VTHO": 12}`.
- Benötigte Klärung: Bitget-Web-Exports/Statements für Spot/Bot/Grid/Strategy/Internal Transfers 2024; SOL- und Stablecoin-Bestände prüfen.

## Größte aktuelle Anlage-SO-Assetgruppen

| Asset | Zeilen | Gewinn/Verlust EUR | Erlöse EUR | Kostenbasis EUR |
|---|---:|---:|---:|---:|
| USDC | 1 | 473.40 | 473.40 | 0.00 |
| USDT | 23 | -73.00 | 707.62 | 780.62 |
| JUP | 9 | -0.37 | 0.00 | 0.37 |
| SOL | 157 | -0.04 | -0.02 | 0.02 |
| JUPYIWRYJFSKUPIHA7HKER8VUTAEFOSYBKEDZNSDVCN | 84 | -0.02 | -0.02 | 0.00 |
| ES9VMFRZACERMJFRF4H2FYD4KCONKY11MCCE8BENWNYB | 79 | -0.01 | -0.01 | 0.00 |
| ZEUS1AR7AX8DFFJF5QJWJ2FTDDDNTROMNGO8YOQM3GQ | 28 | -0.01 | -0.01 | 0.00 |
| EPJFWDD5AUFQSSQEM2QN1XZYBAPC8G4WEGGKZWYTDT1V | 38 | -0.01 | -0.01 | 0.00 |
| URAE9VVDRWXNCIKCCRP7TGNQESARFTP22IXZH7GPUMP | 1 | -0.01 | -0.01 | 0.00 |
| IOTEVVZLEYWOTN1QDWNPDDXPWSZN3ZFHEOT3MFL9FNS | 69 | -0.00 | -0.00 | 0.00 |
| SHARKSYJJQANYXVFRPNBN9PJGKHWDHATNMYICWPNR1S | 2 | -0.00 | -0.00 | 0.00 |
| UPTX1D24ABWURGWXVNFMX4GNRAJ3QGFZL3QQBGXTWQG | 1 | -0.00 | -0.00 | 0.00 |
| 25HAYBQFODHFWX9AY6RARBGVWGWDDNQCHSXS3JQ3MTDJ | 2 | -0.00 | -0.00 | 0.00 |
| 3NZ9JMVBMGAQOCYBIC2C7LQCJSCMGSAZ6VQQTDZCQMJH | 3 | -0.00 | -0.00 | 0.00 |
| 7GCIHGDB8FE6KNJN2MYTKZZCRJQY3T9GHDC8UHYMW2HR | 2 | -0.00 | -0.00 | 0.00 |

## Termingeschäfte nach Asset

| Asset | Zeilen | Gewinn/Verlust EUR | Gebühren EUR |
|---|---:|---:|---:|
| SOL | 26 | -7528.74 | 1347.90 |
| BTC | 10 | -884.95 | 179.64 |

## Entwurf Begründung Finanzamt

Nach Abgabe der Einkommensteuererklärung 2024 wurden weitere Primärdaten aus Wallets und Börsen sowie ergänzende Export-/API-Daten ausgewertet. Der ursprünglich eingereichte WISO/Blockpit-Report wird als Referenzstand behandelt, ist nach aktuellem Datenstand aber nicht mehr vollständig deckungsgleich mit den verfügbaren Primärdaten.

Die aktuelle Neuberechnung weist abweichende Besteuerungsgrundlagen in Anlage SO sowie gesondert zu berücksichtigende Termingeschäfte aus. Vor Einreichung dieses Entwurfs werden die noch offenen Bestandsdifferenzen und Plattform-Statements final abgeglichen.
