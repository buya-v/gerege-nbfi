#!/usr/bin/env bash
# T386 -- F-1b. THE SAME SHAPE, AFTER THE FRONT DOOR.
#
#   bash .softhouse/reviews/t386-review-t381/instruments/t386-errf-midrun-drive.sh <repo> <ref>
#
# t386-errf-drive.sh established two things:
#   * a 2> redirect that cannot be opened makes bash return 1 WITHOUT RUNNING THE COMMAND, and 1
#     is the exact status this file reads as "the engine ran and matched nothing";
#   * when that state exists from the START, the -F POSITIVE calibration arm catches it and the
#     sweep refuses at exit 3. That is P-72 earning its keep and T381 deserves the credit.
#
# THIS DRIVE ASKS THE NEXT QUESTION: the calibration runs ONCE, at the front door. What happens
# if $SWEEP_ERRF becomes unopenable AFTER it? A `git` shim counts grep invocations and removes
# the scratch directory once calibration is past. Every subsequent search is a failed redirect.
#
# CONTROL: the identical shim, with the removal disabled. If the control does not produce a
# clean 16-selector sweep the rig is broken and the RED arm means nothing.
set -uo pipefail

REPO=${1:?usage: <repo-root> <ref>}
REF=${2:?usage: <repo-root> <ref>}
SRC='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t386-midrun.XXXXXXXX") || exit 2
trap 'rm -rf "$WORK"' EXIT
git -C "$REPO" show "$REF:$SRC" > "$WORK/sweep.sh" || exit 2
echo "UNDER TEST : $REF:$SRC"
echo "  sha256   : $(shasum -a 256 < "$WORK/sweep.sh" | cut -d' ' -f1)"
echo

REALGIT=$(command -v git)
mkdir -p "$WORK/shim"
cat > "$WORK/shim/git" <<SHIM
#!/usr/bin/env bash
if [ "\${1:-}" = "grep" ]; then
  n=\$(cat "\$T386_COUNT" 2>/dev/null || echo 0); n=\$((n+1)); printf '%s' "\$n" > "\$T386_COUNT"
  if [ "\${T386_ARM:-red}" = "red" ] && [ "\$n" -gt "\$T386_AFTER" ]; then
    rm -rf "\$T386_ERRDIR"
  fi
fi
exec "$REALGIT" "\$@"
SHIM
chmod +x "$WORK/shim/git"

cat > "$WORK/shim/mktemp" <<'SHIM'
#!/usr/bin/env bash
# hand the sweep a scratch path inside the directory this drive can delete on cue
mkdir -p "$T386_ERRDIR"
printf '%s\n' "$T386_ERRDIR/errf"
: > "$T386_ERRDIR/errf"
exit 0
SHIM
chmod +x "$WORK/shim/mktemp"

run_arm() { # run_arm <red|control> <out>
  local arm="$1" outf="$2"
  rm -rf "$WORK/errdir"; : > "$WORK/count"
  (
    cd "$REPO" || exit 9
    T386_ARM="$arm" T386_AFTER=7 T386_COUNT="$WORK/count" T386_ERRDIR="$WORK/errdir" \
      PATH="$WORK/shim:$PATH" bash "$WORK/sweep.sh"
    echo "SWEEP EXIT=$?"
  ) > "$outf" 2>&1
}

echo '=== CONTROL: shim installed, scratch directory left alone =========================='
run_arm control "$WORK/control.txt"
grep -E 'SWEEP CALIBRATE|SWEEP-RESULT|SWEEP EXIT' "$WORK/control.txt" | sed 's/^/  /'
C_MZ=$(grep -c 'MEASURED ZERO' "$WORK/control.txt")
C_EXIT=$(sed -n 's/^SWEEP EXIT=//p' "$WORK/control.txt")
echo "  control: exit=$C_EXIT  MEASURED-ZERO lines=$C_MZ"
echo

echo '=== RED: the scratch directory is removed once calibration is past ================='
run_arm red "$WORK/red.txt"
grep -E 'SWEEP CALIBRATE|SWEEP-RESULT|SWEEP EXIT' "$WORK/red.txt" | sed 's/^/  /'
R_MZ=$(grep -c 'MEASURED ZERO' "$WORK/red.txt")
R_DNR=$(grep -c 'DID NOT RUN' "$WORK/red.txt")
R_EXIT=$(sed -n 's/^SWEEP EXIT=//p' "$WORK/red.txt")
echo "  red: exit=$R_EXIT  MEASURED-ZERO lines=$R_MZ  DID-NOT-RUN lines=$R_DNR"
echo "  --- a sample selector block from the RED run ---"
awk '/^=== S1 /,/^=== S2 /' "$WORK/red.txt" | head -12 | sed 's/^/  /'
echo
echo "DRIVE-RESULT: control_exit=$C_EXIT control_mz=$C_MZ red_exit=$R_EXIT red_mz=$R_MZ red_dnr=$R_DNR"
if [ "$C_EXIT" = "0" ] && [ "$C_MZ" = "0" ] && [ "$R_EXIT" = "0" ] && [ "$R_MZ" -gt 0 ]; then
  echo "*** F-1b REPRODUCED: calibration=yes, exit=0, did_not_run=0 -- and $R_MZ selectors printed"
  echo "*** 'MEASURED ZERO -- engine ran over N tracked files and matched nothing' for searches"
  echo "*** THAT NEVER RAN. The seventh instance of the shape, downstream of the front door."
else
  echo "F-1b did not reproduce."
fi
