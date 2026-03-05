"""
Gemeinsame HTTP-Client-Infrastruktur für UNESCO UIS und OECD APIs.
Enthält Rate-Limiting, Caching und einheitliche Fehlerbehandlung.
"""

import json
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Basis-URLs ───────────────────────────────────────────────────────────────

UNESCO_BASE_URL = "https://api.uis.unesco.org/api/public"
OECD_BASE_URL = "https://sdmx.oecd.org/public/rest"

# ─── Bekannte UNESCO-Bildungsindikatoren ──────────────────────────────────────

UNESCO_EDUCATION_INDICATORS = {
    # Alphabetisierung
    "LR.AG15T99": "Alphabetisierungsrate Erwachsene (15+)",
    "LR.AG15T24": "Alphabetisierungsrate Jugendliche (15–24)",
    "LR.AG15T24.F": "Alphabetisierungsrate Jugendliche weiblich",
    "LR.AG15T24.M": "Alphabetisierungsrate Jugendliche männlich",
    # Schulabschluss & Einschulungsraten
    "CR.1": "Abschlussquote Primarstufe",
    "CR.2": "Abschlussquote Sekundarstufe I",
    "CR.3": "Abschlussquote Sekundarstufe II",
    "NERA.1": "Einschulungsrate bereinigt Primarstufe",
    "NERA.2": "Einschulungsrate bereinigt Sekundarstufe I",
    "NERA.3": "Einschulungsrate bereinigt Sekundarstufe II",
    "OFST.1.CP": "Kinder ausserhalb der Schule (Primarschulalter)",
    # Bildungsausgaben
    "XUNIT.FSGOV.FFNTR.L1.PTGDP": "Bildungsausgaben als % des BIP (Primarstufe)",
    "XUNIT.FSGOV.FFNTR.L23.PTGDP": "Bildungsausgaben als % des BIP (Sekundarstufe)",
    "XUNIT.FSGOV.FFNTR.L1T3.PTGDP": "Bildungsausgaben als % des BIP (gesamt)",
    "XGDP.FSGOV": "Öffentliche Bildungsausgaben als % des BIP",
    # Lehrer
    "PTR.1": "Schüler-Lehrer-Verhältnis Primarstufe",
    "PTR.2": "Schüler-Lehrer-Verhältnis Sekundarstufe I",
    "PTR.3": "Schüler-Lehrer-Verhältnis Sekundarstufe II",
    "TRTP.1": "Anteil ausgebildete Lehrpersonen Primarstufe (%)",
    # Geschlechterparität
    "GPI.NERA.1": "Geschlechterparitätsindex Einschulung Primarstufe",
    "GPI.CR.1": "Geschlechterparitätsindex Abschluss Primarstufe",
    # SDG 4
    "SDG4": "SDG 4 Bildungsqualität Gesamtindikator",
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
HEADERS_JSON = {"Accept": "application/json"}


async def http_get_json(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
) -> Any:
    """Führt einen HTTP GET-Request aus und gibt JSON zurück."""
    request_headers = {**HEADERS_JSON, **(headers or {})}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(url, params=params, headers=request_headers)
        response.raise_for_status()
        return response.json()


async def http_get_text(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
) -> str:
    """Führt einen HTTP GET-Request aus und gibt Text zurück."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(url, params=params, headers=headers or {})
        response.raise_for_status()
        return response.text


# ─── UNESCO UIS API ───────────────────────────────────────────────────────────


async def uis_get_indicators(theme: Optional[str] = None) -> list[dict]:
    """Ruft verfügbare UIS-Indikatoren ab."""
    url = f"{UNESCO_BASE_URL}/indicators"
    params: dict = {}
    if theme:
        params["theme"] = theme
    data = await http_get_json(url, params=params)
    return data if isinstance(data, list) else data.get("indicators", [])


async def uis_get_geo_units() -> list[dict]:
    """Ruft verfügbare geografische Einheiten (Länder/Regionen) ab."""
    url = f"{UNESCO_BASE_URL}/geo-units"
    data = await http_get_json(url)
    return data if isinstance(data, list) else data.get("geoUnits", [])


async def uis_get_data(
    indicator: str,
    geo_unit: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    version: Optional[str] = None,
) -> dict:
    """Ruft UIS-Datenpunkte für einen Indikator ab."""
    url = f"{UNESCO_BASE_URL}/data"
    params: dict = {"indicator": indicator}
    if geo_unit:
        params["geoUnit"] = geo_unit
    if start_year:
        params["startYear"] = start_year
    if end_year:
        params["endYear"] = end_year
    if version:
        params["version"] = version
    return await http_get_json(url, params=params)


async def uis_get_versions() -> list[dict]:
    """Ruft verfügbare Datenbankversionen ab."""
    url = f"{UNESCO_BASE_URL}/versions"
    data = await http_get_json(url)
    return data if isinstance(data, list) else data.get("versions", [])


# ─── OECD SDMX API ────────────────────────────────────────────────────────────


async def oecd_get_dataflows(agency: str = "OECD.EDU.IMEP") -> list[dict]:
    """Ruft verfügbare OECD-Dataflows für Bildung ab."""
    url = f"{OECD_BASE_URL}/dataflow/{agency}"
    params = {"format": "jsondata"}
    try:
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

    return await http_get_json(url, params=params)


async def oecd_search_education_datasets(keyword: str) -> list[dict]:
    """Sucht nach OECD-Datensätzen mit Bildungsbezug via SDMX Catalogue."""
    url = f"{OECD_BASE_URL}/dataflow/all"
    params = {"format": "jsondata", "references": "none"}
    try:
        data = await http_get_json(url, params=params)
        all_flows = data.get("data", {}).get("dataflows", [])
        # Filtern nach Keyword
        keyword_lower = keyword.lower()
        return [
            f
            for f in all_flows
            if keyword_lower in json.dumps(f).lower()
        ]
    except Exception:
        return []


# ─── Fehlerbehandlung ─────────────────────────────────────────────────────────


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
    observations = data.get("observations", data.get("data", []))
    if not observations:
        return f"_Keine Daten für Indikator {indicator_id} gefunden._"

    lines = [f"## {indicator_name or indicator_id}", ""]

    # Gruppieren nach Land
    by_country: dict[str, list] = {}
    for obs in observations:
        country = obs.get("geoUnit", obs.get("geoUnitId", "?"))
        country_name = obs.get("geoUnitName", country)
        key = f"{country_name} ({country})"
        if key not in by_country:
            by_country[key] = []
        by_country[key].append(obs)

    for country_label, obs_list in sorted(by_country.items()):
        # Sortieren nach Jahr
        obs_list.sort(key=lambda x: x.get("year", 0))
        latest = obs_list[-1]
        value = latest.get("value", "–")
        year = latest.get("year", "?")
        lines.append(f"**{country_label}**: {value} ({year})")

    lines.append("")
    lines.append("_Quelle: UNESCO Institute for Statistics (UIS)_")
    return "\n".join(lines)


def format_country_timeseries(
    observations: list[dict],
    country_name: str,
    indicator_id: str,
) -> str:
    """Formatiert eine Zeitreihe für ein einzelnes Land."""
    if not observations:
        return f"_Keine Zeitreihendaten für {country_name}._"

    sorted_obs = sorted(observations, key=lambda x: x.get("year", 0))
    rows = ["| Jahr | Wert | Status |", "|------|------|--------|"]
    for obs in sorted_obs:
        year = obs.get("year", "?")
        value = obs.get("value", "–")
        status = obs.get("observationStatus", "")
        rows.append(f"| {year} | {value} | {status} |")

    return f"### {country_name} – {indicator_id}\n\n" + "\n".join(rows)
