#!/usr/bin/env bash
# 30-casualty-sweep-t388.sh -- WHERE I LOOKED for things the T388 oracle-state movement
# invalidated.
#
#   bash .softhouse/capture/t388-accrual-capture/30-casualty-sweep-t388.sh
#
# SAME SHAPE AS `.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh`
# AS REPAIRED BY T371, and deliberately a SEPARATE FILE rather than an edit to it: that
# instrument has produced committed evidence (T114's standing ruling) and it is outside
# this task's write grant. What is carried over verbatim, because each item was paid for
# by a real defect:
#
#   * git grep's EXIT STATUS IS READ (T367 F2). "the engine ran and matched nothing"
#     (rc 1) and "the search never ran" (rc >= 2) print differently and exit differently.
#     An instrument must not be able to emit a negative it did not measure.
#   * a POSITIVE calibration -- a known-present string must be findable before any zero
#     below is interpretable (P-72).
#   * an ANTI-calibration on a sentinel composed AT RUN TIME -- `git grep -E` on this host
#     has been measured FABRICATING a hit (T238), so "I got hits therefore my rig works"
#     is not a calibration. The sentinel is composed rather than written literally,
#     because a literal one would appear in this very file and match itself.
#   * NO `\b` ANYWHERE. `git grep -E` reads `\b` as a literal 'b' on this host and returns
#     zero SILENTLY (T232).
#   * total / archived / LIVE reported per selector, with the archive predicate printed
#     rather than buried, and `.softhouse/observations/` classed LIVE (T371's widening).
#
# WHAT T388 MOVED, and therefore what these selectors hunt. Derived from
# out/T388-B01-before-snapshot.txt (BEFORE) against out/T388-S01-after-snapshot.txt (AFTER):
#
#     acc_gl_journal_entry        71/75  -> 91/95
#     distinct_transaction_id        31  -> 35
#     m_portfolio_command_source 359/359 -> 379/379
#     acc_gl_account              23/34  -> 36/47
#     m_product_loan              33/60  -> 34/63
#     m_client                      2/2  -> 3/3
#     m_loan                          7  -> 8          <-- NEW. T363 recorded m_loan as UNMOVED.
#     m_loan_transaction          17/27  -> 21/31
#     acc_product_mapping       132/156  -> 145/189
#     ACCRUAL_PERIODIC products    {28}  -> {28, 63}   <-- "product 28 is the ONLY one" is now FALSE
#     receivable-slot entries         0  -> 9          <-- "NOT ONE JOURNAL ENTRY" is now FALSE
#
# UNMOVED, and checked rather than assumed: every GL account a promoted vector reads
# (1, 2, 4, 6, 8, 10, 15, 16, 17, 18, 21, 22), acc_gl_closure, m_office.
#
# THIS SCRIPT GATES NOTHING. Its exit code says whether the sweep is ADMISSIBLE, never
# whether a casualty exists; a LIVE hit is adjudicated by a human in
# ORACLE-STATE-MOVED-BY-T388.md. It writes nothing, opens no database and reaches no
# network. It is a grep.
#
# EXIT CODES
#   0  every selector RAN. Hits or measured zeros; both are MEASUREMENTS.
#   2  corpus unusable -- not in a git work tree, or it tracks zero files (P-35).
#   3  calibration failed -- no negative from this run is interpretable.
#   4  at least one selector DID NOT RUN. Its "zero" is not a zero.
set -uo pipefail

if [ -z "${BASH_VERSION:-}" ] || ( shopt -qo posix 2>/dev/null ); then
  echo "REFUSING (exit 3): run this with bash, not sh. On this host /bin/sh IS bash in POSIX" >&2
  echo "  mode, so testing BASH_VERSION alone admits it -- the exact defect T363 found in its" >&2
  echo "  own instrument (CASUALTIES.md section E)." >&2
  exit 3
fi

_top=$(git rev-parse --show-toplevel 2>/dev/null) || _top=""
if [ -z "$_top" ] || ! cd "$_top"; then
  echo "SWEEP ABORT (exit 2): not inside a usable git work tree; there is no corpus to sweep" >&2
  exit 2
fi

SWEEP_RC=0
SWEEP_SELECTORS=0
SWEEP_DIDNOTRUN=0
SWEEP_CALIBRATED=no

ARCHIVE='(/out/|/evidence/|/transcripts/|/logs/|/red-drive/|/baseline/|/schema-drive/|/probe/|/prose/|\.softhouse/runs/|\.softhouse/logs/|\.softhouse/capture/bar-|\.softhouse/handoff/|\.softhouse/reviews/)'

CALIB_POS_STR='WHERE I LOOKED for things the T388 oracle-state movement'
CALIB_POS_PATH='.softhouse/capture/t388-accrual-capture/'
CALIB_NEG_STR="zzq-t388-anticalibration-sentinel-$$-${RANDOM}-$(date -u +%s)"

calibrate() {
  local n
  n=$(git grep -c -F "$CALIB_POS_STR" -- "$CALIB_POS_PATH" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  if [ "${n:-0}" -lt 1 ]; then
    echo "SWEEP ABORT (exit 3): CALIBRATION MISSED. '$CALIB_POS_STR' found 0 in $CALIB_POS_PATH," >&2
    echo "  where it is KNOWN present. Either this file is not tracked yet -- git grep sees only" >&2
    echo "  TRACKED files, so run 'git add -A' first -- or the engine is broken. Either way no" >&2
    echo "  negative below would be interpretable, so nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE+: PASS -- known positive matched %s time(s) in %s\n' "$n" "$CALIB_POS_PATH"
  n=$(git grep -c -F "$CALIB_NEG_STR" -- .softhouse/ 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  if [ "${n:-0}" -gt 0 ]; then
    echo "SWEEP ABORT (exit 3): ANTI-CALIBRATION FAILED. The known-absent sentinel matched $n time(s)." >&2
    echo "  The engine is FABRICATING matches; every POSITIVE below would be suspect too." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE-: PASS -- known negative matched 0 times across the tracked corpus\n'
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
  SWEEP_SELECTORS=$((SWEEP_SELECTORS+1))
  local all live arch rc
  all=$(git grep "$@" -- .softhouse/ 2>&1); rc=$?
  if [ "$rc" -ge 2 ]; then
    SWEEP_DIDNOTRUN=$((SWEEP_DIDNOTRUN+1)); SWEEP_RC=4
    printf '    *** SELECTOR DID NOT RUN (git grep rc=%s). THIS IS NOT "ZERO HITS".\n' "$rc"
    printf '%s' "$all" | grep . | cut -c1-200 | sed 's/^/      ! /'
    return
  fi
  if [ "$rc" -eq 1 ]; then
    printf '    MEASURED ZERO -- engine ran over %s tracked files under .softhouse/ and matched nothing\n' \
      "$(git ls-files .softhouse | grep -c .)"
    printf '    hits total: 0   archived (snapshots, correctly stale): 0   LIVE: 0\n'
    return
  fi
  live=$(printf '%s' "$all" | grep -v -E "$ARCHIVE")
  arch=$(printf '%s' "$all" | grep -c -E "$ARCHIVE")
  printf '    hits total: %s   archived (snapshots, correctly stale): %s   LIVE: %s\n' \
    "$(printf '%s' "$all" | grep -c .)" "$arch" "$(printf '%s' "$live" | grep -c .)"
  printf '%s' "$live" | grep . | cut -c1-200 | sed 's/^/      /'
}

echo "CASUALTY SWEEP for the T388 oracle-state movement"
echo "repo: $(git rev-parse --short HEAD)   date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "population: $(git ls-files .softhouse | wc -l | tr -d ' ') tracked files under .softhouse/"
echo "untracked under .softhouse/: $(git ls-files --others --exclude-standard .softhouse | wc -l | tr -d ' ')"
echo "NOTE: git grep sees TRACKED files only. Run this AFTER 'git add -A' or this task's own"
echo "      new files are invisible to it -- the T370/T361 failure, in a different costume."
if [ "$(git ls-files .softhouse | grep -c .)" -lt 1 ]; then
  echo "SWEEP ABORT (exit 2): corpus reachable but tracks ZERO files under .softhouse/." >&2
  exit 2
fi
calibrate

# ---- A. the standing-baseline counter pins, which are literal string comparisons ---------
sel "S1  the t305/t327 standing-baseline pin lines 'gerege <table> = '" -n -E 'gerege (acc_gl_journal_entry|acc_gl_closure|distinct_transaction_id|m_portfolio_command_source|m_loan|m_office) = '
sel "S2  the executable string-equality refusal those pins feed" -n -F 'STANDING ORACLE MOVED'
sel "S3  the literal row/maxid pins '60/64', '71/75', '352/352', '359/359'" -n -E '60/64|71/75|352/352|359/359'
sel "S4  a literal m_loan cardinal -- MOVED BY T388, 7 -> 8" -n -E 'm_loan = [0-9]+|m_loan .{0,12}= *[0-9]+|gerege m_loan'

# ---- B. the ACCRUAL claims T388 falsified ------------------------------------------------
sel "S5  'product 28 is the ONLY ACCRUAL_PERIODIC product' and relatives" -n -E 'ONLY ACCRUAL_PERIODIC|only ACCRUAL_PERIODIC|ONLY row with that value|only row with that value'
sel "S6  'NOT ONE JOURNAL ENTRY ... RECEIVABLE SLOT' and relatives" -n -E 'NOT ONE (JOURNAL )?ENTRY|NOT ONE JOURNAL ENTRY|no accrual product has a loan|ARRIVED THROUGH A RECEIVABLE SLOT'
sel "S7  'accrual is entirely absent / entirely ungraded'" -n -E 'ACCRUAL is entirely absent|ENTIRELY UNGRADED|accrual .{0,20}entirely absent'
sel "S8  'product 28 HAS NO LOAN' / 'the single missing ingredient is A LOAN'" -n -E 'HAS NO LOAN|missing ingredient is A LOAN|product_id = 28|zero loans'
sel "S9  claims that no accrual or COB job has run" -n -E 'no accrual or COB job|no accrual job has|COB job has ever run'

# ---- C. per-account leg counts written as prose (the class that has gone stale 3x) --------
sel "S10 per-account leg counts spelled as words" -n -E 'gl 16 (carries|->) (SIXTEEN|TWENTY|TWENTY-ONE)|is TWELVE|gl 17 is|gl 21 is'
sel "S11 per-account leg counts spelled as digits" -n -E 'gl (16|17|18|21|22) (->|=) [0-9]+'

# ---- D. the wider SHAPE: any present-tense cardinal about a live table (T371 S12-S16) -----
sel "S12 a command-source STATUS SPLIT written as a cardinal" -n -E '[0-9]+ (PROCESSED|ERROR|REJECTED|INVALID)'
sel "S13 a cardinal immediately adjacent to a table name" -n -E '(acc_gl_journal_entry|acc_gl_account|acc_product_mapping|m_product_loan|m_client|m_loan_transaction|m_portfolio_command_source)[^a-z_]{0,24}[0-9]+ (rows|entries|records)'
sel "S14 'there are N products / N clients / N loans in this tenant'" -n -E '(THIRTY-THREE|thirty-three|33) (loan )?products|TWO clients|two clients in|SEVEN loans|seven loans'
sel "S15 max-id pins on the tables T388 appended to" -n -E 'max\(id\)[^0-9]{0,20}(34|60|75|156|27|359)([^0-9]|$)'

# ---- E. id collisions: the ids T388 consumed, in case something assumed them free ---------
sel "S16 references to GL account ids 35-47, product 63, client 3, loan 8" -n -E 'gl (3[5-9]|4[0-7])([^0-9]|$)|product 63|loanproducts/63|clients/3([^0-9]|$)|loans/8([^0-9?]|$)'

# ---- F. negative controls: things T388 did NOT move --------------------------------------
sel "S17 acc_gl_closure pins -- T388 did not touch closures (expect stale-or-fine, not new)" -n -E 'acc_gl_closure = |acc_gl_closure 0/null'
sel "S18 does any guard or the harness reach the tenant database at all?" -n -E 'psql|docker exec|fineract-db-1'

printf '\n----------------------------------------------------------------------------------\n'
printf 'selectors run: %s   selectors that DID NOT RUN: %s\n' "$SWEEP_SELECTORS" "$SWEEP_DIDNOTRUN"
if [ "$SWEEP_DIDNOTRUN" -gt 0 ]; then
  printf 'SWEEP EXIT 4: at least one selector did not run. No absence above is interpretable.\n'
fi
printf 'A LIVE HIT IS A CANDIDATE, NOT A VERDICT. Adjudication is in ORACLE-STATE-MOVED-BY-T388.md.\n'
exit "$SWEEP_RC"
