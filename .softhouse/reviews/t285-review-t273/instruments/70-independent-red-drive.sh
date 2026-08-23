#!/usr/bin/env bash
# T285 — DRIVE T273's TWO NEW GUARDS RED MYSELF (P-50/P-72).
#
# T273 shipped its own 50-red-drive.sh. Running someone's own red drive is agreement,
# not verification, so this one is written from the guards' stated rules and not from
# T273's script. Four mutations, each restored, each checked back to a clean tree with
# `git status --porcelain` rather than assumed:
#
#   CONTROL  nothing                                     -> expect BAR exit 0 (P-72 calibration)
#   M1       plant NAME=/tmp/... in a repo-wide search instrument
#                                                        -> expect census 18 != 17, exit 2
#   M2       repair a PINNED site (the '-' direction)     -> expect census 16 != 17, exit 2
#   M3       reintroduce T273's own defect: put the literal /tmp fixture back into
#            02-escape-matrix-fix.sh                      -> expect BOTH guards fire, exit 2
#   M4       delete 80-host-state-bracket.py              -> expect the sensitivity guard
#                                                           refuse on ABSENT BRACKET, exit 2
#
# THE TREE MUST BE CLEAN BEFORE THE TRAP IS ARMED. T273's own handoff records that the
# first draft of its red drive armed `trap restore EXIT` before the dirty-tree check and
# destroyed its own uncommitted work. That ordering is inverted here on purpose.
set -u

cd "$(git rev-parse --show-toplevel)" || exit 2
OUT=".softhouse/reviews/t285-review-t273/evidence"
mkdir -p "$OUT"

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "T285 RED DRIVE REFUSED: the work tree is dirty before any mutation. This script"
  echo "restores by `git checkout --`, which would destroy uncommitted work. Commit first."
  git status --porcelain --untracked-files=no
  exit 2
fi
# Only now is restoring safe.
restore() { git checkout -- . 2>/dev/null; }
trap restore EXIT

ESCAPE=".softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh"
PLANT=".softhouse/capture/t239-r11-rerun/instruments/10-population.sh"
PINNED=".softhouse/reviews/T158-compare-enumerators.sh"
BRACKET=".softhouse/capture/t273-residue/instruments/80-host-state-bracket.py"

run_bar() {                      # $1 = tag
  local tag="$1" log="$OUT/70-reddrive-$1.log" rc probe census delta
  bash .softhouse/conformance.sh >"$log" 2>&1
  rc=$?
  probe="$(grep -c 'probe = ' "$log")"
  census="$(grep -c 'THE HOST-STATE CENSUS IS NOT THE PINNED CENSUS' "$log")"
  delta="$(grep -c 'THE HOST-SENSITIVE FRONTIER DELTA IS NOT THE PINNED DELTA' "$log")"
  local absent frontier
  absent="$(grep -c 'THE HOST-STATE BRACKET IS ABSENT' "$log")"
  frontier="$(grep -c 'THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER' "$log")"
  printf '%-8s exit=%s probe=%s  census-fired=%s  delta-fired=%s  bracket-absent=%s  frontier-fired=%s\n' \
    "$tag" "$rc" "$probe" "$census" "$delta" "$absent" "$frontier"
}

echo "### T285 — INDEPENDENT RED DRIVE of guard_no_host_state_in_lint_corpus and"
echo "###        guard_frontier_host_sensitivity"
echo "  tree : $(pwd)"
echo "  HEAD : $(git rev-parse HEAD)"
echo "  residue /tmp/t234_matrix2.txt present at start: $([ -e /tmp/t234_matrix2.txt ] && echo YES || echo NO)"
echo

run_bar CONTROL

# M1 — a NEW host-state assignment enters the lint corpus.
printf '\nT285_PLANTED=/tmp/t285-planted-scratch\n' >>"$PLANT"
run_bar M1-plus
restore

# M2 — a PINNED site is repaired, and the pin is left stale ('-' direction).
/usr/bin/sed -i '' 's%^C=/tmp/t158-clone$%C="$(mktemp -d "${TMPDIR:-/tmp}/t158-clone.XXXXXXXXXX")"%' "$PINNED"
if [ -z "$(git status --porcelain -- "$PINNED")" ]; then
  echo "M2-minus SKIPPED: the sed did not change $PINNED — re-read the pinned spelling."
else
  run_bar M2-minus
fi
restore

# M3 — T273's own defect, put back. This is the regression test the pin claims to be.
/usr/bin/sed -i '' 's%^D="\$(mktemp -d .*$%C=/tmp/t234_matrix2.txt%' "$ESCAPE"
/usr/bin/sed -i '' "s%^trap 'rm -rf \"\\\$D\"' EXIT\$%%" "$ESCAPE"
/usr/bin/sed -i '' 's%^C="\$D/matrix2.txt"$%%' "$ESCAPE"
if [ -z "$(git status --porcelain -- "$ESCAPE")" ]; then
  echo "M3-regress SKIPPED: the sed did not change $ESCAPE — re-read the repaired spelling."
else
  echo "  M3 planted; the file now reads:"
  /usr/bin/sed -n '5,9p' "$ESCAPE" | /usr/bin/sed 's/^/      /'
  rm -f /tmp/t234_matrix2.txt
  run_bar M3-regress
fi
restore
rm -f /tmp/t234_matrix2.txt

# M4 — the wired instrument is gone.
rm -f "$BRACKET"
run_bar M4-nobracket
restore

echo
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "### T285 RED DRIVE ENDED DIRTY — the restore did not hold. Inspect before trusting:"
  git status --porcelain --untracked-files=no
  exit 2
fi
echo "### tree restored clean (git status --porcelain empty, checked not assumed)."
