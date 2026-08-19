#!/bin/bash
# ---------------------------------------------------------------------------
# SessionStart-Hook: Klon-Aktualitaet
#
# Meldet beim Sessionstart, wie viele Commits der ausgecheckte Stand hinter
# origin/<default-branch> liegt. Bei 0 schweigt er.
#
# GRUND: Ein veralteter Klon hat am 3.8.2026 zweimal eine rote CI erzeugt,
# deren Ursache nicht im Diff stand -- die fehlenden Commits waren jeweils
# genau die, die das Gate einfuehrten, an dem der Branch scheiterte. Die
# Pruefung kostet eine Sekunde und ersetzt eine Fehlersuche in den falschen
# Dateien. Ausfuehrlich in .claude/hooks/README.md.
#
# OBERSTE REGEL: Dieser Hook blockiert die Session NIEMALS. Kein Netz, kein
# Remote, detached HEAD, flatterndes DNS, fehlendes `timeout` -- jeder dieser
# Faelle geht still durch (exit 0, keine Ausgabe). Ein Hook, der bei
# Netzproblemen die Arbeit anhaelt, wird nach dem zweiten Mal abgeschaltet
# und schuetzt danach gar nichts.
#
# Deshalb ausdruecklich KEIN `set -e` / `set -u`: ein einzelner fehlschlagender
# Befehl darf nicht den ganzen Hook mit Fehlerstatus beenden.
# ---------------------------------------------------------------------------

# Was auch immer unten passiert -- der Hook endet mit 0.
trap 'exit 0' EXIT

FETCH_TIMEOUT=5      # Sekunden fuer das fetch
LSREMOTE_TIMEOUT=3   # Sekunden fuer die Default-Branch-Abfrage
STDIN_TIMEOUT=1      # Sekunden fuer das Einlesen des Hook-JSON

# --- Timeout-Wrapper -------------------------------------------------------
# `timeout` fehlt auf manchem macOS (dort `gtimeout`, und auch das nur mit
# coreutils). Fehlt beides, uebernimmt ein Watchdog aus reinem Shell -- der
# Hook darf nicht daran scheitern, dass ein Hilfsprogramm fehlt.
if command -v timeout >/dev/null 2>&1; then
  run_limited() { timeout "$@"; }
elif command -v gtimeout >/dev/null 2>&1; then
  run_limited() { gtimeout "$@"; }
else
  run_limited() {
    secs="$1"; shift
    "$@" &
    _pid=$!
    ( sleep "$secs"; kill -9 "$_pid" >/dev/null 2>&1 ) >/dev/null 2>&1 &
    _watchdog=$!
    wait "$_pid" >/dev/null 2>&1
    _rc=$?
    kill "$_watchdog" >/dev/null 2>&1
    return "$_rc"
  }
fi

# --- Hook-JSON von stdin ---------------------------------------------------
# Mit hartem Limit: ein `cat` an einer offenen Pipe wuerde sonst unbegrenzt
# warten -- genau die Blockade, die dieser Hook nie verursachen darf.
hook_input=$(run_limited "$STDIN_TIMEOUT" cat 2>/dev/null)

# Bei `compact` und `clear` laeuft die Arbeit schon -- dann ist ein
# Netzaufruf nur Laerm. Nur beim echten Start und beim Resume pruefen.
case "$hook_input" in
  *'"source"'*'"compact"'*|*'"source"'*'"clear"'*) exit 0 ;;
esac

# --- Vorbedingungen --------------------------------------------------------
command -v git >/dev/null 2>&1 || exit 0

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# Kein Remote `origin` -> nichts zu vergleichen.
git remote get-url origin >/dev/null 2>&1 || exit 0

# Unbeborener HEAD (frisches Repo ohne Commit) -> nichts zu vergleichen.
git rev-parse --verify --quiet HEAD >/dev/null 2>&1 || exit 0

# Git darf unter keinen Umstaenden interaktiv nach Zugangsdaten fragen -- ein
# Prompt haengt entweder bis zum Timeout oder, bei offenem Terminal, ewig.
# Als `env`-Praefix, nicht als Shell-Funktion: `timeout` fuehrt ein Programm
# aus und kennt keine Funktionen -- ein `timeout 5 meine_funktion` scheitert
# mit "command not found", und der Hook waere stumm immer still.
GIT_NET=(env
  GIT_TERMINAL_PROMPT=0
  GIT_ASKPASS=/bin/true
  SSH_ASKPASS=/bin/true
  SSH_ASKPASS_REQUIRE=never
  GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes -o ConnectTimeout=3}"
  git -c credential.helper=)

# --- Default-Branch ermitteln, NICHT `main` annehmen -----------------------
# Mindestens ein Repo im Portfolio nutzt `master`; genau diese Annahme hat
# schon einmal einen Branch 15 Commits alt werden lassen.
#
# 1. Den Remote fragen -- das ist die autoritative Antwort.
default_branch=$(run_limited "$LSREMOTE_TIMEOUT" "${GIT_NET[@]}" \
  ls-remote --symref origin HEAD 2>/dev/null \
  | sed -n 's|^ref: refs/heads/\([^[:space:]]*\).*|\1|p' | head -n 1)

# 2. Kein Netz? Dann der lokal aufgezeichnete origin/HEAD. Der wird beim Klonen
#    einmal gesetzt und danach nie wieder -- nach einem Umbenennen des
#    Default-Branch zeigt er auf den alten. Deshalb nur als Rueckfallebene:
#    lieber die veraltete Antwort als gar keine Pruefung, aber nie vor der
#    frischen. Ein stiller Vergleich gegen den falschen Branch waere genau
#    der Fehler, den dieser Hook verhindern soll.
if [ -z "$default_branch" ]; then
  default_branch=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
  default_branch=${default_branch#origin/}
fi

# Nicht ermittelbar -> still raus. Lieber keine Meldung als eine falsche.
[ -n "$default_branch" ] || exit 0

# --- Fetch mit kurzem Timeout ---------------------------------------------
# Nur bei sauberem Erfolg weiterrechnen: nach einem Abbruch koennte FETCH_HEAD
# noch von einem frueheren Lauf stammen und eine falsche Zahl liefern.
run_limited "$FETCH_TIMEOUT" "${GIT_NET[@]}" \
  fetch --quiet origin "$default_branch" >/dev/null 2>&1 || exit 0

fetched=$(git rev-parse --verify --quiet FETCH_HEAD 2>/dev/null)
[ -n "$fetched" ] || exit 0

behind=$(git rev-list --count "HEAD..$fetched" 2>/dev/null)

# Keine Zahl -> still raus.
case "$behind" in
  ''|*[!0-9]*) exit 0 ;;
esac

# --- Ausgabe nur, wenn tatsaechlich Commits fehlen -------------------------
[ "$behind" -gt 0 ] || exit 0

if head_ref=$(git symbolic-ref --quiet --short HEAD 2>/dev/null); then
  here="$head_ref"
else
  here="detached HEAD $(git rev-parse --short HEAD 2>/dev/null)"
fi

printf '%s\n' \
  "Klon-Aktualitaet: '${here}' liegt ${behind} Commit(s) hinter origin/${default_branch}." \
  "" \
  "  git merge origin/${default_branch}    # oder rebase, je nach Konvention" \
  "" \
  "Ein veralteter Klon erzeugt eine rote CI, deren Ursache nicht im Diff steht:" \
  "die fehlenden Commits sind typischerweise genau die, die das Gate einfuehren," \
  "an dem der Branch dann scheitert."

exit 0
