# Mitwirken an global-education-mcp

[🇬🇧 English Version](CONTRIBUTING.md)

> 🇨🇭 **Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)**

Vielen Dank für dein Interesse an einem Beitrag! Dieses Projekt ist Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide).

---

## Erste Schritte

```bash
# Forken und klonen
git clone https://github.com/your-username/global-education-mcp.git
cd global-education-mcp

# Mit Dev-Abhängigkeiten installieren
pip install -e ".[dev]"

# Testsuite ausführen, um das Setup zu überprüfen
PYTHONPATH=src pytest tests/ -v -m "not integration"
```

---

## Wie du beitragen kannst

### Fehler melden

Bitte öffne ein Issue und füge Folgendes bei:
- Eine klare Beschreibung des Problems
- Die genaue Abfrage oder den Tool-Aufruf, der das Problem ausgelöst hat
- Die Fehlermeldung oder unerwartete Ausgabe
- Deine Python-Version und dein Betriebssystem

### Funktionen vorschlagen

Öffne ein Issue mit dem Label `enhancement`. Beschreibe:
- Den Anwendungsfall (Wer braucht das, in welchem Kontext?)
- Welche Datenquelle die Daten liefern würde (UNESCO UIS oder OECD?)
- Ob ein bestehendes Tool erweitert oder ein neues Tool benötigt wird

### Einen Pull Request einreichen

1. Öffne zuerst ein Issue, um die Änderung zu besprechen
2. Erstelle einen Feature-Branch: `git checkout -b feat/your-feature-name`
3. Nimm deine Änderungen vor (siehe Code-Standards unten)
4. Führe die vollständige Testsuite aus
5. Committe mit einer [Conventional-Commit](https://www.conventionalcommits.org/)-Nachricht
6. Pushe und öffne einen Pull Request gegen `main`

---

## Code-Standards

- **Stil:** [Ruff](https://docs.astral.sh/ruff/) für Linting und Formatierung (`ruff check . && ruff format .`)
- **Typen:** Type-Hints für alle öffentlichen Funktionen
- **Docstrings:** Einzeilige Zusammenfassung für jede Tool-Funktion
- **Abhängigkeiten:** Keine neuen Runtime-Abhängigkeiten ohne vorherige Absprache

---

## Testen

Alle Beiträge müssen Tests enthalten.

```bash
# Nur Unit-Tests (kein Netzwerk)
PYTHONPATH=src pytest tests/ -v -m "not integration"

# Vollständige Suite inklusive Live-API-Smoke-Tests
PYTHONPATH=src pytest tests/ -v
```

- Füge Unit-Tests zu `tests/test_server.py` oder `tests/test_extended_scenarios.py` hinzu
- Markiere Tests, die Live-APIs aufrufen, mit `@pytest.mark.integration`
- Strebe Abdeckung von Grenzfällen an, nicht nur des Happy Path

---

## Logging & Fehlerbehandlung

### Strukturiertes JSON-Logging (Audit-Befund OBS-003)

Sämtliche Log-Ausgaben laufen über `global_education_mcp.logging_setup.JSONFormatter`
und schreiben ein JSON-Objekt pro Zeile auf **stderr**. Schreibe niemals auf stdout,
wenn der stdio-Transport verwendet wird — stdout ist für MCP-Protokoll-Frames
reserviert.

```python
import logging
logger = logging.getLogger("global_education_mcp.tool")
logger.info("tool_call", extra={"extra_fields": {
    "tool": "uis_get_education_data",
    "duration_ms": 482,
    "status": "ok",
    "indicator": params.indicator_id,
}})
```

`level` im ausgegebenen JSON ist RFC-5424-konform (debug/info/notice/warning/error/critical).
Das Level wird über die Umgebungsvariable `LOG_LEVEL` konfiguriert (Standard `INFO`).

Jede `@mcp.tool`-Funktion sollte zusätzlich mit `@logged_tool` umhüllt werden:

```python
@mcp.tool(name="…", annotations={…})
@logged_tool
async def my_tool(params: MyInput) -> str:
    ...
```

Dies gibt eine `tool_call`-Logzeile pro Aufruf aus, mit `tool`, `duration_ms`
und `status` (`ok` | `error`). `functools.wraps` bewahrt die Signatur,
sodass das von FastMCP generierte Input-Schema und der `tools.lock.json`-Hash
stabil bleiben.

### Protokoll- vs. Ausführungsfehler (Audit-Befund OBS-001)

`api_client.raise_if_transient(e, context)` unterscheidet:

- **Transiente Upstream-Ausfälle** (5xx, `httpx.TimeoutException`,
  `httpx.ConnectError`) → wirft `McpError(code=INTERNAL_ERROR)`, damit der
  MCP-Host es erneut versuchen kann.
- **4xx + andere Ausnahmen** → kein Effekt; der Aufrufer formatiert via
  `handle_api_error()` und gibt den Text als Tool-Ergebnis zurück, sodass das LLM
  sich anpassen kann (z. B. einen anderen Indikator vorschlagen).

Muster für neue Tools ohne Graceful Fallback:

```python
try:
    raw = await uis_get_data(...)
    ...
except Exception as e:
    raise_if_transient(e, context="my_tool")  # 5xx/Timeout -> McpError
    return handle_api_error(e, "my_tool")     # 4xx/andere -> Text
```

Tools mit expliziten Graceful Fallbacks (z. B. lokale Indikatorliste, wenn
die UNESCO-API nicht erreichbar ist) überspringen `raise_if_transient`
absichtlich — degradierte Daten sind bessere UX als ein Host-Retry, der
denselben Ausfall trifft.

### Fortschrittsmeldung (Audit-Befund SDK-003)

Tools, die mehr als eine Handvoll Upstream-Aufrufe ausführen (Multi-Country-
Vergleiche, Länderprofile, Benchmarks), akzeptieren einen optionalen FastMCP-
`Context`-Parameter und geben Fortschrittsereignisse aus:

```python
from mcp.server.fastmcp import Context

@mcp.tool(...)
@logged_tool
async def my_long_tool(params: MyInput, ctx: Optional[Context] = None) -> str:
    await _ctx_info(ctx, f"Starting {len(params.items)} fetches")
    progress = {"done": 0}

    async def fetch(item):
        try:
            return await upstream_call(item)
        finally:
            progress["done"] += 1
            await _ctx_progress(ctx, progress["done"], len(params.items), str(item))

    results = await asyncio.gather(*(fetch(i) for i in params.items), return_exceptions=True)
    ...
```

Die `_ctx_*`-Helfer in `server.py` sind No-Ops, wenn `ctx is None` (Unit-
Tests). Tool-Funktionen stürzen nie wegen eines defekten Context ab — die
Helfer schlucken jede Ausnahme von `ctx.info` / `ctx.report_progress`.

FastMCP erkennt die `Context`-Typannotation und injiziert sie automatisch,
wenn der Host das Tool aufruft. Sie ist vom generierten Input-Schema
ausgeschlossen, sodass das Hinzufügen von `ctx` den `tools.lock.json`-Hash
**nicht** verändert.

---

## Tool-Signatur-Lockfile

Das Repository fixiert alle MCP-Tool-Signaturen (Name, Beschreibung, Input-Schema,
Annotationen) in `tools.lock.json`. Dies schützt vor Tool-Poisoning-/Rug-Pull-
Supply-Chain-Angriffen (Audit-Befunde SEC-022 + SEC-015).

CI führt bei jedem PR `python scripts/tool_signatures.py ci` aus. Der Job schlägt fehl, wenn:

- Name, Beschreibung, Schema oder Annotationen eines Tools geändert wurden, ohne
  dass das Lockfile aktualisiert wurde, **oder**
- eine Beschreibung einen verdächtigen Prompt-Injection-Marker enthält
  (z. B. `ignore previous instructions`, `act as system`, `eval the following`).

**Workflow, wenn du ein Tool legitim änderst:**

```bash
# Nach dem Bearbeiten von server.py:
PYTHONPATH=src python scripts/tool_signatures.py update
git add tools.lock.json
git commit  # zusammen mit der Code-Änderung
```

Der Lockfile-Diff ist der Audit-Trail — Reviewer sollten ihn explizit prüfen.

---

## Format der Commit-Nachrichten

```
<type>: <kurze Beschreibung>

Beispiele:
feat: add uis_get_regional_data tool
fix: handle empty SDMX response from OECD
docs: update caching strategy table
test: add adversarial input tests for uis_compare_countries
chore: bump httpx to 0.28
```

| Typ | Wann verwenden |
|---|---|
| `feat` | Neues Tool, neue Resource oder neuer Prompt |
| `fix` | Bugfix |
| `docs` | Nur Dokumentation |
| `test` | Nur Tests |
| `refactor` | Code-Umstrukturierung, kein Verhaltensänderung |
| `chore` | Build, Abhängigkeiten, CI |

---

## Projektstruktur

```
global-education-mcp/
├── src/global_education_mcp/
│   ├── server.py       # Tool-Definitionen – neue Tools hier hinzufügen
│   └── api_client.py   # API-Wrapper – neue Datenquellen-Logik hier hinzufügen
└── tests/
    ├── test_server.py              # Kern-Tool-Tests
    └── test_extended_scenarios.py  # Erweiterte Szenario-Tests
```

---

## Fragen

Öffne ein Issue oder starte eine [GitHub-Discussion](https://github.com/malkreide/global-education-mcp/discussions). Bitte verwende Issues nicht für allgemeine Fragen zu MCP oder den UNESCO-/OECD-APIs.
