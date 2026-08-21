#!/usr/bin/env bash
# T191 — how close is the REAL tree to the inversion point today? Do not inherit
# this number from another handoff; it moves with every file added to the module
# and every vector captured.
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"

echo "=== site 2: POST-STRIP size of every .go file under $REPO/nexus (top 5) ==="
while IFS= read -r f; do
  n="$(perl -0pe 's{//[^\n]*}{}g; s{/\*.*?\*/}{}gs' "$f" | wc -c | tr -d ' ')"
  raw="$(wc -c < "$f" | tr -d ' ')"
  printf '%9s  (raw %9s)  %s\n' "$n" "$raw" "${f#"$REPO/"}"
done < <(find "$REPO/nexus" -name '*.go' -type f | sort) | sort -rn | head -5

echo
echo "=== site 1: POST-STRIP size of every vector .json (top 5) ==="
while IFS= read -r f; do
  n="$(perl -0pe 's/"(\\.|[^"\\])*"//g' "$f" | wc -c | tr -d ' ')"
  raw="$(wc -c < "$f" | tr -d ' ')"
  printf '%9s  (raw %9s)  %s\n' "$n" "$raw" "${f#"$REPO/"}"
done < <(find "$REPO/.softhouse/vectors" -name '*.json' -type f | sort) | sort -rn | head -5

echo
echo "=== site 3: size of a full --self-test run's combined output (\$out20) ==="
. "$REPO/.softhouse/bin/go-env.sh" >/dev/null 2>&1 || true
out="$(bash "$REPO/.softhouse/conformance.sh" --self-test 2>&1 || true)"
printf '%9s  bytes of \$out20-equivalent (harness --self-test stdout+stderr)\n' "${#out}"
