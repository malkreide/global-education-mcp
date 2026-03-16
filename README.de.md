Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide/swiss-public-data-mcp)

---

# Global Education Data MCP Server

[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Data Source](https://img.shields.io/badge/Data-UNESCO%20UIS-blue.svg)](https://uis.unesco.org/)
[![Data Source](https://img.shields.io/badge/Data-OECD%20Education-red.svg)](https://www.oecd.org/education/education-at-a-glance/)

**Internationaler Bildungsvergleich via UNESCO UIS und OECD APIs**

MCP-Server für den Zugriff auf internationale Bildungsdaten – zwei der wichtigsten Quellen für international vergleichbare Bildungsstatistiken. Keine API-Schlüssel erforderlich.

```
Keine API-Schlüssel erforderlich · Dual-Transport (stdio + SSE) · 113 Tests
```

> 🇬🇧 [English version (README.md)](README.md)

---

## Datenquellen

### UNESCO Institute for Statistics (UIS)

- **4'000+ Indikatoren** zu Bildung, Wissenschaft, Kultur und Kommunikation
- **Alle UNESCO-Mitgliedsländer** – global vergleichbar
- Themen: Alphabetisierung, Einschulungsraten, Schulabschlüsse, Bildungsausgaben, Lehrerquoten, Geschlechterparität
- SDG-4-Monitoring (Bildungsqualität für alle bis 2030)

### OECD – Education at a Glance

- **38 OECD-Länder** + Partnerländer (inkl. Schweiz, Deutschland, Österreich)
- Jährliches Referenzwerk für internationale Bildungsvergleiche
- Themen: Bildungsausgaben, Einschreibungsraten, Lehrergehälter, Bildungsrendite
- Zugriff via **SDMX REST API**

---

## Tools (10 gesamt)

| Tool | Beschreibung | Quelle |
|---|---|---|
| `uis_list_indicators` | Verfügbare Indikatoren suchen und auflisten | UNESCO UIS |
| `uis_list_countries` | Länder und Regionen mit ISO-Codes | UNESCO UIS |
| `uis_get_education_data` | Daten für einen Indikator abrufen | UNESCO UIS |
| `uis_compare_countries` | Mehrländervergleich für einen Indikator | UNESCO UIS |
| `uis_country_education_profile` | Vollständiges Bildungsprofil eines Landes (10 Kernindikatoren) | UNESCO UIS |
| `uis_list_versions` | Datenbankversionen auflisten | UNESCO UIS |
| `oecd_list_education_datasets` | Education at a Glance Datensätze auflisten | OECD |
| `oecd_get_education_indicator` | OECD-Bildungsdaten via SDMX abrufen | OECD |
| `oecd_search_datasets` | OECD-Datensätze durchsuchen | OECD |
| `education_benchmark_countries` | Benchmark mehrerer Länder (5 Fokusthemen) | UNESCO UIS |

**Ressourcen:**

- `education://indicators/unesco` – Schnellreferenz Kernindikatoren
- `education://datasets/oecd` – Schnellreferenz OECD Dataflows

**Prompts:**

- `bildungsvergleich_schweiz` – Schweiz vs. Finnland, Singapur, Japan
- `sdg4_monitoring` – SDG-4-Report für CH/DE/AT

---

## Installation

### Voraussetzungen

- Python 3.11+
- `uv` (empfohlen) oder `pip`

```bash
git clone https://github.com/malkreide/global-education-mcp
cd global-education-mcp
pip install -e ".[dev]"
```

---

## Konfiguration (Claude Desktop)

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

Alternativ via `claude_desktop_config.json` im Repository-Root.

---

## Cloud-Deployment (Render.com / SSE)

```bash
# Umgebungsvariablen setzen
MCP_TRANSPORT=sse
PORT=8000

# Start
global-education-mcp
```

---

## Ländercodes

ISO 3166-1 Alpha-3 Standard:

| Code | Land | Code | Land |
|---|---|---|---|
| `CHE` | Schweiz | `FIN` | Finnland |
| `DEU` | Deutschland | `SGP` | Singapur |
| `AUT` | Österreich | `KOR` | Südkorea |
| `FRA` | Frankreich | `JPN` | Japan |
| `SWE` | Schweden | `USA` | USA |

---

## Beispielanfragen

> „Wie hoch ist die Alphabetisierungsrate der Schweiz im Vergleich zu Finnland und Singapur?"

> „Zeige mir die Bildungsausgaben als % des BIP für CHE, DEU und AUT über die letzten 10 Jahre."

> „Erstelle ein vollständiges Bildungsprofil für Südkorea."

> „Welche OECD-Datensätze gibt es zu Lehrergehältern?"

> „Vergleiche die Abschlussquoten der Sekundarstufe II in 5 europäischen Ländern."

> „Erstelle einen SDG-4-Monitoring-Report für die Schweiz."

---

## Architektur

```
src/global_education_mcp/
├── __init__.py        # Paket-Metadaten
├── server.py          # 10 Tools · 2 Resources · 2 Prompts
└── api_client.py      # HTTP-Client · API-Wrapper · Formatter

tests/
├── test_server.py              # 39 Tests (einfach / mittel / komplex)
└── test_extended_scenarios.py  # 74 Tests in 8 Kategorien
```

**Dual-Transport:** `stdio` (lokale Claude Desktop) und `SSE` (Cloud) in einer Codebasis.

**Graceful Degradation:** API-Ausfälle liefern hilfreiche Fehlermeldungen mit Fallback auf lokale Referenzdaten – kein harter Absturz.

---

## Tests

```bash
# Alle Unit-Tests (ohne Live-API)
pytest tests/ -v -m "not integration"

# Mit Live-API-Smoke-Tests
pytest tests/ -v
```

**113 Tests** in zwei Dateien, drei Komplexitätsstufen:

| Kategorie | Tests | Beschreibung |
|---|---|---|
| Grenzwerte & Edge Cases | 19 | Jahresgrenzen, Stringlängen, Null/Zero-Werte |
| Sicherheit & Adversarial | 14 | Injection-Versuche, HTTP-Fehlercodes, Whitespace |
| Output-Qualität | 11 | Markdown-Struktur, Quellenangaben, Sortierung |
| Resilience & Fehlerkaskaden | 9 | API-Totalausfall, Teilergebnisse, Timeouts |
| Fachliche Korrektheit | 10 | SDG-4-Abdeckung, korrekte Indikatoren je Fokus |
| Performanz & Parallelität | 4 | Concurrent requests, Zeitlimits |
| Schulamt-Szenarien | 7 | DACH-Vergleich, PISA, Lehrpersonenmangel |
| Live API Smoke | 4 | Echte Endpunkte (via `--integration`) |

---

## Lizenz

[MIT License](LICENSE) — © malkreide
