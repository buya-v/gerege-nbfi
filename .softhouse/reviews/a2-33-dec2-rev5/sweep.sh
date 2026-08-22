#!/bin/bash
# A2-33 independent claim sweep.
# TARGET: a file, or "REPO" to sweep all tracked content at HEAD.
# Patterns are deliberately NOT right-anchored on inflected stems (T227's 0/9-recall lesson:
# \bexist\b cannot match EXISTING). Every stem is left-anchored or bare.
#
# ============================================================================================
# T238 FAIL-CLOSED REPAIR, 2026-08-22.  READ THIS BEFORE CITING EITHER VERSION.
#
# WHAT WAS WRONG.  The original line 7 read
#     WT=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a5244bad2b6814a39
# and the body was  ( cd "$WT" && git grep ... ) || echo "   (no hits)".
# That worktree was deleted after A2-33 finished.  A re-run therefore printed "(no hits)" for
# all 34 patterns, emitted ZERO hit lines and EXITED 0 -- indistinguishable, to a reader, from
# "I swept and the concept is absent".  A fail-OPEN instrument: it cannot report a positive,
# and its silence corroborates whatever the reader already believed.
#
# WHAT IS **NOT** WRONG, AND MUST NOT BE INFERRED.  That describes a RE-RUN, not A2-33's run.
# A2-33's committed transcript sweep-output-live-population.txt carries 34 patterns, ZERO
# "(no hits)" and 6334 hit lines: the sweep ran, and it found things, while the worktree still
# existed.  **DEC-2 rev 5 and G-11 are UNAFFECTED and are NOT re-opened by this repair.**
#
# WHAT CHANGED.  The corpus root is now resolved RELATIVELY, the failure arm ABORTS instead of
# printing a reassurance, and the instrument CALIBRATES ON A KNOWN POSITIVE (P-72) before it is
# allowed to report any negative.  ALL 34 PATTERNS ARE BYTE-IDENTICAL TO THE ORIGINAL.
# The original file is preserved verbatim, with its sha256, in CORRECTION.md alongside; the
# committed transcripts are untouched (T114/T176).
#
# EXIT CODES: 0 measured | 90 corpus unreachable | 91 corpus empty | 92 calibration missed
#             93 engine error.  "Zero hits" and "could not look" are no longer the same answer.
# ============================================================================================
set -u
MODE="${1:-REPO}"

if [ "$MODE" = "REPO" ]; then
  ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || ROOT=""
  [ -n "$ROOT" ] || { echo "SWEEP ABORT (90): not inside a git work tree; cannot reach a corpus." >&2; exit 90; }
  cd "$ROOT" || { echo "SWEEP ABORT (90): cannot cd into $ROOT" >&2; exit 90; }
  NFILES=$(git ls-files | wc -l | tr -d ' ')
  [ "${NFILES:-0}" -gt 0 ] 2>/dev/null || { echo "SWEEP ABORT (91): $ROOT tracks ZERO files. A sweep over nothing proves nothing (P-35)." >&2; exit 91; }
  echo "SWEEP ROOT   : $ROOT"
  echo "SWEEP COMMIT : $(git rev-parse HEAD)"
  echo "SWEEP CORPUS : $NFILES tracked files"
  echo "SWEEP ENGINE : git grep -n -I -i -E   [git $(git --version | awk '{print $3}')]"
  echo "SWEEP ENGINE NB: this engine does NOT implement \\b \\d \\s \\w. A2-33 audited every"
  echo "               pattern below for those escapes and none uses one. Do not add one."
else
  [ -f "$MODE" ] || { echo "SWEEP ABORT (90): target file does not exist: $MODE" >&2; exit 90; }
  [ -s "$MODE" ] || { echo "SWEEP ABORT (91): target file is EMPTY: $MODE" >&2; exit 91; }
  NFILES=1
  echo "SWEEP ROOT   : (single file) $MODE"
  echo "SWEEP ENGINE : /usr/bin/grep -n -i -E   [$(/usr/bin/grep --version 2>&1 | head -1)]"
fi

# ---- P-72 CALIBRATION.  Prove the instrument can find something BEFORE it may report nothing.
# The known positive is this file's own name, which is present in every corpus this script can
# legitimately be pointed at.  A MISS aborts: a sweep that cannot find a string it is standing
# on has unknown, possibly zero, recall, and none of its negatives is interpretable.
CAL_RE='a2-33'
if [ "$MODE" = "REPO" ]; then
  CAL_N=$(git grep -c -I -i -E "$CAL_RE" -- .softhouse/reviews/a2-33-dec2-rev5 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
else
  # NB: no `|| echo 0` here. That idiom is the very fail-open shape this repair removes, and
  # T238's linter flagged it in this line on its first run. `|| CAL_N=0` assigns without printing.
  CAL_N=$(/usr/bin/grep -c -i -E 'PATTERN|pass|the' "$MODE" 2>/dev/null); [ -n "$CAL_N" ] || CAL_N=0
fi
if [ "${CAL_N:-0}" -lt 1 ]; then
  echo "SWEEP ABORT (92): CALIBRATION MISSED. '$CAL_RE' matched 0 times where it is KNOWN present." >&2
  echo "                  The engine, the pattern language or the corpus is broken." >&2
  echo "                  NO NEGATIVE FROM THIS RUN IS INTERPRETABLE (P-72)." >&2
  exit 92
fi
echo "SWEEP CALIBRATE+: PASS — known positive '$CAL_RE' matched $CAL_N time(s)"

# ---- ANTI-CALIBRATION.  Prove the engine does not FABRICATE, not only that it can find.
# The driver measured at main 8275f8b that `git grep -E '\bmain\b'` MATCHED the line `bmainb`.
# So the literal-backslash-b defect is not merely RECALL LOSS, which is all P-53 and P-12
# record -- git grep -E can return a hit THAT IS NOT THERE. A positive-only calibration passes
# happily on a fabricating engine, so "I got hits, so my rig works" is not a valid calibration.
# The token is ASSEMBLED AT RUN TIME so that the literal string never appears in this file.
# A known-negative that is written out verbatim would match its own source and abort every run --
# the anti-calibration has to be absent from the corpus it is testing, including from itself.
ANTI_RE="$(printf 'zzq%snoSUCHtokenzzq' 'T238')"
if [ "$MODE" = "REPO" ]; then
  ANTI_N=$(git grep -c -I -i -E "$ANTI_RE" -- . 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
else
  ANTI_N=$(/usr/bin/grep -c -i -E "$ANTI_RE" "$MODE" 2>/dev/null); [ -n "$ANTI_N" ] || ANTI_N=0
fi
if [ "${ANTI_N:-0}" -gt 0 ]; then
  echo "SWEEP ABORT (92): ANTI-CALIBRATION FAILED. '$ANTI_RE' matched $ANTI_N time(s)" >&2
  echo "                  where it is KNOWN to be ABSENT. The engine is FABRICATING matches;" >&2
  echo "                  every POSITIVE from this run is suspect, not only its negatives." >&2
  exit 92
fi
echo "SWEEP CALIBRATE-: PASS — known negative matched 0 times (engine is not fabricating)"
echo

NPAT=0
NHIT=0

run() {  # run <label> <regex>
  local label="$1" re="$2" out rc
  NPAT=$((NPAT+1))
  echo "########## PATTERN $label :: $re"
  if [ "$MODE" = "REPO" ]; then
    out=$(git grep -n -I -i -E "$re" -- . 2>&1); rc=$?
  else
    out=$(/usr/bin/grep -n -i -E "$re" "$MODE" 2>&1); rc=$?
  fi
  case "$rc" in
    0) printf '%s\n' "$out"; NHIT=$((NHIT + $(printf '%s\n' "$out" | wc -l | tr -d ' '))) ;;
    1) echo "   MEASURED ZERO (engine ran over $NFILES file(s) and matched nothing)" ;;
    *) echo "SWEEP ABORT (93): engine ERROR exit=$rc on $label :: $re" >&2
       printf '%s\n' "$out" >&2
       exit 93 ;;
  esac
  echo
}

trailer() {
  local rc=$?
  echo "=================================================================="
  if [ "$rc" -ne 0 ]; then
    echo "SWEEP-RESULT: ABORTED rc=$rc patterns_completed=$NPAT hit_lines=$NHIT"
    echo "SWEEP-RESULT: THIS RUN MEASURED NOTHING USABLE. Do not read it as a negative."
    return
  fi
  if [ "$NPAT" -eq 0 ]; then
    echo "SWEEP-RESULT: ABORTED rc=91 zero patterns ran; there is nothing to report."
    exit 91
  fi
  echo "SWEEP-RESULT: commit=$(git rev-parse --short HEAD 2>/dev/null || echo n/a) corpus_files=$NFILES patterns=$NPAT hit_lines=$NHIT calibration=PASS"
}
trap trailer EXIT

# ---- F-2 CLASS: "the number of detection classes with an empty population is THREE" ----
run F2-01 'three of (its |the |them|these )?(seven|7|four|4)'
run F2-02 '(^|[^0-9])3 of (7|4|seven|four)'
run F2-03 'three of them'
run F2-04 'empty population'
run F2-05 'inspect.{0,40}empty'
run F2-06 'numerator'
run F2-07 'denominator'
run F2-08 'i4.?builder'
run F2-09 'nil.?coverage'
run F2-10 'detection class'
run F2-11 'not established'
run F2-12 'i.?4 arm'
run F2-13 'three .{0,80}(class|detect)'
run F2-14 '(57|43|25) ?%|57 per ?cent|43 per ?cent'
run F2-15 '(three|3|four|4) declared'
run F2-16 'declared detection'
run F2-17 'the (three|four)( that| classes| of them)?'
run F2-18 'i3.?sql.?balance'
run F2-19 'i4.?dml'
run F2-20 'opaque.?sql'
run F2-21 'selftest only|--selftest. only|self-test and .{0,20}nothing'
run F2-22 'guard is (25|43|57)|% live|per ?cent live'

# ---- F-1 CLASS: "the guard head DROPS the CANNOT-CATCH block on the pass path" ----
run F1-01 'fu.?t208.?1|t208.?1'
run F1-02 'cannot.?catch.{0,100}(drop|swallow|filter|omit|strip|suppress|absent|not present|never|does not|doesn.t)'
run F1-03 '(drop|swallow|filter|omit|strip|suppress|absent|never|does not arrive|doesn.t arrive).{0,100}cannot.?catch'
run F1-04 'head drop'
run F1-05 'pass.?path|pass path'
run F1-06 'not present anywhere'
run F1-07 'absent from every'
run F1-08 'never reach'
run F1-09 'does not arrive|do not arrive|doesn.t arrive'
run F1-10 'only .{0,12}\^?census'
run F1-11 'condensed copy|redundant restatement|8.line condensation|eight.line condensation'
run F1-12 'green run'
