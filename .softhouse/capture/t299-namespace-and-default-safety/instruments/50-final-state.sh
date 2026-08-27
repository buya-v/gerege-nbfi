#!/usr/bin/env bash
# T299 -- THE TWO STATES THE TASK ASKED TO BE SHOWN, on the COMMITTED tree.
#
#   1. the collision-safe state          -> the namespace guard is green and names the owner
#   2. the bare invocation is safe       -> `git status --porcelain` is byte-identical across it
#
# ENGINE (P-33/P-53): bash, git 2.50.x, python3; versions printed. No pattern engine is used
# for a negative claim here -- the comparison is `diff -u` over two full porcelain listings,
# so nothing rests on a regex matching nothing.
#
# CALIBRATION (P-72): the tree must be COMMITTED-CLEAN before the bare run, otherwise "no new
# dirty path" is a claim about a tree that was already dirty and the arm proves nothing. A
# dirty starting tree ABORTS.
set -u

ROOT="$(git rev-parse --show-toplevel)" || exit 2
[ -n "$ROOT" ] || exit 2
cd "$ROOT" || exit 2

echo "T299 FINAL STATE"
echo "engine    : $(bash --version | head -1)"
echo "          : $(git --version) | $(python3 --version 2>&1)"
echo "HEAD      : $(git rev-parse HEAD)"
echo "branch    : $(git rev-parse --abbrev-ref HEAD)"
echo

echo "=== CALIBRATION: the tree is committed-clean before anything is run ==="
git status --porcelain >"${TMPDIR:-/tmp}/t299-final-before.$$"
n="$(grep -ac '' "${TMPDIR:-/tmp}/t299-final-before.$$" || true)"
[ -n "$n" ] || n=0
echo "  dirty paths at start : $n"
if [ "$n" -ne 0 ]; then
  echo "  ABORT(2): the tree is dirty at start, so 'the bare run adds no dirty path' would be"
  echo "  a claim about a tree that was already dirty. Commit first."
  cat "${TMPDIR:-/tmp}/t299-final-before.$$"
  rm -f "${TMPDIR:-/tmp}/t299-final-before.$$"
  exit 2
fi
echo

echo "=== 1. THE COLLISION-SAFE STATE ==="
echo "  directories carrying the t256 prefix, and who actually owns each:"
git ls-files >"${TMPDIR:-/tmp}/t299-final-tracked.$$"
sed -n -E 's#^(\.softhouse/capture/t256[^/]*)/.*#\1#p' "${TMPDIR:-/tmp}/t299-final-tracked.$$" \
  | LC_ALL=C sort -u | while IFS= read -r d; do
      rec="$(sed -n -E "s#^(${d}/OWNER[^/]*\.md)\$#\1#p" "${TMPDIR:-/tmp}/t299-final-tracked.$$" | head -1)"
      echo "    $d"
      echo "        ownership record : ${rec:-<none: this is the id OWN rig>}"
    done
echo
echo "  the guard:"
bash .softhouse/guards/check-capture-namespace.sh 2>&1 | sed 's/^/    /'
grc=${PIPESTATUS[0]}
echo "  guard exit : $grc"
echo

echo "=== 2. A BARE 50-failopen-lint.py RUN DOES NOT DIRTY THE TREE ==="
echo "  command  : python3 .softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
echo "             (FAILOPEN_LINT_JSON deliberately UNSET)"
env -u FAILOPEN_LINT_JSON python3 .softhouse/capture/t238-failopen/instruments/50-failopen-lint.py \
  >"${TMPDIR:-/tmp}/t299-final-lint.$$" 2>&1
lrc=$?
echo "  exit     : $lrc  (0 clean / 1 violations / 2 corpus refusal -- unchanged contract)"
sed -n '/JSON-DESTINATION DIVERTED/,+4p' "${TMPDIR:-/tmp}/t299-final-lint.$$" | sed 's/^/    /'
git status --porcelain >"${TMPDIR:-/tmp}/t299-final-after.$$"
echo "  git status --porcelain AFTER:"
if diff -u "${TMPDIR:-/tmp}/t299-final-before.$$" "${TMPDIR:-/tmp}/t299-final-after.$$" >/dev/null; then
  echo "    byte-identical to before the run. The listing is:"
  if [ -s "${TMPDIR:-/tmp}/t299-final-after.$$" ]; then
    sed 's/^/      /' "${TMPDIR:-/tmp}/t299-final-after.$$"
  else
    echo "      (the porcelain listing has zero lines)"
  fi
  frc=0
else
  echo "    **THE LISTINGS DIFFER**:"
  diff -u "${TMPDIR:-/tmp}/t299-final-before.$$" "${TMPDIR:-/tmp}/t299-final-after.$$" | sed 's/^/      /'
  frc=1
fi
rm -f "${TMPDIR:-/tmp}/t299-final-before.$$" "${TMPDIR:-/tmp}/t299-final-after.$$" \
      "${TMPDIR:-/tmp}/t299-final-lint.$$" "${TMPDIR:-/tmp}/t299-final-tracked.$$"
echo

if [ "$grc" -eq 0 ] && [ "$frc" -eq 0 ]; then
  echo "BOTH STATES SHOWN."
  exit 0
fi
echo "FINAL STATE NOT ESTABLISHED (guard exit $grc, tree-cleanliness arm $frc)."
exit 1
