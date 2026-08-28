#!/usr/bin/env bash
# T402 -- C-1 / F-1. THE SCRATCH-FILE CHANNEL, DRIVEN AS A CLASS RATHER THAN AS ONE SYNTAX.
#
#   bash .softhouse/capture/t402-t386-conditions/instruments/t402-errf-class-drive.sh \
#        <repo-root> <ref> <red|green>
#
# ENGINE DECLARED: this drive runs no search of its own. It runs `casualty-sweep.sh` (whose
# engine is `git grep`, declared in its own header) under a shimmed PATH and reads what the
# sweep printed. The only patterns below are `grep -c` over a captured transcript, fixed
# strings, no `-E`, and therefore no backslash-class anywhere (P-53 / C5).
#
# WHAT IT DRIVES
# --------------
# T386's F-1 says: a `2>` redirect that cannot be OPENED makes bash return 1 WITHOUT RUNNING
# THE COMMAND, and 1 is precisely the status `sel()` and `engine_count()` read as "the engine
# ran over the corpus and matched nothing". T386 proved that with ONE sabotage -- the scratch
# DIRECTORY removed mid-run -- and proposed a five-line fix: read `cat`'s status at both sites.
#
# This drive keeps that arm and ADDS THE ONE THAT DECIDES WHETHER THE PROPOSED FIX IS ENOUGH.
#
#   ARM U  "unlink"    the scratch DIRECTORY is removed once calibration is past.
#                      redirect fails (ENOENT)  AND  `cat` fails (ENOENT).
#                      -> a cat-status check DOES catch this.
#
#   ARM R  "readonly"  the scratch FILE is left in place, is filled with STALE text, and is
#                      chmod 0444 once calibration is past.
#                      redirect fails (EACCES, the file exists and cannot be truncated)
#                      BUT  `cat` SUCCEEDS and returns the stale text.
#                      -> a cat-status check does NOT catch this. The selector prints
#                         `ENGINE STDERR on a search that DID complete (rc=1)` -- naming a
#                         completion that never happened -- and then `MEASURED ZERO`.
#
#   ARM M  "T386-min"  ARM R run against a CONSTRUCTED specimen: the ref's own sweep with
#                      T386's literal five-line fix applied and NOTHING else. Built by
#                      t402-make-t386min.sh, which refuses unless each anchor is found
#                      exactly once. This arm exists to answer a question the review could not:
#                      is the five-line fix sufficient, or only necessary?
#
#   CONTROL            the identical shim with every sabotage disabled. If the control does not
#                      produce a clean sixteen-selector sweep at exit 0, the rig is broken and
#                      no RED arm above means anything. T383 shipped a fail-open repair that
#                      refused every healthy run; a guard that refuses everything is the same
#                      defect wearing the opposite sign.
#
# THIS DRIVE REPORTS FAILURE THROUGH ITS EXIT STATUS  [T402, closing FU-T386-7 on itself].
# T386 filed FU-T386-7 against `t381-red-drives.sh` because it exits 0 whatever its arms say --
# P-45 applied to the instrument written to enforce P-45. Every expectation below feeds one
# accumulator and the last line is an `exit`. A reader who checks this drive's status learns
# something about this drive.
#   0  every expectation for the requested mode held
#   1  at least one expectation did not hold  (see DRIVE-RESULT / the EXPECT rows)
#   2  the rig could not be built (bad ref, no git, specimen construction refused)
set -uo pipefail

REPO=${1:?usage: <repo-root> <ref> <red|green>}
REF=${2:?usage: <repo-root> <ref> <red|green>}
MODE=${3:?usage: <repo-root> <ref> <red|green>}
case "$MODE" in red|green) ;; *) echo "mode must be red or green" >&2; exit 2 ;; esac

SRC='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'
HERE=$(cd -- "$(dirname -- "$0")" && pwd) || exit 2

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t402-errf.XXXXXXXX") || exit 2
trap 'chmod -R u+w "$WORK" 2>/dev/null; rm -rf "$WORK"' EXIT

git -C "$REPO" show "$REF:$SRC" > "$WORK/sweep.sh" || exit 2
SWEEP_SHA=$(shasum -a 256 < "$WORK/sweep.sh" | cut -d' ' -f1) || exit 2
HEAD_SHA=$(git -C "$REPO" rev-parse --short "$REF") || exit 2

echo "T402 ERRF CLASS DRIVE"
echo "  repo       : $REPO"
echo "  ref        : $REF  ($HEAD_SHA)"
echo "  under test : $SRC"
echo "  sha256     : $SWEEP_SHA"
echo "  mode       : expecting $MODE"
echo "  host git   : $(git --version)"
echo

# ---- the T386-minimal specimen -----------------------------------------------------------
MIN_OK=no
if bash "$HERE/t402-make-t386min.sh" "$WORK/sweep.sh" "$WORK/sweep-t386min.sh" > "$WORK/min.log" 2>&1; then
  MIN_OK=yes
  echo "  ARM M specimen : BUILT  sha256 $(shasum -a 256 < "$WORK/sweep-t386min.sh" | cut -d' ' -f1)"
  sed 's/^/                 | /' "$WORK/min.log"
else
  echo "  ARM M specimen : NOT BUILT -- the anchors T386's five-line fix patches are not present"
  echo "                 exactly once in this ref. ARM M is reported as NOT-APPLICABLE, never"
  echo "                 as a pass. Builder output:"
  sed 's/^/                 | /' "$WORK/min.log"
fi
echo

# ---- the shims ---------------------------------------------------------------------------
REALGIT=$(command -v git) || exit 2
mkdir -p "$WORK/shim" || exit 2

# `git` shim: counts `grep` invocations and performs the arm's sabotage ONCE, after the seven
# calibration searches. Everything else is passed straight through.
cat > "$WORK/shim/git" <<SHIM
#!/usr/bin/env bash
if [ "\${1:-}" = "grep" ]; then
  n=\$(cat "\$T402_COUNT"); n=\$((n+1)); printf '%s' "\$n" > "\$T402_COUNT"
  if [ "\$n" -gt "\$T402_AFTER" ] && [ ! -e "\$T402_DONE" ]; then
    case "\$T402_ARM" in
      unlink)
        : > "\$T402_DONE"
        rm -rf "\$T402_ERRDIR"
        ;;
      readonly)
        : > "\$T402_DONE"
        printf '%s\n' "warning: STALE TEXT left by an earlier selector, not written by this search" \
          > "\$T402_ERRDIR/errf"
        chmod 0444 "\$T402_ERRDIR/errf"
        ;;
      none) : ;;
    esac
  fi
fi
exec "$REALGIT" "\$@"
SHIM
chmod +x "$WORK/shim/git" || exit 2

# `mktemp` shim: hands the sweep a scratch path inside a directory this drive can sabotage.
cat > "$WORK/shim/mktemp" <<'SHIM'
#!/usr/bin/env bash
mkdir -p "$T402_ERRDIR" || exit 1
printf '%s\n' "$T402_ERRDIR/errf"
: > "$T402_ERRDIR/errf"
exit 0
SHIM
chmod +x "$WORK/shim/mktemp" || exit 2

# ---- one arm -----------------------------------------------------------------------------
FAILS=0
run_arm() { # run_arm <arm: none|unlink|readonly> <script> <outfile>
  local arm="$1" script="$2" outf="$3"
  chmod -R u+w "$WORK/errdir" 2>/dev/null
  rm -rf "$WORK/errdir"
  rm -f "$WORK/done"
  printf '0' > "$WORK/count"
  (
    cd "$REPO" || exit 9
    T402_ARM="$arm" T402_AFTER=7 T402_COUNT="$WORK/count" T402_DONE="$WORK/done" \
      T402_ERRDIR="$WORK/errdir" PATH="$WORK/shim:$PATH" bash "$script"
    echo "SWEEP EXIT=$?"
  ) > "$outf" 2>&1
}

# Every cardinal this drive reports is read out of the transcript by a fixed-string count.
mz()  { grep -c 'MEASURED ZERO' "$1"; }
dnr() { grep -c 'SELECTOR DID NOT RUN' "$1"; }
xit() { sed -n 's/^SWEEP EXIT=//p' "$1"; }
res() { grep 'SWEEP-RESULT' "$1" | tail -1; }

expect() { # expect <label> <actual> <wanted>
  if [ "$2" = "$3" ]; then
    printf '    EXPECT %-34s %-10s OK\n' "$1" "$2"
  else
    printf '    EXPECT %-34s %-10s *** WANTED %s\n' "$1" "$2" "$3"
    FAILS=$((FAILS+1))
  fi
}
expect_gt() { # expect_gt <label> <actual> <floor>
  if [ "$2" -gt "$3" ]; then
    printf '    EXPECT %-34s %-10s OK (> %s)\n' "$1" "$2" "$3"
  else
    printf '    EXPECT %-34s %-10s *** WANTED > %s\n' "$1" "$2" "$3"
    FAILS=$((FAILS+1))
  fi
}

report() { # report <title> <outfile>
  echo "$1"
  res "$2" | sed 's/^/    /'
  printf '    sweep exit=%s   MEASURED-ZERO lines=%s   DID-NOT-RUN lines=%s\n' \
    "$(xit "$2")" "$(mz "$2")" "$(dnr "$2")"
}

# =========================================================================================
echo '=== CONTROL -- shim installed, nothing sabotaged ========================================'
run_arm none "$WORK/sweep.sh" "$WORK/control.txt"
grep 'SWEEP CALIBRATE' "$WORK/control.txt" | sed 's/^/    /'
grep 'SWEEP OBSERVE' "$WORK/control.txt" | sed 's/^/    /'
report '  -- control result' "$WORK/control.txt"
C_EXIT=$(xit "$WORK/control.txt"); C_MZ=$(mz "$WORK/control.txt")
C_SEL=$(res "$WORK/control.txt" | sed -n 's/.*selectors=\([0-9]*\).*/\1/p')
expect 'healthy sweep exits 0'        "$C_EXIT" '0'
expect 'healthy sweep has no MZ line' "$C_MZ"   '0'
expect 'healthy sweep ran 16 selectors' "$C_SEL" '16'
echo

# =========================================================================================
echo '=== ARM U -- the scratch DIRECTORY is removed once calibration is past =================='
echo '    redirect fails ENOENT; cat fails ENOENT. T386 F-1b, re-driven.'
run_arm unlink "$WORK/sweep.sh" "$WORK/armU.txt"
report '  -- ARM U result' "$WORK/armU.txt"
U_EXIT=$(xit "$WORK/armU.txt"); U_MZ=$(mz "$WORK/armU.txt"); U_DNR=$(dnr "$WORK/armU.txt")
if [ "$MODE" = red ]; then
  expect    'ARM U sweep still exits 0'   "$U_EXIT" '0'
  expect_gt 'ARM U fabricated MZ lines'   "$U_MZ"   0
  expect    'ARM U refusals'              "$U_DNR"  '0'
else
  expect    'ARM U refuses (exit 4)'      "$U_EXIT" '4'
  expect    'ARM U fabricated MZ lines'   "$U_MZ"   '0'
  expect_gt 'ARM U refusals'              "$U_DNR"  0
fi
echo '    -- S2 block from ARM U --'
awk '/^=== S2 /,/^=== S3 /' "$WORK/armU.txt" | head -8 | sed 's/^/      /'
echo

# =========================================================================================
echo '=== ARM R -- the scratch FILE is left readable, filled with STALE text, chmod 0444 ======'
echo '    redirect fails EACCES; cat SUCCEEDS. This is the arm a cat-status check cannot see.'
run_arm readonly "$WORK/sweep.sh" "$WORK/armR.txt"
report '  -- ARM R result' "$WORK/armR.txt"
R_EXIT=$(xit "$WORK/armR.txt"); R_MZ=$(mz "$WORK/armR.txt"); R_DNR=$(dnr "$WORK/armR.txt")
R_STALE=$(grep -c 'STALE TEXT left by an earlier selector' "$WORK/armR.txt")
if [ "$MODE" = red ]; then
  expect    'ARM R sweep still exits 0'   "$R_EXIT" '0'
  expect_gt 'ARM R fabricated MZ lines'   "$R_MZ"   0
  expect    'ARM R refusals'              "$R_DNR"  '0'
  expect_gt 'ARM R stale text reprinted'  "$R_STALE" 0
else
  expect    'ARM R refuses (exit 4)'      "$R_EXIT" '4'
  expect    'ARM R fabricated MZ lines'   "$R_MZ"   '0'
  expect_gt 'ARM R refusals'              "$R_DNR"  0
fi
echo '    -- S2 block from ARM R --'
awk '/^=== S2 /,/^=== S3 /' "$WORK/armR.txt" | head -8 | sed 's/^/      /'
echo

# =========================================================================================
echo '=== ARM M -- ARM R against T386'"'"'s literal five-line fix, and NOTHING else ============='
if [ "$MIN_OK" != yes ]; then
  echo '    NOT APPLICABLE at this ref -- the specimen could not be constructed (see above).'
  echo '    Reported as not-applicable, never as a pass.'
else
  run_arm readonly "$WORK/sweep-t386min.sh" "$WORK/armM.txt"
  report '  -- ARM M result' "$WORK/armM.txt"
  M_EXIT=$(xit "$WORK/armM.txt"); M_MZ=$(mz "$WORK/armM.txt"); M_DNR=$(dnr "$WORK/armM.txt")
  echo '    -- S2 block from ARM M --'
  awk '/^=== S2 /,/^=== S3 /' "$WORK/armM.txt" | head -8 | sed 's/^/      /'
  echo
  echo '    ADJUDICATION. The five-line fix reads cat'"'"'s status. On ARM R cat SUCCEEDS, so the'
  echo '    check does not fire, and the specimen prints a MEASURED ZERO for a search that never'
  echo '    ran -- under a stale warning line that names a completion which did not happen.'
  expect    'ARM M (T386-min) still exits 0' "$M_EXIT" '0'
  expect_gt 'ARM M fabricated MZ lines'      "$M_MZ"   0
  expect    'ARM M refusals'                 "$M_DNR"  '0'
fi
echo

# =========================================================================================
printf 'DRIVE-RESULT: ref=%s mode=%s control_exit=%s control_mz=%s control_sel=%s' \
  "$HEAD_SHA" "$MODE" "$C_EXIT" "$C_MZ" "$C_SEL"
printf ' U_exit=%s U_mz=%s U_dnr=%s R_exit=%s R_mz=%s R_dnr=%s\n' \
  "$U_EXIT" "$U_MZ" "$U_DNR" "$R_EXIT" "$R_MZ" "$R_DNR"
echo "DRIVE-EXPECTATIONS-FAILED: $FAILS"
if [ "$FAILS" -eq 0 ]; then
  echo "*** ALL EXPECTATIONS FOR MODE=$MODE HELD."
else
  echo "*** $FAILS EXPECTATION(S) DID NOT HOLD FOR MODE=$MODE. This drive is reporting FAILURE"
  echo "*** through its exit status, which is the whole of FU-T386-7."
fi
exit $(( FAILS > 0 ? 1 : 0 ))
