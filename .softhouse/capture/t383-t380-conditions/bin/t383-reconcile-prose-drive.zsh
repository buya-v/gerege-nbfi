#!/bin/zsh
# =====================================================================================
# T383 — F-T380-3: the reconciliation diagnostic's EXPLANATORY CLAUSE was the undercount
# sentence unconditionally, and it is false in the other direction.
#
# T380 measured both directions land here and both refuse correctly (x06: a group guarded
# off, ROWS=38 vs a census of 45; x04: two rows written on ONE line, ROWS=45 vs a census of
# 44). The NUMBERS printed were right in both. Only the prose was wrong in one: *"Rows exist
# that neither ran nor announced themselves skipped, so the tally understates what was left
# ungraded"* is true of x06 and false of x04, where the tally OVERstates and nothing was left
# ungraded. Cosmetic in the sense that the refusal is unaffected — and not cosmetic at all to
# the operator who reads the sentence at 06:00 and goes looking for a disabled group that
# does not exist.
#
# Both directions are driven here against the SHIPPED file. Expectations are POST-FIX.
#
# NO MONEY IS COMPUTED ON THIS PATH.
# =====================================================================================
emulate -L zsh
set -u

SUBJ="${SUBJ:-/tmp/t383-subject/.softhouse/bin/fire-program.sh}"
SUBJ_BIN="${SUBJ:h}"
SUBJ_REPO="${SUBJ_REPO:-${SUBJ:h:h:h}}"
WORK="${WORK:-/tmp/t383-prose}"
/bin/rm -rf "$WORK"; /bin/mkdir -p "$WORK"

unset FIRE_SNAPSHOT_OF FIRE_REPO_SCRIPT

typeset -i CHECKS=0 WRONG=0 VOID=0

run() {   # <id> <want_rc> <want_regex> <forbid_regex|-> [<find> <repl>]...
  local id="$1" want_rc="$2" want_re="$3" forbid_re="$4"; shift 4
  local f="$WORK/$id.sh" out find repl; local -i rc n
  /bin/cp "$SUBJ" "$f"
  while (( $# >= 2 )); do
    find="$1"; repl="$2"; shift 2
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

print -r -- "=== T383 reconciliation-prose drive — subject $SUBJ"
print -r -- "=== sha256: $(/usr/bin/shasum -a 256 "$SUBJ" | cut -c1-64)"
print -r -- ""

# ---- p01 UNDERCOUNT (T380's x06): group Z's 7 rows are DECLARED but guarded off, so they
#      neither run nor announce a skip. ROWS=38 + SKIPPED=0 vs a census of 45. The UNDERSTATES
#      sentence is the correct one here. ------------------------------------------------------
run p01 2 'ROWS=38 \+ SKIPPED=0 = 38, but 45 rows are DECLARED in .*\. Rows are DECLARED that neither ran nor announced themselves skipped, so the tally UNDERSTATES' \
          'OVERSTATES' \
  '  _row z01 HELD' \
  '  if false; then
  _row z01 HELD' \
  '  print -r -- "--- E. T361 C4 (F-T361-4). FOREIGN host.' \
  '  fi
  print -r -- "--- E. T361 C4 (F-T361-4). FOREIGN host.'

# ---- p02 OVERCOUNT (T380's x04): two rows on ONE line. All 45 execute, but the line-based
#      census can only see 44. ROWS=45 vs a census of 44 — the tally OVERSTATES relative to the
#      population and NOTHING was left ungraded. This is the sentence that was inverted. ------
run p02 2 'ROWS=45 \+ SKIPPED=0 = 45, but 44 rows are DECLARED in .*\. MORE rows ran than the census can find declared, so the tally OVERSTATES' \
          'UNDERSTATES' \
  '  _arow h02 86400      "1970-01-02T00:00:00Z" OPEN "one day past the epoch: grades the *86400 scaling and the day term"
' \
  '  _arow h02 86400      "1970-01-02T00:00:00Z" OPEN "one day past the epoch"; '

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG VOID=$VOID"
if (( WRONG == 0 && VOID == 0 )); then print -r -- "RESULT: PASS"; exit 0; fi
print -r -- "RESULT: FAIL"; exit 1
