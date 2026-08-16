# CLAUDE.md

## Teil 1 — Portfolio-weite Konventionen

### Vor der Arbeit

Klon-Aktualität prüfen: `git fetch origin main && git rev-list --count HEAD..origin/main`
Ein veralteter Klon erzeugt eine rote CI, deren Ursache nicht im Diff steht.
Am 3.8.2026 zweimal passiert — beide Male fehlten genau die Commits, die
das Gate einführten, an dem der Branch scheiterte.

Gates lokal fahren, mit der GEPINNTEN ruff-Version aus der CI. Eine andere
Version meldet Abweichungen, die niemand verursacht hat.

### Tests

Gegenprobe ist Pflicht. Ein Test, der grün bleibt, wenn man die
Implementierung entfernt, prüft nichts. Jede neue Zusicherung einzeln
neutralisieren und zeigen, dass genau die zugehörigen Tests fallen.

Zwei Fallen, die beide grün blieben:

- Eine Fake-Uhr, die nur beim Schlafen vorrückt, kann eine Zusicherung über
  echte Zeit nicht widerlegen.
- `monkeypatch.setattr(modul.asyncio, "sleep", ...)` greift ins Modul
  `asyncio` selbst und entschärft die Mechanik im ganzen Prozess. Patche
  einen Modul-Alias (`_sleep = asyncio.sleep`), nicht das fremde Modul.

Handgeschriebene Fixtures kodieren die Annahme des Autors und können sie
nicht widerlegen. Mindestens eine aufgezeichnete Antwort pro externem
Endpunkt, mit Aufnahmedatum.

### Wenn etwas rot ist

Roter Live-Test: erst die Quelle abfragen, dann einordnen. Nicht aus der
Fehlermeldung schliessen. Am 3.8.2026 hiess «nicht gefunden» nicht, dass der
Datensatz weg war, sondern dass die Quelle die Schreibweise ihrer Kopfzeile
gewechselt hatte — vier von sechs Datensätzen produktiv kaputt, alle
Unit-Tests grün.

PR ohne jeden Check ist selten ein Repo ohne CI, meistens ein
Merge-Konflikt: GitHub berechnet dafür keinen Merge-Commit und startet nichts.

Ein Codex-Review auf einem PR wird beantwortet oder behoben, nie ignoriert.

---

## Teil 2 — Dieses Repo

**ruff: eine Quelle.** Der Pin `0.16.1` steht in `pyproject.toml` — und
**nicht** mehr als eigener Install-Schritt in der CI.

Der CI-Schritt lief nach dem Install der Abhängigkeiten und überschrieb sie.
Eine Abweichung im Pin konnte deshalb in der CI gar nicht auffallen, sondern
nur lokal — wo niemand sie erwartet. Ein manuelles Nachinstallieren von ruff
vor den Gates ist damit nicht mehr nötig und wäre schädlich: Es würde eine
spätere Anhebung hier stillschweigend überstimmen.
`tests/test_werkzeug_versionen.py` fällt, wenn hier wieder eine Spanne steht
oder ein Workflow eine zweite Version setzt — dieser Absatz kann das nicht,
er ist beim letzten Umschreiben selbst kaputtgegangen.

**Gate-Befehle, wörtlich aus `.github/workflows/ci.yml`** (Python 3.11/3.12/3.13):

```bash
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/ -v -m "not integration"
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
PYTHONPATH=src python scripts/tool_signatures.py ci
python scripts/check_version_sync.py
```

Danach baut der Job `docker` das gehärtete Image und macht einen
Smoke-Test (TCP :8000, uid 10001, read-only-FS).

**Live-Tests: DRIFT-005 ist erfüllt.** `.github/workflows/live-tests.yml`
fährt `pytest tests/ -m integration` planmässig gegen `api.uis.unesco.org`:
cron `23 4 * * 1` plus `workflow_dispatch`, mit Einordnung über
`scripts/classify_live_run.py` und automatischem `upstream`-Issue. Der Marker
heisst hier `integration`, nicht `live`; die PR-CI schliesst ihn weiterhin per
`-m "not integration"` aus, und das ist korrekt, weil der geplante Lauf
existiert.

Hier stand das Gegenteil — «Live-Tests laufen nie», «sie sind faktisch tot» —
und es war einen Tag lang richtig: Die CLAUDE.md entstand am 14.08.2026,
`live-tests.yml` kam am 15.08.2026 dazu (`de682ae`). Ein Befund in Prosa
altert still. (Der Katalog in `audits/*/catalog.json` führt die DRIFT-Familie
noch nicht; die Regel gilt trotzdem.)

Fixtures: `scripts/record_fixtures.py`, Aufnahmedatum in
`tests/fixtures/PROVENANCE.md` (aktuell 2026-08-08). Nicht von Hand pflegen.
