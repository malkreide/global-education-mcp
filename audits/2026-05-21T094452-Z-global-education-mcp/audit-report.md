# MCP-Server Audit-Report — `global-education-mcp`

**Audit-Datum:** 
**Skill-Version:** 1.0.0
**Catalog-Version:** ?

---

## 1. Executive Summary

Server `global-education-mcp` wurde gegen 36 anwendbare Best-Practice-Checks geprüft. 24 bestanden, 12 Findings dokumentiert (0 critical, 8 high, 4 medium, 0 low). Production-Readiness: NICHT erreicht — blockierend: SDK-001, SEC-007, SEC-022.

**Production-Readiness:** NO

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `global-education-mcp` |
| Audit-Datum | ? |
| Skill-Version | 1.0.0 |
| Catalog-Version | ? |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| arch | 10 | 0 | 1 | 0 | 0 |
| ch | 0 | 0 | 2 | 0 | 0 |
| obs | 2 | 1 | 1 | 0 | 0 |
| ops | 3 | 0 | 0 | 0 | 0 |
| scale | 0 | 0 | 1 | 0 | 1 |
| sdk | 2 | 2 | 0 | 0 | 0 |
| sec | 7 | 2 | 2 | 0 | 4 |
| **Total** | **24** | **5** | **7** | **0** | **5** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| CH-005 | ch | high | partial |
| CH-006 | ch | high | partial |
| OBS-001 | obs | high | partial |
| SCALE-002 | scale | high | partial |
| SDK-001 | sdk | high | fail |
| SEC-006 | sec | high | partial |
| SEC-007 | sec | high | fail |
| SEC-022 | sec | high | fail |
| ARCH-012 | arch | medium | partial |
| OBS-003 | obs | medium | fail |
| SDK-003 | sdk | medium | fail |
| SEC-015 | sec | medium | partial |

**Gesamt:** 12 Findings

---

## 5. Detail-Findings

### ARCH-012

## Finding: ARCH-012 — protocolVersion-Pinning + CHANGELOG + SDK-Update-Disziplin

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `ARCH-012` |
| **PDF-Reference** | Sec 2.12 |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

- `README.md:261` und `README.de.md:248-265` referenzieren `CHANGELOG.md` in der Projekt-Struktur, aber die Datei existiert **nicht** im Repo (`find . -iname "CHANGELOG*"` → 0 Treffer).
- `pyproject.toml:23` pinnt `mcp[cli]>=1.0.0` (untere Grenze ok), aber keine obere Grenze — bei Breaking-Changes in MCP-SDK 2.x würde der Server unkontrolliert mitwandern.
- Kein expliziter `protocolVersion`-Pin gegenüber dem MCP-Protokoll (FastMCP wählt Default).

### Expected Behavior

- `CHANGELOG.md` im Repo-Root, Format "Keep a Changelog" (Unreleased / 0.2.0 / 0.1.0).
- Dependency `mcp[cli]>=1.0.0,<2.0.0` (oder explizit `==1.x.x` für deterministische Reproduzierbarkeit).
- README-Sektion "Compatibility" mit MCP-Protocol-Version-Matrix.

### Evidence

- `find /home/user/global-education-mcp -iname "CHANGELOG*"` → 0 Treffer
- `README.md:261` listet `CHANGELOG.md` in der Project-Structure-Box → Doku-Lüge
- `pyproject.toml:23` — `"mcp[cli]>=1.0.0"` ohne obere Grenze
- README.de.md:334 hat einen Abschnitt "## Changelog" mit Verweis "siehe CHANGELOG.md" — der ins Leere zeigt

### Risk Description

- **Vertrauen:** User klickt auf den CHANGELOG-Link in der Doku und findet nichts → wirkt unprofessionell.
- **Breaking-Update-Risiko:** Beim nächsten MCP-SDK-Major-Bump (1.x → 2.x) kann pip einen inkompatiblen SDK installieren; Server bricht für alle User.

### Remediation

**Schritt 1:** CHANGELOG.md anlegen.

```markdown
# Changelog

Alle nennenswerten Änderungen werden hier dokumentiert.
Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]
### Added
- ...

## [0.2.0] — 2025-XX-XX
### Added
- 10 MCP-Tools für UNESCO UIS + OECD Education at a Glance
- Bilingualer README (EN + DE)
- 113 Unit- + Integrations-Tests

## [0.1.0] — 2025-XX-XX
### Added
- Initial release
```

**Schritt 2:** `pyproject.toml` Dependency-Bound:

```toml
dependencies = [
    "mcp[cli]>=1.0.0,<2.0.0",
    "httpx>=0.27.0,<1.0.0",
    "pydantic>=2.0.0,<3.0.0",
]
```

**Schritt 3:** Compatibility-Sektion im README:

```markdown
## Compatibility

| Component | Version |
|---|---|
| MCP Protocol | 2024-11-05 |
| MCP Python SDK | 1.x |
| Python | 3.11, 3.12, 3.13 |
```

### Effort Estimate

**S** (< 1 Tag) — CHANGELOG schreiben, pyproject bumpen, README ergänzen.


### CH-005

## Finding: CH-005 — ISDS Stadt Zürich Schutzbedarfsklasse-Mapping

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `CH-005` |
| **PDF-Reference** | Custom CH-Compliance |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

README.md:286 deklariert `"No personal data — only aggregated country-level statistics"`. Das ist inhaltlich korrekt, mapped aber nicht explizit auf das ISDS-Schema der Stadt Zürich. Es fehlt:

- Schutzbedarfs-Klassifizierung (öffentlich / intern / vertraulich / streng vertraulich)
- Bewertung der drei ISDS-Dimensionen (Vertraulichkeit / Integrität / Verfügbarkeit)
- Verantwortlichkeits-Eintrag (Daten-Owner, System-Owner)

### Expected Behavior

README-Sektion "ISDS-Klassifikation" mit Tabelle:

| Dimension | Stufe | Begründung |
|---|---|---|
| Vertraulichkeit | öffentlich | UNESCO/OECD veröffentlichen die Daten unter CC BY-SA 3.0 IGO bzw. OECD ToC |
| Integrität | normal | Upstream-Daten sind authoritativ, aber Cache-Misuse möglich |
| Verfügbarkeit | normal | Server hat Graceful-Fallback bei API-Ausfall |
| **Gesamt-Klasse** | **öffentlich (G1)** | niedrigste Schutzbedarfsklasse |

### Evidence

- README.md/README.de.md enthalten keine ISDS-/Schutzbedarfs-Sektion
- `pyproject.toml` Autor: "Schulamt der Stadt Zürich" → Stadt-Zürich-Compliance ist relevant
- "🛡️ Safety & Limits"-Sektion behandelt Operational Limits, nicht aber das ISDS-Schema

### Risk Description

- **Compliance-Lücke:** Bei einem internen Audit der Stadt Zürich oder einem ISDS-Review kann der Server nicht ohne weitere Klassifikations-Arbeit zugelassen werden.
- **Nutzungs-Unklarheit:** Schulamt-Mitarbeitende wissen nicht, ob sie den Server für vertrauliche Recherchen einsetzen dürfen (sie dürfen — aber das muss dokumentiert sein).

### Remediation

README.md / README.de.md ergänzen um eine Sektion "## Compliance & Klassifikation":

```markdown
## Compliance & ISDS-Klassifikation (Stadt Zürich)

| Dimension | Stufe | Begründung |
|---|---|---|
| Vertraulichkeit | öffentlich | UNESCO UIS CC BY-SA 3.0 IGO, OECD ToC |
| Integrität | normal | Upstream-authoritativ, lokales Caching nur TTL-basiert |
| Verfügbarkeit | normal | Graceful Fallback auf statische Referenzdaten |
| **Schutzbedarfsklasse** | **G1 (öffentlich)** | niedrigste Klasse |

- Daten-Owner: UNESCO UIS / OECD (extern)
- System-Owner: Schulamt der Stadt Zürich
- Verarbeitet PII: nein
- DSG/EDÖB-relevant: nein (anonymisierte Aggregate)
```

### Effort Estimate

**S** (< 1 Tag) — Doku-Ergänzung, Review mit Datenschutz-Verantwortlichem.


### CH-006

## Finding: CH-006 — Schulamt Klassifikationsschema: BUI/Vertraulich/Streng-Vertraulich

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `CH-006` |
| **PDF-Reference** | Custom CH-Compliance |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

Schulamt-spezifisches Klassifikationsschema (BUI = "betrieblich unkritische Information" / Vertraulich / Streng vertraulich) wird in der Doku nicht angesprochen.

### Expected Behavior

Explizite Aussage in README, dass die vom Server gelieferten Daten **BUI** sind (siehe CH-005 Finding) — und damit für Schulamt-Use-Cases freigegeben sind. Bei Cross-Source-Tools (`education_benchmark_countries`) wäre ein Hinweis hilfreich, dass aggregierte UNESCO+OECD-Statistiken weiterhin BUI bleiben.

### Evidence

- README ohne BUI-Hinweis
- Schulamt-Kontext im Audit-Profil aktiviert (`schulamt_context: true`)

### Risk Description

- **Adoption-Hürde:** Schulamt-Mitarbeitende fragen Datenschutz-Beauftragte vor jedem Einsatz; ohne BUI-Stempel im README dauert die interne Freigabe Wochen.

### Remediation

Im README-Compliance-Abschnitt (siehe CH-005-Remediation) zusätzlich:

```markdown
### Schulamt-Klassifikation

| Aspekt | Klassifikation |
|---|---|
| Server-Output | **BUI** (betrieblich unkritische Information) |
| Cache-Inhalt | BUI (gleiche Klasse wie Quelle) |
| Logs (nach OBS-003-Fix) | BUI (nur Tool-Namen + Tool-Params, keine PII) |

Damit ist der Server für jeden Schulamt-Use-Case ohne weitere Freigabe einsetzbar.
```

### Effort Estimate

**S** (< 0.5 Tag) — gleicher Doku-PR wie CH-005.


### OBS-001

## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `OBS-001` |
| **PDF-Reference** | Sec 6.1 |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

Alle Tools fangen Exceptions und geben formatierte Strings zurück (`handle_api_error()`), z.B.:

```python
# server.py:330-357
try:
    raw_data = await uis_get_data(...)
    ...
except Exception as e:
    return handle_api_error(e, context=f"uis_get_data({params.indicator_id})")
```

Damit wird **jeder** Fehler — auch klare Protocol-Fehler wie ungültige Params oder unbekannte Indikatoren — als Tool-Result zurückgegeben statt als MCP-Protocol-Error (`isError: true`).

### Expected Behavior

Trennung gemäss MCP-Spec:
- **Execution-Errors** (Upstream-API timeout/503, Daten nicht gefunden): als Tool-Result-Text → User sieht's
- **Protocol-Errors** (ungültige Input-Schema-Werte, unbekannter Indikator-Format): MCP-Error raisen oder `isError: true` setzen → Host kann darauf reagieren

### Evidence

- `server.py` — alle 10 Tools haben `except Exception as e: return handle_api_error(...)` Pattern
- Pydantic-Validation-Errors greifen implizit (FastMCP wandelt sie in MCP-Errors), aber nirgends explizit dokumentiert
- `handle_api_error` (api_client.py:210) unterscheidet bereits HTTP-Status-Codes — die Logik für die Klassifikation existiert, wird aber nicht für die Status-Differenzierung genutzt

### Risk Description

- **LLM-Verwirrung:** Wenn ein Indikator nicht existiert, kommt eine deutsche Fehlermeldung als "valider" Tool-Result zurück — Claude wertet das als Daten und kann halluzinieren ("Laut Server hat die Schweiz Alphabetisierungsrate: Fehler [HTTP 404]…").
- **Keine Retry-Signale:** Bei transienten Fehlern (503, Timeout) bekommt der Host keinen retry-fähigen Error-Code, der User muss manuell wiederholen.

### Remediation

```python
# server.py — Beispiel uis_get_education_data
from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS

async def uis_get_education_data(params: UISDataInput) -> str:
    try:
        raw_data = await uis_get_data(...)
    except httpx.HTTPStatusError as e:
        if 400 <= e.response.status_code < 500:
            # Client-Error (z.B. 404 unknown indicator) → Tool-Result mit Text
            return f"_Indikator '{params.indicator_id}' nicht verfügbar. Liste mit `uis_list_indicators` prüfen._"
        # Server-Error (5xx) → transient, MCP-Error raisen (Host kann retryen)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"UNESCO API {e.response.status_code}"))
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"UNESCO API unreachable: {type(e).__name__}"))
    ...
```

Plus: README-Sektion "Error Handling" mit Tabelle (HTTP-Code → MCP-Behaviour).

### Effort Estimate

**M** (1–3 Tage) — 10 Tool-Bodies refactoren, Tests anpassen, Doku ergänzen.


### OBS-003

## Finding: OBS-003 — Structured Logging mit RFC 5424 Severity-Stufen

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `OBS-003` |
| **PDF-Reference** | Sec 6.2 |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

`api_client.py:12` deklariert einen Logger:

```python
logger = logging.getLogger(__name__)
```

…aber `grep -rn "logger\." src/` ergibt **0 Aufrufe**. Es gibt weder `basicConfig`-Setup noch JSON-Formatter noch `structlog`. `pyproject.toml` listet keine Logging-Bibliothek.

### Expected Behavior

Strukturiertes Logging im JSON-Format mit RFC-5424-Severity-Mapping, damit SIEM/Loki/Splunk Felder direkt indizieren können:

```json
{"ts":"2026-05-21T09:44:52Z","level":"info","tool":"uis_get_education_data","duration_ms":482,"status":"ok","indicator":"LR.AG15T99","country":"CHE"}
```

### Evidence

- `src/global_education_mcp/api_client.py:12` — Logger deklariert
- `grep -rn "logger\.\(info\|warning\|error\|debug\)" src/` → 0 Treffer
- `grep -rn "basicConfig\|dictConfig\|structlog" src/ pyproject.toml` → 0 Treffer
- Tool-Calls erzeugen keinen Audit-Trail → bei Schulamt-Compliance-Audits keine Nachvollziehbarkeit

### Risk Description

- **Keine Observability:** Bei Production-Issues (UNESCO-API langsam, OECD-Timeout-Häufung) gibt es keine Metriken, keine Logs.
- **Schulamt-Compliance:** ISDS / DSG-Audits verlangen lückenloses Logging von Datenzugriffen. Aktuell unmöglich nachzuweisen, wer wann welchen Indikator abgefragt hat.
- **Tooling-Debt:** Logger existiert, wird aber nicht genutzt — Doku-Lüge im Code.

### Remediation

```python
# src/global_education_mcp/logging_setup.py (neu)
import logging, json, sys, time
from logging import LogRecord

class JSONFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for k, v in getattr(record, "extra_fields", {}).items():
            payload[k] = v
        return json.dumps(payload, ensure_ascii=False)

def configure(level: str = "INFO") -> None:
    h = logging.StreamHandler(sys.stderr)  # stdio-safe
    h.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers = [h]
    root.setLevel(level)
```

```python
# server.py — in main()
from .logging_setup import configure
configure(os.environ.get("LOG_LEVEL", "INFO"))
```

Pro Tool-Call (in einem Decorator oder Middleware):

```python
logger.info("tool_call", extra={"extra_fields": {
    "tool": "uis_get_education_data",
    "duration_ms": int((time.time() - start) * 1000),
    "indicator": params.indicator_id,
    "status": "ok",
}})
```

### Effort Estimate

**S** (< 1 Tag) — Logging-Setup-Modul + Tool-Call-Decorator + Tests dass logs auf stderr (nicht stdout) gehen.


### SCALE-002

## Finding: SCALE-002 — Concurrent-Request-Limits + Backpressure

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `SCALE-002` |
| **PDF-Reference** | Sec 5.2 |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

- `api_client.py:67` — globaler Timeout (30s/connect 10s) ist gesetzt ✓
- `uis_compare_countries` (server.py:415) — sequenzielle `for code in params.country_codes[:15]` Schleife ohne Bulk-Limit / Semaphore
- `education_benchmark_countries` (server.py:961-985) — pro Datenquelle separate Schleifen, kein gemeinsames Throttle
- Kein `httpx.Limits(max_connections=...)` konfiguriert

### Expected Behavior

```python
TIMEOUT = httpx.Timeout(30.0, connect=10.0)
LIMITS = httpx.Limits(max_connections=10, max_keepalive_connections=5)
client = httpx.AsyncClient(timeout=TIMEOUT, limits=LIMITS)

# Pro Tool ein Semaphore zur Begrenzung paralleler Upstream-Calls
_uis_semaphore = asyncio.Semaphore(5)

async def uis_get_data(...):
    async with _uis_semaphore:
        return await client.get(...)
```

### Evidence

- `api_client.py:78,90` — neuer Client pro Request (siehe SDK-001) und keine `Limits`-Konfiguration
- Tool `uis_compare_countries` mit `max_length=15` für country_codes → bis zu 15 parallele Calls möglich wenn man auf asyncio.gather refactort

### Risk Description

- **Quota-Verbrauch:** UNESCO UIS API hat unbekannte Rate-Limits; 15 parallele Calls könnten zu HTTP 429 führen → schlechte UX.
- **Resource-Exhaustion bei SSE-Deployment:** Mehrere parallel verbundene Clients × 15 parallele Upstream-Calls = potentiell hunderte Sockets.

### Remediation

Mit dem SDK-001-Lifespan-Fix den Client einmal mit `Limits` initialisieren, plus pro Tool-Boundary Semaphore-Limit. Bei `uis_compare_countries` zusätzlich `asyncio.gather` (parallel) mit Semaphore statt sequenzieller Schleife — schnellere Calls, gedeckelte Last.

### Effort Estimate

**S** (< 1 Tag) — gemeinsam mit SDK-001 (Lifespan + Limits).


### SDK-001

## Finding: SDK-001 — FastMCP Lifespan via @asynccontextmanager + AsyncExitStack

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `SDK-001` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

Der Server definiert keinen FastMCP-Lifespan-Context. `httpx.AsyncClient` wird stattdessen pro Request neu instanziert:

```python
# src/global_education_mcp/api_client.py:71-82
async def http_get_json(url, params=None, headers=None):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(url, params=params, headers=request_headers)
        ...
```

`grep -rn "lifespan\|AsyncExitStack\|asynccontextmanager" src/` ergibt **0 Treffer**.

### Expected Behavior

FastMCP-Server sollen einen Lifespan-Context definieren, in dem teure Ressourcen (HTTP-Client, DB-Pool) einmalig erstellt und sauber heruntergefahren werden:

```python
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP

@asynccontextmanager
async def lifespan(server):
    client = httpx.AsyncClient(timeout=TIMEOUT)
    try:
        yield {"http": client}
    finally:
        await client.aclose()

mcp = FastMCP("global_education_mcp", lifespan=lifespan, ...)
```

### Evidence

- Datei: `src/global_education_mcp/api_client.py:71-94` — neuer `AsyncClient` pro Call
- Datei: `src/global_education_mcp/server.py:40-55` — `FastMCP(...)` ohne `lifespan=`-Parameter
- grep: `lifespan|AsyncExitStack|asynccontextmanager` → 0 Treffer in `src/`

### Risk Description

- **Performance:** Bei `uis_compare_countries` (bis zu 15 Länder × 1 Call) und `uis_country_education_profile` (10 sequenzielle Calls) wird pro Iteration ein neuer Connection-Pool + TLS-Handshake aufgebaut. Latenz steigt 3–5× gegenüber persistentem Client.
- **Connection-Exhaustion:** Bei SSE-Deployment unter Last können sich Sockets im `TIME_WAIT` ansammeln.
- **Kein graceful shutdown:** Bei Server-Stop bleiben offene Verbindungen unsauber zurück (kein Aufruf von `aclose()`).

### Remediation

```python
# src/global_education_mcp/server.py — am Anfang
from contextlib import asynccontextmanager
import httpx
from . import api_client

@asynccontextmanager
async def lifespan(server):
    client = httpx.AsyncClient(timeout=api_client.TIMEOUT)
    api_client.set_shared_client(client)  # neue Setter-Funktion
    try:
        yield
    finally:
        await client.aclose()
        api_client.set_shared_client(None)

mcp = FastMCP("global_education_mcp", lifespan=lifespan, instructions=..., host=..., port=...)
```

```python
# src/global_education_mcp/api_client.py — refactor
_shared_client: Optional[httpx.AsyncClient] = None

def set_shared_client(client): 
    global _shared_client
    _shared_client = client

async def http_get_json(url, params=None, headers=None):
    if _shared_client is None:
        # Fallback für Test-Pfade, die ohne Lifespan laufen
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            return await _do_get(c, url, params, headers)
    return await _do_get(_shared_client, url, params, headers)
```

### Effort Estimate

**S** (< 1 Tag) — Lifespan-Definition + Refactor von `http_get_json/text` + Test-Anpassung.


### SDK-003

## Finding: SDK-003 — Context Injection für Progress Reports und Logging

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `SDK-003` |
| **PDF-Reference** | Sec 3.3 |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

Keines der 10 Tools nutzt FastMCP-Context-Injection. `grep -rn "ctx: Context\|ctx\.\(info\|report_progress\)" src/` ergibt 0 Treffer. Long-Running-Tools führen viele sequenzielle Calls aus, ohne dem Host (Claude Desktop) Progress zu melden:

- `uis_compare_countries` (`server.py:399`) — bis zu 15 sequenzielle UIS-Calls
- `uis_country_education_profile` (`server.py:489`) — 10 sequenzielle Calls
- `education_benchmark_countries` (`server.py:885`) — Cross-Source (UNESCO + OECD)

### Expected Behavior

```python
from mcp.server.fastmcp import Context

@mcp.tool(...)
async def uis_compare_countries(params: UISCompareInput, ctx: Context) -> str:
    for i, code in enumerate(params.country_codes):
        await ctx.report_progress(i, len(params.country_codes), f"Querying {code}")
        await ctx.info(f"UIS fetch: indicator={params.indicator_id}, geo={code}")
        ...
```

### Evidence

- `src/global_education_mcp/server.py:399-466` — Schleife über country_codes ohne Progress-Report
- `src/global_education_mcp/server.py:489-563` — 10 sequenzielle uis_get_data-Aufrufe ohne ctx.info
- `grep -rn "Context\|ctx\." src/` → 0 Treffer

### Risk Description

- **Schlechte UX:** Bei langsamen UNESCO/OECD-APIs (30s Timeout pro Call × 15 Länder = bis zu 7.5 min Wartezeit) sieht der User keinen Progress.
- **Debugging-Defizit:** Keine MCP-Logs des Servers im Claude-Desktop-Log-Stream — Issue-Reports schwer reproduzierbar.
- **Cancellation:** Ohne Progress kann der User nicht entscheiden, ob er den Call abbrechen soll.

### Remediation

```python
# server.py — uis_compare_countries
from mcp.server.fastmcp import Context

async def uis_compare_countries(params: UISCompareInput, ctx: Context) -> str:
    indicator_name = UNESCO_EDUCATION_INDICATORS.get(params.indicator_id, params.indicator_id)
    results, errors = [], []
    total = len(params.country_codes[:15])
    for i, code in enumerate(params.country_codes[:15], 1):
        await ctx.report_progress(i - 1, total, f"Querying {code}")
        try:
            ...
            await ctx.info(f"OK: {code} = {latest.get('value')}")
        except Exception as e:
            errors.append(f"{code}: {handle_api_error(e)}")
            await ctx.warning(f"Skip {code}: {e}")
    await ctx.report_progress(total, total, "Done")
```

Analog für `uis_country_education_profile` und `education_benchmark_countries`.

### Effort Estimate

**S** (< 1 Tag) — 3 Tools refactoren + Tests anpassen (Mock-Context).


### SEC-006

## Finding: SEC-006 — Lokaler Server: stdio-Transport zwingend (Netzwerk-Isolation)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `SEC-006` |
| **PDF-Reference** | Sec 4.6 |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

stdio ist Default (`server.py:1052: transport = os.environ.get("MCP_TRANSPORT", "stdio")`), aber:

```python
# server.py:53-54
host=os.environ.get("MCP_HOST", "0.0.0.0"),
port=int(os.environ.get("PORT", "8000")),
```

Bei `MCP_TRANSPORT=sse` bindet der Server auf **0.0.0.0** — alle Netzwerk-Interfaces. README.md:121-145 dokumentiert "Cloud Deployment (SSE for browser access)" ohne TLS-/Auth-/Reverse-Proxy-Warnung.

### Expected Behavior

- stdio bleibt Default ✓
- SSE-Mode bindet auf `127.0.0.1` per Default (nicht 0.0.0.0)
- README-Hinweis: SSE-Mode nur hinter Reverse-Proxy mit TLS + Auth nutzen

### Evidence

- `server.py:53` — `host = "0.0.0.0"`
- `server.py:1053-1056` — bei `sse` keine Auth/TLS-Konfiguration
- `README.md:121-145` — Cloud-Deployment-Sektion ohne Security-Hinweis
- Kein Reverse-Proxy-Beispiel (nginx/caddy) in der Doku

### Risk Description

- **Unbeabsichtigte Netzwerk-Exposition:** User testet schnell `MCP_TRANSPORT=sse python -m global_education_mcp.server` auf seinem Laptop in einem Schulamt-WLAN → Server ist für alle im LAN erreichbar.
- **Keine Authentifizierung:** Jeder im Netzwerk kann die 10 Tools aufrufen (read-only, aber Logs/Tracking könnten sensitiv werden bei strukturiertem Logging).
- **DoS:** Ohne Rate-Limiting kann jeder Netzwerk-Teilnehmer den Server gegen UNESCO/OECD-Quotas laufen lassen.

### Remediation

**Schritt 1:** Default-Host auf 127.0.0.1.

```python
# server.py:53
host=os.environ.get("MCP_HOST", "127.0.0.1"),
```

**Schritt 2:** Warnung bei 0.0.0.0 + non-stdio.

```python
def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    if transport != "stdio" and host == "0.0.0.0":
        import sys, warnings
        warnings.warn(
            "MCP_HOST=0.0.0.0 with SSE transport exposes the server to the network "
            "without auth/TLS. Use a reverse proxy. To dismiss, set MCP_HOST=127.0.0.1.",
            RuntimeWarning,
        )
    ...
```

**Schritt 3:** README "Cloud Deployment"-Sektion erweitern um Reverse-Proxy-Beispiel + TLS + Auth-Hinweis.

### Effort Estimate

**S** (< 1 Tag) — 3-Zeilen-Default-Change + Warnung + README-Update.


### SEC-007

## Finding: SEC-007 — Container-Sandboxing: Docker / chroot mit minimalen Privilegien

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `SEC-007` |
| **PDF-Reference** | Sec 4.7 |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

Repo enthält **keine** Container-Konfiguration. `find . -iname "Dockerfile*" -o -iname "docker-compose*" -o -iname "*.dockerfile"` ergibt 0 Treffer. README.md:121 dokumentiert ein "Cloud Deployment (SSE for browser access)" ohne Sandboxing-Anleitung.

### Expected Behavior

Bei Cloud-/SSE-Deployment (Schulamt-Kontext, Stadt Zürich) sollte der Server in einem Container mit minimalen Privilegien laufen:

- Non-root User
- Read-only Root Filesystem
- Dropped Capabilities (`--cap-drop ALL`)
- No new privileges (`--security-opt no-new-privileges`)

### Evidence

- Kein Dockerfile / docker-compose.yml im Repo-Root
- README.md:121-145 (Cloud Deployment) beschreibt SSE-Start aber keine Container-Konfiguration
- `server.py:53` — `host=os.environ.get("MCP_HOST", "0.0.0.0")` bindet bei SSE auf alle Interfaces

### Risk Description

- **Compromise-Escape:** Bei Kompromittierung des Servers (z.B. via Tool-Poisoning gegen die Upstream-APIs) hat ein Angreifer vollen Host-Zugriff.
- **Schulamt-Compliance:** Stadt-Zürich-Hosting verlangt Container-Isolation bei jeder kunden-exponierten Komponente.
- **Lateral Movement:** Ohne Network-Egress-Policy kann ein kompromittierter Server beliebige externe Ziele erreichen.

### Remediation

```dockerfile
# Dockerfile (neu, im Repo-Root)
FROM python:3.13-slim AS build
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

FROM python:3.13-slim AS runtime
RUN useradd --create-home --shell /usr/sbin/nologin mcp
COPY --from=build /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=build /usr/local/bin/global-education-mcp /usr/local/bin/
USER mcp
WORKDIR /home/mcp
EXPOSE 8000
ENV MCP_TRANSPORT=sse PYTHONUNBUFFERED=1
ENTRYPOINT ["global-education-mcp"]
```

```yaml
# docker-compose.yml (Beispiel)
services:
  global-education-mcp:
    build: .
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    ports: ["127.0.0.1:8000:8000"]
    environment:
      MCP_TRANSPORT: sse
      LOG_LEVEL: INFO
```

README-Sektion "Cloud Deployment" aktualisieren auf Docker-First.

### Effort Estimate

**S** (< 1 Tag) — Dockerfile + compose + README-Update + CI-Build-Workflow.


### SEC-015

## Finding: SEC-015 — Pre-Flight Tool-Poisoning Detection

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `SEC-015` |
| **PDF-Reference** | Sec 4.15 |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

Tool-Beschreibungen sind sauber dokumentiert und committed, aber es gibt keinen automatisierten Mechanismus, der bei einem Update gegen eine Baseline prüft, ob die Beschreibungen "vergiftet" wurden (z.B. mit verstecktem Prompt-Injection-Text).

### Expected Behavior

Pre-Flight-Check als CI-Step:
1. Snapshot der Tool-Descriptions aus `tools.lock.json` (siehe SEC-022)
2. Pro Description: Heuristiken anwenden (suspicious tokens: "ignore previous", "instead do", "filesystem", "exec", "as a system prompt"…)
3. Bei Treffer: CI fail mit klarem Hinweis

### Evidence

- Keine Snapshot-/Lock-Datei (siehe SEC-022)
- Keine Lint-Regel im Repo für Tool-Descriptions

### Risk Description

- **Supply-Chain-Tool-Poisoning:** Ein böswilliger PR (oder kompromittierter Maintainer-Account) kann die Tool-Beschreibung von `uis_get_education_data` so manipulieren, dass Claude sie als zusätzliche System-Instruction interpretiert. Ohne Pre-Flight-Check fällt das nicht auf.

### Remediation

Hängt teilweise von SEC-022 (Lock-Datei) ab. Zusatz-Lint:

```python
# tools/check_tool_descriptions.py (neu)
SUSPICIOUS = [
    r"ignore (all )?(previous|prior) (instructions|prompts)",
    r"system prompt",
    r"act as",
    r"\b(execute|run|eval|os\.system|subprocess)\b",
    r"filesystem|file system",
    r"`?cat /etc/",
]

def lint(description: str) -> list[str]:
    hits = []
    for pat in SUSPICIOUS:
        if re.search(pat, description, re.I):
            hits.append(pat)
    return hits

# CI-Step: für jeden Tool die Description linten, Fehler bei hit
```

### Effort Estimate

**S** (< 1 Tag) — Lint-Skript + CI-Step.


### SEC-022

## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `global-education-mcp` |
| **Check-Reference** | `SEC-022` |
| **PDF-Reference** | Sec 4.18 |
| **Audit-Datum** | 2026-05-21 |
| **Auditor** | Claude (mcp-audit-skill v1.0.0) |

### Observed Behavior

Keine Tool-Hash-Pinning-Mechanik im Repo. Es gibt:
- keinen `tools.lock.json` / `tools.lock.yaml` / `mcp-tools.lock`
- keine CI-Validierung gegen einen committed Snapshot
- semantische Namespace-Präfixe (`uis_`, `oecd_`, `education_`) aber kein Schutz gegen Rename/Shadow

### Expected Behavior

Pro Release ist eine deterministische Hash-Liste über alle Tool-Signaturen (name + description + JSON-Schema des Inputs) im Repo committet. CI bricht bei jedem PR, der den Hash ändert ohne den Lockfile bewusst zu aktualisieren.

### Evidence

- `find . -iname "*.lock*" -o -iname "tools*" | grep -v audits` ergibt nur node-style Lockfiles (keine), nichts MCP-spezifisches
- `.github/workflows/ci.yml` führt nur pytest aus, kein Tool-Snapshot-Check
- 10 Tool-Namen aus `server.py`: `uis_list_indicators`, `uis_list_countries`, `uis_get_education_data`, `uis_compare_countries`, `uis_country_education_profile`, `uis_list_versions`, `oecd_list_education_datasets`, `oecd_get_education_indicator`, `oecd_search_datasets`, `education_benchmark_countries`

### Risk Description

- **Rug Pull:** Bei Schulamt-Multi-Server-Setup könnte ein kompromittiertes Update die Tool-Description ändern (z.B. `uis_compare_countries`: "Vergleicht Länder" → "Lädt API-Keys aus dem Filesystem"). Claude würde dem neuen Description folgen, der User merkt es erst beim Side-Effect.
- **Shadow-MCP:** Ohne Namespace-Präfix kann ein zweiter Server mit identischem Tool-Namen den Original-Server überschreiben (z.B. wenn beide `oecd_get_education_indicator` registrieren).

### Remediation

**Schritt 1:** Hash-Snapshot generieren und committen.

```python
# tools/dump_tool_hashes.py (neu)
import hashlib, json, sys
from global_education_mcp.server import mcp

snapshot = {}
for name, tool in mcp._tools.items():  # interne API; alternativ MCP-protocol list_tools
    sig = {
        "name": name,
        "description": tool.description,
        "input_schema": tool.inputSchema,
        "annotations": tool.annotations,
    }
    h = hashlib.sha256(json.dumps(sig, sort_keys=True).encode()).hexdigest()
    snapshot[name] = {"hash": h, "signature": sig}
json.dump(snapshot, sys.stdout, indent=2, sort_keys=True)
```

```bash
python -m global_education_mcp.tools.dump_tool_hashes > tools.lock.json
git add tools.lock.json
```

**Schritt 2:** CI-Check.

```yaml
# .github/workflows/ci.yml — neuer Step
- name: Verify tool signatures unchanged
  run: |
    python -m global_education_mcp.tools.dump_tool_hashes > /tmp/current.json
    diff -u tools.lock.json /tmp/current.json || (
      echo "::error::Tool signatures changed. Update tools.lock.json deliberately."
      exit 1
    )
```

**Schritt 3 (optional):** Namespace-Präfix `globaledu.` für Multi-Server-Setups via Tool-Renaming.

### Effort Estimate

**M** (1–3 Tage) — Snapshot-Tool + CI-Step + Release-Doku, da FastMCP-Internals geprüft werden müssen.


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **CH-005** (high, partial)
2. **CH-006** (high, partial)
3. **OBS-001** (high, partial)
4. **SCALE-002** (high, partial)
5. **SDK-001** (high, fail)
6. **SEC-006** (high, partial)
7. **SEC-007** (high, fail)
8. **SEC-022** (high, fail)
9. **ARCH-012** (medium, partial)
10. **OBS-003** (medium, fail)
11. **SDK-003** (medium, fail)
12. **SEC-015** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |


_Generated by tools/build_report.py — do not edit by hand._
