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
#     halves deliberate.
#
#     *** SETTLED BY T108 (2026-08-21).  BOTH TOKENS ARE LOAD-BEARING, AGAINST TWO DIFFERENT
#     PROGRAMS.  DO NOT REMOVE EITHER. ***
#     On this host the token `grep` names two programs and which one you get depends on where you
#     type it (P-33):
#       * inside a script (`sh x.sh` / `bash x.sh`): /usr/bin/grep — BSD grep 2.6.0-FreeBSD.
#       * typed into the Claude Code Bash tool: a shell function re-exec'ing the `claude` binary
#         with argv[0]=ugrep — ugrep 7.5.0 with `-I` hard-coded.  There is NO ugrep binary on this
#         host; ugrep is embedded in `claude`.  That is why every search for one came back empty.
#     They fail in OPPOSITE ways:
#       * BSD grep goes blind to the rest of ONE LINE, from an invalid multibyte byte rightwards.
#         `LC_ALL=C` fixes it; `-a` does NOT.
#       * ugrep `-I` skips the WHOLE FILE.  `-a` fixes it; `LC_ALL=C` does NOT.
#     [VERIFIED: .softhouse/capture/t108-grep/MATRIX.md §1 and §3.1; out/matrix.tsv — 360 cells,
#     12 silent misses, every one BSD grep in a UTF-8 locale; out/probe-flags.txt §B for ugrep.]
#
#     T80's MEASUREMENT was correct and is exactly reproduced.  Only T80's GENERALISATION — "matches
#     nothing in a FILE" — was wrong: the BSD blindness is per line and directional, never per file.
#     An earlier version of this comment said T80's behaviour "does not reproduce on this host".
#     THAT WAS WRONG, and it was wrong for a reason worth keeping: T91's and T107b's probes put the
#     invalid byte AFTER the match on the same line and ran both arms under LC_ALL=C — the very
#     mitigation under test.  N-of-N green cells refute nothing unless the failing shape is among
#     the N.  T138 re-measured on this host: byte BEFORE the match, `utf8 -qF` -> 1, `utf8 -aqF` ->
#     1, `LC_ALL=C -qF` -> 0.  T107's ugrep limb is likewise no longer [UNVERIFIED]: T108 committed
#     the evidence and retired C-7.
#
#     Independent of both: `LC_ALL=C` also defends against GNU grep on Linux, where a UTF-8 locale
#     genuinely can fail to match across an invalid multibyte sequence.  These scripts run on macOS
#     today and nothing pins that.  [UNVERIFIED on Linux — no Linux host available.]
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

# V-A (T115).  The scoring loop below runs in a PIPELINE SUBSHELL, so a failed row cannot set a
# variable the tail of the script can see; the ONLY channel is this file.  Until T115 it lived in
# $D — the transcript directory — and if $D was not writable EVERY append failed, `[ -s ]` was
# false, and the script printed "ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION" and exited 0 WHILE
# ITS OWN TABLE SHOWED SIX `ADMITS` ROWS ON SCREEN.  Measured by T115 with `chmod a-w` on a copy of
# the real pre-fix transcripts: six admissions visible, verdict "ALL 13", exit 0.  A read-only
# checkout, an export owned by another user or a mounted volume is all it takes; no attacker
# required.  This is T80's F-1 shape — a message that is FALSE at the moment it prints — recurring
# inside the file whose own honesty note is about that class.
#
# Two changes: the channel moves to a directory this script creates and owns, and its writability
# is ASSERTED before any scoring happens.  A guard that cannot record a failure must refuse to run.
FAILDIR=$(mktemp -d "${TMPDIR:-/tmp}/verdict-score.XXXXXX") || {
  echo "ERROR: cannot create a scratch directory for the failure channel — refusing to score." >&2
  exit 3; }
FAILS=$FAILDIR/score-fail
trap 'rm -rf "$FAILDIR"' EXIT
if ! : >> "$FAILS" 2>/dev/null || [ ! -w "$FAILS" ]; then
  echo "ERROR: the failure channel '$FAILS' is not writable — a scorer that cannot RECORD a" >&2
  echo "       failure would report every run as clean.  Refusing to score." >&2
  exit 3
fi
rm -f "$D/.score-fail"          # tidy up the pre-T115 location if an old run left one
printf '%-46s %-6s %-9s %-10s %s\n' TRANSCRIPT EXIT CANARY-OK DIGEST-PIN VERDICT
printf '%-46s %-6s %-9s %-10s %s\n' '---' '---' '---' '---' '---'
echo "$TABLE" | while IFS='|' read -r name want sent why; do
  [ -n "${name:-}" ] || continue
  f=$D/$name
  if [ ! -f "$f" ]; then
    printf '%-46s %-6s %-9s %-10s %s\n' "$name" '-' '-' '-' 'MISSING TRANSCRIPT'
    echo "$name MISSING" >> "$FAILS"
    continue
  fi
  # MF-1 (T115, closing T107's F-1).  Zero FILES was already an error below; zero CONTENT was not.
  # `st` was never validated, and the ten BREACH rows are scored `[ "$st" != 0 ]`, which ANY string
  # satisfies — so ten content-free transcripts scored "ALL 13 ATTACKS MET THEIR DECLARED
  # EXPECTATION", exit 0.  A transcript with no `EXIT=<digits>` last line has no attack body: it is
  # an ERROR, never a pass.  Driven RED against exactly that input by `t115-drive-mf1.sh`.
  #
  # Two tests, deliberately, and the ORDER matters:
  #   (a) the SHAPE of the last line must be exactly `EXIT=<digits>`.  T107b recorded that the
  #       value-only test below still accepts a transcript whose final line is a bare numeral
  #       (e.g. `5`), left the decision to the next worker, and T115 closes it: `5` is not an
  #       EXIT line and a truncation that happens to end in a digit must not read as a status.
  #   (b) the VALUE test as T107 specified it, kept as well.  It is redundant given (a) and that
  #       is the point — this is the file whose own honesty note is about vacuous passes.
  last=$(LC_ALL=C tail -1 "$f")
  st=$(printf '%s\n' "$last" | sed 's/EXIT=//')
  case "$last" in
    EXIT=*) shape=ok ;;
    *)      shape=bad ;;
  esac
  case "$st" in
    ''|*[!0-9]*) shape=bad ;;
  esac
  if [ "$shape" = bad ]; then
    printf '%-46s %-6s %-9s %-10s %s\n' "$name" "-" "-" "-" 'ERROR (no EXIT= line — the transcript has no attack body)'
    echo "$name NO EXIT LINE — ERROR (no EXIT= line; the transcript has no attack body)" >> "$FAILS"
    continue
  fi
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
  [ "$v" = OK ] || echo "$name $v" >> "$FAILS"
done

n=$(echo "$TABLE" | grep -c '|')
files=$(ls "$D"/A*.txt 2>/dev/null | wc -l | tr -d ' ')
echo
if [ "$files" -eq 0 ]; then
  echo "ERROR: zero transcripts in $D — a scan over an empty file set proves NOTHING." >&2
  echo "       (this is the vacuous-pass defect class; it is an error here, not a pass)" >&2
  exit 3
fi
# V-B (T115 found it, T138 ruled it, T151 applied it).  NOTHING IN THE TABLE ASSERTS THE ORACLE
# ANSWERED.  `NEVER` forbids the certification sentence and `PINNED` merely PERMITS it — the whole
# sentence check is gated on `if [ "$c" = YES ]`, so when the oracle is dead and `c=no` the PINNED
# rows assert nothing at all.  The scorer's resistance to a dead oracle rested entirely on `A4c`,
# `A7` and `A8` happening to be `CLEAN` rows: an accident of the data, not a decision.
#
# MEASURED, and T115's version of this hazard was overstated 3x.  T115 wrote that retyping ANY ONE
# of those three rows to `BREACH` creates a scorer that reports clean over an oracle that never
# answered.  It does not: retyping one (`A7`) still exits 1 with two `REGRESSION` rows.  It takes
# ALL THREE — and then 13 dead-oracle transcripts score `ALL 13 ATTACKS MET THEIR DECLARED
# EXPECTATION`, exit 0 [VERIFIED: T138 out/R13-VB.txt; reproduced by t151-drive-vb.sh].
#
# T115 declined to fix it on the grounds that changing the expectation table is a substantive act.
# That reason is sound and it does not apply here: this assertion CHANGES NO ROW.  It converts the
# accident into a decision for nine lines, and it is a no-op on every committed transcript
# directory (20 of 20, exit code identical) while going exit 3 on a dead oracle and exit 3 on the
# all-three-retyped case that scored exit 0.  Driven all three legs by t151-drive-vb.sh.
if ! LC_ALL=C grep -alF "$S" "$D"/A*.txt >/dev/null 2>&1; then
  echo "ERROR: not one transcript contains the rounding-mode certification sentence — the suite" >&2
  echo "       never reached a live oracle.  Scoring it would grade an outage as a clean sweep." >&2
  exit 3
fi
[ "$files" = "$n" ] || echo "WARNING: $files transcripts on disk, $n attacks in the expectation table"
if [ -s "$FAILS" ]; then
  echo "EXPECTATIONS NOT MET ($(wc -l < "$FAILS" | tr -d ' ')):"
  cat "$FAILS"
  exit 1
fi
echo "ALL $n ATTACKS MET THEIR DECLARED EXPECTATION."
exit 0
