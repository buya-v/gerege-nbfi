#!/usr/bin/env bash
# T401 / F-T385-4 -- THE RED DRIVE: A PLANTED .zsh FAIL-OPEN, WITH A HEALTHY CONTROL.
#
# The claim under test is NOT "the selector says .sh and .py". Anyone can read that. The claim
# is BEHAVIOURAL: a genuinely fail-open instrument, written in zsh, walks past all four censuses
# and the bar stays GREEN -- and the SAME instrument, under a one-token-wider selector, is
# caught. Without both halves this is an opinion about a glob.
#
# FOUR ARMS, and the control is what makes the other three mean anything:
#   RED-FO   a .zsh that IS fail-open: dead absolute worktree root, `git grep` inside it,
#            and `|| echo "(no hits)"` -- the exact shape of the pinned TIER1 sweep-ORIGINAL.sh.
#   RED-DP   a .zsh naming a `.softhouse/` path the repository does not contain.
#   GREEN-C  a .zsh with the SAME search, rooted at a path that resolves, failing CLOSED with
#            `|| exit 2` and printing no reassurance. If the widened selector flags THIS, the
#            widening is not a fix, it is noise -- so a flagged control is a FAILED drive.
#   ALSO     the same three planted under the SHIPPED selector, which must see NOTHING.
#
# NOTHING IS COMMITTED AND THE REAL INDEX IS NEVER TOUCHED. The planted files are written into
# the worktree untracked and added to a COPY of the index via GIT_INDEX_FILE, which every
# `git ls-files` / `git grep` in the censuses inherits. The trap removes both. `git status`
# is asserted clean at the end, because a red drive that leaves its evidence in the tree is
# how a planted defect becomes a real one.
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
CENSUS_ZSH="$G/.t401-red-census-zsh.py"
trap 'rm -rf "$D" "$PLANT" "$CENSUS_ZSH"' EXIT INT TERM
mkdir -p "$PLANT"

# ---- the widened copies (same one-token patches as 20-cost-of-extending.sh) ----
sed 's/f\.endswith((\"\.sh\", \"\.py\"))/f.endswith((".sh", ".py", ".zsh"))/' "$LINT" >"$D/lint-zsh.py"
sed 's|"git", "ls-files", "\.softhouse/\*\.py", "\.softhouse/\*\.sh"|"git", "ls-files", ".softhouse/*.py", ".softhouse/*.sh", ".softhouse/*.zsh"|' "$CENSUS" >"$CENSUS_ZSH"
cmp -s "$LINT" "$D/lint-zsh.py"   && { printf 'T401 RED ABORT (2): failopen patch was a no-op.\n' >&2; exit 2; }
cmp -s "$CENSUS" "$CENSUS_ZSH"    && { printf 'T401 RED ABORT (2): deadpath patch was a no-op.\n' >&2; exit 2; }

# ---------------------------------------------------------------------------------------
# THE PLANTED INSTRUMENTS. Written by heredoc so the DEFECT LIVES IN SCRATCH, never in a
# tracked file: this driver must not itself become a frontier row for carrying its own bait.
# ---------------------------------------------------------------------------------------
cat >"$PLANT/red-failopen.zsh" <<'PLANTED'
#!/usr/bin/env zsh
# T401 PLANTED BAIT -- a deliberately FAIL-OPEN sweep, in zsh. Never run for its result.
set -u
WT=/Users/buv/gerege-nbfi/.claude/worktrees/agent-t401-does-not-exist
run() {
  local label="$1" re="$2"
  echo "########## PATTERN $label"
  ( cd "$WT" && git grep -n -I -i -E "$re" -- . ) || echo "   (no hits)"
}
run P1 'floating.?point'
run P2 'BigDecimal'
PLANTED

cat >"$PLANT/red-deadpath.zsh" <<'PLANTED'
#!/usr/bin/env zsh
# T401 PLANTED BAIT -- names a `.softhouse/` path the repository does not contain.
set -u
ref=".softhouse/capture/t401-zsh-census-gap/this-file-is-not-in-the-index.json"
printf 'reading %s\n' "$ref"
PLANTED

cat >"$PLANT/green-control.zsh" <<'PLANTED'
#!/usr/bin/env zsh
# T401 PLANTED CONTROL -- the SAME search, HEALTHY. Root resolves, failure is CLOSED,
# nothing reassuring is printed on the failure arm, and every path it names is tracked.
set -eu
WT="$(git rev-parse --show-toplevel)" || exit 2
[ -d "$WT" ] || exit 2
ref=".softhouse/capture/t316-dead-path-guards/census_dead_paths.py"
[ -f "$WT/$ref" ] || exit 2
run() {
  local label="$1" re="$2"
  echo "########## PATTERN $label"
  ( cd "$WT" && git grep -n -I -i -E "$re" -- . )
  local rc=$?
  if [ "$rc" -gt 1 ]; then exit 2; fi
}
run P1 'floating.?point'
PLANTED

# ---- a scratch INDEX, so the planted files are "tracked" for the censuses only ----
REALIDX="$(git rev-parse --git-path index)"
cp "$REALIDX" "$D/index" || { printf 'T401 RED ABORT (2): could not copy the index.\n' >&2; exit 2; }
export GIT_INDEX_FILE="$D/index"
git add -f "$PLANT/red-failopen.zsh" "$PLANT/red-deadpath.zsh" "$PLANT/green-control.zsh" \
  || { printf 'T401 RED ABORT (2): could not stage the planted files.\n' >&2; exit 2; }
staged="$(git ls-files | LC_ALL=C grep -c 't401-plant' || true)"
if [ "$staged" -ne 3 ]; then
  printf 'T401 RED ABORT (2): expected 3 planted files in the scratch index, saw %s.\n' "$staged" >&2
  printf 'T401 RED ABORT (2): a drive whose bait is not in the corpus proves nothing.\n' >&2
  exit 2
fi

R="$G/evidence"
mkdir -p "$R"
out="$R/40-red-drive.txt"
: >"$out"
say() { printf '%s\n' "$*" >>"$out"; }

say "T401 RED DRIVE -- PLANTED .zsh FAIL-OPEN vs HEALTHY CONTROL"
say "commit : $(git rev-parse --short HEAD)"
say "index  : SCRATCH copy ($GIT_INDEX_FILE); the real index is untouched"
say "planted: 3 files, staged in the scratch index only:"
git ls-files | LC_ALL=C grep 't401-plant' | sed 's/^/         /' >>"$out"
say ""

fail=0
# ---------------------------------------------------------------------------------------
# ARM 1 -- SHIPPED fail-open selector. MUST SEE NOTHING.
# ---------------------------------------------------------------------------------------
FAILOPEN_LINT_JSON="$D/a1.json" python3 "$LINT" >"$D/a1.txt" 2>&1
a1c="$(LC_ALL=C sed -n 's/^corpus    : \([0-9][0-9]*\) tracked.*$/\1/p' "$D/a1.txt")"
a1n="$(LC_ALL=C grep -c '^FAILOPEN-FRONTIER ' "$D/a1.txt" || true)"
a1p="$(LC_ALL=C grep -c 't401-plant' "$D/a1.txt" || true)"
say "ARM 1  SHIPPED failopen selector, bait staged"
say "       corpus $a1c   frontier rows $a1n   rows naming the bait: $a1p"
if [ "$a1p" -ne 0 ]; then say "       UNEXPECTED: the shipped selector saw the bait."; fail=1
else say "       => BLIND, as measured. A fail-open zsh instrument is INVISIBLE. This is the gap."; fi
say ""

# ---------------------------------------------------------------------------------------
# ARM 2 -- WIDENED fail-open selector. MUST FLAG THE BAIT AND SPARE THE CONTROL.
# ---------------------------------------------------------------------------------------
FAILOPEN_LINT_JSON="$D/a2.json" python3 "$D/lint-zsh.py" >"$D/a2.txt" 2>&1
a2c="$(LC_ALL=C sed -n 's/^corpus    : \([0-9][0-9]*\) tracked.*$/\1/p' "$D/a2.txt")"
a2n="$(LC_ALL=C grep -c '^FAILOPEN-FRONTIER ' "$D/a2.txt" || true)"
say "ARM 2  WIDENED failopen selector (+.zsh), same bait"
say "       corpus $a2c   frontier rows $a2n"
LC_ALL=C grep '^FAILOPEN-FRONTIER ' "$D/a2.txt" | LC_ALL=C grep 't401-plant' >"$D/a2.hits" || true
if LC_ALL=C grep -q 'red-failopen\.zsh' "$D/a2.hits"; then
  say "       CAUGHT the planted fail-open:"
  sed 's/^/         /' "$D/a2.hits" >>"$out"
else
  say "       FAILED: the widened selector did NOT put red-failopen.zsh on the frontier."
  say "       (frontier rows naming any bait:)"
  sed 's/^/         /' "$D/a2.hits" >>"$out"
  fail=1
fi
if LC_ALL=C grep -q 'green-control\.zsh' "$D/a2.hits"; then
  say "       FAILED: the CONTROL was flagged. A widening that reddens healthy files is noise."
  fail=1
else
  say "       CONTROL green-control.zsh NOT flagged -- the widening discriminates."
fi
say ""

# ---------------------------------------------------------------------------------------
# ARM 3 -- SHIPPED dead-path census. MUST SEE NOTHING.
# ---------------------------------------------------------------------------------------
python3 "$CENSUS" >"$D/a3.txt" 2>&1
a3="$(LC_ALL=C grep '^T316-DEADPATH-CENSUS:' "$D/a3.txt" || true)"
a3p="$(LC_ALL=C grep -c 't401-plant' "$D/a3.txt" || true)"
say "ARM 3  SHIPPED dead-path selector, bait staged"
say "       $a3"
say "       rows naming the bait: $a3p"
if [ "$a3p" -ne 0 ]; then say "       UNEXPECTED: the shipped selector saw the bait."; fail=1
else say "       => BLIND. A zsh instrument naming a path the repo does not contain is INVISIBLE."; fi
say ""

# ---------------------------------------------------------------------------------------
# ARM 4 -- WIDENED dead-path census. MUST COUNT THE BAIT AND SPARE THE CONTROL.
# ---------------------------------------------------------------------------------------
python3 "$CENSUS_ZSH" >"$D/a4.txt" 2>&1
a4="$(LC_ALL=C grep '^T316-DEADPATH-CENSUS:' "$D/a4.txt" || true)"
say "ARM 4  WIDENED dead-path selector (+.zsh), same bait"
say "       $a4"
LC_ALL=C grep -A1 't401-plant' "$D/a4.txt" >"$D/a4.hits" 2>/dev/null || true
if LC_ALL=C grep -q 'red-deadpath\.zsh' "$D/a4.hits"; then
  say "       CAUGHT the planted dead path:"
  sed 's/^/         /' "$D/a4.hits" >>"$out"
else
  say "       FAILED: red-deadpath.zsh is not among the dead files."
  fail=1
fi
if LC_ALL=C grep -q 'green-control\.zsh' "$D/a4.hits"; then
  say "       FAILED: the CONTROL was counted dead. Its every literal is tracked."
  fail=1
else
  say "       CONTROL green-control.zsh NOT counted dead -- the widening discriminates."
fi
say ""

# ---------------------------------------------------------------------------------------
# TEARDOWN, ASSERTED. The real index and the working tree must be exactly as found.
# ---------------------------------------------------------------------------------------
unset GIT_INDEX_FILE
rm -rf "$PLANT" "$CENSUS_ZSH"
dirty="$(git status --porcelain | LC_ALL=C grep -c '' || true)"
say "TEARDOWN"
say "       GIT_INDEX_FILE unset; scratch index discarded; planted files removed"
say "       git status --porcelain lines: $dirty  (0 or only this run's evidence is expected)"
git status --porcelain | sed 's/^/         /' >>"$out"

if [ "$fail" -ne 0 ]; then
  say ""
  say "T401-RED-DRIVE: FAILED"
  cat "$out"
  exit 1
fi
say ""
say "T401-RED-DRIVE: PASSED -- blind before, caught after, control spared in both directions."
cat "$out"
