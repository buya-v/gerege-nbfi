#!/usr/bin/env bash
# T277 -- ONE COMMAND that re-runs every claim this directory makes, including
# the ones that MUST FAIL.
#
#   bash .softhouse/capture/t277-shapelaw-salvage/src/verify_t277.sh [repo-root]
#
# Exit 0 only when: both instruments self-test clean, both censuses reproduce
# every pin, and all four deliberate mutations trip. Any other outcome is a
# non-zero exit and a named line.
#
# WHY: "a guard that only works when someone remembers to run it enforces
# nothing" is this program's most repeated lesson. There is now one command,
# and it grades its own negatives -- a guard that cannot fail proves nothing.
#
# Contacts no oracle. Reads no vector. Touches no file in the repository: the
# mutants are written to a scratch directory under $TMPDIR and deleted.

set -u
set -o pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t277-verify.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

FAILURES=0

pass_case() {   # name, command...  -- must exit 0
    local name="$1"; shift
    if "$@" > "$WORK/out.txt" 2>&1; then
        echo "  PASS-CASE  ok    $name"
    else
        echo "  PASS-CASE  FAIL  $name  (expected exit 0, got $?)"
        sed 's/^/      | /' "$WORK/out.txt" | tail -20
        FAILURES=$((FAILURES + 1))
    fi
}

fail_case() {   # name, command...  -- must exit NON-zero
    local name="$1"; shift
    if "$@" > "$WORK/out.txt" 2>&1; then
        echo "  FAIL-CASE  DID NOT TRIP  $name  (expected non-zero, got 0)"
        sed 's/^/      | /' "$WORK/out.txt" | tail -20
        FAILURES=$((FAILURES + 1))
    else
        echo "  FAIL-CASE  tripped  $name"
    fi
}

# A mutant that fails to BUILD would make its fail_case "trip" for the wrong
# reason -- a false green, and exactly the failure mode this whole task is about.
# So mutate() is FATAL: if the copy or the edit does not succeed, the run aborts
# rather than scoring a trip it did not earn.
mutate() {      # source-file, dest-file, python-edit-source
    if ! cp "$SRC/$1" "$WORK/$2"; then
        echo "  ABORT: could not copy $SRC/$1 -- a mutant that cannot be built"
        echo "         would score a FAIL-CASE trip it did not earn."
        exit 2
    fi
    if ! python3 - "$WORK/$2" <<PYEOF
import sys
path = sys.argv[1]
text = open(path).read()
$3
open(path, "w").write(text)
PYEOF
    then
        echo "  ABORT: mutation of $2 did not apply -- its anchor has moved."
        echo "         A mutation that silently no-ops proves nothing."
        exit 2
    fi
    # A no-op edit is also a false green: the "mutant" would be the original.
    if cmp -s "$SRC/$1" "$WORK/$2"; then
        echo "  ABORT: mutant $2 is byte-identical to $1 -- the edit was a no-op."
        exit 2
    fi
}

echo "T277 verify -- repo root: $ROOT"
echo
echo "POSITIVE: the instruments must self-test and reproduce every pin."
pass_case "census --selftest"        python3 "$SRC/shapelaw_census_t277.py" --selftest
pass_case "census both scopes"       python3 "$SRC/shapelaw_census_t277.py" "$ROOT" --report
pass_case "seven-cell row dump"      python3 "$SRC/dump_seven_t277.py" "$ROOT"
pass_case "cross-check --selftest"   python3 "$SRC/crosscheck_seven_t277b.py" --selftest
pass_case "cross-check t229corpus"   python3 "$SRC/crosscheck_seven_t277b.py" "$ROOT"

echo
echo "NEGATIVE: each of these MUST trip. A guard that cannot fail proves nothing."

# M1 -- the cloud T241's exact claim: law (ii) sound on the whole FACT-A domain.
mutate shapelaw_census_t277.py m1.py '
n = text.count("\"lawII_holds_on_factA\": 213")
assert n == 1, "expected exactly one t229corpus pin of 213, found %d" % n
text = text.replace("\"lawII_holds_on_factA\": 213", "\"lawII_holds_on_factA\": 220")
'
fail_case "M1 census: law (ii) pinned 220/220 on FACT A (df0aed2c's claim)" \
    python3 "$WORK/m1.py" "$ROOT" --report

# M2 -- the sharpest counterexample dropped from the expected exception set.
mutate shapelaw_census_t277.py m2.py '
assert "T159-R600p0-N2000-B999" in text
text = "".join(l for l in text.splitlines(True) if "T159-R600p0-N2000-B999" not in l)
'
fail_case "M2 census: T159-R600p0-N2000-B999 dropped from the exception set" \
    python3 "$WORK/m2.py" "$ROOT" --report

# M3 -- the cross-check off by ONE MINOR UNIT on the same cell.
mutate crosscheck_seven_t277b.py m3.py '
old = "(\"T159-R600p0-N2000-B999\", 2000, 999, 499, 500, 1, 0, 166),"
assert text.count(old) == 1
text = text.replace(old, "(\"T159-R600p0-N2000-B999\", 2000, 999, 499, 500, 1, 0, 165),")
'
fail_case "M3 cross-check: 165 minor units expected where 166 is measured" \
    python3 "$WORK/m3.py" "$ROOT"

# M4 -- the I1q trap: delta read from row 1's clipped `interest` field.
fail_case "M4 cross-check: I1q read from the schedule instead of computed" \
    python3 "$SRC/crosscheck_seven_t277b.py" "$ROOT" --i1q-from-row

echo
if [ "$FAILURES" -eq 0 ]; then
    echo "T277 VERIFY: PASS -- every pin reproduced and every negative tripped."
    exit 0
fi
echo "T277 VERIFY: FAIL -- $FAILURES case(s) did not behave as required."
exit 1
