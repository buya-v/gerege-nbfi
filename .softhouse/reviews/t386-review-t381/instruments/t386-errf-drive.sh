#!/usr/bin/env bash
# T386 -- F-1. THE SEVENTH INSTANCE OF THE DISCARDED-STATUS SHAPE.
#
#   bash .softhouse/reviews/t386-review-t381/instruments/t386-errf-drive.sh <repo-root> <ref>
#
# T381 routed every calibration search through engine_count() and hardened sel(), and both now
# read `git grep`'s status. Both write the engine's stderr to `$SWEEP_ERRF`:
#
#     out=$(git grep "$@" 2>"$SWEEP_ERRF"); rc=$?          # engine_count()
#     all=$(git grep "$@" -- .softhouse 2>"$SWEEP_ERRF"); rc=$?   # sel()
#
# IF THE REDIRECT ITSELF CANNOT BE OPENED, THE COMMAND NEVER RUNS AND BASH RETURNS 1.
# `rc == 1` is the one status this file has taught itself to read as A MEASURED ZERO:
#   * engine_count() returns 0 with ENGINE_N=0;
#   * the -F ANTI arm prints `PASS -- known negative matched 0 times, and the search RAN (rc=1)`;
#   * sel() prints `MEASURED ZERO -- engine ran over N tracked files ... and matched nothing`.
# A search that ERRORED is again indistinguishable from a search that found nothing -- the exact
# shape, in the chokepoint, after the repair. The R4 scratch file is the new single point of
# failure and nothing checks it is still writable.
#
# ARM 1 proves what bash returns for a failed redirect.
# ARM 2 drives the SHIPPED script with an unwritable $SWEEP_ERRF and reads what it prints.
# ARM 3 is the CONTROL: the same script, same corpus, writable scratch file -- it must PASS,
#       so ARM 2's refusal-free green cannot be blamed on a broken rig.
set -uo pipefail

REPO=${1:?usage: <repo-root> <ref>}
REF=${2:?usage: <repo-root> <ref>}
SRC='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t386-errf.XXXXXXXX") || exit 2
cleanup() { chmod -R u+rwX "$WORK" 2>/dev/null; rm -rf "$WORK"; }
trap cleanup EXIT

git -C "$REPO" show "$REF:$SRC" > "$WORK/sweep.sh" || exit 2
echo "UNDER TEST : $REF:$SRC"
echo "  sha256   : $(shasum -a 256 < "$WORK/sweep.sh" | cut -d' ' -f1)"
echo

echo '=== ARM 1: what exit status does bash give when a 2> redirect cannot be opened? ====='
mkdir -p "$WORK/a1"
E="$WORK/a1/nosuchdir/errf"
out=$(git -C "$REPO" --version 2>"$E"); rc=$?
echo "  parent directory missing   : rc=$rc  stdout=[$out]"
: > "$WORK/a1/ro"; chmod 000 "$WORK/a1/ro"
out=$(git -C "$REPO" --version 2>"$WORK/a1/ro"); rc2=$?
echo "  scratch file mode 000      : rc=$rc2 stdout=[$out]"
chmod 644 "$WORK/a1/ro"
echo "  >>> bash returns 1 -- the SAME status git grep uses for 'ran, matched nothing'."
echo

echo '=== ARM 2 (RED): the shipped sweep with an unwritable $SWEEP_ERRF =================='
# mktemp is left alone; the scratch file is made unwritable immediately after it is created, by
# pointing TMPDIR at a directory that is writable for the mktemp and then read-only afterwards.
# The cleanest way to reach the same state without racing is to preload a `mktemp` shim that
# hands back a path whose parent does not exist.
mkdir -p "$WORK/shim2"
cat > "$WORK/shim2/mktemp" <<'SHIM'
#!/usr/bin/env bash
# hand back a path inside a directory that does not exist: the file cannot be created, but the
# script's own `|| exit 2` guard does not fire because mktemp itself reports success.
printf '%s\n' "${T386_DEAD_PATH:?}"
exit 0
SHIM
chmod +x "$WORK/shim2/mktemp"
(
  cd "$REPO" || exit 9
  T386_DEAD_PATH="$WORK/gone/errf" PATH="$WORK/shim2:$PATH" bash "$WORK/sweep.sh"
  echo "SWEEP EXIT=$?"
) > "$WORK/arm2.txt" 2>&1
echo "  --- first 24 lines of the RED run ---"
sed -n '1,24p' "$WORK/arm2.txt" | sed 's/^/  /'
echo "  --- the summary line and exit ---"
grep -E 'SWEEP-RESULT|SWEEP EXIT|MEASURED ZERO' "$WORK/arm2.txt" | head -20 | sed 's/^/  /'
A2_MZ=$(grep -c 'MEASURED ZERO' "$WORK/arm2.txt")
A2_EXIT=$(sed -n 's/^SWEEP EXIT=//p' "$WORK/arm2.txt")
echo
echo "  RED VERDICT: exit=$A2_EXIT  'MEASURED ZERO' lines=$A2_MZ"
echo

echo '=== ARM 3 (CONTROL): the same shipped sweep, scratch file writable ================='
(
  cd "$REPO" || exit 9
  bash "$WORK/sweep.sh"
  echo "SWEEP EXIT=$?"
) > "$WORK/arm3.txt" 2>&1
grep -E 'SWEEP-RESULT|SWEEP EXIT' "$WORK/arm3.txt" | sed 's/^/  /'
A3_EXIT=$(sed -n 's/^SWEEP EXIT=//p' "$WORK/arm3.txt")
echo
echo "DRIVE-RESULT: red_exit=$A2_EXIT red_measured_zero_lines=$A2_MZ control_exit=$A3_EXIT"
if [ "$A2_EXIT" = "0" ]; then
  echo "*** F-1 REPRODUCED: the sweep reported exit 0 -- a clean, admissible sweep -- while NOT ONE"
  echo "*** of its searches ran. Every zero it printed is a zero nobody measured."
else
  echo "F-1 did not reproduce at this head."
fi
