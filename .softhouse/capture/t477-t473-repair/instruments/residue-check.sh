#!/bin/bash
# =============================================================================================
# T477 -- RESIDUE, VERIFIED AGAINST THIS REPOSITORY AND NOT AGAINST THE SCRATCH.
#
# Every index bit, filter driver, attributes file and PATH shim this task used lived in a
# throwaway clone under the scratch root, which `arm.sh` refuses to place inside the repository.
# This checks the REPOSITORY, wider than the four classes the dispatch named, for the reason
# T473 m-1 gives: `.git/info/attributes` is one of four places a filter can be declared, and a
# residue check that reads only one of them can report clean while a filter is attached.
#
# The repository root is derived from this file`s own location and entered ONCE, FATALLY.
# Every listing prints its MATCH COUNT before its rows.
# =============================================================================================
set -u

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 3
R=$(CDPATH= cd -- "$SELF_DIR/../../../.." && pwd) || exit 3
SH=".soft""house"
cd "$R" || { echo "REFUSED: could not enter the derived repository root: $R" >&2; exit 3; }
[ -f "$SH/conformance"".sh" ] || {
  echo "REFUSED: the derived root does not carry the harness. Nothing below is a measurement." >&2
  exit 3; }

echo "repository under test : $R"
echo "HEAD                  : $(git rev-parse HEAD)"
echo
echo "--- 1. INDEX BITS: every tracked entry whose ls-files -v state is not H"
echo "    entries not in state H: $(git ls-files -v | LC_ALL=C grep -vc '^H ' || true)"
git ls-files -v | LC_ALL=C grep -v '^H ' | LC_ALL=C sed 's/^/    /' || true
echo
echo "--- 2. ATTRIBUTE SOURCES, ALL FOUR"
GD=$(git rev-parse --git-dir) || exit 3
CD=$(git rev-parse --git-common-dir) || exit 3
echo "    git-dir        : $GD"
echo "    git-common-dir : $CD"
for f in "$GD/info/attributes" "$CD/info/attributes"; do
  if [ -f "$f" ]; then
    echo "    PRESENT ($(LC_ALL=C grep -c '' "$f") line(s)): $f"
  else
    echo "    ABSENT : $f"
  fi
done
echo "    core.attributesFile   : [$(git config --get core.attributesFile || true)]  (empty = unset)"
XDG="${XDG_CONFIG_HOME:-$HOME/.config}/git/attributes"
if [ -f "$XDG" ]; then
  echo "    PRESENT ($(LC_ALL=C grep -c '' "$XDG") line(s)): $XDG"
else
  echo "    ABSENT : $XDG"
fi
echo "    TRACKED .gitattributes files: $(git ls-files -- '.gitattributes' '*/.gitattributes' | LC_ALL=C grep -c '' || true)"
echo
echo "--- 3. CONTENT FILTERS, AT EVERY CONFIG LEVEL"
echo "    local  filter.* entries: $(git config --local  --get-regexp '^filter\.' 2>/dev/null | LC_ALL=C grep -c '' || true)"
echo "    global filter.* entries: $(git config --global --get-regexp '^filter\.' 2>/dev/null | LC_ALL=C grep -c '' || true)"
echo "    system filter.* entries: $(git config --system --get-regexp '^filter\.' 2>/dev/null | LC_ALL=C grep -c '' || true)"
echo "    ALL levels             : $(git config --get-regexp '^filter\.' 2>/dev/null | LC_ALL=C grep -c '' || true)"
git config --get-regexp '^filter\.' 2>/dev/null | LC_ALL=C sed 's/^/    /' || true
echo "    core.autocrlf          : [$(git config --get core.autocrlf || true)]  (empty = unset)"
echo
echo "--- 4. WORKING TREE"
echo "    porcelain lines: $(git status --porcelain | LC_ALL=C grep -c '' || true)"
git status --porcelain | LC_ALL=C sed 's/^/    /' || true
echo
echo "--- 5. THE FIXTURE TOKEN NEVER TOUCHED THIS REPOSITORY"
MK="T477-""FORGED-MARKER"
echo "    tracked paths carrying the forged-marker token: $(git grep -l -F -- "$MK" -- . ':!*/t477-t473-repair/*' 2>/dev/null | LC_ALL=C grep -c '' || true)"
echo "    tracked paths named for the scratch root      : $(git ls-files | LC_ALL=C grep -c 't477-work' || true)"
echo
echo "--- 6. THE LOCK AND THE PINS ARE UNTOUCHED"
echo "    LOCK in HEAD : $(git rev-parse "HEAD:$SH/LOCK" 2>/dev/null || echo '<absent>')"
echo "    LOCK on disk : $(git hash-object --no-filters -- "$SH/LOCK" 2>/dev/null || echo '<absent>')"
for p in tasks.json RESUME.md program.json patterns.md; do
  echo "    $p changed vs merge-base with main: $(git diff --name-only "$(git merge-base main HEAD)"...HEAD -- "$SH/$p" | LC_ALL=C grep -c '' || true)"
done
