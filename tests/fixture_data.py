"""Zugriff auf die aufgezeichneten Fixtures unter ``tests/fixtures/``.

Quelle, Datum, Auswahlregel und SHA-256 je Datei stehen in
``tests/fixtures/PROVENANCE.md``, geschrieben von
``scripts/record_fixtures.py``.

Davor hatte dieses Repo weder aufgezeichnete Fixtures noch **einen einzigen
Live-Test**: ``pytest -m integration`` sammelte null ein. Nichts hier war je
gegen die Quelle gehalten worden — und drei von vier UIS-Pfaden antworteten
seit der API-Umstellung mit HTTP 404, ohne dass eine Suite je rot wurde.

Ein fehlender Name ist hier ein Fehler und keine leere Struktur. Ein Loader,
der bei einem Tippfehler ``{}`` zurueckgibt, erzeugt einen Test, der nichts
mehr prueft und trotzdem Erfolg meldet — die teuerste Sorte gruen.
"""

from __future__ import annotations

import copy
import json
from functools import cache
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@cache
def _load(name: str) -> Any:
    path = FIXTURES / name
    if not path.is_file():
        available = sorted(p.name for p in FIXTURES.glob("*.json"))
        raise FileNotFoundError(
            f"Keine Fixture {name!r} unter {FIXTURES}. Vorhanden: {available}. "
            "Neu aufzeichnen mit `python scripts/record_fixtures.py`."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def payload(name: str) -> Any:
    """Die aufgezeichnete Antwort für ``name`` — als Kopie.

    Der Produktivcode bekommt diese Struktur in die Hand; ein Test, der sie
    verändert, würde sonst dem nächsten die Fixture unter den Füssen wegziehen.
    """
    return copy.deepcopy(_load(name))


def declared_indicator_codes() -> set[str]:
    """Die Indikator-Codes, die die Quelle führt.

    Das ist der Vertrag, gegen den ``UNESCO_EDUCATION_INDICATORS`` gehalten
    wird. Am 2026-08-08 gab es **12 der 22** Einträge dieser Tabelle hier
    nicht — und weil der API-Pfad zugleich 404 gab, war genau diese Tabelle
    die einzige Indikatorliste, die ein Nutzer je zu sehen bekam.
    """
    return {d["indicatorCode"] for d in payload("uis_definitions_indicators.json")}


def declared_query_params(path: str) -> set[str]:
    """Die Query-Parameter, die die OpenAPI der Quelle für ``path`` deklariert.

    Ein Parameter, der hier fehlt, wird nicht mit HTTP 400 abgelehnt — die UIS
    antwortet mit 200 und lässt ihn fallen. Ein nicht angewandter Filter sieht
    deshalb aus wie ein angewandter, und nur diese Liste trennt die beiden.
    """
    params = payload("uis_openapi_query_params.json")
    if path not in params:
        raise KeyError(f"Für '{path}' ist nichts aufgezeichnet. Vorhanden: {sorted(params)}.")
    return set(params[path])
