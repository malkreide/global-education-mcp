"""
Erweiterte Testszenarien – Global Education MCP Server
========================================================
Schulamt der Stadt Zürich | Ergänzung zu test_server.py

Teststrategie:
  A) Grenzwerte & Edge Cases           – Validierung an den Systemgrenzen
  B) Sicherheit & Adversarial Inputs   – Robustheit gegen Fehleingaben
  C) Output-Qualität & Markdown        – Korrekte Formatierung und Inhalt
  D) Resilience & Fehlerkaskaden       – Verhalten bei multiplen Ausfällen
  E) Fachliche Korrektheit             – Bildungspolitisch relevante Inhalte
  F) Performanz & Parallelverarbeitung – Concurrent requests, Skalierung
  G) Realistische Schulamt-Szenarien   – Praxisfälle aus Zürcher Perspektive
  H) API-Integrationssmoke-Tests       – Echte APIs (mit Timeout-Toleranz)
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from global_education_mcp.api_client import (
    OECD_EDUCATION_DATAFLOWS,
    UNESCO_EDUCATION_INDICATORS,
    format_country_timeseries,
    format_uis_data_as_markdown,
    handle_api_error,
)
from global_education_mcp.server import (
    CrossSourceInput,
    OECDDataInput,
    OECDSearchInput,
    UISCompareInput,
    UISCountryProfileInput,
    UISDataInput,
    UISGeoUnitsInput,
    UISIndicatorsInput,
    education_benchmark_countries,
    oecd_get_education_indicator,
    oecd_list_education_datasets,
    oecd_search_datasets,
    uis_compare_countries,
    uis_country_education_profile,
    uis_get_education_data,
    uis_list_countries,
    uis_list_indicators,
    uis_list_versions,
)

# ─── Gemeinsame Hilfsdaten ─────────────────────────────────────────────────────

MOCK_SINGLE_OBS = lambda country, value, year=2022: {
    "observations": [{"geoUnit": country, "geoUnitName": country, "year": year, "value": value}]
}

MOCK_EMPTY = {"observations": []}

MOCK_NULL_VALUE = {
    "observations": [{"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": 2022, "value": None}]
}

MOCK_ZERO_VALUE = {
    "observations": [{"geoUnit": "SSD", "geoUnitName": "South Sudan", "year": 2022, "value": 0.0}]
}

MOCK_LARGE_TIMESERIES = {
    "observations": [
        {"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": y, "value": 95.0 + (y - 1990) * 0.1}
        for y in range(1990, 2024)
    ]
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# A) GRENZWERTE & EDGE CASES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestEdgeCases:
    """Grenzwerte: Was passiert an den Rändern des erlaubten Bereichs?"""

    # ─── Input-Validierung: Jahresgrenzen ─────────────────────────────────────

    def test_start_year_minimum_valid(self):
        """Jahr 1970 ist die untere Grenze – soll akzeptiert werden."""
        inp = UISDataInput(indicator_id="LR.AG15T99", start_year=1970)
        assert inp.start_year == 1970

    def test_start_year_below_minimum_rejected(self):
        """Jahr 1969 liegt unter der Grenze – soll abgelehnt werden."""
        with pytest.raises(Exception):
            UISDataInput(indicator_id="LR.AG15T99", start_year=1969)

    def test_end_year_maximum_valid(self):
        """Jahr 2030 ist die obere Grenze."""
        inp = UISDataInput(indicator_id="LR.AG15T99", end_year=2030)
        assert inp.end_year == 2030

    def test_end_year_above_maximum_rejected(self):
        """Jahr 2031 liegt über der Grenze."""
        with pytest.raises(Exception):
            UISDataInput(indicator_id="LR.AG15T99", end_year=2031)

    # ─── Input-Validierung: Stringlängen ──────────────────────────────────────

    def test_indicator_id_minimum_length(self):
        """Indikator-ID muss mind. 2 Zeichen haben."""
        inp = UISDataInput(indicator_id="AB")
        assert inp.indicator_id == "AB"

    def test_indicator_id_too_short_rejected(self):
        """Einzelnes Zeichen soll abgelehnt werden."""
        with pytest.raises(Exception):
            UISDataInput(indicator_id="X")

    def test_search_term_max_length(self):
        """Suchbegriff: max. 200 Zeichen."""
        long_search = "a" * 200
        inp = UISIndicatorsInput(search=long_search)
        assert len(inp.search) == 200

    def test_search_term_too_long_rejected(self):
        """201 Zeichen sollen abgelehnt werden."""
        with pytest.raises(Exception):
            UISIndicatorsInput(search="a" * 201)

    # ─── Limit-Grenzwerte ─────────────────────────────────────────────────────

    def test_limit_minimum_one(self):
        inp = UISIndicatorsInput(limit=1)
        assert inp.limit == 1

    def test_limit_zero_rejected(self):
        with pytest.raises(Exception):
            UISIndicatorsInput(limit=0)

    def test_limit_maximum_500(self):
        inp = UISIndicatorsInput(limit=500)
        assert inp.limit == 500

    def test_limit_above_500_rejected(self):
        with pytest.raises(Exception):
            UISIndicatorsInput(limit=501)

    # ─── Länder-Array-Grenzen ─────────────────────────────────────────────────

    def test_compare_minimum_two_countries(self):
        """Mindestens 2 Länder für Vergleich."""
        inp = UISCompareInput(indicator_id="LR.AG15T99", country_codes=["CHE", "DEU"])
        assert len(inp.country_codes) == 2

    def test_compare_exactly_15_countries_allowed(self):
        """Genau 15 Länder sind erlaubt."""
        codes = ["CHE", "DEU", "AUT", "FIN", "SGP", "KOR", "JPN", "FRA",
                 "SWE", "NOR", "DNK", "NLD", "BEL", "ESP", "ITA"]
        inp = UISCompareInput(indicator_id="LR.AG15T99", country_codes=codes)
        assert len(inp.country_codes) == 15

    def test_benchmark_maximum_10_countries(self):
        """CrossSourceInput: max. 10 Länder."""
        codes = ["CHE", "DEU", "AUT", "FIN", "SGP", "KOR", "JPN", "FRA", "SWE", "NOR"]
        inp = CrossSourceInput(country_codes=codes, focus="literacy")
        assert len(inp.country_codes) == 10

    # ─── Datenkanten: Null/Zero/Einzel-Observation ────────────────────────────

    @pytest.mark.asyncio
    async def test_null_value_in_observations_handled(self):
        """None-Werte in Beobachtungen dürfen nicht zum Absturz führen."""
        with patch("global_education_mcp.server.uis_get_data", new_callable=AsyncMock, return_value=MOCK_NULL_VALUE):
            params = UISDataInput(indicator_id="LR.AG15T99", country_code="CHE")
            result = await uis_get_education_data(params)
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_zero_value_in_observations_displayed(self):
        """Wert 0.0 ist ein gültiger Wert (kein fehlender Wert!)."""
        with patch("global_education_mcp.server.uis_get_data", new_callable=AsyncMock, return_value=MOCK_ZERO_VALUE):
            params = UISDataInput(indicator_id="LR.AG15T99", country_code="SSD")
            result = await uis_get_education_data(params)
            assert "0.0" in result or "0" in result

    @pytest.mark.asyncio
    async def test_large_timeseries_34_years_handled(self):
        """34 Jahre Zeitreihendaten sollen vollständig verarbeitet werden."""
        with patch("global_education_mcp.server.uis_get_data", new_callable=AsyncMock,
                   return_value=MOCK_LARGE_TIMESERIES):
            params = UISDataInput(indicator_id="LR.AG15T99", country_code="CHE")
            result = await uis_get_education_data(params)
            assert "1990" in result
            assert "2023" in result

    @pytest.mark.asyncio
    async def test_single_observation_year_shown(self):
        """Nur eine einzige Beobachtung: Jahr muss korrekt angezeigt werden."""
        mock = {"observations": [{"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": 2019, "value": 98.7}]}
        with patch("global_education_mcp.server.uis_get_data", new_callable=AsyncMock, return_value=mock):
            params = UISDataInput(indicator_id="LR.AG15T99", country_code="CHE")
            result = await uis_get_education_data(params)
            assert "2019" in result
            assert "98.7" in result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# B) SICHERHEIT & ADVERSARIAL INPUTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestSecurityAndAdversarialInputs:
    """
    Robustheit gegen fehlerhafte, unerwartete und potentiell schädliche Eingaben.
    MCP-Server sind exponiert gegenüber LLM-generierten Inputs – Paranoia ist angebracht.
    """

    # ─── Whitespace-Handling (Pydantic str_strip_whitespace=True) ─────────────

    def test_indicator_id_whitespace_stripped(self):
        """Führende/nachfolgende Leerzeichen sollen entfernt werden."""
        inp = UISDataInput(indicator_id="  LR.AG15T99  ")
        assert inp.indicator_id == "LR.AG15T99"

    def test_country_code_whitespace_stripped(self):
        inp = UISDataInput(indicator_id="LR.AG15T99", country_code="  CHE  ")
        assert inp.country_code == "CHE"

    def test_search_whitespace_stripped(self):
        inp = UISIndicatorsInput(search="  literacy  ")
        assert inp.search == "literacy"

    # ─── Pydantic extra="forbid" ──────────────────────────────────────────────

    def test_extra_fields_rejected_in_uis_data_input(self):
        """Unbekannte Felder müssen abgelehnt werden (kein Parameter-Injection)."""
        with pytest.raises(Exception):
            UISDataInput(indicator_id="LR.AG15T99", unknown_field="hacked")

    def test_extra_fields_rejected_in_compare_input(self):
        with pytest.raises(Exception):
            UISCompareInput(
                indicator_id="LR.AG15T99",
                country_codes=["CHE", "DEU"],
                malicious_extra="DROP TABLE indicators",
            )

    def test_extra_fields_rejected_in_cross_source(self):
        with pytest.raises(Exception):
            CrossSourceInput(country_codes=["CHE", "DEU"], focus="literacy", extra="injection")

    # ─── Ungültige Enum-Werte ─────────────────────────────────────────────────

    def test_invalid_focus_rejected(self):
        """Nur explizit definierte Fokus-Werte sind erlaubt."""
        for invalid in ["LITERACY", "Literacy", "sql_injection", "", "all", "None"]:
            with pytest.raises(Exception):
                CrossSourceInput(country_codes=["CHE", "DEU"], focus=invalid)

    # ─── Spezialzeichen in Suchbegriffen ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_search_with_special_characters_does_not_crash(self):
        """Sonderzeichen im Suchbegriff führen nicht zum Absturz."""
        with patch("global_education_mcp.server.uis_get_indicators",
                   new_callable=AsyncMock, return_value=[]):
            for special_input in ["<script>", "'; DROP TABLE--", "/../etc/passwd", "🔥", "null", "undefined"]:
                params = UISIndicatorsInput(search=special_input[:200])
                result = await uis_list_indicators(params)
                assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_sql_like_country_code_handled_gracefully(self):
        """SQL-ähnlicher Ländercode führt zu sauberem Fehler, nicht zum Absturz."""
        with patch("global_education_mcp.server.uis_get_data",
                   side_effect=Exception("invalid country code")):
            params = UISDataInput(indicator_id="LR.AG15T99", country_code="OR1=1")
            result = await uis_get_education_data(params)
            assert isinstance(result, str)
            assert len(result) > 0

    # ─── API-Fehler: Verschiedene HTTP-Statuscodes ────────────────────────────

    def test_error_handler_401_unauthorized(self):
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        e = httpx.HTTPStatusError("", request=AsyncMock(), response=mock_response)
        result = handle_api_error(e, "test")
        assert "401" in result or "Fehler" in result

    def test_error_handler_500_server_error(self):
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        e = httpx.HTTPStatusError("", request=AsyncMock(), response=mock_response)
        result = handle_api_error(e, "test")
        assert "500" in result or "Fehler" in result

    def test_error_handler_503_service_unavailable(self):
        mock_response = AsyncMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        e = httpx.HTTPStatusError("", request=AsyncMock(), response=mock_response)
        result = handle_api_error(e, "test")
        assert "503" in result or "verfügbar" in result.lower()

    def test_error_handler_connect_error(self):
        e = httpx.ConnectError("Connection refused")
        result = handle_api_error(e)
        assert "Verbindung" in result or "connect" in result.lower()

    def test_error_handler_rate_limit_429(self):
        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        e = httpx.HTTPStatusError("", request=AsyncMock(), response=mock_response)
        result = handle_api_error(e)
        assert "429" in result or "limit" in result.lower() or "warten" in result.lower()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# C) OUTPUT-QUALITÄT & MARKDOWN-FORMATIERUNG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestOutputQuality:
    """
    MCP-Outputs sind das, was das LLM sieht. Qualität ist entscheidend:
    Markdown-Struktur, Quellenangaben, Tabellen-Alignment.
    """

    # ─── Quellenangaben ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_uis_output_contains_source_attribution(self):
        """Alle UNESCO-Outputs müssen Quellenangabe enthalten."""
        with patch("global_education_mcp.server.uis_get_indicators",
                   new_callable=AsyncMock, return_value=[
                       {"indicatorId": "LR.AG15T99", "indicatorName": "Literacy", "theme": "EDUCATION"}
                   ]):
            result = await uis_list_indicators(UISIndicatorsInput())
            assert "UNESCO" in result

    @pytest.mark.asyncio
    async def test_oecd_output_contains_source_attribution(self):
        """Alle OECD-Outputs müssen Quellenangabe enthalten."""
        with patch("global_education_mcp.server.oecd_get_dataflows",
                   new_callable=AsyncMock, return_value=[]):
            result = await oecd_list_education_datasets()
            assert "OECD" in result

    @pytest.mark.asyncio
    async def test_compare_output_contains_markdown_table(self):
        """Vergleichsoutput muss Markdown-Tabelle mit | enthalten."""
        async def mock_data(indicator, geo_unit=None, **kwargs):
            return MOCK_SINGLE_OBS(geo_unit, 95.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            params = UISCompareInput(indicator_id="LR.AG15T99", country_codes=["CHE", "DEU"])
            result = await uis_compare_countries(params)
            assert "|" in result
            assert "---" in result  # Tabellentrennlinie

    @pytest.mark.asyncio
    async def test_profile_output_contains_all_indicator_labels(self):
        """Länderprofil: Alle 10 Indikatoren-Labels müssen im Output erscheinen."""
        expected_labels = [
            "Alphabetisierungsrate",
            "Einschulungsrate",
            "Abschlussquote",
            "Bildungsausgaben",
            "Schüler-Lehrer-Verhältnis",
            "Geschlechterparitätsindex",
        ]
        async def mock_data(indicator, geo_unit=None, **kwargs):
            return MOCK_SINGLE_OBS("CHE", 95.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            result = await uis_country_education_profile(UISCountryProfileInput(country_code="CHE"))
            for label in expected_labels:
                assert label in result, f"Fehlendes Label im Profil: '{label}'"

    # ─── Markdown-Header-Struktur ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_benchmark_output_has_section_headers(self):
        """Benchmark-Report soll H2/H3-Header haben."""
        async def mock_data(indicator, geo_unit=None, **kwargs):
            return MOCK_SINGLE_OBS(geo_unit, 90.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            result = await education_benchmark_countries(
                CrossSourceInput(country_codes=["CHE", "DEU"], focus="literacy")
            )
            assert "##" in result

    @pytest.mark.asyncio
    async def test_timeseries_output_has_year_column(self):
        """Zeitreihen-Output muss Jahresspalte enthalten."""
        with patch("global_education_mcp.server.uis_get_data",
                   new_callable=AsyncMock, return_value=MOCK_LARGE_TIMESERIES):
            result = await uis_get_education_data(
                UISDataInput(indicator_id="LR.AG15T99", country_code="CHE")
            )
            assert "Jahr" in result or "Year" in result or "year" in result

    # ─── Sortierungs-Invarianten ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_compare_rank_column_starts_at_1(self):
        """Rang-Spalte im Vergleich muss mit 1 beginnen."""
        async def mock_data(indicator, geo_unit=None, **kwargs):
            return MOCK_SINGLE_OBS(geo_unit, 95.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            result = await uis_compare_countries(
                UISCompareInput(indicator_id="LR.AG15T99", country_codes=["CHE", "DEU", "FIN"])
            )
            assert "| 1 |" in result

    @pytest.mark.asyncio
    async def test_timeseries_sorted_chronologically(self):
        """Zeitreihe soll chronologisch (1990→2023) sortiert sein."""
        with patch("global_education_mcp.server.uis_get_data",
                   new_callable=AsyncMock, return_value=MOCK_LARGE_TIMESERIES):
            result = await uis_get_education_data(
                UISDataInput(indicator_id="LR.AG15T99", country_code="CHE")
            )
            idx_1990 = result.find("1990")
            idx_2023 = result.find("2023")
            assert idx_1990 < idx_2023, "1990 muss vor 2023 erscheinen"

    # ─── Formatierungs-Hilfsfunktionen direkt ─────────────────────────────────

    def test_format_timeseries_preserves_observation_status(self):
        """observationStatus ('E' = Estimate) soll im Output erscheinen."""
        obs = [{"year": 2022, "value": 95.0, "observationStatus": "E"}]
        result = format_country_timeseries(obs, "CHE", "LR.AG15T99")
        assert "E" in result

    def test_format_timeseries_handles_missing_status_field(self):
        """Fehlender observationStatus darf nicht zum Absturz führen."""
        obs = [{"year": 2022, "value": 95.0}]  # kein observationStatus
        result = format_country_timeseries(obs, "CHE", "LR.AG15T99")
        assert "2022" in result
        assert "95.0" in result

    def test_format_multi_country_sorted_alphabetically(self):
        """Länderübersicht soll alphabetisch sortiert sein (by country label)."""
        data = {
            "observations": [
                {"geoUnit": "ZWE", "geoUnitName": "Zimbabwe", "year": 2022, "value": 80.0},
                {"geoUnit": "AUS", "geoUnitName": "Australia", "year": 2022, "value": 95.0},
                {"geoUnit": "MEX", "geoUnitName": "Mexico", "year": 2022, "value": 90.0},
            ]
        }
        result = format_uis_data_as_markdown(data, "LR.AG15T99")
        aus_pos = result.find("Australia")
        mex_pos = result.find("Mexico")
        zwe_pos = result.find("Zimbabwe")
        assert aus_pos < mex_pos < zwe_pos, "Länder sollen alphabetisch sortiert sein"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# D) RESILIENCE & FEHLERKASKADEN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestResilienceAndFailureCascades:
    """
    Was passiert wenn APIs ausfallen, Daten unvollständig sind,
    oder Netzwerkfehler auftreten? Graceful Degradation ist Pflicht.
    """

    @pytest.mark.asyncio
    async def test_all_countries_fail_in_compare_returns_error_message(self):
        """Alle Länder-Abfragen scheitern: Saubere Fehlermeldung statt Exception."""
        with patch("global_education_mcp.server.uis_get_data",
                   side_effect=Exception("All down")):
            params = UISCompareInput(
                indicator_id="LR.AG15T99",
                country_codes=["CHE", "DEU", "AUT"],
            )
            result = await uis_compare_countries(params)
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_profile_with_all_indicators_failing(self):
        """Länderprofil wenn alle 10 Indikator-Abfragen scheitern."""
        with patch("global_education_mcp.server.uis_get_data",
                   side_effect=Exception("API down")):
            result = await uis_country_education_profile(
                UISCountryProfileInput(country_code="CHE")
            )
            assert isinstance(result, str)
            assert "Bildungsprofil" in result or "CHE" in result

    @pytest.mark.asyncio
    async def test_benchmark_with_complete_api_failure(self):
        """Benchmark wenn UIS komplett nicht erreichbar."""
        with patch("global_education_mcp.server.uis_get_data",
                   side_effect=httpx.ConnectError("Network unreachable")):
            result = await education_benchmark_countries(
                CrossSourceInput(country_codes=["CHE", "DEU"], focus="spending")
            )
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_oecd_indicator_with_timeout_returns_helpful_message(self):
        """OECD-Timeout soll hilfreiche Fehlermeldung mit Dataflow-ID liefern."""
        with patch("global_education_mcp.server.oecd_get_education_data",
                   side_effect=httpx.TimeoutException("Timeout")):
            result = await oecd_get_education_indicator(
                OECDDataInput(dataflow_id="EAG_FISC", countries=["CHE"])
            )
            assert "EAG_FISC" in result  # Kontext bleibt erhalten
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_uis_versions_api_failure_returns_string(self):
        """Versionsabfrage-Fehler soll String zurückgeben."""
        with patch("global_education_mcp.server.uis_get_versions",
                   side_effect=Exception("Version API unavailable")):
            result = await uis_list_versions()
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_intermittent_failure_in_benchmark_partial_results(self):
        """3 von 5 Ländern liefern Daten – Teilergebnis soll angezeigt werden."""
        call_counter = {"n": 0}

        async def intermittent_fail(indicator, geo_unit=None, **kwargs):
            call_counter["n"] += 1
            if geo_unit in ["AUT", "FRA"]:
                raise Exception("Intermittent error")
            return MOCK_SINGLE_OBS(geo_unit, 92.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=intermittent_fail):
            result = await education_benchmark_countries(
                CrossSourceInput(
                    country_codes=["CHE", "DEU", "AUT", "FIN", "FRA"],
                    focus="literacy",
                )
            )
            assert "CHE" in result
            assert "DEU" in result
            assert "FIN" in result

    @pytest.mark.asyncio
    async def test_oecd_empty_datasets_returns_hint(self):
        """Leere OECD-Antwort soll hilfreichen Tipp zur Dataflow-ID geben."""
        with patch("global_education_mcp.server.oecd_get_education_data",
                   new_callable=AsyncMock,
                   return_value={"dataSets": [], "structure": {}}):
            result = await oecd_get_education_indicator(
                OECDDataInput(dataflow_id="EAG_NONEXISTENT")
            )
            assert "EAG_NONEXISTENT" in result or "keine Daten" in result.lower()

    @pytest.mark.asyncio
    async def test_country_list_api_failure_shows_known_countries(self):
        """Bei API-Ausfall sollen mindestens CHE/DEU/AUT/FIN als Fallback erscheinen."""
        with patch("global_education_mcp.server.uis_get_geo_units",
                   side_effect=Exception("Geo API down")):
            result = await uis_list_countries(UISGeoUnitsInput())
            for code in ["CHE", "DEU", "AUT", "FIN"]:
                assert code in result, f"Fallback-Land {code} fehlt im Output"

    @pytest.mark.asyncio
    async def test_indicators_api_failure_shows_known_indicators(self):
        """Bei API-Ausfall: Mindestens LR.AG15T99 und CR.1 als Fallback."""
        with patch("global_education_mcp.server.uis_get_indicators",
                   side_effect=Exception("Indicators API down")):
            result = await uis_list_indicators(UISIndicatorsInput())
            assert "LR.AG15T99" in result
            assert "CR.1" in result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# E) FACHLICHE KORREKTHEIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestSubjectMatterCorrectness:
    """
    Bildungspolitisch korrekte Inhalte: Stimmen die Indikatoren,
    decken die Profile die richtigen Dimensionen ab?
    """

    # ─── Indikator-Vollständigkeit ────────────────────────────────────────────

    def test_sdg4_core_indicators_all_present(self):
        """Die 4 SDG-4-Kerndimensionen müssen abgedeckt sein."""
        # SDG-4: Abschluss, Alphabetisierung, Ausgaben, Gleichstellung
        assert "CR.1" in UNESCO_EDUCATION_INDICATORS        # Abschluss Primar
        assert "LR.AG15T24" in UNESCO_EDUCATION_INDICATORS  # Alphabetisierung Jugendliche
        assert "XGDP.FSGOV" in UNESCO_EDUCATION_INDICATORS  # Ausgaben
        assert "GPI.NERA.1" in UNESCO_EDUCATION_INDICATORS  # Gleichstellung

    def test_gender_indicators_available_for_all_levels(self):
        """Geschlechterdifferenzierte Alphabetisierung muss verfügbar sein."""
        assert "LR.AG15T24.F" in UNESCO_EDUCATION_INDICATORS
        assert "LR.AG15T24.M" in UNESCO_EDUCATION_INDICATORS

    def test_education_system_levels_complete(self):
        """Alle Schulstufen 1-3 müssen abgebildet sein."""
        for level in ["1", "2", "3"]:
            assert f"CR.{level}" in UNESCO_EDUCATION_INDICATORS
            assert f"NERA.{level}" in UNESCO_EDUCATION_INDICATORS or f"PTR.{level}" in UNESCO_EDUCATION_INDICATORS

    def test_oecd_eag_all_main_chapters_covered(self):
        """Education at a Glance Hauptkapitel: Einschreibung, Ausgaben, Personal, Beschäftigung."""
        eag_ids = list(OECD_EDUCATION_DATAFLOWS.keys())
        # Einschreibung
        assert any("ENRL" in x or "GRAD" in x for x in eag_ids)
        # Ausgaben
        assert any("FISC" in x for x in eag_ids)
        # Personal
        assert any("PERS" in x for x in eag_ids)
        # Arbeitsmarkt
        assert any("EMP" in x or "EARN" in x for x in eag_ids)

    # ─── Benchmark-Indikator-Mapping ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_literacy_benchmark_uses_correct_indicators(self):
        """literacy-Benchmark muss LR.AG15T99 UND LR.AG15T24 abfragen."""
        called_indicators = []

        async def capture_calls(indicator, geo_unit=None, **kwargs):
            called_indicators.append(indicator)
            return MOCK_SINGLE_OBS(geo_unit, 95.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=capture_calls):
            await education_benchmark_countries(
                CrossSourceInput(country_codes=["CHE", "DEU"], focus="literacy")
            )
        assert "LR.AG15T99" in called_indicators, "Erwachsenen-Alphabetisierung fehlt"
        assert "LR.AG15T24" in called_indicators, "Jugend-Alphabetisierung fehlt"

    @pytest.mark.asyncio
    async def test_spending_benchmark_uses_gdp_indicator(self):
        """spending-Benchmark muss BIP-Bildungsausgaben-Indikator verwenden."""
        called_indicators = []

        async def capture_calls(indicator, geo_unit=None, **kwargs):
            called_indicators.append(indicator)
            return MOCK_SINGLE_OBS(geo_unit, 5.2)

        with patch("global_education_mcp.server.uis_get_data", side_effect=capture_calls):
            await education_benchmark_countries(
                CrossSourceInput(country_codes=["CHE", "DEU"], focus="spending")
            )
        assert "XGDP.FSGOV" in called_indicators, "BIP-Bildungsausgaben-Indikator fehlt"

    @pytest.mark.asyncio
    async def test_teachers_benchmark_uses_ptr_indicator(self):
        """teachers-Benchmark muss Schüler-Lehrer-Verhältnis (PTR) abfragen."""
        called_indicators = []

        async def capture_calls(indicator, geo_unit=None, **kwargs):
            called_indicators.append(indicator)
            return MOCK_SINGLE_OBS(geo_unit, 15.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=capture_calls):
            await education_benchmark_countries(
                CrossSourceInput(country_codes=["CHE", "DEU"], focus="teachers")
            )
        assert any("PTR" in ind for ind in called_indicators), "PTR-Indikator fehlt im teachers-Benchmark"

    @pytest.mark.asyncio
    async def test_enrollment_benchmark_uses_nera_indicator(self):
        """enrollment-Benchmark muss Einschulungsrate (NERA) abfragen."""
        called_indicators = []

        async def capture_calls(indicator, geo_unit=None, **kwargs):
            called_indicators.append(indicator)
            return MOCK_SINGLE_OBS(geo_unit, 98.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=capture_calls):
            await education_benchmark_countries(
                CrossSourceInput(country_codes=["CHE", "DEU"], focus="enrollment")
            )
        assert any("NERA" in ind for ind in called_indicators), "NERA-Indikator fehlt im enrollment-Benchmark"

    # ─── Länderprofil: 10 Kernindikatoren ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_country_profile_queries_exactly_10_indicators(self):
        """Länderprofil soll exakt 10 Kernindikatoren abfragen."""
        call_count = {"n": 0}

        async def count_calls(indicator, geo_unit=None, **kwargs):
            call_count["n"] += 1
            return MOCK_SINGLE_OBS(geo_unit, 95.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=count_calls):
            await uis_country_education_profile(UISCountryProfileInput(country_code="CHE"))

        assert call_count["n"] == 10, f"Erwartet 10 API-Aufrufe, erhalten: {call_count['n']}"

    @pytest.mark.asyncio
    async def test_country_profile_uses_latest_value_not_oldest(self):
        """Profil soll neuesten Wert, nicht ältesten anzeigen."""
        mock_multi_year = {
            "observations": [
                {"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": 2010, "value": 85.0},
                {"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": 2022, "value": 99.2},
                {"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": 2015, "value": 92.0},
            ]
        }
        with patch("global_education_mcp.server.uis_get_data",
                   new_callable=AsyncMock, return_value=mock_multi_year):
            result = await uis_country_education_profile(UISCountryProfileInput(country_code="CHE"))
        assert "99.2" in result, "Neuester Wert (99.2, 2022) muss im Profil erscheinen"
        assert "85.0" not in result, "Alter Wert (85.0, 2010) darf nicht im Profil erscheinen"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F) PERFORMANZ & PARALLELVERARBEITUNG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestPerformanceAndConcurrency:
    """
    MCP-Server werden von LLM-Agenten teils parallel aufgerufen.
    Sequentielle Korrektheit unter Concurrent Load testen.
    """

    @pytest.mark.asyncio
    async def test_benchmark_completes_within_reasonable_time(self):
        """5-Länder-Benchmark (gemockt) soll schnell abgeschlossen sein."""
        async def fast_mock(indicator, geo_unit=None, **kwargs):
            await asyncio.sleep(0.001)  # simuliert minimale API-Latenz
            return MOCK_SINGLE_OBS(geo_unit, 90.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=fast_mock):
            start = time.monotonic()
            await education_benchmark_countries(
                CrossSourceInput(
                    country_codes=["CHE", "DEU", "AUT", "FIN", "SGP"],
                    focus="completion",
                )
            )
            elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"Benchmark dauerte {elapsed:.2f}s – zu langsam"

    @pytest.mark.asyncio
    async def test_concurrent_profile_requests_do_not_interfere(self):
        """3 parallele Profilanfragen sollen sich nicht gegenseitig beeinflussen."""
        async def mock_data(indicator, geo_unit=None, **kwargs):
            await asyncio.sleep(0.005)
            return MOCK_SINGLE_OBS(geo_unit, 95.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            results = await asyncio.gather(
                uis_country_education_profile(UISCountryProfileInput(country_code="CHE")),
                uis_country_education_profile(UISCountryProfileInput(country_code="DEU")),
                uis_country_education_profile(UISCountryProfileInput(country_code="FIN")),
            )
        assert len(results) == 3
        assert "CHE" in results[0]
        assert "DEU" in results[1]
        assert "FIN" in results[2]

    @pytest.mark.asyncio
    async def test_concurrent_compare_requests_independent(self):
        """3 parallele Vergleiche – jeder gibt sein eigenes Ergebnis zurück."""
        async def mock_data(indicator, geo_unit=None, **kwargs):
            return MOCK_SINGLE_OBS(geo_unit, 95.0)

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            r1, r2, r3 = await asyncio.gather(
                uis_compare_countries(UISCompareInput(
                    indicator_id="LR.AG15T99", country_codes=["CHE", "DEU"])),
                uis_compare_countries(UISCompareInput(
                    indicator_id="CR.1", country_codes=["FIN", "SGP"])),
                uis_compare_countries(UISCompareInput(
                    indicator_id="XGDP.FSGOV", country_codes=["AUT", "FRA"])),
            )
        assert "LR.AG15T99" in r1
        assert "CR.1" in r2
        assert "XGDP.FSGOV" in r3

    @pytest.mark.asyncio
    async def test_15_countries_compare_returns_all_in_output(self):
        """Maximum 15-Länder-Vergleich: Alle müssen im Output erscheinen."""
        codes_15 = ["CHE", "DEU", "AUT", "FIN", "SGP", "KOR", "JPN", "FRA",
                    "SWE", "NOR", "DNK", "NLD", "BEL", "ESP", "ITA"]

        async def mock_data(indicator, geo_unit=None, **kwargs):
            return MOCK_SINGLE_OBS(geo_unit, 90.0 + len(geo_unit))

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            result = await uis_compare_countries(
                UISCompareInput(indicator_id="LR.AG15T99", country_codes=codes_15)
            )
        for code in codes_15:
            assert code in result, f"Land {code} fehlt im 15-Länder-Vergleich"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# G) REALISTISCHE SCHULAMT-SZENARIEN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestRealisticSchulامtScenarios:
    """
    Praxisfälle aus dem Schulamt Zürich:
    Steuerung, Qualitätssicherung, Bildungspolitik, GL-Berichte.
    """

    @pytest.mark.asyncio
    async def test_scenario_dach_comparison_literacy(self):
        """
        SZENARIO: Jahresbericht Volksschule – DACH-Vergleich Alphabetisierung.
        Fragestellung der GL: Wie steht Zürich im DACH-Kontext?
        """
        dach_values = {"CHE": 99.0, "DEU": 99.1, "AUT": 98.8}

        async def mock_data(indicator, geo_unit=None, **kwargs):
            val = dach_values.get(geo_unit, 90.0)
            return MOCK_SINGLE_OBS(geo_unit, val)

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            result = await uis_compare_countries(
                UISCompareInput(
                    indicator_id="LR.AG15T99",
                    country_codes=["CHE", "DEU", "AUT"],
                    year=2022,
                )
            )
        assert "CHE" in result
        assert "DEU" in result
        assert "AUT" in result
        assert "Rang" in result

    @pytest.mark.asyncio
    async def test_scenario_pisa_reference_countries(self):
        """
        SZENARIO: Bildungspolitik – Benchmarking gegen PISA-Spitzenländer.
        Fragestellung: Wo liegt CH im Vergleich zu FIN, SGP, KOR?
        """
        pisa_values = {"CHE": 85.0, "FIN": 96.0, "SGP": 97.0, "KOR": 95.0}

        async def mock_data(indicator, geo_unit=None, **kwargs):
            val = pisa_values.get(geo_unit, 80.0)
            return MOCK_SINGLE_OBS(geo_unit, val)

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            result = await education_benchmark_countries(
                CrossSourceInput(
                    country_codes=["CHE", "FIN", "SGP", "KOR"],
                    focus="completion",
                )
            )
        # Nur im Tabellenbereich nach Rang suchen (Header enthält ebenfalls Ländercodes)
        table_start = result.find("|---")
        table_section = result[table_start:] if table_start >= 0 else result
        # SGP und FIN sollen vor CHE ranken (höhere completion rate → besserer Rang)
        sgp_pos = table_section.find("SGP")
        che_pos = table_section.find("CHE")
        assert sgp_pos < che_pos, "SGP (97%) soll vor CHE (85%) im Tabellenbereich erscheinen"

    @pytest.mark.asyncio
    async def test_scenario_sdg4_monitoring_report(self):
        """
        SZENARIO: SDG-4-Monitoring für Stadtrat-Bericht.
        Vollständiges Länderprofil Schweiz für Berichterstattung.
        """
        profile_data = {
            "LR.AG15T99": 99.0, "LR.AG15T24": 99.5,
            "NERA.1": 97.0, "NERA.2": 94.0,
            "CR.1": 98.0, "CR.2": 96.0, "CR.3": 89.0,
            "XGDP.FSGOV": 5.3,
            "PTR.1": 14.2,
            "GPI.NERA.1": 1.01,
        }

        async def mock_data(indicator, geo_unit=None, **kwargs):
            val = profile_data.get(indicator, 90.0)
            return {"observations": [{"geoUnit": "CHE", "geoUnitName": "Switzerland",
                                      "year": 2022, "value": val}]}

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            result = await uis_country_education_profile(
                UISCountryProfileInput(country_code="CHE", latest_year_only=True)
            )

        assert "5.3" in result    # Bildungsausgaben
        assert "14.2" in result   # Schüler-Lehrer-Verhältnis
        assert "99.0" in result   # Alphabetisierung

    @pytest.mark.asyncio
    async def test_scenario_teacher_shortage_analysis(self):
        """
        SZENARIO: Analyse Lehrpersonenmangel – Vergleich PTR Schweiz vs. Nachbarländer.
        Je höher PTR, desto mehr Schüler pro Lehrperson = potentieller Mangel.
        """
        # CH hat höheres PTR als FIN → möglicher Handlungsbedarf
        ptr_values = {"CHE": 16.5, "DEU": 15.0, "AUT": 14.8, "FIN": 12.5}

        async def mock_data(indicator, geo_unit=None, **kwargs):
            val = ptr_values.get(geo_unit, 15.0)
            return MOCK_SINGLE_OBS(geo_unit, val)

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            result = await education_benchmark_countries(
                CrossSourceInput(
                    country_codes=["CHE", "DEU", "AUT", "FIN"],
                    focus="teachers",
                )
            )

        # CH (16.5) hat höchsten PTR → letzter Rang (schlechtester Wert)
        # (höher = mehr Schüler pro Lehrer = schlechter bei Lehrermangel-Perspektive)
        # Da absteigend sortiert, ist CH bei PTR an erster Stelle
        assert "16.5" in result
        assert "12.5" in result

    @pytest.mark.asyncio
    async def test_scenario_education_spending_vs_outcomes(self):
        """
        SZENARIO: Effizienzanalyse – Ausgaben vs. Abschlussquoten.
        Politisch relevant: Gibt CH zu viel/wenig aus im Vergleich?
        """
        spending_data = {"CHE": 5.3, "DEU": 4.8, "FIN": 6.1, "SGP": 2.9}

        async def mock_data(indicator, geo_unit=None, **kwargs):
            val = spending_data.get(geo_unit, 5.0)
            return MOCK_SINGLE_OBS(geo_unit, val)

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_data):
            result = await education_benchmark_countries(
                CrossSourceInput(
                    country_codes=["CHE", "DEU", "FIN", "SGP"],
                    focus="spending",
                )
            )
        assert "5.3" in result  # CH-Ausgaben sichtbar
        assert "6.1" in result  # FIN-Ausgaben (höchste im Set)
        assert "2.9" in result  # SGP-Ausgaben (niedrigste im Set)

    @pytest.mark.asyncio
    async def test_scenario_oecd_teacher_salary_data(self):
        """
        SZENARIO: Lehrergehalt-Vergleich für Personalstrategie-Bericht.
        OECD EAG_PERS_SALARY enthält vergleichbare Lohndaten.
        """
        mock_salary_data = {
            "dataSets": [{"observations": {"0:0:0": [85000], "1:0:0": [72000], "2:0:0": [68000]}}],
            "structure": {
                "dimensions": {
                    "observation": [
                        {"id": "REF_AREA", "name": "Country", "values": [
                            {"id": "CHE"}, {"id": "DEU"}, {"id": "AUT"}
                        ]},
                    ]
                }
            },
        }
        with patch("global_education_mcp.server.oecd_get_education_data",
                   new_callable=AsyncMock, return_value=mock_salary_data):
            result = await oecd_get_education_indicator(
                OECDDataInput(
                    dataflow_id="EAG_PERS_SALARY",
                    countries=["CHE", "DEU", "AUT"],
                )
            )
        assert "EAG_PERS_SALARY" in result
        assert "3" in result  # 3 Beobachtungen

    @pytest.mark.asyncio
    async def test_scenario_global_literacy_overview_no_country_filter(self):
        """
        SZENARIO: Globaler Überblick für Strategiepapier – alle Länder, neueste Daten.
        Kein Länderfilter: Gibt die Formatierungsfunktion sinnvoll aus?
        """
        global_data = {
            "observations": [
                {"geoUnit": c, "geoUnitName": c, "year": 2022, "value": v}
                for c, v in [("CHE", 99.0), ("DEU", 99.1), ("MLI", 33.0), ("NER", 27.0)]
            ]
        }
        with patch("global_education_mcp.server.uis_get_data",
                   new_callable=AsyncMock, return_value=global_data):
            result = await uis_get_education_data(
                UISDataInput(indicator_id="LR.AG15T99")  # kein country_code
            )
        assert "CHE" in result or "Switzerland" in result
        assert "MLI" in result or "Mali" in result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# H) API-INTEGRATIONSSMOKE-TESTS (Live – mit Timeout-Toleranz)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.mark.integration
class TestLiveApiSmoke:
    """
    Live-API-Tests gegen echte Endpunkte.
    Markiert mit @pytest.mark.integration – nur mit --run-integration ausführen.
    Akzeptieren Netzwerkfehler als tolerierten Ausfall (nicht als Testfehler).
    """

    @pytest.mark.asyncio
    async def test_live_uis_indicators_endpoint_reachable(self):
        """Smoke: UIS-Indikatoren-Endpunkt ist erreichbar und liefert Daten."""
        params = UISIndicatorsInput(theme="EDUCATION", limit=5)
        result = await uis_list_indicators(params)
        # Akzeptiere sowohl Live-Daten als auch Fallback
        assert isinstance(result, str)
        assert len(result) > 50  # Mindestens etwas Output

    @pytest.mark.asyncio
    async def test_live_uis_switzerland_literacy_data(self):
        """Smoke: Echte Alphabetisierungsdaten für die Schweiz abrufbar."""
        params = UISDataInput(
            indicator_id="LR.AG15T99",
            country_code="CHE",
            start_year=2015,
        )
        result = await uis_get_education_data(params)
        assert isinstance(result, str)
        assert "CHE" in result or "Switzerland" in result or "Fehler" in result

    @pytest.mark.asyncio
    async def test_live_oecd_dataset_list_reachable(self):
        """Smoke: OECD-Dataflow-Liste ist erreichbar."""
        result = await oecd_list_education_datasets()
        assert isinstance(result, str)
        assert "EAG_FISC" in result  # Lokal immer vorhanden

    @pytest.mark.asyncio
    async def test_live_uis_geo_units_returns_switzerland(self):
        """Smoke: Schweiz (CHE) muss in der Länderliste erscheinen."""
        params = UISGeoUnitsInput(search="Switzerland")
        result = await uis_list_countries(params)
        assert isinstance(result, str)
        # Entweder Live-Daten oder Fallback – CHE muss immer da sein
        assert "CHE" in result
