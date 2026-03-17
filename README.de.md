[🇬🇧 English Version](README.md)

> 🇨🇭 **Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)**

# 🎓 global-education-mcp

![Version](https://img.shields.io/badge/version-1.0.0-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![Daten: UNESCO UIS](https://img.shields.io/badge/Daten-UNESCO%20UIS-blue)](https://uis.unesco.org/)
[![Daten: OECD](https://img.shields.io/badge/Daten-OECD%20EaG-green)](https://www.oecd.org/education/education-at-a-glance/)
[![Tests](https://img.shields.io/badge/Tests-113-brightgreen)](tests/)
[![Kein API-Key](https://img.shields.io/badge/API%20Key-nicht%20erforderlich-success)](https://uis.unesco.org/bdds)

> MCP-Server für internationale Bildungsdaten – UNESCO UIS (4'000+ Indikatoren für alle Mitgliedsländer) und OECD Education at a Glance via SDMX. Kein API-Key erforderlich.

---

## Übersicht

**global-education-mcp** gibt KI-Assistenten wie Claude ein vollständiges internationales Bildungsinformationssystem – Alphabetisierungsraten, Einschulungsquoten, Bildungsausgaben, Lehrergehälter, Geschlechterparität und SDG-4-Monitoring, alles über eine einzige, standardisierte MCP-Schnittstelle zugänglich.

Der Server verbindet zwei der massgeblichsten Quellen für international vergleichbare Bildungsstatistiken: UNESCO UIS (globale Abdeckung, 4'000+ Indikatoren) und das jährliche Referenzwerk *Education at a Glance* der OECD (38 OECD-Länder, SDMX REST API). Beide Quellen sind offen und erfordern keinen API-Key.

**Anker-Demo-Abfrage:** *«Vergleiche die Bildungsausgaben der Schweiz als Prozentsatz des BIP mit Finnland, Singapur und Südkorea über die letzten 10 Jahre – und hebe SDG-4-Lücken hervor.»*

---

## Funktionen

- 🌍 **UNESCO UIS** – 4'000+ Indikatoren, alle UNESCO-Mitgliedsländer, kein API-Key
- 📊 **OECD Education at a Glance** – 38 OECD-Länder + Partner via SDMX REST
- 🔍 **Indikatorensuche** – gesamten UNESCO-Indikatorenkatalog durchsuchen und filtern
- 🗺️ **Mehrländervergleich** – jeden Indikator für mehrere Länder vergleichen
- 🏫 **Bildungsprofile nach Land** – 10 Kernindikatoren in einem einzigen Aufruf
- 🎯 **SDG-4-Monitoring** – strukturierte Berichte zu den Education-for-All-Zielen
- 📈 **OECD-Datensatzsuche** – Education at a Glance Dataflows entdecken und abrufen
- 🔑 **Kein API-Key erforderlich** – vollständig offene Daten, kein Setup-Aufwand
- ☁️ **Dual Transport** – stdio für Claude Desktop, Streamable HTTP/SSE für Cloud-Deployment
- 🛡️ **Graceful Degradation** – API-Ausfälle liefern hilfreiche Fehlermeldungen mit lokalem Referenz-Fallback

---

## Voraussetzungen

- Python 3.11+
- `uv` (empfohlen) oder `pip`
- Kein API-Key erforderlich

---

## Installation

```bash
# Repository klonen
git clone https://github.com/malkreide/global-education-mcp.git
cd global-education-mcp

# Installieren
pip install -e ".[dev]"
```

Oder mit `uvx` (ohne dauerhafte Installation):

```bash
uvx global-education-mcp
```

---

## Schnellstart

```bash
# Server starten (stdio-Modus für Claude Desktop)
global-education-mcp
```

Sofort in Claude Desktop ausprobieren:

> *«Wie hoch ist die Alphabetisierungsrate der Schweiz im Vergleich zu Finnland und Singapur?»*
> *«Zeige mir die Bildungsausgaben als % des BIP für CHE, DEU und AUT über die letzten 10 Jahre.»*

---

## Konfiguration

### Claude Desktop Konfiguration

**Windows** (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "global-education": {
      "command": "uvx",
      "args": ["global-education-mcp"]
    }
  }
}
```

**macOS** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "global-education": {
      "command": "uvx",
      "args": ["global-education-mcp"]
    }
  }
}
```

Eine einsatzbereite `claude_desktop_config.json` liegt im Repository-Root.

### Cloud-Deployment (SSE für Browser-Zugriff)

Für den Einsatz via **claude.ai im Browser** (z.B. auf verwalteten Arbeitsplätzen ohne lokale Software-Installation):

**Render.com (empfohlen):**
1. Repository auf GitHub pushen/forken
2. Auf [render.com](https://render.com): New Web Service → GitHub-Repo verbinden
3. Umgebungsvariablen im Render-Dashboard setzen:
   ```
   MCP_TRANSPORT=sse
   PORT=8000
   ```
4. In claude.ai unter Settings → MCP Servers eintragen: `https://your-app.onrender.com/sse`

**Docker:**
```bash
docker build -t global-education-mcp .
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=sse \
  global-education-mcp
```

> 💡 *«stdio für den Entwickler-Laptop, SSE für den Browser.»*

---

## Verfügbare Tools

### UNESCO UIS Tools

| Tool | Beschreibung |
|---|---|
| `uis_list_indicators` | Verfügbare Indikatoren suchen und auflisten (4'000+) |
| `uis_list_countries` | Länder und Regionen mit ISO-Codes auflisten |
| `uis_get_education_data` | Daten für einen bestimmten Indikator abrufen |
| `uis_compare_countries` | Mehrländervergleich für einen Indikator |
| `uis_country_education_profile` | Vollständiges Bildungsprofil eines Landes (10 Kernindikatoren) |
| `uis_list_versions` | Verfügbare Datenbankversionen auflisten |

### OECD Tools

| Tool | Beschreibung |
|---|---|
| `oecd_list_education_datasets` | Education at a Glance Datensätze auflisten |
| `oecd_get_education_indicator` | OECD-Bildungsdaten via SDMX abrufen |
| `oecd_search_datasets` | OECD-Dataflows nach Stichwort durchsuchen |

### Quellenübergreifende Tools

| Tool | Beschreibung |
|---|---|
| `education_benchmark_countries` | Benchmark mehrerer Länder über 5 Fokusthemen (UNESCO UIS) |

### Ressourcen und Prompts

**Ressourcen:**
- `education://indicators/unesco` – Schnellreferenz für UNESCO-Kernindikatoren
- `education://datasets/oecd` – Schnellreferenz für OECD Education at a Glance Dataflows

**Prompts:**
- `bildungsvergleich_schweiz` – Schweiz vs. Finnland, Singapur, Japan
- `sdg4_monitoring` – SDG-4-Report für CH/DE/AT

### Ländercodes

ISO 3166-1 Alpha-3 Standard:

| Code | Land | Code | Land |
|---|---|---|---|
| `CHE` | Schweiz | `FIN` | Finnland |
| `DEU` | Deutschland | `SGP` | Singapur |
| `AUT` | Österreich | `KOR` | Südkorea |
| `FRA` | Frankreich | `JPN` | Japan |
| `SWE` | Schweden | `USA` | USA |

### Beispiel-Abfragen

| Abfrage | Tool |
|---|---|
| *«Alphabetisierungsrate der Schweiz vs. Finnland und Singapur?»* | `uis_compare_countries` |
| *«Bildungsausgaben als % des BIP für CHE, DEU, AUT über 10 Jahre»* | `uis_get_education_data` |
| *«Vollständiges Bildungsprofil für Südkorea erstellen»* | `uis_country_education_profile` |
| *«Welche OECD-Datensätze behandeln Lehrergehälter?»* | `oecd_search_datasets` |
| *«Abschlussquoten Sekundarstufe II in 5 europäischen Ländern vergleichen»* | `education_benchmark_countries` |
| *«SDG-4-Monitoring-Report für die Schweiz erstellen»* | `sdg4_monitoring` (Prompt) |

---

## Architektur

```
┌─────────────────┐     ┌──────────────────────────────┐     ┌────────────────────┐
│   Claude / KI   │────▶│   Global Education MCP       │────▶│   UNESCO UIS API   │
│   (MCP Host)    │◀────│   (MCP Server)               │◀────│   uis.unesco.org   │
└─────────────────┘     │                              │     └────────────────────┘
                        │  10 Tools · 2 Ressourcen     │
                        │   · 2 Prompts                │     ┌────────────────────┐
                        │  Stdio | SSE                 │────▶│   OECD SDMX API    │
                        │                              │◀────│   sdmx.oecd.org    │
                        │  server.py                   │     └────────────────────┘
                        │   + api_client.py            │
                        └──────────────────────────────┘
```

### Infrastruktur-Komponenten

| Komponente | Metapher | Funktion |
|---|---|---|
| HTTPClient | Briefzusteller | Verwaltet alle ausgehenden HTTP-Anfragen, Retries und Timeouts |
| SimpleCache | Wandtafel | In-Memory-TTL-Cache für wiederholte Abfragen |
| GracefulFallback | Sicherheitsnetz | Liefert lokale Referenzdaten bei API-Ausfall |
| SDMXParser | Dolmetscher | Wandelt OECD SDMX/XML-Antworten in sauberes JSON um |

### Caching-Strategie

| Datenquelle | Cache-TTL | Begründung |
|---|---|---|
| UNESCO UIS Indikatoren | 3600s | Katalog ist stabil; jährliche Aktualisierung |
| UNESCO UIS Länderdaten | 1800s | Kennzahlen aktualisieren jährlich, nicht unterjährig |
| OECD Datensatzliste | 3600s | Education at a Glance erscheint jährlich |
| OECD Indikatordaten | 1800s | Gleicher Jahres-Update-Zyklus |
| Länder-/Regionenliste | 86400s | ISO-Codes und Länderlisten sind sehr stabil |

---

## Projektstruktur

```
global-education-mcp/
├── src/global_education_mcp/       # Hauptpaket
│   ├── __init__.py                 # Paket-Metadaten, Version
│   ├── server.py                   # FastMCP-Server, 10 Tools, 2 Ressourcen, 2 Prompts
│   └── api_client.py               # HTTP-Client, UNESCO UIS + OECD Wrapper, Formatter
├── tests/
│   ├── test_server.py              # 39 Tests (einfach / mittel / komplex)
│   └── test_extended_scenarios.py  # 74 Tests in 8 Kategorien
├── claude_desktop_config.json      # Einsatzbereite Claude Desktop Konfiguration
├── pyproject.toml                  # Build-Konfiguration (hatchling)
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md                       # Englische Hauptversion
└── README.de.md                    # Diese Datei (Deutsch)
```

---

## Bekannte Einschränkungen

- **UNESCO UIS:** Für einige Indikatoren ist die Abdeckung bei einkommensschwachen Ländern oder aktuellen Jahren lückenhaft
- **OECD SDMX:** Bei grossen Mehrländer- und Mehrjahres-Anfragen können gelegentlich Timeouts auftreten; in diesem Fall den Jahreszeitraum einschränken
- **OECD-Abdeckung:** 38 OECD-Mitglieder + ausgewählte Partner – nicht alle UNESCO-Mitgliedsstaaten sind enthalten
- **Historische Tiefe:** Die Datenverfügbarkeit der UNESCO UIS variiert je nach Indikator; nicht alle Zeitreihen reichen bis 1970 zurück
- **Sprache:** UNESCO UIS liefert Indikatorbezeichnungen nur auf Englisch; OECD-Labels können je nach Dataflow variieren
- **Keine Echtzeitdaten:** Beide Quellen veröffentlichen jährlich – die Zahlen entsprechen der neuesten publizierten Ausgabe, nicht aktuellen Schulstatistiken

---

## Tests

```bash
# Unit-Tests (kein API-Key, keine Netzwerkverbindung erforderlich)
PYTHONPATH=src pytest tests/ -v -m "not integration"

# Vollständige Testsuite inkl. Live-API-Smoke-Tests
PYTHONPATH=src pytest tests/ -v
```

**113 Tests** in zwei Dateien und drei Komplexitätsstufen:

| Kategorie | Tests | Beschreibung |
|---|---|---|
| Grenzwerte & Edge Cases | 19 | Jahresgrenzen, Stringlängen, Null/Zero-Werte |
| Sicherheit & Adversarial | 14 | Injection-Versuche, HTTP-Fehlercodes, Whitespace |
| Output-Qualität | 11 | Markdown-Struktur, Quellenangaben, Sortierung |
| Resilience & Fehlerkaskaden | 9 | API-Totalausfall, Teilergebnisse, Timeouts |
| Fachliche Korrektheit | 10 | SDG-4-Abdeckung, korrekte Indikatoren je Fokus |
| Performanz & Parallelität | 4 | Concurrent Requests, Zeitlimits |
| Schulamt-Szenarien | 7 | DACH-Vergleich, PISA, Lehrpersonenmangel |
| Live API Smoke Tests | 4 | Echte Endpunkte (via `--integration`-Flag) |

---

## Mitwirken

Beiträge sind willkommen. Bitte öffne zuerst ein Issue, um zu besprechen, was du ändern möchtest.

- Bestehenden Code-Stil einhalten (Ruff Linting, Black Formatierung)
- Tests für neue Tools hinzufügen (`tests/test_server.py` oder `test_extended_scenarios.py`)
- `@pytest.mark.integration` für Tests verwenden, die Live-APIs aufrufen
- `CHANGELOG.md` und die Tool-Tabelle in diesem README aktualisieren
- Vollständiger Beitragsleitfaden: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md)

---

## Lizenz

MIT-Lizenz – siehe [LICENSE](LICENSE)

---

## Autor

Hayal Oezkan · [github.com/malkreide](https://github.com/malkreide)

---

## Credits & Verwandte Projekte

- **Daten:** [UNESCO Institute for Statistics (UIS)](https://uis.unesco.org/) – offene Bildungsdaten für alle UNESCO-Mitgliedsstaaten
- **Daten:** [OECD Education at a Glance](https://www.oecd.org/education/education-at-a-glance/) – jährliche OECD-Bildungsstatistiken via SDMX
- **Protokoll:** [Model Context Protocol](https://modelcontextprotocol.io/) – Anthropic / Linux Foundation
- **Verwandt:** [swiss-transport-mcp](https://github.com/malkreide/swiss-transport-mcp) – MCP-Server für den Schweizer öffentlichen Verkehr
- **Verwandt:** [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) – MCP-Server für Zürcher Stadtdaten
- **Portfolio:** [Swiss Public Data MCP Portfolio](https://github.com/malkreide)
