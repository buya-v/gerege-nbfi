#!/usr/bin/env bash
# T256 — census of tracked files that hardcode a Mac-local path to a REPO INSTRUMENT.
#
# WHY THIS IS AN INSTRUMENT AND NOT A SENTENCE. T256's brief handed me "30 executable
# instruments" and "40 tracked files (30 + 10 prose)". A count restated in a place that
# rots is itself a defect this program has logged, so this file re-derives every figure
# from the tree at whatever commit it is run against, and prints the SELECTOR beside each
# number. Re-run it at any commit; if a figure in the handoff disagrees with this output,
# THIS OUTPUT IS RIGHT and the handoff has rotted.
#
#   P-67 ("The driver certified a figure as EXACT and propagated it to four files — the
#   denominator was never measured") and P-69 ("The measured claim went stale between the
#   review and the revision — inside a single fire"): re-measure, never quote.
#   P-66 / P-70 ("Latent, not promoted, can never resolve, no guard exists — four ways
#   this program stated a search result as a world fact"): NOT FOUND IS A STATEMENT ABOUT
#   THE SEARCH. Every negative below prints the selector that produced it.
#   P-40 ("an enumerator must count what it skipped and say so"): the SKIPPED bucket is
#   counted and listed, not dropped.
#
# Portable by construction: no absolute path to this repo appears anywhere in this file.

set -u -o pipefail

REPO=$(git rev-parse --show-toplevel) || { echo "census: not inside a git checkout — refusing" >&2; exit 2; }
cd "$REPO" || exit 2

# Scratch lives in a per-run mktemp dir, never a literal /tmp path. Two reasons, both
# measured rather than stylistic: (1) two workers of the same fire running this census
# concurrently would otherwise trample one another's intermediate lists and each report a
# number derived from the other's tree; (2) conformance.sh's guard_no_host_state_in_lint_corpus
# holds a PINNED CENSUS of literal shared-temp assignments in repo-wide instruments, and a new
# one entering unseen is exactly what that guard exists to refuse. This instrument is repo-wide
# (it runs `git ls-files` and `git grep`), so it is inside that corpus by construction.
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t256-census.XXXXXXXXXX")" || exit 2
trap 'rm -rf "$WORK"' EXIT HUP INT TERM QUIT

COMMIT=$(git rev-parse HEAD)
echo "T256 TOOLCHAIN-PATH POPULATION CENSUS"
echo "commit   : $COMMIT"
echo "repo     : (path deliberately not printed — it is the very thing under audit)"
echo "date     : $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo

# The two literals. T253's census measured BOTH and the T256 brief carried only the first.
L1='/Users/buv/gerege-nbfi/.softhouse/toolchain'
L2='/Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh'

# ---------------------------------------------------------------------------
# SELECTOR, stated in full so the numbers below can be reproduced or refuted:
#   universe      : `git ls-files` at HEAD  (TRACKED files only; untracked scratch and
#                   the gitignored .softhouse/toolchain/ itself are deliberately outside)
#   match         : `git grep -F -l <literal> HEAD` — fixed string, no regex
#   git grep rc   : 0 = matches, 1 = a MEASURED no-match, >1 = an ERROR that must not be
#                   read as a no-match. The rc is classified, never swallowed.
# ---------------------------------------------------------------------------

TOTAL=$(git ls-files | wc -l | tr -d ' ')
echo "universe : $TOTAL tracked files at HEAD (selector: git ls-files)"
echo

match_or_die() {   # $1 = literal ; writes matching paths on stdout
    local out rc
    out=$(git grep -F -l -- "$1" HEAD 2>/dev/null)
    rc=$?
    case $rc in
        0) printf '%s\n' "$out" | sed 's|^HEAD:||' ;;
        1) : ;;   # measured no-match, not an error, not an absence in the world
        *) echo "census: git grep ERRORED rc=$rc on literal [$1] — this is NOT a no-match" >&2
           exit 2 ;;
    esac
    return 0
}

match_or_die "$L1" | sort > "$WORK"/t256-L1.txt
match_or_die "$L2" | sort > "$WORK"/t256-L2.txt
sort -u "$WORK"/t256-L1.txt "$WORK"/t256-L2.txt > "$WORK"/t256-union.txt

n1=$(wc -l < "$WORK"/t256-L1.txt | tr -d ' ')
n2=$(wc -l < "$WORK"/t256-L2.txt | tr -d ' ')
nu=$(wc -l < "$WORK"/t256-union.txt | tr -d ' ')

echo "LITERAL 1  $L1"
echo "  matched : $n1 tracked files"
echo "LITERAL 2  $L2"
echo "  matched : $n2 tracked files"
echo "UNION (deduplicated)"
echo "  matched : $nu tracked files"
echo

# ---------------------------------------------------------------------------
# THE THREE BUCKETS. The T256 brief names two (instrument / record). Measuring the tree
# forces a third, and the third is the whole finding:
#
#   LIVE      — a future fire EXECUTES this file. Portability here is load-bearing.
#               Selector: the live harness surface = .softhouse/bin/, .softhouse/guards/,
#               .softhouse/conformance.sh, .softhouse/launchd/, nexus/.
#   ARCHIVED  — an executable-shaped file under .softhouse/capture/**, .softhouse/reviews/**
#               or .softhouse/handoff/**. No live instrument EXECUTES it. It is the RECORD of
#               a drive that already happened, and its committed transcript is byte-identical
#               evidence OF IT. Rewriting it makes the transcript a lie about the file.
#               AND IT IS WORSE THAN THAT — see the invocation check below, which found that
#               conformance.sh PINS specific archived instruments BY PATH AND BY CONTENT LINE.
#               An archived instrument is therefore not inert: it is graded input to a live
#               guard. Rewriting one can turn the bar red on a host where nothing is wrong.
#   PROSE     — .md / .txt / .json / .log. Must stay byte-identical (T114 binds).
# ---------------------------------------------------------------------------

is_live() {
    case $1 in
        .softhouse/bin/*|.softhouse/guards/*|.softhouse/launchd/*|.softhouse/conformance.sh|nexus/*) return 0 ;;
        *) return 1 ;;
    esac
}
is_runnable() {
    case $1 in
        *.sh|*.py|*.zsh|*.bash) return 0 ;;
        *) return 1 ;;
    esac
}

: > "$WORK"/t256-live.txt ; : > "$WORK"/t256-arch.txt ; : > "$WORK"/t256-prose.txt ; : > "$WORK"/t256-other.txt
while IFS= read -r f; do
    [ -n "$f" ] || continue
    if is_live "$f"; then          echo "$f" >> "$WORK"/t256-live.txt
    elif is_runnable "$f"; then    echo "$f" >> "$WORK"/t256-arch.txt
    else
        case $f in
            *.md|*.txt|*.json|*.log|*.plist) echo "$f" >> "$WORK"/t256-prose.txt ;;
            *) echo "$f" >> "$WORK"/t256-other.txt ;;
        esac
    fi
done < "$WORK"/t256-union.txt

nl=$(wc -l < "$WORK"/t256-live.txt | tr -d ' ')
na=$(wc -l < "$WORK"/t256-arch.txt | tr -d ' ')
np=$(wc -l < "$WORK"/t256-prose.txt | tr -d ' ')
no=$(wc -l < "$WORK"/t256-other.txt | tr -d ' ')

echo "=== BUCKET 1 — LIVE harness (a future fire executes these): $nl ==="
cat "$WORK"/t256-live.txt
echo
echo "=== BUCKET 2 — ARCHIVED evidence instruments (no live instrument EXECUTES these): $na ==="
echo "  A TEXT SEARCH CANNOT TELL A SPECIMEN FROM A DEFECT; ONLY A READER CAN. T253's census"
echo "  said this first and it still holds. Some members below hold the Mac path ON PURPOSE,"
echo "  as the fixture they drive red — the hardcode is the thing under test, not a mistake:"
echo "    .softhouse/capture/t253-portability/instruments/30-d2-red-drive.sh    (T253's OLD_ENV_BODY)"
echo "    .softhouse/capture/t256-toolchain-population/instruments/30-portability-red-drive.sh"
echo "                                                                         (this task's two vacuity arms)"
echo "  and .softhouse/bin/go-env.sh, in BUCKET 1, carries it only inside the comment that"
echo "  records the defect T253b removed. So this count RISES when someone writes a new red"
echo "  drive, and a rise is not by itself evidence of a regression. The invariant that is"
echo "  actually graded is the LIVE-HARNESS check further down, which must read zero."
cat "$WORK"/t256-arch.txt
echo
echo "=== BUCKET 3 — PROSE / transcript records (must stay byte-identical): $np ==="
echo "  (with ONE exception, listed here and treated oppositely: .softhouse/reference-oracle.md"
echo "   is not a record of what was run, it is an INSTRUCTION for what to run. See the"
echo "   PRESCRIPTIVE SITES section at the end.)"
cat "$WORK"/t256-prose.txt
echo

# ---------------------------------------------------------------------------
# BUCKET 2's DEFINING CLAIM, PUT AT RISK. "Nothing invokes these" is the whole reason bucket 2
# must NOT be rewritten. Asserting it would be worthless, so it is measured: every bucket-2
# basename is searched for across the live harness AND the fire driver. A hit means that file
# is really LIVE, was mis-bucketed, and rewriting it is now load-bearing.
# ---------------------------------------------------------------------------
echo "=== IS ANY ARCHIVED INSTRUMENT ACTUALLY INVOKED? (the claim that licenses leaving them alone) ==="
LIVE_SURFACE=".softhouse/conformance.sh .softhouse/bin .softhouse/guards .softhouse/launchd"
invoked=0
while IFS= read -r f; do
    [ -n "$f" ] || continue
    b=$(basename "$f")
    # shellcheck disable=SC2086
    hit=$(grep -rl -F -- "$b" $LIVE_SURFACE 2>/dev/null | grep -v -F "$f" | head -3)
    if [ -n "$hit" ]; then
        echo "  INVOKED?  $b  referenced by:"
        printf '            %s\n' $hit
        invoked=$((invoked+1))
    fi
done < "$WORK"/t256-arch.txt
echo "  archived instruments referenced anywhere in the live surface: $invoked"
echo "  selector : grep -rl -F <basename> over [$LIVE_SURFACE]"
echo
echo "  READ THE HITS, DO NOT COUNT THEM. None of these is EXECUTED by the harness. They are"
echo "  CITED by it — and one form of citation is load-bearing: conformance.sh's"
echo "  HOSTSTATE_PIN_TEMP_ASSIGN_LIST pins archived instruments BY PATH AND BY THE EXACT"
echo "  ASSIGNMENT LINE they contain, and guard_no_host_state_in_lint_corpus fails when the"
echo "  repo census disagrees with the pin. So an archived instrument is graded INPUT to a"
echo "  live guard. Editing one to look portable could turn the bar red with nothing wrong."
echo "  That is a SECOND, independent reason not to touch bucket 2, and it was found by"
echo "  measuring a claim rather than asserting it."
echo
echo "  A zero here would have been a statement about THAT search over THAT surface — never a"
echo "  proof that no human will ever run one of these by hand (P-70)."
echo
echo "=== SKIPPED — matched the literal, fits no bucket above (P-40: counted, not dropped): $no ==="
if [ "$no" -eq 0 ]; then
    echo "  (none — and that is a statement about the two extension lists above, not about the world)"
else
    cat "$WORK"/t256-other.txt
fi
echo

# ---------------------------------------------------------------------------
# THE CLAIM THAT MATTERS, PUT AT RISK RATHER THAN ASSERTED:
#   "the live harness contains no executable hardcode of the Mac toolchain."
# Measured, not stated. go-env.sh's single hit is inside the comment that documents the
# defect T253b removed; the check below therefore strips comment lines before deciding.
# ---------------------------------------------------------------------------
echo "=== LIVE-HARNESS EXECUTABLE HARDCODE CHECK ==="
live_bad=0
for f in .softhouse/conformance.sh .softhouse/bin/go-env.sh .softhouse/bin/fire-program.sh \
         .softhouse/bin/build-oracle-image.sh .softhouse/bin/rehydrate-check.sh \
         .softhouse/guards/check-ledger-invariants.sh .softhouse/guards/drive-red-ledger-invariants.sh; do
    [ -f "$f" ] || { echo "  ABSENT   $f  (selector: -f test; the file is not in this checkout)"; continue; }
    # strip full-line comments, then look for the literal
    hits=$(grep -v '^[[:space:]]*#' "$f" | grep -c -F "$L1")
    hits2=$(grep -v '^[[:space:]]*#' "$f" | grep -c -F "$L2")
    tot=$(( hits + hits2 ))
    if [ "$tot" -gt 0 ]; then
        echo "  HARDCODE $f  ($tot non-comment line(s))"
        live_bad=$(( live_bad + 1 ))
    else
        echo "  clean    $f"
    fi
done
echo "  live executable hardcodes: $live_bad"
echo

# ---------------------------------------------------------------------------
# THE PRESCRIPTION. This is the site T256 calls the sharpest, and it is the one that
# MANUFACTURES new members of bucket 2: every archived instrument above exists because a
# worker read an activation line and pasted the absolute path out of it.
# ---------------------------------------------------------------------------
echo "=== HOST-PATH SITES in .softhouse/reference-oracle.md ==="
echo "  Each surviving site must be an OBSERVATION (what one host was measured to have) and"
echo "  never an INSTRUCTION (what a reader should type). Deleting the observations would"
echo "  destroy a recorded fact; leaving an instruction manufactures the next hardcode."
echo "  The instruction itself now lives between the T256-ACTIVATION-LINE markers and is"
echo "  EXECUTED by 30-portability-red-drive.sh, which asserts it names no host at all —"
echo "  so that one is graded by a drive, not by this grep."
# REPAIRED, NOT PINNED. This block used to be
#     grep -n -F "$L1" <file> || echo "  (no match for LITERAL 1 — selector: ...)"
# which is exactly the shape conformance.sh's fail-open linter refuses — and it refused
# THIS FILE for it (C2, TIER2, frontier 12 against a pin of 11, HARD guard, exit 2, and
# the run printed no oracle probe line at all). The `||` arm fires on rc=1, a MEASURED
# zero, and on rc=2, an ENGINE ERROR, printing the same reassurance for both: a negative
# the instrument did not measure. conformance.sh's own text says repair rather than pin,
# and T238's sweeplib.sh is the adoptable shape. rc is captured, classified, and an error
# ABORTS instead of being reported as an absence.
site_report() {          # site_report LABEL LITERAL
    local out rc
    out=$(grep -n -F -- "$2" .softhouse/reference-oracle.md); rc=$?
    case $rc in
        0) printf '%s\n' "$out" ;;
        1) echo "  MEASURED ZERO for $1 — grep ran over that one file and matched nothing." ;;
        *) printf 'census: grep ERRORED rc=%s looking for %s. That is NOT a no-match, and a\n' "$rc" "$1" >&2
           printf 'census: negative printed here would be one this instrument did not measure.\n' >&2
           exit 2 ;;
    esac
}
site_report "LITERAL 1" "$L1"
site_report "LITERAL 2" "$L2"
echo
echo "census: done."
