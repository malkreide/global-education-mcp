"""
Gemeinsame HTTP-Client-Infrastruktur für UNESCO UIS und OECD APIs.
Enthält Rate-Limiting, Caching und einheitliche Fehlerbehandlung.
"""

import asyncio
import json
import logging
from typing import Any, Optional

import httpx

from . import __version__

# Wer fragt hier an? Ohne eigenen User-Agent geht der httpx-Default
# hinaus und der Betreiber der Datenquelle sieht bloss eine Bibliothek.
# Die Version stammt aus den Paket-Metadaten und kann nicht driften.
USER_AGENT = f"global-education-mcp/{__version__} (+https://github.com/malkreide/global-education-mcp)"
logger = logging.getLogger(__name__)

# Shared httpx client, gesetzt durch den MCPServer-Lifespan in server.py.
# Bei None (z.B. in Unit-Tests ohne Lifespan) erstellt http_get_* einen
# Per-Request-Client als Fallback.
_shared_client: Optional[httpx.AsyncClient] = None

# Upstream-Throttling: max. 5 gleichzeitige Calls pro API, damit ein
# uis_compare_countries(15 Länder) nicht das UNESCO-Quota auf einmal verbraucht.
_uis_semaphore = asyncio.Semaphore(5)
_oecd_semaphore = asyncio.Semaphore(5)


def set_shared_client(client: Optional[httpx.AsyncClient]) -> None:
    """Setzt den vom Lifespan verwalteten Shared-Client (oder löscht ihn)."""
    global _shared_client
    _shared_client = client


# ─── Basis-URLs ───────────────────────────────────────────────────────────────

UNESCO_BASE_URL = "https://api.uis.unesco.org/api/public"
OECD_BASE_URL = "https://sdmx.oecd.org/public/rest"

# ─── Bekannte UNESCO-Bildungsindikatoren ──────────────────────────────────────
#
# Diese Tabelle ist die Ersatzliste, die angezeigt wird, wenn die Quelle nicht
# erreichbar ist — und sie war lange die EINZIGE Liste, die ein Nutzer je zu
# sehen bekam, weil der API-Pfad 404 gab.
#
# Am 2026-08-08 gegen `definitions/indicators` gehalten: **12 der 22 IDs gibt
# es in der Quelle nicht.** Darunter alle drei `NERA.*`, alle drei `XUNIT.*`,
# alle drei `PTR.*`, beide `GPI.*` und `SDG4`. Es waren genau die Kategorien,
# die der Docstring von `uis_list_indicators` bewarb.
#
# Jeder Code hier ist jetzt gegen die Quelle geprüft, und
# `tests/test_indicator_table.py` hält die Tabelle gegen die aufgezeichnete
# Definition. Zwei Kategorien fallen weg, weil die UIS sie nicht mehr führt:
# das Schüler-Lehrer-Verhältnis (`PTR.*`) und ein SDG-4-Gesamtindikator. Ein
# Ersatz wäre erfunden, und eine erfundene ID ist schlimmer als eine fehlende
# Zeile — sie sieht aus wie eine Antwort.
UNESCO_EDUCATION_INDICATORS = {
    # Alphabetisierung
    "LR.AG15T99": "Alphabetisierungsrate Erwachsene (15+)",
    "LR.AG15T24": "Alphabetisierungsrate Jugendliche (15–24)",
    "LR.AG15T24.F": "Alphabetisierungsrate Jugendliche weiblich",
    "LR.AG15T24.M": "Alphabetisierungsrate Jugendliche männlich",
    # Schulabschluss
    "CR.1": "Abschlussquote Primarstufe",
    "CR.2": "Abschlussquote Sekundarstufe I",
    "CR.3": "Abschlussquote Sekundarstufe II",
    "CR.1.F": "Abschlussquote Primarstufe weiblich",
    "CR.1.M": "Abschlussquote Primarstufe männlich",
    # Einschulungsraten — die Quelle führt `NERT.*`, nicht `NERA.*`
    "NERT.1.CP": "Netto-Einschulungsrate Primarstufe",
    "NERT.1.F.CP": "Netto-Einschulungsrate Primarstufe weiblich",
    "NERT.1.M.CP": "Netto-Einschulungsrate Primarstufe männlich",
    "OFST.1.CP": "Kinder ausserhalb der Schule (Primarschulalter)",
    # Bildungsausgaben — `XGDP.*`, nicht `XUNIT.*`
    "XGDP.FSGOV": "Öffentliche Bildungsausgaben als % des BIP",
    "XGDP.FSGOV.FFNTR": "Initiale öffentliche Bildungsausgaben als % des BIP",
    # Lehrpersonen
    "TRTP.1": "Anteil Lehrpersonen mit Mindestqualifikation, Primarstufe (%)",
    "FTP.1": "Anteil weiblicher Lehrpersonen, Primarstufe (%)",
}

# ─── OECD Education at a Glance Dataflow-IDs ─────────────────────────────────

OECD_EDUCATION_DATAFLOWS = {
    "EAG_ENRL": "Einschreibungsraten nach Bildungsstufe",
    "EAG_GRAD_ENTR": "Abschluss- und Eintrittsquoten",
    "EAG_PERS": "Lehrpersonal nach Bildungsstufe",
    "EAG_FISC": "Bildungsausgaben und Finanzierung",
    "EAG_PERS_SALARY": "Lehrergehälter",
    "EAG_PERS_WORK": "Arbeitszeit Lehrpersonen",
    "EAG_EMP_EDUC": "Beschäftigung nach Bildungsabschluss",
    "EAG_EARN_RATIO": "Einkommensunterschiede nach Bildung",
}

# ─── HTTP-Client ──────────────────────────────────────────────────────────────

TIMEOUT = httpx.Timeout(30.0, connect=10.0)
LIMITS = httpx.Limits(max_connections=10, max_keepalive_connections=5)
HEADERS_JSON = {"Accept": "application/json"}


async def http_get_json(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
) -> Any:
    """Führt einen HTTP GET-Request aus und gibt JSON zurück."""
    request_headers = {**HEADERS_JSON, **(headers or {})}
    if _shared_client is not None:
        response = await _shared_client.get(url, params=params, headers=request_headers)
        response.raise_for_status()
        return response.json()
    async with httpx.AsyncClient(timeout=TIMEOUT, limits=LIMITS, headers={"User-Agent": USER_AGENT}) as client:
        response = await client.get(url, params=params, headers=request_headers)
        response.raise_for_status()
        return response.json()


async def http_get_text(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
) -> str:
    """Führt einen HTTP GET-Request aus und gibt Text zurück."""
    request_headers = headers or {}
    if _shared_client is not None:
        response = await _shared_client.get(url, params=params, headers=request_headers)
        response.raise_for_status()
        return response.text
    async with httpx.AsyncClient(timeout=TIMEOUT, limits=LIMITS, headers={"User-Agent": USER_AGENT}) as client:
        response = await client.get(url, params=params, headers=request_headers)
        response.raise_for_status()
        return response.text


# ─── UNESCO UIS API ───────────────────────────────────────────────────────────


async def uis_get_indicators(theme: Optional[str] = None) -> list[dict]:
    """Ruft verfügbare UIS-Indikatoren ab.

    Der Pfad lautet `/definitions/indicators`, nicht `/indicators`. Gemessen am
    2026-08-08 antwortete `/indicators` mit HTTP 404 («Cannot GET
    /api/public/indicators») — und zwar auf jede Anfrage, seit die UIS ihre
    API umgestellt hat. Sichtbar war das nicht: Der Aufrufer fängt den Fehler
    und zeigt eine lokale Ersatzliste an. Das ist ehrlich beschriftet
    («API nicht erreichbar»), heisst aber, dass dieses Werkzeug die Quelle nie
    erreicht hat und die 5063 tatsächlich geführten Indikatoren nie zeigte.

    `theme` wird hier NICHT mehr an die Quelle gesendet, sondern lokal
    gefiltert. `openapi/schema.json` kennt für diesen Pfad nur `version`,
    `glossaryTerms` und `disaggregations` — unbekannte Query-Parameter
    beantwortet die Quelle mit HTTP 200 und lässt sie fallen. Die Kontrolle
    ist in `uis_indicator_themes.json` aufgezeichnet: `theme=bogus-theme`
    liefert dieselben 5063 Zeilen wie `theme=EDUCATION`. Ein Filter, der
    stillschweigend nichts filtert, ist schlimmer als keiner — er beschriftet
    die Gesamtmenge als Auswahl.
    """
    url = f"{UNESCO_BASE_URL}/definitions/indicators"
    async with _uis_semaphore:
        data = await http_get_json(url)
    indicators = data if isinstance(data, list) else data.get("indicators", [])
    if theme:
        wanted = theme.strip().upper()
        indicators = [i for i in indicators if str(i.get("theme", "")).upper() == wanted]
    return indicators


async def uis_get_geo_units() -> list[dict]:
    """Ruft verfügbare geografische Einheiten (Länder/Regionen) ab."""
    # `/geo-units` gab es nie; die Quelle schreibt `geounits`, klein und ohne
    # Bindestrich. Auch das antwortete mit 404 auf jede Anfrage.
    url = f"{UNESCO_BASE_URL}/definitions/geounits"
    async with _uis_semaphore:
        data = await http_get_json(url)
    return data if isinstance(data, list) else data.get("geoUnits", [])


async def uis_get_data(
    indicator: str,
    geo_unit: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    version: Optional[str] = None,
) -> dict:
    """Ruft UIS-Datenpunkte für einen Indikator ab.

    `/data` ist 404; die Daten liegen unter `/data/indicators`. Ohne
    `indicator` oder `geoUnit` antwortet die Quelle mit HTTP 400 und sagt
    ausdruecklich, dass mindestens einer der beiden noetig ist.

    Der Jahresfilter heisst `start`/`end`. Gesendet wurde `startYear`/`endYear`
    — Namen, die die Quelle nicht kennt. Zurueckweisen tut sie sie nicht:
    Unbekannte Query-Parameter beantwortet sie mit HTTP 200 und laesst sie
    fallen. `CR.1`/`CHE` fuer 2015–2018 lieferte damit alle 14 Jahre von 2006
    bis 2021, und die Ausgabe schrieb ein Fenster darueber, das nie angewandt
    wurde. Gemessen am 2026-08-08 gegen `openapi/schema.json` der Quelle und
    gegen die Antwort selbst; mit `start`/`end` kommen genau die vier Jahre.
    """
    url = f"{UNESCO_BASE_URL}/data/indicators"
    params: dict = {"indicator": indicator}
    if geo_unit:
        params["geoUnit"] = geo_unit
    if start_year:
        params["start"] = start_year
    if end_year:
        params["end"] = end_year
    if version:
        params["version"] = version
    async with _uis_semaphore:
        return await http_get_json(url, params=params)


class UpstreamShapeError(RuntimeError):
    """Die Quelle hat geantwortet, aber nicht mit dem, womit sie antwortet.

    Bewusst getrennt von einem Transportfehler: Warten hilft beim einen und
    nie beim anderen.
    """


def uis_records(payload: dict) -> list[dict]:
    """Die Datenzeilen einer UIS-Antwort — oder ein Fehler, nie stillschweigend [].

    Die Quelle legt sie unter `records` ab. Gesucht wurde bis zum 2026-08-08
    `observations`, mit `data` als zweitem Versuch — beide gibt es nicht, und
    weil der Ausdruck mit `[]` endete, kam aus jeder Antwort eine leere Liste
    heraus. Aus einem Formfehler wurde damit die Aussage «für dieses Land gibt
    es keine Daten»: vollständig, plausibel, formatiert und falsch. Gemessen
    liefert `CR.1`/`CHE` **14 Zeilen**.

    Ein leeres `records` bleibt eine Aussage der Quelle und kommt als leere
    Liste zurück. Ein FEHLENDES `records` ist keine Aussage über die Daten,
    sondern über die Antwort — und wird als solcher gemeldet.
    """
    if not isinstance(payload, dict) or "records" not in payload:
        keys = sorted(payload) if isinstance(payload, dict) else type(payload).__name__
        raise UpstreamShapeError(
            "Die UIS-Antwort führt kein Feld `records`. Vorhanden: "
            f"{keys}. Das ist keine leere Treffermenge, sondern eine andere "
            "Antwortform — die Abfrage gehört geprüft, nicht wiederholt."
        )
    records = payload["records"]
    if not isinstance(records, list):
        raise UpstreamShapeError(f"`records` ist {type(records).__name__}, nicht eine Liste.")
    return records


def uis_hints(payload: dict) -> list[str]:
    """Was die Quelle zur Anfrage selbst sagt — im Klartext, im selben Payload.

    Ein unbekannter Ländercode ist kein Fehler-Status. Die UIS antwortet mit
    HTTP 200, leerem `records` und einer Zeile in `hints`:

        {"code": "UIS::HINT::003",
         "message": "The geoUnit could not be found, XXX"}

    Bis zum 2026-08-08 las das niemand. Aus «diesen Code gibt es nicht» wurde
    damit «für dieses Land liegen keine Daten vor» — dieselbe leere Tabelle,
    dieselbe ruhige Formulierung, und der Tippfehler blieb unsichtbar. Genau
    diese Verwechslung ist der Grund, aus dem dieses Repo geprüft wurde: ein
    Ausfall, der wie eine Antwort aussieht.

    `UIS::HINT::001` sagt dasselbe über eine unbekannte Indikator-ID.
    """
    hints = payload.get("hints") if isinstance(payload, dict) else None
    if not isinstance(hints, list):
        return []
    out: list[str] = []
    for h in hints:
        if isinstance(h, dict):
            text = str(h.get("message", "")).strip()
            code = str(h.get("code", "")).strip()
            if text:
                out.append(f"{text} ({code})" if code else text)
        elif isinstance(h, str) and h.strip():
            out.append(h.strip())
    return out


async def uis_get_versions() -> list[dict]:
    """Ruft verfügbare Datenbankversionen ab."""
    url = f"{UNESCO_BASE_URL}/versions"
    async with _uis_semaphore:
        data = await http_get_json(url)
    return data if isinstance(data, list) else data.get("versions", [])


# ─── OECD SDMX API ────────────────────────────────────────────────────────────


async def oecd_get_dataflows(agency: str = "OECD.EDU.IMEP") -> list[dict]:
    """Ruft verfügbare OECD-Dataflows für Bildung ab."""
    url = f"{OECD_BASE_URL}/dataflow/{agency}"
    params = {"format": "jsondata"}
    try:
        async with _oecd_semaphore:
            data = await http_get_json(url, params=params)
        # SDMX-JSON Struktur parsen
        structures = data.get("data", {}).get("dataflows", [])
        return structures
    except Exception:
        return []


async def oecd_get_education_data(
    dataflow_id: str,
    countries: Optional[list[str]] = None,
    start_period: Optional[str] = None,
    end_period: Optional[str] = None,
    agency: str = "OECD.EDU.IMEP",
) -> dict:
    """Ruft OECD-Bildungsdaten via SDMX REST API ab.

    Beispiel: EAG_FISC = Education at a Glance Ausgaben
    """
    # Länder-Filter aufbauen (SDMX-Syntax: CHE+DEU+AUT oder leer für alle)
    country_filter = "+".join(countries) if countries else ""

    url = f"{OECD_BASE_URL}/data/{agency},DSD_{dataflow_id}@DF_{dataflow_id}"
    if country_filter:
        url += f"/{country_filter}"
    else:
        url += "/."

    params: dict = {"dimensionAtObservation": "AllDimensions", "format": "jsondata"}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period

    async with _oecd_semaphore:
        return await http_get_json(url, params=params)


async def oecd_search_education_datasets(keyword: str) -> list[dict]:
    """Sucht nach OECD-Datensätzen mit Bildungsbezug via SDMX Catalogue."""
    url = f"{OECD_BASE_URL}/dataflow/all"
    params = {"format": "jsondata", "references": "none"}
    try:
        async with _oecd_semaphore:
            data = await http_get_json(url, params=params)
        all_flows = data.get("data", {}).get("dataflows", [])
        # Filtern nach Keyword
        keyword_lower = keyword.lower()
        return [f for f in all_flows if keyword_lower in json.dumps(f).lower()]
    except Exception:
        return []


# ─── Fehlerbehandlung ─────────────────────────────────────────────────────────


def raise_if_transient(e: Exception, context: str = "") -> None:
    """Loest MCPError aus, wenn `e` ein transienter Upstream-Fehler ist.

    Adressiert Audit-Finding OBS-001 (Trennung Protocol vs. Execution
    Errors). Idee:

    - 5xx / Timeout / Connect-Failures sind transient -> MCP-Host kann
      sinnvoll retryen. Wir raisen MCPError(code=INTERNAL_ERROR), damit
      der Host das Signal bekommt.
    - 4xx ist Client-Error (z.B. unbekannter Indikator, 400 Bad Request).
      Hier ist Retry sinnlos -> Caller formatiert via handle_api_error()
      als Tool-Result-Text, damit das LLM die Fehlermeldung sieht und
      sich anpassen kann.

    Diese Funktion ist ein No-op fuer 4xx + andere Exceptions; der Caller
    fuehrt danach den text-basierten Pfad aus.
    """
    # Lokaler Import: MCPError ist nur in Tool-Bodies relevant; das
    # vermeidet einen Modul-Level-Import-Cycle bei Test-Bootstrapping.
    from mcp.shared.exceptions import MCPError
    from mcp.types import INTERNAL_ERROR

    ctx = f" [{context}]" if context else ""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if 500 <= status < 600:
            raise MCPError(code=INTERNAL_ERROR, message=f"Upstream API {status}{ctx}")
        # 4xx oder Sonstiges: kein raise, Caller formatiert als Text.
        return
    if isinstance(e, (httpx.TimeoutException, httpx.ConnectError)):
        raise MCPError(
            code=INTERNAL_ERROR,
            message=f"Upstream API unreachable{ctx}: {type(e).__name__}",
        )


def handle_api_error(e: Exception, context: str = "") -> str:
    """Einheitliche Fehlerformatierung mit hilfreichen Hinweisen."""
    ctx = f" [{context}]" if context else ""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 400:
            return f"Fehler{ctx}: Ungültige Anfrage. Bitte Indikator-ID und Ländercode prüfen (ISO 3166-1 Alpha-3)."
        elif status == 404:
            return f"Fehler{ctx}: Ressource nicht gefunden. Indikator oder Ländercode existiert möglicherweise nicht."
        elif status == 429:
            return f"Fehler{ctx}: Anfragelimit erreicht. Bitte etwas warten und erneut versuchen."
        elif status == 503:
            return f"Fehler{ctx}: API vorübergehend nicht verfügbar. Bitte später erneut versuchen."
        return f"Fehler{ctx}: HTTP {status} – {e.response.text[:200]}"
    elif isinstance(e, httpx.TimeoutException):
        return f"Fehler{ctx}: Zeitüberschreitung. Die API hat nicht rechtzeitig geantwortet."
    elif isinstance(e, httpx.ConnectError):
        return f"Fehler{ctx}: Verbindung fehlgeschlagen. Netzwerkverbindung oder API-Verfügbarkeit prüfen."
    return f"Fehler{ctx}: Unerwarteter Fehler – {type(e).__name__}: {str(e)[:200]}"


# ─── Formatierungshilfen ──────────────────────────────────────────────────────


def format_uis_data_as_markdown(
    data: dict,
    indicator_id: str,
    indicator_name: str = "",
) -> str:
    """Formatiert UIS-Rohdaten als lesbare Markdown-Tabelle."""
    observations = uis_records(data)
    hints = uis_hints(data)
    if not observations:
        if hints:
            # Die Quelle hat einen Grund genannt. Ihn zu verschweigen und
            # «keine Daten» zu schreiben, macht aus einem Tippfehler einen
            # Befund über die Welt.
            return f"_Keine Daten für Indikator {indicator_id}._ Die Quelle nennt dazu:\n\n" + "\n".join(
                f"- {h}" for h in hints
            )
        return f"_Keine Daten für Indikator {indicator_id} gefunden._"

    lines = [f"## {indicator_name or indicator_id}", ""]
    if hints:
        lines += ["_Hinweise der Quelle:_"] + [f"- {h}" for h in hints] + [""]

    # Gruppieren nach Land.
    #
    # Eine Datenzeile führt NUR den Code. `geoUnitName` gab es nie; der Ausdruck
    # fiel deshalb immer auf den Code zurück und schrieb «CHE (CHE)» — ein
    # Klammerzusatz, der aussah, als stünde davor ein Name. Die Namen liegen
    # unter `/definitions/geounits` und damit hinter einem zweiten Aufruf; sie
    # hier zu erfinden wäre die schlechtere Antwort als der blosse Code.
    by_country: dict[str, list] = {}
    for obs in observations:
        country = obs.get("geoUnit", obs.get("geoUnitId", "?"))
        by_country.setdefault(country, []).append(obs)

    for country, obs_list in sorted(by_country.items()):
        # Sortieren nach Jahr
        obs_list.sort(key=lambda x: x.get("year", 0))
        latest = obs_list[-1]
        value = latest.get("value", "–")
        year = latest.get("year", "?")
        qualifier = latest.get("qualifier")
        note = f", {UIS_QUALIFIERS.get(qualifier, qualifier)}" if qualifier else ""
        lines.append(f"**{country}**: {value} ({year}{note})")

    lines.append("")
    lines.append("_Ländercodes nach ISO 3166-1 Alpha-3; Klarnamen via `uis_list_countries`._")

    lines.append("")
    lines.append("_Quelle: UNESCO Institute for Statistics (UIS)_")
    return "\n".join(lines)


# Was `qualifier` in einer UIS-Zeile bedeutet. Die Quelle liefert den Code
# ohne Legende; ohne sie steht in der Statusspalte ein Kürzel, das der Leser
# raten muss. Ein leeres Feld heisst «von der nationalen Statistik gemeldet»
# und ist damit die aussagekräftigste Zeile von allen — sie darf nicht
# gleich aussehen wie eine Schätzung.
UIS_QUALIFIERS = {
    "UIS_EST": "UIS-Schätzung",
    "NAT_EST": "nationale Schätzung",
}


def format_country_timeseries(
    observations: list[dict],
    country_name: str,
    indicator_id: str,
    hints: Optional[list[str]] = None,
) -> str:
    """Formatiert eine Zeitreihe für ein einzelnes Land.

    Die Statusspalte las bis zum 2026-08-08 `observationStatus` — ein Feld,
    das die Quelle nicht führt. Sie war deshalb in jeder Zeile leer, und eine
    UIS-Schätzung sah aus wie ein gemeldeter Wert. Bei `LR.AG15T99` sind das
    1306 von 9818 Werten. Die Quelle schreibt `qualifier`.
    """
    if not observations:
        if hints:
            return f"_Keine Zeitreihendaten für {country_name}._ Die Quelle nennt dazu:\n\n" + "\n".join(
                f"- {h}" for h in hints
            )
        return f"_Keine Zeitreihendaten für {country_name}._"

    sorted_obs = sorted(observations, key=lambda x: x.get("year", 0))
    rows = ["| Jahr | Wert | Status |", "|------|------|--------|"]
    for obs in sorted_obs:
        year = obs.get("year", "?")
        value = obs.get("value", "–")
        qualifier = obs.get("qualifier")
        status = UIS_QUALIFIERS.get(qualifier, qualifier) if qualifier else "gemeldet"
        rows.append(f"| {year} | {value} | {status} |")

    out = f"### {country_name} – {indicator_id}\n\n" + "\n".join(rows)
    if hints:
        out += "\n\n_Hinweise der Quelle:_\n" + "\n".join(f"- {h}" for h in hints)
    return out
