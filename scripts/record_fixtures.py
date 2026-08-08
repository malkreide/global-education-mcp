#!/usr/bin/env python3
"""Zeichnet die Test-Fixtures von der UNESCO-UIS-API auf.

    python scripts/record_fixtures.py

WARUM ES DAS GIBT. Ein handgeschriebener Mock kodiert die Annahme seines
Autors und kann sie deshalb prinzipiell nicht widerlegen: Produktivcode und
Fixture stammen aus demselben Kopf, derselben Stunde, derselben Lektuere der
Doku. Wo beide irren, irren beide gleich, und die Suite bleibt dauerhaft
gruen.

Dieses Repo hatte weder aufgezeichnete Fixtures noch **einen einzigen
Live-Test** — `pytest -m integration` sammelte null ein. Nichts darin war je gegen die
Quelle gehalten worden. Was der erste Vergleich am 2026-08-08 ergab:

1. **Drei von vier UIS-Pfaden waren 404.** Der Server baute `/indicators`,
   `/geo-units` und `/data`; die Quelle fuehrt `/definitions/indicators`,
   `/definitions/geounits` und `/data/indicators`. Nur `/versions` stimmte.

2. **Der Umschlag der Datenantwort hiess anders.** Gelesen wurde
   `observations`, mit `data` als zweitem Versuch und `[]` als drittem — die
   Quelle schreibt `records`. Aus jeder Antwort kam damit eine leere Liste, und
   aus einem Formfehler wurde die Aussage «fuer dieses Land gibt es keine
   Daten». Gemessen liefert `CR.1`/`CHE` **14 Zeilen**.

3. **12 von 22 Indikator-IDs der lokalen Tabelle gibt es nicht** — genau die
   Kategorien, die der Docstring bewarb.

4. **Zwei Filter filterten nie.** `theme` kennt `/definitions/indicators`
   nicht, `startYear`/`endYear` kennt `/data/indicators` nicht — und
   unbekannte Query-Parameter beantwortet die Quelle mit HTTP 200 und laesst
   sie fallen. Die Ausgabe schrieb die Filter trotzdem darueber.

5. **`hints` las niemand.** Ein erfundener Ländercode liefert HTTP 200,
   leeres `records` und im selben Payload den Klartext «The geoUnit could not
   be found, XXX». Daraus wurde «keine Daten für dieses Land».

Aufgezeichnet werden deshalb drei Dinge: die Antworten, die Definitionsliste
als Vertrag — **und Kontrollen**. Ein erfundener `theme`-Wert und ein
erfundener Ländercode belegen, was die Quelle unterscheidet; ohne sie belegt
eine Messung nur, was ICH bekommen habe.

Ohne Aufzeichnungsdatum ist «aufgezeichnet» nach zwei Jahren von «ausgedacht»
nicht mehr zu unterscheiden. Es steht je Datei in
`tests/fixtures/PROVENANCE.md`.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "src"))

# Basis-URL und Indikatorentabelle kommen aus dem Produktivcode. Ein Skript,
# das eine andere Adresse fragt als der Server, misst den falschen Gegenstand.
from global_education_mcp.api_client import (  # noqa: E402
    UNESCO_BASE_URL,
    UNESCO_EDUCATION_INDICATORS,
)

# Das Paar, an dem die Datenaufbereitung haengt. Die Schweiz ist der
# Anwendungsfall dieses Portfolios, und `CR.1` fuehrt fuer sie eine
# vollstaendige Reihe — beides ist noetig, damit die Fixture etwas belegt.
DATA_INDICATOR = "CR.1"
DATA_COUNTRY = "CHE"


def record() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    recorded_at = datetime.now(UTC).strftime("%Y-%m-%d")
    entries: list[dict] = []

    def write(name: str, payload: object, url: str, rule: str) -> None:
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        (FIXTURES / name).write_text(text, encoding="utf-8")
        entries.append(
            {
                "name": name,
                "url": url,
                "rule": rule,
                "bytes": len(text.encode("utf-8")),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
        )
        print(f"ok  {name:<30} {len(text.encode('utf-8')):>8} B")

    with httpx.Client(timeout=120.0, follow_redirects=True) as c:

        def get(path: str, **params: object) -> object:
            r = c.get(f"{UNESCO_BASE_URL}{path}", params=params or None)
            r.raise_for_status()
            return r.json()

        # -- 0) Der Vertrag ueber die Vertraege: die eigene OpenAPI der Quelle -
        #
        # Sie steht unter `openapi/schema.json` — nicht unter den ueblichen
        # Namen, `/openapi.json` und `/swagger.json` sind 404. Sie ist der
        # Grund, aus dem die Parameternamen jetzt belegt und nicht geraten
        # sind: Der Jahresfilter heisst `start`/`end`, und `theme` steht dort
        # ueberhaupt nicht.
        schema = get("/openapi/schema.json")
        params_by_path = {
            path: sorted(p["name"] for p in op.get("parameters", []) if p.get("in") == "query")
            for path, ops in schema.get("paths", {}).items()
            for op in ops.values()
        }
        data_params = params_by_path.get("/api/public/data/indicators", [])
        def_params = params_by_path.get("/api/public/definitions/indicators", [])
        if "start" not in data_params or "end" not in data_params:
            raise SystemExit(
                f"Der Jahresfilter heisst nicht mehr `start`/`end`, sondern: "
                f"{data_params}. Der Aufrufer gehoert nachgezogen."
            )
        if "theme" in def_params:
            raise SystemExit(
                "`/definitions/indicators` kennt jetzt `theme` — dann gehoert "
                "der Filter wieder an die Quelle statt in den Client."
            )
        write(
            "uis_openapi_query_params.json",
            params_by_path,
            f"{UNESCO_BASE_URL}/openapi/schema.json",
            "nur die Query-Parameter je Pfad, aus der OpenAPI der Quelle. Das "
            "ist der Vertrag, an dem `start`/`end` haengen: Gesendet wurde "
            "`startYear`/`endYear`, und weil unbekannte Parameter mit HTTP 200 "
            "durchfallen, sah der nicht angewandte Filter aus wie ein "
            "angewandter",
        )

        # -- 1) Der Vertrag: welche Indikatoren die Quelle fuehrt -------------
        defs = get("/definitions/indicators")
        codes = {d["indicatorCode"] for d in defs}
        missing = sorted(k for k in UNESCO_EDUCATION_INDICATORS if k not in codes)
        if missing:
            raise SystemExit(
                f"Die lokale Tabelle fuehrt {len(missing)} IDs, die es in der "
                f"Quelle nicht gibt: {missing}. Das gehoert behoben, nicht "
                "aufgezeichnet — eine erfundene ID sieht aus wie eine Antwort."
            )
        # Vollstaendig waeren 1.9 MB. Behalten wird jede ID, die der Server
        # anbietet — plus ein Rest, damit die Suche etwas zu filtern hat.
        # Ausgewaehlt wird nach VERWENDUNG, nicht nach Position: «die ersten
        # N» haetten von 5063 Eintraegen keinen der angebotenen getroffen.
        offered = [d for d in defs if d["indicatorCode"] in UNESCO_EDUCATION_INDICATORS]
        others = [d for d in defs if d["indicatorCode"] not in UNESCO_EDUCATION_INDICATORS][:8]
        write(
            "uis_definitions_indicators.json",
            offered + others,
            f"{UNESCO_BASE_URL}/definitions/indicators",
            f"alle {len(offered)} Indikatoren, die der Server anbietet, plus "
            f"{len(others)} weitere (von {len(defs)}). Nach Verwendung "
            "ausgewaehlt, nicht nach Position — «die ersten N» haetten keinen "
            "der angebotenen enthalten und damit den Befund verdeckt",
        )

        # -- 1b) KONTROLLE: filtert `theme` ueberhaupt? -----------------------
        #
        # Ohne die erfundene dritte Zeile belegt der Vergleich nichts: Dass
        # `theme=EDUCATION` alle Zeilen liefert, koennte auch heissen, dass
        # fast alles EDUCATION ist. Erst `theme=bogus-theme` mit derselben
        # Zahl zeigt, dass der Parameter gar nicht gelesen wird.
        census = {}
        for label in ("EDUCATION", "CULTURE", "bogus-theme-den-es-nicht-gibt"):
            got = get("/definitions/indicators", theme=label)
            census[label] = len(got)
        census["ohne Parameter"] = len(defs)
        by_theme: dict[str, int] = {}
        for d in defs:
            by_theme[d.get("theme", "?")] = by_theme.get(d.get("theme", "?"), 0) + 1
        if len(set(census.values())) != 1:
            raise SystemExit(
                f"`theme` filtert jetzt doch: {census}. Dann gehoert der lokale Filter zurueck an die Quelle."
            )
        write(
            "uis_indicator_themes.json",
            {"antwortgroesse_je_theme_parameter": census, "tatsaechlich_je_theme": by_theme},
            f"{UNESCO_BASE_URL}/definitions/indicators?theme=…",
            "die KONTROLLE zum `theme`-Filter. Drei Werte, darunter ein "
            "erfundener, liefern dieselbe Zeilenzahl wie gar kein Parameter — "
            "der Filter wird nicht gelesen. Daneben die echte Verteilung aus "
            "dem Feld `theme` der Zeilen selbst, gegen die jetzt lokal "
            "gefiltert wird",
        )

        # -- 2) Laender und Regionen -----------------------------------------
        geo = get("/definitions/geounits")
        if any("entityType" in g for g in geo):
            raise SystemExit(
                "Die Quelle fuehrt wieder `entityType` — dann gehoert der Typfilter darauf geprueft, nicht auf `type`."
            )
        geo_types = sorted({g.get("type") for g in geo})
        if set(geo_types) != {"NATIONAL", "REGIONAL"}:
            raise SystemExit(
                f"Die Quelle fuehrt jetzt die Typen {geo_types}. Beschreibung "
                "des Parameters `entity_type` gehoert nachgezogen — sonst "
                "bewirbt sie wieder Werte, die es nicht gibt."
            )
        # Ausgewaehlt so, dass beide Typen UND der Anwendungsfall drin sind.
        # «Die ersten 40» waeren rein alphabetisch und haetten von den 221
        # regionalen Aggregaten keines getroffen — der Typfilter, dessen
        # Fehler hier belegt wird, waere damit unpruefbar geblieben.
        wanted = {"CHE", "DEU", "AUT", "FRA", "WORLD"}
        picked = [g for g in geo if g.get("id") in wanted]
        picked += [g for g in geo if g.get("type") == "NATIONAL" and g.get("id") not in wanted][:20]
        picked += [g for g in geo if g.get("type") == "REGIONAL" and g.get("id") not in wanted][:20]
        write(
            "uis_definitions_geounits.json",
            picked,
            f"{UNESCO_BASE_URL}/definitions/geounits",
            f"{len(picked)} von {len(geo)} Eintraegen: die fuenf, die der "
            "Server namentlich anbietet, plus je 20 NATIONAL und REGIONAL. "
            "Nach Typ ausgewaehlt und nicht nach Position — die Liste ist "
            "alphabetisch, «die ersten 40» haetten kein einziges der 221 "
            "regionalen Aggregate enthalten und den Typfilter unpruefbar "
            "gelassen",
        )

        # -- 3) Die Datenantwort — der Umschlag ist der Befund ----------------
        data = get("/data/indicators", indicator=DATA_INDICATOR, geoUnit=DATA_COUNTRY)
        if "records" not in data:
            raise SystemExit(
                f"Die Datenantwort fuehrt kein `records` mehr, sondern {sorted(data)}. Der Leser gehoert geprueft."
            )
        if not data["records"]:
            raise SystemExit(
                f"{DATA_INDICATOR}/{DATA_COUNTRY} liefert keine Zeilen mehr — "
                "dann belegt die Fixture nicht mehr, dass hier Daten kommen, "
                "und der Befund «immer leer» waere von einer echten Leermenge "
                "nicht zu unterscheiden."
            )
        write(
            "uis_data_records.json",
            data,
            f"{UNESCO_BASE_URL}/data/indicators?indicator={DATA_INDICATOR}&geoUnit={DATA_COUNTRY}",
            f"vollstaendig, {len(data['records'])} Zeilen. Der Umschlag ist der "
            "Gegenstand: Er heisst `records`, und gesucht wurde `observations` "
            "— deshalb kam aus jeder Antwort eine leere Liste",
        )

        # -- 3a) KONTROLLE: greift der Jahresfilter? --------------------------
        #
        # Zwei Anfragen an dieselbe Reihe, einmal mit den Namen, die der Server
        # sendete, einmal mit denen aus der OpenAPI. Der Unterschied IST der
        # Befund — eine der beiden Zeilen allein zeigte ihn nicht.
        wrong = get(
            "/data/indicators",
            indicator=DATA_INDICATOR,
            geoUnit=DATA_COUNTRY,
            startYear=2015,
            endYear=2018,
        )
        right = get(
            "/data/indicators",
            indicator=DATA_INDICATOR,
            geoUnit=DATA_COUNTRY,
            start=2015,
            end=2018,
        )
        wrong_years = sorted({r["year"] for r in wrong["records"]})
        right_years = sorted({r["year"] for r in right["records"]})
        if right_years != [2015, 2016, 2017, 2018]:
            raise SystemExit(
                f"`start`/`end` liefern {right_years}, nicht 2015–2018 — dann "
                "traegt der Befund ueber den Jahresfilter nicht mehr."
            )
        if wrong_years == right_years:
            raise SystemExit(
                "`startYear`/`endYear` filtern jetzt genauso — dann ist der "
                "Befund ueberholt und diese Kontrolle sinnlos."
            )
        write(
            "uis_data_year_filter.json",
            {
                "startYear_endYear": {"jahre": wrong_years, "zeilen": len(wrong["records"])},
                "start_end": {"jahre": right_years, "zeilen": len(right["records"])},
            },
            f"{UNESCO_BASE_URL}/data/indicators?indicator={DATA_INDICATOR}&geoUnit={DATA_COUNTRY}&start=2015&end=2018",
            "dieselbe Reihe zweimal, einmal mit den gesendeten Parameternamen "
            "und einmal mit den deklarierten. `startYear`/`endYear` liefern "
            "die volle Reihe, `start`/`end` die vier verlangten Jahre. Nur "
            "das Paar belegt den Befund: Eine einzelne Antwort mit 14 Zeilen "
            "sieht nach reichlich Daten aus, nicht nach einem ignorierten "
            "Filter",
        )

        # -- 3b) Eine echte Leermenge — der Gegenfall ------------------------
        #
        # Ohne sie liesse sich «immer leer» nicht von «hier gibt es wirklich
        # nichts» unterscheiden, und genau diese Unterscheidung ist der Befund.
        empty = get("/data/indicators", indicator="10", geoUnit=DATA_COUNTRY)
        if empty.get("records"):
            raise SystemExit(
                "Der Gegenfall liefert jetzt Zeilen — dann trennt die Fixture "
                "die echte Leermenge nicht mehr vom Formfehler. Anderen "
                "Indikator waehlen."
            )
        write(
            "uis_data_empty.json",
            empty,
            f"{UNESCO_BASE_URL}/data/indicators?indicator=10&geoUnit={DATA_COUNTRY}",
            "eine ECHTE Leermenge: `records` ist da und leer. Der Gegenfall zum "
            "Befund — ohne ihn liesse sich «der Leser findet nie etwas» nicht "
            "von «hier gibt es nichts» unterscheiden",
        )

        # -- 3c) KONTROLLE: der erfundene Ländercode --------------------------
        #
        # Das ist der Gegenfall zu 3b, und er ist der wichtigere. Beide
        # Antworten haben HTTP 200 und leeres `records`; unterscheidbar sind
        # sie nur an `hints`. Ohne diese Zeile hier waere «keine Daten» und
        # «diesen Code gibt es nicht» in der Fixture dasselbe.
        unknown = get("/data/indicators", indicator=DATA_INDICATOR, geoUnit="XXX")
        if not unknown.get("hints"):
            raise SystemExit(
                "Ein erfundener Ländercode liefert keinen `hints`-Eintrag mehr "
                "— dann laesst sich ein Tippfehler nicht mehr von einer echten "
                "Leermenge trennen, und der Leser gehoert neu gebaut."
            )
        if unknown["records"]:
            raise SystemExit("Der erfundene Ländercode liefert jetzt Zeilen. Neu messen.")
        write(
            "uis_data_unknown_geounit.json",
            unknown,
            f"{UNESCO_BASE_URL}/data/indicators?indicator={DATA_INDICATOR}&geoUnit=XXX",
            "die KONTROLLE zu `uis_data_empty.json`: ein erfundener "
            "Ländercode. HTTP 200, leeres `records` — und ein `hints`-Eintrag, "
            "der den Grund im Klartext nennt. Beide Antworten sehen ohne "
            "`hints` gleich aus, und genau daraus wurde aus einem Tippfehler "
            "die Aussage «für dieses Land gibt es keine Daten»",
        )

        # -- 4) Datenbankversionen -------------------------------------------
        versions = get("/versions")
        write(
            "uis_versions.json",
            versions,
            f"{UNESCO_BASE_URL}/versions",
            f"vollstaendig, {len(versions)} Versionen — der einzige Pfad, den "
            "der Server von Anfang an richtig gebaut hat",
        )

    _write_provenance(recorded_at, entries)
    print(f"\nPROVENANCE.md geschrieben, Aufzeichnungsdatum {recorded_at}")
    return 0


def _write_provenance(recorded_at: str, entries: list[dict]) -> None:
    lines = [
        "# Herkunft der Fixtures",
        "",
        "**Erzeugt von `scripts/record_fixtures.py`. Nicht von Hand pflegen.**",
        "",
        f"Aufgezeichnet am **{recorded_at}** von `api.uis.unesco.org`.",
        "",
        "Ohne Datum ist «aufgezeichnet» nach zwei Jahren von «ausgedacht» nicht",
        "mehr zu unterscheiden — die Datei sieht gleich aus.",
        "",
        "## `uis_definitions_indicators.json` ist der Vertrag",
        "",
        "Die lokale Indikatorentabelle des Servers wird gegen diese",
        "Aufzeichnung gehalten. Am 2026-08-08 gab es **12 der 22 IDs** darin",
        "nicht — und weil der API-Pfad ebenfalls 404 gab, war diese Tabelle",
        "die einzige Liste, die ein Nutzer je zu sehen bekam.",
        "",
        "## Zwei Datenantworten, und beide werden gebraucht",
        "",
        "`uis_data_records.json` traegt Zeilen, `uis_data_empty.json` ist eine",
        "echte Leermenge. Erst zusammen trennen sie den Befund («der Leser",
        "findet nie etwas») von einer Aussage der Quelle («hier gibt es",
        "nichts»). Eine Fixture mit nur einem der beiden Faelle liesse den",
        "Fehler wieder durch.",
        "",
        "**Es sind Ausschnitte, keine Vollabzuege.** Die Auswahlregel steht je",
        "Datei dabei. Wo nach Verwendung ausgewaehlt wurde und nicht nach",
        "Position, steht auch das dort — «die ersten N» haetten bei 5063",
        "Indikatoren keinen der angebotenen getroffen.",
        "",
    ]
    for e in entries:
        lines += [
            f"## `{e['name']}`",
            "",
            f"- **Quelle:** `{e['url']}`",
            f"- **Aufgezeichnet:** {recorded_at}",
            f"- **Auswahl:** {e['rule']}",
            f"- **Groesse:** {e['bytes']} B",
            f"- **SHA-256:** `{e['sha256']}`",
            "",
        ]
    (FIXTURES / "PROVENANCE.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    try:
        raise SystemExit(record())
    except httpx.HTTPError as exc:
        print(f"FEHLER: Quelle nicht erreichbar: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
