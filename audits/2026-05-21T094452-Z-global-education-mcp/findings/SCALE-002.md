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
