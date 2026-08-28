#!/usr/bin/env bash
# T401 / F-T385-4 -- RED DRIVE FOR THE TWO SELECTORS THAT LIVE INSIDE conformance.sh (S3, S4).
#
# `conformance.sh` is held by T404 this wave, so S3 and S4 can only be shipped as a REQUEST.
# "A patch that has not been driven red is a proposal, not a request." S1 and S2 are driven in
# 40-red-drive-planted-zsh.sh by running the real instruments. S3 and S4 are spelled INSIDE the
# held file, so they are driven here at SELECTOR level, and that limit is stated rather than
# glossed: what is proven is that the shipped pathspec does not REACH a planted `.zsh` and the
# widened one does. What is NOT proven here is the whole guard's behaviour end to end, because
# running that would require editing the held file.
#
# THE TRANSLITERATION IS BYTE-ASSERTED against the live conformance.sh before any figure is
# printed (see 30-conformance-own-selectors.sh, same fragments, same refusal). A selector that
# has drifted from the one under test makes every number below a statement about a different
# search -- P-70.
#
# BAIT IS A RUNTIME COPY, NEVER A HEREDOC. Reason recorded at length in
# 40-red-drive-planted-zsh.sh: this task has already turned the bar red twice by writing bait
# text, and once more by writing an example path, into a TRACKED file.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 9
ROOT="$(pwd)"
G="$ROOT/.softhouse/capture/t401-zsh-census-gap"
CONF="$ROOT/.softhouse/conformance.sh"
[ -f "$CONF" ] || { printf 'T401 S3/S4 ABORT (2): conformance.sh absent.\n' >&2; exit 2; }

rw='(git[[:space:]]+(-[A-Za-z][[:space:]]+[^[:space:]]+[[:space:]]+|--[A-Za-z-]+=[^[:space:]]+[[:space:]]+|-[A-Za-z]+[[:space:]]+)*(grep|ls-files)|grep[[:space:]]+-[a-zA-Z]*[rR])'
as_head='^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*='
as_tail=']?/(tmp|private/tmp|var/tmp)/'
as='^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*=["'"'"']?/(tmp|private/tmp|var/tmp)/'
for frag in "$rw" "$as_head" "$as_tail"; do
  LC_ALL=C grep -qF "$frag" "$CONF" || {
    printf 'T401 S3/S4 ABORT (2): selector fragment absent from conformance.sh; it drifted.\n' >&2
    exit 2; }
done

D="$(mktemp -d "${TMPDIR:-/tmp}/t401-s34.XXXXXXXXXX")" || exit 2
PLANT="$G/.t401-plant34"
# FOURTH instance in this one task of "a `.softhouse/`-rooted literal for a path that does not
# exist is a DEAD-PATH ROW". Written whole, this line put a row on this file and took the
# frontier to 109. The prefix is a variable that RESOLVES (the guards directory is tracked);
# the scratch basename carries no `.softhouse/` and so is not a literal the census extracts.
GDROOT="$ROOT/.softhouse/guards"
GPLANT="$GDROOT/.t401-plant34"
trap 'rm -rf "$D" "$PLANT" "$GPLANT"' EXIT INT TERM
mkdir -p "$PLANT" "$GPLANT"

R="$G/evidence"; mkdir -p "$R"
out="$R/45-red-drive-s3-s4.txt"; : >"$out"
say() { printf '%s\n' "$*" >>"$out"; }
fail=0

say "T401 RED DRIVE -- S3 (host-state census) and S4 (guards-dir census), both spelled in"
say "the T404-held conformance.sh. Driven at SELECTOR level; the limit is stated above."
say "commit : $(git rev-parse --short HEAD)"
say "selector fragments VERIFIED byte-present in .softhouse/conformance.sh"
say ""

# =========================================================================================
# S3 -- HOST-STATE CENSUS.  conformance.sh:2131  `git grep -l -E "$rw" -- '*.sh' '*.py'`
# =========================================================================================
# BAIT: a file that is BOTH a repo-wide search instrument AND assigns a literal /tmp path --
# i.e. a file already ON the host-state pin. Chosen at runtime from the census itself.
LC_ALL=C git grep -l -E "$rw" -- '*.sh' '*.py' >"$D/searchers"
LC_ALL=C git grep -l -E "$as" -- '*.sh' '*.py' >"$D/assigners"
LC_ALL=C sort "$D/searchers" >"$D/s"; LC_ALL=C sort "$D/assigners" >"$D/a"
LC_ALL=C comm -12 "$D/s" "$D/a" >"$D/both"
BAIT_HS="$(LC_ALL=C sed -n '1p' "$D/both")"
LC_ALL=C comm -23 "$D/s" "$D/a" >"$D/clean"
CTRL_HS="$(LC_ALL=C sed -n '1p' "$D/clean")"
[ -n "$BAIT_HS" ] || { printf 'T401 S3 ABORT (2): no pinned host-state site to use as bait.\n' >&2; exit 2; }
[ -n "$CTRL_HS" ] || { printf 'T401 S3 ABORT (2): no clean search instrument to use as control.\n' >&2; exit 2; }
cp "$ROOT/$BAIT_HS" "$PLANT/bait-hoststate.zsh" || exit 2
cp "$ROOT/$CTRL_HS" "$PLANT/control-hoststate.zsh" || exit 2

# S4 -- BAIT: an existing tracked guards checker, copied to a .zsh name inside the guards dir.
GD=".softhouse/guards"
BAIT_G="$(git ls-files -- ":(glob)$GD/**/*.sh" ":(glob)$GD/*.sh" | LC_ALL=C sed -n '1p')"
[ -n "$BAIT_G" ] || { printf 'T401 S4 ABORT (2): no guards .sh to use as bait.\n' >&2; exit 2; }
cp "$ROOT/$BAIT_G" "$GPLANT/unwired-checker.zsh" || exit 2

REALIDX="$(git rev-parse --git-path index)"
cp "$REALIDX" "$D/index" || exit 2
export GIT_INDEX_FILE="$D/index"
git add -f "$PLANT/bait-hoststate.zsh" "$PLANT/control-hoststate.zsh" "$GPLANT/unwired-checker.zsh" || exit 2
staged="$(git ls-files | LC_ALL=C grep -c 't401-plant34' || true)"
if [ "$staged" -ne 3 ]; then
  printf 'T401 S3/S4 ABORT (2): expected 3 planted files, saw %s.\n' "$staged" >&2; exit 2
fi

say "== S3  HOST-STATE CENSUS (conformance.sh:2131) =="
say "   BAIT    $BAIT_HS  (already on the host-state pin: a repo-wide search"
say "           instrument that assigns a literal /tmp path) -> .zsh copy"
say "   CONTROL $CTRL_HS  (a repo-wide search instrument with NO such"
say "           assignment) -> .zsh copy"
# ARM A: shipped pathspec
LC_ALL=C git grep -l -E "$rw" -- '*.sh' '*.py' >"$D/popA"
LC_ALL=C git grep -n -E "$as" -- '*.sh' '*.py' >"$D/rowsA" 2>/dev/null || true
nA="$(LC_ALL=C grep -c 't401-plant34' "$D/rowsA" || true)"
pA="$(LC_ALL=C grep -c 't401-plant34' "$D/popA" || true)"
say "   ARM A  SHIPPED pathspec '*.sh' '*.py'"
say "          planted files reaching the POPULATION : $pA"
say "          planted host-state ROWS censused      : $nA"
if [ "$pA" -ne 0 ] || [ "$nA" -ne 0 ]; then say "          UNEXPECTED: the shipped pathspec reached the bait."; fail=1
else say "          => BLIND. A byte-identical host-state site is invisible under a .zsh name."; fi
# ARM B: widened pathspec
LC_ALL=C git grep -l -E "$rw" -- '*.sh' '*.py' '*.zsh' >"$D/popB"
LC_ALL=C git grep -n -E "$as" -- '*.sh' '*.py' '*.zsh' >"$D/rowsB" 2>/dev/null || true
say "   ARM B  WIDENED pathspec '*.sh' '*.py' '*.zsh'"
LC_ALL=C grep 't401-plant34' "$D/popB" >"$D/popB.hits" || true
LC_ALL=C grep 't401-plant34' "$D/rowsB" >"$D/rowsB.hits" || true
if LC_ALL=C grep -q 'bait-hoststate\.zsh' "$D/popB.hits" && LC_ALL=C grep -q 'bait-hoststate\.zsh' "$D/rowsB.hits"; then
  say "          CAUGHT the planted host-state site:"
  LC_ALL=C sed -n '1,4p' "$D/rowsB.hits" | sed 's/^/            /' >>"$out"
else
  say "          DRIVE FAILED: the widened pathspec did not censusd the bait."
  fail=1
fi
if LC_ALL=C grep -q 'control-hoststate\.zsh' "$D/rowsB.hits"; then
  say "          DRIVE FAILED: the CONTROL produced a host-state row."
  fail=1
else
  say "          CONTROL is in the widened POPULATION but produces NO row -- the widening"
  say "          discriminates, and it discriminates on the assignment, not on the extension."
  if ! LC_ALL=C grep -q 'control-hoststate\.zsh' "$D/popB.hits"; then
    say "          DRIVE FAILED: the control never entered the population, so 'no row' is vacuous."
    fail=1
  fi
fi
say ""

# =========================================================================================
# S4 -- GUARDS-DIRECTORY UNWIRED-CHECKER CENSUS.  conformance.sh:3267-3269
# =========================================================================================
say "== S4  GUARDS-DIR UNWIRED-CHECKER CENSUS (conformance.sh:3267-3269) =="
say "   BAIT $BAIT_G -> .zsh copy inside the guards directory, invoked by nothing,"
say "        declared nowhere, carrying no REACHED-BY row."
a="$(git ls-files -- ":(glob)$GD/**/*.sh" ":(glob)$GD/**/*.py" ":(glob)$GD/**/*.go" ":(glob)$GD/*.sh" ":(glob)$GD/*.py" ":(glob)$GD/*.go" | LC_ALL=C grep -c 't401-plant34' || true)"
b="$(git ls-files -- ":(glob)$GD/**/*.sh" ":(glob)$GD/**/*.py" ":(glob)$GD/**/*.go" ":(glob)$GD/**/*.zsh" ":(glob)$GD/*.sh" ":(glob)$GD/*.py" ":(glob)$GD/*.go" ":(glob)$GD/*.zsh" | LC_ALL=C grep -c 't401-plant34' || true)"
say "   ARM A  SHIPPED pathspec (sh|py|go)   planted checkers in population: $a"
say "   ARM B  WIDENED pathspec (+zsh)       planted checkers in population: $b"
if [ "$a" -ne 0 ]; then say "          UNEXPECTED: the shipped pathspec reached the bait."; fail=1
else say "          => BLIND. An unwired zsh checker can land in the guards directory today."; fi
if [ "$b" -lt 1 ]; then say "          DRIVE FAILED: the widened pathspec did not reach the bait."; fail=1
else say "          CAUGHT. Under the widened pathspec the unwired zsh checker is a member,"; say "          and members must be INVOKED, DECLARED or REACHED-BY."; fi
say ""

unset GIT_INDEX_FILE
rm -rf "$PLANT" "$GPLANT"
res="$(git status --porcelain | LC_ALL=C grep -c 't401-plant34' || true)"
say "TEARDOWN"
say "       GIT_INDEX_FILE unset; scratch index discarded; copies removed"
say "       residue: $res  (must be 0)"
[ "$res" -eq 0 ] || fail=1

if [ "$fail" -ne 0 ]; then
  say ""; say "T401-RED-DRIVE-S3-S4: FAILED"; cat "$out"; exit 1
fi
say ""
say "T401-RED-DRIVE-S3-S4: PASSED -- blind before, reached after, control spared."
cat "$out"
