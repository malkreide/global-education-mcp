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
spätere Anhebung hier stillschweigend überstimmen.ignatures.py ci python
scripts/check_version_sync.py ```

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
