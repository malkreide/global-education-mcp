"""Was dieser Server annimmt, gegen das gehalten, was die UNESCO UIS liefert.

Zwei Ebenen, und beide werden gebraucht:

* **Vertragstests** halten den Produktivcode gegen `tests/fixtures/`,
  aufgezeichnet am 2026-08-08 von `api.uis.unesco.org`. Sie laufen ohne Netz.
* **Live-Tests** (`-m integration`) fragen die Quelle. Sie sind die einzigen
  Tests dieses Repos, die eine Änderung an der Quelle überhaupt bemerken
  können — vorher gab es hier keinen einzigen; `pytest -m integration`
  sammelte null ein.

Warum das nötig war: Die Suite hatte 128 grüne Tests, während drei von vier
UIS-Pfaden mit HTTP 404 antworteten und jede Datenabfrage eine leere Liste
zurückbrachte. Möglich war das, weil die Fixtures dieselben erfundenen
Feldnamen trugen wie der Produktivcode. Ein Mock aus demselben Kopf kann die
Annahme dieses Kopfes nicht widerlegen.
"""

from __future__ import annotations

import httpx
import pytest

from global_education_mcp.api_client import (
    UIS_QUALIFIERS,
    UNESCO_BASE_URL,
    UNESCO_EDUCATION_INDICATORS,
    UpstreamShapeError,
    uis_hints,
    uis_records,
)
from tests.fixture_data import (
    declared_indicator_codes,
    declared_query_params,
    payload,
)

DATA_PATH = "/api/public/data/indicators"
DEFS_PATH = "/api/public/definitions/indicators"


# ─── Der Vertrag: gegen die Aufzeichnung ──────────────────────────────────────


class TestIndicatorTableContract:
    """`UNESCO_EDUCATION_INDICATORS` gegen die Definitionsliste der Quelle.

    Am 2026-08-08 gab es **12 der 22 IDs** dieser Tabelle in der Quelle nicht:
    alle drei `NERA.*`, alle drei `XUNIT.*`, alle drei `PTR.*`, beide `GPI.*`
    und `SDG4`. Das waren genau die Kategorien, die der Docstring von
    `uis_list_indicators` bewarb — und weil der API-Pfad zugleich 404 gab und
    der Aufrufer auf diese Tabelle zurückfiel, war sie die einzige
    Indikatorliste, die ein Nutzer je zu sehen bekam.
    """

    def test_every_offered_indicator_exists_in_the_source(self):
        declared = declared_indicator_codes()
        missing = sorted(k for k in UNESCO_EDUCATION_INDICATORS if k not in declared)
        assert not missing, (
            f"{len(missing)} angebotene Indikator-IDs gibt es in der aufgezeichneten Definitionsliste nicht: {missing}"
        )

    def test_the_recording_is_wide_enough_to_refute_something(self):
        """Ein Vertrag, der nur die eigenen Zeilen enthält, prüft nichts.

        Enthielte die Fixture ausschliesslich die angebotenen IDs, wäre der
        Test oben eine Tautologie: Die Auswahlregel hätte die Prüfung schon
        erfüllt. Aufgezeichnet sind deshalb zusätzlich fremde Einträge.
        """
        declared = declared_indicator_codes()
        assert declared - set(UNESCO_EDUCATION_INDICATORS), (
            "Die aufgezeichnete Definitionsliste enthält nur noch die "
            "angebotenen IDs — dann prüft der Vertragstest sich selbst."
        )

    def test_no_indicator_family_the_source_dropped_returns(self):
        """Die erfundenen Präfixe dürfen nicht zurückkehren."""
        gone = ("NERA.", "XUNIT.", "PTR.", "GPI.")
        back = sorted(k for k in UNESCO_EDUCATION_INDICATORS if k.startswith(gone))
        assert not back, f"Diese Präfixe führt die UIS nicht: {back}"


class TestRecordedShapeContract:
    """Die Feldnamen der Testmocks gegen die aufgezeichnete Antwort.

    Die Mocks in `test_server.py` sind weiterhin Literale — sie müssen
    lesbar bleiben. Was sie nicht mehr dürfen, ist eine Form erfinden. Diese
    Klasse ist die Klammer dazwischen.
    """

    def test_data_rows_carry_the_fields_the_mocks_use(self):
        recorded = payload("uis_data_records.json")["records"][0]
        for field in ("indicatorId", "geoUnit", "year", "value", "magnitude", "qualifier"):
            assert field in recorded, f"`{field}` führt eine UIS-Datenzeile nicht"

    def test_data_rows_do_not_carry_the_fields_that_were_invented(self):
        recorded = payload("uis_data_records.json")["records"][0]
        for invented in ("observationStatus", "geoUnitName"):
            assert invented not in recorded, (
                f"`{invented}` ist wieder da — dann gehört der Leser nachgezogen statt der Test angepasst."
            )

    def test_definitions_use_indicator_code_not_indicator_id(self):
        """Zwei Namen für dieselbe Sache in derselben API.

        Datenzeile: `indicatorId`. Definitionsliste: `indicatorCode`. Gelesen
        wurde in beiden Fällen `indicatorId` — in der Definitionsliste fiel das
        auf das Literal `"?"` zurück, und in jeder der 5063 Zeilen des
        Werkzeugs, dessen einzige Aufgabe das Finden von IDs ist, stand ein
        Fragezeichen.
        """
        first = payload("uis_definitions_indicators.json")[0]
        assert "indicatorCode" in first
        assert "indicatorId" not in first

    def test_geo_units_use_type_not_entity_type(self):
        first = payload("uis_definitions_geounits.json")[0]
        assert set(first) == {"id", "name", "type"}, (
            f"Ein Ländereintrag führt {sorted(first)}. Der Typfilter las "
            '`entityType` und verglich damit ausnahmslos `"" == "NATIONAL"`.'
        )

    def test_recorded_geo_units_contain_both_types(self):
        """Sonst wäre der Typfilter mit dieser Fixture nicht prüfbar."""
        types = {g["type"] for g in payload("uis_definitions_geounits.json")}
        assert types == {"NATIONAL", "REGIONAL"}, types


class TestQueryParameterContract:
    """Welche Query-Parameter die Quelle deklariert — und welche sie schluckt.

    Die UIS lehnt einen unbekannten Parameter nicht ab. Sie antwortet mit
    HTTP 200 und lässt ihn fallen. Ein nicht angewandter Filter ist deshalb von
    einem angewandten nur an dieser Liste zu unterscheiden.
    """

    def test_year_filter_uses_the_declared_names(self):
        declared = declared_query_params(DATA_PATH)
        assert {"start", "end"} <= declared
        assert "startYear" not in declared and "endYear" not in declared

    def test_definitions_endpoint_has_no_theme_parameter(self):
        assert "theme" not in declared_query_params(DEFS_PATH)

    def test_the_wrong_names_returned_the_full_series(self):
        """Der aufgezeichnete Beleg, nicht die Behauptung.

        Dieselbe Reihe zweimal: mit den gesendeten Parameternamen und mit den
        deklarierten. Eine einzelne Antwort mit 14 Zeilen sieht nach reichlich
        Daten aus — erst das Paar zeigt den ignorierten Filter.
        """
        rec = payload("uis_data_year_filter.json")
        assert rec["start_end"]["jahre"] == [2015, 2016, 2017, 2018]
        assert len(rec["startYear_endYear"]["jahre"]) > 4

    def test_theme_parameter_did_not_filter(self):
        """Die Kontrolle mit dem erfundenen Thema trägt diesen Befund.

        Dass `theme=EDUCATION` alle Zeilen liefert, könnte auch heissen, dass
        fast alles EDUCATION ist — und tatsächlich sind es 4986 von 5063.
        Erst der erfundene Wert mit derselben Zahl zeigt, dass der Parameter
        nicht gelesen wird.
        """
        census = payload("uis_indicator_themes.json")["antwortgroesse_je_theme_parameter"]
        assert len(set(census.values())) == 1, census
        assert any("bogus" in k for k in census), "Die Kontrollzeile fehlt — dann belegt die Messung nichts."


class TestEnvelopeAndHints:
    """Der Umschlag heisst `records`, und `hints` sagt, warum er leer ist."""

    def test_records_is_read_from_the_recorded_envelope(self):
        rows = uis_records(payload("uis_data_records.json"))
        assert len(rows) == 14, "CR.1/CHE lieferte am 2026-08-08 vierzehn Zeilen"

    def test_a_genuinely_empty_result_stays_empty(self):
        assert uis_records(payload("uis_data_empty.json")) == []

    def test_a_missing_envelope_is_an_error_not_an_empty_result(self):
        """Der Befund in einer Zeile.

        Gesucht wurde `observations`, mit `data` als zweitem Versuch und `[]`
        als drittem. Aus jeder Antwort wurde damit eine leere Liste — und aus
        einem Formfehler die Aussage «für dieses Land gibt es keine Daten».
        """
        with pytest.raises(UpstreamShapeError):
            uis_records({"observations": [{"year": 2022, "value": 99.0}]})

    def test_empty_and_unknown_country_are_indistinguishable_without_hints(self):
        """Warum `hints` gelesen werden muss.

        Beide Antworten haben HTTP 200 und leeres `records`. Ohne `hints` ist
        ein Tippfehler im Ländercode dasselbe wie ein Land ohne Daten.
        """
        empty = payload("uis_data_empty.json")
        unknown = payload("uis_data_unknown_geounit.json")
        assert uis_records(empty) == uis_records(unknown) == []
        assert uis_hints(empty) == []
        assert any("could not be found" in h for h in uis_hints(unknown))

    def test_hints_carry_the_source_code(self):
        assert any("UIS::HINT::003" in h for h in uis_hints(payload("uis_data_unknown_geounit.json")))

    def test_hints_tolerates_an_absent_field(self):
        assert uis_hints({"records": []}) == []


class TestQualifierLegend:
    """Ein geschätzter Wert darf nicht aussehen wie ein gemeldeter."""

    def test_every_qualifier_in_the_recording_has_a_legend_entry(self):
        seen = {r.get("qualifier") for r in payload("uis_data_records.json")["records"]}
        unknown = {q for q in seen if q and q not in UIS_QUALIFIERS}
        assert not unknown, f"Ohne Legende steht hier ein Kürzel zum Raten: {unknown}"


class TestTheCodeActuallySendsWhatItClaims:
    """Was der Server auf die Leitung legt — nicht, was die Fixture zeigt.

    Die Klassen darüber halten den aufgezeichneten Vertrag fest. Sie würden
    aber allesamt grün bleiben, wenn der Produktivcode weiterhin die falschen
    Parameternamen sendete: Sie lesen die Aufzeichnung, nicht den Aufruf. Das
    hier ist der fehlende Teil — jeder Test hier wurde gegen eine gezielte
    Rückmutation gehalten und wird rot.
    """

    async def test_the_year_filter_goes_out_as_start_and_end(self):
        from unittest.mock import AsyncMock, patch

        from global_education_mcp.api_client import uis_get_data

        with patch(
            "global_education_mcp.api_client.http_get_json",
            new_callable=AsyncMock,
            return_value={"records": []},
        ) as get:
            await uis_get_data(indicator="CR.1", geo_unit="CHE", start_year=2015, end_year=2018)
        sent = get.await_args.kwargs["params"]
        assert sent["start"] == 2015 and sent["end"] == 2018
        assert "startYear" not in sent and "endYear" not in sent, (
            f"Gesendet wurde {sorted(sent)}. Die Quelle kennt diese Namen nicht, "
            "lehnt sie aber nicht ab — der Filter fällt still weg."
        )

    async def test_the_theme_filter_is_applied_locally_and_not_sent(self):
        from unittest.mock import AsyncMock, patch

        from global_education_mcp.api_client import uis_get_indicators

        rows = [
            {"indicatorCode": "CR.1", "name": "Completion", "theme": "EDUCATION"},
            {"indicatorCode": "CULT.1", "name": "Museen", "theme": "CULTURE"},
        ]
        with patch(
            "global_education_mcp.api_client.http_get_json",
            new_callable=AsyncMock,
            return_value=rows,
        ) as get:
            got = await uis_get_indicators(theme="CULTURE")
        assert [i["indicatorCode"] for i in got] == ["CULT.1"], (
            "Der Themenfilter greift nicht. An die Quelle gereicht bewirkt er "
            "nichts: Sie kennt den Parameter nicht und antwortet mit allen "
            "5063 Zeilen — als Auswahl beschriftet."
        )
        assert not get.await_args.kwargs.get("params"), "`theme` gehört nicht auf die Leitung."

    async def test_the_country_type_filter_matches_the_recorded_field(self):
        from unittest.mock import AsyncMock, patch

        from global_education_mcp.server import UISGeoUnitsInput, uis_list_countries

        recorded = payload("uis_definitions_geounits.json")
        with patch(
            "global_education_mcp.server.uis_get_geo_units",
            new_callable=AsyncMock,
            return_value=recorded,
        ):
            result = await uis_list_countries(UISGeoUnitsInput(entity_type="REGIONAL"))

        expected = [g["id"] for g in recorded if g["type"] == "REGIONAL"]
        assert expected, "Die Fixture führt keine regionalen Aggregate — dann prüft dieser Test nichts."
        assert f"`{expected[0]}`" in result, (
            "Der Typfilter liefert nichts. Er las `entityType`; die Quelle "
            "schreibt `type`. Der Vergleich lautete damit ausnahmslos "
            '`"" == "REGIONAL"` — aus 462 Einträgen wurden null.'
        )
        for national in (g["id"] for g in recorded if g["type"] == "NATIONAL"):
            assert f"`{national}`" not in result, f"{national} ist NATIONAL und darf hier nicht stehen."


# ─── Live: gegen die Quelle ───────────────────────────────────────────────────
#
# Die ersten Tests dieses Repos, die überhaupt an die Quelle gehen. Sie prüfen
# nicht die Werte — die ändern sich —, sondern die Form und die Pfade. Genau
# das war das, was fünf Jahre lang niemand geprüft hat.


@pytest.fixture(scope="module")
def client():
    with httpx.Client(timeout=60.0, follow_redirects=True) as c:
        yield c


@pytest.mark.integration
class TestLiveUISPaths:
    def test_the_paths_the_server_builds_still_answer(self, client):
        for path in ("/definitions/indicators", "/definitions/geounits", "/versions"):
            r = client.get(f"{UNESCO_BASE_URL}{path}")
            assert r.status_code == 200, f"{path} antwortet mit {r.status_code}"
            assert isinstance(r.json(), list)

    def test_the_paths_the_server_used_to_build_are_still_gone(self, client):
        """Die Kontrolle zum Befund.

        Ohne sie belegte der Test oben nur, dass die neuen Pfade gehen — nicht,
        dass die alten der Fehler waren. Kehrt einer von ihnen zurück, ist der
        Befund überholt und gehört neu geschrieben, nicht stillschweigend
        weitergetragen.
        """
        for path in ("/indicators", "/geo-units", "/data"):
            r = client.get(f"{UNESCO_BASE_URL}{path}")
            assert r.status_code == 404, f"{path} antwortet wieder mit {r.status_code}"

    def test_the_data_envelope_is_still_called_records(self, client):
        r = client.get(f"{UNESCO_BASE_URL}/data/indicators", params={"indicator": "CR.1", "geoUnit": "CHE"})
        r.raise_for_status()
        assert uis_records(r.json()), "CR.1/CHE liefert keine Zeilen mehr"

    def test_the_year_filter_still_needs_start_and_end(self, client):
        base = {"indicator": "CR.1", "geoUnit": "CHE"}
        right = client.get(f"{UNESCO_BASE_URL}/data/indicators", params={**base, "start": 2015, "end": 2018})
        wrong = client.get(f"{UNESCO_BASE_URL}/data/indicators", params={**base, "startYear": 2015, "endYear": 2018})
        right.raise_for_status()
        wrong.raise_for_status()
        assert sorted({x["year"] for x in right.json()["records"]}) == [2015, 2016, 2017, 2018]
        # Die Kontrolle: Der falsche Name wird nicht abgelehnt, sondern
        # fallengelassen — daran hing der ganze Befund.
        assert wrong.status_code == 200
        assert len({x["year"] for x in wrong.json()["records"]}) > 4

    def test_an_unknown_country_still_answers_200_with_a_hint(self, client):
        r = client.get(f"{UNESCO_BASE_URL}/data/indicators", params={"indicator": "CR.1", "geoUnit": "XXX"})
        assert r.status_code == 200
        assert uis_records(r.json()) == []
        assert uis_hints(r.json()), "Ohne Hinweis ist ein Tippfehler nicht mehr von Datenmangel zu trennen"

    def test_every_offered_indicator_still_exists(self, client):
        r = client.get(f"{UNESCO_BASE_URL}/definitions/indicators")
        r.raise_for_status()
        codes = {d["indicatorCode"] for d in r.json()}
        missing = sorted(k for k in UNESCO_EDUCATION_INDICATORS if k not in codes)
        assert not missing, f"Die Quelle führt diese angebotenen IDs nicht mehr: {missing}"


@pytest.mark.integration
class TestLiveProductionCodeReachesTheSource:
    """Die Werkzeuge selbst gegen die Quelle — nicht eine Abschrift davon.

    Die Klasse darüber baut ihre URLs aus Literalen. Sie bliebe deshalb grün,
    wenn der Server wieder `/indicators` bauen würde: Sie misst die Quelle,
    aber nicht den Aufrufer. Gegengeprüft, indem der Pfad im Produktivcode auf
    den alten zurückgesetzt wurde — die Klasse oben merkte nichts, diese wird
    rot.

    Genau dieselbe Lücke hatte ein Schwester-Repo, in dem das
    Aufzeichnungsskript eine andere Adresse abfragte als der Server. Was
    darüber geprüft wird, muss der Produktivcode aufbauen.
    """

    async def test_uis_get_indicators_returns_the_catalogue(self):
        from global_education_mcp.api_client import uis_get_indicators

        got = await uis_get_indicators()
        assert len(got) > 4000, f"Nur {len(got)} Indikatoren — am 2026-08-08 waren es 5063."
        assert "indicatorCode" in got[0]

    async def test_uis_get_indicators_theme_filter_narrows(self):
        from global_education_mcp.api_client import uis_get_indicators

        alle = await uis_get_indicators()
        kultur = await uis_get_indicators(theme="CULTURE")
        assert 0 < len(kultur) < len(alle)
        assert {i["theme"] for i in kultur} == {"CULTURE"}

    async def test_uis_get_geo_units_returns_both_types(self):
        from global_education_mcp.api_client import uis_get_geo_units

        got = await uis_get_geo_units()
        assert {g["type"] for g in got} == {"NATIONAL", "REGIONAL"}
        assert any(g["id"] == "CHE" for g in got)

    async def test_uis_get_data_returns_rows_and_honours_the_window(self):
        from global_education_mcp.api_client import uis_get_data

        raw = await uis_get_data(indicator="CR.1", geo_unit="CHE", start_year=2015, end_year=2018)
        assert sorted({r["year"] for r in uis_records(raw)}) == [2015, 2016, 2017, 2018]

    async def test_uis_get_data_names_an_unknown_country(self):
        from global_education_mcp.api_client import uis_get_data

        raw = await uis_get_data(indicator="CR.1", geo_unit="XXX")
        assert uis_records(raw) == []
        assert uis_hints(raw), "Der Grund steht im Payload und gehört ausgegeben."

    async def test_uis_get_versions_returns_versions(self):
        from global_education_mcp.api_client import uis_get_versions

        got = await uis_get_versions()
        assert got and "version" in got[0]

    async def test_the_tool_output_carries_real_values(self):
        """Der Endpunkt, an dem der Befund für einen Nutzer sichtbar wurde.

        Dieses Werkzeug antwortete auf jede Anfrage «Keine Zeitreihendaten für
        CHE» — bei 14 vorhandenen Zeilen.
        """
        from global_education_mcp.server import UISDataInput, uis_get_education_data

        out = await uis_get_education_data(UISDataInput(indicator_id="CR.1", country_code="CHE"))
        assert "Keine Zeitreihendaten" not in out
        assert "| 2015 |" in out
