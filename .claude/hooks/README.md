# SessionStart-Hook: Klon-Aktualität

`session-start.sh` meldet beim Sessionstart, wie viele Commits der
ausgecheckte Stand hinter `origin/<default-branch>` liegt. Liegt er nicht
zurück, sagt er nichts.

## Grund

Ein veralteter Klon hat am 3.8.2026 **zweimal** eine rote CI erzeugt, deren
Ursache nicht im Diff stand — die fehlenden Commits waren jeweils genau die,
die das Gate einführten, an dem der Branch scheiterte. Man sucht den Fehler
dann in den Dateien, die man selbst geändert hat, und findet dort nichts,
weil dort nichts ist.

Die Prüfung kostet eine Sekunde und ersetzt eine Fehlersuche in den falschen
Dateien.

Sie ist die automatisierte Form dessen, was in `CLAUDE.md` unter «Vor der
Arbeit» ohnehin verlangt wird — mit dem Unterschied, dass sie nicht vergessen
werden kann.

## Anforderungen, in dieser Reihenfolge

### 1. Der Hook blockiert die Session niemals

Das ist die oberste Regel, nicht eine unter mehreren. Ein Hook, der bei
Netzproblemen die Arbeit anhält, wird nach dem zweiten Mal abgeschaltet und
schützt danach gar nichts.

Jeder dieser Fälle geht still durch — Exit 0, keine Ausgabe:

| Fall | Behandlung |
| --- | --- |
| Kein Netz / DNS flattert / Proxy antwortet nicht | `fetch` läuft in den Timeout, Hook endet still |
| Kein Remote `origin` | Vorbedingung schlägt fehl |
| Kein Git-Repo, `git` nicht im `PATH` | Vorbedingung schlägt fehl |
| Repo ohne Commit (unbeborener HEAD) | Vorbedingung schlägt fehl |
| Detached HEAD | wird geprüft und **gemeldet**, mit Kurz-SHA statt Branchname |
| Default-Branch nicht ermittelbar | still raus — lieber keine Meldung als eine falsche |
| Git will nach Zugangsdaten fragen | `GIT_TERMINAL_PROMPT=0`, `GIT_ASKPASS`, `ssh -o BatchMode=yes` |
| `timeout` fehlt (macOS ohne coreutils) | Watchdog aus reinem Shell |
| Irgendein unerwarteter Fehler | `trap 'exit 0' EXIT` |

Deshalb steht in dem Skript ausdrücklich **kein** `set -e` / `set -u`: ein
einzelner fehlschlagender Befehl darf nicht den ganzen Hook mit Fehlerstatus
beenden.

### 2. Kurzes Timeout

`fetch` 5 s, Default-Branch-Abfrage 3 s, Einlesen des Hook-JSON 1 s. Zusätzlich
begrenzt `settings.json` den gesamten Hook auf 15 s.

Nach einem Timeout wird **nicht** weitergerechnet: `FETCH_HEAD` könnte dann
noch von einem früheren Lauf stammen und eine falsche Zahl liefern.

### 3. Ausgabe nur, wenn Commits fehlen

Bei 0 schweigt der Hook. Eine Meldung, die bei jedem Start erscheint, wird
nach einer Woche nicht mehr gelesen.

### 4. Der Default-Branch wird ermittelt, nicht angenommen

Drei Server im Portfolio heissen ihren Standard-Branch `master`
(`openlex-mcp`, `swiss-courts-mcp`, `swisstopo-mcp`). Ein fest verdrahtetes
`main` scheitert dort mit «couldn't find remote ref main» — und genau diese
Annahme hat schon einmal einen Branch 15 Commits alt werden lassen, weil der
Fehler wie ein Netzproblem aussah.

Ermittelt wird in zwei Stufen:

1. `git symbolic-ref refs/remotes/origin/HEAD` — lokal, kostenlos, kein Netz.
2. Fehlt der (viele Klone haben kein `origin/HEAD`):
   `git ls-remote --symref origin HEAD`, mit Timeout.

Kommt aus beiden nichts, endet der Hook still.

## Wann er läuft

Bei `source=startup` und `source=resume`. Bei `compact` und `clear` läuft die
Arbeit bereits — ein Netzaufruf wäre dort nur Lärm.

## Selbst ausführen

```bash
echo '{"source":"startup"}' | .claude/hooks/session-start.sh; echo "exit=$?"
```

Der Exit-Code muss **immer** 0 sein. Ist er es nicht, ist der Hook kaputt,
unabhängig davon was er ausgibt.

## Gegenprobe

Ein Hook, der nie etwas meldet, ist von einem funktionierenden Hook auf einem
aktuellen Klon nicht zu unterscheiden. Wer ihn ändert, weist die Wirkung nach:

```bash
# künstlich veralteten Stand erzeugen und prüfen, dass der Hook ihn meldet
git checkout --detach HEAD~3
echo '{"source":"startup"}' | .claude/hooks/session-start.sh   # muss "3 Commit(s)" melden
git checkout -            # zurück
```

Der erste Entwurf dieses Hooks reichte `git` über eine Shell-Funktion an
`timeout` weiter. `timeout` führt ein Programm aus und kennt keine Funktionen;
der Aufruf scheiterte mit «command not found», der Hook schwieg — und sah
dabei aus wie ein Hook auf einem aktuellen Klon. Genau deshalb ist die
Gegenprobe oben Pflicht und nicht Kür.
