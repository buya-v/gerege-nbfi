#!/usr/bin/env bash
# T411 item 6: an INDEPENDENT discrimination drive for the .zsh census gap.
#
# This does not run T401's drive. It builds its own, because the question a review
# must answer is not "does the author's drive pass" but "does the widening actually
# discriminate on the DEFECT rather than on the EXTENSION".
#
# THE CONTROL IS THE POINT (P-98). T401's controls are all `.sh` files, so they sit in
# the corpus in BOTH arms and their membership does not change when the selector widens
# -- they prove the linter does not refuse everything, but they do NOT exercise the
# widening. The control that exercises the widening is a HEALTHY `.zsh`: absent from the
# shipped corpus, present in the widened corpus, and still not flagged. Bait and control
# then differ in exactly one thing -- their CONTENT -- so a difference in verdict cannot
# be attributed to the extension.
#
# BAIT is never authored. It is a byte copy of a file already ON the pinned frontier,
# with the extension as the only change, so "it got caught" cannot be an artefact of
# bait written to be catchable.
#
# NO PATH UNDER THE .softhouse PREFIX IS SPELLED WHOLE IN THIS FILE. Every scratch path
# is assembled from a variable that resolves at runtime. The dead-path census reads BYTES
# and does not know prose from intent; a scratch path spelled as a literal here would be
# graded as a dead reference. That is the defect T401 committed four times.
set -uo pipefail
GREP=/usr/bin/grep
ROOT="$(git rev-parse --show-toplevel)" || exit 9
cd "$ROOT" || exit 9

GRANT="$(cd "$(dirname "$0")/.." && pwd)"          # this grant dir, DERIVED, never spelled
D="$GRANT/.drive-scratch"                           # under the .softhouse prefix, so S2 can see it
DREL="${D#"$ROOT"/}"
IDX="$(mktemp -d)/index"

BAIT_SRC="$(git ls-files | $GREP -E 'red-drive/sweep-ORIGINAL\.sh$' | head -1)"
[ -n "$BAIT_SRC" ] || { echo "REFUSE: canonical TIER1 bait source not found in the index."; exit 1; }

cleanup() {
  unset GIT_INDEX_FILE   # else `git status` below reads the deleted scratch index and
                         # reports every tracked file as changed -- a scary, meaningless number
  rm -rf "$D" "$(dirname "$IDX")"
  local residue
  residue="$(git status --porcelain 2>/dev/null | $GREP -c 'drive-scratch' || true)"
  echo
  echo "TEARDOWN: worktree residue rows naming the scratch = ${residue:-0} (MUST be 0)"
  echo "TEARDOWN: real index still clean? $(git status --porcelain | $GREP -c . ) non-clean path(s) (expected: only this task's own edits)"
  [ "${residue:-0}" = "0" ] || { echo "TEARDOWN FAILED"; exit 1; }
}
trap cleanup EXIT INT TERM

rm -rf "$D"; mkdir -p "$D"

echo "T411 DISCRIMINATION DRIVE @ $(git rev-parse --short HEAD)"
echo "bait source (already on the pinned frontier): $BAIT_SRC"
echo

# ---- BAIT: byte copy of the canonical TIER1 fail-open, extension changed --------------
cp "$BAIT_SRC" "$D/bait-failopen.zsh"
cmp -s "$BAIT_SRC" "$D/bait-failopen.zsh" || { echo "REFUSE: bait is not a byte copy."; exit 1; }
echo "BAIT    : bait-failopen.zsh  == byte-identical to $BAIT_SRC ($(wc -c < "$D/bait-failopen.zsh" | tr -d ' ') bytes)"

# ---- CONTROL: a HEALTHY repo-wide search instrument, same extension -------------------
# Copied from a tracked instrument the shipped linter does NOT flag, so "not flagged"
# is a property of its content. It is a repo-wide search instrument, so it ENTERS the
# populations rather than being ignored -- a control outside the population cannot fail
# and would make "no row" vacuous.
CTRL_SRC="$(git ls-files | $GREP -E '^\.softhouse/guards/check-capture-namespace\.sh$' | head -1)"
[ -n "$CTRL_SRC" ] || { echo "REFUSE: control source not found."; exit 1; }
cp "$CTRL_SRC" "$D/control-healthy.zsh"
echo "CONTROL : control-healthy.zsh == byte copy of $CTRL_SRC"

# ---- BAIT-DP -------------------------------------------------------------------------
# The S1 bait carries no dead literal under the .softhouse prefix, so it cannot bait S2.
# Each arm must be baited with a file already on THAT arm's OWN pinned frontier; a bait
# that cannot be caught by the census under test proves nothing about that census.
BAIT_DP_SRC="$(git ls-files | $GREP -E 'bin/fire-program\.sh$' | head -1)"
[ -n "$BAIT_DP_SRC" ] || { echo "REFUSE: dead-path bait source not found."; exit 1; }
cp "$BAIT_DP_SRC" "$D/bait-deadpath.zsh"
cmp -s "$BAIT_DP_SRC" "$D/bait-deadpath.zsh" || { echo "REFUSE: dead-path bait is not a byte copy."; exit 1; }
echo "BAIT-DP : bait-deadpath.zsh == byte-identical to $BAIT_DP_SRC (already on the dead-path pin)"
echo

# ---- scratch index: the REAL index is never written ----------------------------------
cp "$ROOT/$(git rev-parse --git-dir)/index" "$IDX" 2>/dev/null || cp "$(git rev-parse --absolute-git-dir)/index" "$IDX"
export GIT_INDEX_FILE="$IDX"
git add -f "$D/bait-failopen.zsh" "$D/bait-deadpath.zsh" "$D/control-healthy.zsh"
PLANTED="$(git ls-files | $GREP -c 'drive-scratch' || true)"
[ "$PLANTED" = "3" ] || { echo "REFUSE: expected 3 planted files in the scratch index, saw $PLANTED"; exit 1; }
echo "scratch index: 3 planted files visible to git ls-files; real index untouched."
echo

W="$(dirname "$IDX")"
S1W="$W/s1-widened.py"; S2W="$W/s2-widened.py"
sed -E 's/f\.endswith\(\("\.sh", "\.py"\)\)/f.endswith((".sh", ".py", ".zsh"))/' \
    "$(git ls-files | $GREP -E '50-failopen-lint\.py$' | head -1)" > "$S1W"
cmp -s "$(git ls-files | $GREP -E '50-failopen-lint\.py$' | head -1)" "$S1W" && { echo "REFUSE: S1 widening was a no-op."; exit 1; }
CEN="$(git ls-files | $GREP -E 'census_dead_paths\.py$' | head -1)"
# the widened census copy must live inside the repo: it locates the root from __file__
S2W="$D/../.drive-census-widened.py"
sed -E 's/"\.softhouse\/\*\.py", "\.softhouse\/\*\.sh"/".softhouse\/*.py", ".softhouse\/*.sh", ".softhouse\/*.zsh"/' "$CEN" > "$S2W"
cmp -s "$CEN" "$S2W" && { echo "REFUSE: S2 widening was a no-op."; exit 1; }

report() { # $1=label $2=outfile
  local b c
  b=$($GREP -c "bait-failopen.zsh" "$2" || true)
  c=$($GREP -c "control-healthy.zsh" "$2" || true)
  printf '   %-18s bait rows: %-3s   control rows: %-3s\n' "$1" "$b" "$c"
}

echo "=============== ARM 1/2 : S1 FAIL-OPEN LINTER ==============="
python3 "$(git ls-files | $GREP -E '50-failopen-lint\.py$' | head -1)" > "$W/s1a.txt" 2>&1
echo "   shipped corpus: $($GREP -E '^corpus' "$W/s1a.txt")"
$GREP 'FAILOPEN-FRONTIER' "$W/s1a.txt" > "$W/s1a.rows" || true
report "ARM1 shipped" "$W/s1a.rows"
echo "     -> bait must be 0 here (INVISIBLE), control 0"

python3 "$S1W" > "$W/s1b.txt" 2>&1
echo "   widened corpus: $($GREP -E '^corpus' "$W/s1b.txt")"
$GREP 'FAILOPEN-FRONTIER' "$W/s1b.txt" > "$W/s1b.rows" || true
report "ARM2 widened" "$W/s1b.rows"
echo "     -> bait must be 1 here (CAUGHT), control still 0"
echo "   is the control IN the widened corpus at all? (if not, 'no row' is vacuous)"
INCORP=$(python3 "$S1W" "$DREL" 2>&1 | $GREP -E '^corpus' | sed -E 's/^corpus *: ([0-9]+).*/\1/')
echo "     files from the scratch dir in the widened corpus: $INCORP  (MUST be 3)"

echo
echo "=============== ARM 3/4 : S2 DEAD-PATH CENSUS ==============="
python3 "$CEN" --json "$W/s2a.json" > "$W/s2a.txt" 2>&1
echo "   shipped: $($GREP 'T316-DEADPATH-CENSUS:' "$W/s2a.txt")"
python3 "$S2W" --json "$W/s2b.json" > "$W/s2b.txt" 2>&1
echo "   widened: $($GREP 'T316-DEADPATH-CENSUS:' "$W/s2b.txt")"
rows() { python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
for f in d['deadFiles']:
    for x in d['perFile'][f]['dead']:
        print('%s | %s' % (f, x))
" "$1" | sort; }
rows "$W/s2a.json" > "$W/s2a.rows"; rows "$W/s2b.json" > "$W/s2b.rows"
report_dp() { printf '   %-18s bait-DP rows: %-3s   control rows: %-3s\n' \
  "$1" "$($GREP -c 'bait-deadpath.zsh' "$2" || true)" "$($GREP -c 'control-healthy.zsh' "$2" || true)"; }
report_dp "ARM3 shipped" "$W/s2a.rows"
echo "     -> bait must be 0 here (INVISIBLE), control 0"
report_dp "ARM4 widened" "$W/s2b.rows"
echo "     -> bait must be >0 here (CAUGHT), control still 0"
echo "   bait rows caught, with their literals:"
# not `|| echo "(none)"` -- that prints a negative off an exit status, which is the very
# C2 shape this drive exists to detect. Materialise, then report the count.
$GREP 'bait-deadpath.zsh' "$W/s2b.rows" > "$W/s2b.bait" 2>/dev/null || true
if [ -s "$W/s2b.bait" ]; then sed 's/^/     /' "$W/s2b.bait"; else echo "     0 rows (measured, not inferred)"; fi
echo "   is the control IN the widened corpus at all?"
echo -n "     "; $GREP -c 'drive-scratch' <(git ls-files '.softhouse/*.zsh') || true
echo "     ^ planted .zsh files the widened S2 selector reaches (MUST be 3)"

echo
echo "=============== VERDICT ==============="
FAIL=0
chk() { if [ "$2" = "$3" ]; then echo "   PASS  $1 (=$2)"; else echo "   FAIL  $1 (got $2, want $3)"; FAIL=1; fi; }
chk "S1 shipped: bait INVISIBLE"  "$($GREP -c 'bait-failopen.zsh' "$W/s1a.rows" || true)" 0
chk "S1 widened: bait CAUGHT"     "$($GREP -c 'bait-failopen.zsh' "$W/s1b.rows" || true)" 1
chk "S1 shipped: control spared"  "$($GREP -c 'control-healthy.zsh' "$W/s1a.rows" || true)" 0
chk "S1 widened: control spared"  "$($GREP -c 'control-healthy.zsh' "$W/s1b.rows" || true)" 0
chk "S2 shipped: bait INVISIBLE"  "$($GREP -c 'bait-deadpath.zsh' "$W/s2a.rows" || true)" 0
chk "S2 shipped: control spared"  "$($GREP -c 'control-healthy.zsh' "$W/s2a.rows" || true)" 0
chk "S2 widened: control spared"  "$($GREP -c 'control-healthy.zsh' "$W/s2b.rows" || true)" 0
B4=$($GREP -c 'bait-deadpath.zsh' "$W/s2b.rows" || true)
if [ "$B4" -gt 0 ]; then echo "   PASS  S2 widened: bait CAUGHT (=$B4 row(s))"; else echo "   FAIL  S2 widened: bait NOT caught"; FAIL=1; fi
echo
[ "$FAIL" = "0" ] && echo "DRIVE: PASS -- the widening discriminates on CONTENT, not on extension." \
                  || echo "DRIVE: FAIL"
rm -f "$S2W"
exit 0
