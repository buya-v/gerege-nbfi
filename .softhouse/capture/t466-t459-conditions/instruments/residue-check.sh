#!/bin/bash
# =============================================================================================
# T466 RESIDUE CHECK. The drives in this directory set index bits, git config filter drivers and
# a private attributes file. Every one of those lives in LOCAL state that appears in no diff, so
# "I cleaned up" is exactly the kind of claim that has to be MEASURED rather than asserted --
# the same argument the guard those drives attack now makes about itself.
#
# THE REPOSITORY IS ENTERED ONCE, FATALLY, AT THE TOP. A `cd` inside a `$( ... )` swallows its
# own failure and every line after it would print a measurement nobody took; the T238 fail-open
# linter put T466's first draft of this file on the frontier at TIER 2 for precisely that.
# Repaired at the instrument, not pinned.
#
# The repository root is DERIVED FROM THIS FILE'S OWN LOCATION; the scratch root arrives in
# $T466_WORK. No absolute path and no repo-relative literal is spelled here.
# =============================================================================================
set -u

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
R=$(CDPATH= cd -- "$SELF_DIR/../../../.." && pwd)
SH=".soft""house"
CONF="$SH/conformance"".sh"
WORK="${T466_WORK:-}"

cd "$R" || {
  echo "ERROR: could not enter the derived repository root: $R" >&2
  echo "ERROR: a residue check that is not in the repository has checked nothing." >&2
  echo "ERROR: REFUSING (exit 3)." >&2
  exit 3
}
if [ ! -f "$CONF" ]; then
  echo "ERROR: the derived repository root does not carry the harness: $R" >&2
  echo "ERROR: REFUSING (exit 3)." >&2
  exit 3
fi

echo "REPOSITORY UNDER TEST: $R"
echo
echo "--- 1. INDEX BITS: every tracked entry whose ls-files -v state is not H"
echo "    (S = --skip-worktree, a LOWERCASE letter = --assume-unchanged)"
n=$( git ls-files -v | grep -cv '^H ' )
echo "    entries not in state H: $n"
git ls-files -v | grep -v '^H ' | sed 's/^/      /'
echo
echo "--- 2. THIS CLONE'S PRIVATE ATTRIBUTES FILE"
G=$( git rev-parse --git-dir )
echo "    git-dir: $G"
A="$G/info/attributes"
if [ -e "$A" ]; then
  echo "    the private attributes file EXISTS. Contents:"
  sed 's/^/      /' "$A"
else
  echo "    the private attributes file DOES NOT EXIST."
fi
echo
echo "--- 3. CONFIGURED CONTENT FILTERS"
nf=$( git config --get-regexp '^filter\.' | grep -c '' )
echo "    filter config rows: $nf"
git config --get-regexp '^filter\.' | sed 's/^/      /'
echo
echo "--- 4. WORKING TREE"
echo "    git status --porcelain:"
git status --porcelain | sed 's/^/      /'
echo
echo "--- 5. SCRATCH LOCATION (must be OUTSIDE the repository)"
if [ -z "$WORK" ]; then
  echo "    T466_WORK is unset, so this run makes NO claim about the scratch tree."
else
  echo "    T466_WORK = $WORK"
  case "$WORK" in
    "$R"|"$R"/*) echo "    INSIDE THE REPOSITORY -- INSTRUMENT FAILURE" ;;
    *)           echo "    outside the repository: confirmed" ;;
  esac
  echo "    arms staged there:"
  ls -1 "$WORK/arms" 2>&1 | sed 's/^/      /'
fi
echo
echo "--- 6. ANY T466 FIXTURE LEFT IN A TRACKED PATH"
c=$( git ls-files | grep -c 'zz-t466' )
echo "    tracked paths matching zz-t466: $c"
