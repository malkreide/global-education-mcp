# 🔒 Security Policy

[🇩🇪 Deutsche Version](SECURITY.de.md)

> 🇨🇭 **Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide)**

Thank you for helping keep **global-education-mcp** and its users safe. This document explains which versions receive security fixes, how to report a vulnerability, and the security properties the server is designed around.

---

## Supported Versions

Security fixes are applied to the latest minor release line. Older lines do not receive backports.

| Version | Supported |
|---|---|
| 1.0.x | ✅ |
| < 1.0 | ❌ |

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.**

Instead, use one of the following private channels:

1. **GitHub Security Advisories (preferred)** — open a private report via the
   [Security tab → "Report a vulnerability"](https://github.com/malkreide/global-education-mcp/security/advisories/new).
2. **Email** — write to the maintainer at **hayal.oezkan@gmail.com** with the subject line `[SECURITY] global-education-mcp`.

Please include, as far as possible:

- A description of the vulnerability and its potential impact
- The affected version, tool, or component (e.g. `uis_get_education_data`, SSE transport, Docker image)
- Step-by-step reproduction instructions or a proof of concept
- Any relevant logs, configuration, or environment details

---

## Disclosure Process

- **Acknowledgement:** within **72 hours** of your report.
- **Assessment:** we triage and confirm the issue, then agree on a severity and target fix window with you.
- **Fix & release:** validated fixes are released as a patch version; the `CHANGELOG.md` notes the security relevance.
- **Coordinated disclosure:** we credit reporters (unless you prefer to stay anonymous) and publish details only after a fix is available.

We follow a coordinated-disclosure model and ask that you give us reasonable time to remediate before any public disclosure.

---

## Security Model

This server is **read-only** and processes **no personal data** — both design choices that bound its security exposure.

| Property | Detail |
|---|---|
| **Access** | Read-only (`readOnlyHint: true`) — the server cannot modify, write, or delete any upstream data |
| **Personal data** | None — UNESCO UIS and OECD EaG publish only aggregated, country-level statistics (no PII, no DSG/EDÖB relevance) |
| **Authentication** | No API keys or secrets required; nothing sensitive is stored or logged |
| **Network egress** | Only outbound HTTPS to `uis.unesco.org` and `sdmx.oecd.org`; 30-second timeouts with graceful fallback |
| **Logging** | Structured JSON to stderr — tool name, parameters, and duration only; no PII (see audit finding OBS-003) |
| **Caching** | In-memory, TTL-bounded; never written to disk |
| **Rate limits** | Built-in per-query caps (max 50 indicators per search, max 10 countries per comparison, conservative year ranges) |

### Supply-Chain Hardening

- **Tool-signature lockfile** — all MCP tool signatures (name, description, input schema, annotations) are pinned in `tools.lock.json`. CI fails on any unreviewed change or on prompt-injection markers in tool descriptions, guarding against tool-poisoning / rug-pull attacks (audit findings SEC-022 + SEC-015).
- **Pinned dependency bounds** — `pyproject.toml` sets explicit upper bounds so a transitive bump cannot silently break or alter the server.

### Deployment Hardening (SSE / Cloud)

The SSE transport must **always** run behind a reverse proxy that adds TLS, authentication, and rate-limiting. Since v0.3, `MCP_HOST` defaults to `127.0.0.1`; `MCP_HOST=0.0.0.0` is only safe inside an isolated container network.

The shipped `Dockerfile` and `docker-compose.yml` apply defence-in-depth: `read_only: true`, `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, a non-root user (`uid 10001`), and port binding to `127.0.0.1`.

---

## Scope

In scope: the server code (`src/global_education_mcp/`), the MCP tool surface, the Docker/SSE deployment artefacts, and the supply-chain controls described above.

Out of scope: vulnerabilities in the upstream data providers (UNESCO UIS, OECD), the underlying Python runtime or third-party libraries (please report those to the respective projects), and issues that require a pre-compromised host.

---

## Author

Hayal Oezkan · [github.com/malkreide](https://github.com/malkreide)
