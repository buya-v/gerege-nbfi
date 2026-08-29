#!/usr/bin/env bash
# =============================================================================================
# T465 -- THE FINDING WAS STATED ABOUT THE WHOLE BAR, SO THE REMEDY IS DRIVEN ON THE WHOLE BAR.
#
#     bash 60-bar-on-a-released-tree.sh <rev> <outdir>
#
# C-T461-1's sentence is *"the full bar on a lock-released tree is EXIT 2 WITH NO PROBE LINE"*.
# `10-lock-arms.sh` proves the GUARD is green both ways after the repair, which is necessary and
# not sufficient: it does not prove that the frontier guard is the ONLY thing in the bar that is
# sensitive to whether the fire lock is in the index. This runs the WHOLE BAR on a tree with the
# lock released, by `release_lock`'s own sequence, and reports the PROBE-LINE COUNT beside the
# exit status.
#
# READ THIS BEFORE READING THE RESULT: the arm is meaningful ONLY beside a CONTROL run of the
# same bar on the same tree with the lock HELD. A bar that exits 2 for a reason having nothing to
# do with the lock -- a missing toolchain, an unreachable reference oracle -- would look exactly
# like the finding. So the control runs first and the instrument REFUSES if the control is not
# clean, rather than reporting an arm nobody can interpret.
#
# THE TOOLCHAIN IS GITIGNORED HOST STATE and no clone can carry it, so it is DERIVED from the
# source repository's common dir and ANNOUNCED -- never typed as an absolute literal, which would
# be host state in a tracked instrument and a dead path on any other machine. Same shape, and the
# same reason, as `drive-arms.sh`'s mode=bar setup.
#
# No real repo path is spelt: the softhouse directory name is assembled from $SH_NAME.
#
# EXIT: 0 both runs reached a verdict and the arm is clean; 1 the arm is NOT clean; 9x the
# fixture or the control failed, which is never an arm verdict.
# Probe line `T465-BAR-RELEASED:` only when both runs reached a verdict (P-84).
# =============================================================================================
set -u

ME='t465-bar-released'
say() { printf '%s: %s\n' "$ME" "$*"; }
die() { printf '%s: ABORT(%s) -- %s\n' "$ME" "$1" "$2" >&2; exit "$1"; }

REV="${1:-}"; OUT="${2:-}"
[ -n "$REV" ] && [ -n "$OUT" ] || die 90 "usage: 60-bar-on-a-released-tree.sh <rev> <outdir>"
mkdir -p "$OUT" || die 90 "could not create $OUT"
OUT="$(cd "$OUT" && pwd -P)" || die 90 "could not enter $OUT"

SH_NAME='.softhouse'
LOCK_REL="$SH_NAME/LOCK"
BAR_REL="$SH_NAME/conformance.sh"
TCLEAF='toolchain'

SRC="$(git rev-parse --show-toplevel 2>/dev/null)" || die 90 "not inside a git work tree"
SRCSHA="$(git rev-parse --verify --quiet "$REV^{commit}")" || die 90 "'$REV' does not resolve"

U="$(mktemp -d "${TMPDIR:-/tmp}/t465-barrel.XXXXXXXXXX")" || die 90 "could not create a scratch dir"
trap '[ -n "${U:-}" ] && [ -d "$U" ] && rm -rf "$U"' EXIT
WT="$U/wt"
GIT="git -c user.name=t465-bar -c user.email=t465@invalid -c commit.gpgsign=false"

# A REAL CLONE WITH REAL HISTORY: guards in this bar read historical commits BY SHA, and a
# squashed fixture makes them refuse about the FIXTURE (T453 measured that on its first draft).
$GIT clone --local --quiet --no-checkout "$SRC" "$WT" || die 90 "could not clone $SRC"
cd "$WT" || die 90 "could not enter $WT"
$GIT checkout -q -B main "$SRCSHA" || die 90 "could not check out $SRCSHA"
$GIT remote remove origin || die 90 "could not detach the clone from its source"
[ -f "$BAR_REL" ] || die 91 "the bar is absent from tree $SRCSHA: $BAR_REL"
$GIT ls-files --error-unmatch -- "$LOCK_REL" >/dev/null 2>&1 \
  || die 91 "the lock is NOT tracked at $SRCSHA, so there is no CONTROL arm to run."

SRCCOMMON="$(git -C "$SRC" rev-parse --git-common-dir 2>/dev/null)" || die 90 "no git common dir"
case "$SRCCOMMON" in /*) : ;; *) SRCCOMMON="$SRC/$SRCCOMMON" ;; esac
TOOLCHAIN="$(cd "$SRCCOMMON/.." 2>/dev/null && pwd -P)/$SH_NAME/$TCLEAF" \
  || die 90 "could not resolve the main checkout beside $SRCCOMMON"
[ -d "$TOOLCHAIN" ] \
  || die 90 "the pinned Go toolchain is not at $TOOLCHAIN. A bar without it exits 2 about the FIXTURE, which is indistinguishable from the finding."
export GEREGE_TOOLCHAIN="$TOOLCHAIN"
say "toolchain $TOOLCHAIN (DERIVED from the source repo's common dir, announced)"

run_bar() {
  local id="$1" f rc probes notup verdict
  f="$OUT/bar-$id.txt"
  bash "$BAR_REL" >"$f" 2>&1
  rc=$?
  probes="$(LC_ALL=C grep -ac 'probe = ' "$f" || true)"
  case "${probes:-}" in ''|*[!0-9]*) probes=0 ;; esac
  if [ "$probes" -lt 1 ]; then
    BAR_RC="$rc"; BAR_PROBES=0; BAR_LINE='(NO PROBE LINE PRINTED -- no verdict is available)'
    say "$id  exit=$rc probe-lines=0  $BAR_LINE"
    return 0
  fi
  notup="$(LC_ALL=C grep -a 'probe = ' "$f" | LC_ALL=C grep -avc 'probe = up' || true)"
  case "${notup:-}" in ''|*[!0-9]*) notup=0 ;; esac
  verdict="$(LC_ALL=C grep -a 'VERDICT' "$f" | LC_ALL=C tail -1)"
  BAR_RC="$rc"; BAR_PROBES="$probes"
  BAR_LINE="probe-lines=$probes not-up=$notup  $verdict"
  say "$id  exit=$rc  $BAR_LINE"
}

# ---- CONTROL: the same tree, the lock HELD ---------------------------------------------------
say "CONTROL running the full bar with the lock IN the index ..."
run_bar CONTROL-LOCK-HELD
C_RC="$BAR_RC"; C_PROBES="$BAR_PROBES"; C_LINE="$BAR_LINE"
[ "$C_PROBES" -ge 1 ] \
  || die 92 "the CONTROL printed NO probe line (exit $C_RC). The arm below would be uninterpretable: a bar that cannot pass on a lock-HELD tree says nothing about a lock-RELEASED one."
[ "$C_RC" -eq 0 ] \
  || die 92 "the CONTROL bar exited $C_RC on the lock-HELD tree. REFUSING to attribute anything to the lock."

# ---- ARM: release the lock by release_lock's own sequence, then run the same bar --------------
rm -f -- "$LOCK_REL"       || die 93 "could not remove the lock"
$GIT add -A -- "$LOCK_REL" || die 93 "could not stage the lock's deletion"
$GIT diff --cached --quiet && die 93 "staging the lock's deletion changed nothing -- the arm did not apply."
$GIT commit -q -m 'T465: release the fire lock (release_lock sequence)' \
                           || die 93 "could not commit the release"
say "ARM     running the same bar with the lock OUT of the index ..."
run_bar ARM-LOCK-RELEASED
A_RC="$BAR_RC"; A_PROBES="$BAR_PROBES"; A_LINE="$BAR_LINE"

say ""
say "  CONTROL lock HELD      exit=$C_RC  $C_LINE"
say "  ARM     lock RELEASED  exit=$A_RC  $A_LINE"
say "T465-BAR-RELEASED: rev=$SRCSHA control_exit=$C_RC control_probes=$C_PROBES arm_exit=$A_RC arm_probes=$A_PROBES"
[ "$A_PROBES" -ge 1 ] && [ "$A_RC" -eq 0 ] || exit 1
exit 0
