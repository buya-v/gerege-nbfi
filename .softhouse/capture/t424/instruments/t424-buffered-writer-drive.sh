#!/usr/bin/env bash
# =============================================================================================
# T424 / F-T408-4 -- THE BUFFERED-WRITER DRIVE.
#
# T402's FU-T386-7 patch makes `t381-red-drives.sh` report its arms through its exit status by
# RE-READING $T381_DRIVE_LOG -- a file `tee` is still writing. T408 measured the guard 8/8
# correct with this host's BSD `tee` and 3/3 FAIL-OPEN with a stdio-buffered stand-in. Correct by
# accident of the local writer's buffering is not correct.
#
# This drive proves the amended guard on THE CASE THAT BROKE THE OLD ONE, and keeps the case
# that already worked beside it.
#
# NEITHER GUARD IS RETYPED. Both are extracted, by content, from the shipped patch files:
#   OLD = .../t402-t386-conditions/patches/FU-T386-7-red-drive-must-report-failure.patch
#   NEW = .../t424/patches/FU-T386-7-...AMENDED-BY-T424.patch
# Extraction refuses unless each anchor is found exactly once, so this cannot report "the fix
# works" about a guard that was never extracted.
#
# WRITERS
#   HOSTTEE  -- this host's `tee` (BSD). The control: the case that already passed.
#   BUFTEE   -- instruments/t424-buffered-tee-standin.py, a 1 MiB stdio-buffered stand-in
#               (T408 used 64 KiB; larger is strictly harsher -- nothing reaches the file until
#               close()). Screen output stays live, so the failing arm is VISIBLE while the
#               guard reads a file that does not have it yet.
#
# Exit 0 only if every arm meets its declared expectation.
# =============================================================================================
set -uo pipefail

REPO=${T424_REPO:-$(git rev-parse --show-toplevel)}
HERE="$REPO/.softhouse/capture/t424/instruments"
OLD_PATCH="$REPO/.softhouse/capture/t402-t386-conditions/patches/FU-T386-7-red-drive-must-report-failure.patch"
NEW_PATCH="$REPO/.softhouse/capture/t424/patches/FU-T386-7-red-drive-must-report-failure.AMENDED-BY-T424.patch"
BUFTEE="$HERE/t424-buffered-tee-standin.py"
REAL_DRIVE='.softhouse/capture/t381-t379-conditions/instruments/t381-red-drives.sh'
RUNS=${T424_RUNS:-8}
FAILED=0
# The last ref at which casualty-sweep.sh still carried the pre-T402 defects; the real drive
# refuses outright if BEFORE and AFTER are the same file, which they are on this branch.
export BEFORE_REF=${BEFORE_REF:-964b532e}

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t424-buf.XXXXXXXX") || exit 2
trap 'rm -rf "$WORK"' EXIT

for f in "$OLD_PATCH" "$NEW_PATCH" "$BUFTEE"; do
  [ -r "$f" ] || { echo "REFUSED: cannot read $f" >&2; exit 2; }
done
echo "OLD guard patch sha256: $(shasum -a 256 "$OLD_PATCH" | cut -c1-16)   $OLD_PATCH"
echo "NEW guard patch sha256: $(shasum -a 256 "$NEW_PATCH" | cut -c1-16)   $NEW_PATCH"
echo "host tee              : $(command -v tee)"
echo "buffered stand-in     : $BUFTEE"
echo "runs per arm          : $RUNS"
echo

# ---------------------------------------------------------------------------------------------
# EXTRACT the two guards from their patches, by content.
# ---------------------------------------------------------------------------------------------
_added() { grep '^+' "$1" | grep -v '^+++' | sed 's/^+//'; }

_added "$OLD_PATCH" > "$WORK/old-added.txt"
n=$(grep -c -F 'if [ -n "${T381_DRIVE_LOG:-}" ] && [ -f "${T381_DRIVE_LOG:-}" ]; then' "$WORK/old-added.txt")
[ "$n" = "1" ] || { echo "REFUSED: OLD guard anchor matched $n times, expected 1" >&2; exit 2; }
awk 'index($0,"if [ -n \"${T381_DRIVE_LOG:-}\" ] && [ -f \"${T381_DRIVE_LOG:-}\" ]; then")==1 {o=1}
     o {print}' "$WORK/old-added.txt" > "$WORK/old-guard.sh"
grep -q 'T402 GUARD: every arm reproduced' "$WORK/old-guard.sh" \
  || { echo "REFUSED: OLD guard extraction is truncated" >&2; exit 2; }

_added "$NEW_PATCH" > "$WORK/new-added.txt"
n=$(grep -c -F 'if [ -z "${T381_DRIVE_INNER:-}" ]; then' "$WORK/new-added.txt")
[ "$n" = "1" ] || { echo "REFUSED: NEW guard anchor matched $n times, expected 1" >&2; exit 2; }
# Stop at the guard's own closing `fi` -- the only one at column 0; every `fi` inside it is
# indented. Refuse if that closer is never seen.
awk 'index($0,"if [ -z \"${T381_DRIVE_INNER:-}\" ]; then")==1 {o=1}
     o {print}
     o && $0=="fi" {closed=1; exit}
     END { if (!closed) exit 3 }' "$WORK/new-added.txt" > "$WORK/new-guard.sh"
tail -1 "$WORK/new-guard.sh" | grep -qx 'fi' \
  || { echo "REFUSED: NEW guard extraction did not end at its closing fi" >&2; exit 2; }
grep -q 'does not depend on any writer' "$WORK/new-guard.sh" \
  || { echo "REFUSED: NEW guard extraction is truncated" >&2; exit 2; }

echo "OLD guard extracted: $(grep -c . "$WORK/old-guard.sh") lines"
echo "NEW guard extracted: $(grep -c . "$WORK/new-guard.sh") lines"
echo

# ---------------------------------------------------------------------------------------------
# SPECIMEN BODIES. Same shape as the real drive: a long run of arm output, then the last thing
# printed before the guard is the arm verdict -- the worst case, and the real one, since D-R5's
# `THE HARDENING IS NOT PROVEN` line is the last verdict the real drive prints.
# ---------------------------------------------------------------------------------------------
body_bad()   { echo 'for i in $(seq 1 400); do echo "D-R$i ... filler ...................................."; done'
               echo 'echo "  >>> D-R5 DID NOT REPRODUCE in the RED specimen."'
               echo 'echo "END OF DRIVES."'; }
body_good()  { echo 'for i in $(seq 1 400); do echo "D-R$i ... filler ...................................."; done'
               echo 'echo "  >>> GREEN CONFIRMED: the shipped form REFUSES and exits 3."'
               echo 'echo "END OF DRIVES."'; }
body_abort() { echo 'for i in $(seq 1 40); do echo "D-R$i ... filler ...................................."; done'
               echo 'echo "  D-R2: could not patch BEFORE. DRIVE FAILED."'
               echo 'exit 4'; }

mk_specimen() { # mk_specimen <old|new> <bad|good|abort> <outfile>
  local guard=$1 body=$2 out=$3
  { echo '#!/usr/bin/env bash'
    echo 'set -uo pipefail'
    if [ "$guard" = new ]; then cat "$WORK/new-guard.sh"; fi
    "body_$body"
    if [ "$guard" = old ]; then echo; cat "$WORK/old-guard.sh"; else echo 'exit 0'; fi
  } > "$out"
  bash -n "$out" || { echo "REFUSED: specimen $out is not valid bash" >&2; exit 2; }
}

# ---------------------------------------------------------------------------------------------
# WRITER shims. For the NEW guard the writer is invoked as `tee` from inside the guard, so the
# stand-in is put on PATH under the name `tee` -- the guard is given no way to tell.
# ---------------------------------------------------------------------------------------------
mkdir -p "$WORK/shim-buftee"
{ echo '#!/usr/bin/env bash'
  echo "exec /usr/bin/env python3 $BUFTEE \"\$@\""
} > "$WORK/shim-buftee/tee"
chmod +x "$WORK/shim-buftee/tee"

run_old () { # run_old <body> <hosttee|buftee>  -> echoes guard exit status
  local body=$1 writer=$2 spec="$WORK/spec-old-$1-$2.sh" log="$WORK/log-old-$1-$2.txt" rc
  mk_specimen old "$body" "$spec"
  : > "$log"
  if [ "$writer" = hosttee ]; then
    T381_DRIVE_LOG="$log" bash "$spec" 2>&1 | tee "$log" > /dev/null
  else
    T381_DRIVE_LOG="$log" bash "$spec" 2>&1 | "$WORK/shim-buftee/tee" "$log" > /dev/null
  fi
  rc=${PIPESTATUS[0]}
  echo "$rc"
}

run_new () { # run_new <body> <hosttee|buftee>  -> echoes guard exit status
  local body=$1 writer=$2 spec="$WORK/spec-new-$1-$2.sh" log="$WORK/log-new-$1-$2.txt" rc
  mk_specimen new "$body" "$spec"
  if [ "$writer" = hosttee ]; then
    T381_DRIVE_LOG="$log" bash "$spec" > /dev/null 2>&1
  else
    T381_DRIVE_LOG="$log" PATH="$WORK/shim-buftee:$PATH" bash "$spec" > /dev/null 2>&1
  fi
  rc=$?
  echo "$rc"
}

arm () { # arm <label> <old|new> <body> <writer> <expected-rc>
  local label=$1 guard=$2 body=$3 writer=$4 want=$5 i rc hits=0 seen=""
  for i in $(seq 1 "$RUNS"); do
    rc=$("run_$guard" "$body" "$writer")
    seen="$seen $rc"
    if [ "$rc" = "$want" ]; then hits=$((hits+1)); fi
  done
  printf '%-58s %s/%s  exits:%s  want %s  %s\n' "$label" "$hits" "$RUNS" "$seen" "$want" \
    "$( if [ "$hits" = "$RUNS" ]; then echo OK; else echo '*** MISMATCH'; fi )"
  if [ "$hits" != "$RUNS" ]; then FAILED=$((FAILED+1)); fi
}

echo "=============================================================================="
echo "PART 1 -- RED. T402's SHIPPED guard, on both writers."
echo "  exit 1 = the failing arm was seen (correct). exit 0 = FAIL-OPEN."
echo "=============================================================================="
arm "OLD guard / failing arm / host tee (BSD)      [control]" old bad   hosttee 1
arm "OLD guard / failing arm / BUFFERED stand-in   [the bug]" old bad   buftee  0
arm "OLD guard / healthy     / host tee            [control]" old good  hosttee 0
arm "OLD guard / healthy     / BUFFERED stand-in            " old good  buftee  0
arm "OLD guard / drive dies early (exit 4)                  " old abort hosttee 4
echo "  note: the 'exit 0' rows are opposite things. Row 2 is THE FAIL-OPEN -- a failing arm on"
echo "        screen and exit 0 from the guard. Rows 3-4 are correct passes."
echo "  note: row 5 is NOT a fail-open and is recorded so as not to overstate the finding. The"
echo "        real drive's aborts all use a non-zero \`exit\`, and T402's tail guard is simply"
echo "        NEVER REACHED -- the script exits 4 on its own. What it does mean is that on this"
echo "        tree the T402 guard is never exercised at all (PART 3), so its buffering"
echo "        dependence would have been discovered by nobody."
echo

echo "=============================================================================="
echo "PART 2 -- GREEN. T424's amended guard, on the SAME writers and the SAME bodies."
echo "=============================================================================="
arm "NEW guard / failing arm / BUFFERED stand-in  [the proof]" new bad   buftee  1
arm "NEW guard / failing arm / host tee (BSD)     [control]  " new bad   hosttee 1
arm "NEW guard / healthy     / BUFFERED stand-in  [not vacuous]" new good buftee  0
arm "NEW guard / healthy     / host tee           [not vacuous]" new good hosttee 0
arm "NEW guard / ABORTED run / BUFFERED stand-in  [refuses]  " new abort buftee  2
arm "NEW guard / ABORTED run / host tee           [refuses]  " new abort hosttee 2
echo

echo "=============================================================================="
echo "PART 3 -- END-TO-END on the REAL t381-red-drives.sh, each guard actually applied."
echo "  The real drive aborts on this tree (BEFORE_REF=$BEFORE_REF; its D-R2 BEFORE specimen"
echo "  has rotted), so this is a real early death, not a synthetic one. The point is WHERE the"
echo "  grader sits: T402's is the last statement of the drive and is skipped by every abort;"
echo "  T424's is in the PARENT and grades the run whatever the child did."
echo "=============================================================================="
SCRATCH="$WORK/e2e"
mkdir -p "$SCRATCH"
cp "$REPO/$REAL_DRIVE" "$SCRATCH/real-unpatched.sh"
cp "$REPO/$REAL_DRIVE" "$SCRATCH/real-old.sh"
cp "$REPO/$REAL_DRIVE" "$SCRATCH/real-new.sh"
# Apply each patch's added tail/top to the copies with the same anchors the patch uses.
_apply_added_tail() { cat "$WORK/old-guard.sh" >> "$1"; }
_apply_new() {
  awk -v g="$WORK/new-guard.sh" '
    { print }
    $0 == "set -uo pipefail" { while ((getline l < g) > 0) print l; close(g) }' "$1" > "$1.tmp"
  mv "$1.tmp" "$1"
  printf '\nexit 0\n' >> "$1"
}
_apply_added_tail "$SCRATCH/real-old.sh"
_apply_new "$SCRATCH/real-new.sh"
bash -n "$SCRATCH/real-old.sh" || { echo "REFUSED: real-old.sh invalid" >&2; exit 2; }
bash -n "$SCRATCH/real-new.sh" || { echo "REFUSED: real-new.sh invalid" >&2; exit 2; }

cd "$REPO" || exit 2
_l1="$WORK/e2e-old.log"; : > "$_l1"
T381_DRIVE_LOG="$_l1" bash "$SCRATCH/real-old.sh" 2>&1 | tee "$_l1" > /dev/null
_e1=${PIPESTATUS[0]}
_l2="$WORK/e2e-new.log"; : > "$_l2"
T381_DRIVE_LOG="$_l2" bash "$SCRATCH/real-new.sh" > /dev/null 2>&1
_e2=$?
_l3="$WORK/e2e-newbuf.log"; : > "$_l3"
T381_DRIVE_LOG="$_l3" PATH="$WORK/shim-buftee:$PATH" bash "$SCRATCH/real-new.sh" > /dev/null 2>&1
_e3=$?
_raw=$(bash "$SCRATCH/real-unpatched.sh" > /dev/null 2>&1; echo $?)
printf '  REAL drive, unpatched, its own exit status        -> %s  (it aborts at D-R2)\n' "$_raw"
printf '  REAL drive + T402 guard   (host tee)              -> %s  %s\n' "$_e1" \
  "$( if [ "$_e1" = 4 ]; then echo '<- the guard was NEVER REACHED; this is the drive own exit'; fi )"
printf '  REAL drive + T424 guard   (host tee)              -> %s  %s\n' "$_e2" \
  "$( if [ "$_e2" = 2 ]; then echo '<- REFUSES: inner exited 4, no END-OF-DRIVES sentinel'; fi )"
printf '  REAL drive + T424 guard   (BUFFERED stand-in)     -> %s  %s\n' "$_e3" \
  "$( if [ "$_e3" = 2 ]; then echo '<- REFUSES, same verdict, different writer'; fi )"
if [ "$_e1" != "4" ]; then echo "  *** expected the T402 guard not to be reached (exit 4)"; FAILED=$((FAILED+1)); fi
if [ "$_e2" != "2" ]; then echo "  *** expected the T424 guard to refuse (host tee)"; FAILED=$((FAILED+1)); fi
if [ "$_e3" != "2" ]; then echo "  *** expected the T424 guard to refuse (buffered)"; FAILED=$((FAILED+1)); fi
echo

echo "=============================================================================="
printf 'T424-BUFFERED-WRITER-DRIVE-RESULT: arms_failed=%s runs_per_arm=%s\n' "$FAILED" "$RUNS"
if [ "$FAILED" -gt 0 ]; then
  echo "*** THIS DRIVE FAILED. It reports that through its exit status."
  exit 1
fi
echo "Every arm met its declared expectation."
exit 0
