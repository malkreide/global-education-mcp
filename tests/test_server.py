"""
Tests für den Global Education MCP Server.
Drei Komplexitätsstufen: einfach, mittel, komplex.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from global_education_mcp.api_client import (
    OECD_EDUCATION_DATAFLOWS,
    UNESCO_EDUCATION_INDICATORS,
    format_country_timeseries,
    format_uis_data_as_markdown,
    handle_api_error,
)
from global_education_mcp.server import (
    OECDDataInput,
    OECDSearchInput,
    UISCompareInput,
    UISCountryProfileInput,
    UISDataInput,
    UISGeoUnitsInput,
    UISIndicatorsInput,
    CrossSourceInput,
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

# ─── Hilfsdaten für Tests ─────────────────────────────────────────────────────

MOCK_UIS_INDICATORS = [
    {"indicatorId": "LR.AG15T99", "indicatorName": "Adult literacy rate", "theme": "EDUCATION"},
    {"indicatorId": "CR.1", "indicatorName": "Completion rate primary", "theme": "EDUCATION"},
    {"indicatorId": "XGDP.FSGOV", "indicatorName": "Government expenditure on education", "theme": "EDUCATION"},
]

MOCK_UIS_GEO_UNITS = [
    {"geoUnitId": "CHE", "geoUnitName": "Switzerland", "entityType": "COUNTRY"},
    {"geoUnitId": "DEU", "geoUnitName": "Germany", "entityType": "COUNTRY"},
    {"geoUnitId": "FIN", "geoUnitName": "Finland", "entityType": "COUNTRY"},
    {"geoUnitId": "WORLD", "geoUnitName": "World", "entityType": "REGION"},
]

MOCK_UIS_OBSERVATIONS = {
    "observations": [
        {"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": 2020, "value": 99.0},
        {"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": 2021, "value": 99.1},
        {"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": 2022, "value": 99.2},
    ]
}

MOCK_UIS_MULTI_COUNTRY = {
    "observations": [
        {"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": 2022, "value": 99.2},
        {"geoUnit": "DEU", "geoUnitName": "Germany", "year": 2022, "value": 99.1},
        {"geoUnit": "FIN", "geoUnitName": "Finland", "year": 2022, "value": 99.0},
    ]
}

MOCK_VERSIONS = [
    {"version": "20251112-3e719d9a", "publicationDate": "2025-11-13", "description": "November 2025 Refresh"},
    {"version": "20250917-73f4b95c", "publicationDate": "2025-09-18", "description": "September 2025 Release"},
]

MOCK_OECD_DATA = {
    "dataSets": [
        {
            "observations": {
                "0:0:0:0": [95.2],
                "0:1:0:0": [96.1],
                "1:0:0:0": [91.3],
            }
        }
    ],
    "structure": {
        "dimensions": {
            "observation": [
                {"id": "REF_AREA", "name": "Country", "values": [{"id": "CHE", "name": "Switzerland"}]},
                {"id": "EDUCATION_LEV", "name": "Education Level", "values": []},
            ]
        }
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EINFACHE TESTS – Hilfsfunktionen und Konstanten
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestConstants:
    """Tests für die lokalen Konstanten-Tabellen."""

    def test_unesco_indicators_not_empty(self):
        assert len(UNESCO_EDUCATION_INDICATORS) >= 10

    def test_unesco_indicators_have_readable_names(self):
        for ind_id, ind_name in UNESCO_EDUCATION_INDICATORS.items():
            assert len(ind_id) >= 2, f"Indikator-ID zu kurz: {ind_id}"
            assert len(ind_name) >= 5, f"Indikatorname zu kurz: {ind_name}"

    def test_oecd_dataflows_not_empty(self):
        assert len(OECD_EDUCATION_DATAFLOWS) >= 5

    def test_key_indicators_present(self):
        assert "LR.AG15T99" in UNESCO_EDUCATION_INDICATORS
        assert "CR.1" in UNESCO_EDUCATION_INDICATORS
        assert "XGDP.FSGOV" in UNESCO_EDUCATION_INDICATORS
        assert "PTR.1" in UNESCO_EDUCATION_INDICATORS

    def test_oecd_key_dataflows_present(self):
        assert "EAG_FISC" in OECD_EDUCATION_DATAFLOWS
        assert "EAG_ENRL" in OECD_EDUCATION_DATAFLOWS


class TestFormatters:
    """Tests für Formatierungshilfsfunktionen."""

    def test_format_country_timeseries_basic(self):
        observations = [
            {"year": 2020, "value": 98.5, "observationStatus": "A"},
            {"year": 2021, "value": 99.0, "observationStatus": "A"},
        ]
        result = format_country_timeseries(observations, "Switzerland", "LR.AG15T99")
        assert "Switzerland" in result
        assert "2020" in result
        assert "98.5" in result

    def test_format_country_timeseries_empty(self):
        result = format_country_timeseries([], "Germany", "LR.AG15T99")
        assert "keine" in result.lower() or "no" in result.lower()

    def test_format_uis_data_markdown(self):
        data = {
            "observations": [
                {"geoUnit": "CHE", "geoUnitName": "Switzerland", "year": 2022, "value": 99.2},
                {"geoUnit": "DEU", "geoUnitName": "Germany", "year": 2022, "value": 99.0},
            ]
        }
        result = format_uis_data_as_markdown(data, "LR.AG15T99", "Adult literacy")
        assert "Switzerland" in result
        assert "Germany" in result
        assert "99.2" in result

    def test_format_uis_data_empty(self):
        result = format_uis_data_as_markdown({}, "LR.AG15T99")
        assert "keine" in result.lower() or "no" in result.lower()

    def test_handle_api_error_timeout(self):
        import httpx
        error = httpx.TimeoutException("timeout")
        result = handle_api_error(error, "test_context")
        assert "Zeitüberschreitung" in result or "timed out" in result.lower()

    def test_handle_api_error_404(self):
        import httpx
        mock_response = AsyncMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("not found", request=AsyncMock(), response=mock_response)
        result = handle_api_error(error)
        assert "404" in result or "nicht gefunden" in result.lower()

    def test_handle_api_error_generic(self):
        result = handle_api_error(ValueError("test error"), "context")
        assert "Fehler" in result or "Error" in result


class TestInputValidation:
    """Tests für Pydantic-Input-Validierung."""

    def test_uis_data_input_valid(self):
        inp = UISDataInput(indicator_id="LR.AG15T99", country_code="CHE")
        assert inp.indicator_id == "LR.AG15T99"
        assert inp.country_code == "CHE"

    def test_uis_data_input_year_range(self):
        with pytest.raises(Exception):
            UISDataInput(indicator_id="LR.AG15T99", start_year=1900)

    def test_uis_compare_max_countries(self):
        with pytest.raises(Exception):
            UISCompareInput(
                indicator_id="LR.AG15T99",
                country_codes=["CHE"] * 20,  # Zu viele
            )

    def test_cross_source_focus_validation(self):
        with pytest.raises(Exception):
            CrossSourceInput(country_codes=["CHE", "DEU"], focus="invalid_focus")

    def test_cross_source_valid_focus(self):
        for focus in ["literacy", "spending", "completion", "teachers", "enrollment"]:
            inp = CrossSourceInput(country_codes=["CHE", "DEU"], focus=focus)
            assert inp.focus == focus


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MITTLERE TESTS – Tool-Funktionen mit Mock-API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestUISTools:
    """Tests für UNESCO UIS Tool-Funktionen."""

    @pytest.mark.asyncio
    async def test_uis_list_indicators_success(self):
        with patch(
            "global_education_mcp.server.uis_get_indicators",
            new_callable=AsyncMock,
            return_value=MOCK_UIS_INDICATORS,
        ):
            params = UISIndicatorsInput(limit=50)
            result = await uis_list_indicators(params)
            assert "LR.AG15T99" in result
            assert "Adult literacy rate" in result

    @pytest.mark.asyncio
    async def test_uis_list_indicators_with_search(self):
        with patch(
            "global_education_mcp.server.uis_get_indicators",
            new_callable=AsyncMock,
            return_value=MOCK_UIS_INDICATORS,
        ):
            params = UISIndicatorsInput(search="literacy")
            result = await uis_list_indicators(params)
            assert "LR.AG15T99" in result

    @pytest.mark.asyncio
    async def test_uis_list_indicators_api_failure_fallback(self):
        """Bei API-Fehler soll Fallback auf lokale Indikatoren erfolgen."""
        with patch(
            "global_education_mcp.server.uis_get_indicators",
            side_effect=Exception("API down"),
        ):
            params = UISIndicatorsInput()
            result = await uis_list_indicators(params)
            # Fallback-Indikatoren aus der lokalen Tabelle
            assert "LR.AG15T99" in result or "Alphabetisierung" in result

    @pytest.mark.asyncio
    async def test_uis_list_countries_success(self):
        with patch(
            "global_education_mcp.server.uis_get_geo_units",
            new_callable=AsyncMock,
            return_value=MOCK_UIS_GEO_UNITS,
        ):
            params = UISGeoUnitsInput()
            result = await uis_list_countries(params)
            assert "CHE" in result
            assert "Switzerland" in result

    @pytest.mark.asyncio
    async def test_uis_list_countries_search_filter(self):
        with patch(
            "global_education_mcp.server.uis_get_geo_units",
            new_callable=AsyncMock,
            return_value=MOCK_UIS_GEO_UNITS,
        ):
            params = UISGeoUnitsInput(search="Switzerland")
            result = await uis_list_countries(params)
            assert "CHE" in result
            assert "Germany" not in result

    @pytest.mark.asyncio
    async def test_uis_list_countries_fallback(self):
        """Bekannte Ländercodes als Fallback bei API-Fehler."""
        with patch(
            "global_education_mcp.server.uis_get_geo_units",
            side_effect=Exception("API down"),
        ):
            params = UISGeoUnitsInput()
            result = await uis_list_countries(params)
            assert "CHE" in result
            assert "Schweiz" in result

    @pytest.mark.asyncio
    async def test_uis_get_education_data_timeseries(self):
        with patch(
            "global_education_mcp.server.uis_get_data",
            new_callable=AsyncMock,
            return_value=MOCK_UIS_OBSERVATIONS,
        ):
            params = UISDataInput(indicator_id="LR.AG15T99", country_code="CHE")
            result = await uis_get_education_data(params)
            assert "CHE" in result or "Switzerland" in result
            assert "99" in result

    @pytest.mark.asyncio
    async def test_uis_get_education_data_all_countries(self):
        with patch(
            "global_education_mcp.server.uis_get_data",
            new_callable=AsyncMock,
            return_value=MOCK_UIS_MULTI_COUNTRY,
        ):
            params = UISDataInput(indicator_id="LR.AG15T99")
            result = await uis_get_education_data(params)
            assert "Switzerland" in result or "CHE" in result

    @pytest.mark.asyncio
    async def test_uis_get_education_data_error(self):
        import httpx
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        with patch(
            "global_education_mcp.server.uis_get_data",
            side_effect=httpx.HTTPStatusError("bad request", request=AsyncMock(), response=mock_response),
        ):
            params = UISDataInput(indicator_id="INVALID.ID", country_code="CHE")
            result = await uis_get_education_data(params)
            assert "Fehler" in result or "Error" in result

    @pytest.mark.asyncio
    async def test_uis_list_versions(self):
        with patch(
            "global_education_mcp.server.uis_get_versions",
            new_callable=AsyncMock,
            return_value=MOCK_VERSIONS,
        ):
            result = await uis_list_versions()
            assert "20251112" in result
            assert "November 2025" in result


class TestOECDTools:
    """Tests für OECD Tool-Funktionen."""

    @pytest.mark.asyncio
    async def test_oecd_list_education_datasets(self):
        with patch(
            "global_education_mcp.server.oecd_get_dataflows",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await oecd_list_education_datasets()
            assert "EAG_FISC" in result
            assert "EAG_ENRL" in result
            assert "Bildungsausgaben" in result

    @pytest.mark.asyncio
    async def test_oecd_get_education_indicator_success(self):
        with patch(
            "global_education_mcp.server.oecd_get_education_data",
            new_callable=AsyncMock,
            return_value=MOCK_OECD_DATA,
        ):
            params = OECDDataInput(dataflow_id="EAG_FISC", countries=["CHE", "DEU"])
            result = await oecd_get_education_indicator(params)
            assert "EAG_FISC" in result
            assert "Beobachtungen" in result or "observation" in result.lower()

    @pytest.mark.asyncio
    async def test_oecd_get_education_indicator_no_data(self):
        with patch(
            "global_education_mcp.server.oecd_get_education_data",
            new_callable=AsyncMock,
            return_value={"dataSets": [], "structure": {}},
        ):
            params = OECDDataInput(dataflow_id="EAG_FISC")
            result = await oecd_get_education_indicator(params)
            assert "keine Daten" in result.lower() or "EAG_FISC" in result

    @pytest.mark.asyncio
    async def test_oecd_get_education_indicator_error_graceful(self):
        with patch(
            "global_education_mcp.server.oecd_get_education_data",
            side_effect=Exception("Network error"),
        ):
            params = OECDDataInput(dataflow_id="EAG_FISC")
            result = await oecd_get_education_indicator(params)
            assert "EAG_FISC" in result  # Hilfreiche Fehlermeldung mit Kontext

    @pytest.mark.asyncio
    async def test_oecd_search_datasets(self):
        mock_results = [
            {"id": "EAG_FISC", "agencyID": "OECD.EDU.IMEP", "name": "Education Spending"},
        ]
        with patch(
            "global_education_mcp.server.oecd_search_education_datasets",
            new_callable=AsyncMock,
            return_value=mock_results,
        ):
            params = OECDSearchInput(keyword="education")
            result = await oecd_search_datasets(params)
            assert "EAG_FISC" in result

    @pytest.mark.asyncio
    async def test_oecd_search_datasets_no_results(self):
        with patch(
            "global_education_mcp.server.oecd_search_education_datasets",
            new_callable=AsyncMock,
            return_value=[],
        ):
            params = OECDSearchInput(keyword="xyznotfound")
            result = await oecd_search_datasets(params)
            assert "gefunden" in result or "found" in result.lower()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KOMPLEXE TESTS – Mehrschrittige Workflows
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestComplexWorkflows:
    """Komplexe Tests für mehrstufige Analyseworkflows."""

    @pytest.mark.asyncio
    async def test_uis_compare_countries_sorted_output(self):
        """Vergleich soll nach Wert sortiert sein."""
        def mock_uis_data(indicator, geo_unit=None, **kwargs):
            values = {"CHE": 99.2, "DEU": 99.0, "AUT": 98.5, "FIN": 99.5}
            if geo_unit in values:
                return {"observations": [{"year": 2022, "value": values[geo_unit], "geoUnitName": geo_unit}]}
            return {"observations": []}

        with patch("global_education_mcp.server.uis_get_data", new_callable=AsyncMock, side_effect=mock_uis_data):
            params = UISCompareInput(
                indicator_id="LR.AG15T99",
                country_codes=["CHE", "DEU", "AUT", "FIN"],
            )
            result = await uis_compare_countries(params)
            assert "Rang" in result
            assert "FIN" in result
            assert "CHE" in result
            # FIN (99.5) sollte vor CHE (99.2) erscheinen
            fin_pos = result.find("FIN")
            che_pos = result.find("CHE")
            assert fin_pos < che_pos

    @pytest.mark.asyncio
    async def test_uis_compare_countries_partial_failure(self):
        """Teilergebnisse sollen trotz einzelner Fehler zurückgegeben werden."""
        call_count = 0

        async def mock_uis_data(indicator, geo_unit=None, **kwargs):
            nonlocal call_count
            call_count += 1
            if geo_unit == "INVALID":
                raise Exception("Country not found")
            return {"observations": [{"year": 2022, "value": 95.0, "geoUnitName": geo_unit}]}

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_uis_data):
            params = UISCompareInput(
                indicator_id="LR.AG15T99",
                country_codes=["CHE", "INVALID", "DEU"],
            )
            result = await uis_compare_countries(params)
            assert "CHE" in result
            assert "DEU" in result

    @pytest.mark.asyncio
    async def test_uis_country_education_profile_complete(self):
        """Profil soll alle 10 Kernindikatoren abdecken."""

        async def mock_uis_data(indicator, geo_unit=None, **kwargs):
            return {"observations": [{"year": 2022, "value": 95.0, "geoUnitName": "Switzerland"}]}

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_uis_data):
            params = UISCountryProfileInput(country_code="CHE")
            result = await uis_country_education_profile(params)
            # Alle Kernindikatoren sollten erwähnt sein
            assert "Alphabetisierungsrate" in result
            assert "Einschulungsrate" in result
            assert "Abschlussquote" in result
            assert "Bildungsausgaben" in result

    @pytest.mark.asyncio
    async def test_education_benchmark_all_focus_types(self):
        """Benchmark soll für alle 5 Fokustypen funktionieren."""

        async def mock_uis_data(indicator, geo_unit=None, **kwargs):
            return {"observations": [{"year": 2022, "value": 90.0, "geoUnitName": geo_unit or "?"}]}

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_uis_data):
            for focus in ["literacy", "spending", "completion", "teachers", "enrollment"]:
                params = CrossSourceInput(country_codes=["CHE", "DEU"], focus=focus)
                result = await education_benchmark_countries(params)
                assert "CHE" in result, f"Benchmark für focus={focus} enthält keine Länderdaten"
                assert "UNESCO" in result

    @pytest.mark.asyncio
    async def test_education_benchmark_sorts_correctly(self):
        """Benchmark-Tabellen sollen nach Wert sortiert sein."""
        call_count = 0
        countries_data = [
            ("CHE", 85.0),
            ("DEU", 92.0),
            ("FIN", 96.0),
        ]

        async def mock_uis_data(indicator, geo_unit=None, **kwargs):
            for code, value in countries_data:
                if geo_unit == code:
                    return {"observations": [{"year": 2022, "value": value, "geoUnitName": code}]}
            return {"observations": []}

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_uis_data):
            params = CrossSourceInput(country_codes=["CHE", "DEU", "FIN"], focus="literacy")
            result = await education_benchmark_countries(params)
            # Tabellendaten extrahieren (nach dem Header-Trennstrich)
            table_start = result.find("|---")
            table_section = result[table_start:] if table_start >= 0 else result
            # FIN (96) soll vor DEU (92) erscheinen, DEU vor CHE (85)
            fin_pos = table_section.find("FIN")
            deu_pos = table_section.find("DEU")
            che_pos = table_section.find("CHE")
            assert fin_pos < deu_pos, f"FIN ({fin_pos}) sollte vor DEU ({deu_pos}) erscheinen"
            assert deu_pos < che_pos, f"DEU ({deu_pos}) sollte vor CHE ({che_pos}) erscheinen"

    @pytest.mark.asyncio
    async def test_full_workflow_indicator_to_comparison(self):
        """Vollständiger Workflow: Indikator suchen → Daten abrufen → vergleichen."""

        # Schritt 1: Indikatoren auflisten
        with patch(
            "global_education_mcp.server.uis_get_indicators",
            new_callable=AsyncMock,
            return_value=MOCK_UIS_INDICATORS,
        ):
            indicator_list = await uis_list_indicators(UISIndicatorsInput(search="literacy"))
            assert "LR.AG15T99" in indicator_list

        # Schritt 2: Daten für Schweiz abrufen
        with patch(
            "global_education_mcp.server.uis_get_data",
            new_callable=AsyncMock,
            return_value=MOCK_UIS_OBSERVATIONS,
        ):
            data_result = await uis_get_education_data(
                UISDataInput(indicator_id="LR.AG15T99", country_code="CHE")
            )
            assert "99" in data_result

        # Schritt 3: Vergleich erstellen
        async def mock_compare_data(indicator, geo_unit=None, **kwargs):
            vals = {"CHE": 99.2, "DEU": 99.0, "FIN": 99.5}
            v = vals.get(geo_unit, 95.0)
            return {"observations": [{"year": 2022, "value": v, "geoUnitName": geo_unit}]}

        with patch("global_education_mcp.server.uis_get_data", side_effect=mock_compare_data):
            compare_result = await uis_compare_countries(
                UISCompareInput(
                    indicator_id="LR.AG15T99",
                    country_codes=["CHE", "DEU", "FIN"],
                )
            )
            assert "Rang" in compare_result
            assert "FIN" in compare_result
