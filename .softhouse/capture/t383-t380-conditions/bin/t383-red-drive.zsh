#!/bin/zsh
# =====================================================================================
# T383 — drives F-T380-1 (the `tail -1` FAIL-OPEN in the fatal pre-fire wiring of
# `.softhouse/bin/fire-program.sh`) in all three multiplicity directions, and then tries
# to DEFEAT the fix five ways.
#
# WHAT F-T380-1 IS. The wiring selects the self-test's summary with
#   `... | grep -E '^ROWS=…$' | tail -1`
# so when TWO summary lines are emitted the LAST one wins. T380 MEASURED the consequence
# (`t380-review-t377/out/06-x09-tail1-hazard.txt`): the fire log carries BOTH
# `FAIL_OPEN=1` AND `FAIL_OPEN=0`, and THE FIRE STARTS. A real failing summary is silenced
# by a later clean-looking one, in the control that gates every fire start.
#
# `head -1` IS NOT THE FIX — it only moves which line wins (case m04 below is the mirror
# image, and would fail open under `head -1` exactly as m03 does under `tail -1`).
#
# THE FIX GRADED HERE IS *REFUSE ON MULTIPLICITY*: exactly one summary line is admissible.
#   zero    -> REFUSE (P-84 presence-before-value, `.softhouse/patterns.md:2813`)
#   one     -> behave exactly as before
#   two+    -> REFUSE, because the control can no longer say which run it describes
# That is the same "an ambiguous population is a SELECTOR failure" move the empty-census
# check beside it already makes.
#
# EXPECTATIONS BELOW ARE POST-FIX. Run against the SHIPPED (pre-fix) file this driver is
# RED on m03/m05/m07/m08 and reports the wrong REASON on m04; run against the fixed file it
# is green. That difference IS the evidence — see `out/01-red-shipped.txt` vs
# `out/02-green-fixed.txt`.
#
# METHOD (borrowed from T380's `t380-attack-census.zsh`, whose shape works): each case copies
# the SUBJECT wrapper, applies exact-once literal replacements (anything but exactly one
# occurrence scores VOID and is never a pass), and drives `--probe` at the copy. `--probe`
# exits before the lock is read and before anything is dispatched, and `GEREGE_NBFI_REPO`
# points at a scratch repo, so no real lock, repo or fire is touched.
#
# NO MONEY IS COMPUTED ON THIS PATH. Every number here is an exit status or a line count.
# =====================================================================================
emulate -L zsh
set -u

SUBJ="${SUBJ:-/tmp/t383-subject/.softhouse/bin/fire-program.sh}"
SUBJ_BIN="${SUBJ:h}"
SUBJ_REPO="${SUBJ_REPO:-/tmp/t383-subject}"
WORK="${WORK:-/tmp/t383-drive}"
/bin/rm -rf "$WORK"; /bin/mkdir -p "$WORK"

# This driver runs INSIDE a live fire, which exports FIRE_SNAPSHOT_OF / FIRE_REPO_SCRIPT.
# Inheriting them makes every child believe it is already a snapshot of the REAL repo copy.
unset FIRE_SNAPSHOT_OF FIRE_REPO_SCRIPT

typeset -i CHECKS=0 WRONG=0 VOID=0

# The summary printer, the tally initialiser and the self-test's own exit — the three anchors
# every case below mutates. Spelled once here so a drift in the file VOIDs the run loudly
# instead of silently matching nothing.
PRINTER='  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"'
TALLY0='  typeset -i _n=0 _open=0 _shut=0 _skipped=0'
TALLY1='  typeset -i _n=0 _open=1 _shut=0 _skipped=0'
OWNEXIT='  (( _open == 0 && _shut == 0 )) || exit 1'
NOEXIT='  : # T383: the self-tests own exit removed, so only the WIRING can refuse'

run() {   # <id> <want_rc> <want_regex> <forbid_regex|-> [<find> <repl>]...
  local id="$1" want_rc="$2" want_re="$3" forbid_re="$4"; shift 4
  local f="$WORK/$id.sh" out find repl; local -i rc n
  /bin/cp "$SUBJ" "$f"

  while (( $# >= 2 )); do
    find="$1"; repl="$2"; shift 2
    [[ -n "$find" ]] || continue
    n=$(/usr/bin/python3 -c '
import sys
src=open(sys.argv[1],encoding="utf-8").read()
sys.stdout.write(str(src.count(sys.argv[2])))' "$f" "$find")
    (( n == 1 )) || { print -r -- "$id  *** VOID  anchor occurs $n time(s), not exactly once"; (( VOID+=1, CHECKS+=1 )); return; }
    /usr/bin/python3 -c '
import sys
p,a,b=sys.argv[1],sys.argv[2],sys.argv[3]
src=open(p,encoding="utf-8").read()
open(p,"w",encoding="utf-8").write(src.replace(a,b,1))' "$f" "$find" "$repl"
  done
  /bin/chmod +x "$f"

  out="$(FIRE_NO_SNAPSHOT=1 FIRE_SCRIPT_DIR="$SUBJ_BIN" GEREGE_NBFI_REPO="$SUBJ_REPO" \
         LOG_DIR="$WORK/logs" /bin/zsh "$f" --probe 2>&1)"; rc=$?
  print -r -- "$out" > "$WORK/$id.out"

  local verdict="ok"
  (( rc == want_rc )) || verdict="*** WRONG rc=$rc want=$want_rc"
  if [[ "$verdict" == ok ]]; then
    print -r -- "$out" | LC_ALL=C grep -qE "$want_re" || verdict="*** WRONG missing /$want_re/"
  fi
  if [[ "$verdict" == ok && "$forbid_re" != "-" ]]; then
    print -r -- "$out" | LC_ALL=C grep -qE "$forbid_re" && verdict="*** WRONG forbidden /$forbid_re/ present"
  fi
  [[ "$verdict" == ok ]] || (( WRONG+=1 ))
  (( CHECKS+=1 ))
  print -r -- "$id  $verdict  rc=$rc"
}

print -r -- "=== T383 multiplicity drive — subject $SUBJ"
print -r -- "=== sha256: $(/usr/bin/shasum -a 256 "$SUBJ" | cut -c1-64)"
print -r -- "=== expectations are POST-FIX; RED against the shipped file is the finding"
print -r -- ""

# ============================ THE THREE DIRECTIONS ===================================

# ---- m00 CONTROL, EXACTLY ONE, CLEAN: the fire must still START. A control that refuses
#      everything is not a control. -------------------------------------------------------
run m00 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' \
          'TALLY LINE' '' ''

# ---- m01 ZERO LINES: the summary printer emits something else entirely. P-84 presence
#      before value — refuse rather than parse an absent line into a comfortable 0. --------
run m01 2 'printed NO TALLY LINE' 'tally VERIFIED' \
  "$PRINTER" '  print -r -- "the tally is none of your business"'

# ---- m02 EXACTLY ONE, FAILING: unchanged behaviour. The single line reports FAIL_OPEN=1
#      while the self-test itself exits 0, so only the wiring's second reading can refuse. -
run m02 2 'FAILED \(rc=0, FAIL_OPEN=1' 'tally VERIFIED' \
  "$TALLY0" "$TALLY1"  "$OWNEXIT" "$NOEXIT"

# ---- m03 TWO LINES, FAILING FIRST THEN CLEAN. **THE EXACT INPUT T380 MEASURED THE FIRE
#      STARTING ON.** Under `tail -1` the impostor wins: log carries FAIL_OPEN=1 AND
#      FAIL_OPEN=0, rc 0, fire starts. Post-fix this must REFUSE ON MULTIPLICITY. ----------
run m03 2 'printed 2 TALLY LINES' 'tally VERIFIED' \
  "$TALLY0" "$TALLY1"  "$OWNEXIT" "$NOEXIT" \
  "$PRINTER" "$PRINTER
  print -r -- \"ROWS=\$_n FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=\$_skipped\""

# ---- m04 TWO LINES, CLEAN FIRST THEN FAILING — the MIRROR IMAGE, and the reason `head -1`
#      is not the fix. `tail -1` happens to land on the failing line here and refuses for
#      the RIGHT-LOOKING but WRONG reason; `head -1` would prefer the clean impostor and the
#      fire would start. Post-fix both are moot: multiplicity refuses either ordering, and
#      the reader-fault message must be ABSENT because no reader has been graded. ----------
run m04 2 'printed 2 TALLY LINES' 'this is the READERS' \
  "$TALLY0" "$TALLY1"  "$OWNEXIT" "$NOEXIT" \
  "$PRINTER" '  print -r -- "ROWS=$_n FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=$_skipped"
'"$PRINTER"

# ---- m05 TWO IDENTICAL CLEAN LINES: no line is WRONG, and the fire starts today. This is
#      multiplicity in its purest form — the wiring cannot say which run either line
#      describes, so it must not certify either. --------------------------------------------
run m05 2 'printed 2 TALLY LINES' 'tally VERIFIED' \
  "$PRINTER" "$PRINTER
$PRINTER"

# ============================ FIVE ATTEMPTS TO DEFEAT THE FIX ========================

# ---- m06a TRAILING WHITESPACE on the impostor. The selector is anchored `…SKIPPED=[0-9]+$`,
#      so `… SKIPPED=0 ` does NOT match: the population stays at ONE and the REAL failing
#      line still governs. Must refuse as a READER failure, NOT as multiplicity. -----------
run m06a 2 'FAILED \(rc=0, FAIL_OPEN=1' 'TALLY LINES' \
  "$TALLY0" "$TALLY1"  "$OWNEXIT" "$NOEXIT" \
  "$PRINTER" "$PRINTER
  print -r -- \"ROWS=\$_n FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=\$_skipped \""

# ---- m06b TRAILING WHITESPACE on the ONLY summary. Then NOTHING matches, the population is
#      zero, and P-84 refuses. Direction SHUT: a summary the wiring cannot recognise is an
#      absent summary. -----------------------------------------------------------------------
run m06b 2 'printed NO TALLY LINE' 'tally VERIFIED' \
  "$PRINTER" '  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped "'

# ---- m07 A SUMMARY LINE THAT IS DATA INSIDE A QUOTED STRING, printed earlier in the run.
#      It reaches stdout as a whole line, so it IS a summary as far as any reader can tell —
#      and that is precisely the ambiguity multiplicity refuses. -----------------------------
run m07 2 'printed 2 TALLY LINES' 'tally VERIFIED' \
  '  print -r -- "self-test: file=${0:A}"' \
  '  print -r -- "ROWS=99 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0"
  print -r -- "self-test: file=${0:A}"'

# ---- m08 A SUMMARY ON **STDERR**, not stdout. The wiring captures with `2>&1`, so a stderr
#      impostor is in the population exactly like a stdout one. Anyone reasoning "the summary
#      is a stdout contract" is wrong about this wiring. -------------------------------------
run m08 2 'printed 2 TALLY LINES' 'tally VERIFIED' \
  "$PRINTER" "$PRINTER
  print -u2 -r -- \"ROWS=\$_n FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0\""

# ---- m09a SPLIT ACROSS A WRITE/PIPE BOUNDARY: the summary emitted as TWO writes with no
#      newline between them. It is still ONE line on the far side of the pipe, so the count
#      must stay 1 and the fire must START — no false refusal from a fragmented writer. -----
run m09a 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' 'TALLY LINE' \
  "$PRINTER" '  print -rn -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT="
  print -r -- "$_shut SKIPPED=$_skipped"'

# ---- m09b SPLIT ACROSS A **LINE** BOUNDARY: a newline lands mid-summary. Now NEITHER half
#      matches the anchored selector, the population is zero, and P-84 refuses. SHUT. -------
run m09b 2 'printed NO TALLY LINE' 'tally VERIFIED' \
  "$PRINTER" '  print -r -- "ROWS=$_n FAIL_OPEN=$_open"
  print -r -- "FAIL_SHUT=$_shut SKIPPED=$_skipped"'

# ---- m10 A LINE THAT MERELY *CONTAINS* THE SUMMARY TOKEN as a substring, on both sides:
#      a prefixed narrative line and a suffixed one. Neither is anchored, so neither joins the
#      population, the count stays 1, and the fire must START. This is the false-multiplicity
#      case — a fix that refused here would refuse the wiring's own `lockselftest| ` echo. ---
run m10 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' 'TALLY LINE' \
  "$PRINTER" '  print -r -- "note: the previous run said ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0"
'"$PRINTER"'
  print -r -- "ROWS=45 FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=0 (historical, not this run)"'

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG VOID=$VOID"
if (( WRONG == 0 && VOID == 0 )); then print -r -- "RESULT: PASS"; exit 0; fi
print -r -- "RESULT: FAIL"; exit 1
