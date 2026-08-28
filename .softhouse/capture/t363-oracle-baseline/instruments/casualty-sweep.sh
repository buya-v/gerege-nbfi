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
# POPULATION: `git ls-files .softhouse` -- TRACKED files only. Untracked files are not part of
# the record and were separately confirmed to be zero in number at the time of writing.
#
# It writes nothing and reaches no network and no database. It is a grep.
set -uo pipefail
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

calibrate() {
  local n
  n=$(git grep -c -F "$CALIB_POS_STR" -- "$CALIB_POS_PATH" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  if [ "${n:-0}" -lt 1 ]; then
    echo "SWEEP ABORT (exit 3): CALIBRATION MISSED. '$CALIB_POS_STR' found 0 in $CALIB_POS_PATH," >&2
    echo "  where it is KNOWN present. The engine, the pattern language or the corpus is broken;" >&2
    echo "  no negative printed below would be interpretable, so nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE+: PASS -- known positive matched %s time(s) in %s\n' "$n" "$CALIB_POS_PATH"
  n=$(git grep -c -F "$CALIB_NEG_STR" -- .softhouse/ 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  if [ "${n:-0}" -gt 0 ]; then
    echo "SWEEP ABORT (exit 3): ANTI-CALIBRATION FAILED. The known-absent sentinel matched $n time(s)." >&2
    echo "  The engine is FABRICATING matches; every POSITIVE below would be suspect, not only the" >&2
    echo "  zeros. Nothing is printed." >&2
    exit 3
  fi
  printf 'SWEEP CALIBRATE-: PASS -- known negative matched 0 times in .softhouse/\n'
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
  # THE REPAIR. stderr is FOLDED IN rather than discarded, and the status is READ.
  #   rc 0  -> matched
  #   rc 1  -> a MEASURED zero: the engine ran over the corpus and matched nothing
  #   rc >1 -> the search DID NOT RUN. That is not "zero hits" and must never print as one.
  all=$(git grep "$@" -- .softhouse/ 2>&1); rc=$?
  if [ "$rc" -ge 2 ]; then
    SWEEP_DIDNOTRUN=$((SWEEP_DIDNOTRUN+1)); SWEEP_RC=4
    printf '    *** SELECTOR DID NOT RUN (git grep rc=%s). THIS IS NOT "ZERO HITS" -- no absence\n' "$rc"
    printf '    *** may be read from this selector. Engine output follows:\n'
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
# `156 PROCESSED / 194 ERROR` -- live 162 / 197, T371 re-derived it against the live database
# in `.softhouse/capture/t371-t367-conditions/sql/q2-status-split.sql`.
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
