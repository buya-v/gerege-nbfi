#!/bin/bash
# T319 -- F6. WHICH ANCHOR ACTUALLY IDENTIFIES A FIRE'S LOCK COMMIT?
#
# T309 anchors on  git log -1 --fixed-strings --grep "softhouse: local fire lock (<id>)".
# `--grep` matches the whole message (subject AND body) and `-1` takes the NEWEST match,
# so a later commit that merely QUOTES the subject moves the anchor forward (T302 F6).
#
# Three candidate anchors are measured here against the five real fire ids T302 named.
# Read-only.  Usage: bash .softhouse/capture/t319-reconciler-f5/probe-anchor.sh [repo]
set -u
REPO="${1:-$PWD}"
cd "$REPO" || exit 1
echo "repo: $REPO"
echo

for FIRE in 20260827-230001 20260823-140001 20260823-080004 20260822-140002 20260821-080001; do
  SUB="softhouse: local fire lock ($FIRE)"
  echo "=== fire $FIRE ==="

  echo "--- A: T309's anchor  (--fixed-strings --grep, WHOLE MESSAGE, newest wins) ---"
  git log --format='%H %ct %s' --fixed-strings --grep "$SUB" | sed 's/^/    /'
  N_A=$(git log --format=%H --fixed-strings --grep "$SUB" | wc -l | tr -d ' ')
  echo "    matches: $N_A"

  echo "--- B: T319's anchor  (candidates narrowed by --grep, then EXACT %s equality) ---"
  N_B=0
  while IFS=$'\t' read -r H S; do
    if [ "$S" = "$SUB" ]; then
      echo "    $H  EXACT-SUBJECT"
      N_B=$((N_B + 1))
    else
      echo "    $H  body-only quote, REJECTED: $S"
    fi
  done < <(git log --format='%H%x09%s' --fixed-strings --grep "$SUB")
  echo "    exact-subject matches: $N_B  (T319 REFUSES unless this is exactly 1)"

  echo "--- C: corroboration  (commit that ADDED .softhouse/LOCK, newest first, 3) ---"
  git log --format='%H %s' --diff-filter=A -- .softhouse/LOCK | head -3 | sed 's/^/    /'
  echo
done
