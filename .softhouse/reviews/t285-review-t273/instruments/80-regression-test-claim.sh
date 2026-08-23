#!/usr/bin/env bash
# T285 — IS `guard_frontier_host_sensitivity` REALLY "a permanent regression test for the
#        exact defect T273 was filed for"?
#
# conformance.sh (T273, commit 2ae2c8c) claims, in the guard's own comment:
#
#     "THE REPAIRED FILE IS NOT IN THE DELTA. ... reintroduce the residue dependence and
#      that row enters the delta and this guard refuses. That is a permanent regression
#      test for the exact defect T273 was filed for."
#
# This drives it. Two arms, both with `C=/tmp/t234_matrix2.txt` PUT BACK into
# 02-escape-matrix-fix.sh exactly as it stood at fe24419, differing in ONE thing:
#
#   A  the repaired file's T273 EXPLANATORY COMMENT is left in place. That comment
#      contains the eleven characters `> /tmp/t234_matrix2.txt` (:12), and the linter's
#      ownership filter is `re.search(RE_OWNED_HEAD + re.escape(p), txt)` over the WHOLE
#      FILE TEXT — comments included [50-failopen-lint.py:233, :368]. So the comment
#      OWNS the path and C1 never fires.
#   B  that one comment line is removed, and nothing else.
#
# If the claim holds, BOTH arms put the row back in the delta. Prints the bracket's delta
# count for each arm. Restores the tree and verifies the restore.
set -u

cd "$(git rev-parse --show-toplevel)" || exit 2
F=".softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh"
B=".softhouse/capture/t273-residue/instruments/80-host-state-bracket.py"

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "T285 REFUSED: dirty tree before any mutation; the restore below would eat it."
  git status --porcelain --untracked-files=no
  exit 2
fi
restore() { git checkout -- . 2>/dev/null; }
trap restore EXIT

plant_defect() {
  /usr/bin/sed -i '' 's%^D="\$(mktemp -d .*$%C=/tmp/t234_matrix2.txt%' "$F"
  /usr/bin/sed -i '' "s%^trap 'rm -rf \"\\\$D\"' EXIT\$%%" "$F"
  /usr/bin/sed -i '' 's%^C="\$D/matrix2.txt"$%%' "$F"
}

report() {   # $1 = arm label
  local n row
  rm -f /tmp/t234_matrix2.txt
  python3 "$B" >".softhouse/reviews/t285-review-t273/scratch/80-$1.txt" 2>&1
  n="$(/usr/bin/grep -c '^      [+-] TIER' ".softhouse/reviews/t285-review-t273/scratch/80-$1.txt")"
  row="$(/usr/bin/grep -c '02-escape-matrix-fix.sh' ".softhouse/reviews/t285-review-t273/scratch/80-$1.txt" || true)"
  echo "  ARM $1: bracket delta rows = $n ; lines naming 02-escape-matrix-fix.sh in the whole report = $row"
  /usr/bin/grep -n 'FAILOPEN-FRONTIER\|02-escape-matrix-fix' ".softhouse/reviews/t285-review-t273/scratch/80-$1.txt" \
    | /usr/bin/grep '02-escape' | /usr/bin/sed 's/^/        /'
}

mkdir -p .softhouse/reviews/t285-review-t273/scratch
echo "### T285 — IS THE PIN A REGRESSION TEST FOR 02-escape-matrix-fix.sh?"
echo "  tree : $(pwd)"
echo "  HEAD : $(git rev-parse HEAD)"
echo "  pinned delta = 7 rows (HOSTSENSITIVE_PIN_FRONTIER_DELTA)"
echo

echo "BASELINE — repaired file, untouched:"
report BASELINE

echo
echo "ARM A — defect reintroduced, T273's explanatory comment LEFT IN PLACE:"
plant_defect
/usr/bin/grep -n 't234_matrix2.txt' "$F" | /usr/bin/sed 's/^/      /'
report A-comment-present
restore

echo
echo "ARM B — defect reintroduced AND the one comment line carrying \`> /tmp/t234_matrix2.txt\` removed:"
plant_defect
/usr/bin/sed -i '' '/for a literal `> \/tmp\/t234_matrix2.txt` and the redirection here/d' "$F"
/usr/bin/grep -n 't234_matrix2.txt' "$F" | /usr/bin/sed 's/^/      /'
report B-comment-removed
restore
rm -f /tmp/t234_matrix2.txt

echo
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "### ENDED DIRTY — restore did not hold:"
  git status --porcelain --untracked-files=no
  exit 2
fi
echo "### tree restored clean (checked, not assumed)."
