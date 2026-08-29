#!/usr/bin/env bash
# =============================================================================================
# T465 / C-T461-3 -- DOES FU-T453-1's STATED BLOCKER REPRODUCE?
#
#     bash 40-cheap-tier-blocker.sh <rev> <outdir>
#
# THE CLAIM UNDER TEST, quoted from T453's handoff section 6: extending the cheap tier to RUN
# `check-capture-namespace.sh` is blocked because "`cheap-subset.sh` materialises its tree with
# `read-tree`+`checkout-index` and NOT as a real work tree, so `check-capture-namespace.sh`'s
# `git rev-parse --show-toplevel` would grade the caller's tree -- the T165/T201 defect", and
# fixing it "means giving the cheap subset a real scratch work tree, which is a design change,
# not a micro-fix."
#
# T461 says it does not reproduce. T465 RE-DERIVES IT RATHER THAN INHERITING EITHER ANSWER, and
# the derivation needs a CONTROL, because "the guard reported N directories" means nothing
# unless the caller's tree and the materialised tree report DIFFERENT N. So the fixture is built
# to make them differ ON PURPOSE:
#
#   CONTROL  the guard run in the CALLER's tree                    -> dirs = C
#   ARM      the guard run under the EXACT environment cheap-subset.sh establishes, from a rev
#            whose capture inventory differs from the caller's     -> dirs = A
#
#   A != C  ==> the guard graded the MATERIALISED tree. The blocker does not reproduce.
#   A == C  ==> indistinguishable. The instrument says so and refuses to conclude either way.
#
# The environment is reproduced from `cheap-subset.sh`'s own three exports, read out of that
# file at run time rather than transcribed, so this cannot drift away from the thing it models.
#
# No real repo path is spelt: the softhouse directory name is assembled from $SH_NAME.
#
# EXIT: 0 the two arms are DISTINGUISHABLE and the finding is stated; 1 they are not; 9x the
# fixture could not be built. Probe line `T465-CHEAP-ROOT:` on every path that reaches a
# verdict, never on a 9x (P-84).
# =============================================================================================
set -u

ME='t465-cheap-root'
say() { printf '%s: %s\n' "$ME" "$*"; }
die() { printf '%s: ABORT(%s) -- %s\n' "$ME" "$1" "$2" >&2; exit "$1"; }

REV="${1:-}"
OUT="${2:-}"
[ -n "$REV" ] && [ -n "$OUT" ] || die 90 "usage: 40-cheap-tier-blocker.sh <rev> <outdir>"
mkdir -p "$OUT" || die 90 "could not create $OUT"
OUT="$(cd "$OUT" && pwd -P)" || die 90 "could not enter $OUT"

SH_NAME='.softhouse'
NSGUARD_REL="$SH_NAME/guards/check-capture-namespace.sh"
SUBSET_REL="$SH_NAME/hooks/cheap-subset.sh"

TOP="$(git rev-parse --show-toplevel 2>/dev/null)" || die 90 "not inside a git work tree"
[ -f "$TOP/$NSGUARD_REL" ] || die 90 "the namespace guard is absent: $TOP/$NSGUARD_REL"
[ -f "$TOP/$SUBSET_REL" ]  || die 90 "the cheap subset is absent: $TOP/$SUBSET_REL"

# THE MODEL IS READ OUT OF THE THING IT MODELS. If cheap-subset.sh ever stops exporting these
# three names, this instrument must stop claiming to reproduce its environment -- so it checks,
# and refuses rather than measuring a fiction.
for v in GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE; do
  if ! LC_ALL=C grep -aq "^export $v=" "$TOP/$SUBSET_REL"; then
    die 91 "cheap-subset.sh no longer exports $v. This instrument would be reproducing an environment that no longer exists; REFUSING rather than reporting about it."
  fi
done
LC_ALL=C grep -aq 'git read-tree'      "$TOP/$SUBSET_REL" || die 91 "cheap-subset.sh no longer runs \`git read-tree\`."
LC_ALL=C grep -aq 'git checkout-index' "$TOP/$SUBSET_REL" || die 91 "cheap-subset.sh no longer runs \`git checkout-index\`."
say "model    cheap-subset.sh still exports GIT_DIR/GIT_INDEX_FILE/GIT_WORK_TREE and materialises"
say "         with read-tree + checkout-index. The environment below is that environment."

COMMON="$(git rev-parse --git-common-dir 2>/dev/null)" || die 90 "could not resolve the git common dir"
case "$COMMON" in /*) : ;; *) COMMON="$TOP/$COMMON" ;; esac
TREE="$(git rev-parse --verify --quiet "$REV^{tree}")" || die 90 "'$REV' does not resolve to a tree"

D="$(mktemp -d "${TMPDIR:-/tmp}/t465-cheaproot.XXXXXXXXXX")" || die 90 "could not create a scratch dir"
trap '[ -n "${D:-}" ] && [ -d "$D" ] && rm -rf "$D"' EXIT
mkdir -p "$D/tree" || die 90 "could not create the materialisation directory"

PROBE='NAMESPACE-CENSUS'

# ---- CONTROL: the guard in the caller's own work tree ---------------------------------------
CTRL="$OUT/cheap-root-CONTROL.txt"
( cd "$TOP" && bash "$NSGUARD_REL" ) >"$CTRL" 2>&1
CTRL_RC=$?
CTRL_N="$(LC_ALL=C grep -ac "$PROBE" "$CTRL" || true)"
case "${CTRL_N:-}" in ''|*[!0-9]*) CTRL_N=0 ;; esac
[ "$CTRL_N" -ge 1 ] \
  || die 92 "the CONTROL printed no $PROBE line (exit $CTRL_RC). Without a control figure the arm below is uninterpretable."
CTRL_LINE="$(LC_ALL=C grep -a "$PROBE" "$CTRL" | LC_ALL=C tail -1)"
CTRL_DIRS="$(printf '%s' "$CTRL_LINE" | LC_ALL=C sed -n 's/.*dirs=\([0-9][0-9]*\).*/\1/p')"
case "${CTRL_DIRS:-}" in ''|*[!0-9]*) CTRL_DIRS=-1 ;; esac
say "CONTROL  caller's tree $TOP"
say "         exit=$CTRL_RC  $CTRL_LINE"

# ---- ARM: the guard under cheap-subset.sh's environment --------------------------------------
(
  export GIT_DIR="$COMMON"
  export GIT_INDEX_FILE="$D/index"
  export GIT_WORK_TREE="$D/tree"
  git read-tree "$TREE"    || exit 90
  git checkout-index -a -f || exit 90
  cd "$D/tree" || exit 90
  printf 'toplevel under the cheap-subset environment: %s\n' "$(git rev-parse --show-toplevel 2>&1)"
  bash "$D/tree/$NSGUARD_REL"
) >"$OUT/cheap-root-ARM.txt" 2>&1
ARM_RC=$?
[ "$ARM_RC" -ne 90 ] || die 91 "the materialisation itself failed; there is no arm to read."
ARM_N="$(LC_ALL=C grep -ac "$PROBE" "$OUT/cheap-root-ARM.txt" || true)"
case "${ARM_N:-}" in ''|*[!0-9]*) ARM_N=0 ;; esac
[ "$ARM_N" -ge 1 ] \
  || die 92 "the ARM printed no $PROBE line (exit $ARM_RC). No verdict is available from it (P-84)."
ARM_LINE="$(LC_ALL=C grep -a "$PROBE" "$OUT/cheap-root-ARM.txt" | LC_ALL=C tail -1)"
ARM_DIRS="$(printf '%s' "$ARM_LINE" | LC_ALL=C sed -n 's/.*dirs=\([0-9][0-9]*\).*/\1/p')"
case "${ARM_DIRS:-}" in ''|*[!0-9]*) ARM_DIRS=-1 ;; esac
ARM_TOP="$(LC_ALL=C sed -n 's/^toplevel under the cheap-subset environment: //p' "$OUT/cheap-root-ARM.txt" | LC_ALL=C tail -1)"
say "ARM      materialised tree of $REV at $D/tree"
say "         rev-parse --show-toplevel -> $ARM_TOP"
say "         exit=$ARM_RC  $ARM_LINE"

# ---- the verdict ------------------------------------------------------------------------------
say ""
if [ "$CTRL_DIRS" -lt 0 ] || [ "$ARM_DIRS" -lt 0 ]; then
  say "NEITHER ARM YIELDED A READABLE dirs= FIGURE. An unreadable measurement is an ERROR, never"
  say "  a finding (P-81)."
  say "T465-CHEAP-ROOT: rev=$REV control=$CTRL_DIRS arm=$ARM_DIRS distinguishable=UNREADABLE"
  exit 1
fi
if [ "$ARM_DIRS" -eq "$CTRL_DIRS" ]; then
  say "THE TWO ARMS ARE INDISTINGUISHABLE (both dirs=$ARM_DIRS). That is NOT evidence that the"
  say "  guard graded the materialised tree, and it is NOT evidence that it graded the caller's:"
  say "  a fixture whose two trees agree cannot tell them apart. Pick a rev whose capture"
  say "  inventory differs from the working tree's and run again. REFUSING to conclude."
  say "T465-CHEAP-ROOT: rev=$REV control=$CTRL_DIRS arm=$ARM_DIRS distinguishable=NO"
  exit 1
fi
say "DISTINGUISHABLE: the guard reports dirs=$ARM_DIRS under the cheap-subset environment and"
say "  dirs=$CTRL_DIRS in the caller's tree. The figure it reports is a property of the"
say "  MATERIALISED tree, so FU-T453-1's stated blocker DOES NOT REPRODUCE: the three exports"
say "  already redirect \`git rev-parse --show-toplevel\`, and a cheap tier that ran this guard"
say "  would be grading the PUSHED tree. What remains true from T453 is the OBLIGATION, not the"
say "  blocker -- T165/T201 require the root to be READ BACK and asserted, not assumed."
say "T465-CHEAP-ROOT: rev=$REV control=$CTRL_DIRS arm=$ARM_DIRS distinguishable=YES"
exit 0
