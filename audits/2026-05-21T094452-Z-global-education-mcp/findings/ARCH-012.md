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
