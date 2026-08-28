#!/usr/bin/env bash
# casualty-sweep.sh -- WHERE I LOOKED for things the T352/T359 oracle movement invalidated.
#
#   bash .softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh
#
# "Not found" is a statement about the SEARCH, never about the world (P-66/P-70). So this
# script IS the statement: it names the population, the engine, the flags and every selector,
# and it prints the hit count beside each one. A reader who doubts the casualty list re-runs
# this and gets a different list if I missed a selector -- which is the point.
#
# ------------------------------------------------------------------------------------------
# T371 REPAIR -- F2 FROM T367'S REVIEW. READ THIS BEFORE TRUSTING ANY ZERO BELOW.
#
# The version T363 shipped DISCARDED `git grep`'s exit status:
#
#     all=$(git grep "$@" -- .softhouse/ 2>/dev/null)          # <-- old :39, rc never read
#
# T367 drove it: a MALFORMED selector (rc 128, the search never ran) and a valid selector with
# GENUINELY NO HITS (rc 1) both printed the identical line `total=0 archived=0 LIVE=0`. That is
# a negative the instrument never measured -- the exact fail-open shape T232 exists to name --
# reappearing inside the artefact written to prevent it. Writing the rule does not immunise you
# against it; only the guard does (P-81).
#
# THE INVARIANT THIS FILE NOW ENFORCES, adopted from T238's `sweeplib.sh`:
#
#     AN INSTRUMENT MUST NOT BE ABLE TO EMIT A NEGATIVE IT DID NOT MEASURE.
#
#   "the engine ran and matched nothing"  and  "the engine never ran"  are DIFFERENT FACTS and
#   they now print differently and exit differently. Two further guards come with it:
#     * a POSITIVE calibration -- prove a known-present string is findable before any zero here
#       is interpretable (P-72);
#     * an ANTI-calibration -- prove a known-absent string returns zero, because `git grep -E`
#       on this host has been measured FABRICATING a hit (T238: `git grep -nE '\bmain\b'` and
#       `git grep -nE 'bmainb'` returned byte-identical output, and it was the decoy line). So
#       "I got hits, therefore my rig works" is NOT a valid calibration.
#
# EXIT CODES -- chosen so a caller can tell the failures apart
#   0  every selector RAN. Hits or measured zeros; both are MEASUREMENTS.
#   2  corpus unusable  -- not in a git work tree, or it tracks zero files (P-35).
#   3  calibration failed -- the engine cannot find a known positive, or fabricates on a known
#      negative. NO negative from this run is interpretable and none should be quoted.
#   4  at least one selector DID NOT RUN. Its "zero" is not a zero.
#
# This instrument still GATES NOTHING -- no caller reads its status, by design; it is evidence,
# not a bar. A LIVE hit is therefore NOT an exit code: the sweep reports candidate casualties, a
# human adjudicates them. What the exit code carries is only whether the sweep is ADMISSIBLE.
#
# ENGINE AND FLAGS, stated because they have bitten this program: `git grep` with `-E` and
# `-F` explicitly per selector; NO `\b` anywhere, because `git grep -E` reads `\b` as a
# LITERAL 'b' on this machine and returns zero SILENTLY (T232's measurement).
#
# ------------------------------------------------------------------------------------------
# T381 REPAIR -- R1..R4 FROM T379'S REVIEW OF THE T371 REPAIR ABOVE.
#
# T379 approved T371 and filed four residual defects. THREE OF THEM ARE THE SAME SHAPE AS THE
# ONE T371 CAME HERE TO FIX, and one of those three was INSIDE T371's fix. Writing the rule
# does not immunise you against it; only a guard that RUNS does (P-81).
#
# WHAT IS AND IS NOT ENFORCED BY THIS REPAIR, said plainly because P-45's rule is "when
# hardening a check, verify the path that actually executes in CI/conformance calls it, not
# merely that a test does". THIS FILE STILL GATES NOTHING -- the paragraph above saying so is
# still true and T381 did not change it. What T381 adds is:
#   * four calibration arms and three refusals that run WHENEVER THIS SCRIPT RUNS, so a reader
#     who quotes a zero from a transcript is quoting a measured one or an explicit refusal;
#   * a RED DRIVE that constructs each defect and proves the refusal fires --
#     `.softhouse/capture/t381-t379-conditions/instruments/t381-red-drives.sh`, transcript in
#     `.softhouse/capture/t381-t379-conditions/out/D-RED-DRIVES.txt`;
#   * and the bar's OWN static readers already cover this file -- `guard_no_fail_open_instruments`
#     lints every tracked .sh in the repository and `guard_dead_path_frontier`'s census reads
#     every tracked file here, so a regression that reintroduces the shape is visible there.
# It is NOT invoked by `.softhouse/conformance.sh`, and T381 could not wire it: that file was
# held by another worker this fire. That residual exposure is recorded in T381's handoff as
# backlog rather than described as closed.
#
#   R2 (the near-rejection). The ANTI-calibration was itself fail-open:
#
#       n=$(git grep -c -F "$CALIB_NEG_STR" -- <corpus> 2>/dev/null | awk ...)
#       if [ "${n:-0}" -gt 0 ]; then ... exit 3; fi
#
#     `2>/dev/null` threw the engine's complaint away and the PIPE threw its exit status away,
#     so a search that ERRORED yielded n=0 -- which on THIS arm is the PASS condition. It
#     printed `CALIBRATE-: PASS -- known negative matched 0 times across the tracked corpus`
#     and `calibration=yes exit=0`, BYTE-IDENTICALLY to a run in which the search really ran.
#     `set -o pipefail` is ON in this file and did NOT help, because the status of the
#     assignment was never read either: pipefail is not a substitute for CHECKING.
#     FIXED: every calibration search now runs through engine_count(), which reads git grep's
#     status AND awk's status and refuses a non-numeric tally. RED-DRIVEN: T381 drive D-R2.
#
#   R3. Both calibrations were `-F`; THIRTEEN OF THE SIXTEEN SELECTORS ARE `-E`, and the
#     anti-calibration's own stated justification is an `-E` hazard. The calibration therefore
#     never exercised the mode the selectors run in. FIXED three ways: an `-E` POSITIVE arm
#     whose pattern matches only if ERE metacharacters are really interpreted; an `-E` ANTI arm
#     on a run-time sentinel; and sel() now REFUSES any selector pattern carrying a
#     backslash-class, which turns this header's `NO \b anywhere` CLAIM into a CHECK.
#     RED-DRIVEN: T381 drive D-R3, a shim that rewrites `-E` to `-F` -- a literal-minded engine.
#
#   R1. sel() read `git grep`'s status and then handed the hits to two ARCHIVE-predicate greps
#     whose status it did not read, so a malformed predicate turned a real hit into `LIVE: 0`
#     at exit 0 -- F2's shape moved one step downstream of the repair. FIXED: both statuses are
#     read, and a classification that did not run refuses instead of printing a zero. D-R1.
#
#   R4. `2>&1` folded stderr into the hit set on EVERY path: at rc=0 a warning line was counted
#     as a hit and listed as LIVE, and at rc=1 it was discarded unprinted. FIXED: stderr goes
#     to a private scratch file outside the repository and is reported on its own line on every
#     path. RED-DRIVEN: T381 drive D-R4.
#
# THE T238 HAZARD IS STILL LIVE ON THIS HOST, and calibrate() now MEASURES it on every run
# instead of asserting it in prose -- see the `SWEEP OBSERVE` line. Re-measured by T381: the
# escaped and the literal spelling of the same term return byte-identical output, because git
# compiles the backslash-class down to those literal letters.
#
# POPULATION: `git ls-files .softhouse` -- TRACKED files only. Untracked files are not part of
# the record and were separately confirmed to be zero in number at the time of writing.
#
# It reaches no network and no database, and it writes NOTHING INTO THE REPOSITORY. Since T381
# it creates exactly one scratch file, via `mktemp`, outside the repository, to keep the
# engine's stderr out of the hit set; it is removed on exit. It is still a grep.
set -uo pipefail

# THE ENGINE'S STDERR NEEDS SOMEWHERE TO GO THAT IS NOT THE HIT SET. [T381, R4]
SWEEP_ERRF=$(mktemp "${TMPDIR:-/tmp}/casualty-sweep-stderr.XXXXXXXXXX") || {
  echo "SWEEP ABORT (exit 2): could not create a scratch file for the engine's stderr. Without" >&2
  echo "  it a warning line cannot be told apart from a hit, and no count below is trustworthy." >&2
  exit 2
}
trap 'rm -f "$SWEEP_ERRF"' EXIT HUP INT TERM
_top=$(git rev-parse --show-toplevel 2>/dev/null) || _top=""
if [ -z "$_top" ] || ! cd "$_top"; then
  echo "SWEEP ABORT (exit 2): not inside a usable git work tree; there is no corpus to sweep" >&2
  exit 2
fi

SWEEP_RC=0          # accumulated explicitly; never inherited from a pipeline
SWEEP_SELECTORS=0
SWEEP_DIDNOTRUN=0
SWEEP_CALIBRATED=no

# THE TOTAL IS NOT THE INTERESTING NUMBER, AND SAYING SO IS THE POINT OF THIS SCRIPT.
# Most hits land in ARCHIVED evidence -- a conformance transcript, a psql dump, a review's
# out/ directory. Those are SNAPSHOTS OF A STATE THE ORACLE HAS LEFT and they are supposed to
# go stale; editing one to match today would be forging a witness, which this program has a
# named pattern for. What matters is the hits in LIVE files: doctrine a reader treats as
# current, and executables that run.
#
# So every selector reports THREE numbers -- total, archived, live -- and lists only the live
# ones. The archive predicate is stated here rather than buried, so a reader can disagree with
# it by reading one regex.
#
# T371 CHANGE, and it WIDENS the LIVE list: `.softhouse/observations/` is no longer classed as
# archived. T367 caught the inconsistency -- T363's own casualty list correctly names
# `observations/20260827-chain2-standing-oracle-baseline.md:21-26` as a LIVE casualty while
# this predicate was hiding that entire directory, so the shipped list was not derivable from
# the shipped script. An observation is a standing note a reader treats as current; a review, a
# handoff and an `out/` transcript are dated records of a moment. Only the latter are archive.
ARCHIVE='(/out/|/evidence/|/transcripts/|/logs/|/red-drive/|/baseline/|/schema-drive/|/probe/|/prose/|\.softhouse/runs/|\.softhouse/logs/|\.softhouse/capture/bar-|\.softhouse/handoff/|\.softhouse/reviews/)'

# --------------------------------------------------------------------------- calibration
# P-72 plus T238's fabrication finding: prove the engine finds a known POSITIVE and does NOT
# find a known NEGATIVE, before any selector's zero is allowed to mean anything.
CALIB_POS_STR='CASUALTY SWEEP for the T352'
CALIB_POS_PATH='.softhouse/capture/t363-oracle-baseline/instruments/'
# The known-NEGATIVE sentinel is built AT RUN TIME from the pid and the clock, deliberately.
# A hard-coded sentinel string appears verbatim in this very file, so `git grep` would FIND it
# and the anti-calibration would fail on every run for the wrong reason -- an instrument that
# cannot be searched for its own sentinel. Composed like this it cannot exist in the corpus.
CALIB_NEG_STR="zzq-t371-anticalibration-sentinel-$$-${RANDOM}-$(date -u +%s)"

# T381 (R3). THE SELECTORS RUN IN `-E`, SO THE CALIBRATION MUST TOO. Thirteen of S1..S16 are
# `-E` and both of T371's calibration arms were `-F`, which has no metacharacters and so cannot
# reach the hazard the anti-calibration's own comment cites as its reason for existing.
#
# CALIB_POS_ERE matches ONLY if the engine really interprets a bracket expression, a group, an
# alternation and a bounded quantifier. A literal-minded `-E` -- exactly the failure T238 named
# -- returns 0 for it, and the run now ABORTS instead of printing thirteen unmeasured zeros. It
# is written so that its OWN definition line cannot match it: the text here reads `C[A]SUALTY`
# while the pattern demands a literal `CASUALTY`.
CALIB_POS_ERE='C[A]SUALTY SW(EEP|OOP) for the T3[0-9]{2}'
CALIB_NEG_ERE="(zzq|qzz)-t381-ere-anticalib-[0-9]+-$$-${RANDOM}-$(date -u +%s)"

# --------------------------------------------------------------------------- engine plumbing
# T381 (R2). ONE PLACE RUNS `git grep` FOR A COUNT, AND IT READS BOTH STATUSES.
#   ENGINE_RC   0 matched | 1 a MEASURED zero | >=2 the search DID NOT RUN
#   return      0 usable  | 2 did-not-run     | 3 the TALLY itself failed
# An errored search is not an empty one, and a missing count is not a count of zero.
ENGINE_N=""; ENGINE_RC=0; ENGINE_ERR=""
engine_count() {
  local out rc n arc
  ENGINE_N=""; ENGINE_ERR=""
  out=$(git grep "$@" 2>"$SWEEP_ERRF"); rc=$?
  ENGINE_RC=$rc
  ENGINE_ERR=$(cat "$SWEEP_ERRF")
  if [ "$rc" -ge 2 ]; then return 2; fi
  n=$(printf '%s\n' "$out" | awk -F: '{s+=$NF} END{print s+0}'); arc=$?
  if [ "$arc" -ne 0 ]; then return 3; fi
  case "$n" in ''|*[!0-9]*) return 3 ;; esac
  ENGINE_N=$n
  return 0
}

_calib_refuse() { # _calib_refuse <arm label> <engine_count return>
  local arm="$1" ec="$2"
  if [ "$ec" -eq 2 ]; then
    echo "SWEEP ABORT (exit 3): the $arm calibration search DID NOT RUN -- git grep rc=$ENGINE_RC." >&2
    echo "  An ERRORED search is not a search that found nothing. Until T381 this arm discarded" >&2
    echo "  that status and printed PASS for exactly this state (T379 R2). Engine output follows:" >&2
    printf '%s' "$ENGINE_ERR" | grep . | cut -c1-200 | sed 's/^/    ! /' >&2
  else
    echo "SWEEP ABORT (exit 3): the $arm calibration ran, but its TALLY produced no number." >&2
    echo "  A missing count is not a count of zero, so nothing below would be interpretable." >&2
  fi
  exit 3
}

calibrate() {
  local ec
  # ---- arm 1 of 4: -F POSITIVE. A known-present string must be findable (P-72).
  engine_count -c -F "$CALIB_POS_STR" -- "$CALIB_POS_PATH"; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-F POSITIVE" "$ec"
  if [ "$ENGINE_N" -lt 1 ]; then
    echo "SWEEP ABORT (exit 3): CALIBRATION MISSED. '$CALIB_POS_STR' found 0 in $CALIB_POS_PATH," >&2
    echo "  where it is KNOWN present. The engine, the pattern language or the corpus is broken;" >&2
    echo "  no negative printed below would be interpretable, so nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE+F: PASS -- known positive matched %s time(s) in %s\n' "$ENGINE_N" "$CALIB_POS_PATH"

  # ---- arm 2 of 4: -F ANTI. A known-absent sentinel must return zero -- AND THE SEARCH MUST
  # HAVE RUN, or that zero means nothing. This is the arm T379 R2 caught printing PASS.
  engine_count -c -F "$CALIB_NEG_STR" -- .softhouse; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-F ANTI" "$ec"
  if [ "$ENGINE_N" -gt 0 ]; then
    echo "SWEEP ABORT (exit 3): ANTI-CALIBRATION FAILED. The known-absent sentinel matched $ENGINE_N time(s)." >&2
    echo "  The engine is FABRICATING matches; every POSITIVE below would be suspect, not only the" >&2
    echo "  zeros. Nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE-F: PASS -- known negative matched 0 times, and the search RAN (rc=%s)\n' "$ENGINE_RC"

  # ---- arm 3 of 4: -E POSITIVE. [T381 R3] The mode thirteen of the sixteen selectors use.
  engine_count -c -E "$CALIB_POS_ERE" -- "$CALIB_POS_PATH"; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-E POSITIVE" "$ec"
  if [ "$ENGINE_N" -lt 1 ]; then
    echo "SWEEP ABORT (exit 3): -E CALIBRATION MISSED. The pattern '$CALIB_POS_ERE' matched 0 times" >&2
    echo "  in $CALIB_POS_PATH, where an ERE-interpreting engine finds it. This engine is NOT" >&2
    echo "  interpreting ERE metacharacters, so the thirteen '-E' selectors below would each print" >&2
    echo "  a zero NOBODY MEASURED. Nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE+E: PASS -- ERE metacharacters ARE interpreted; pattern matched %s time(s)\n' "$ENGINE_N"

  # ---- arm 4 of 4: -E ANTI. [T381 R3] No fabrication in the mode those thirteen use.
  engine_count -c -E "$CALIB_NEG_ERE" -- .softhouse; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-E ANTI" "$ec"
  if [ "$ENGINE_N" -gt 0 ]; then
    echo "SWEEP ABORT (exit 3): -E ANTI-CALIBRATION FAILED. A run-time sentinel that cannot exist" >&2
    echo "  in the corpus matched $ENGINE_N time(s) under '-E'. The engine FABRICATES in the mode" >&2
    echo "  thirteen selectors use. Nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE-E: PASS -- known negative matched 0 times under -E, and the search RAN (rc=%s)\n' "$ENGINE_RC"

  # ---- the T238 hazard, MEASURED rather than asserted. [T381 R3] Deliberately NOT a gate, and
  # it says so: on this host the two spellings are EXPECTED to agree, because git compiles the
  # backslash-class down to the literal letters, so gating on disagreement would brick the sweep
  # for the wrong reason. The GATE built on this fact is the refusal in sel() below. This line
  # is the standing measurement that keeps that gate honest -- a host where the hazard has gone
  # away shows up in the transcript instead of being assumed either way.
  local bs hz_esc hz_lit n_esc n_lit
  bs='\'
  hz_esc="${bs}bmain${bs}b"
  hz_lit="bmainb"
  engine_count -c -E "$hz_esc" -- .softhouse; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-E T238-HAZARD (escaped)" "$ec"
  n_esc="$ENGINE_N"
  engine_count -c -E "$hz_lit" -- .softhouse; ec=$?
  [ "$ec" -eq 0 ] || _calib_refuse "-E T238-HAZARD (literal)" "$ec"
  n_lit="$ENGINE_N"
  if [ "$n_esc" -eq "$n_lit" ]; then
    printf 'SWEEP OBSERVE: T238 hazard LIVE -- escaped=%s literal=%s AGREE, so -E compiles the\n' "$n_esc" "$n_lit"
    printf '               backslash-class to the literal letters. sel() REFUSES such patterns.\n'
  else
    printf 'SWEEP OBSERVE: T238 hazard NOT reproducing here -- escaped=%s literal=%s DISAGREE. The\n' "$n_esc" "$n_lit"
    printf '               refusal in sel() is conservative rather than necessary; it stays.\n'
  fi
  SWEEP_CALIBRATED=yes
}

sel() { # sel <label> <git-grep args...>
  local label="$1"; shift
  printf '\n=== %s\n' "$label"
  printf '    engine: git grep %s\n' "$*"
  if [ "$SWEEP_CALIBRATED" != yes ]; then
    printf '    *** SELECTOR REFUSED: sel() called before calibration. Nothing was searched.\n'
    SWEEP_RC=3
    return
  fi
  # T381 (R3). THE HEADER'S `NO \b ANYWHERE` WAS A CLAIM. THIS MAKES IT A CHECK.
  # This engine compiles a backslash-class down to the literal letter and returns zero
  # SILENTLY -- calibrate() re-measures that on every run and prints the result. A selector
  # carrying one would emit a negative nobody measured, which is the invariant this whole file
  # is named after, so it is REFUSED before the engine is asked anything at all.
  # THE CHECK'S OWN STATUS IS READ TOO. [T381, from its own 2>/dev/null / discarded-pipe audit]
  # `if printf | grep -q ...; then` would have been the fifth instance of the shape in this one
  # file: grep exits 2 on ERROR, an `if` reads that as FALSE, and the selector would sail past
  # a check that never ran. The three outcomes are separated instead. `set -o pipefail` is on,
  # so esc_rc is the PIPELINE's status and a failed printf is caught here as well.
  local a esc_rc
  for a in "$@"; do
    printf '%s' "$a" | LC_ALL=C grep -q '\\[bBdDsSwW<>]'; esc_rc=$?
    if [ "$esc_rc" -ge 2 ]; then
      printf '    *** SELECTOR REFUSED: the backslash-class CHECK ITSELF did not run (rc=%s). An\n' "$esc_rc"
      printf '    *** unrun check is not a clean check, so nothing was searched.\n'
      [ "$SWEEP_RC" -ge 3 ] || SWEEP_RC=3
      return
    fi
    if [ "$esc_rc" -eq 0 ]; then
      printf '    *** SELECTOR REFUSED: its pattern carries a backslash-class, which this engine\n'
      printf '    *** reads as a LITERAL letter (see the SWEEP OBSERVE line above). Nothing was\n'
      printf '    *** searched, because the zero it would return would not be a measurement.\n'
      [ "$SWEEP_RC" -ge 3 ] || SWEEP_RC=3
      return
    fi
  done
  SWEEP_SELECTORS=$((SWEEP_SELECTORS+1))
  local all live arch rc err live_rc arch_rc
  # THE REPAIR. The status is READ.
  #   rc 0  -> matched
  #   rc 1  -> a MEASURED zero: the engine ran over the corpus and matched nothing
  #   rc >1 -> the search DID NOT RUN. That is not "zero hits" and must never print as one.
  # T381 (R4): stderr now goes to a scratch file OUTSIDE the hit set. T371 folded it in with
  # `2>&1`, so at rc=0 a warning line was counted by `grep -c .` as a hit and listed as LIVE,
  # and at rc=1 it was thrown away unprinted. It is now neither counted nor lost.
  all=$(git grep "$@" -- .softhouse 2>"$SWEEP_ERRF"); rc=$?
  err=$(cat "$SWEEP_ERRF")
  if [ "$rc" -ge 2 ]; then
    SWEEP_DIDNOTRUN=$((SWEEP_DIDNOTRUN+1)); SWEEP_RC=4
    printf '    *** SELECTOR DID NOT RUN (git grep rc=%s). THIS IS NOT "ZERO HITS" -- no absence\n' "$rc"
    printf '    *** may be read from this selector. Engine output follows:\n'
    printf '%s' "$err" | grep . | cut -c1-200 | sed 's/^/      ! /'
    return
  fi
  if [ -n "$err" ]; then
    printf '    ENGINE STDERR on a search that DID complete (rc=%s). NOT counted as a hit:\n' "$rc"
    printf '%s' "$err" | grep . | cut -c1-200 | sed 's/^/      ~ /'
  fi
  if [ "$rc" -eq 1 ]; then
    printf '    MEASURED ZERO -- engine ran over %s tracked files in the sweep corpus and matched nothing\n' \
      "$(git ls-files .softhouse | grep -c .)"
    printf '    hits total: 0   archived (snapshots, correctly stale): 0   LIVE: 0\n'
    return
  fi
  # T381 (R1). THE THIRD AND FOURTH STATUSES. T371 read the engine's and then handed the hits
  # to these two greps without reading theirs, so a malformed $ARCHIVE turned a REAL HIT into
  # `LIVE: 0` at exit 0 -- F2's exact shape, one step downstream of where it was repaired.
  # grep: 0 matched, 1 matched nothing (both legitimate here), >=2 CLASSIFICATION DID NOT RUN.
  live=$(printf '%s' "$all" | grep -v -E "$ARCHIVE"); live_rc=$?
  arch=$(printf '%s' "$all" | grep -c -E "$ARCHIVE"); arch_rc=$?
  if [ "$live_rc" -ge 2 ] || [ "$arch_rc" -ge 2 ]; then
    SWEEP_DIDNOTRUN=$((SWEEP_DIDNOTRUN+1)); SWEEP_RC=4
    printf '    *** SELECTOR HIT, BUT ITS CLASSIFICATION DID NOT RUN (archive-predicate grep\n'
    printf '    *** rc=%s/%s). The engine FOUND %s line(s) and they could not be split into\n' \
      "$live_rc" "$arch_rc" "$(printf '%s' "$all" | grep -c .)"
    printf '    *** archived and LIVE, so NO live figure may be printed here -- a "LIVE: 0" would\n'
    printf '    *** be a negative nobody measured. Check ARCHIVE is a valid ERE.\n'
    return
  fi
  printf '    hits total: %s   archived (snapshots, correctly stale): %s   LIVE: %s\n' \
    "$(printf '%s' "$all" | grep -c .)" "$arch" "$(printf '%s' "$live" | grep -c .)"
  printf '%s' "$live" | grep . | cut -c1-200 | sed 's/^/      /'
}

echo "CASUALTY SWEEP for the T352+T359 oracle-state movement"
echo "repo: $(git rev-parse --short HEAD)   date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "population: $(git ls-files .softhouse | wc -l | tr -d ' ') tracked files under .softhouse/"
echo "untracked under .softhouse/: $(git ls-files --others --exclude-standard .softhouse | wc -l | tr -d ' ')"
if [ "$(git ls-files .softhouse | grep -c .)" -lt 1 ]; then
  echo "SWEEP ABORT (exit 2): corpus reachable but tracks ZERO files under .softhouse/." >&2
  echo "  A sweep over nothing proves nothing (P-35); a denominator of zero is an ERROR, not a pass." >&2
  exit 2
fi
calibrate

# ---- S1..S3: the counter pins themselves ------------------------------------------------
sel "S1  the literal row/maxid pin '60/64'" -n -F '60/64'
sel "S2  the standing-baseline pin format 'gerege <table> = '" -n -E 'gerege (acc_gl_journal_entry|acc_gl_closure|distinct_transaction_id|m_portfolio_command_source|m_loan|m_office) = '
sel "S3  string-equality comparison of a standing counter" -n -F 'STANDING ORACLE MOVED'

# ---- S4..S5: per-account leg counts written as PROSE -------------------------------------
sel "S4  per-account leg counts spelled as words in the capability store" -n -E 'gl 16 (carries|->) (SIXTEEN|TWENTY)|is TWELVE|gl 17 is|gl 21 is'
sel "S5  per-account leg counts spelled as digits" -n -E 'gl (16|17|18|21|22) (->|=) [0-9]+'

# ---- S6..S8: the MNT-only / single-currency assertions -----------------------------------
sel "S6  'every row currency_code = MNT' and its relatives" -n -E 'every row currency_code|every journal entry (in the corpus )?is MNT|Every entry is MNT'
sel "S7  the captured distinct_currency_codes projection" -n -F 'distinct_currency_codes'
sel "S8  MULTI-CURRENCY untouched claims" -n -E 'MULTI-CURRENCY untouched|no cross-currency|multi.currency entry'

# ---- S9..S11: anything that re-derives a count at RUN time --------------------------------
sel "S9  does the conformance harness or a guard reach the tenant database at all?" -n -E 'psql|docker exec|fineract-db-1'
sel "S10 count(*) over the ledger tables in an executable" -n -E 'count\(\*\).{0,40}acc_gl_journal_entry|acc_gl_journal_entry.{0,40}count\(\*\)'
sel "S11 the ledger invariant guard's own pins" -n -E 'EXEMPTION_PIN|parity vectors|LEDGER_.*PIN'

# ---- S12..S16: ADDED BY T371. THE SHAPE THE ELEVEN SELECTORS ABOVE COULD NOT SEE ----------
# T363's honest `[UNVERIFIED] that the 11 selectors are exhaustive` bit, and F2 is why it bit
# unnoticed. NONE of S1..S11 matched `reference-oracle.md`'s present-tense
# `156 PROCESSED / 194 ERROR` -- live 162 / 197 AS AT 2026-08-27, T371's re-derivation against
# the live database in `.softhouse/capture/t371-t367-conditions/sql/q2-status-split.sql`.
# [T381, closing FU-T379-2: a cardinal about a live table, typed into a live instrument, MUST
# carry the date it was true -- `.softhouse/capture/t363-oracle-baseline/CASUALTIES.md` already
# dates its own copy. It is a moving counter; undated it reads as current forever, and S12
# reports this very line LIVE on every run.]
#
# The eleven selectors above all hunt a LEDGER count -- `acc_gl_journal_entry`, per-GL-account
# legs, currency. The missed casualty was an AUDIT-TABLE count, and the class is wider than
# that: ANY cardinal about a live table, written in the present tense, in a file a reader treats
# as doctrine. S12..S16 therefore look for the SHAPE, not for known strings. They are noisier by
# construction, and that is the correct trade: a selector that only finds what you already knew
# was there is not a search.
sel "S12 a command-source STATUS SPLIT written as a cardinal" -n -E '[0-9]+ (PROCESSED|ERROR|REJECTED|INVALID|AWAITING_APPROVAL|UNDER_PROCESSING)'
sel "S13 present-tense 'the <thing> is/are/now <digits>' about a live counter" -n -E '(split|count|total|tally) (is|are|now) [*]*[0-9]'
sel "S14 'N rows' / 'max id N' prose pins over any watched table" -n -E '[0-9]+ rows|max id [0-9]+'
sel "S15 a digit sitting next to a watched table name, either order" -n -E '(acc_gl_journal_entry|acc_gl_closure|m_portfolio_command_source|m_office|m_loan)[^0-9]{0,30}[0-9]{2,}|[0-9]{2,}[^0-9]{0,30}(acc_gl_journal_entry|acc_gl_closure|m_portfolio_command_source)'
sel "S16 status-enum prose, which is where a stale split tends to sit" -n -E 'status *= *5|status 5|CommandProcessingResultType'

echo
echo "END OF SWEEP. A selector not listed above was not searched, and this file is the"
echo "record of that. Add a selector and re-run rather than asserting absence."
printf 'SWEEP-RESULT: commit=%s selectors=%s did_not_run=%s calibration=%s exit=%s\n' \
  "$(git rev-parse --short HEAD)" "$SWEEP_SELECTORS" "$SWEEP_DIDNOTRUN" "$SWEEP_CALIBRATED" "$SWEEP_RC"
if [ "$SWEEP_DIDNOTRUN" -gt 0 ]; then
  echo "*** $SWEEP_DIDNOTRUN SELECTOR(S) DID NOT RUN. The casualty list from this run is INCOMPLETE" >&2
  echo "*** by an unknown amount, and no absence claimed above is admissible." >&2
fi
exit "$SWEEP_RC"
