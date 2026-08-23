# Changelog

Alle nennenswerten Änderungen werden hier dokumentiert.

Format basiert auf [Keep a Changelog 1.1.0](https://keepachangelog.com/de/1.1.0/);
Versionierung folgt [Semantic Versioning 2.0](https://semver.org/lang/de/).

## [Unreleased]

### Hinzugefuegt

- **Frischehinweise auf den auflistenden Methoden** (SEP-2549, Spec
  `2026-07-28`): `ttlMs` 300000, `cacheScope` `public`. Das SDK setzt beides von
  sich aus auf «sofort veraltet, nie geteilt» — wer nichts übergibt, lässt jeden
  Client bei jeder Verbindung neu auflisten, für Verzeichnisse, die per
  Dekorator beim Import feststehen und nicht vom Aufrufer abhängen.

  `resources/read` und `prompts/get` bleiben ohne Hinweis: das wäre eine
  Zusicherung über den Inhalt statt über das Verzeichnis. Ein Test hält das an
  der Antwort fest, ein zweiter an der Konfiguration.

- **Protokoll-Gate: beide Spec-Aeren gepinnt und geprueft**
  (`tests/test_protocol_version.py`). `mcp` 2.x bedient zwei Aeren ueber
  denselben Server — den `initialize`-Handshake, der bei `2025-11-25`
  deckelt, und den Pro-Request-Envelope, der `2026-07-28` erreicht.
  `LATEST_PROTOCOL_VERSION` ist ein Alias auf die **moderne** Aera; wer nur
  dagegen pinnt, laesst genau die Aera frei wandern, die heutige Clients
  aushandeln. Beide sind jetzt einzeln gepinnt, ein Dependabot-Bump von
  `mcp` kann keine davon still verschieben.

  Ohne gemessenen Teil: dieser Server baut keine ASGI-App, durch die sich ein
  `initialize` schicken liesse. Das Gate haengt deshalb an den SDK-Konstanten —
  die schwaechere Form, im Docstring benannt statt verschwiegen.

  Beide READMEs beschreiben die Aeren; ein Test haelt jede Sprache einzeln
  dagegen — im Portfolio sind EN und DE desselben Repos schon dreimal
  auseinandergelaufen, weil nur eine Fassung nachgezogen wurde.

### Behoben

- **`README.md` hatte zwei `## Installation`-Abschnitte.** Der als
  `<!-- BEGIN GENERATED: install -->` markierte Block wurde ans Ende
  angehaengt, ohne dass jemand bemerkte, dass weiter oben bereits einer
  stand. Zwei gleichnamige Ueberschriften in einem Dokument — und der
  zweite handelt gar nicht von der Installation, sondern von der
  MCP-Client-Konfiguration.

  Die Ueberschrift heisst jetzt «MCP Client Configuration». Marker und
  JSON-Beispiel sind unveraendert.

  Anmerkung fuer spaeter: Die `GENERATED`-Marker legen ein Werkzeug nahe, das
  diesen Bereich schreibt. Im Repo gibt es keines — weder ein Skript noch ein
  Workflow beruehrt ihn. Sollte je eines dazukommen, muss es diese
  Ueberschrift kennen, sonst kehrt die Dopplung zurueck.

- **Die beiden READMEs liefen an dieser Stelle auseinander.** Den Block gab
  es nur auf Englisch. `README.de.md` fuehrt ihn jetzt ebenfalls, auf
  Deutsch; beide Dateien haben wieder dieselbe Struktur (117 Bloecke).

  Nicht gespiegelt wird der `<!-- mcp-name: … -->`-Kommentar darueber: Er ist
  die Eigentumszuordnung fuer die MCP-Registry, muss genau einmal und in
  `README.md` stehen, und ist als HTML-Kommentar fuer Leser ohnehin
  unsichtbar. Eine zweite Zuordnung waere keine Uebersetzung, sondern ein
  zweiter Anspruch.


### Behoben

- **Drei von vier UNESCO-UIS-Pfaden gaben HTTP 404 — auf jede Anfrage.**
  Gebaut wurden `/indicators`, `/geo-units` und `/data`; die Quelle fuehrt
  `/definitions/indicators`, `/definitions/geounits` und `/data/indicators`.
  Nur `/versions` stimmte.

  Sichtbar war davon nichts. Jeder betroffene Aufrufer faengt den Fehler und
  zeigt eine lokale Ersatzliste — ehrlich beschriftet mit «API nicht
  erreichbar», aber eben eine Liste. Wer den Server benutzte, sah eine
  Antwort.

- **Der Umschlag der Datenantwort wurde nie gelesen.** Gesucht wurde
  `observations`, mit `data` als zweitem Versuch und `[]` als drittem. Die
  Quelle schreibt `records`. Aus **jeder** Antwort kam damit eine leere Liste,
  und aus einem Formfehler wurde die Aussage «fuer dieses Land gibt es keine
  Daten» — vollstaendig, plausibel, formatiert und falsch. Gemessen liefert
  `CR.1`/`CHE` **14 Zeilen**.

  `uis_records()` liest jetzt `records` und trennt dabei zwei Faelle, die
  vorher denselben Ausgang hatten: Ein leeres `records` ist eine Aussage der
  Quelle und kommt als leere Liste zurueck. Ein FEHLENDES `records` ist keine
  Aussage ueber die Daten, sondern ueber die Antwort, und wird als
  `UpstreamShapeError` gemeldet.

- **12 von 22 Indikator-IDs der lokalen Tabelle gab es in der Quelle nicht:**
  alle drei `NERA.*`, alle drei `XUNIT.*`, alle drei `PTR.*`, beide `GPI.*`
  und `SDG4`. Das waren genau die Kategorien, die der Docstring von
  `uis_list_indicators` bewarb — und weil der API-Pfad zugleich 404 gab und
  der Aufrufer auf diese Tabelle zurueckfiel, war sie die einzige
  Indikatorliste, die ein Nutzer je zu sehen bekam.

  Die Tabelle fuehrt jetzt 17 gegen die Quelle gepruefte Codes. Zwei
  Kategorien fallen ersatzlos weg, weil die UIS sie nicht mehr fuehrt: das
  Schueler-Lehrer-Verhaeltnis (`PTR.*`) und ein SDG-4-Gesamtindikator. Einen
  Ersatz zu erfinden waere schlechter als eine fehlende Zeile — eine
  erfundene ID sieht aus wie eine Antwort.

- **Der Jahresfilter wurde nie angewandt.** Gesendet wurde
  `startYear`/`endYear`; die OpenAPI der Quelle deklariert `start`/`end`.
  Unbekannte Query-Parameter lehnt die UIS nicht ab — sie antwortet mit HTTP
  200 und laesst sie fallen. Eine Abfrage 2015–2018 auf `CR.1`/`CHE` lieferte
  damit alle 14 Jahre von 2006 bis 2021, und die Ausgabe schrieb das Fenster
  darueber, das nie gegriffen hatte.

- **Der Themenfilter filterte nie.** `/definitions/indicators` kennt gar
  keinen `theme`-Parameter. Belegt ist das mit einer Kontrolle:
  `theme=bogus-theme-den-es-nicht-gibt` liefert dieselben 5063 Zeilen wie
  `theme=EDUCATION` und wie gar kein Parameter. Gefiltert wird jetzt lokal
  ueber das Feld `theme` der Zeilen selbst.

- **`hints` las niemand — dabei nennt die Quelle dort den Grund im Klartext.**
  Ein unbekannter Laendercode ist kein Fehlerstatus: HTTP 200, leeres
  `records`, und daneben `{"code": "UIS::HINT::003", "message": "The geoUnit
  could not be found, XXX"}`. Ausgegeben wurde «keine Daten fuer dieses
  Land». Ein Tippfehler sah damit exakt aus wie ein Befund ueber die Welt.
  `uis_hints()` liest das Feld; alle vier Datenwerkzeuge geben es aus.

- **`uis_list_indicators` schrieb in jede Zeile ein Fragezeichen.** Gelesen
  wurde `indicatorId`, dann `id`, dann das Literal `"?"`. Die
  Definitionsliste der Quelle fuehrt `indicatorCode`. Ausgerechnet das
  Werkzeug, dessen einzige Aufgabe das Finden einer ID fuer den naechsten
  Aufruf ist, zeigte fuer alle 5063 Eintraege `?`.

  (In den DATENzeilen heisst dasselbe Feld tatsaechlich `indicatorId`. Zwei
  Namen fuer dieselbe Sache in derselben API — die Sorte Detail, die man sich
  nicht ausdenkt und deshalb aufzeichnet.)

- **Der Typfilter von `uis_list_countries` lieferte ausnahmslos nichts.**
  Verglichen wurde `entityType`; die Quelle schreibt `type`. Der Ausdruck
  stellte damit immer `"" == "NATIONAL"` an — aus 462 vorhandenen Eintraegen
  wurden null, gemeldet als «Keine geografischen Einheiten gefunden». Die
  Parameterbeschreibung bewarb ausserdem `COUNTRY`/`REGION`/`SDG_REGION`; die
  Quelle fuehrt `NATIONAL` und `REGIONAL`.

- **Die Statusspalte der Zeitreihe war in jeder Zeile leer.** Gelesen wurde
  `observationStatus`, die Quelle schreibt `qualifier`. Eine UIS-Schaetzung
  sah damit aus wie ein gemeldeter Wert — bei `LR.AG15T99` betrifft das 1306
  von 9818 Werten. Die Spalte zeigt jetzt «gemeldet», «UIS-Schaetzung» oder
  «nationale Schaetzung».

- **Die Laenderuebersicht schrieb «CHE (CHE)».** Der Klammerzusatz sollte den
  Klarnamen aus `geoUnitName` tragen; dieses Feld fuehrt eine UIS-Datenzeile
  nicht, der Ausdruck fiel auf den Code zurueck. Ausgegeben wird jetzt der
  Code, mit einem Verweis auf `uis_list_countries` fuer die Namen — ein
  erfundener Name waere die schlechtere Antwort als ein blosser Code.

### Hinzugefuegt

- **Aufgezeichnete Fixtures statt handgeschriebener** — `tests/fixtures/`,
  `scripts/record_fixtures.py`, `tests/fixture_data.py` und ein
  `PROVENANCE.md` mit Quelle, Aufzeichnungsdatum, Auswahlregel und SHA-256 je
  Datei.

  Der Anlass steht oben, aber eine Zahl gehoert daneben: Vor dieser Aenderung
  hatte dieses Repo **128 gruene Tests**, waehrend drei von vier Pfaden 404
  gaben und jede Datenabfrage leer zurueckkam. Moeglich war das, weil die
  Mocks dieselben erfundenen Feldnamen trugen wie der Produktivcode —
  `observations`, `indicatorId`, `entityType`. Ein Mock aus demselben Kopf
  kann die Annahme dieses Kopfes nicht widerlegen; wo beide irren, irren
  beide gleich, und die Suite bleibt gruen.

  Drei der neun Fixtures sind **Kontrollen**: ein erfundener `theme`-Wert,
  ein erfundener Laendercode und dieselbe Zeitreihe zweimal mit
  unterschiedlichen Parameternamen. Ohne sie belegt eine Messung nur, was ich
  bekommen habe — nicht, was die Quelle unterscheidet.

  Das Aufzeichnungsskript importiert Basis-URL und Indikatorentabelle aus dem
  Produktivcode. Ein Skript, das eine andere Adresse fragt als der Server,
  misst den falschen Gegenstand, und das faellt niemandem auf, weil das
  Ergebnis plausibel aussieht.

- **Die ersten Live-Tests dieses Repos.** `pytest -m integration` sammelte
  vorher null ein — nichts hier war je gegen die Quelle gehalten worden. Neu
  sind 17, davon 7 gegen die Produktivfunktionen selbst.

  Diese Trennung ist nicht kosmetisch: Eine erste Fassung der Live-Tests baute
  ihre URLs aus Literalen und blieb gruen, als der Pfad im Produktivcode
  testweise auf `/indicators` zurueckgesetzt wurde. Was geprueft werden soll,
  muss der Produktivcode aufbauen.

- **`tests/test_source_contract.py`** haelt die lokale Indikatorentabelle, die
  Feldnamen der Mocks und die Query-Parameter gegen die Aufzeichnung.

  Gegengeprueft mit neun gezielten Rueckmutationen — je einer pro Befund oben.
  Alle neun machen die Suite rot; ein Test, der nicht fehlschlagen kann,
  belegt nichts.

- **`scripts/check_version_sync.py` und ein CI-Schritt dafuer.** Der Check
  vergleicht `pyproject.toml` gegen `server.json` und die README-Badges und
  meldet zusaetzlich jede von Hand gepflegte Versionsnummer unter `src/`.

  Anlass ist ein Befund in genau diesem Repo: `server.json` stand auf `0.3.3`,
  waehrend `pyproject.toml` bei `0.3.4` war. Aufgefallen ist es niemandem, und
  das hat einen strukturellen Grund — `publish.yml` schreibt das Feld beim
  Veroeffentlichen aus dem Tag-Namen, die committete Zahl wirkt also nie auf
  das Artefakt und wird von nichts widerlegt. Sie ist aber die Zahl, die
  Menschen im Repo lesen.

  Dieses Repo war eines von nur zwei im Portfolio ohne diesen Check, und beide
  waren verstimmt; die uebrigen 31 tragen ihn und waren alle synchron.

  Gegengeprueft: mit dem realen Vorzustand (`server.json` auf 0.3.3) meldet der
  Check `DRIFT` und beendet sich mit Exit 1.

## [0.3.5] — 2026-07-31

### Hinzugefuegt

- **Der Server nennt jetzt seinen Namen.** Bisher ging gegenueber jedem
  Upstream der httpx-Default hinaus: der Betreiber der Datenquelle sah
  eine Bibliothek, nicht uns, und hatte keinen Weg, uns bei Fehlverhalten
  zu erreichen. Neu traegt jeden der 3 HTTP-Clients
  `global-education-mcp/<version> (+github.com/malkreide/global-education-mcp)`.

- **`__version__` kommt aus den Paket-Metadaten.** Vorher von Hand
  gepflegt bzw. gar nicht vorhanden. Ein Literal waere genau die Drift,
  die dieses Portfolio gerade ueberall beseitigt hat.

  Die Version stammt aus `importlib.metadata` und kann nicht getrennt vom
  Paket driften.

## [0.3.4] — 2026-06-07

### Changed
- Versions-Bump für ein neues PyPI-Release (0.3.3 war auf PyPI bereits
  belegt und kann laut PyPI-Policy nicht erneut hochgeladen werden).
- `__version__` in `__init__.py` mit `pyproject.toml` synchronisiert
  (stand zuvor auf `0.3.0`).

### Fixed
- Publish-Workflow setzt `skip-existing: true`, damit Re-Runs eines Tags
  nicht mehr mit `400 File already exists` fehlschlagen.

## [0.3.0] — 2026-05-21

Release nach vollständiger Umsetzung des MCP-Best-Practice-Audits
(siehe `audits/2026-05-21T094452-Z-global-education-mcp/`).

Production-Readiness gemäss Audit-Definition: ✅ erreicht.

### Added
- **FastMCP Lifespan** (SDK-001): Shared `httpx.AsyncClient` über Server-
  Laufzeit; sauberer Shutdown via `aclose()`.
- **Parallele Multi-Country-Calls** (SCALE-002): `uis_compare_countries`,
  `uis_country_education_profile`, `education_benchmark_countries` nutzen
  jetzt `asyncio.gather` mit `httpx.Limits` + Semaphore-Throttling
  (5 gleichzeitige Calls pro Upstream). ~5× schneller bei 15-Länder-Compare.
- **Tool-Signature-Lockfile** (SEC-022): `tools.lock.json` mit SHA-256
  pro Tool, CI-Verify gegen Drift; Subcommands in
  `scripts/tool_signatures.py`.
- **Tool-Description-Lint** (SEC-015): 8 Regex-Heuristiken erkennen
  Prompt-Injection-Marker; läuft im selben CI-Step.
- **Container-Sandboxing** (SEC-007): Multi-Stage `Dockerfile` (non-root
  uid 10001), `docker-compose.yml` mit `read_only`/`cap_drop ALL`/
  `no-new-privileges`, neuer CI-Smoke-Job.
- **Structured JSON Logging** (OBS-003): `logging_setup.py` mit
  RFC-5424-Severities, schreibt auf stderr (stdio-safe). `@logged_tool`
  Decorator auf allen 10 Tools.
- **Protocol vs. Execution Errors** (OBS-001):
  `api_client.raise_if_transient()` — 5xx/Timeout/Connect → `McpError`,
  4xx + andere → Tool-Result-Text.
- **FastMCP Context Injection** (SDK-003): `ctx: Optional[Context] = None`
  in den 3 Long-Running-Tools mit `ctx.info` + `ctx.report_progress` pro
  Upstream-Call. Claude Desktop zeigt jetzt Fortschritt.
- **CHANGELOG.md** (ARCH-012, dieser Eintrag).
- **CONTRIBUTING.md** erweitert um Logging-, Lockfile-, Progress- und
  Compliance-Konventionen.
- **README Compliance-Sektion** (CH-005, CH-006): ISDS-
  Schutzbedarfsklassen Stadt Zürich + Schulamt-Klassifikation BUI
  explizit dokumentiert.

### Changed
- **`MCP_HOST` Default** (SEC-006): von `0.0.0.0` auf `127.0.0.1`. Bei
  SSE-Transport plus `MCP_HOST=0.0.0.0` wird eine Warnung auf stderr
  geschrieben.
- **Dependency-Bounds**: obere Grenzen in `pyproject.toml`
  (`mcp[cli]<2.0.0`, `httpx<1.0.0`, `pydantic<3.0.0`) — bewusster
  Upgrade-Pfad bei Major-Bumps.
- **Python 3.13 Compatibility** (CI-Fix): `inspect.cleandoc()` auf
  Tool-Descriptions vor dem Hashing — Python 3.13 strippt Docstring-
  Einrückung im Compiler (PEP 257), 3.11/3.12 nicht.

## [0.2.0] — 2025-XX-XX

### Added
- Initiale Implementierung mit 10 MCP-Tools (5 UNESCO UIS, 4 OECD, 1 Cross-Source)
- 2 Resources (`education://indicators/unesco`, `education://datasets/oecd`)
- 2 Prompts (`bildungsvergleich_schweiz`, `sdg4_monitoring`)
- 113 Unit-Tests + Live-API-Integration-Tests
- Bilingualer README (EN + DE)
- Claude-Desktop-Config-Beispiel
- GitHub-Actions-CI (pytest auf Python 3.11/3.12/3.13)
- Hatchling-Build + PyPI-Publish-Workflow

[Unreleased]: https://github.com/malkreide/global-education-mcp/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/malkreide/global-education-mcp/releases/tag/v0.3.0
[0.2.0]: https://github.com/malkreide/global-education-mcp/releases/tag/v0.2.0
