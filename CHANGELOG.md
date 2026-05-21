# Changelog

Alle nennenswerten Änderungen werden hier dokumentiert.

Format basiert auf [Keep a Changelog 1.1.0](https://keepachangelog.com/de/1.1.0/);
Versionierung folgt [Semantic Versioning 2.0](https://semver.org/lang/de/).

## [Unreleased]

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
