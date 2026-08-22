#!/usr/bin/env bash
# T246 — did revisions 1..5 EACH carry the false sentence, as revision 6's Hunk A asserts
# ("Revisions 1-5 said 'The A2 corpus contains no reversal'")? Read the blobs, do not infer.
# Engine: git show + /usr/bin/grep -c (absolute path; NEVER bare grep, P-75).
set -euo pipefail
cd "$(dirname "$0")/../../.." || exit 9
F=docs/adr/DEC-2-gl-accounting-adapter.md

# revision -> the commit that authored it (from `git log -- $F`)
REVS="rev1:e2decab rev1-banner:e2decab rev2:09074ea rev2-microfix:f39a65d rev3:ead328a rev4:1b6b3cf rev5:cab9e82 HEAD:HEAD"

echo "=== 'The A2 corpus contains no reversal' — occurrences per revision blob ==="
for pair in $REVS; do
  label="${pair%%:*}"; sha="${pair##*:}"
  n=$(git show "$sha:$F" | LC_ALL=C /usr/bin/grep -c "The A2 corpus contains no reversal" || true)
  m=$(git show "$sha:$F" | LC_ALL=C /usr/bin/grep -c "no reversal appears" || true)
  z=$(git show "$sha:$F" | LC_ALL=C /usr/bin/grep -c "ZZZ-NOSUCH-T246" || true)
  printf '  %-14s %-9s site1=%s  site2=%s  known-negative=%s (MUST be 0)\n' "$label" "$sha" "$n" "$m" "$z"
done
echo
echo "=== when did each site FIRST appear? ==="
echo -n "  site1 first commit: "; git log --oneline -S"The A2 corpus contains no reversal" --reverse -- "$F" | head -1
echo -n "  site2 first commit: "; git log --oneline -S"no reversal appears" --reverse -- "$F" | head -1
echo
echo "=== the reversal capture that falsified them — when was it committed? ==="
git log --oneline -1 -- .softhouse/capture/tierA-a2/out/A2-348-je-reverse.json | sed 's/^/  A2-348: /'
git log --oneline -1 -- .softhouse/capture/tierA-a2/out/A2-460-je-reverse.json | sed 's/^/  A2-460: /'
echo
echo "=== DEC-2 last touched / ledger vectors landed (the P-69 window) ==="
git log -1 --format='  DEC-2 rev5      %h  %ci  %s' cab9e82
git log -1 --format='  ledger vectors  %h  %ci  %s' -- .softhouse/vectors/ledger
echo
echo "=== END ==="
