#!/bin/zsh
# T302 — DRIVE foreign_live_session_in_repo() using ITS OWN BYTES, cut out of
# fire-program.sh by line range and eval'd, so nothing is paraphrased. Exactly ONE edit
# is made and it is declared: the absolute token `/bin/ps` is rebound to a shim, because
# the function calls ps by absolute path and PATH cannot reach it.
#
# THE SUBJECT IS A REAL LIVE PROCESS. The function does `kill -0` on every candidate and
# silently skips anything it cannot signal, so a fabricated pid would be discarded for
# the wrong reason and the drive would prove nothing. So each shimmed table row carries
# the pid of a genuinely live `claude` on this host, discovered at run time. Only the
# COMMAND TEXT and the reported cwd vary between cases.
#
# CASE 0  control, real /bin/ps, real lsof  -- shows the cut function works unmodified
# CASE 1  the live session's command text has no `claude` basename in f[3]
#         (an install path with a space; equally a `node .../cli.js` wrapper launch)
# CASE 2  a live `claude` whose cwd is the project root, that is NOT this fire
# CASE 3  T288's own measured case: a live `claude` whose cwd is /Users/buv
set -uo pipefail
SRC="${0:A:h}/../../bin/fire-program.sh"
FIRST=$(/usr/bin/grep -n '^foreign_live_session_in_repo() {' "$SRC" | cut -d: -f1)
LAST=$(/usr/bin/awk -v s="$FIRST" 'NR>=s && $0=="}" {print NR; exit}' "$SRC")
print -r -- "cut foreign_live_session_in_repo from fire-program.sh lines $FIRST-$LAST"
BODY=$(/usr/bin/sed -n "${FIRST},${LAST}p" "$SRC")

REPO=/Users/buv/gerege-nbfi
FOREIGN_SESSIONS=""
SB=$(mktemp -d /tmp/t302-probe-XXXXXX)

# --- find a real live claude to use as the subject -------------------------------
LIVE=$(/bin/ps -Ao pid=,command= | /usr/bin/awk '{n=split($2,a,"/"); if(a[n]=="claude"){print $1; exit}}')
if [[ -z "$LIVE" ]]; then
  print -r -- "NO live \`claude\` on this host — this drive needs one as its subject. Aborting."
  exit 1
fi
print -r -- "live subject: pid $LIVE (a real claude on this host)"

mkshim_ps() {   # $1 = dir, $2 = the one subject row
  local d="$1" row="$2"
  mkdir -p "$d"
  { print -r -- '#!/bin/sh'
    print -r -- "cat <<'TBL'"
    print -r -- '    1 Ss   /sbin/launchd'
    print -r -- '  400 Ss   /usr/libexec/logd'
    print -r -- '  900 S    /usr/sbin/cupsd'
    print -r -- ' 4627 S    /bin/zsh /Users/buv/gerege-nbfi/.softhouse/bin/fire-program.sh'
    print -r -- "$row"
    print -r -- 'TBL' ; } > "$d/ps"
  chmod +x "$d/ps"
}
mkshim_lsof() { # $1 = dir, $2 = cwd to report
  local d="$1" c="$2"
  mkdir -p "$d"
  { print -r -- '#!/bin/sh'; print -r -- 'echo p0'; print -r -- 'echo fcwd'
    print -r -- "echo n$c" ; } > "$d/lsof"
  chmod +x "$d/lsof"
}
run_case() {    # $1 = ps binary path ("" = real /bin/ps), $2 = lsof binary path
  local b="$BODY"
  [[ -n "$1" ]] && b="${BODY//\/bin\/ps/$1}"
  LSOF_BIN="$2"
  eval "$b"
  foreign_live_session_in_repo
  return $?
}
verdict() {
  case $1 in
    0) print -r -- "  -> 0 REFUSE: a live foreign session was found" ;;
    1) print -r -- "  -> 1 MAY RECONCILE: 'positively established that nobody is working here'" ;;
    2) print -r -- "  -> 2 REFUSE: could not establish" ;;
  esac
}

print -r -- ""
print -r -- "=== CASE 0 (control): real /bin/ps, real /usr/sbin/lsof, unmodified bytes ==="
run_case "" /usr/sbin/lsof; RC=$?
print -r -- "  evidence: $FOREIGN_SESSIONS"; verdict $RC

mkshim_ps  "$SB/ps1" " $LIVE SN   /Applications/Claude Code/claude -p /softhouse-program"
mkshim_lsof "$SB/ls1" "$REPO"
print -r -- ""
print -r -- "=== CASE 1: the SAME live pid, working in the repo, but f[3] is"
print -r -- "            '/Applications/Claude' — a spaced install path (a 'node .../cli.js'"
print -r -- "            wrapper launch has the identical signature) ==="
run_case "$SB/ps1/ps" "$SB/ls1/lsof"; RC=$?
print -r -- "  evidence: $FOREIGN_SESSIONS"; verdict $RC
(( RC == 1 )) && print -r -- "  FINDING: examined=0 is spelled 'nobody', not 'I could not tell'. The declared"
(( RC == 1 )) && print -r -- "           polarity is violated by a candidate the NAME FILTER never saw."

mkshim_ps  "$SB/ps2" " $LIVE SN   /Users/buv/.local/bin/claude"
mkshim_lsof "$SB/ls2" "$REPO"
print -r -- ""
print -r -- "=== CASE 2: a live claude, idle, cwd = the project root, NOT this fire ==="
run_case "$SB/ps2/ps" "$SB/ls2/lsof"; RC=$?
print -r -- "  evidence: $FOREIGN_SESSIONS"; verdict $RC
(( RC == 0 )) && print -r -- "  FINDING: REFUSED. Nothing here distinguishes an idle interactive session in"
(( RC == 0 )) && print -r -- "           the project root from a fire that is working. CLAUDE.md documents"
(( RC == 0 )) && print -r -- "           '/softhouse' as an interactive entry point, so this cwd is normal."

mkshim_lsof "$SB/ls3" "/Users/buv"
print -r -- ""
print -r -- "=== CASE 3 (control): T288's own measured case, cwd = /Users/buv ==="
run_case "$SB/ps2/ps" "$SB/ls3/lsof"; RC=$?
print -r -- "  evidence: $FOREIGN_SESSIONS"; verdict $RC
(( RC == 1 )) && print -r -- "  The cwd discriminator DOES separate a session elsewhere on the filesystem."
(( RC == 1 )) && print -r -- "  That is the case T288 measured, and it is the only one it measured."
print -r -- ""
print -r -- "sandbox: $SB"
