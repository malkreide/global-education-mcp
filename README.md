> 🇨🇭 **Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide)**

# 🎓 global-education-mcp

![Version](https://img.shields.io/badge/version-0.3.5-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![Data: UNESCO UIS](https://img.shields.io/badge/Data-UNESCO%20UIS-blue)](https://uis.unesco.org/)
[![Data: OECD](https://img.shields.io/badge/Data-OECD%20EaG-green)](https://www.oecd.org/education/education-at-a-glance/)
[![Tests](https://img.shields.io/badge/tests-169-brightgreen)](tests/)
[![No API Key](https://img.shields.io/badge/API%20Key-not%20required-success)](https://uis.unesco.org/bdds)
![CI](https://github.com/malkreide/global-education-mcp/actions/workflows/ci.yml/badge.svg)

> MCP server for international education data – UNESCO UIS (4,000+ indicators across all member countries) and OECD Education at a Glance via SDMX. No API keys required.

[🇩🇪 Deutsche Version](README.de.md)

![global-education-mcp demo flow](assets/demo-flow.svg)

---

## Overview

**global-education-mcp** gives AI assistants like Claude a complete international education intelligence system – literacy rates, enrolment ratios, education expenditure, teacher salaries, gender parity and SDG-4 monitoring, all accessible through a single standardised MCP interface.

The server bridges two of the most authoritative sources for internationally comparable education statistics: UNESCO UIS (global coverage, 4,000+ indicators) and the OECD's annual *Education at a Glance* (38 OECD countries, SDMX REST API). Both are open and require no API key.

**Anchor demo query:** *"Compare Switzerland's education expenditure as a percentage of GDP with Finland, Singapore and South Korea over the last 10 years – and flag any SDG-4 gaps."*

---

## Features

- 🌍 **UNESCO UIS** – 4,000+ indicators, all UNESCO member countries, no API key
- 📊 **OECD Education at a Glance** – 38 OECD countries + partners via SDMX REST
- 🔍 **Indicator search** – browse and filter the full UNESCO indicator catalogue
- 🗺️ **Multi-country comparison** – benchmark any indicator across multiple countries
- 🏫 **Country education profiles** – 10 core indicators in one call
- 🎯 **SDG-4 monitoring** – structured reporting on Education for All targets
- 📈 **OECD dataset search** – discover and retrieve Education at a Glance dataflows
- 🔑 **No API keys required** – fully open data, zero setup friction
- ☁️ **Dual transport** – stdio for Claude Desktop, Streamable HTTP/SSE for cloud deployment
- 🛡️ **Graceful degradation** – API failures return helpful messages with local reference fallback

---

## Prerequisites

- Python 3.11+
- `uv` (recommended) or `pip`
- No API keys needed

---

## Installation

```bash
# Clone the repository
git clone https://github.com/malkreide/global-education-mcp.git
cd global-education-mcp

# Install
pip install -e ".[dev]"
```

Or with `uvx` (no permanent installation):

```bash
uvx global-education-mcp
```

---

## Quickstart

```bash
# Start the server (stdio mode for Claude Desktop)
global-education-mcp
```

Try it immediately in Claude Desktop:

> *"What is Switzerland's literacy rate compared to Finland and Singapore?"*
> *"Show me education expenditure as % of GDP for CHE, DEU and AUT over the last 10 years."*

---

## Configuration

### Claude Desktop Configuration

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

A ready-to-use `claude_desktop_config.json` is included in the repository root.

### Cloud Deployment (SSE for browser access)

For use via **claude.ai in the browser** (e.g. on managed workstations without local software).

> ⚠️ **Security note:** Since v0.3, `MCP_HOST` defaults to `127.0.0.1`. The
> SSE transport must **always** run behind a reverse proxy that adds TLS,
> authentication, and rate-limiting. Never expose the raw port to the
> internet — `MCP_HOST=0.0.0.0` is only safe inside an isolated
> container network.

**Docker (recommended):**

The repository ships a hardened multi-stage `Dockerfile` and a
`docker-compose.yml` that applies `read_only: true`, `cap_drop: [ALL]`,
`security_opt: [no-new-privileges:true]`, and runs as non-root user
`uid 10001`. The compose file binds the port to `127.0.0.1` so a host-level
reverse proxy is required for any external access.

```bash
docker compose up --build
# then point nginx/caddy at 127.0.0.1:8000/sse with TLS + auth
```

Plain `docker run` (without compose):

```bash
docker build -t global-education-mcp .
docker run --rm \
  --read-only --cap-drop ALL --security-opt no-new-privileges \
  --tmpfs /tmp:size=16M,mode=1777 \
  -p 127.0.0.1:8000:8000 \
  global-education-mcp
```

**Render.com:**
1. Push/fork the repository to GitHub
2. On [render.com](https://render.com): New Web Service → connect GitHub repo
3. Set environment variables in the Render dashboard:
   ```
   MCP_TRANSPORT=sse
   MCP_HOST=0.0.0.0      # Render needs 0.0.0.0; their edge layer provides TLS + auth.
   PORT=8000
   ```
4. In claude.ai under Settings → MCP Servers, add: `https://your-app.onrender.com/sse`

> 💡 *"stdio for the developer laptop, sandboxed SSE container for the browser."*

---

## Available Tools

### UNESCO UIS Tools

| Tool | Description |
|---|---|
| `uis_list_indicators` | Search and list available indicators (4,000+) |
| `uis_list_countries` | List countries and regions with ISO codes |
| `uis_get_education_data` | Retrieve data for a specific indicator |
| `uis_compare_countries` | Multi-country comparison for one indicator |
| `uis_country_education_profile` | Full education profile (10 core indicators) |
| `uis_list_versions` | List available database versions |

### OECD Tools

| Tool | Description |
|---|---|
| `oecd_list_education_datasets` | List Education at a Glance datasets |
| `oecd_get_education_indicator` | Retrieve OECD education data via SDMX |
| `oecd_search_datasets` | Search OECD dataflows by keyword |

### Cross-Source Tools

| Tool | Description |
|---|---|
| `education_benchmark_countries` | Benchmark multiple countries across 5 focus themes (UNESCO UIS) |

### Resources & Prompts

**Resources:**
- `education://indicators/unesco` – Quick reference for core UNESCO indicators
- `education://datasets/oecd` – Quick reference for OECD Education at a Glance dataflows

**Prompts:**
- `bildungsvergleich_schweiz` – Switzerland vs. Finland, Singapore, Japan
- `sdg4_monitoring` – SDG-4 report for CH/DE/AT

### Country Codes

ISO 3166-1 Alpha-3 standard:

| Code | Country | Code | Country |
|---|---|---|---|
| `CHE` | Switzerland | `FIN` | Finland |
| `DEU` | Germany | `SGP` | Singapore |
| `AUT` | Austria | `KOR` | South Korea |
| `FRA` | France | `JPN` | Japan |
| `SWE` | Sweden | `USA` | United States |

### Example Use Cases

| Query | Tool |
|---|---|
| *"What is Switzerland's literacy rate vs. Finland and Singapore?"* | `uis_compare_countries` |
| *"Education expenditure as % of GDP for CHE, DEU, AUT over 10 years"* | `uis_get_education_data` |
| *"Create a full education profile for South Korea"* | `uis_country_education_profile` |
| *"Which OECD datasets cover teacher salaries?"* | `oecd_search_datasets` |
| *"Compare secondary graduation rates across 5 European countries"* | `education_benchmark_countries` |
| *"Create an SDG-4 monitoring report for Switzerland"* | `sdg4_monitoring` (prompt) |

→ [More use cases by audience](EXAMPLES.md) →

---

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────┐     ┌────────────────────┐
│   Claude / AI   │────▶│   Global Education MCP       │────▶│   UNESCO UIS API   │
│   (MCP Host)    │◀────│   (MCP Server)               │◀────│   uis.unesco.org   │
└─────────────────┘     │                              │     └────────────────────┘
                        │  10 Tools · 2 Resources      │
                        │   · 2 Prompts                │     ┌────────────────────┐
                        │  Stdio | SSE                 │────▶│   OECD SDMX API    │
                        │                              │◀────│   sdmx.oecd.org    │
                        │  server.py                   │     └────────────────────┘
                        │   + api_client.py            │
                        └──────────────────────────────┘
```

### Infrastructure Components

| Component | Metaphor | Function |
|---|---|---|
| HTTPClient | Postal service | Handles all outbound HTTP requests, retries and timeouts |
| SimpleCache | Whiteboard | In-memory TTL cache for repeated queries |
| GracefulFallback | Safety net | Returns local reference data when APIs are unavailable |
| SDMXParser | Translator | Converts OECD SDMX/XML responses to clean JSON |

### Caching Strategy

| Data Source | Cache TTL | Rationale |
|---|---|---|
| UNESCO UIS indicators | 3600s | Catalogue is stable; updated annually |
| UNESCO UIS country data | 1800s | Figures update yearly, not intraday |
| OECD dataset list | 3600s | Education at a Glance is an annual publication |
| OECD indicator data | 1800s | Same annual update cycle |
| Country/region list | 86400s | ISO codes and country lists are highly stable |

---

## Project Structure

```
global-education-mcp/
├── src/global_education_mcp/       # Main package
│   ├── __init__.py                 # Package metadata, version
│   ├── server.py                   # FastMCP server, 10 tools, 2 resources, 2 prompts
│   └── api_client.py               # HTTP client, UNESCO UIS + OECD wrappers, formatters
├── scripts/
│   └── record_fixtures.py          # Records the fixtures from the live UIS API
├── tests/
│   ├── fixtures/                   # Recorded responses + PROVENANCE.md (source, date, SHA-256)
│   ├── fixture_data.py             # Fixture loader – raises on a missing name
│   ├── test_source_contract.py     # Contract vs. the recording + live tests
│   ├── test_server.py              # 42 tests (basic / intermediate / advanced)
│   └── test_extended_scenarios.py  # 74 tests across 8 categories
├── claude_desktop_config.json      # Ready-to-use Claude Desktop config
├── pyproject.toml                  # Build configuration (hatchling)
├── CHANGELOG.md
├── CONTRIBUTING.md                 # Contribution guide (English)
├── CONTRIBUTING.de.md              # Contribution guide (German)
├── SECURITY.md                     # Security policy (English)
├── SECURITY.de.md                  # Security policy (German)
├── LICENSE
├── README.md                       # This file (English)
└── README.de.md                    # German version
```

---

## Known Limitations

- **UNESCO UIS:** Some indicators have sparse coverage for low-income countries or recent years
- **OECD SDMX:** Occasional API timeouts on large multi-country, multi-year requests; reduce the year range if needed
- **OECD coverage:** 38 OECD members + select partners – does not cover all UNESCO member states
- **Historical depth:** UNESCO UIS data availability varies by indicator; not all series go back to 1970
- **Language:** UNESCO UIS returns indicator labels in English only; OECD labels may vary by dataflow
- **No real-time data:** Both sources publish annually – figures reflect the latest published edition, not live school statistics
- **Estimated values are labelled:** UIS marks part of its observations `UIS_EST` (UIS estimate) or `NAT_EST` (national estimate) – for `LR.AG15T99` that is 1,306 of 9,818 values. The status column names it; an unlabelled value is a reported one.
- **Data rows carry the ISO code, not the country name:** plain names come from `uis_list_countries`. The data tools print the code rather than inventing a name.
- **An unknown country code is not an error status:** UIS answers HTTP 200 with an empty result set and states the reason in the payload's `hints` field. The tools print that hint – otherwise a typo would look exactly like a country without data.

---

## Compliance & Data Classification (City of Zurich)

> Verbindliche Klassifikation für den Einsatz im Schulamt der Stadt Zürich
> (German section follows in `README.de.md`).

### ISDS Protection Class (Stadt Zürich Schutzbedarfsklassen)

| Dimension | Class | Reasoning |
|---|---|---|
| Confidentiality | public | UNESCO UIS data licensed under [CC BY-SA 3.0 IGO](https://creativecommons.org/licenses/by-sa/3.0/igo/); OECD EaG under public [OECD Terms](https://www.oecd.org/termsandconditions/) |
| Integrity | normal | Upstream is authoritative; local in-memory cache is TTL-bounded and never written to disk |
| Availability | normal | Graceful fallback to bundled static reference data when an API is unreachable |
| **Overall protection class** | **G1 — public (öffentlich)** | lowest tier per ISDS Stadt Zürich |

- Data owner: UNESCO UIS / OECD (external)
- System owner: Schulamt der Stadt Zürich
- Processes personal data: **no**
- DSG / EDÖB relevance: **none** (only anonymized country-level aggregates)

### Schulamt Classification (BUI / Vertraulich / Streng Vertraulich)

| Aspect | Classification |
|---|---|
| Tool output (Markdown tables, summaries) | **BUI** (betrieblich unkritische Information) |
| In-memory TTL cache | BUI (same tier as source) |
| Structured logs (JSON on stderr, see OBS-003) | BUI — only tool name, params, duration; no PII |
| `tools.lock.json`, `audits/` artefacts | BUI |

→ The server is approved for any Schulamt use case without additional clearance from the data protection officer.

### Compatibility

| Component | Supported version |
|---|---|
| MCP Protocol | 2024-11-05 |
| MCP Python SDK | `>=1.0.0,<2.0.0` |
| Python | 3.11, 3.12, 3.13 |
| `httpx` | `>=0.27.0,<1.0.0` |
| `pydantic` | `>=2.0.0,<3.0.0` |

Major-version upgrades are deliberate decisions — the upper bounds in
`pyproject.toml` exist so a transitive bump does not silently break the
server. See `CHANGELOG.md` for the upgrade trail.

---

## 🛡️ Safety & Limits

| Aspect | Details |
|--------|---------|
| **Access** | Read-only (`readOnlyHint: true`) — the server cannot modify, write or delete any data |
| **Personal data** | No personal data — UNESCO UIS and OECD EaG publish only aggregated, country-level statistics |
| **Rate limits** | Built-in per-query caps (max 50 indicators per search, max 10 countries per comparison, conservative year ranges) |
| **Caching** | In-memory TTL cache (1800–86400s) reduces upstream load and respects publisher capacity |
| **Timeout** | 30 seconds per upstream API call, with graceful fallback to local reference data |
| **Authentication** | No API keys required — both UNESCO UIS and OECD SDMX are publicly accessible |
| **Licenses** | UNESCO UIS data under [CC BY-SA 3.0 IGO](https://creativecommons.org/licenses/by-sa/3.0/igo/); OECD data under [OECD Terms and Conditions](https://www.oecd.org/termsandconditions/) |
| **Terms of Service** | Subject to ToS of the respective sources: [UNESCO UIS](https://uis.unesco.org/en/terms-and-conditions-use), [OECD](https://www.oecd.org/termsandconditions/) — please cite the source when redistributing |
| **Attribution** | All tool responses include source attribution (`Source: UNESCO UIS` / `Source: OECD Education at a Glance`) |

---

## MCP Protocol Version

This server speaks **two protocol eras** over the same endpoint. The client's
first request on a connection decides which one applies; a later claim from the
other era is refused.

| Era | Revision | Who reaches it |
|---|---|---|
| `initialize` handshake | `2024-11-05` … **`2025-11-25`** | What today's clients speak. The server answers with the revision asked for, or with the `2025-11-25` ceiling when the request asks for something newer. |
| Per-request envelope | **`2026-07-28`** | A request carrying the `2026-07-28` `_meta` envelope opens a modern connection. |

Both revisions are pinned in
[`tests/test_protocol_version.py`](tests/test_protocol_version.py) and asserted
against the installed SDK, so a Dependabot bump of `mcp` cannot move either one
silently. This server builds no ASGI app to send an `initialize` through, so
the gate asserts the SDK constants rather than a measured response — the
weaker form, named rather than left unsaid.

Note that the SDK's `LATEST_PROTOCOL_VERSION` is an alias for the **modern**
era, not for the handshake era — pinning against it alone would leave the era
that current clients actually negotiate free to drift.

**Update policy.** When the gate fails, do not edit the constant blindly: read
the spec changelog between the two revisions, verify the server still behaves,
then move the constant, this section, `README.de.md` and
[`CHANGELOG.md`](CHANGELOG.md) together.

---

## Testing

```bash
# Unit tests (no API key required, no network)
PYTHONPATH=src pytest tests/ -v -m "not integration"

# Full suite including the live tests against api.uis.unesco.org
PYTHONPATH=src pytest tests/ -v

# Re-record the fixtures (writes tests/fixtures/ + PROVENANCE.md)
PYTHONPATH=src python scripts/record_fixtures.py
```

**169 tests** – 152 offline, 17 against the live source.

| Category | Tests | Description |
|---|---|---|
| Edge cases & boundary values | 19 | Year limits, string lengths, null/zero values |
| Security & adversarial inputs | 14 | Injection attempts, HTTP error codes, whitespace |
| Output quality | 11 | Markdown structure, source attribution, sort order |
| Resilience & error cascades | 9 | Full API outage, partial results, timeouts |
| Subject-matter correctness | 10 | SDG-4 coverage, correct indicators per focus theme |
| Performance & concurrency | 4 | Concurrent requests, time limits |
| Schulamt scenarios | 7 | DACH comparison, PISA, teacher shortage |
| Source contract vs. the recording | 23 | Field names, envelope, query parameters, hints |
| Live tests (`-m integration`) | 17 | The paths, the shape, and the tools themselves |

### Why the fixtures are recorded rather than written

A hand-written mock encodes its author's assumption and therefore cannot
refute it: production code and fixture come from the same head, the same hour,
the same reading of the docs. Where both are wrong, both are wrong together —
and the suite stays green.

That is not a hypothetical here. Before 2026-08-08 this repo had **128 green
tests** while three of its four UNESCO paths answered HTTP 404 and every data
query returned an empty list. The mocks carried the same invented field names
as the production code (`observations`, `indicatorId`, `entityType`), so
nothing could ever contradict them.

Every fixture under `tests/fixtures/` is now a recorded response.
`PROVENANCE.md` names the source URL, the recording date, the selection rule
and the SHA-256 for each one. Without a date, "recorded" becomes
indistinguishable from "invented" after two years — the file looks the same.

Three of the fixtures are **controls**: a made-up `theme` value, a made-up
country code, and the same time series requested twice with different
parameter names. Without them a measurement only shows what *we* received; with
them it shows what the source actually distinguishes.

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change.

- Follow the existing code style (Ruff linting, Black formatting)
- Add tests for new tools (`tests/test_server.py` or `test_extended_scenarios.py`)
- Use the `@pytest.mark.integration` marker for tests that call live APIs
- Update `CHANGELOG.md` and the tool table in this README
- See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution guide

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

---

## Security

To report a vulnerability, see [SECURITY.md](SECURITY.md) ([🇩🇪 Deutsche Version](SECURITY.de.md)). Please use the private channels described there rather than public issues.

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Author

Hayal Oezkan · [github.com/malkreide](https://github.com/malkreide)

---

## Credits & Related Projects

- **Data:** [UNESCO Institute for Statistics (UIS)](https://uis.unesco.org/) – open education data for all UNESCO member states
- **Data:** [OECD Education at a Glance](https://www.oecd.org/education/education-at-a-glance/) – annual OECD education statistics via SDMX
- **Protocol:** [Model Context Protocol](https://modelcontextprotocol.io/) – Anthropic / Linux Foundation
- **Related:** [swiss-transport-mcp](https://github.com/malkreide/swiss-transport-mcp) – MCP server for Swiss public transport
- **Related:** [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) – MCP server for Zurich city open data
- **Portfolio:** [Swiss Public Data MCP Portfolio](https://github.com/malkreide)

<!-- mcp-name: io.github.malkreide/global-education-mcp -->

<!-- BEGIN GENERATED: install -->
## MCP Client Configuration

Run via [`uv`](https://docs.astral.sh/uv/)'s `uvx` — no clone or manual install needed. Add to your MCP client config (`mcpServers` for Claude Desktop, Cursor and Windsurf; use a top-level `servers` key for VS Code in `.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "global-education-mcp": {
      "command": "uvx",
      "args": [
        "global-education-mcp"
      ]
    }
  }
}
```
<!-- END GENERATED: install -->
