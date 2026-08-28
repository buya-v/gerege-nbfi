#!/usr/bin/env bash
# T401 / F-T385-4 -- WHAT DOES EXTENDING THE SELECTOR TO .zsh ACTUALLY COST?
#
# "Say what it costs before you choose." The cost is not arguable from the file count; it is
# the number of NEW FRONTIER ROWS and NEW DEAD OCCURRENCES that appear when the two censuses
# are allowed to see 121 tracked .zsh files. So this MEASURES it, by running both censuses
# twice: once as shipped, once with .zsh in the selector.
#
# THE COPIES ARE MATERIALISED IN SCRATCH AND NEVER COMMITTED, for three reasons that are all
# defects this program has already paid for:
#   1. `50-failopen-lint.py` and `census_dead_paths.py` belong to T238 and T316. Editing them
#      in place is outside this grant.
#   2. A COMMITTED copy would enter both corpora -- it is a tracked .py under .softhouse/ --
#      and would move the very figures this instrument exists to measure. The measurement
#      would perturb its own subject.
#   3. This file's own first draft moved deadOccurrences 108 -> 109 by spelling one fake path
#      in a comment. A committed 1400-line copy naming scratch paths throughout would be far
#      worse. Scratch, from mktemp, is the only safe place for it.
#
# NO LITERAL /tmp ASSIGNMENT (mktemp -d instead): a NAME=/tmp/... line in a tracked instrument
# that also runs a repo-wide search is a row in conformance.sh's HOSTSTATE census.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 9
ROOT="$(pwd)"

LINT="$ROOT/.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
CENSUS="$ROOT/.softhouse/capture/t316-dead-path-guards/census_dead_paths.py"

# FAIL CLOSED ON A MISSING DEPENDENCY. A cost report produced without the instrument it is
# supposed to run is the exact shape the fail-open linter exists to refuse.
for f in "$LINT" "$CENSUS"; do
  if [ ! -f "$f" ]; then
    printf 'T401 COST ABORT (2): dependency absent: %s\n' "$f" >&2
    printf 'T401 COST ABORT (2): a delta measured without both instruments is not a delta.\n' >&2
    exit 2
  fi
done

D="$(mktemp -d "${TMPDIR:-/tmp}/t401-cost.XXXXXXXXXX")" || exit 2

# `census_dead_paths.py` finds the repository by walking UP from `Path(__file__)` looking for
# a `.git` entry (:98-104). A copy in $TMPDIR therefore exits 2 with "no .git ancestor" -- it
# is not portable to scratch. So the dead-path copy is materialised INSIDE the worktree, under
# this task's own grant, DOT-PREFIXED and UNTRACKED, and removed by the trap. It never enters
# `git ls-files`, so it never enters either corpus and cannot perturb the figures.
#
# THE PATH IS ASSEMBLED FROM $G, NOT SPELLED WHOLE, and that is not style. Spelling
# `<grant-dir>/<scratch-name>.py` as ONE literal, with the grant directory written out,
# put a DEAD-PATH ROW on this very file -- the scratch target is untracked by construction,
# so the T316 census reads the literal, fails to resolve it, and counts it. It took the bar
# to `T316-DEADPATH-FRONTIER: REFUSED rows=110 pinned=108`. The census extracts literals that
# CONTAIN `.softhouse/`; a bare basename joined to a variable is not one, and $G itself
# resolves because this directory is tracked.
G="$ROOT/.softhouse/capture/t401-zsh-census-gap"
INREPO="$G/.t401-scratch-census-zsh.py"
trap 'rm -rf "$D"; rm -f "$INREPO"' EXIT INT TERM

# ---------------------------------------------------------------------------------------
# The two patches, each a ONE-TOKEN widening of a selector, applied to a COPY.
# ---------------------------------------------------------------------------------------
sed 's/f\.endswith((\"\.sh\", \"\.py\"))/f.endswith((".sh", ".py", ".zsh"))/' "$LINT" >"$D/lint-zsh.py"
sed 's|"git", "ls-files", "\.softhouse/\*\.py", "\.softhouse/\*\.sh"|"git", "ls-files", ".softhouse/*.py", ".softhouse/*.sh", ".softhouse/*.zsh"|' "$CENSUS" >"$INREPO"

# A `sed` THAT MATCHED NOTHING IS A SILENT NO-OP, and a no-op copy would report a delta of
# ZERO and read as "extending costs nothing". That is the fail-open shape. Both patches are
# therefore VERIFIED to have changed the file, and an unchanged copy is a refusal.
if cmp -s "$LINT" "$D/lint-zsh.py"; then
  printf 'T401 COST ABORT (2): the failopen selector patch changed NOTHING. A no-op copy would\n' >&2
  printf 'T401 COST ABORT (2): report a zero delta and read as "extending is free". REFUSED.\n' >&2
  exit 2
fi
if cmp -s "$CENSUS" "$INREPO"; then
  printf 'T401 COST ABORT (2): the deadpath selector patch changed NOTHING. Same refusal.\n' >&2
  exit 2
fi

E="$ROOT/.softhouse/capture/t401-zsh-census-gap/evidence"
mkdir -p "$E"

printf 'T401 COST OF EXTENDING THE CENSUS SELECTORS TO .zsh\n'
printf 'commit  : %s\n' "$(git rev-parse --short HEAD)"
printf 'patches : failopen  endswith((".sh",".py"))  ->  endswith((".sh",".py",".zsh"))\n'
printf '          deadpath  ls-files .softhouse/{*.py,*.sh}  ->  + .softhouse/*.zsh\n'
printf '\n'

# ---------------------------------------------------------------------------------------
# 1. FAIL-OPEN LINTER
# ---------------------------------------------------------------------------------------
( cd "$ROOT" && FAILOPEN_LINT_JSON="$D/base.json" python3 "$LINT" ) >"$E/20-failopen-BASE.txt" 2>&1
rcb=$?
( cd "$ROOT" && FAILOPEN_LINT_JSON="$D/zsh.json"  python3 "$D/lint-zsh.py" ) >"$E/22-failopen-ZSH.txt" 2>&1
rcz=$?
for t in "$E/20-failopen-BASE.txt" "$E/22-failopen-ZSH.txt"; do
  if ! LC_ALL=C grep -qF 'T238 FAIL-OPEN LINT' "$t"; then
    printf 'T401 COST ABORT (2): no banner in %s -- the linter did not run.\n' "$t" >&2
    exit 2
  fi
done
LC_ALL=C sed -n 's/^FAILOPEN-FRONTIER //p' "$E/20-failopen-BASE.txt" | LC_ALL=C sort >"$D/fo-base"
LC_ALL=C sed -n 's/^FAILOPEN-FRONTIER //p' "$E/22-failopen-ZSH.txt"  | LC_ALL=C sort >"$D/fo-zsh"
cb="$(LC_ALL=C sed -n 's/^corpus    : \([0-9][0-9]*\) tracked.*$/\1/p' "$E/20-failopen-BASE.txt")"
cz="$(LC_ALL=C sed -n 's/^corpus    : \([0-9][0-9]*\) tracked.*$/\1/p' "$E/22-failopen-ZSH.txt")"
ib="$(LC_ALL=C sed -n 's/^corpus    : [0-9][0-9]* tracked \.sh\/\.py; \([0-9][0-9]*\) are.*$/\1/p' "$E/20-failopen-BASE.txt")"
iz="$(LC_ALL=C sed -n 's/^corpus    : [0-9][0-9]* tracked \.sh\/\.py; \([0-9][0-9]*\) are.*$/\1/p' "$E/22-failopen-ZSH.txt")"
nb="$(LC_ALL=C grep -c '' "$D/fo-base" || true)"
nz="$(LC_ALL=C grep -c '' "$D/fo-zsh"  || true)"

printf '== 1. FAIL-OPEN LINTER (T238) ==\n'
printf '  exit code                    base %s   +zsh %s   (0=clean 1=violations 2=abort)\n' "$rcb" "$rcz"
printf '  corpus (tracked files)       base %s   +zsh %s\n' "$cb" "$cz"
printf '  repo-wide search instruments base %s   +zsh %s\n' "$ib" "$iz"
printf '  FRONTIER ROWS                base %s   +zsh %s\n' "$nb" "$nz"
printf '  NEW FRONTIER ROWS the pin would have to absorb:\n'
LC_ALL=C comm -13 "$D/fo-base" "$D/fo-zsh" >"$D/fo-new"
if [ -s "$D/fo-new" ]; then LC_ALL=C sed 's/^/    + /' "$D/fo-new"; else printf '    (none)\n'; fi
LC_ALL=C comm -23 "$D/fo-base" "$D/fo-zsh" >"$D/fo-gone"
printf '  ROWS LOST (must be empty -- widening may not drop a row):\n'
if [ -s "$D/fo-gone" ]; then LC_ALL=C sed 's/^/    - /' "$D/fo-gone"; else printf '    (none)\n'; fi
printf '\n'

# ---------------------------------------------------------------------------------------
# 2. DEAD-PATH CENSUS
# ---------------------------------------------------------------------------------------
( cd "$ROOT" && python3 "$CENSUS" )        >"$E/21-deadpath-BASE.txt" 2>&1
( cd "$ROOT" && python3 "$INREPO" ) >"$E/23-deadpath-ZSH.txt" 2>&1
sb="$(LC_ALL=C grep '^T316-DEADPATH-CENSUS:' "$E/21-deadpath-BASE.txt" || true)"
sz="$(LC_ALL=C grep '^T316-DEADPATH-CENSUS:' "$E/23-deadpath-ZSH.txt"  || true)"
if [ -z "$sb" ] || [ -z "$sz" ]; then
  printf 'T401 COST ABORT (2): a dead-path census produced no summary line.\n' >&2
  exit 2
fi
printf '== 2. DEAD-PATH CENSUS (T316) ==\n'
printf '  base : %s\n' "$sb"
printf '  +zsh : %s\n' "$sz"
printf '  NEW DEAD-PATH ROWS the pin would have to absorb (file -> literal):\n'
LC_ALL=C sed -n '/^THE .* FILE(S) NAMING A DEAD CONCRETE PATH/,$p' "$E/21-deadpath-BASE.txt" | LC_ALL=C sort >"$D/dp-base"
LC_ALL=C sed -n '/^THE .* FILE(S) NAMING A DEAD CONCRETE PATH/,$p' "$E/23-deadpath-ZSH.txt"  | LC_ALL=C sort >"$D/dp-zsh"
LC_ALL=C comm -13 "$D/dp-base" "$D/dp-zsh" >"$D/dp-new"
if [ -s "$D/dp-new" ]; then LC_ALL=C sed 's/^/    + /' "$D/dp-new"; else printf '    (none)\n'; fi
printf '\n'
printf '== 3. THE PIN FILE THE DEAD-PATH GUARD COMPARES AGAINST ==\n'
printf '  %s\n' "$ROOT/.softhouse/guards/dead-path-frontier.pin"
printf '  pin rows (non-comment, non-blank): '
LC_ALL=C grep -c -v -e '^#' -e '^[[:space:]]*$' "$ROOT/.softhouse/guards/dead-path-frontier.pin" || true
