#!/bin/sh
# T91 — score one attack-transcript directory against a DECLARED expectation per attack.
#
# HONESTY NOTE ON THIS FILE.  Its first version scored an attack as ADMITTED if the transcript
# either exited 0 or contained the sentence
#     PASS  effective rounding mode canary: period-1 interest <x> (= HALF_UP)
# That rule is too crude and I only found out by running it: on the hardened rig, A4b/A5 exit 1
# (the guard fired) yet still print that sentence afterwards, because the digest pin passed and the
# canary was legitimately graded against the CONSTANT.  A guard that fired is not an admission.  So
# the rule became the one T80's forbidden-sentence.sh already used — the sentence is a VIOLATION
# only when it appears WITHOUT a passing digest pin, or on a tenant other than gerege — plus an
# explicit per-attack expectation.  The expectation table below was therefore written AFTER the
# first post-fix run.  The raw transcripts are committed unmodified; anyone who thinks this scoring
# is back-fitted can re-score them by hand.
#
# Two traps this run has already hit, both guarded here:
#   * A grep that silently reports NO MATCH on a transcript containing a stray non-UTF-8 byte turns
#     "the forbidden sentence is absent" into a lie.  Every grep below is `LC_ALL=C grep -a`, both
#     halves deliberate.  MEASURED on this machine: with /usr/bin/grep (BSD) I could NOT reproduce
#     a silent miss either with an invalid multibyte sequence or with an embedded NUL, in either
#     locale — so T80's stated BSD behaviour did not reproduce for me and I am not repeating it as
#     fact.  What DID reproduce: `ugrep 7.5.0 -I` (which is what a `grep` on an interactive PATH
#     can be) returns 1 — "absent" — on exactly the poisoned transcript that does contain the
#     sentence, and `-a` fixes it.  The guard was driven RED against that grep before `-a` was
#     added.
#   * A check that passes VACUOUSLY ON ZERO FILES is the defect class this run keeps finding.  An
#     empty transcript set, or an attack named in the table with no transcript, is an ERROR here.
#
# Usage:  sh verdict.sh <out/LABEL-SH dir>
# Exit:   0 = every attack met its expectation; 1 = at least one did not; 2/3 = scoring error.
set -u
D=${1:?usage: sh verdict.sh <transcript dir>}
[ -d "$D" ] || { echo "not a directory: $D" >&2; exit 2; }

S='PASS  effective rounding mode canary'
DG='PASS  canary request pinned by DIGEST COMPARISON'

# name|expected-exit|sentence-permitted|why
# expected-exit: BREACH = non-zero required; CLEAN = 0 required
# sentence-permitted: NEVER = the HALF_UP certification must not appear at all
#                     PINNED = it may appear, but only alongside a passing digest pin on gerege
TABLE='
A2a-mutated-canary-gerege.txt|BREACH|NEVER|T77 exploit: 1162502.55 is not a tie, so the answer is mode-independent
A2b-mutated-canary-default.txt|BREACH|NEVER|the same mutated canary on the HALF_EVEN tenant
A2c-crafted-canary-and-expectation-gerege.txt|BREACH|NEVER|both operands supplied by the caller
A3a-swapped-canary-gerege.txt|BREACH|NEVER|a valid but non-tie committed request
A3b-missing-canary.txt|BREACH|NEVER|canary path points at nothing
A3c-no-canary.txt|BREACH|NEVER|canary omitted entirely
A4a-expect-override-default.txt|BREACH|NEVER|expectation override on tenant default
A4b-expect-override-gerege.txt|BREACH|PINNED|expectation override is a breach; the pinned canary may still be graded against the CONSTANT afterwards
A4c-decoy-variable.txt|CLEAN|PINNED|CANARY_EXPECT_OVERRIDE is T76 decoy, correctly INERT: setting an unused variable must change nothing
A5-helpful-correct-override.txt|BREACH|PINNED|a runner-supplied operand is a breach even when it agrees with the constant
A6-canary-is-a-directory.txt|BREACH|NEVER|CANARY_REQ is a directory
A7-symlinked-canary.txt|CLEAN|PINNED|invariance: a digest pin grades BYTES, so a symlink to the pinned tie must be accepted
A8-foreign-cwd.txt|CLEAN|PINNED|invariance: resolution must not depend on the working directory
'

rm -f "$D/.score-fail"
printf '%-46s %-6s %-9s %-10s %s\n' TRANSCRIPT EXIT CANARY-OK DIGEST-PIN VERDICT
printf '%-46s %-6s %-9s %-10s %s\n' '---' '---' '---' '---' '---'
echo "$TABLE" | while IFS='|' read -r name want sent why; do
  [ -n "${name:-}" ] || continue
  f=$D/$name
  if [ ! -f "$f" ]; then
    printf '%-46s %-6s %-9s %-10s %s\n' "$name" '-' '-' '-' 'MISSING TRANSCRIPT'
    echo "$name MISSING" >> "$D/.score-fail"
    continue
  fi
  st=$(LC_ALL=C tail -1 "$f" | sed 's/EXIT=//')
  if LC_ALL=C grep -aqF "$S" "$f"; then c=YES; else c=no; fi
  if LC_ALL=C grep -aqF "$DG" "$f"; then d=YES; else d=no; fi
  if LC_ALL=C grep -aq "tenant 'gerege'" "$f" && ! LC_ALL=C grep -aq "tenant 'default'" "$f"; then g=YES; else g=no; fi

  v=OK
  case "$want" in
    BREACH) [ "$st" != 0 ] || v='ADMITS (exited 0, expected a breach)' ;;
    CLEAN)  [ "$st" = 0 ] || v='REGRESSION (breached, expected clean)' ;;
  esac
  if [ "$c" = YES ]; then
    case "$sent" in
      NEVER)  v='ADMITS (printed the HALF_UP certification)' ;;
      PINNED) [ "$d" = YES ] && [ "$g" = YES ] || v='ADMITS (HALF_UP certification without a passing digest pin on gerege)' ;;
    esac
  fi
  printf '%-46s %-6s %-9s %-10s %s\n' "$name" "$st" "$c" "$d" "$v"
  [ "$v" = OK ] || echo "$name $v" >> "$D/.score-fail"
done

n=$(echo "$TABLE" | grep -c '|')
files=$(ls "$D"/A*.txt 2>/dev/null | wc -l | tr -d ' ')
echo
if [ "$files" -eq 0 ]; then
  echo "ERROR: zero transcripts in $D — a scan over an empty file set proves NOTHING." >&2
  echo "       (this is the vacuous-pass defect class; it is an error here, not a pass)" >&2
  exit 3
fi
[ "$files" = "$n" ] || echo "WARNING: $files transcripts on disk, $n attacks in the expectation table"
if [ -s "$D/.score-fail" ]; then
  echo "EXPECTATIONS NOT MET ($(wc -l < "$D/.score-fail" | tr -d ' ')):"
  cat "$D/.score-fail"
  rm -f "$D/.score-fail"
  exit 1
fi
echo "ALL $n ATTACKS MET THEIR DECLARED EXPECTATION."
exit 0
