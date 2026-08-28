#!/usr/bin/env bash
# T401 / F-T385-4 -- THE RED DRIVE: A PLANTED .zsh FAIL-OPEN, WITH A HEALTHY CONTROL.
#
# The claim under test is NOT "the selector says .sh and .py". Anyone can read that. The claim
# is BEHAVIOURAL: a genuinely fail-open instrument, written in zsh, walks past the censuses and
# the bar stays GREEN -- and the SAME instrument, under a one-token-wider selector, is caught.
# Without both halves this is an opinion about a glob.
#
# ===========================================================================================
# WHY THE BAIT IS A RUNTIME COPY AND NOT A HEREDOC. THIS INSTRUMENT'S FIRST DRAFT TOOK THE
# WHOLE BAR TO EXIT 2, THREE TIMES OVER, AND THAT IS RECORDED HERE RATHER THAN QUIETLY FIXED.
# ===========================================================================================
# Draft 1 wrote the bait with `cat >... <<'PLANTED'` heredocs and carried a comment saying
# "the DEFECT LIVES IN SCRATCH, never in a tracked file". That comment was FALSE and the bar
# said so within a minute of the commit:
#
#   conformance: THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER (- pinned, + measured):
#   + TIER1 .softhouse/capture/t401-zsh-census-gap/instruments/40-red-drive-planted-zsh.sh
#   T316-DEADPATH-FRONTIER: REFUSED rows=110 pinned=108 added=2 removed=0
#
# A heredoc body is TEXT IN THE TRACKED FILE. The linter reads bytes, not intent: the bait's
# dead worktree root and its reassuring failure arm were mine, at my path, and this driver
# became a genuine TIER1 fail-open row -- while ALSO adding two dead-path rows, one from the
# bait's fake `.softhouse/` literal and one from the scratch filename in 20-cost-of-extending.
# The instrument written to demonstrate a blind census was itself caught by the census that
# can see. That is the guards working, and it is the second time in this one task that prose
# in a tracked file became a graded row (the first moved deadOccurrences 108 -> 109).
#
# So the bait is now CHOSEN AT RUNTIME FROM THE TREE, never authored:
#   BAIT-FO  = a file the shipped linter ALREADY ranks TIER1, copied to a `.zsh` name.
#   BAIT-DP  = a file the shipped census ALREADY counts as naming a dead path, copied likewise.
#   CONTROL  = a file that IS a repo-wide search instrument and is on NEITHER list, copied
#              likewise.
# This is strictly the better experiment as well as the safer one. The bait and the control
# differ from their originals in EXACTLY ONE CHARACTER SEQUENCE -- the extension -- so a
# difference in verdict cannot be attributed to anything else. Nothing in this file spells a
# dead path, and nothing in it spells a reassuring failure arm.
#
# NOTHING IS COMMITTED AND THE REAL INDEX IS NEVER TOUCHED. The copies are written untracked
# and added to a COPY of the index via GIT_INDEX_FILE, which the censuses inherit. The trap
# removes them, and the teardown asserts the tree.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 9
ROOT="$(pwd)"
G="$ROOT/.softhouse/capture/t401-zsh-census-gap"
LINT="$ROOT/.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
CENSUS="$ROOT/.softhouse/capture/t316-dead-path-guards/census_dead_paths.py"

for f in "$LINT" "$CENSUS"; do
  [ -f "$f" ] || { printf 'T401 RED ABORT (2): dependency absent: %s\n' "$f" >&2; exit 2; }
done

D="$(mktemp -d "${TMPDIR:-/tmp}/t401-red.XXXXXXXXXX")" || exit 2
PLANT="$G/.t401-plant"
# Assembled from $G so that no `.softhouse/`-rooted literal for a file that does not exist is
# ever spelled in this source. The dead-path census extracts literals CONTAINING `.softhouse/`;
# a bare basename is not one.
CENSUS_ZSH="$G/.t401-red-census-zsh.py"
trap 'rm -rf "$D" "$PLANT" "$CENSUS_ZSH"' EXIT INT TERM
mkdir -p "$PLANT"

# ---- the widened copies (same one-token patches as 20-cost-of-extending.sh) ----
sed 's/f\.endswith((\"\.sh\", \"\.py\"))/f.endswith((".sh", ".py", ".zsh"))/' "$LINT" >"$D/lint-zsh.py"
sed 's|"git", "ls-files", "\.softhouse/\*\.py", "\.softhouse/\*\.sh"|"git", "ls-files", ".softhouse/*.py", ".softhouse/*.sh", ".softhouse/*.zsh"|' "$CENSUS" >"$CENSUS_ZSH"
cmp -s "$LINT" "$D/lint-zsh.py" && { printf 'T401 RED ABORT (2): failopen patch was a no-op.\n' >&2; exit 2; }
cmp -s "$CENSUS" "$CENSUS_ZSH"  && { printf 'T401 RED ABORT (2): deadpath patch was a no-op.\n' >&2; exit 2; }

# ---------------------------------------------------------------------------------------
# BASELINE, AND THE BAIT/CONTROL CHOSEN FROM IT.
# ---------------------------------------------------------------------------------------
FAILOPEN_LINT_JSON="$D/b.json" python3 "$LINT" >"$D/base-fo.txt" 2>&1
LC_ALL=C grep -qF 'T238 FAIL-OPEN LINT' "$D/base-fo.txt" \
  || { printf 'T401 RED ABORT (2): the shipped linter produced no banner.\n' >&2; exit 2; }
python3 "$CENSUS" >"$D/base-dp.txt" 2>&1
LC_ALL=C grep -q '^T316-DEADPATH-CENSUS:' "$D/base-dp.txt" \
  || { printf 'T401 RED ABORT (2): the shipped census produced no summary line.\n' >&2; exit 2; }

LC_ALL=C sed -n 's/^FAILOPEN-FRONTIER TIER1 \(.*\.sh\)$/\1/p' "$D/base-fo.txt" >"$D/tier1"
LC_ALL=C sed -n 's/^  \(\.softhouse\/.*\.sh\)$/\1/p' "$D/base-dp.txt" | LC_ALL=C sort -u >"$D/deadfiles"
BAIT_FO="$(LC_ALL=C sed -n '1p' "$D/tier1")"
BAIT_DP="$(LC_ALL=C sed -n '1p' "$D/deadfiles")"
[ -n "$BAIT_FO" ] || { printf 'T401 RED ABORT (2): no TIER1 .sh row to use as bait.\n' >&2; exit 2; }
[ -n "$BAIT_DP" ] || { printf 'T401 RED ABORT (2): no dead-path .sh file to use as bait.\n' >&2; exit 2; }

# The CONTROL must be a repo-wide search instrument -- otherwise "it was not flagged" is
# trivially true and the control tests nothing. Same `rw` regex conformance.sh:2122 uses.
rw='(git[[:space:]]+(-[A-Za-z][[:space:]]+[^[:space:]]+[[:space:]]+|--[A-Za-z-]+=[^[:space:]]+[[:space:]]+|-[A-Za-z]+[[:space:]]+)*(grep|ls-files)|grep[[:space:]]+-[a-zA-Z]*[rR])'
LC_ALL=C git grep -l -E "$rw" -- '*.sh' | LC_ALL=C sort >"$D/searchers"
LC_ALL=C sed -n 's/^FAILOPEN-FRONTIER [A-Z0-9]* //p' "$D/base-fo.txt" | LC_ALL=C sort -u >"$D/frontier"
LC_ALL=C comm -23 "$D/searchers" "$D/frontier" >"$D/c1"
LC_ALL=C comm -23 "$D/c1" "$D/deadfiles" >"$D/c2"
CONTROL="$(LC_ALL=C sed -n '1p' "$D/c2")"
[ -n "$CONTROL" ] || { printf 'T401 RED ABORT (2): no healthy search instrument to use as control.\n' >&2; exit 2; }

cp "$ROOT/$BAIT_FO"  "$PLANT/bait-failopen.zsh" || exit 2
cp "$ROOT/$BAIT_DP"  "$PLANT/bait-deadpath.zsh" || exit 2
cp "$ROOT/$CONTROL"  "$PLANT/control.zsh"       || exit 2

# ---- a scratch INDEX, so the copies are "tracked" for the censuses only ----
REALIDX="$(git rev-parse --git-path index)"
cp "$REALIDX" "$D/index" || { printf 'T401 RED ABORT (2): could not copy the index.\n' >&2; exit 2; }
export GIT_INDEX_FILE="$D/index"
git add -f "$PLANT/bait-failopen.zsh" "$PLANT/bait-deadpath.zsh" "$PLANT/control.zsh" \
  || { printf 'T401 RED ABORT (2): could not stage the copies.\n' >&2; exit 2; }
staged="$(git ls-files | LC_ALL=C grep -c 't401-plant' || true)"
if [ "$staged" -ne 3 ]; then
  printf 'T401 RED ABORT (2): expected 3 planted files in the scratch index, saw %s.\n' "$staged" >&2
  printf 'T401 RED ABORT (2): a drive whose bait is outside the corpus proves nothing.\n' >&2
  exit 2
fi

R="$G/evidence"; mkdir -p "$R"
out="$R/40-red-drive.txt"; : >"$out"
say() { printf '%s\n' "$*" >>"$out"; }

say "T401 RED DRIVE -- PLANTED .zsh FAIL-OPEN vs HEALTHY CONTROL"
say "commit  : $(git rev-parse --short HEAD)"
say "index   : SCRATCH copy of the real index; the real index is untouched"
say "BAIT-FO : $BAIT_FO"
say "          -> copied verbatim to .t401-plant/bait-failopen.zsh (extension is the ONLY change)"
say "BAIT-DP : $BAIT_DP"
say "          -> copied verbatim to .t401-plant/bait-deadpath.zsh"
say "CONTROL : $CONTROL"
say "          -> copied verbatim to .t401-plant/control.zsh; it IS a repo-wide search"
say "             instrument and is on NEITHER the frontier nor the dead-file list."
say ""

fail=0
# ---- ARM 1: SHIPPED fail-open selector ----
FAILOPEN_LINT_JSON="$D/a1.json" python3 "$LINT" >"$D/a1.txt" 2>&1
a1c="$(LC_ALL=C sed -n 's/^corpus    : \([0-9][0-9]*\) tracked.*$/\1/p' "$D/a1.txt")"
a1n="$(LC_ALL=C grep -c '^FAILOPEN-FRONTIER ' "$D/a1.txt" || true)"
a1p="$(LC_ALL=C grep -c 't401-plant' "$D/a1.txt" || true)"
say "ARM 1  SHIPPED failopen selector, bait staged"
say "       corpus $a1c   frontier rows $a1n   rows naming a planted file: $a1p"
if [ "$a1p" -ne 0 ]; then say "       UNEXPECTED: the shipped selector reached the bait."; fail=1
else say "       => BLIND. A byte-identical TIER1 fail-open is invisible under a .zsh name."; fi
say ""

# ---- ARM 2: WIDENED fail-open selector ----
FAILOPEN_LINT_JSON="$D/a2.json" python3 "$D/lint-zsh.py" >"$D/a2.txt" 2>&1
a2c="$(LC_ALL=C sed -n 's/^corpus    : \([0-9][0-9]*\) tracked.*$/\1/p' "$D/a2.txt")"
a2n="$(LC_ALL=C grep -c '^FAILOPEN-FRONTIER ' "$D/a2.txt" || true)"
say "ARM 2  WIDENED failopen selector (+.zsh), same bait"
say "       corpus $a2c   frontier rows $a2n"
LC_ALL=C grep '^FAILOPEN-FRONTIER ' "$D/a2.txt" | LC_ALL=C grep 't401-plant' >"$D/a2.hits" || true
if LC_ALL=C grep -q 'bait-failopen\.zsh' "$D/a2.hits"; then
  say "       CAUGHT the planted fail-open:"
  sed 's/^/         /' "$D/a2.hits" >>"$out"
else
  say "       DRIVE FAILED: bait-failopen.zsh did not reach the frontier. Rows seen:"
  sed 's/^/         /' "$D/a2.hits" >>"$out"
  fail=1
fi
if LC_ALL=C grep -q 'control\.zsh' "$D/a2.hits"; then
  say "       DRIVE FAILED: the CONTROL was flagged. A widening that reddens a healthy search"
  say "       instrument is noise, not coverage."
  fail=1
else
  say "       CONTROL not flagged -- the widening discriminates."
fi
say ""

# ---- ARM 3: SHIPPED dead-path census ----
python3 "$CENSUS" >"$D/a3.txt" 2>&1
a3="$(LC_ALL=C grep '^T316-DEADPATH-CENSUS:' "$D/a3.txt" || true)"
a3p="$(LC_ALL=C grep -c 't401-plant' "$D/a3.txt" || true)"
say "ARM 3  SHIPPED dead-path selector, bait staged"
say "       $a3"
say "       rows naming a planted file: $a3p"
if [ "$a3p" -ne 0 ]; then say "       UNEXPECTED: the shipped selector reached the bait."; fail=1
else say "       => BLIND. A byte-identical dead-path namer is invisible under a .zsh name."; fi
say ""

# ---- ARM 4: WIDENED dead-path census ----
python3 "$CENSUS_ZSH" >"$D/a4.txt" 2>&1
a4="$(LC_ALL=C grep '^T316-DEADPATH-CENSUS:' "$D/a4.txt" || true)"
say "ARM 4  WIDENED dead-path selector (+.zsh), same bait"
say "       $a4"
LC_ALL=C grep -A1 't401-plant' "$D/a4.txt" >"$D/a4.hits" 2>/dev/null || true
if LC_ALL=C grep -q 'bait-deadpath\.zsh' "$D/a4.hits"; then
  say "       CAUGHT the planted dead path:"
  sed 's/^/         /' "$D/a4.hits" >>"$out"
else
  say "       DRIVE FAILED: bait-deadpath.zsh is not among the dead files."
  fail=1
fi
if LC_ALL=C grep -q '\bcontrol\.zsh' "$D/a4.hits"; then
  say "       DRIVE FAILED: the CONTROL was counted dead."
  fail=1
else
  say "       CONTROL not counted dead -- the widening discriminates."
fi
say ""

# ---- TEARDOWN, ASSERTED ----
unset GIT_INDEX_FILE
rm -rf "$PLANT" "$CENSUS_ZSH"
say "TEARDOWN"
say "       GIT_INDEX_FILE unset; scratch index discarded; copies removed"
say "       residue under .t401-plant: $(git status --porcelain | LC_ALL=C grep -c 't401-plant' || true)  (must be 0)"
if [ "$(git status --porcelain | LC_ALL=C grep -c 't401-plant' || true)" -ne 0 ]; then fail=1; fi

if [ "$fail" -ne 0 ]; then
  say ""
  say "T401-RED-DRIVE: FAILED"
  cat "$out"
  exit 1
fi
say ""
say "T401-RED-DRIVE: PASSED -- blind before, caught after, control spared in both directions."
cat "$out"
