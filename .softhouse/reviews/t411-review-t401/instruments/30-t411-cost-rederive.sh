#!/usr/bin/env bash
# T411 item 4: re-derive T401's cost table WITHOUT reading it.
#
# For each of the four live censuses, run the SHIPPED selector and a ONE-TOKEN-WIDER
# selector and diff the graded output. Widened copies are materialised in a scratch
# directory that is deleted on exit and asserted to leave zero residue; committing one
# would put it in both corpora and move the very figures it exists to measure.
#
# A sed that matched nothing is a silent no-op that reports a ZERO delta and reads as
# "extending is free" -- the exact fail-open shape this apparatus exists to catch. So
# every patch is cmp-verified to have changed the file, and an unchanged copy REFUSES.
#
# NOTE ON THE SCRATCH ROOT: it is deliberately NOT under the .softhouse/ prefix, because
# the dead-path census extracts .softhouse/-rooted literals from file BYTES and would
# otherwise grade this instrument's own scratch path as a dead reference.
set -uo pipefail
GREP=/usr/bin/grep
ROOT="$(git rev-parse --show-toplevel)" || exit 9
cd "$ROOT" || exit 9

SCRATCH="$ROOT/.t411-cost-scratch"
rm -rf "$SCRATCH"; mkdir -p "$SCRATCH"
cleanup() {
  rm -rf "$SCRATCH"
  local residue
  residue="$(git status --porcelain 2>/dev/null | $GREP -c 't411-cost-scratch' || true)"
  echo
  echo "TEARDOWN: scratch residue rows = ${residue:-0}  (MUST be 0)"
  [ "${residue:-0}" = "0" ] || { echo "TEARDOWN FAILED -- scratch survived"; exit 1; }
}
trap cleanup EXIT INT TERM

# a patch that did not change the file is a refusal, not a zero
patch_or_refuse() {  # $1=orig $2=copy $3=sed-expr $4=label
  cp "$1" "$2"
  sed -i '' -E "$3" "$2" 2>/dev/null || sed -i -E "$3" "$2"
  if cmp -s "$1" "$2"; then
    echo "REFUSE: the $4 widening patch matched NOTHING. A no-op reports a zero delta"
    echo "REFUSE: and reads as 'extending is free'. That is the defect, not the result."
    exit 1
  fi
  echo "  patch OK ($4): $(diff "$1" "$2" | $GREP -c '^[<>]') line(s) changed"
}

echo "T411 COST RE-DERIVATION @ $(git rev-parse --short HEAD)"
echo "tree state: $(git status --porcelain | $GREP -c . ) modified/untracked path(s)"
echo

################################################################ S1
echo "=============================================================="
echo "S1  FAIL-OPEN LINT  -- capture/t238-failopen/instruments/50-failopen-lint.py:211"
echo "=============================================================="
L_ORIG=".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
L_COPY="$SCRATCH/s1-widened.py"
patch_or_refuse "$L_ORIG" "$L_COPY" 's/f\.endswith\(\("\.sh", "\.py"\)\)/f.endswith((".sh", ".py", ".zsh"))/' "S1"

echo "-- shipped --"
( cd "$ROOT" && python3 "$L_ORIG" ) > "$SCRATCH/s1.shipped" 2>&1
echo "   $($GREP -E '^corpus' "$SCRATCH/s1.shipped" || echo '(no corpus line)')"
S1_FRONT_A=$($GREP -c 'FAILOPEN-FRONTIER' "$SCRATCH/s1.shipped" || true)
echo "   FAILOPEN-FRONTIER rows: $S1_FRONT_A"
echo "-- widened --"
( cd "$ROOT" && python3 "$L_COPY" ) > "$SCRATCH/s1.widened" 2>&1
echo "   $($GREP -E '^corpus' "$SCRATCH/s1.widened" || echo '(no corpus line)')"
S1_FRONT_B=$($GREP -c 'FAILOPEN-FRONTIER' "$SCRATCH/s1.widened" || true)
echo "   FAILOPEN-FRONTIER rows: $S1_FRONT_B"
echo "-- frontier DIFF (shipped -> widened) --"
$GREP 'FAILOPEN-FRONTIER' "$SCRATCH/s1.shipped" | sort > "$SCRATCH/s1.fa"
$GREP 'FAILOPEN-FRONTIER' "$SCRATCH/s1.widened" | sort > "$SCRATCH/s1.fb"
diff "$SCRATCH/s1.fa" "$SCRATCH/s1.fb" | sed 's/^/   /' || true
echo "   S1 COST: frontier $S1_FRONT_A -> $S1_FRONT_B"
echo
echo "-- does conformance.sh:1673's parser still parse the WIDENED corpus line? --"
echo -n "   sed yields: "
$GREP -E '^corpus' "$SCRATCH/s1.widened" | sed -n 's/^corpus    : \([0-9][0-9]*\) tracked.*$/\1/p'

################################################################ S2
echo
echo "=============================================================="
echo "S2  DEAD-PATH CENSUS -- capture/t316-dead-path-guards/census_dead_paths.py:110"
echo "=============================================================="
C_ORIG=".softhouse/capture/t316-dead-path-guards/census_dead_paths.py"
C_COPY="$SCRATCH/s2-widened.py"
patch_or_refuse "$C_ORIG" "$C_COPY" 's/"\.softhouse\/\*\.py", "\.softhouse\/\*\.sh"/".softhouse\/*.py", ".softhouse\/*.sh", ".softhouse\/*.zsh"/' "S2"

rows_from_json() { python3 - "$1" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
rows = set()
for f in doc["deadFiles"]:
    for d in doc["perFile"][f]["dead"]:
        rows.add("%s | %s" % (f, d))
for r in sorted(rows):
    print(r)
PY
}

echo "-- shipped --"
python3 "$C_ORIG" --json "$SCRATCH/s2a.json" > "$SCRATCH/s2a.out" 2>&1
echo "   $($GREP 'T316-DEADPATH-CENSUS:' "$SCRATCH/s2a.out" || echo '(no probe line)')"
echo "   $($GREP -E '^  corpus' "$SCRATCH/s2a.out" || true)"
rows_from_json "$SCRATCH/s2a.json" > "$SCRATCH/s2a.rows"
echo "   rows: $(wc -l < "$SCRATCH/s2a.rows" | tr -d ' ')"

echo "-- widened --"
python3 "$C_COPY" --json "$SCRATCH/s2b.json" > "$SCRATCH/s2b.out" 2>&1
echo "   $($GREP 'T316-DEADPATH-CENSUS:' "$SCRATCH/s2b.out" || echo '(no probe line)')"
echo "   $($GREP -E '^  corpus' "$SCRATCH/s2b.out" || true)"
rows_from_json "$SCRATCH/s2b.json" > "$SCRATCH/s2b.rows"
echo "   rows: $(wc -l < "$SCRATCH/s2b.rows" | tr -d ' ')"

echo
echo "-- ADDED rows (widened minus shipped) --"
comm -13 "$SCRATCH/s2a.rows" "$SCRATCH/s2b.rows" | sed 's/^/   + /'
echo "-- REMOVED rows (a widening may only ADD; any removal is a refusal) --"
REMOVED="$(comm -23 "$SCRATCH/s2a.rows" "$SCRATCH/s2b.rows")"
if [ -n "$REMOVED" ]; then printf '%s\n' "$REMOVED" | sed 's/^/   - /'; echo "   REFUSE: widening REMOVED rows"; else echo "   (none)"; fi
echo "   S2 COST: dead rows $(wc -l < "$SCRATCH/s2a.rows" | tr -d ' ') -> $(wc -l < "$SCRATCH/s2b.rows" | tr -d ' ')"
cp "$SCRATCH/s2a.rows" "$ROOT/.softhouse/reviews/t411-review-t401/evidence/30-s2-shipped-rows.txt"
comm -13 "$SCRATCH/s2a.rows" "$SCRATCH/s2b.rows" > "$ROOT/.softhouse/reviews/t411-review-t401/evidence/30-s2-added-rows.txt"

################################################################ S3
echo
echo "=============================================================="
echo "S3  HOST-STATE CENSUS -- conformance.sh:2131 (selector level)"
echo "=============================================================="
# lift the repo-wide-search regex out of conformance.sh BY BYTES; a drifted
# definition must refuse rather than report a figure about a different search.
RW_LINE="$($GREP -nE '^[[:space:]]*(local )?rw=' .softhouse/conformance.sh | head -1)"
echo "   rw= definition found at: ${RW_LINE%%:*}"
RW="$(sed -n "$(echo "${RW_LINE%%:*}")p" .softhouse/conformance.sh | sed -E "s/^[[:space:]]*(local )?rw='//; s/'[[:space:]]*\$//")"
if [ -z "$RW" ]; then echo "   REFUSE: could not lift \$rw from conformance.sh"; exit 1; fi
echo "   rw (first 90 chars): ${RW:0:90}"
A=$( ( cd "$ROOT" && LC_ALL=C git grep -l -E "$RW" -- '*.sh' '*.py' ) 2>/dev/null | $GREP -c . || true)
B=$( ( cd "$ROOT" && LC_ALL=C git grep -l -E "$RW" -- '*.sh' '*.py' '*.zsh' ) 2>/dev/null | $GREP -c . || true)
echo "   population shipped : $A"
echo "   population widened : $B   (delta $((B-A)))"
echo "   the .zsh files that ENTER the population:"
( cd "$ROOT" && LC_ALL=C git grep -l -E "$RW" -- '*.zsh' ) 2>/dev/null | sed 's/^/     /' || echo "     (none)"
echo
echo "   -- do any of them assign a host path, i.e. would the PIN move? --"
HS_RE='(^|[[:space:]])[A-Za-z_][A-Za-z0-9_]*=(\"|'"'"')?/(tmp|var|private)/'
( cd "$ROOT" && LC_ALL=C git grep -l -E "$RW" -- '*.zsh' ) 2>/dev/null | while read -r f; do
   hits=$(LC_ALL=C $GREP -cE "$HS_RE" "$f" || true)
   echo "     $f  host-path assignments: $hits"
done
echo "   raw NAME=/tmp assignment lines in ALL tracked .zsh (for contrast):"
echo -n "     "; git ls-files '*.zsh' | while read -r f; do LC_ALL=C $GREP -HnE "$HS_RE" "$f" || true; done | $GREP -c . || true

################################################################ S4
echo
echo "=============================================================="
echo "S4  GUARDS-DIR POPULATION -- conformance.sh:3267-3269 (selector level)"
echo "=============================================================="
GD=".softhouse/guards"
a=$( ( cd "$ROOT" && git ls-files -- ":(glob)$GD/"'**/*.sh' ":(glob)$GD/"'**/*.py' ":(glob)$GD/"'**/*.go' ) 2>/dev/null | $GREP -c . || true)
b=$( ( cd "$ROOT" && git ls-files -- ":(glob)$GD/"'**/*.sh' ":(glob)$GD/"'**/*.py' ":(glob)$GD/"'**/*.go' ":(glob)$GD/"'**/*.zsh' ) 2>/dev/null | $GREP -c . || true)
echo "   population shipped : $a"
echo "   population widened : $b   (delta $((b-a)))"
echo "   members:"; ( cd "$ROOT" && git ls-files -- ":(glob)$GD/"'**/*.sh' ":(glob)$GD/"'**/*.py' ":(glob)$GD/"'**/*.go' ) 2>/dev/null | sed 's/^/     /'
