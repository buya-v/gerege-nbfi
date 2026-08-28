#!/usr/bin/env bash
# T278 -- META-CALIBRATION of T277's verifier, run by the REVIEWER, not by its author.
#
# FU-T277-5 says: "a negative test can pass for the wrong reason -- a mutant that
# fails to BUILD scores a trip it did not earn, because a crash and a caught
# defect are both non-zero exits", and claims the defect is FIXED in
# verify_t277.sh's mutate().  "I fixed it" needs a transcript.  Built from outside:
#
#   B1  a mutation whose ANCHOR HAS MOVED, so the edit no-ops   -> must ABORT (2)
#   B2  a negative case repointed at `true`, which cannot fail  -> must be caught
#   B3  DOES EACH DELIVERED MUTANT ACTUALLY BUILD AND RUN?  i.e. does it trip
#       because the instrument GRADED a defect, or because python crashed?
#       This is FU-T277-5's own generalisation, and it is STRICTLY STRONGER than
#       what mutate() enforces.
#
# NOTE ON METHOD: verify_t277.sh resolves SRC from its OWN directory, so a copy
# of the script alone cannot find the instruments.  The whole src/ directory is
# therefore copied to scratch and the COPY of verify_t277.sh is mutated, with
# $ROOT still pointing at the real repository so the data is unchanged.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SRC="$ROOT/.softhouse/capture/t277-shapelaw-salvage/src"
W="$(mktemp -d "${TMPDIR:-/tmp}/t278-meta.XXXXXX")"
trap 'rm -rf "$W"' EXIT
echo "T278 META-CALIBRATION of T277's verifier   root=$ROOT"
echo

# ---------------------------------------------------------------- B1
echo "B1  M1's mutation anchor REPOINTED so the edit no-ops -- must ABORT, not 'trip'"
mkdir -p "$W/b1"
cp "$SRC"/*.py "$SRC"/verify_t277.sh "$W/b1/"
python3 - "$W/b1/verify_t277.sh" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()
old_count = 'n = text.count("\\"lawII_holds_on_factA\\": 213")'
old_assert = 'assert n == 1, "expected exactly one t229corpus pin of 213, found %d" % n'
old_repl = ('text = text.replace("\\"lawII_holds_on_factA\\": 213", '
            '"\\"lawII_holds_on_factA\\": 220")')
for s in (old_count, old_assert, old_repl):
    assert t.count(s) == 1, "B1 could not find: " + s
# Simulate the real-world failure: the pin moved, so the anchor is absent.
# The mutation's own assert is ALSO removed, so nothing but mutate()'s no-op
# guard stands between this and a false green.
t = t.replace(old_count, 'n = 1')
t = t.replace(old_assert, 'pass')
t = t.replace(old_repl, 'text = text.replace("PIN-THAT-MOVED-AWAY", "x")')
open(p, "w").write(t)
PY
bash "$W/b1/verify_t277.sh" "$ROOT" > "$W/b1.txt" 2>&1
B1=$?
echo "    exit=$B1"
grep -E 'ABORT|no-op|byte-identical|DID NOT TRIP|FAIL-CASE|VERIFY:' "$W/b1.txt" | sed 's/^/      /'
if [ "$B1" -eq 2 ]; then echo "    B1 RESULT: ABORTED as required (exit 2) -- FU-T277-5's fix HOLDS"
else echo "    B1 RESULT: *** did NOT abort (exit $B1) -- FALSE GREEN ***"; fi
echo

# ---------------------------------------------------------------- B2
echo "B2  a negative case repointed at \`true\` -- verifier must report DID NOT TRIP"
mkdir -p "$W/b2"
cp "$SRC"/*.py "$SRC"/verify_t277.sh "$W/b2/"
python3 - "$W/b2/verify_t277.sh" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()
old = ('fail_case "M4 cross-check: I1q read from the schedule instead of computed" \\\n'
       '    python3 "$SRC/crosscheck_seven_t277b.py" "$ROOT" --i1q-from-row')
assert t.count(old) == 1, "B2 could not find M4's fail_case"
t = t.replace(old, 'fail_case "M4 (B2-NEUTERED: pointed at true)" true')
open(p, "w").write(t)
PY
bash "$W/b2/verify_t277.sh" "$ROOT" > "$W/b2.txt" 2>&1
B2=$?
echo "    exit=$B2"
grep -E 'DID NOT TRIP|VERIFY:' "$W/b2.txt" | sed 's/^/      /'
if [ "$B2" -eq 1 ] && grep -q 'DID NOT TRIP' "$W/b2.txt"; then
  echo "    B2 RESULT: caught the un-failable negative and named it"
else
  echo "    B2 RESULT: *** exit $B2 without a DID NOT TRIP line ***"; fi
echo

# ---------------------------------------------------------------- B3
echo "B3  DID EACH MUTANT ACTUALLY BUILD?  a crash and a catch share an exit code."
build_and_probe() {   # label, srcfile, dest, python-edit, args...
    local label="$1" f="$2" d="$3" edit="$4"
    cp "$SRC/$f" "$W/$d"
    python3 - "$W/$d" <<PYEOF
import sys
path = sys.argv[1]
text = open(path).read()
$edit
open(path, "w").write(text)
PYEOF
    if python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$W/$d" 2>/dev/null; then
        echo "    $label  PARSES: yes"
    else
        echo "    $label  PARSES: *** NO -- this mutant cannot build ***"
    fi
    shift 4
    python3 "$W/$d" "$@" > "$W/$d.out" 2>&1
    local rc=$?
    if grep -qE 'Traceback \(most recent call last\)' "$W/$d.out"; then
        local last
        last="$(grep -E '^[A-Za-z_.]*(Error|Exception)' "$W/$d.out" | tail -1)"
        echo "    $label  exit=$rc  ended in a PYTHON TRACEBACK: ${last:-<unnamed>}"
        echo "             -> an UNEARNED trip unless the instrument raised deliberately."
    else
        echo "    $label  exit=$rc  no traceback; the instrument GRADED it. tail:"
        tail -3 "$W/$d.out" | sed 's/^/               /'
    fi
}

build_and_probe "M1" shapelaw_census_t277.py m1.py '
n = text.count("\"lawII_holds_on_factA\": 213")
assert n == 1
text = text.replace("\"lawII_holds_on_factA\": 213", "\"lawII_holds_on_factA\": 220")
' "$ROOT" --report

build_and_probe "M2" shapelaw_census_t277.py m2.py '
assert "T159-R600p0-N2000-B999" in text
text = "".join(l for l in text.splitlines(True) if "T159-R600p0-N2000-B999" not in l)
' "$ROOT" --report

build_and_probe "M3" crosscheck_seven_t277b.py m3.py '
old = "(\"T159-R600p0-N2000-B999\", 2000, 999, 499, 500, 1, 0, 166),"
assert text.count(old) == 1
text = text.replace(old, "(\"T159-R600p0-N2000-B999\", 2000, 999, 499, 500, 1, 0, 165),")
' "$ROOT"

echo
echo "T278 META-CALIBRATION complete."
