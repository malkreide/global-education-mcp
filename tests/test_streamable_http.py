"""Spec 2026-07-28, gemessen: beide Aeren durch die HTTP-App, die `main()` startet.

`tests/test_protocol_version.py` pinnt die SDK-Konstanten und nennt das selbst
die schwaechere Form — dieses Repo baute keine ASGI-App, durch die sich ein
`initialize` haette schicken lassen. Mit dem Streamable-HTTP-Transport gibt es
sie. Die App entsteht hier aus `STREAMABLE_HTTP_OPTIONS`, denselben Optionen,
mit denen `main()` startet; ein Test mit eigener Konfiguration wuerde eine
andere App pruefen als die ausgelieferte.

Gesendet wird ueber `httpx2.ASGITransport` — kein Socket, kein Netz. Der Host
traegt einen Port, weil das SDK fuer `127.0.0.1` DNS-Rebinding-Schutz mit
`127.0.0.1:*` einschaltet; ohne Port antwortet es 421, und zwar zu Recht.
"""

from __future__ import annotations

import ast
import pathlib
import warnings
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import patch

import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import MCPDeprecationWarning
from mcp.types.version import LATEST_HANDSHAKE_VERSION, LATEST_MODERN_VERSION

from global_education_mcp import __version__, server
from global_education_mcp.server import LIST_CACHE_TTL_MS, STREAMABLE_HTTP_OPTIONS, STREAMABLE_HTTP_PATH, mcp

from .test_protocol_version import DOCUMENTED_HANDSHAKE_VERSION, DOCUMENTED_MODERN_VERSION

BASE = "http://127.0.0.1:8000"
MCP_URL = f"{BASE}{STREAMABLE_HTTP_PATH}"
DEPRECATED_CTX_LOGGING = {"log", "debug", "info", "warning", "error"}
ACCEPT = {"accept": "application/json, text/event-stream", "content-type": "application/json"}


@asynccontextmanager
async def _http_app() -> AsyncIterator[httpx2.AsyncClient]:
    app = mcp.streamable_http_app(host="127.0.0.1", **STREAMABLE_HTTP_OPTIONS)
    async with app.router.lifespan_context(app):
        async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url=BASE) as http:
            yield http


@asynccontextmanager
async def _client(mode: str) -> AsyncIterator[Client]:
    async with _http_app() as http:
        async with Client(streamable_http_client(MCP_URL, http_client=http), mode=mode) as client:
            yield client


async def test_ein_modern_client_erreicht_2026_07_28() -> None:
    """Der Kern des Auftrags: ein Client, der die Revision direkt uebernimmt,
    spricht sie auch — ohne `initialize`, ueber den Einzel-POST."""
    async with _client(DOCUMENTED_MODERN_VERSION) as client:
        assert client.session.protocol_version == DOCUMENTED_MODERN_VERSION
        tools = await client.list_tools()

    # Die Serverkennung reist in 2026-07-28 im `_meta` jeder Antwort.
    server_info = (tools.meta or {}).get("io.modelcontextprotocol/serverInfo")
    assert server_info == {"name": "global_education_mcp", "version": __version__}, server_info
    assert __version__, "leere Version — der Client kann zwei Staende nicht unterscheiden"

    assert len(tools.tools) == 10
    # Die Frischehinweise sind Felder von 2026-07-28 — hier kommen sie an.
    assert tools.ttl_ms == LIST_CACHE_TTL_MS
    assert tools.cache_scope == "public"


def discover_request(version: str = DOCUMENTED_MODERN_VERSION) -> tuple[dict[str, str], dict[str, Any]]:
    """Ein `server/discover` in Drahtform, ohne SDK-Client — dieselbe Anfrage
    schickt der Docker-Smoke-Test in `ci.yml` per curl an den Container."""
    headers = {**ACCEPT, "mcp-protocol-version": version, "mcp-method": "server/discover"}
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "server/discover",
        "params": {
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": version,
                "io.modelcontextprotocol/clientInfo": {"name": "gate", "version": "0"},
                "io.modelcontextprotocol/clientCapabilities": {},
            }
        },
    }
    return headers, body


async def test_server_discover_in_drahtform() -> None:
    """Unabhaengig vom SDK-Client: stimmt die Drahtform nicht, faellt dieser
    Test auch dann, wenn Client und Server im selben SDK-Bug uebereinstimmen."""
    headers, body = discover_request()
    async with _http_app() as http:
        response = await http.post(STREAMABLE_HTTP_PATH, headers=headers, json=body)

    assert response.status_code == 200, response.text
    result = response.json()["result"]
    assert DOCUMENTED_MODERN_VERSION in result["supportedVersions"]
    assert "logging" not in result["capabilities"], "abgekuendigte Capability angeboten (SEP-2577)"
    assert result["ttlMs"] == LIST_CACHE_TTL_MS


async def test_ein_client_mit_auto_landet_in_der_modernen_aera() -> None:
    """`auto` probiert `server/discover` und faellt sonst auf `initialize`
    zurueck. Landet er in der Legacy-Aera, hat der Server die Probe nicht
    verstanden — genau das, was ein SSE-Endpunkt liefern wuerde."""
    async with _client("auto") as client:
        assert client.session.protocol_version == LATEST_MODERN_VERSION == DOCUMENTED_MODERN_VERSION


async def test_ein_heutiger_client_handelt_die_handshake_aera_aus() -> None:
    """Die Aera, die heutige Clients sprechen, auf demselben Endpunkt. Ohne
    diese Zusicherung koennte der Umbau die bestehenden Clients verlieren,
    waehrend die modernen Tests gruen bleiben."""
    async with _client("legacy") as client:
        assert client.session.protocol_version == DOCUMENTED_HANDSHAKE_VERSION
        tools = await client.list_tools()

    assert len(tools.tools) == 10


async def test_ein_initialize_mit_neuerer_revision_wird_auf_die_obergrenze_gedeckelt() -> None:
    """Die Aushandlung aus der README («oder mit der Obergrenze, wenn die Anfrage
    etwas Neueres verlangt») als rohe HTTP-Antwort statt als Konstante."""
    async with _http_app() as http:
        response = await http.post(
            STREAMABLE_HTTP_PATH,
            headers=ACCEPT,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2099-01-01",
                    "capabilities": {},
                    "clientInfo": {"name": "gate", "version": "0"},
                },
            },
        )

    assert response.status_code == 200, response.text
    assert f'"protocolVersion":"{LATEST_HANDSHAKE_VERSION}"' in response.text.replace(" ", "")
    assert LATEST_HANDSHAKE_VERSION == DOCUMENTED_HANDSHAKE_VERSION


async def _fake_uis_data(indicator: str, geo_unit: str | None = None, **_: Any) -> dict[str, Any]:
    return {"records": [{"year": 2022, "value": 99.0}]}


@pytest.mark.parametrize("mode", [DOCUMENTED_MODERN_VERSION, "legacy"])
async def test_die_ansage_vor_dem_fan_out_kommt_als_fortschritt_an(mode: str) -> None:
    """Hier stand `ctx.info()`. In der modernen Aera stellt das SDK
    `notifications/message` nur zu, wenn die Anfrage einen Log-Level mitbringt —
    die Ansage «Vergleiche 3 Laender …» erreichte einen Client also nicht, und
    der Aufruf warf eine `MCPDeprecationWarning` (SEP-2577). Jetzt reist sie als
    Fortschritt 0 und kommt in beiden Aeren an."""
    events: list[tuple[float, float | None, str | None]] = []

    async def on_progress(progress: float, total: float | None, message: str | None) -> None:
        events.append((progress, total, message))

    with warnings.catch_warnings():
        warnings.simplefilter("error", MCPDeprecationWarning)
        with patch("global_education_mcp.server.uis_get_data", side_effect=_fake_uis_data):
            async with _client(mode) as client:
                result = await client.call_tool(
                    "uis_compare_countries",
                    {"params": {"indicator_id": "LR.AG15T99", "country_codes": ["CHE", "DEU", "FIN"]}},
                    progress_callback=on_progress,
                )

    assert not result.is_error, result
    assert events, "kein einziges Fortschrittsereignis angekommen"
    first = events[0]
    assert first[0] == 0 and first[1] == 3
    assert first[2] is not None and "Vergleiche 3 Länder" in first[2]
    assert events[-1][0] == 3


def test_der_server_ruft_die_abgekuendigte_logging_capability_nicht_auf() -> None:
    """Dieselbe Absicht an der Quelle: kein `ctx.info/debug/warning/error/log`.
    Der Laufzeittest oben deckt nur das eine Werkzeug ab, das er aufruft.
    Am Syntaxbaum statt am Text, damit ein Kommentar, der die Abkuendigung
    erklaert, nicht als Aufruf zaehlt."""
    tree = ast.parse(pathlib.Path(server.__file__).read_text(encoding="utf-8"))
    calls = [
        f"{node.func.value.id}.{node.func.attr}() Zeile {node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "ctx"
        and node.func.attr in DEPRECATED_CTX_LOGGING
    ]
    assert not calls, f"Logging-Capability ist ab 2026-07-28 abgekuendigt (SEP-2577): {calls}"
    # Positivkontrolle: der Baum wird gelesen — der Fortschrittskanal steht drin.
    assert any(isinstance(n, ast.Attribute) and n.attr == "report_progress" for n in ast.walk(tree)), (
        "report_progress nicht gefunden — misst dieser Test ueberhaupt die richtige Datei?"
    )


# ─── main(): welcher Transport startet ─────────────────────────────────────────


def _run_main(monkeypatch: pytest.MonkeyPatch, transport: str | None) -> list[tuple[str, dict[str, Any]]]:
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(server.mcp, "run", lambda transport, **kw: calls.append((transport, kw)))
    monkeypatch.setattr(server, "configure_logging", lambda: None)
    for key in ("MCP_TRANSPORT", "MCP_HOST", "PORT"):
        monkeypatch.delenv(key, raising=False)
    if transport is not None:
        monkeypatch.setenv("MCP_TRANSPORT", transport)
    server.main()
    return calls


def test_streamable_http_startet_mit_den_geprueften_optionen(monkeypatch: pytest.MonkeyPatch) -> None:
    """Die Bruecke zwischen den Messungen oben und dem Betrieb: dieselben
    Optionen, nicht bloss derselbe Transportname."""
    calls = _run_main(monkeypatch, "streamable-http")
    assert calls == [("streamable-http", {"host": "127.0.0.1", "port": 8000, **STREAMABLE_HTTP_OPTIONS})]


def test_ohne_angabe_bleibt_es_bei_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _run_main(monkeypatch, None) == [("stdio", {})]


def test_sse_laeuft_weiter_fuer_bestehende_deployments(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _run_main(monkeypatch, "sse")
    assert calls == [("sse", {"host": "127.0.0.1", "port": 8000})]


def test_ein_unbekannter_transport_bricht_ab_statt_still_stdio_zu_starten(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vorher startete `MCP_TRANSPORT=http` stdio — im Container ohne offenen
    Port, ohne Fehlermeldung."""
    with pytest.raises(SystemExit, match="streamable-http"):
        _run_main(monkeypatch, "http")
