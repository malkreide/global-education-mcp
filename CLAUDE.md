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

**ruff: nur in der CI gepinnt (`ruff==0.16.1`), nirgends sonst.**
Es gibt keine `.pre-commit-config.yaml`. `pyproject.toml` `[dev]` fordert
`ruff>=0.5.0` ohne Obergrenze — `pip install -e ".[dev]"` liefert also
irgendeine Version, nicht 0.16.1 (in dieser Umgebung: 0.15.8). Vor dem
Lint-Gate explizit `pip install ruff==0.16.1`.

Gate-Befehle, wörtlich aus `.github/workflows/ci.yml` (Python 3.11/3.12/3.13):

```bash
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/ -v -m "not integration"
pip install ruff==0.16.1
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
PYTHONPATH=src python scripts/tool_signatures.py ci
python scripts/check_version_sync.py
```

Danach baut der Job `docker` das gehärtete Image und macht einen
Smoke-Test (TCP :8000, uid 10001, read-only-FS).

**Befund — Live-Tests laufen nie (DRIFT-005).** Kein Workflow hat einen
cron-Trigger; `ci.yml` läuft nur auf push/PR gegen `main`. Live-Tests sind
ausschliesslich per Marker ausgeschlossen (`-m "not integration"`, Marker
heisst hier `integration`, nicht `live`) und werden von nichts geplant
ausgeführt. Die `@pytest.mark.integration`-Klassen in
`tests/test_source_contract.py` und `tests/test_extended_scenarios.py` sind
die einzigen Tests, die einen Schreibweisen-Wechsel der Quelle bemerken
würden — sie sind faktisch tot. (Der Katalog in `audits/*/catalog.json` führt die
DRIFT-Familie noch nicht; die Regel gilt trotzdem.)

Fixtures: `scripts/record_fixtures.py`, Aufnahmedatum in
`tests/fixtures/PROVENANCE.md` (aktuell 2026-08-08). Nicht von Hand pflegen.
