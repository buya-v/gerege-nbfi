#!/bin/bash
# T361 — RE-DERIVE the holder@host census T353 uses to refute the driver's framing.
# Written from scratch, not copied from T353's `lock-host-census.sh`, so the two are
# independent derivations of the same population (P-22).
#
# The claim under test: "the cloud fire does not execute `fire-program.sh`", inferred from
# the fact that every lock this wrapper writes carries a hard-coded `holder`, and no lock in
# history pairs that holder with a non-Mac host.
#
# If the inference is WRONG — if the cloud fire does run this wrapper by any path — then the
# `date -j` defect was LIVE, not latent, and the severity of T342/T353 goes back up.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 3

LOCKPATH=".softhouse/LOCK"
echo "=== every commit that touched $LOCKPATH ==="
# /bin/bash on macOS is 3.2 and has no `mapfile`. Read into an array the portable way.
SHAS=()
while IFS= read -r _s; do SHAS+=("$_s"); done < <(git log --all --format=%H -- "$LOCKPATH")
echo "commits touching the LOCK (git log --all): ${#SHAS[@]}"
echo

echo "=== holder @ host, one line per commit, tallied ==="
for sha in "${SHAS[@]}"; do
  body="$(git show "$sha:$LOCKPATH" 2>/dev/null)" || { echo "DELETED-AT-THIS-COMMIT"; continue; }
  /usr/bin/python3 - <<PY
import json,sys
raw = """$body"""
try:
    d = json.loads(raw)
except Exception:
    print("UNPARSEABLE @ -")
    sys.exit()
if not isinstance(d, dict):
    print("NOT-AN-OBJECT @ -")
    sys.exit()
print("%s @ %s" % (d.get("holder","<no holder key>"), d.get("host","<no host key>")))
PY
done | sort | uniq -c | sort -rn

echo
echo "=== the wrapper's OWN hard-coded holder string, quoted by extraction from the file ==="
grep -n 'holder' .softhouse/bin/fire-program.sh | grep -v '^\s*[0-9]*:#' | head -20

echo
echo "=== does ANY holder string this wrapper can emit appear with a non-Mac host? ==="
for sha in "${SHAS[@]}"; do
  git show "$sha:$LOCKPATH" 2>/dev/null | tr -d '\n' | \
    grep -o '"holder"[^,}]*\|"host"[^,}]*' | tr '\n' ' '
  echo
done | sort -u

echo
echo "=== OTHER paths by which the cloud fire could reach this wrapper ==="
echo "-- launchd plists referencing it:"
grep -rln 'fire-program' .softhouse/launchd/ 2>/dev/null || echo "   (no .softhouse/launchd match)"
echo "-- every tracked file that INVOKES fire-program.sh (not merely names it):"
git grep -n -E '(zsh|bash|sh|exec|source|\./)[^\n]*fire-program\.sh' -- \
  ':!.softhouse/handoff' ':!.softhouse/reviews' ':!.softhouse/capture' ':!.softhouse/patterns.md' \
  ':!.softhouse/gates.md' ':!.softhouse/obligations.md' 2>/dev/null
echo "-- GitHub Actions / CI workflows in the repo:"
ls -1 .github/workflows/ 2>/dev/null || echo "   (no .github/workflows)"
echo "-- anything in the repo that names the cloud sandbox host:"
git grep -ln 'claude-code-remote-sandbox' 2>/dev/null | head -20
