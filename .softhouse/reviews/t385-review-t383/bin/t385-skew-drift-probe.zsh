#!/bin/zsh
# ============================================================================
# T385 · F-T385-2 -- the z06/z07 offsets ARE re-spelled, so the gate and the rows
#                    CAN drift apart. T383's source comment says they cannot.
#
# The claim under test, at fire-program.sh:748-749 (T383's file):
#   "The z06/z07 offsets are named here rather than re-spelled, so the tests
#    below and the rows that consume them cannot drift apart."
#
# But `_SKEW_FAR` / `_SKEW_NEAR` occur ONLY in the gate (753-754, 759-761) and in
# its message (763). The z06/z07 rows at 883-884 still spell
# `LOCK_RELEASE_SKEW_SECS * 2 + 60` and `LOCK_RELEASE_SKEW_SECS / 2` INLINE.
# They are two independent spellings of one expression -- the P-80 shape.
#
#   s01  drift the ROW's spelling, leave the gate's alone
#        -> the gate must NOT notice, the self-test must go FAIL-SHUT, and the
#           wiring must blame "the READERS" -- exactly the fault class the gate
#           was built to close.
#   s02  CONTROL: drift the GATE's own variable
#        -> the gate MUST notice, exit 78, THRESHOLD.
#   s00  CONTROL: unmutated -> rc 0, the fire starts.
#
# --probe only, copies under /tmp, throwaway repo, no lock, nothing dispatched.
# ============================================================================
set -u
unset FIRE_SNAPSHOT_OF FIRE_SCRIPT_DIR FIRE_REPO_SCRIPT FIRE_NO_SNAPSHOT
SUBJ=/tmp/t385/fixed.sh
WORK=/tmp/t385/skew; rm -rf "$WORK"; mkdir -p "$WORK/frag"; mkdir -p /tmp/t385/logs-sk
print -r -- "T385 skew-drift probe"
print -r -- "subject: $SUBJ  sha256=$(shasum -a 256 $SUBJ | awk '{print $1}')"
print -r -- ""
print -r -- "--- where the four gate variables actually occur ---"
LC_ALL=C grep -n '_SKEW_FAR\|_SKEW_NEAR\|_OLD_AGE\|_NEAR_AGE' "$SUBJ" | cut -c1-120
print -r -- ""
print -r -- "--- the z06/z07 rows, which re-spell the offsets ---"
LC_ALL=C grep -n '_row z0[67] ' "$SUBJ" | cut -c1-200
print -r -- ""

typeset -i CHECKS=0 WRONG=0 VOID=0
_case() {
  local id="$1" want="$2" must="$3" mustnot="$4" note="$5"
  CHECKS+=1
  mkdir -p "$WORK/$id"; cp /tmp/t385/lib-worktree-prune.zsh "$WORK/$id/"
  if ! /usr/bin/python3 /tmp/t385/mutate.py "$SUBJ" "$WORK/$id/fire-program.sh" \
       "$WORK/frag/$id.old" "$WORK/frag/$id.new" 2>"$WORK/$id/void.txt"; then
    VOID+=1; print -r -- "$id  VOID  $(cat "$WORK/$id/void.txt")"; return
  fi
  chmod +x "$WORK/$id/fire-program.sh"
  local OUT RC
  OUT="$(GEREGE_NBFI_REPO=/tmp/t385/subject LOG_DIR=/tmp/t385/logs-sk \
         /bin/zsh "$WORK/$id/fire-program.sh" --probe 2>&1)"; RC=$?
  local verdict=ok
  (( RC == want )) || verdict="WRONG(rc=$RC want=$want)"
  [[ "$must" == "-" ]] || print -r -- "$OUT" | LC_ALL=C grep -qE "$must" || verdict="WRONG(missing /$must/)"
  [[ "$mustnot" == "-" ]] || ! print -r -- "$OUT" | LC_ALL=C grep -qE "$mustnot" || verdict="WRONG(FORBIDDEN /$mustnot/)"
  [[ "$verdict" == ok ]] || WRONG+=1
  printf '%-5s %-40s rc=%-3d %s\n' "$id" "$verdict" "$RC" "$note"
  print -r -- "$OUT" | LC_ALL=C grep -E 'CONFIGURATION ERROR|FATAL|tally VERIFIED|probe only|z06|z07' \
    | cut -c1-300 | sed 's/^/        | /'
}

# s00 -- unmutated control (a no-op replacement of a unique comment line)
printf '%s\n' '  _FIXOK=1' > "$WORK/frag/s00.old"
printf '%s\n' '  _FIXOK=1' > "$WORK/frag/s00.new"
# a no-op mutation would be rejected by mutate.py? no: it only requires uniqueness.
_case s00 0 'tally VERIFIED' 'CONFIGURATION ERROR' 'CONTROL: unmutated -- the fire must start'

# s01 -- drift the ROW's own spelling of the z06 offset. The gate is untouched.
/usr/bin/python3 - <<'PY'
src=open('/tmp/t385/fixed.sh',encoding='utf-8').read()
import re
for line in src.split('\n'):
    if line.lstrip().startswith('_row z06 '):
        old=line
        break
new=old.replace('LOCK_RELEASE_SKEW_SECS * 2 + 60', 'LOCK_RELEASE_SKEW_SECS / 2')
assert new!=old
open('/tmp/t385/skew/frag/s01.old','w',encoding='utf-8').write(old+'\n')
open('/tmp/t385/skew/frag/s01.new','w',encoding='utf-8').write(new+'\n')
PY
_case s01 2 'this is the READERS' 'CONFIGURATION ERROR' \
  'DRIFT the ROW spelling: the gate must FAIL to notice (that is the finding)'

# s02 -- CONTROL: drift the GATE's own variable instead.
printf '%s\n' '  _SKEW_FAR=$(( LOCK_RELEASE_SKEW_SECS * 2 + 60 ))' > "$WORK/frag/s02.old"
printf '%s\n' '  _SKEW_FAR=$(( LOCK_RELEASE_SKEW_SECS - LOCK_RELEASE_SKEW_SECS ))' > "$WORK/frag/s02.new"
_case s02 78 'past-skew offset=0' 'this is the READERS' \
  'CONTROL: drift the GATE variable -- the gate MUST notice, EX_CONFIG 78'

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG VOID=$VOID"
if (( WRONG == 0 && VOID == 0 )); then
  print -r -- "RESULT: PASS -- every case landed where predicted."
  print -r -- "MEANING: s01 confirms the row spelling is OUTSIDE the gate's reach, so the"
  print -r -- "         comment's 'cannot drift apart' is FALSE. s02 confirms the gate is"
  print -r -- "         live and reacts to its own variable, so s01 is not a dead gate."
else
  print -r -- "RESULT: FAIL"
fi
