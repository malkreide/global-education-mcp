"""
Global Education Data MCP Server
==================================
MCP-Server für internationalen Bildungsvergleich via UNESCO UIS und OECD APIs.

Datenquellen:
  - UNESCO Institute for Statistics (UIS): 4'000+ Indikatoren zu Bildung,
    Wissenschaft, Kultur und Kommunikation für alle UNESCO-Länder.
  - OECD SDMX API: Education at a Glance – jährliches Referenzwerk für
    internationale Bildungsvergleiche (38 OECD-Länder + Partner).

Zielgruppe: Bildungsforschung, Schuladministration, Politikanalyse.
Entwickelt von: Schulamt der Stadt Zürich.
"""

import json
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from .api_client import (
    OECD_EDUCATION_DATAFLOWS,
    UNESCO_EDUCATION_INDICATORS,
    format_country_timeseries,
    format_uis_data_as_markdown,
    handle_api_error,
    oecd_get_dataflows,
    oecd_get_education_data,
    oecd_search_education_datasets,
    uis_get_data,
    uis_get_geo_units,
    uis_get_indicators,
    uis_get_versions,
)

# ─── Server Setup ─────────────────────────────────────────────────────────────

mcp = FastMCP(
    "global_education_mcp",
    instructions=(
        "MCP-Server für internationale Bildungsdaten. "
        "Bietet Zugriff auf zwei komplementäre Quellen: "
        "(1) UNESCO UIS API: 4'000+ Bildungsindikatoren für alle UNESCO-Länder – "
        "Alphabetisierung, Einschulungsraten, Schulabschlüsse, Bildungsausgaben, Lehrerquoten. "
        "(2) OECD SDMX API: Education at a Glance – vertiefende Bildungsdaten "
        "für 38 OECD-Länder inkl. Schweiz, Deutschland, Österreich. "
        "Ideal für Ländervergleiche, Zeitreihenanalysen und SDG-4-Monitoring. "
        "Alle Daten frei zugänglich, keine API-Schlüssel erforderlich. "
        "Ländercodes: ISO 3166-1 Alpha-3 (z.B. CHE=Schweiz, DEU=Deutschland, AUT=Österreich)."
    ),
    host=os.environ.get("MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("PORT", "8000")),
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UNESCO UIS – Discovery & Exploration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class UISIndicatorsInput(BaseModel):
    """Input für die Abfrage verfügbarer UIS-Indikatoren."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    theme: Optional[str] = Field(
        default=None,
        description="Filter nach Thema, z.B. 'EDUCATION', 'SCIENCE', 'CULTURE'. "
        "Ohne Angabe werden alle Themen zurückgegeben.",
        max_length=50,
    )
    search: Optional[str] = Field(
        default=None,
        description="Freitextsuche in Indikatorname und -beschreibung.",
        max_length=200,
    )
    limit: int = Field(
        default=50,
        description="Maximale Anzahl zurückgegebener Indikatoren.",
        ge=1,
        le=500,
    )


@mcp.tool(
    name="uis_list_indicators",
    annotations={
        "title": "UIS-Indikatoren auflisten",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def uis_list_indicators(params: UISIndicatorsInput) -> str:
    """Listet verfügbare Indikatoren der UNESCO Institute for Statistics auf.

    Die UIS bietet über 4'000 Indikatoren zu Bildung, Wissenschaft, Kultur
    und Kommunikation. Diese Funktion dient zur Exploration und Indikatorsuche.

    Wichtige Indikator-Kategorien:
      - Alphabetisierung (LR.*): Lese-/Schreibkompetenz nach Alter, Geschlecht
      - Einschulungsraten (NERA.*): Netto-Einschulungsraten nach Schulstufe
      - Schulabschlüsse (CR.*): Abschlussquoten Primar- bis Sekundarstufe
      - Bildungsausgaben (XGDP.*, XUNIT.*): % BIP, pro Schüler
      - Lehrerquoten (PTR.*, TRTP.*): Schüler-Lehrer-Verhältnis, Ausbildungsgrad

    Args:
        params: theme (optional), search (optional), limit

    Returns:
        Markdown-Liste mit Indikator-IDs und Beschreibungen
    """
    try:
        indicators = await uis_get_indicators(theme=params.theme)

        # Freitextfilter anwenden
        if params.search:
            search_lower = params.search.lower()
            indicators = [
                i
                for i in indicators
                if search_lower in json.dumps(i).lower()
            ]

        # Limit anwenden
        indicators = indicators[: params.limit]

        if not indicators:
            return f"_Keine Indikatoren gefunden für Thema='{params.theme}', Suche='{params.search}'._"

        lines = [
            "## UNESCO UIS – Verfügbare Indikatoren",
            f"_{len(indicators)} Einträge (von insgesamt 4'000+)_",
            "",
        ]
        for ind in indicators:
            ind_id = ind.get("indicatorId", ind.get("id", "?"))
            ind_name = ind.get("indicatorName", ind.get("name", "–"))
            theme_tag = ind.get("theme", "")
            lines.append(f"- **`{ind_id}`** – {ind_name} _{theme_tag}_")

        lines.append("")
        lines.append("_Quelle: UNESCO Institute for Statistics (api.uis.unesco.org)_")
        return "\n".join(lines)

    except Exception as e:
        # Fallback: bekannte Indikatoren aus der lokalen Tabelle anzeigen
        if params.search:
            search_lower = params.search.lower()
            filtered = {
                k: v
                for k, v in UNESCO_EDUCATION_INDICATORS.items()
                if search_lower in k.lower() or search_lower in v.lower()
            }
        else:
            filtered = UNESCO_EDUCATION_INDICATORS

        lines = [
            "## Bekannte UNESCO UIS Bildungsindikatoren",
            f"_(API nicht erreichbar – zeige lokale Auswahl: {handle_api_error(e)})_",
            "",
        ]
        for ind_id, ind_name in list(filtered.items())[: params.limit]:
            lines.append(f"- **`{ind_id}`** – {ind_name}")
        return "\n".join(lines)


# ─── UIS: Geografische Einheiten ──────────────────────────────────────────────


class UISGeoUnitsInput(BaseModel):
    """Input für die Abfrage verfügbarer Länder und Regionen."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    search: Optional[str] = Field(
        default=None,
        description="Filter nach Land- oder Regionsname (z.B. 'Switzerland', 'Europe').",
        max_length=100,
    )
    entity_type: Optional[str] = Field(
        default=None,
        description="Typ der Einheit: 'COUNTRY', 'REGION', 'SDG_REGION' etc.",
        max_length=50,
    )


@mcp.tool(
    name="uis_list_countries",
    annotations={
        "title": "UIS-Länder und Regionen auflisten",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def uis_list_countries(params: UISGeoUnitsInput) -> str:
    """Listet verfügbare Länder und Regionen in der UNESCO UIS-Datenbank auf.

    Gibt ISO 3166-1 Alpha-3 Codes zurück, die für Datenabfragen benötigt werden.
    Beispiele: CHE (Schweiz), DEU (Deutschland), AUT (Österreich), FRA (Frankreich).

    Neben Einzelländern sind auch regionale Aggregate verfügbar:
    Weltregionen, Einkommensgruppen (World Bank), SDG-Regionen.

    Args:
        params: search (optional Textfilter), entity_type (optional)

    Returns:
        Markdown-Liste mit ISO-Codes und Ländernamen
    """
    try:
        geo_units = await uis_get_geo_units()

        # Filter anwenden
        if params.search:
            search_lower = params.search.lower()
            geo_units = [
                g for g in geo_units if search_lower in json.dumps(g).lower()
            ]
        if params.entity_type:
            geo_units = [
                g for g in geo_units if g.get("entityType", "").upper() == params.entity_type.upper()
            ]

        if not geo_units:
            return "_Keine geografischen Einheiten gefunden._"

        lines = [
            "## UNESCO UIS – Länder und Regionen",
            f"_{len(geo_units)} Einträge_",
            "",
        ]
        for g in geo_units[:200]:  # Max. 200 für Übersichtlichkeit
            geo_id = g.get("geoUnitId", g.get("id", "?"))
            geo_name = g.get("geoUnitName", g.get("name", "–"))
            entity_type = g.get("entityType", "")
            lines.append(f"- **`{geo_id}`** – {geo_name} _{entity_type}_")

        lines.append("")
        lines.append("_Ländercodes: ISO 3166-1 Alpha-3 Standard_")
        return "\n".join(lines)

    except Exception as e:
        return (
            f"## Wichtige ISO 3166-1 Alpha-3 Ländercodes\n\n"
            f"_(API nicht erreichbar – {handle_api_error(e)})_\n\n"
            "- **CHE** – Schweiz\n"
            "- **DEU** – Deutschland\n"
            "- **AUT** – Österreich\n"
            "- **FRA** – Frankreich\n"
            "- **FIN** – Finnland\n"
            "- **SGP** – Singapur\n"
            "- **KOR** – Südkorea\n"
            "- **USA** – USA\n"
            "- **JPN** – Japan\n"
            "- **WORLD** – Welt (Durchschnitt)\n"
        )


# ─── UIS: Kerndaten abrufen ───────────────────────────────────────────────────


class UISDataInput(BaseModel):
    """Input für den Abruf von UIS-Bildungsdaten."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    indicator_id: str = Field(
        ...,
        description="Indikator-ID, z.B. 'LR.AG15T99' (Alphabetisierung), "
        "'CR.1' (Primarabschluss), 'XGDP.FSGOV' (Bildungsausgaben % BIP). "
        "Bekannte IDs via uis_list_indicators abrufen.",
        min_length=2,
        max_length=100,
    )
    country_code: Optional[str] = Field(
        default=None,
        description="ISO 3166-1 Alpha-3 Ländercode, z.B. 'CHE', 'DEU', 'AUT'. "
        "Ohne Angabe werden alle Länder zurückgegeben (kann gross sein).",
        min_length=2,
        max_length=10,
    )
    start_year: Optional[int] = Field(
        default=None,
        description="Startjahr der Zeitreihe, z.B. 2010.",
        ge=1970,
        le=2030,
    )
    end_year: Optional[int] = Field(
        default=None,
        description="Endjahr der Zeitreihe, z.B. 2023.",
        ge=1970,
        le=2030,
    )


@mcp.tool(
    name="uis_get_education_data",
    annotations={
        "title": "UIS-Bildungsdaten abrufen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def uis_get_education_data(params: UISDataInput) -> str:
    """Ruft Bildungsdaten von der UNESCO Institute for Statistics API ab.

    Kernfunktion des Servers. Liefert international vergleichbare Daten
    zu einem spezifischen Indikator – für ein Land oder alle Länder.

    Typische Anwendungsfälle:
      - Alphabetisierungsrate der Schweiz: indicator='LR.AG15T99', country='CHE'
      - Bildungsausgaben OECD-Länder: indicator='XGDP.FSGOV', kein Land
      - Schulabschlussquoten Europa: indicator='CR.1' + Jahresfilter
      - Schüler-Lehrer-Verhältnis: indicator='PTR.1'

    Args:
        params: indicator_id (erforderlich), country_code, start_year, end_year

    Returns:
        Markdown-formatierte Tabelle oder Zeitreihe mit Daten und Metadaten
    """
    try:
        raw_data = await uis_get_data(
            indicator=params.indicator_id,
            geo_unit=params.country_code,
            start_year=params.start_year,
            end_year=params.end_year,
        )

        indicator_name = UNESCO_EDUCATION_INDICATORS.get(params.indicator_id, "")

        if params.country_code:
            # Zeitreihe für ein Land
            observations = raw_data.get("observations", raw_data.get("data", []))
            return format_country_timeseries(
                observations=observations,
                country_name=params.country_code,
                indicator_id=f"{params.indicator_id} {indicator_name}",
            )
        else:
            # Länderübersicht
            return format_uis_data_as_markdown(
                data=raw_data,
                indicator_id=params.indicator_id,
                indicator_name=indicator_name,
            )

    except Exception as e:
        return handle_api_error(e, context=f"uis_get_data({params.indicator_id})")


# ─── UIS: Ländervergleich ─────────────────────────────────────────────────────


class UISCompareInput(BaseModel):
    """Input für Mehrländervergleich."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    indicator_id: str = Field(
        ...,
        description="Indikator-ID für den Vergleich, z.B. 'LR.AG15T99'.",
        min_length=2,
        max_length=100,
    )
    country_codes: list[str] = Field(
        ...,
        description="Liste von ISO Alpha-3 Codes, z.B. ['CHE', 'DEU', 'AUT', 'FIN']. "
        "Maximal 15 Länder pro Anfrage.",
        min_length=2,
        max_length=15,
    )
    year: Optional[int] = Field(
        default=None,
        description="Referenzjahr für den Vergleich (neueste verfügbare Daten wenn leer).",
        ge=1990,
        le=2030,
    )


@mcp.tool(
    name="uis_compare_countries",
    annotations={
        "title": "Ländervergleich UIS-Bildungsdaten",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def uis_compare_countries(params: UISCompareInput) -> str:
    """Vergleicht Bildungsindikatoren zwischen mehreren Ländern (UNESCO UIS).

    Ideal für den direkten internationalen Vergleich: Wie steht die Schweiz
    im Vergleich zu Finnland, Singapur und dem OECD-Durchschnitt?

    Args:
        params: indicator_id, country_codes (Liste), year (optional)

    Returns:
        Markdown-Vergleichstabelle sortiert nach Indikatorwert
    """
    indicator_name = UNESCO_EDUCATION_INDICATORS.get(params.indicator_id, params.indicator_id)
    results: list[dict] = []
    errors: list[str] = []

    for code in params.country_codes[:15]:
        try:
            raw = await uis_get_data(
                indicator=params.indicator_id,
                geo_unit=code,
                start_year=params.year,
                end_year=params.year,
            )
            observations = raw.get("observations", raw.get("data", []))
            if observations:
                # Neuesten verfügbaren Wert nehmen
                sorted_obs = sorted(observations, key=lambda x: x.get("year", 0), reverse=True)
                latest = sorted_obs[0]
                results.append(
                    {
                        "country": code,
                        "country_name": latest.get("geoUnitName", code),
                        "value": latest.get("value"),
                        "year": latest.get("year", "?"),
                    }
                )
            else:
                errors.append(f"{code}: keine Daten")
        except Exception as e:
            errors.append(f"{code}: {handle_api_error(e)}")

    if not results:
        return f"_Keine Daten für {params.indicator_id} gefunden. Fehler: {'; '.join(errors)}_"

    # Sortieren nach Wert (absteigend)
    try:
        results.sort(key=lambda x: float(x["value"] or 0), reverse=True)
    except (TypeError, ValueError):
        pass

    lines = [
        f"## Ländervergleich: {indicator_name}",
        f"_Indikator: `{params.indicator_id}` | Quelle: UNESCO UIS_",
        "",
        "| Rang | Land | Code | Wert | Jahr |",
        "|------|------|------|------|------|",
    ]
    for i, r in enumerate(results, 1):
        lines.append(
            f"| {i} | {r['country_name']} | {r['country']} | {r['value']} | {r['year']} |"
        )

    if errors:
        lines.append("")
        lines.append(f"_Nicht verfügbar: {', '.join(errors)}_")

    return "\n".join(lines)


# ─── UIS: SDG-4-Profil für ein Land ──────────────────────────────────────────


class UISCountryProfileInput(BaseModel):
    """Input für das Bildungsprofil eines Landes."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    country_code: str = Field(
        ...,
        description="ISO 3166-1 Alpha-3 Ländercode, z.B. 'CHE' für die Schweiz.",
        min_length=2,
        max_length=10,
    )
    latest_year_only: bool = Field(
        default=True,
        description="True = nur neueste verfügbare Werte; False = Zeitreihe.",
    )


@mcp.tool(
    name="uis_country_education_profile",
    annotations={
        "title": "Bildungsprofil eines Landes (UNESCO UIS)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def uis_country_education_profile(params: UISCountryProfileInput) -> str:
    """Erstellt ein umfassendes Bildungsprofil für ein Land via UNESCO UIS.

    Ruft automatisch die wichtigsten Schlüsselindikatoren ab:
    Alphabetisierung, Einschulungsraten, Abschlussquoten, Bildungsausgaben,
    Schüler-Lehrer-Verhältnis, Geschlechterparität.

    Args:
        params: country_code (ISO Alpha-3), latest_year_only

    Returns:
        Vollständiges Markdown-Bildungsprofil mit allen Kernindikatoren
    """
    key_indicators = [
        ("LR.AG15T99", "Alphabetisierungsrate Erwachsene (%)"),
        ("LR.AG15T24", "Alphabetisierungsrate Jugendliche (%)"),
        ("NERA.1", "Einschulungsrate Primarstufe (%)"),
        ("NERA.2", "Einschulungsrate Sekundarstufe I (%)"),
        ("CR.1", "Abschlussquote Primarstufe (%)"),
        ("CR.2", "Abschlussquote Sekundarstufe I (%)"),
        ("CR.3", "Abschlussquote Sekundarstufe II (%)"),
        ("XGDP.FSGOV", "Bildungsausgaben (% BIP)"),
        ("PTR.1", "Schüler-Lehrer-Verhältnis Primarstufe"),
        ("GPI.NERA.1", "Geschlechterparitätsindex Einschulung"),
    ]

    lines = [
        f"## Bildungsprofil: {params.country_code}",
        "_Quelle: UNESCO Institute for Statistics (UIS) – alle international vergleichbaren Werte_",
        "",
        "| Indikator | Wert | Jahr |",
        "|-----------|------|------|",
    ]

    errors: list[str] = []
    for ind_id, ind_label in key_indicators:
        try:
            raw = await uis_get_data(indicator=ind_id, geo_unit=params.country_code)
            observations = raw.get("observations", raw.get("data", []))
            if observations:
                sorted_obs = sorted(observations, key=lambda x: x.get("year", 0), reverse=True)
                latest = sorted_obs[0]
                value = latest.get("value", "–")
                year = latest.get("year", "?")
                lines.append(f"| {ind_label} | **{value}** | {year} |")
            else:
                lines.append(f"| {ind_label} | _keine Daten_ | – |")
        except Exception as e:
            errors.append(f"{ind_id}: {str(e)[:80]}")
            lines.append(f"| {ind_label} | _nicht verfügbar_ | – |")

    lines.append("")
    lines.append("### Hinweis")
    lines.append(
        "Werte basieren auf den neuesten verfügbaren Meldungen. "
        "Datenlücken entstehen durch fehlende nationale Berichterstattung."
    )
    if errors:
        lines.append(f"\n_Fehler bei: {'; '.join(errors[:3])}_")

    return "\n".join(lines)


# ─── UIS: Datenbankversionen ──────────────────────────────────────────────────


@mcp.tool(
    name="uis_list_versions",
    annotations={
        "title": "UIS-Datenbankversionen auflisten",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def uis_list_versions() -> str:
    """Listet verfügbare Versionen der UNESCO UIS-Datenbank auf.

    Die UIS veröffentlicht mehrmals jährlich neue Datenversionen.
    Nützlich um sicherzustellen, dass mit den neuesten Daten gearbeitet wird.

    Returns:
        Markdown-Liste mit Versionsbezeichnungen und Publikationsdaten
    """
    try:
        versions = await uis_get_versions()
        lines = ["## UNESCO UIS – Datenbankversionen", ""]
        for v in versions[:15]:
            version_id = v.get("version", v.get("id", "?"))
            pub_date = v.get("publicationDate", v.get("date", "–"))
            description = v.get("description", "")
            lines.append(f"- **{version_id}** ({pub_date}) – {description}")
        lines.append("")
        lines.append("_Neueste Version wird standardmässig verwendet._")
        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e, "uis_list_versions")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OECD – Education at a Glance
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.tool(
    name="oecd_list_education_datasets",
    annotations={
        "title": "OECD-Bildungsdatensätze auflisten",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def oecd_list_education_datasets() -> str:
    """Listet verfügbare OECD Education at a Glance Datensätze auf.

    Education at a Glance ist das jährliche Referenzwerk der OECD für
    internationale Bildungsvergleiche. Es umfasst 38 OECD-Länder plus Partner.

    Abgedeckte Themenbereiche:
      - Bildungsbeteiligung und -abschlüsse (EAG_ENRL, EAG_GRAD_ENTR)
      - Bildungsausgaben und Finanzierung (EAG_FISC)
      - Lehrpersonal und Arbeitsbedingungen (EAG_PERS, EAG_PERS_SALARY)
      - Bildungsrendite und Arbeitsmarkt (EAG_EMP_EDUC, EAG_EARN_RATIO)

    Returns:
        Markdown-Liste der Datensätze mit Beschreibungen und Dataflow-IDs
    """
    lines = [
        "## OECD – Education at a Glance Datensätze",
        "_Zugriff via SDMX REST API (sdmx.oecd.org)_",
        "",
    ]

    for dataflow_id, description in OECD_EDUCATION_DATAFLOWS.items():
        lines.append(f"- **`{dataflow_id}`** – {description}")

    lines.append("")
    lines.append("### Verwendung")
    lines.append(
        "Dataflow-IDs für `oecd_get_education_indicator` verwenden. "
        "Ländercodes: ISO 3166-1 Alpha-2 (CHE, DEU, AUT, FRA, FIN, etc.)"
    )
    lines.append("")

    # Versuche, live Daten von OECD zu holen
    try:
        live_flows = await oecd_get_dataflows()
        if live_flows:
            lines.append(f"_API live: {len(live_flows)} Dataflows verfügbar._")
    except Exception:
        lines.append("_Hinweis: OECD-API momentan nicht erreichbar, lokale Datensatzliste gezeigt._")

    return "\n".join(lines)


# ─── OECD: Bildungsdaten abrufen ──────────────────────────────────────────────


class OECDDataInput(BaseModel):
    """Input für OECD Education at a Glance Daten."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    dataflow_id: str = Field(
        ...,
        description="OECD Dataflow-ID, z.B. 'EAG_FISC' (Ausgaben), 'EAG_ENRL' (Einschreibungen). "
        "Verfügbare IDs via oecd_list_education_datasets.",
        min_length=3,
        max_length=50,
    )
    countries: Optional[list[str]] = Field(
        default=None,
        description="ISO 3166-1 Alpha-3 Ländercodes, z.B. ['CHE', 'DEU', 'FIN']. "
        "Ohne Angabe: alle verfügbaren Länder (kann grosse Datenmenge erzeugen).",
        max_length=20,
    )
    start_period: Optional[str] = Field(
        default=None,
        description="Startzeitraum im SDMX-Format, z.B. '2015' oder '2015-A'.",
        max_length=10,
    )
    end_period: Optional[str] = Field(
        default=None,
        description="Endzeitraum im SDMX-Format, z.B. '2022'.",
        max_length=10,
    )


@mcp.tool(
    name="oecd_get_education_indicator",
    annotations={
        "title": "OECD-Bildungsindikatoren abrufen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def oecd_get_education_indicator(params: OECDDataInput) -> str:
    """Ruft Bildungsdaten aus dem OECD Education at a Glance Report ab.

    Greift auf die OECD SDMX REST API zu. Liefert strukturierte Daten
    für OECD-Länder zu Bildungsausgaben, Einschreibungsraten, Lehrergehältern etc.

    Beispiele:
      - Bildungsausgaben Schweiz/DE/AT: dataflow='EAG_FISC', countries=['CHE','DEU','AUT']
      - Lehrergehälter OECD: dataflow='EAG_PERS_SALARY'
      - Beschäftigung nach Bildungsabschluss: dataflow='EAG_EMP_EDUC'

    Args:
        params: dataflow_id, countries (optional), start_period, end_period

    Returns:
        Markdown-formatierte Datentabelle oder Rohdaten-Zusammenfassung
    """
    try:
        raw = await oecd_get_education_data(
            dataflow_id=params.dataflow_id,
            countries=params.countries,
            start_period=params.start_period,
            end_period=params.end_period,
        )

        dataset_name = OECD_EDUCATION_DATAFLOWS.get(params.dataflow_id, params.dataflow_id)
        countries_label = ", ".join(params.countries) if params.countries else "alle Länder"

        # SDMX-JSON Struktur verarbeiten
        data_sets = raw.get("dataSets", [])
        structure = raw.get("structure", {})
        dimensions = structure.get("dimensions", {}).get("observation", [])

        if not data_sets:
            return (
                f"## OECD – {dataset_name}\n\n"
                f"_Keine Daten für {params.dataflow_id} / {countries_label} verfügbar._\n\n"
                f"Tipp: Dataflow-ID und Ländercodes via `oecd_list_education_datasets` prüfen."
            )

        observations = data_sets[0].get("observations", {})
        obs_count = len(observations)

        lines = [
            f"## OECD Education at a Glance – {dataset_name}",
            f"_Dataflow: `{params.dataflow_id}` | Länder: {countries_label}_",
            f"_Beobachtungen: {obs_count}_",
            "",
        ]

        # Dimensionen ausgeben für Orientierung
        if dimensions:
            lines.append("### Dimensionen")
            for dim in dimensions[:6]:
                dim_id = dim.get("id", "?")
                dim_name = dim.get("name", "–")
                values_count = len(dim.get("values", []))
                lines.append(f"- **{dim_id}** ({dim_name}): {values_count} Werte")
            lines.append("")

        # Erste Beobachtungen als Beispiel
        if obs_count > 0:
            lines.append("### Datenausschnitt (erste 20 Beobachtungen)")
            lines.append("_Für vollständige Analyse: Rohdaten direkt verarbeiten_")
            lines.append("")

            sample_items = list(observations.items())[:20]
            for key, value_list in sample_items:
                obs_value = value_list[0] if value_list else "–"
                lines.append(f"- `{key}`: {obs_value}")

        lines.append("")
        lines.append("_Quelle: OECD SDMX API (sdmx.oecd.org) – Education at a Glance_")
        return "\n".join(lines)

    except Exception as e:
        return (
            f"## OECD – {params.dataflow_id}\n\n"
            f"{handle_api_error(e, context=f'oecd({params.dataflow_id})')}\n\n"
            f"**Hinweis:** Die OECD SDMX API hat komplexe Dataflow-IDs.\n"
            f"Bekannte Bildungs-Dataflows: {', '.join(OECD_EDUCATION_DATAFLOWS.keys())}\n"
            f"OECD Data Explorer: https://data-explorer.oecd.org/"
        )


# ─── OECD: Datensätze durchsuchen ─────────────────────────────────────────────


class OECDSearchInput(BaseModel):
    """Input für die OECD-Datensatzsuche."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    keyword: str = Field(
        ...,
        description="Suchbegriff für OECD-Datensätze, z.B. 'education', 'literacy', 'teachers'.",
        min_length=2,
        max_length=100,
    )
    limit: int = Field(
        default=20,
        description="Maximale Anzahl Ergebnisse.",
        ge=1,
        le=100,
    )


@mcp.tool(
    name="oecd_search_datasets",
    annotations={
        "title": "OECD-Datensätze durchsuchen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def oecd_search_datasets(params: OECDSearchInput) -> str:
    """Durchsucht alle OECD-Datensätze nach einem Stichwort.

    Über die OECD SDMX API sind hunderte Datensätze verfügbar.
    Diese Funktion findet Datensätze mit Bildungsbezug oder anderen Themen.

    Args:
        params: keyword, limit

    Returns:
        Markdown-Liste gefundener Datensätze mit Dataflow-IDs
    """
    try:
        results = await oecd_search_education_datasets(params.keyword)
        results = results[: params.limit]

        if not results:
            return (
                f"_Keine OECD-Datensätze für '{params.keyword}' gefunden._\n\n"
                f"Tipp: Englische Begriffe verwenden, z.B. 'education', 'school', 'literacy'.\n"
                f"OECD Data Explorer: https://data-explorer.oecd.org/"
            )

        lines = [
            f"## OECD-Datensätze für '{params.keyword}'",
            f"_{len(results)} Ergebnisse_",
            "",
        ]
        for r in results:
            ds_id = r.get("id", "?")
            ds_name = r.get("name", r.get("names", {}).get("en", "–"))
            agency = r.get("agencyID", "")
            lines.append(f"- **`{ds_id}`** ({agency}) – {ds_name}")

        lines.append("")
        lines.append("_Quelle: OECD SDMX Catalogue API_")
        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, f"oecd_search({params.keyword})")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Crossquellen: Kombinierte Analysewerkzeuge
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class CrossSourceInput(BaseModel):
    """Input für quellübergreifende Analysen."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    country_codes: list[str] = Field(
        ...,
        description="Liste von ISO Alpha-3 Codes für Bildungsvergleich, "
        "z.B. ['CHE', 'DEU', 'AUT', 'FIN', 'SGP'].",
        min_length=2,
        max_length=10,
    )
    focus: str = Field(
        default="literacy",
        description="Analysefokus: 'literacy' (Alphabetisierung), "
        "'spending' (Ausgaben), 'completion' (Abschlüsse), "
        "'teachers' (Lehrpersonen), 'enrollment' (Einschulungsraten).",
        pattern="^(literacy|spending|completion|teachers|enrollment)$",
    )


@mcp.tool(
    name="education_benchmark_countries",
    annotations={
        "title": "Bildungsbenchmark mehrerer Länder",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def education_benchmark_countries(params: CrossSourceInput) -> str:
    """Benchmarkt mehrere Länder auf einem Bildungsthema via UNESCO UIS.

    Automatisch werden die passenden Indikatoren für den gewählten Fokus
    ausgewählt und ein strukturierter Vergleich erstellt.

    Fokus-Optionen:
      - literacy: Alphabetisierungsraten (Erwachsene + Jugendliche)
      - spending: Bildungsausgaben (% BIP, verschiedene Stufen)
      - completion: Abschlussquoten (Primar, Sek I, Sek II)
      - teachers: Schüler-Lehrer-Verhältnis + Lehrerausbildung
      - enrollment: Einschulungsraten nach Schulstufe

    Args:
        params: country_codes, focus

    Returns:
        Vollständiger Benchmarkreport mit Tabellen für alle relevanten Indikatoren
    """
    focus_indicators = {
        "literacy": [
            ("LR.AG15T99", "Alphabetisierungsrate Erwachsene 15+ (%)"),
            ("LR.AG15T24", "Alphabetisierungsrate Jugendliche 15–24 (%)"),
        ],
        "spending": [
            ("XGDP.FSGOV", "Bildungsausgaben gesamt (% BIP)"),
            ("XUNIT.FSGOV.FFNTR.L1T3.PTGDP", "Ausgaben Primar+Sek (% BIP)"),
        ],
        "completion": [
            ("CR.1", "Abschlussquote Primarstufe (%)"),
            ("CR.2", "Abschlussquote Sekundarstufe I (%)"),
            ("CR.3", "Abschlussquote Sekundarstufe II (%)"),
        ],
        "teachers": [
            ("PTR.1", "Schüler-Lehrer-Verhältnis Primarstufe"),
            ("PTR.2", "Schüler-Lehrer-Verhältnis Sekundarstufe I"),
            ("TRTP.1", "Anteil ausgebildete Lehrpersonen Primarstufe (%)"),
        ],
        "enrollment": [
            ("NERA.1", "Nettoeinschulungsrate Primarstufe (%)"),
            ("NERA.2", "Nettoeinschulungsrate Sekundarstufe I (%)"),
            ("OFST.1.CP", "Kinder ausserhalb der Schule (%)"),
        ],
    }

    selected = focus_indicators.get(params.focus, focus_indicators["literacy"])
    countries_label = " · ".join(params.country_codes)

    lines = [
        f"## Bildungsbenchmark: {params.focus.capitalize()}",
        f"_Länder: {countries_label} | Quelle: UNESCO UIS_",
        "",
    ]

    for ind_id, ind_label in selected:
        lines.append(f"### {ind_label}")
        lines.append(f"_Indikator: `{ind_id}`_")
        lines.append("")
        lines.append("| Rang | Land | Wert | Jahr |")
        lines.append("|------|------|------|------|")

        results: list[dict] = []
        for code in params.country_codes:
            try:
                raw = await uis_get_data(indicator=ind_id, geo_unit=code)
                obs = raw.get("observations", raw.get("data", []))
                if obs:
                    latest = sorted(obs, key=lambda x: x.get("year", 0), reverse=True)[0]
                    results.append(
                        {
                            "country": code,
                            "value": latest.get("value"),
                            "year": latest.get("year", "?"),
                        }
                    )
                else:
                    results.append({"country": code, "value": None, "year": "–"})
            except Exception:
                results.append({"country": code, "value": None, "year": "–"})

        try:
            results.sort(
                key=lambda x: float(x["value"] or 0) if x["value"] is not None else -1,
                reverse=True,
            )
        except (TypeError, ValueError):
            pass

        for i, r in enumerate(results, 1):
            val_display = r["value"] if r["value"] is not None else "–"
            lines.append(f"| {i} | {r['country']} | {val_display} | {r['year']} |")

        lines.append("")

    lines.append("---")
    lines.append(
        "_Daten: UNESCO Institute for Statistics. Datenlücken entstehen durch fehlende nationale Meldungen._"
    )
    return "\n".join(lines)


# ─── Ressourcen ────────────────────────────────────────────────────────────────


@mcp.resource("education://indicators/unesco")
async def resource_unesco_indicators() -> str:
    """UNESCO UIS Schlüsselindikatoren für Bildung – Referenztabelle."""
    lines = ["# UNESCO UIS – Schlüsselindikatoren Bildung", ""]
    for ind_id, ind_name in UNESCO_EDUCATION_INDICATORS.items():
        lines.append(f"- **`{ind_id}`** – {ind_name}")
    return "\n".join(lines)


@mcp.resource("education://datasets/oecd")
async def resource_oecd_datasets() -> str:
    """OECD Education at a Glance – Dataflow-Referenz."""
    lines = ["# OECD Education at a Glance – Dataflows", ""]
    for df_id, df_name in OECD_EDUCATION_DATAFLOWS.items():
        lines.append(f"- **`{df_id}`** – {df_name}")
    return "\n".join(lines)


# ─── Prompts ───────────────────────────────────────────────────────────────────


@mcp.prompt("bildungsvergleich_schweiz")
async def prompt_switzerland_comparison() -> str:
    """Prompt für einen Bildungsvergleich der Schweiz mit PISA-Top-Ländern."""
    return (
        "Erstelle einen detaillierten Bildungsvergleich der Schweiz (CHE) mit "
        "Finnland (FIN), Singapur (SGP), Japan (JPN) und dem OECD-Durchschnitt. "
        "Fokussiere auf: Alphabetisierungsraten, Bildungsausgaben als % des BIP, "
        "Abschlussquoten der Sekundarstufe und Schüler-Lehrer-Verhältnis. "
        "Nutze uis_compare_countries und education_benchmark_countries. "
        "Schlussfolgerungen für die Zürcher Bildungspolitik herausarbeiten."
    )


@mcp.prompt("sdg4_monitoring")
async def prompt_sdg4() -> str:
    """Prompt für SDG-4-Monitoring (Bildungsqualität für alle)."""
    return (
        "Erstelle einen SDG-4-Monitoring-Report für folgende Länder: "
        "CHE, DEU, AUT. Prüfe die wichtigsten SDG-4-Ziele: "
        "(1) Abschlussquoten Primar- und Sekundarstufe, "
        "(2) Alphabetisierungsraten Jugendliche, "
        "(3) Bildungsausgaben, "
        "(4) Geschlechterparität im Bildungszugang. "
        "Nutze uis_country_education_profile für jedes Land, dann vergleichen."
    )


# ─── Einstiegspunkt ────────────────────────────────────────────────────────────


def main() -> None:
    """Startet den MCP-Server."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
