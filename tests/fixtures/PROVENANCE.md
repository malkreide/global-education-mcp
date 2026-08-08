# Herkunft der Fixtures

**Erzeugt von `scripts/record_fixtures.py`. Nicht von Hand pflegen.**

Aufgezeichnet am **2026-08-08** von `api.uis.unesco.org`.

Ohne Datum ist «aufgezeichnet» nach zwei Jahren von «ausgedacht» nicht
mehr zu unterscheiden — die Datei sieht gleich aus.

## `uis_definitions_indicators.json` ist der Vertrag

Die lokale Indikatorentabelle des Servers wird gegen diese
Aufzeichnung gehalten. Am 2026-08-08 gab es **12 der 22 IDs** darin
nicht — und weil der API-Pfad ebenfalls 404 gab, war diese Tabelle
die einzige Liste, die ein Nutzer je zu sehen bekam.

## Zwei Datenantworten, und beide werden gebraucht

`uis_data_records.json` traegt Zeilen, `uis_data_empty.json` ist eine
echte Leermenge. Erst zusammen trennen sie den Befund («der Leser
findet nie etwas») von einer Aussage der Quelle («hier gibt es
nichts»). Eine Fixture mit nur einem der beiden Faelle liesse den
Fehler wieder durch.

**Es sind Ausschnitte, keine Vollabzuege.** Die Auswahlregel steht je
Datei dabei. Wo nach Verwendung ausgewaehlt wurde und nicht nach
Position, steht auch das dort — «die ersten N» haetten bei 5063
Indikatoren keinen der angebotenen getroffen.

## `uis_openapi_query_params.json`

- **Quelle:** `https://api.uis.unesco.org/api/public/openapi/schema.json`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** nur die Query-Parameter je Pfad, aus der OpenAPI der Quelle. Das ist der Vertrag, an dem `start`/`end` haengen: Gesendet wurde `startYear`/`endYear`, und weil unbekannte Parameter mit HTTP 200 durchfallen, sah der nicht angewandte Filter aus wie ein angewandter
- **Groesse:** 804 B
- **SHA-256:** `fa11980e94b4bb3847aa43632b309f37408ea4c2e42a1c3cbb7adeaad950d5e4`

## `uis_definitions_indicators.json`

- **Quelle:** `https://api.uis.unesco.org/api/public/definitions/indicators`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** alle 17 Indikatoren, die der Server anbietet, plus 8 weitere (von 5063). Nach Verwendung ausgewaehlt, nicht nach Position — «die ersten N» haetten keinen der angebotenen enthalten und damit den Befund verdeckt
- **Groesse:** 11570 B
- **SHA-256:** `9750a667ce30a919438edc4549592a7c5a9741045656892cd3c700c9c56f439c`

## `uis_indicator_themes.json`

- **Quelle:** `https://api.uis.unesco.org/api/public/definitions/indicators?theme=…`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** die KONTROLLE zum `theme`-Filter. Drei Werte, darunter ein erfundener, liefern dieselbe Zeilenzahl wie gar kein Parameter — der Filter wird nicht gelesen. Daneben die echte Verteilung aus dem Feld `theme` der Zeilen selbst, gegen die jetzt lokal gefiltert wird
- **Groesse:** 316 B
- **SHA-256:** `2b54f011ac8f02e07501cbf9d2ed19763cdd98b1d4993207dcdbfddbfd7eaafd`

## `uis_definitions_geounits.json`

- **Quelle:** `https://api.uis.unesco.org/api/public/definitions/geounits`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** 44 von 462 Eintraegen: die fuenf, die der Server namentlich anbietet, plus je 20 NATIONAL und REGIONAL. Nach Typ ausgewaehlt und nicht nach Position — die Liste ist alphabetisch, «die ersten 40» haetten kein einziges der 221 regionalen Aggregate enthalten und den Typfilter unpruefbar gelassen
- **Groesse:** 4526 B
- **SHA-256:** `979ef9e48fc8152f0a937abc94ab7c9ab20f6800cb8723aee1bc4ce05c619b68`

## `uis_data_records.json`

- **Quelle:** `https://api.uis.unesco.org/api/public/data/indicators?indicator=CR.1&geoUnit=CHE`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** vollstaendig, 14 Zeilen. Der Umschlag ist der Gegenstand: Er heisst `records`, und gesucht wurde `observations` — deshalb kam aus jeder Antwort eine leere Liste
- **Groesse:** 2276 B
- **SHA-256:** `829ec7629a4625a18323a6b216bab72ca97f8749ec57714c9fa55475592c2c34`

## `uis_data_year_filter.json`

- **Quelle:** `https://api.uis.unesco.org/api/public/data/indicators?indicator=CR.1&geoUnit=CHE&start=2015&end=2018`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** dieselbe Reihe zweimal, einmal mit den gesendeten Parameternamen und einmal mit den deklarierten. `startYear`/`endYear` liefern die volle Reihe, `start`/`end` die vier verlangten Jahre. Nur das Paar belegt den Befund: Eine einzelne Antwort mit 14 Zeilen sieht nach reichlich Daten aus, nicht nach einem ignorierten Filter
- **Groesse:** 346 B
- **SHA-256:** `6dcbf1d7c28b521daf78b1d3a70f5d1bc0a3a1fc2ea5ac17f2b0872aff76e301`

## `uis_data_empty.json`

- **Quelle:** `https://api.uis.unesco.org/api/public/data/indicators?indicator=10&geoUnit=CHE`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** eine ECHTE Leermenge: `records` ist da und leer. Der Gegenfall zum Befund — ohne ihn liesse sich «der Leser findet nie etwas» nicht von «hier gibt es nichts» unterscheiden
- **Groesse:** 62 B
- **SHA-256:** `526036bd92f1157ae19ad43381cf192ad2ad29b6dfe2277773c79f2d58662bf2`

## `uis_data_unknown_geounit.json`

- **Quelle:** `https://api.uis.unesco.org/api/public/data/indicators?indicator=CR.1&geoUnit=XXX`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** die KONTROLLE zu `uis_data_empty.json`: ein erfundener Ländercode. HTTP 200, leeres `records` — und ein `hints`-Eintrag, der den Grund im Klartext nennt. Beide Antworten sehen ohne `hints` gleich aus, und genau daraus wurde aus einem Tippfehler die Aussage «für dieses Land gibt es keine Daten»
- **Groesse:** 164 B
- **SHA-256:** `2ec964af4eac405813fcf3a2ec4c9c2cc475c603caedf1440a62d54cbccd3327`

## `uis_versions.json`

- **Quelle:** `https://api.uis.unesco.org/api/public/versions`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** vollstaendig, 15 Versionen — der einzige Pfad, den der Server von Anfang an richtig gebaut hat
- **Groesse:** 11413 B
- **SHA-256:** `94c1cd49b8245e61bf502507eb553897b3180e64d346dd21dcf4b221a3521670`
