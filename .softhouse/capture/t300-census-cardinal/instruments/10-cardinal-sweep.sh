#!/usr/bin/env bash
# T300 — SWEEP: every HARD-CODED CARDINAL that conformance.sh PRINTS.
#
# The defect T300 was filed for is P-80's shape — "A CORRECTED CARDINAL ROTS IN EVERY PLACE IT
# WAS RESTATED. The count is the same defect as the line number." — occurring inside the
# host-state census: the guard printed `18, pinned at 17` on every run, pass or fail, because
# `17` was a literal typed beside an 18-row list whose length is derivable.
#
# This instrument does not answer "is 17 wrong". It answers the wider question the brief asks:
# WHERE ELSE in conformance.sh is a cardinal typed rather than derived, and printed. It reports
# the POPULATION and the SELECTOR that produced it, so "not found" is a statement about the
# search and never about the world (P-66/P-70).
#
# FAIL-CLOSED. Every selector below must match at least one line. A selector that matches zero
# in a 2,900-line file is a broken selector, not a clean file (P-35), and this script exits 1
# rather than printing a reassuring empty list. There is no `|| true` and no `|| echo "(none)"`
# anywhere in it: `grep` exits 1 on NO MATCH and >1 on ERROR (P-81), and those two are read
# apart, never collapsed onto one printed zero.
#
# NO PIPELINE with an early-exiting consumer (P-57 — "under pipefail, any early-exiting consumer
# — grep -q, head, sed q — poisons the pipeline status"). Every read here is grep/sed over a
# FILE, and counts come from `grep -c`, which drains its input.
set -u

ROOT="$(git rev-parse --show-toplevel)"
rc=$?
if [ "$rc" -ne 0 ] || [ -z "$ROOT" ]; then
  echo "SWEEP REFUSED: not inside a git worktree (git rev-parse exit $rc)." >&2
  exit 1
fi
SUBJECT="$ROOT/.softhouse/conformance.sh"
if [ ! -f "$SUBJECT" ]; then
  echo "SWEEP REFUSED: subject absent: $SUBJECT" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# SELECTOR 1 — the PRINT population. A statement whose first word is say/warn/echo/printf.
# ---------------------------------------------------------------------------
SEL_PRINT='^[[:space:]]*(say|warn|echo|printf)[[:space:]]'
prints="$(LC_ALL=C grep -cE "$SEL_PRINT" "$SUBJECT")"
rc=$?
if [ "$rc" -gt 1 ]; then echo "SWEEP REFUSED: selector 1 errored ($rc)." >&2; exit 1; fi
if [ "${prints:-0}" -lt 1 ]; then
  echo "SWEEP REFUSED: selector 1 matched ZERO print statements in $SUBJECT. Broken selector." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# SELECTOR 2 — a DECIMAL INTEGER LITERAL inside a print statement. The exclusions are named
# rather than silent, because each one is a claim about what is NOT a cardinal:
#   P-nn / T-nn / Tnnn / A2-nn / C-nn / I-nn / DEC-n / FU-Tnnn   ids, not counts (P-86)
#   $VAR / ${VAR} / $((...))                                     already derived
# The exclusions are applied by a SECOND grep over the matched set, so both figures print and
# the reader can see how many lines each exclusion removed.
# ---------------------------------------------------------------------------
SEL_INT='[^A-Za-z0-9_$]([0-9]+)([^A-Za-z0-9_]|$)'
SEL_ID='([PTIC]-[0-9]|A2-[0-9]|DEC-[0-9]|FU-T[0-9]|\bT[0-9]{2,3}\b|P-[0-9]{2})'

hits="$ROOT/.softhouse/capture/t300-census-cardinal/evidence/10-sweep-hits.txt"
LC_ALL=C grep -nE "$SEL_PRINT" "$SUBJECT" >"$hits.stage1"
rc=$?
if [ "$rc" -gt 1 ]; then echo "SWEEP REFUSED: stage 1 errored ($rc)." >&2; exit 1; fi
LC_ALL=C grep -E "$SEL_INT" "$hits.stage1" >"$hits.stage2"
rc=$?
if [ "$rc" -gt 1 ]; then echo "SWEEP REFUSED: stage 2 errored ($rc)." >&2; exit 1; fi
LC_ALL=C grep -vE "$SEL_ID" "$hits.stage2" >"$hits"
rc=$?
if [ "$rc" -gt 1 ]; then echo "SWEEP REFUSED: stage 3 errored ($rc)." >&2; exit 1; fi

n1="$(LC_ALL=C grep -c '' "$hits.stage1")"
n2="$(LC_ALL=C grep -c '' "$hits.stage2")"
n3="$(LC_ALL=C grep -c '' "$hits")"

# The subject's own size is DERIVED and then REUSED below, rather than counted once and
# retyped in the prose. This instrument found the defect it is named for by looking for exactly
# that shape, and its first draft carried it: the closing paragraph said "all 2.9k lines" as a
# typed approximation of a figure two screens above it. P-81's lesson, unedited — "Writing the
# rule does not immunise you against it; only the guard does."
subject_lines="$(LC_ALL=C grep -c '' "$SUBJECT")"

echo "T300 CARDINAL SWEEP — subject: .softhouse/conformance.sh"
echo "  subject lines            : $subject_lines"
echo "  SELECTOR 1 (print stmts) : $SEL_PRINT"
echo "  print statements         : $n1"
echo "  SELECTOR 2 (int literal) : $SEL_INT"
echo "  ... carrying an integer  : $n2"
echo "  SELECTOR 3 (id exclusion): -v $SEL_ID"
echo "  ... after id exclusion   : $n3"
echo ""
echo "THE POPULATION (line:text) ------------------------------------------------"
LC_ALL=C sed -n '1,200p' "$hits"
echo "---------------------------------------------------------------------------"
echo ""

# ---------------------------------------------------------------------------
# SELECTOR 4 — the narrow shape: a cardinal printed BESIDE a collection whose length the
# script can compute. `pinned at <literal>` is the exact spelling the two census guards use.
# ---------------------------------------------------------------------------
SEL_PINNED='pinned at [0-9]'
pinned="$(LC_ALL=C grep -ncE "$SEL_PINNED" "$SUBJECT")"
rc=$?
if [ "$rc" -gt 1 ]; then echo "SWEEP REFUSED: selector 4 errored ($rc)." >&2; exit 1; fi
echo "SELECTOR 4 (literal beside a pin) : $SEL_PINNED"
echo "  matches                         : ${pinned:-0}"
if [ "${pinned:-0}" -gt 0 ]; then
  LC_ALL=C grep -nE "$SEL_PINNED" "$SUBJECT"
fi
echo ""

# ---------------------------------------------------------------------------
# CALIBRATION (P-72 — "a sweep is an INSTRUMENT; calibrate it on a known positive before you
# report its negatives"). The known positive is the defect this task was filed for. If the
# selector cannot see the literal `17` that the pre-fix file printed, its negatives are worth
# nothing. After the repair the literal is gone, so the calibration is run against a
# SYNTHETIC line carrying the pre-fix spelling, not against the repaired file.
# ---------------------------------------------------------------------------
cal="$ROOT/.softhouse/capture/t300-census-cardinal/evidence/10-sweep-calibration.txt"
{
  echo '  say "conformance:   literal /tmp, /private/tmp or /var/tmp path to a name: $m, pinned at 17."'
  echo '  say "conformance:   $REPO_ROOT (git ls-files, whole repository); frontier $n, pinned at 11."'
} >"$cal"
c1="$(LC_ALL=C grep -cE "$SEL_PRINT" "$cal")"
c2="$(LC_ALL=C grep -cE "$SEL_PINNED" "$cal")"
echo "CALIBRATION on the two PRE-FIX spellings (P-72):"
echo "  selector 1 sees          : $c1 / 2"
echo "  selector 4 sees          : $c2 / 2"
if [ "${c1:-0}" -ne 2 ] || [ "${c2:-0}" -ne 2 ]; then
  echo "SWEEP REFUSED: the selectors do not see the KNOWN POSITIVE. Their negatives prove nothing." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# SELECTOR 5 — a cardinal SPELLED IN WORDS beside a counted noun. Selectors 2-4 are blind to
# this: they hunt digits. The blindness was not theoretical — `conformance.sh` carried
# "the seventeen rows below" as a comment about the SAME 18-row pin whose `pinned at 17` this
# task was filed for, and only this selector could see it. A second currency for the same
# defect, exactly as P-80 records ("Same defect, two currencies").
# ---------------------------------------------------------------------------
SEL_WORD='\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty)\b[[:space:]]+(rows|sites|lines|files|instruments|members|entries)'
words="$(LC_ALL=C grep -ciE "$SEL_WORD" "$SUBJECT")"
rc=$?
if [ "$rc" -gt 1 ]; then echo "SWEEP REFUSED: selector 5 errored ($rc)." >&2; exit 1; fi
echo "SELECTOR 5 (cardinal spelled in words) : $SEL_WORD"
echo "  matches                              : ${words:-0}"
if [ "${words:-0}" -gt 0 ]; then
  LC_ALL=C grep -niE "$SEL_WORD" "$SUBJECT"
fi
echo ""

# ---------------------------------------------------------------------------
# CLASSIFICATION of the selector-3 survivors, MEASURED rather than tallied by hand. Every
# survivor must land in exactly one bucket and the buckets must sum to the population; if they
# do not, this script says so rather than printing a table that does not add up. P-46's rule:
# a figure in a handoff is a claim, and it must be diffable against the artefact.
# ---------------------------------------------------------------------------
B_STATUS='EXIT [0-9]|exit [0-9]|exit \$|wanted [0-9]|neither its clean \([0-9]\)|exits [0-9]|>[0-9] is an ERROR|is this guard.s own code|never becomes 0|requires exactly 1'
B_FIXTURE='\|\| (ok|note)[0-9]|CENSUS ascending|\[0-9\]|\[1-9\]'
B_VERSION='go 1\.[0-9]'
B_POSITIONAL='\$\{3:-|gate G-[0-9]'
cstatus="$(LC_ALL=C grep -cE "$B_STATUS" "$hits")"
rest="$hits.rest"
LC_ALL=C grep -vE "$B_STATUS" "$hits" >"$rest"
cfix="$(LC_ALL=C grep -cE "$B_FIXTURE" "$rest")"
LC_ALL=C grep -vE "$B_FIXTURE" "$rest" >"$rest.2"
cver="$(LC_ALL=C grep -cE "$B_VERSION" "$rest.2")"
LC_ALL=C grep -vE "$B_VERSION" "$rest.2" >"$rest.3"
cpos="$(LC_ALL=C grep -cE "$B_POSITIONAL" "$rest.3")"
LC_ALL=C grep -vE "$B_POSITIONAL" "$rest.3" >"$rest.4"
cunc="$(LC_ALL=C grep -c '' "$rest.4")"
echo "CLASSIFICATION of the $n3 survivors (each bucket's selector printed beside its figure):"
echo "  exit/status code in prose  : $cstatus   [$B_STATUS]"
echo "  self-test fixture or regex : $cfix   [$B_FIXTURE]"
echo "  toolchain version          : $cver   [$B_VERSION]"
echo "  positional param / gate id : $cpos   [$B_POSITIONAL]"
echo "  UNCLASSIFIED               : $cunc   <- any of these is a candidate for the defect"
if [ "$cunc" -gt 0 ]; then
  echo "  the unclassified lines:"
  LC_ALL=C sed -n '1,40p' "$rest.4"
fi
sum=$((cstatus + cfix + cver + cpos + cunc))
if [ "$sum" -ne "$n3" ]; then
  echo "SWEEP REFUSED: the buckets sum to $sum but the population is $n3. A table that does not" >&2
  echo "add up is worse than no table: it looks measured. Fix the buckets, not the prose." >&2
  rm -f "$rest" "$rest.2" "$rest.3" "$rest.4"
  exit 1
fi
rm -f "$rest" "$rest.2" "$rest.3" "$rest.4"
echo ""

rm -f "$hits.stage1" "$hits.stage2"
echo ""
echo "WHERE THIS LOOKED, AND WHERE IT DID NOT:"
echo "  looked : every print statement in .softhouse/conformance.sh, whole file, all $subject_lines lines."
echo "  did NOT: the guards' own binaries (ledgerguard, the fail-open linter), the capture rigs,"
echo "           and every other tracked .sh/.py. A cardinal printed by a SUBPROCESS of this bar"
echo "           is out of this sweep's population, and 'not found' here says nothing about them."
exit 0
