#!/usr/bin/env bash
# T183 — regenerate every probe in this directory.  bash, never sh.
#
# SAFETY.  Nothing here executes a file from the reviewed population.  The
# fixtures in fixtures-INERT/ carry a `.py.txt` extension precisely so that no
# sweep enumerates them and no shell can run them by accident; this script
# copies them into a scratch directory under $TMPDIR with a `.py` name, runs
# only the CLASSIFIER (which parses, never executes) over that scratch copy,
# and deletes it.  `docs/adr/` and `nexus/` are never a working directory here.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
GC="$REPO/.softhouse/reviews/t179-guard-classifier/guard_classify.py"
ST="$REPO/.softhouse/reviews/t179-guard-classifier/selftest.py"
HERE="$REPO/.softhouse/reviews/T183-evidence"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/t183.XXXXXX")"
trap 'rm -rf "$SCRATCH"' EXIT

echo "=== T183 probe transcript"
echo "repo            : $REPO"
echo "classifier under review : $GC"
echo "DEC-1  sha256   : $(shasum -a 256 "$REPO/docs/adr/DEC-1-schedule-generator-adapter.md" | cut -d' ' -f1)"
echo "contract.go sha : $(shasum -a 256 "$REPO/nexus/internal/apps/loanschedule/contract/contract.go" | cut -d' ' -f1)"
echo

# ---------------------------------------------------------------- PROBE 1
echo "### PROBE 1 — does the classifier follow IMPORTS?"
echo "Two fixtures whose mutation is LOCAL and whose guard lives ENTIRELY in an"
echo "imported module (a real restoring @contextmanager, and a real atexit restore)."
echo "Correct answer: GUARDED.  Expected defect: UNGUARDED."
mkdir -p "$SCRATCH/imp"
cp "$HERE/fixtures-INERT/mylib_guard.py.txt"          "$SCRATCH/imp/mylib_guard.py"
cp "$HERE/fixtures-INERT/green_imported_cm.py.txt"    "$SCRATCH/imp/green_imported_cm.py"
cp "$HERE/fixtures-INERT/green_imported_atexit.py.txt" "$SCRATCH/imp/green_imported_atexit.py"
python3 "$GC" --root "$SCRATCH/imp" --enforce
echo "PROBE 1 exit=$?"
echo

# ---------------------------------------------------------------- PROBE 2
echo "### PROBE 2 — bare \`assert\` under python3 -O"
echo "A file whose ONLY protection is a bare assert.  Correct answer: UNGUARDED."
mkdir -p "$SCRATCH/asrt"
cp "$HERE/fixtures-INERT/assert_only.py.txt" "$SCRATCH/asrt/assert_only.py"
python3 "$GC" --root "$SCRATCH/asrt" --enforce
echo "PROBE 2 exit=$?"
echo "ast.Assert nodes in each T179 script (0 everywhere => -O cannot neuter them):"
python3 - "$REPO" <<'PY'
import ast, os, sys
d = os.path.join(sys.argv[1], ".softhouse/reviews/t179-guard-classifier")
for f in sorted(x for x in os.listdir(d) if x.endswith(".py")):
    t = ast.parse(open(os.path.join(d, f), encoding="utf-8").read())
    n = [x.lineno for x in ast.walk(t) if isinstance(x, ast.Assert)]
    print("    %-28s ast.Assert nodes: %d %s" % (f, len(n), n))
PY
echo "selftest under python3 -O:"
python3 -O "$ST" >/dev/null 2>&1
echo "    exit=$?  (0 = still passes; the interesting case is PROBE 4)"
echo

# ---------------------------------------------------------------- PROBE 3
echo "### PROBE 3 — the FAIL-OPEN population hole"
echo "The three t41-probe rewriters whose write target is a FUNCTION PARAMETER."
echo "All three truncate the ratified DEC-1 in place with no handler; two of them"
echo "also truncate the frozen contract.go.  Correct --enforce answer: exit 1."
mkdir -p "$SCRATCH/fo"
cp "$REPO/.softhouse/reviews/t41-probe/edit18.py" \
   "$REPO/.softhouse/reviews/t41-probe/edit20.py" \
   "$REPO/.softhouse/reviews/t41-probe/edit21.py" "$SCRATCH/fo/"
python3 "$GC" --root "$SCRATCH/fo" --enforce
echo "PROBE 3 exit=$?   <-- 0 means FAIL-OPEN"
echo

# ---------------------------------------------------------------- PROBE 4
echo "### PROBE 4 — is the selftest NON-VACUOUS?  Sabotage in BOTH directions."
for MODE in always-guarded never-guarded; do
  rm -rf "$SCRATCH/$MODE"
  cp -R "$REPO/.softhouse/reviews/t179-guard-classifier" "$SCRATCH/$MODE"
  python3 - "$SCRATCH/$MODE/guard_classify.py" "$MODE" <<'PY'
import sys
p, mode = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
if mode == "always-guarded":
    old = "        child = cur\n        cur = parents.get(cur)\n    return None\n\n\ndef _in_body(child, body):"
    new = ("        child = cur\n        cur = parents.get(cur)\n"
           "    root = node\n"
           "    while parents.get(root) is not None:\n"
           "        root = parents.get(root)\n"
           "    for n in ast.walk(root):\n"
           "        if isinstance(n, ast.Try) and n.finalbody:\n"
           "            return n\n"
           "    return None\n\n\ndef _in_body(child, body):")
    assert old in s, "anchor 1 moved"
    s = s.replace(old, new, 1)
else:
    for a, b in [
        ('def enclosing_try_finally(node, parents):\n    """',
         'def enclosing_try_finally(node, parents):\n    return None\n    """'),
        ('def enclosing_restoring_with(node, parents, local_cms):\n',
         'def enclosing_restoring_with(node, parents, local_cms):\n    return None, None\n'),
        ('def indirectly_guarded_funcs(tree, parents):\n    """',
         'def indirectly_guarded_funcs(tree, parents):\n    return set()\n    """'),
    ]:
        assert a in s, "anchor moved: %r" % a[:48]
        s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8").write(s)
print("    sabotage applied: %s" % mode)
PY
  python3 "$SCRATCH/$MODE/selftest.py" > "$SCRATCH/$MODE.out" 2>&1
  echo "    selftest vs $MODE classifier      : exit=$?  (1 = the instrument CAN fail)"
  grep -c 'FAIL' "$SCRATCH/$MODE.out" | sed 's/^/    FAIL lines: /'
  python3 -O "$SCRATCH/$MODE/selftest.py" >/dev/null 2>&1
  echo "    same under python3 -O             : exit=$?  (1 = -O does not neuter it)"
done
echo

# ---------------------------------------------------------------- PROBE 5
echo "### PROBE 5 — non-vacuity (P-35): zero files inspected must be an ERROR"
mkdir -p "$SCRATCH/empty"
python3 "$GC" --root "$SCRATCH/empty" >/dev/null 2>&1
echo "    empty root exit=$?  (3 = error, not a pass)"
echo

# ---------------------------------------------------------------- PROBE 6
echo "### PROBE 6 — does the classifier misclassify ITSELF?"
python3 "$GC" --file "$GC" 2>&1 | sed -n '/MUTATION SITES/,$p'
echo

echo "DEC-1  sha256 after : $(shasum -a 256 "$REPO/docs/adr/DEC-1-schedule-generator-adapter.md" | cut -d' ' -f1)"
echo "contract.go   after : $(shasum -a 256 "$REPO/nexus/internal/apps/loanschedule/contract/contract.go" | cut -d' ' -f1)"
