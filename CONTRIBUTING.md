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
