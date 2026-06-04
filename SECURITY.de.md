# 🔒 Sicherheitsrichtlinie

[🇬🇧 English Version](SECURITY.md)

> 🇨🇭 **Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)**

Danke, dass du dabei hilfst, **global-education-mcp** und seine Nutzer:innen sicher zu halten. Dieses Dokument erklärt, welche Versionen Sicherheitsupdates erhalten, wie du eine Schwachstelle meldest und auf welche Sicherheitseigenschaften der Server ausgelegt ist.

---

## Unterstützte Versionen

Sicherheitsupdates werden auf die jeweils aktuelle Minor-Release-Linie angewendet. Ältere Linien erhalten keine Backports.

| Version | Unterstützt |
|---|---|
| 1.0.x | ✅ |
| < 1.0 | ❌ |

---

## Eine Schwachstelle melden

**Bitte melde Sicherheitslücken nicht über öffentliche GitHub-Issues, -Discussions oder -Pull-Requests.**

Nutze stattdessen einen der folgenden privaten Kanäle:

1. **GitHub Security Advisories (bevorzugt)** — öffne einen privaten Report über den
   [Security-Tab → «Report a vulnerability»](https://github.com/malkreide/global-education-mcp/security/advisories/new).
2. **E-Mail** — schreibe an den Maintainer unter **hayal.oezkan@gmail.com** mit der Betreffzeile `[SECURITY] global-education-mcp`.

Bitte gib, soweit möglich, an:

- Eine Beschreibung der Schwachstelle und ihrer möglichen Auswirkungen
- Die betroffene Version, das betroffene Tool oder die betroffene Komponente (z. B. `uis_get_education_data`, SSE-Transport, Docker-Image)
- Schritt-für-Schritt-Anleitung zur Reproduktion oder einen Proof of Concept
- Relevante Logs, Konfigurationen oder Umgebungsdetails

---

## Offenlegungsprozess

- **Empfangsbestätigung:** innerhalb von **72 Stunden** nach deiner Meldung.
- **Bewertung:** wir triagieren und bestätigen das Problem, dann legen wir gemeinsam mit dir Schweregrad und Zeitfenster für den Fix fest.
- **Fix & Release:** validierte Fixes werden als Patch-Version veröffentlicht; das `CHANGELOG.md` vermerkt die Sicherheitsrelevanz.
- **Koordinierte Offenlegung:** wir nennen die meldende Person (sofern du nicht anonym bleiben möchtest) und veröffentlichen Details erst, wenn ein Fix verfügbar ist.

Wir folgen einem Modell der koordinierten Offenlegung und bitten dich, uns angemessene Zeit zur Behebung zu geben, bevor du Details öffentlich machst.

---

## Sicherheitsmodell

Dieser Server ist **schreibgeschützt** und verarbeitet **keine personenbezogenen Daten** — beides Designentscheidungen, die seine Angriffsfläche begrenzen.

| Eigenschaft | Detail |
|---|---|
| **Zugriff** | Schreibgeschützt (`readOnlyHint: true`) — der Server kann keine Upstream-Daten ändern, schreiben oder löschen |
| **Personenbezogene Daten** | Keine — UNESCO UIS und OECD EaG veröffentlichen nur aggregierte Statistiken auf Länderebene (keine PII, keine DSG-/EDÖB-Relevanz) |
| **Authentifizierung** | Keine API-Keys oder Secrets erforderlich; nichts Sensibles wird gespeichert oder geloggt |
| **Netzwerk-Egress** | Nur ausgehendes HTTPS zu `uis.unesco.org` und `sdmx.oecd.org`; 30-Sekunden-Timeouts mit Graceful Fallback |
| **Logging** | Strukturiertes JSON auf stderr — nur Tool-Name, Parameter und Dauer; keine PII (siehe Audit-Befund OBS-003) |
| **Caching** | Im Arbeitsspeicher, TTL-begrenzt; wird nie auf die Festplatte geschrieben |
| **Rate-Limits** | Eingebaute Obergrenzen pro Abfrage (max. 50 Indikatoren pro Suche, max. 10 Länder pro Vergleich, konservative Jahresbereiche) |

### Supply-Chain-Härtung

- **Tool-Signatur-Lockfile** — alle MCP-Tool-Signaturen (Name, Beschreibung, Input-Schema, Annotationen) sind in `tools.lock.json` fixiert. CI schlägt bei jeder ungeprüften Änderung oder bei Prompt-Injection-Markern in Tool-Beschreibungen fehl und schützt so vor Tool-Poisoning-/Rug-Pull-Angriffen (Audit-Befunde SEC-022 + SEC-015).
- **Fixierte Abhängigkeitsgrenzen** — `pyproject.toml` setzt explizite Obergrenzen, sodass ein transitives Update den Server nicht still brechen oder verändern kann.

### Deployment-Härtung (SSE / Cloud)

Der SSE-Transport muss **immer** hinter einem Reverse-Proxy laufen, der TLS, Authentifizierung und Rate-Limiting ergänzt. Seit v0.3 ist `MCP_HOST` standardmässig `127.0.0.1`; `MCP_HOST=0.0.0.0` ist nur innerhalb eines isolierten Container-Netzwerks sicher.

Das mitgelieferte `Dockerfile` und `docker-compose.yml` wenden Defense-in-Depth an: `read_only: true`, `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, einen Non-Root-Benutzer (`uid 10001`) und die Port-Bindung an `127.0.0.1`.

---

## Geltungsbereich

Im Geltungsbereich: der Server-Code (`src/global_education_mcp/`), die MCP-Tool-Oberfläche, die Docker-/SSE-Deployment-Artefakte und die oben beschriebenen Supply-Chain-Kontrollen.

Ausserhalb des Geltungsbereichs: Schwachstellen in den Upstream-Datenanbietern (UNESCO UIS, OECD), in der zugrunde liegenden Python-Laufzeit oder in Drittanbieter-Bibliotheken (bitte dort melden) sowie Probleme, die einen bereits kompromittierten Host voraussetzen.

---

## Autor

Hayal Oezkan · [github.com/malkreide](https://github.com/malkreide)
