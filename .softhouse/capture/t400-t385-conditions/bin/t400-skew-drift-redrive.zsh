#!/bin/zsh
# ============================================================================
# T400 · RE-DRIVE of T385's F-T385-2 drift pair AFTER the fix.
#
# T385's finding: the z06/z07 rows re-spelled `LOCK_RELEASE_SKEW_SECS * 2 + 60`
# and `LOCK_RELEASE_SKEW_SECS / 2` INLINE, while the fixture gate asserted on its
# own `_SKEW_FAR` / `_SKEW_NEAR`. Two spellings of one expression, so a drift in
# the ROW escaped the gate (`s01`) while a drift in the GATE was caught (`s02`).
#
# T400's fix: the rows now CONSUME `_SKEW_FAR` / `_SKEW_NEAR`. There is one
# spelling, so the drift T385 drove is no longer EXPRESSIBLE — which is what
# `s01` now measures, structurally and then by mutation:
#
#   s00   CONTROL, unmutated                 -> rc 0, the fire STARTS
#   s01s  STRUCTURAL: the z06/z07 row lines must contain no inline
#         `LOCK_RELEASE_SKEW_SECS` at all
#   s01   T385's EXACT s01 mutation, replayed verbatim -> must be a NO-OP: the
#         string it drifted is not in the row any more, so the "mutant" is
#         byte-identical to the subject and starts the fire (rc 0, z06 ok).
#         The drift is not "caught"; it is UNSPELLABLE.
#   s01b  the drift with nowhere left to hide: edit the ONE surviving spelling
#         (`_SKEW_FAR`) -> the gate MUST catch it, rc 78, THRESHOLD, and the
#         wiring must NOT say "this is the READERS"
#   s02   T385's CONTROL, verbatim: drift the gate variable to 0 -> rc 78
#   s03   STATED RESIDUAL, not a regression: point the z06 row at the WRONG
#         variable (`_SKEW_NEAR`). No derivation can catch a wrong-fixture typo;
#         C/G have carried the same residual since T361. Driven so the source
#         comment does not overclaim: rc 2 and the READERS message.
#
# SAFETY. Every case mutates a COPY under /tmp/t400 and runs `--probe` only,
# against a throwaway git repo and a /tmp LOG_DIR. FIRE_SNAPSHOT_OF /
# FIRE_SCRIPT_DIR / FIRE_REPO_SCRIPT / FIRE_NO_SNAPSHOT are unset FIRST — a live
# fire exports them (confirmed again by T400: they were in this worker's own
# environment). No lock is taken, nothing is dispatched, the live wrapper is
# never read as the subject and never written.
# ============================================================================
set -u
unset FIRE_SNAPSHOT_OF FIRE_SCRIPT_DIR FIRE_REPO_SCRIPT FIRE_NO_SNAPSHOT
SUBJ="${1:-/tmp/t400/fixed.sh}"
SUBJ="${SUBJ:A}"
WORK=/tmp/t400/skew; rm -rf "$WORK"; mkdir -p "$WORK/frag" /tmp/t400/logs-sk
LIB=/tmp/t400/lib-worktree-prune.zsh

print -r -- "T400 skew-drift RE-DRIVE (post-fix)"
print -r -- "subject: $SUBJ  sha256=$(shasum -a 256 $SUBJ | awk '{print $1}')"
print -r -- "zsh    : $ZSH_VERSION"
print -r -- ""
print -r -- "--- where the four gate variables occur (executable lines only) ---"
LC_ALL=C grep -n '_SKEW_FAR\|_SKEW_NEAR\|_OLD_AGE\|_NEAR_AGE' "$SUBJ" | LC_ALL=C grep -v ':[[:space:]]*#' | cut -c1-160
print -r -- ""
print -r -- "--- the z06/z07 rows ---"
LC_ALL=C grep -n '^[[:space:]]*_row z0[67] ' "$SUBJ" | cut -c1-240
print -r -- ""

typeset -i CHECKS=0 WRONG=0 VOID=0

_case() {   # $1 id  $2 want_rc  $3 must  $4 mustnot  $5 note   (VOID_OK if want_rc == VOID)
  local id="$1" want="$2" must="$3" mustnot="$4" note="$5"
  CHECKS+=1
  mkdir -p "$WORK/$id"; cp "$LIB" "$WORK/$id/"
  if ! /usr/bin/python3 /tmp/t400/mutate.py "$SUBJ" "$WORK/$id/fire-program.sh" \
       "$WORK/frag/$id.old" "$WORK/frag/$id.new" 2>"$WORK/$id/void.txt"; then
    if [[ "$want" == VOID ]]; then
      printf '%-6s %-40s %s\n' "$id" "ok (VOID as required)" "$note"
      print -r -- "        | $(cat "$WORK/$id/void.txt")"
    else
      VOID+=1; WRONG+=1; print -r -- "$id  VOID(unexpected)  $(cat "$WORK/$id/void.txt")"
    fi
    return
  fi
  if [[ "$want" == VOID ]]; then
    WRONG+=1
    printf '%-6s %-40s %s\n' "$id" "WRONG(mutation still applies)" "$note"
    return
  fi
  chmod +x "$WORK/$id/fire-program.sh"
  local OUT RC
  OUT="$(GEREGE_NBFI_REPO=/tmp/t400/subject LOG_DIR=/tmp/t400/logs-sk \
         /bin/zsh "$WORK/$id/fire-program.sh" --probe 2>&1)"; RC=$?
  local verdict=ok
  (( RC == want )) || verdict="WRONG(rc=$RC want=$want)"
  [[ "$must" == "-" ]] || print -r -- "$OUT" | LC_ALL=C grep -qE "$must" || verdict="WRONG(missing /$must/)"
  [[ "$mustnot" == "-" ]] || ! print -r -- "$OUT" | LC_ALL=C grep -qE "$mustnot" || verdict="WRONG(FORBIDDEN /$mustnot/)"
  [[ "$verdict" == ok ]] || WRONG+=1
  printf '%-6s %-40s rc=%-3d %s\n' "$id" "$verdict" "$RC" "$note"
  print -r -- "$OUT" | LC_ALL=C grep -E 'CONFIGURATION ERROR|FATAL|tally VERIFIED|probe only|z06|z07' \
    | cut -c1-300 | sed 's/^/        | /'
}

# ---- s00 CONTROL: unmutated (a unique line replaced by itself) --------------
printf '%s\n' '  _FIXOK=1' > "$WORK/frag/s00.old"
printf '%s\n' '  _FIXOK=1' > "$WORK/frag/s00.new"
_case s00 0 'tally VERIFIED' 'CONFIGURATION ERROR' 'CONTROL: unmutated -- the fire must START'

# ---- s01s STRUCTURAL: no inline skew arithmetic left in the rows ------------
CHECKS+=1
typeset -i _inline
_inline=$(LC_ALL=C grep -c '^[[:space:]]*_row z0[67] .*LOCK_RELEASE_SKEW_SECS' "$SUBJ")
if (( _inline == 0 )); then
  printf '%-6s %-40s %s\n' s01s "ok" "STRUCTURAL: 0 z06/z07 row lines spell LOCK_RELEASE_SKEW_SECS inline"
else
  WRONG+=1
  printf '%-6s %-40s %s\n' s01s "WRONG($_inline inline spellings)" "F-T385-2 is NOT fixed"
fi

# ---- s01 T385's exact mutation, replayed: must now be a NO-OP ---------------
/usr/bin/python3 - "$SUBJ" "$WORK/frag" <<'PY'
import sys
subj, frag = sys.argv[1], sys.argv[2]
src = open(subj, encoding='utf-8').read()
old = ''
for line in src.split('\n'):
    if line.lstrip().startswith('_row z06 '):
        old = line
        break
assert old, 'no _row z06 line found at all'
new = old.replace('LOCK_RELEASE_SKEW_SECS * 2 + 60', 'LOCK_RELEASE_SKEW_SECS / 2')
# If the fix landed, `new == old` -- the drifted spelling is not in the row.
open(frag + '/s01.old', 'w', encoding='utf-8').write(old + '\n')
open(frag + '/s01.new', 'w', encoding='utf-8').write(new + '\n')
open(frag + '/s01.verdict', 'w', encoding='utf-8').write('NOOP' if new == old else 'DRIFTED')
PY
CHECKS+=1
if [[ "$(cat "$WORK/frag/s01.verdict")" == NOOP ]]; then
  printf '%-6s %-40s %s\n' s01v "ok (T385's s01 is now a NO-OP)" \
    "the string it drifted, 'LOCK_RELEASE_SKEW_SECS * 2 + 60', is not in the z06 row"
else
  WRONG+=1
  printf '%-6s %-40s %s\n' s01v "WRONG(row is STILL driftable)" "F-T385-2 is NOT fixed"
fi
# NOTE the forbidden pattern is the ROW MARK `*** FAIL-OPEN`, not the bare token: the
# self-test's own group headers narrate "Anything else = FAIL-OPEN (P-85 safety)" on every
# healthy run, and matching those would have made this control unfailable in the SHUT
# direction. (Caught by this driver's first run — P-22, and P-84's presence-before-value.)
_case s01 0 'tally VERIFIED' '\*\*\* FAIL-OPEN' \
  "T385's s01 verbatim: byte-identical mutant, so the fire STARTS and z06 is ok"

# ---- s01b the same drift, on the ONE surviving spelling ---------------------
printf '%s\n' '  _SKEW_FAR=$(( LOCK_RELEASE_SKEW_SECS * 2 + 60 ))' > "$WORK/frag/s01b.old"
printf '%s\n' '  _SKEW_FAR=$(( LOCK_RELEASE_SKEW_SECS / 2 ))'      > "$WORK/frag/s01b.new"
_case s01b 78 'CONFIGURATION ERROR' 'this is the READERS' \
  'the drift with nowhere to hide: ONE spelling, so the gate CATCHES it (THRESHOLD, not readers)'

# ---- s02 T385's control, verbatim ------------------------------------------
printf '%s\n' '  _SKEW_FAR=$(( LOCK_RELEASE_SKEW_SECS * 2 + 60 ))' > "$WORK/frag/s02.old"
printf '%s\n' '  _SKEW_FAR=$(( LOCK_RELEASE_SKEW_SECS - LOCK_RELEASE_SKEW_SECS ))' > "$WORK/frag/s02.new"
_case s02 78 'past-skew offset=0' 'this is the READERS' \
  "T385's CONTROL: drift the GATE variable -- still EX_CONFIG 78, the gate is live"

# ---- s03 STATED RESIDUAL: the WRONG variable in the row --------------------
/usr/bin/python3 - "$SUBJ" "$WORK/frag" <<'PY'
import sys
subj, frag = sys.argv[1], sys.argv[2]
src = open(subj, encoding='utf-8').read()
old = [l for l in src.split('\n') if l.lstrip().startswith('_row z06 ')][0]
new = old.replace('_NOW_E + _SKEW_FAR', '_NOW_E + _SKEW_NEAR')
assert new != old, 'z06 does not consume _SKEW_FAR -- the fix is not in this subject'
open(frag + '/s03.old', 'w', encoding='utf-8').write(old + '\n')
open(frag + '/s03.new', 'w', encoding='utf-8').write(new + '\n')
PY
_case s03 2 'this is the READERS' 'CONFIGURATION ERROR' \
  'STATED RESIDUAL: wrong VARIABLE in the row is a typo no derivation can catch (C/G share it)'

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG VOID=$VOID"
if (( WRONG == 0 )); then
  print -r -- "RESULT: PASS -- every case landed where predicted."
  print -r -- "MEANING: s01s + s01 show the ROW-only drift T385 drove is gone by construction;"
  print -r -- "         s01b + s02 show the surviving single spelling is INSIDE the gate;"
  print -r -- "         s00 shows a healthy fire still starts; s03 records what is NOT closed."
else
  print -r -- "RESULT: FAIL"
fi
