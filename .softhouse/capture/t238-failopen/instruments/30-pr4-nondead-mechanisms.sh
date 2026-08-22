#!/bin/bash
# T238 -- PR-4: is the fail-OPEN class WIDER than the dead-`cd` mechanism?
#
# Every fail-open instrument measured in transcript 20 was reached through M1 (a dead absolute
# path). PR-4 predicted the class is wider. This tests the other mechanisms DIRECTLY, using the
# EXACT idioms found in committed instruments, in a scratch corpus, so the demonstration is
# reproducible and touches nothing in the repository.
set -u
S=$(mktemp -d /tmp/t238-pr4-XXXXXX)
trap 'rm -rf "$S"' EXIT
cd "$S" || exit 90
echo "scratch corpus : $S"
echo "engines        : /usr/bin/grep BSD 2.6.0-FreeBSD | git 2.50.1 | perl 5.034001"
echo

hdr(){ echo; echo "=================================================================="; echo "$1"; echo "=================================================================="; }

# ---------------------------------------------------------------- M5
hdr "M5 -- SWALLOWED PRODUCER. The idiom is committed at reviews/T184-evidence/t184-sweep.sh:6"
echo "  sed -n '670,815p' .softhouse/conformance.sh | grep -n 'grep -[a-z]*q' || echo '   none'"
echo
echo "-- (a) the file EXISTS and contains the target: a TRUE POSITIVE"
mkdir -p .softhouse
printf 'line\n%.0s' $(seq 1 700) > .softhouse/conformance.sh
printf 'a grep -q here\n' >> .softhouse/conformance.sh
out=$( sed -n '670,815p' .softhouse/conformance.sh | grep -n 'grep -[a-z]*q' || echo "   none" ); rc=$?
printf '   exit=%s  output=%s\n' "$rc" "$(echo "$out" | tr '\n' '/')"
echo
echo "-- (b) the file DOES NOT EXIST: sed fails, the pipeline's exit is grep's, the || fires"
rm -f .softhouse/conformance.sh
out=$( sed -n '670,815p' .softhouse/conformance.sh 2>/dev/null | grep -n 'grep -[a-z]*q' || echo "   none" ); rc=$?
printf '   exit=%s  output=%s\n' "$rc" "$(echo "$out" | tr '\n' '/')"
echo "   >>> IDENTICAL SHAPE TO A TRUE NEGATIVE. exit 0. No dead cd was involved."
echo "   >>> M5 CONFIRMED: a swallowed producer is a fail-OPEN mechanism in its own right."
echo
echo "-- (c) the same idiom WITH pipefail, which is what fixes it"
out=$( set -o pipefail; sed -n '670,815p' .softhouse/conformance.sh 2>/dev/null | grep -n 'grep -[a-z]*q' ); rc=$?
printf '   exit=%s  (non-zero: the producer failure now propagates)\n' "$rc"

# ---------------------------------------------------------------- M3
hdr "M3 -- EMPTY GLOB. A glob that matches nothing is passed through LITERALLY by the shell."
mkdir -p corpus && printf 'the population is closed\n' > corpus/a.md
echo "-- (a) glob matches: TRUE POSITIVE"
out=$(/usr/bin/grep -l 'population is closed' corpus/*.md 2>&1); rc=$?
printf '   exit=%s  out=%s\n' "$rc" "$out"
echo "-- (b) glob matches NOTHING (wrong extension): the literal 'corpus/*.txt' is passed to grep"
out=$(/usr/bin/grep -l 'population is closed' corpus/*.txt 2>&1 || echo "   (no hits)"); rc=$?
printf '   exit=%s  out=%s\n' "$rc" "$out"
echo "   >>> with the || arm, exit 0 and '(no hits)'. M3 CONFIRMED."

# ---------------------------------------------------------------- M4
hdr "M4 -- EMPTY FOR-LIST. 'for f in \$(producer)' over an empty producer runs the body ZERO times."
echo "-- (a) producer yields files"
n=0; for f in $(ls corpus/*.md 2>/dev/null); do n=$((n+1)); done
printf '   iterations=%s  -> the sweep reports on %s file(s)\n' "$n" "$n"
echo "-- (b) producer yields NOTHING"
n=0; for f in $(ls corpus/*.txt 2>/dev/null); do n=$((n+1)); done
printf '   iterations=%s  -> the sweep reports on %s file(s), prints its summary, EXITS 0\n' "$n" "$n"
echo "   >>> 'I checked 0 files and found 0 problems' is indistinguishable from 'I checked"
echo "   >>> everything and it is clean' unless the DENOMINATOR is printed and asserted."
echo "   >>> M4 CONFIRMED."

# ---------------------------------------------------------------- M6
hdr "M6 -- MISSING ENGINE. ugrep is ABSENT here; rg is a Claude-Code shell function a script"
echo "     cannot see. A command-not-found under a || arm is a fail-OPEN."
out=$( ugrep -n 'population is closed' corpus/a.md 2>/dev/null || echo "   (no hits)" ); rc=$?
printf '   ugrep ...    || echo   exit=%s  out=%s\n' "$rc" "$out"
out=$( rg -n 'population is closed' corpus/a.md 2>/dev/null || echo "   (no hits)" ); rc=$?
printf '   rg ...       || echo   exit=%s  out=%s\n' "$rc" "$out"
out=$( /usr/bin/grep -P 'population' corpus/a.md 2>/dev/null || echo "   (no hits)" ); rc=$?
printf '   grep -P ...  || echo   exit=%s  out=%s\n' "$rc" "$out"
echo "   >>> THREE engines, THREE identical '(no hits)' at exit 0, over a corpus that CONTAINS"
echo "   >>> the string. M6 CONFIRMED, and it needs no dead path at all."

# ---------------------------------------------------------------- verdict
hdr "PR-4 VERDICT"
echo "PR-4 predicted at least ONE fail-open mechanism that is not a dead worktree path."
echo "MEASURED: FOUR -- M3 empty glob, M4 empty for-list, M5 swallowed producer, M6 missing engine."
echo "PR-4 CONFIRMED. The class is not the dead cd; the dead cd is one entry point to it."
echo
echo "THE INVARIANT ALL FOUR VIOLATE, and the one a fix must restore:"
echo "  AN INSTRUMENT MUST NOT BE ABLE TO EMIT A NEGATIVE IT DID NOT MEASURE."
echo "  Equivalently: 'zero hits' and 'zero corpus' and 'no engine' must have DIFFERENT exit codes."
