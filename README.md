**Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide/swiss-public-data-mcp)**

---

# Global Education Data MCP Server

[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Data Source](https://img.shields.io/badge/Data-UNESCO%20UIS-blue.svg)](https://uis.unesco.org/)
[![Data Source](https://img.shields.io/badge/Data-OECD%20Education-red.svg)](https://www.oecd.org/education/education-at-a-glance/)

**International education benchmarking via UNESCO UIS and OECD APIs**

An MCP server for accessing international education data from two of the most authoritative sources for globally comparable education statistics — no API keys required.

```
No API keys required · Dual transport (stdio + SSE) · 113 tests
```

> 🇩🇪 [Deutsche Version (README.de.md)](README.de.md)

---

## Data Sources

### UNESCO Institute for Statistics (UIS)

- **4,000+ indicators** covering education, science, culture and communication
- **All UNESCO member states** – globally comparable
- Topics: literacy, enrolment rates, educational attainment, education expenditure, teacher ratios, gender parity
- SDG-4 monitoring (quality education for all by 2030)

### OECD – Education at a Glance

- **38 OECD countries** + partner countries (incl. Switzerland, Germany, Austria)
- Annual reference work for international education comparisons
- Topics: education expenditure, enrolment rates, teacher salaries, returns to education
- Access via **SDMX REST API**

---

## Tools (10 total)

| Tool | Description | Source |
|---|---|---|
| `uis_list_indicators` | Search and list available indicators | UNESCO UIS |
| `uis_list_countries` | Countries and regions with ISO codes | UNESCO UIS |
| `uis_get_education_data` | Retrieve data for a single indicator | UNESCO UIS |
| `uis_compare_countries` | Multi-country comparison for one indicator | UNESCO UIS |
| `uis_country_education_profile` | Full education profile for a country (10 core indicators) | UNESCO UIS |
| `uis_list_versions` | List database versions | UNESCO UIS |
| `oecd_list_education_datasets` | List Education at a Glance datasets | OECD |
| `oecd_get_education_indicator` | Retrieve OECD education data via SDMX | OECD |
| `oecd_search_datasets` | Search OECD datasets | OECD |
| `education_benchmark_countries` | Benchmark multiple countries across 5 focus themes | UNESCO UIS |

**Resources:**

- `education://indicators/unesco` – Quick reference: core UNESCO indicators
- `education://datasets/oecd` – Quick reference: OECD dataflows

**Prompts:**

- `bildungsvergleich_schweiz` – Switzerland vs. Finland, Singapore, Japan
- `sdg4_monitoring` – SDG-4 report for CH / DE / AT

---

## Installation

### Prerequisites

- Python 3.11+
- `uv` (recommended) or `pip`

```bash
git clone https://github.com/malkreide/global-education-mcp
cd global-education-mcp
pip install -e ".[dev]"
```

---

## Configuration (Claude Desktop)

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

Alternatively, use the `claude_desktop_config.json` in the repository root.

---

## Cloud Deployment (Render.com / SSE)

```bash
# Set environment variables
MCP_TRANSPORT=sse
PORT=8000

# Start
global-education-mcp
```

---

## Country Codes

ISO 3166-1 Alpha-3 standard:

| Code | Country | Code | Country |
|---|---|---|---|
| `CHE` | Switzerland | `FIN` | Finland |
| `DEU` | Germany | `SGP` | Singapore |
| `AUT` | Austria | `KOR` | South Korea |
| `FRA` | France | `JPN` | Japan |
| `SWE` | Sweden | `USA` | United States |

---

## Example Queries

> "What is the literacy rate in Switzerland compared to Finland and Singapore?"

> "Show me education expenditure as % of GDP for CHE, DEU and AUT over the last 10 years."

> "Create a full education profile for South Korea."

> "Which OECD datasets are available on teacher salaries?"

> "Compare upper secondary completion rates across 5 European countries."

> "Generate an SDG-4 monitoring report for Switzerland."

---

## Architecture

```
src/global_education_mcp/
├── __init__.py        # Package metadata
├── server.py          # 10 tools · 2 resources · 2 prompts
└── api_client.py      # HTTP client · API wrappers · formatters

tests/
├── test_server.py              # 39 tests (simple / medium / complex)
└── test_extended_scenarios.py  # 74 tests across 8 categories
```

**Dual transport:** `stdio` for local Claude Desktop and `SSE` for cloud/remote deployment in a single codebase.

**Graceful degradation:** API failures return helpful error messages with fallback to local reference data — no hard crashes.

---

## Tests

```bash
# All unit tests (no live API calls)
pytest tests/ -v -m "not integration"

# With live API smoke tests
pytest tests/ -v
```

**113 tests** across two files and three complexity levels:

| Category | Tests | Description |
|---|---|---|
| Edge cases & boundary values | 19 | Year limits, string lengths, null/zero values |
| Security & adversarial | 14 | Injection attempts, HTTP error codes, whitespace |
| Output quality | 11 | Markdown structure, source attribution, ordering |
| Resilience & failure cascades | 9 | Total API failure, partial results, timeouts |
| Domain correctness | 10 | SDG-4 coverage, correct indicators per focus |
| Performance & concurrency | 4 | Concurrent requests, time limits |
| Schulamt scenarios | 7 | DACH comparison, PISA, teacher shortage |
| Live API smoke | 4 | Real endpoints (via `--integration`) |

---

## License

[MIT License](LICENSE) — © malkreide
