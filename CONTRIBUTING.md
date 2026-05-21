# Contributing to global-education-mcp

Thank you for your interest in contributing! This project is part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide).

---

## Getting Started

```bash
# Fork and clone
git clone https://github.com/your-username/global-education-mcp.git
cd global-education-mcp

# Install with dev dependencies
pip install -e ".[dev]"

# Run the test suite to verify your setup
PYTHONPATH=src pytest tests/ -v -m "not integration"
```

---

## How to Contribute

### Reporting Bugs

Please open an issue and include:
- A clear description of the problem
- The exact query or tool call that triggered the issue
- The error message or unexpected output
- Your Python version and OS

### Suggesting Features

Open an issue with the `enhancement` label. Describe:
- The use case (who needs this, in what context?)
- Which data source would provide the data (UNESCO UIS or OECD?)
- Whether an existing tool could be extended or a new tool is needed

### Submitting a Pull Request

1. Open an issue first to discuss the change
2. Create a feature branch: `git checkout -b feat/your-feature-name`
3. Make your changes (see code standards below)
4. Run the full test suite
5. Commit with a [Conventional Commit](https://www.conventionalcommits.org/) message
6. Push and open a pull request against `main`

---

## Code Standards

- **Style:** [Ruff](https://docs.astral.sh/ruff/) for linting and formatting (`ruff check . && ruff format .`)
- **Types:** Type hints on all public functions
- **Docstrings:** One-line summary for every tool function
- **Dependencies:** No new runtime dependencies without prior discussion

---

## Testing

All contributions must include tests.

```bash
# Unit tests only (no network)
PYTHONPATH=src pytest tests/ -v -m "not integration"

# Full suite including live API smoke tests
PYTHONPATH=src pytest tests/ -v
```

- Add unit tests to `tests/test_server.py` or `tests/test_extended_scenarios.py`
- Mark tests that call live APIs with `@pytest.mark.integration`
- Aim for coverage of edge cases, not just the happy path

---

## Logging & Error Handling

### Structured JSON logging (audit finding OBS-003)

All log output goes through `global_education_mcp.logging_setup.JSONFormatter`
and writes one JSON object per line to **stderr**. Never write to stdout
when the stdio transport is in use — stdout is reserved for MCP protocol
frames.

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

`level` in the emitted JSON is RFC-5424 conform (debug/info/notice/warning/error/critical).
Level configured via `LOG_LEVEL` env var (default `INFO`).

Every `@mcp.tool` function should also be wrapped with `@logged_tool`:

```python
@mcp.tool(name="…", annotations={…})
@logged_tool
async def my_tool(params: MyInput) -> str:
    ...
```

This emits one `tool_call` log line per invocation with `tool`, `duration_ms`,
and `status` (`ok` | `error`). `functools.wraps` preserves the signature,
so the FastMCP-generated input schema and the `tools.lock.json` hash stay
stable.

### Protocol vs. execution errors (audit finding OBS-001)

`api_client.raise_if_transient(e, context)` distinguishes:

- **Transient upstream failures** (5xx, `httpx.TimeoutException`,
  `httpx.ConnectError`) → raises `McpError(code=INTERNAL_ERROR)` so the
  MCP host can retry.
- **4xx + other exceptions** → no-op; caller formats via
  `handle_api_error()` and returns the text as a tool result, so the LLM
  can adapt (e.g. suggest a different indicator).

Pattern for new tools without a graceful fallback:

```python
try:
    raw = await uis_get_data(...)
    ...
except Exception as e:
    raise_if_transient(e, context="my_tool")  # 5xx/timeout -> McpError
    return handle_api_error(e, "my_tool")     # 4xx/other -> text
```

Tools that have explicit graceful fallbacks (e.g. local indicator list when
the UNESCO API is down) intentionally skip `raise_if_transient` — degraded
data is better UX than a host-level retry that hits the same outage.

### Progress reporting (audit finding SDK-003)

Tools that perform more than a handful of upstream calls (multi-country
compares, country profiles, benchmarks) accept an optional FastMCP
`Context` parameter and emit progress events:

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

The `_ctx_*` helpers in `server.py` are no-ops when `ctx is None` (unit
tests). Tool functions never crash because of a broken context — the
helpers swallow any exception from `ctx.info` / `ctx.report_progress`.

FastMCP detects the `Context` type annotation and auto-injects when the
host calls the tool. It is excluded from the generated input schema, so
adding `ctx` does **not** change the `tools.lock.json` hash.

---

## Tool-Signature-Lockfile

The repository pins all MCP tool signatures (name, description, input schema,
annotations) in `tools.lock.json`. This guards against tool-poisoning / rug-pull
supply-chain attacks (audit findings SEC-022 + SEC-015).

CI runs `python scripts/tool_signatures.py ci` on every PR. The job fails if:

- A tool's name, description, schema, or annotations changed without the
  lockfile being updated, **or**
- A description contains a suspicious prompt-injection marker
  (e.g. `ignore previous instructions`, `act as system`, `eval the following`).

**Workflow when you legitimately change a tool:**

```bash
# After editing server.py:
PYTHONPATH=src python scripts/tool_signatures.py update
git add tools.lock.json
git commit  # together with the code change
```

The lockfile diff is the audit trail — reviewers should look at it explicitly.

---

## Commit Message Format

```
<type>: <short description>

Examples:
feat: add uis_get_regional_data tool
fix: handle empty SDMX response from OECD
docs: update caching strategy table
test: add adversarial input tests for uis_compare_countries
chore: bump httpx to 0.28
```

| Type | When to use |
|---|---|
| `feat` | New tool, resource or prompt |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Tests only |
| `refactor` | Code restructure, no behaviour change |
| `chore` | Build, dependencies, CI |

---

## Project Structure

```
global-education-mcp/
├── src/global_education_mcp/
│   ├── server.py       # Tool definitions – add new tools here
│   └── api_client.py   # API wrappers – add new data source logic here
└── tests/
    ├── test_server.py              # Core tool tests
    └── test_extended_scenarios.py  # Extended scenario tests
```

---

## Questions

Open an issue or start a [GitHub Discussion](https://github.com/malkreide/global-education-mcp/discussions). Please do not use issues for general questions about MCP or the UNESCO/OECD APIs.
