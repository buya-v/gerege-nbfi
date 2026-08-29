#!/usr/bin/env bash
# =============================================================================================
# THE CHEAP SUBSET.  [T412]   `bash .softhouse/hooks/cheap-subset.sh <commit-ish>`
#
# Grades the P-NUMBER CITATION CHECKER against a NAMED TREE -- not against the working tree.
# That distinction is the whole point: instance 2 of the defect this exists for was the driver
# grading one tree and pushing another, and a subset that reads `$PWD` would rebuild it.
#
# WHY THIS ONE GUARD AND NOT SOME OTHER SUBSET -- the argument, not a preference:
#
#   * IT IS THE GUARD THAT ACTUALLY REDDENED `main`. On 2026-08-28 the driver wrote `P-100`
#     into .softhouse/RESUME.md, a DIRECTIVE file, naming a pattern that did not exist yet.
#     guard_pnumber_citations is HARD, so the bar went EXIT 2 with NO PROBE LINE and no verdict,
#     across three pushed commits. Every other guard in the file has a corpus the driver's
#     bookkeeping writes cannot reach.
#
#   * ITS CORPUS IS `git ls-files` OVER THE WHOLE TREE, so unlike every other guard there is no
#     path-based skip that could be sound for it and unsound here. It reads exactly the set the
#     driver could have written.
#
#   * IT IS STANDALONE-INVOCABLE with `--root`, so this file forks NO logic out of
#     .softhouse/conformance.sh. A subset that reimplemented guard bodies would be a second
#     copy that rots -- and conformance.sh could not be edited this wave in any case (T445 holds
#     it), which is the honest reason the subset is one guard and not fifteen.
#
# WHAT IT THEREFORE DOES NOT COVER, stated so nobody cites this as the bar: the other fourteen
# guards, the 46 golden parity vectors, and `go build` / `go test`. The gate compensates by
# admitting the cheap path ONLY when the delta from an attested tree is confined to the STATE
# set -- see .softhouse/hooks/driver-push-gate.sh, function state_path, which names the guard
# each exclusion is there for.
#
# COST, MEASURED ON THIS HOST over the real 9,730-file tree at b102875c, not estimated:
#     materialise the tree (read-tree + checkout-index)      5.12 s
#     checker --selftest                                     0.24 s
#     checker graded run                                    19.62 s
#     TOTAL                                                 24.98 s
# The same guard inside a full bar was timed at 39 s by the GUARD-COST CENSUS on 2026-08-29;
# the difference is warm cache, and the smaller figure is the one this gate is charged for
# because it is what this gate actually runs.
#
# ENGINE (P-33/P-53): bash, git, /usr/bin/python3, POSIX grep/sed. Declared, not assumed.
# =============================================================================================
set -u

say() { printf 'cheap-subset: %s\n' "$*"; }
die() { printf 'cheap-subset: %s\n' "$*"; exit 3; }

REF="${1:-HEAD}"

TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || die "ABORT(3) -- \`git rev-parse --show-toplevel\` failed. Not inside a work tree."
[ -n "$TOPLEVEL" ] || die "ABORT(3) -- empty repository root."
COMMON="$(git rev-parse --git-common-dir 2>/dev/null)" \
  || die "ABORT(3) -- \`git rev-parse --git-common-dir\` failed."
case "$COMMON" in /*) : ;; *) COMMON="$TOPLEVEL/$COMMON" ;; esac

TREE="$(git rev-parse --verify --quiet "$REF^{tree}")" \
  || die "ABORT(3) -- could not resolve a tree for '$REF'."

D="$(mktemp -d "${TMPDIR:-/tmp}/t412-cheap.XXXXXXXXXX")" \
  || die "ABORT(3) -- could not create a scratch directory."
# An `rm -rf` on a variable that could be empty is how scratch cleanup destroys a repository.
# $D is non-empty by construction above, and the trap re-tests it before firing.
trap '[ -n "${D:-}" ] && [ -d "$D" ] && rm -rf "$D"' EXIT

say "grading tree $TREE (from '$REF')"
say "  scratch $D"

# ---------------------------------------------------------------------------------------------
# MATERIALISE THE NAMED TREE, with a TEMPORARY INDEX.
#
# `git worktree add` would do this too, and every other task in this program uses it -- but it
# mutates the shared worktree registry, and this runs inside a `pre-push` hook that fires while
# nine workers hold worktrees off the same common dir. read-tree + checkout-index into a private
# index touches nothing shared: it writes $D and $D.index and nothing else.
# ---------------------------------------------------------------------------------------------
mkdir -p "$D/tree" || die "ABORT(3) -- could not create the extraction directory."
export GIT_DIR="$COMMON"
export GIT_INDEX_FILE="$D/index"
export GIT_WORK_TREE="$D/tree"
git read-tree "$TREE"     || die "ABORT(3) -- \`git read-tree $TREE\` failed."
git checkout-index -a -f  || die "ABORT(3) -- \`git checkout-index\` failed; the tree is not on disk."

# P-57: no pipeline. The listing goes to a file; the count is read from the file. A `git`
# failure inside a pipeline would otherwise be laundered into "the corpus is small".
git ls-files >"$D/index-listing" \
  || die "ABORT(3) -- \`git ls-files\` failed against the temporary index. An error is never an empty corpus."
N="$(LC_ALL=C grep -ac '' "$D/index-listing")"
case "${N:-}" in ''|*[!0-9]*) N=0 ;; esac
if [ "$N" -lt 100 ]; then
  die "ABORT(3) -- the materialised index lists $N file(s). A corpus that small is an extraction failure, and an empty corpus passes everything (P-35)."
fi
say "  materialised $N tracked path(s)"

CHK="$D/tree/.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py"
if [ ! -f "$CHK" ]; then
  die "ABORT(3) -- the P-number citation checker is ABSENT from the pushed tree: ${CHK#"$D/tree/"}. It is wired into this subset, so its absence is a refusal and never a pass."
fi
if [ ! -x /usr/bin/python3 ]; then
  die "ABORT(3) -- /usr/bin/python3 is absent. The checker cannot run. This REFUSES rather than degrading to a smaller green."
fi

# SELFTEST FIRST (P-22: a guard that cannot fail is worse than none, because it is believed).
# A checker whose predicate has stopped discriminating reports a clean tree in exactly the same
# words as a clean tree.
OUT="$D/checker.out"
if ! /usr/bin/python3 "$CHK" --selftest >"$OUT" 2>&1; then
  say "REFUSED -- the P-number citation checker FAILED ITS OWN SELFTEST. Its verdict on this"
  say "  tree is worthless until that is fixed."
  LC_ALL=C sed -n '1,20p' "$OUT"
  exit 3
fi
say "  checker selftest: PASS"

/usr/bin/python3 "$CHK" --root "$D/tree" >"$OUT" 2>&1
RC=$?

# PRESENCE BEFORE VALUE (P-84: "EXIT 2 WITH NO PROBE LINE" IS THE GUARD WORKING -- read the
# ABSENCE, not the value). A verdict line that was never PRINTED is a crash, and silence here
# reads exactly like a clean register.
if ! LC_ALL=C grep -aqE '^PNUMBER-CITATIONS: VERDICT ' "$OUT"; then
  say "REFUSED -- the checker printed NO VERDICT line (exit $RC). It did not run, or did not finish."
  LC_ALL=C sed -n '1,25p' "$OUT"
  exit 3
fi
if [ "$RC" -ne 0 ] && [ "$RC" -ne 1 ]; then
  say "REFUSED -- the checker exited $RC, which is neither clean (0) nor violations (1)."
  LC_ALL=C sed -n '1,25p' "$OUT"
  exit 3
fi

LC_ALL=C grep -aE '^PNUMBER-CITATIONS: (register|sites|VERDICT)' "$OUT" \
  | while IFS= read -r l; do say "  $l"; done

if [ "$RC" -ne 0 ]; then
  say ""
  say "FAILED -- A CITED P-NUMBER IN A DIRECTIVE FILE OF THE PUSHED TREE CARRIES A RULE SENTENCE"
  say "  THAT patterns.md DEFINES UNDER A DIFFERENT NUMBER, OR NAMES NO RULE AT ALL."
  LC_ALL=C grep -aE '^PNUMBER-CITATIONS: FATAL' "$OUT"
  say ""
  say "  In a full bar this is guard_pnumber_citations, which is HARD: EXIT 2, no probe line, no"
  say "  verdict. Correct the id, or state the cited rule."
  exit 1
fi

say "PASS -- 0 fatal citation findings in the DIRECTIVE zone of tree $TREE."
exit 0
