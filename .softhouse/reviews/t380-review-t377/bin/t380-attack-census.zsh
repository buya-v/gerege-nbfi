#!/bin/zsh
# =====================================================================================
# T380 — INDEPENDENT attack on T377's DERIVED row-census floor in `.softhouse/bin/fire-program.sh`.
#
# WHY THIS EXISTS AND WHY IT IS NOT T377's DRIVER RE-RUN. T377 shipped `red-drive.zsh`, which
# I did re-run; this file is a SECOND, independently written driver whose cases are chosen to
# FOOL the census rather than to demonstrate it. A grep-based self-census is a derivation, and
# a derivation is only as good as the ways it can be lied to. Every case below is a specific
# lie: a row that is DATA (inside a string), two rows on ONE line, a row split ACROSS lines, a
# row that is DECLARED but unreachable, a skip that is announced, and a SECOND summary line
# that the wiring's `tail -1` would prefer over the real one.
#
# METHOD. Each case copies the SUBJECT wrapper, applies an exact string replacement whose
# anchor must occur EXACTLY ONCE (anything else scores VOID and is never a pass), and drives
# `--probe` at the copy. `FIRE_NO_SNAPSHOT=1` so `$FIRE_SELF` is deterministically the mutated
# copy; the T301 snapshot path is measured separately and NOT suppressed there.
#
# NO MONEY IS COMPUTED ON THIS PATH. Every number below is an exit status or a count of rows.
# =====================================================================================
emulate -L zsh
set -u

SUBJ="${SUBJ:-/tmp/t380-subject/.softhouse/bin/fire-program.sh}"
SUBJ_BIN="${SUBJ:h}"
SUBJ_REPO="${SUBJ_REPO:-/tmp/t380-subject}"
WORK="${WORK:-/tmp/t380-attack}"
/bin/rm -rf "$WORK"; /bin/mkdir -p "$WORK"

typeset -i CHECKS=0 WRONG=0 VOID=0

# run <id> <want_rc> <want_regex> <forbid_regex|-> <find> <repl> [<find2> <repl2> ...]
#   <find>/<repl> may be empty strings for the control. `<repl>` of the literal `@DELETE@`
#   deletes every line matching <find> as an EXTENDED regex (used for the 45-row deletion).
#   Further find/repl PAIRS may follow; each is applied in turn and each must occur EXACTLY
#   ONCE. Two mutations are needed whenever a case must open a block and close it, or must
#   change a counter AND the line that would have exited on it.
run() {
  local id="$1" want_rc="$2" want_re="$3" forbid_re="$4"; shift 4
  local f="$WORK/$id.sh" out find repl; local -i rc n
  /bin/cp "$SUBJ" "$f"

  while (( $# >= 2 )); do
    find="$1"; repl="$2"; shift 2
    [[ -n "$find" ]] || continue
    if [[ "$repl" == "@DELETE@" ]]; then
      n=$(LC_ALL=C grep -cE "$find" "$f")
      (( n > 0 )) || { print -r -- "$id  *** VOID  regex '$find' matched 0 lines"; (( VOID+=1, CHECKS+=1 )); return; }
      LC_ALL=C grep -vE "$find" "$f" > "$f.new" && /bin/mv "$f.new" "$f"
    else
      # exact-once literal anchor
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
    fi
  done
  /bin/chmod +x "$f"

  out="$(FIRE_NO_SNAPSHOT=1 FIRE_SCRIPT_DIR="$SUBJ_BIN" GEREGE_NBFI_REPO="$SUBJ_REPO" \
         /bin/zsh "$f" --probe 2>&1)"; rc=$?
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

print -r -- "=== T380 census attack — subject $SUBJ"
print -r -- "=== sha256: $(/usr/bin/shasum -a 256 "$SUBJ" | cut -c1-64)"
print -r -- ""

# ---- x00 CONTROL: unmutated. The wiring must announce the reconciliation it performed. -----
run x00 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' - '' ''

# ---- x01 THE F-T368-2 CASE: delete every row invocation. Was rc 0 + fire starts. -----------
run x01 2 'POPULATION IS EMPTY' 'tally VERIFIED' '^[[:space:]]*_(row|arow)[[:space:]]' '@DELETE@'

# ---- x02 P-84: delete the summary print. Presence must be read before value. ---------------
run x02 2 'printed NO TALLY LINE' 'tally VERIFIED' \
  'print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"' \
  'print -r -- "the tally is none of your business"'

# ---- x03 A ROW THAT IS DATA, NOT CODE: a `_row ` line inside a QUOTED STRING. The census is
#          source text, so it counts 46 while 45 execute. Direction must be SHUT. ------------
run x03 2 'does not reconcile' 'tally VERIFIED' \
  '  print -r -- "--- H. T361 C5, the half the body rows cannot reach' \
  '  print -r -- "
_row h99 HELD not-a-row this line is DATA inside a string
--- H. T361 C5, the half the body rows cannot reach'

# ---- x04 TWO ROWS ON ONE LINE: census counts lines, so it reads 44 while 45 execute. -------
run x04 2 'does not reconcile' 'tally VERIFIED' \
  '  _arow h02 86400      "1970-01-02T00:00:00Z" OPEN "one day past the epoch: grades the *86400 scaling and the day term"
' \
  '  _arow h02 86400      "1970-01-02T00:00:00Z" OPEN "one day past the epoch"; '

# ---- x05 A ROW SPELLED ACROSS A LINE CONTINUATION. One logical row, and the FIRST physical
#          line still matches, so the census must read 45 and the fire must START. -----------
run x05 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' 'does not reconcile' \
  '  _arow h01 0          "1970-01-01T00:00:00Z" OPEN "the epoch anchor' \
  '  _arow h01 0 \
         "1970-01-01T00:00:00Z" OPEN "the epoch anchor'

# ---- x06 DECLARED BUT NEVER REACHED: group Z (7 rows) guarded off, neither run nor announced
#          skipped. The FLOOR ALONE WOULD MISS THIS — 38 of 45 still looks plausible. --------
run x06 2 'does not reconcile — ROWS=38 \+ SKIPPED=0 = 38, but 45 rows are DECLARED' 'tally VERIFIED' \
  '  _row z01 HELD' \
  '  if false; then
  _row z01 HELD' \
  '  print -r -- "--- E. T361 C4 (F-T361-4). FOREIGN host.' \
  '  fi
  print -r -- "--- E. T361 C4 (F-T361-4). FOREIGN host.'

# ---- x07 THE SKIP PATH ACTUALLY RECONCILES. Force the reaped-pid probe to fail, so groups B
#          and E skip: 41 executed + 4 announced = 45. This must NOT refuse — it is the arm
#          that never fires on this host, so nobody has ever seen it reconcile. -------------
run x07 0 'tally VERIFIED by the wiring — 41 executed \+ 4 skipped = 45 declared' 'does not reconcile' \
  '    kill -0 $_cand 2>/dev/null || { _DEAD=$_cand; break; }' \
  '    kill -0 $_cand 2>/dev/null || { : ; }'

# ---- x08 INDEPENDENCE: the self-test reports FAIL_OPEN=1 but EXITS 0, because its own
#          `|| exit 1` was deleted. The wiring must read the TALLY, not only `rc`. -----------
run x08 2 'FAILED \(rc=0, FAIL_OPEN=1' 'tally VERIFIED' \
  '  typeset -i _n=0 _open=0 _shut=0 _skipped=0' \
  '  typeset -i _n=0 _open=1 _shut=0 _skipped=0' \
  '  (( _open == 0 && _shut == 0 )) || exit 1' \
  '  : # T380 x08: the self-tests own exit removed'

# ---- x09 THE `tail -1` HAZARD, measured rather than assumed: a self-test that prints a REAL
#          failing summary AND THEN a second, clean-looking one. `tail -1` prefers the last
#          match. Recorded as a measurement — the expectation below is what T380 OBSERVED, and
#          the finding is argued in the handoff rather than scored here. ---------------------
run x09 0 'tally VERIFIED' - \
  '  typeset -i _n=0 _open=0 _shut=0 _skipped=0' \
  '  typeset -i _n=0 _open=1 _shut=0 _skipped=0' \
  '  (( _open == 0 && _shut == 0 )) || exit 1' \
  '  : # T380 x09: the self-tests own exit removed' \
  '  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"' \
  '  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"
  print -r -- "ROWS=$_n FAIL_OPEN=0 FAIL_SHUT=0 SKIPPED=$_skipped"'

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG VOID=$VOID"
if (( WRONG == 0 && VOID == 0 )); then print -r -- "RESULT: PASS"; exit 0; fi
print -r -- "RESULT: FAIL"; exit 1
