#!/usr/bin/env bash
# =============================================================================================
# T465 -- IS THE DEAD-PATH FRONTIER A FUNCTION OF WHETHER THE FIRE LOCK IS TRACKED?
#
#     bash 10-lock-arms.sh <source-rev> <outdir>
#
# THE QUESTION, stated so the answer can be wrong. T316's frontier guard classifies a quoted
# `<softhouse>/`-rooted literal as DEAD when it is not in the TRACKED universe (`git ls-files`).
# The fire lock is TRACKED WHILE A FIRE HOLDS IT, and `release_lock` deletes it, stages the
# deletion and COMMITS at every fire exit. So a literal naming it resolves DURING a fire and
# dies BETWEEN fires. If that is true, the colour of the whole bar depends on the phase of the
# fire cycle -- the same class of defect T326 removed when it stopped the census consulting the
# DISK, one level up: not "a snapshot of somebody's disk" but "a snapshot of somebody's fire".
#
# THREE ARMS AND TWO CALIBRATIONS. The third arm is the one that decides the REMEDY, and it is
# the reason this instrument exists rather than a single removal and a re-run:
#
#   CALIBRATION-   the untouched tree. The guard must be GREEN. Without it, REFUSED in ARM B is
#                  indistinguishable from a guard that refuses everything.
#   CALIBRATION+   plant a NEW instrument naming a path that is dead in EVERY phase. The guard
#                  must report added>=1. Without it, `added=0` in ARM A is uninterpretable --
#                  it is indistinguishable from a guard that cannot see anything (P-72).
#   ARM A          lock IN the index (a fire is holding it).
#   ARM B          lock OUT of the index, by the EXACT sequence release_lock uses.
#   ARM C          the pin REGENERATED to ARM B's frontier, and then the lock PUT BACK.
#                  If ARM C also refuses, THE FRONTIER HAS NO FIXED POINT and no pin can encode
#                  it -- pinning is not a remedy that exists, and the repair must be at the
#                  instruments. That is a MEASUREMENT, not a preference.
#
# NO REAL REPO PATH IS SPELT HERE. The softhouse directory name is assembled from $SH_NAME and
# every path below is built from it, because this file is itself a tracked instrument and a
# spelt literal would be the very frontier row it is measuring. Six workers in fire
# 20260829-080002 were refused by that guard for exactly this reflex.
#
# PRESENCE BEFORE VALUE (P-84) at every arm: the count of PRINTED probe lines is reported
# beside the exit status, and a verdict is read only after the line is seen.
#
# EXIT: 0 all arms reached a verdict; 9x the universe could not be built or a calibration
# failed. NEVER an arm verdict.
# =============================================================================================
set -u

ME='t465-lock-arms'
say() { printf '%s: %s\n' "$ME" "$*"; }
die() { printf '%s: ABORT(%s) -- %s\n' "$ME" "$1" "$2" >&2; exit "$1"; }

SRCREV="${1:-}"
OUT="${2:-}"
[ -n "$SRCREV" ] && [ -n "$OUT" ] || die 90 "usage: 10-lock-arms.sh <source-rev> <outdir>"

# ---- the paths this instrument needs, ASSEMBLED --------------------------------------------
SH_NAME='.softhouse'
LOCK_REL="$SH_NAME/LOCK"
GUARD_REL="$SH_NAME/guards/check-dead-path-frontier.sh"
PIN_REL="$SH_NAME/guards/dead-path-frontier.pin"
PROBE='T316-DEADPATH-FRONTIER:'

SRC="$(git rev-parse --show-toplevel 2>/dev/null)" || die 90 "not inside a git work tree"
[ -n "$SRC" ] || die 90 "empty repository root"
SRCSHA="$(git -C "$SRC" rev-parse --verify --quiet "$SRCREV^{commit}")" \
  || die 90 "'$SRCREV' does not resolve to a commit in $SRC"

mkdir -p "$OUT" || die 90 "could not create $OUT"
OUT="$(cd "$OUT" && pwd -P)" || die 90 "could not enter $OUT"

U="$(mktemp -d "${TMPDIR:-/tmp}/t465-arms.XXXXXXXXXX")" || die 90 "could not create a scratch dir"
# $U is non-empty by construction and the trap re-tests it: an `rm -rf` on a variable that could
# be empty is how scratch cleanup destroys a repository.
trap '[ -n "${U:-}" ] && [ -d "$U" ] && rm -rf "$U"' EXIT
WT="$U/wt"
GIT="git -c user.name=t465-drive -c user.email=t465@invalid -c commit.gpgsign=false"

say "source repo   $SRC"
say "source rev    $SRCREV -> $SRCSHA"
say "universe      $U"
say "evidence      $OUT"

# A REAL LOCAL CLONE WITH REAL HISTORY, and `origin` detached IMMEDIATELY -- an instrument that
# could push into the repository it is measuring is worse than no instrument. History matters:
# a squashed single-commit fixture makes guards that read historical commits by sha refuse, and
# a red control makes every red arm uninterpretable (T453 measured that on its first draft).
$GIT clone --local --quiet --no-checkout "$SRC" "$WT" || die 90 "could not clone $SRC"
cd "$WT" || die 90 "could not enter the throwaway work tree"
$GIT checkout -q -B main "$SRCSHA" || die 90 "could not check out $SRCSHA"
$GIT remote remove origin || die 90 "could not detach the throwaway clone from its source"

NTRACK="$($GIT ls-files | LC_ALL=C grep -ac '' || true)"
case "${NTRACK:-}" in ''|*[!0-9]*) NTRACK=0 ;; esac
[ "$NTRACK" -ge 100 ] || die 91 "the base tree tracks $NTRACK path(s): an extraction failure, not a small repo."
say "base tree     $NTRACK tracked path(s)"

# THE PRESUPPOSITION IS TESTED, NOT ASSUMED. Every arm below is about files this rev must
# actually track; if the lock is not among them, ARM A is not "the lock held" and nothing here
# means anything.
$GIT ls-files --error-unmatch -- "$LOCK_REL" >/dev/null 2>&1 \
  || die 91 "the lock is NOT tracked at $SRCSHA, so there is no 'lock held' arm to run. REFUSING."
[ -f "$GUARD_REL" ] || die 91 "the frontier guard is absent at $SRCSHA: $GUARD_REL"
[ -f "$PIN_REL" ]   || die 91 "the frontier pin is absent at $SRCSHA: $PIN_REL"

# ---- one arm --------------------------------------------------------------------------------
# Runs the guard, writes the transcript, and reports PRESENCE (printed probe lines) BEFORE the
# value. An absent probe line is NOT a green and NOT a red: it is "no verdict is available".
ARMS=0
ARM_RC=0; ARM_PROBES=0; ARM_LINE=''
RESULTS="$OUT/RESULTS.txt"
run_guard() {
  local id="$1" desc="$2" f rc probes line
  f="$OUT/arm-$id.txt"
  bash "$GUARD_REL" >"$f" 2>&1
  rc=$?
  probes="$(LC_ALL=C grep -ac "^$PROBE" "$f" || true)"
  case "${probes:-}" in ''|*[!0-9]*) probes=0 ;; esac
  if [ "$probes" -eq 0 ]; then
    line='(NO PROBE LINE PRINTED -- no verdict is available from this arm)'
  else
    line="$(LC_ALL=C sed -n "s/^$PROBE //p" "$f" | LC_ALL=C tail -1)"
  fi
  printf '%-32s exit=%s probe-lines=%s  %s\n' "$id" "$rc" "$probes" "$line" >>"$RESULTS"
  say "$id ($desc)"
  say "    exit=$rc probe-lines=$probes  $line"
  ARMS=$((ARMS+1))
  ARM_RC="$rc"; ARM_PROBES="$probes"; ARM_LINE="$line"
}

: >"$RESULTS" || die 90 "could not create $RESULTS"
{
  printf '# T465 -- the dead-path frontier against the fire-lock cycle\n'
  printf '# source %s (%s)   base tree %s tracked path(s)\n' "$SRCREV" "$SRCSHA" "$NTRACK"
  printf '# columns: arm | guard exit | probe lines PRINTED | probe line\n'
} >>"$RESULTS"

# ---- CALIBRATION- : the untouched tree must be GREEN ----------------------------------------
run_guard CALIB-MINUS 'the untouched tree'
[ "$ARM_PROBES" -ge 1 ] || die 92 "CALIBRATION- printed no probe line. No arm below is interpretable."
[ "$ARM_RC" -eq 0 ] \
  || die 92 "CALIBRATION- is not GREEN on the untouched tree [$ARM_LINE]. Every REFUSED below would be indistinguishable from a guard that refuses everything."

# ---- CALIBRATION+ : a planted dead literal must be SEEN --------------------------------------
# The plant names a directory that is dead in EVERY phase of the fire cycle, so this arm is not
# itself sensitive to the thing under test.
PLANT="$SH_NAME/capture/t465-lock-frontier/instruments/CALIBRATION-PLANT.sh"
mkdir -p "$(dirname -- "$PLANT")" || die 92 "could not create the plant's directory"
{
  printf '#!/usr/bin/env bash\n'
  printf '# T465 CALIBRATION+ PLANT -- throwaway, never committed to the real repository.\n'
  printf 'cat "%s/t465-calibration-there-is-no-such-directory/absent.txt"\n' "$SH_NAME"
} >"$PLANT" || die 92 "could not write the calibration plant"
$GIT add -- "$PLANT" || die 92 "could not stage the calibration plant"
run_guard CALIB-PLUS 'a planted dead literal, dead in every phase'
[ "$ARM_PROBES" -ge 1 ] || die 92 "CALIBRATION+ printed no probe line."
[ "$ARM_RC" -eq 1 ] \
  || die 92 "CALIBRATION+ did not go RED on a planted dead literal [$ARM_LINE]. The guard cannot see a new row, so added=0 anywhere below would mean nothing."
case "$ARM_LINE" in
  *' added=0 '*) die 92 "CALIBRATION+ reported added=0 on a planted row [$ARM_LINE]." ;;
esac
$GIT reset -q --hard "$SRCSHA" || die 92 "could not undo the calibration plant"
$GIT clean -qfd                || die 92 "could not clean after the calibration plant"

# ---- ARM A: the lock is IN the index (a fire holds it) ---------------------------------------
run_guard ARM-A-LOCK-HELD 'the lock is in the index'
A_LINE="$ARM_LINE"

# ---- ARM B: the lock is OUT of the index, by release_lock's OWN sequence ----------------------
# `rm -f`, then stage the deletion, then commit. Reproduced rather than approximated, because
# the point of the arm is what the DRIVER does 34 times per 400 commits.
rm -f -- "$LOCK_REL"       || die 93 "ARM B: could not remove the lock"
$GIT add -A -- "$LOCK_REL" || die 93 "ARM B: could not stage the lock's deletion"
$GIT diff --cached --quiet && die 93 "ARM B: staging the lock's deletion changed nothing -- the arm did not apply."
$GIT commit -q -m 'T465 arm B: release the fire lock (release_lock sequence)' \
                           || die 93 "ARM B: could not commit the release"
run_guard ARM-B-LOCK-RELEASED 'the lock is out of the index'
B_LINE="$ARM_LINE"
B_RC="$ARM_RC"

# ---- ARM C: pin REGENERATED to ARM B's frontier, then the lock PUT BACK -----------------------
# This is the arm that decides whether pinning is even available. The frontier's own rule is
# that a pin is a FRONTIER, NOT AN AMNESTY: a row that leaves must be dropped in the same
# commit. So a pin that admits the released-state rows must refuse in the held state.
C_LINE='(not run)'
if [ "$B_RC" -eq 1 ]; then
  LC_ALL=C sed -n 's/^> //p' "$OUT/arm-ARM-B-LOCK-RELEASED.txt" >"$U/addedrows.txt" 2>/dev/null || :
  ADDED_N="$(LC_ALL=C grep -ac '' "$U/addedrows.txt" || true)"
  case "${ADDED_N:-}" in ''|*[!0-9]*) ADDED_N=0 ;; esac
  [ "$ADDED_N" -ge 1 ] || die 93 "ARM C: ARM B refused but printed no '+' rows to regenerate a pin from."
  cat "$U/addedrows.txt" >>"$PIN_REL" || die 93 "ARM C: could not extend the pin"
  cp "$U/addedrows.txt" "$OUT/arm-B-added-rows.txt" || die 93 "ARM C: could not record the added row set"
  run_guard ARM-C-PIN-AT-RELEASED 'pin regenerated to the released frontier, lock still out'
  $GIT checkout -q "$SRCSHA" -- "$LOCK_REL" || die 93 "ARM C: could not restore the lock to the index"
  run_guard ARM-C-PIN-AT-RELEASED-LOCK-BACK 'the SAME pin, with the lock back in the index'
  C_LINE="$ARM_LINE"
else
  say "ARM C SKIPPED: ARM B did not refuse, so there is no released-state frontier to pin."
fi

# ---- report ----------------------------------------------------------------------------------
[ "$ARMS" -gt 0 ] || die 91 "ZERO arms ran. There is nothing to report, and that is not a clean result."
{
  printf '\n'
  printf '# THE FINDING, read off the arms above and nowhere else:\n'
  printf '#   lock HELD                    %s\n' "$A_LINE"
  printf '#   lock RELEASED                %s\n' "$B_LINE"
  printf '#   pin@released + lock BACK     %s\n' "$C_LINE"
} >>"$RESULTS"
say ""
say "T465-LOCK-ARMS: source=$SRCSHA arms=$ARMS"
LC_ALL=C sed -n '1,200p' "$RESULTS"
exit 0
