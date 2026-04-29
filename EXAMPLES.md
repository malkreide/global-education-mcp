# Use Cases & Examples — global-education-mcp

Real-world queries by audience. Indicate per example whether an API key is required.

## 🏫 Bildung & Schule
Lehrpersonen, Schulbehörden, Fachreferent:innen

### Schulabschlussquoten im DACH-Vergleich
«Wie hoch ist die Abschlussquote in der Sekundarstufe II in der Schweiz im Vergleich zu Deutschland und Österreich?»

→ `uis_compare_countries(indicator_id="CR.3", country_codes=["CHE", "DEU", "AUT"])`

**Warum nützlich:** Erlaubt Schulbehörden, das Schweizer Bildungssystem direkt mit den Nachbarländern zu vergleichen und die eigene Position im internationalen Kontext fundiert zu bewerten. (API-Key nötig: Nein)

### Entwicklung des Schüler-Lehrer-Verhältnisses
«Wie hat sich das Schüler-Lehrer-Verhältnis in der Primarstufe in der Schweiz in den letzten 10 Jahren entwickelt?»

→ `uis_get_education_data(indicator_id="PTR.1", country_code="CHE", start_year=2013, end_year=2023)`

**Warum nützlich:** Liefert Fachreferent:innen evidenzbasierte Daten für die Ressourcenplanung und Argumentation in bildungspolitischen Diskussionen. (API-Key nötig: Nein)

## 👨‍👩‍👧 Eltern & Schulgemeinde
Elternräte, interessierte Erziehungsberechtigte

### Bildungsausgaben im internationalen Vergleich
«Gibt die Schweiz mehr für Bildung aus als Finnland? Zeige mir die Bildungsausgaben als Prozent des BIP.»

→ `uis_compare_countries(indicator_id="XGDP.FSGOV", country_codes=["CHE", "FIN"])`

**Warum nützlich:** Gibt interessierten Eltern und Schulkommissionen eine objektive Diskussionsgrundlage bei Debatten um Bildungsbudgets und die kantonale Ressourcenverteilung. (API-Key nötig: Nein)

### Geschlechterparität in der Bildung
«Gibt es in der Schweiz noch Unterschiede in den Einschulungsraten zwischen Mädchen und Knaben in der Sekundarstufe?»

→ `uis_get_education_data(indicator_id="GPI.NERA.2", country_code="CHE")`

**Warum nützlich:** Hilft Elternräten, das Thema Chancengleichheit mit konkreten internationalen Messwerten an der eigenen Schule oder im Kanton zu diskutieren. (API-Key nötig: Nein)

## 🗳️ Bevölkerung & öffentliches Interesse
Allgemeine Öffentlichkeit, politisch und gesellschaftlich Interessierte

### Umfassendes Bildungsprofil der Schweiz
«Erstelle mir ein kurzes Bildungsprofil für die Schweiz mit den wichtigsten Indikatoren wie Alphabetisierung und Schulabschlüssen.»

→ `uis_country_education_profile(country_code="CHE", latest_year_only=true)`

**Warum nützlich:** Bietet der allgemeinen Öffentlichkeit einen kompakten und verständlichen Überblick über den Status quo des Schweizer Bildungssystems anhand standardisierter Kennzahlen. (API-Key nötig: Nein)

### OECD-Vergleich von Lehrergehältern
«Wie schneiden die Lehrergehälter der Schweiz im Vergleich zu anderen OECD-Ländern ab?»

→ `oecd_get_education_indicator(dataflow_id="EAG_PERS_SALARY", countries=["CHE", "DEU", "AUT", "FRA"])`

**Warum nützlich:** Liefert bei politischen Abstimmungen oder Diskussionen im Bildungssektor transparente, international vergleichbare Fakten zur Einordnung der Gehaltsstrukturen. (API-Key nötig: Nein)

## 🤖 KI-Interessierte & Entwickler:innen
MCP-Enthusiast:innen, Forscher:innen, Prompt Engineers, öffentliche Verwaltung

### SDG-4-Monitoring mit KI
«Analysiere den Fortschritt der Schweiz beim SDG-4-Ziel (Hochwertige Bildung) für die letzten fünf Jahre und zeige mir Trends.»

→ `uis_get_education_data(indicator_id="CR.2", country_code="CHE", start_year=2018, end_year=2023)`
→ `uis_get_education_data(indicator_id="LR.AG15T99", country_code="CHE", start_year=2018, end_year=2023)`

**Warum nützlich:** Zeigt, wie Prompt Engineers mehrere API-Aufrufe bündeln können, um komplexe Monitoring-Berichte für Nachhaltigkeitsziele (SDGs) automatisiert zu generieren. (API-Key nötig: Nein)

### Kombination von Bildungs- und Wirtschaftsdaten (Multi-Server)
«Wie hoch sind die Schweizer Bildungsausgaben im Vergleich zur gesamtwirtschaftlichen Entwicklung und den aktuellen SNB-Leitzinsen?»

→ `uis_get_education_data(indicator_id="XGDP.FSGOV", country_code="CHE", start_year=2015, end_year=2023)`
→ `snb_get_data(id="data-snb-rates")` (via [swiss-snb-mcp](https://github.com/malkreide/swiss-snb-mcp))

**Warum nützlich:** Demonstriert die Stärke des MCP-Ökosystems, indem Bildungsdaten nahtlos mit makroökonomischen Zeitreihen der Schweizerischen Nationalbank verschnitten werden. (API-Key nötig: Nein)

## 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
|---|---|---|
| ...einen Überblick über das Bildungssystem eines Landes erhalten | `uis_country_education_profile` | Nein |
| ...die Schweiz mit anderen Ländern bei einem bestimmten Thema vergleichen | `uis_compare_countries` | Nein |
| ...die historische Entwicklung einer Bildungskennzahl analysieren | `uis_get_education_data` | Nein |
| ...detaillierte OECD-Datensätze (z.B. zu Gehältern oder Finanzierung) abrufen | `oecd_get_education_indicator` | Nein |
| ...herausfinden, welche UNESCO-Indikatoren überhaupt verfügbar sind | `uis_list_indicators` | Nein |
| ...die Ländercodes (ISO 3166-1 Alpha-3) nachschlagen | `uis_list_countries` | Nein |
| ...mehrere Länder über verschiedene UNESCO-Fokusthemen hinweg vergleichen | `education_benchmark_countries` | Nein |
