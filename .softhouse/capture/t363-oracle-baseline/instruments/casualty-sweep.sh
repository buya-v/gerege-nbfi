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
# ENGINE AND FLAGS, stated because they have bitten this program: `git grep` with `-E` and
# `-F` explicitly per selector; NO `\b` anywhere, because `git grep -E` reads `\b` as a
# LITERAL 'b' on this machine and returns zero SILENTLY (T232's measurement).
#
# POPULATION: `git ls-files .softhouse` -- TRACKED files only. Untracked files are not part of
# the record and were separately confirmed to be zero in number at the time of writing.
#
# It writes nothing and reaches no network and no database. It is a grep.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 2

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
ARCHIVE='(/out/|/evidence/|/transcripts/|/logs/|/red-drive/|/baseline/|/schema-drive/|/probe/|/prose/|\.softhouse/runs/|\.softhouse/logs/|\.softhouse/capture/bar-|\.softhouse/handoff/|\.softhouse/reviews/|\.softhouse/observations/)'

sel() { # sel <label> <git-grep args...>
  local label="$1"; shift
  printf '\n=== %s\n' "$label"
  printf '    engine: git grep %s\n' "$*"
  local all live arch
  all=$(git grep "$@" -- .softhouse/ 2>/dev/null)
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

echo
echo "END OF SWEEP. A selector not listed above was not searched, and this file is the"
echo "record of that. Add a selector and re-run rather than asserting absence."
