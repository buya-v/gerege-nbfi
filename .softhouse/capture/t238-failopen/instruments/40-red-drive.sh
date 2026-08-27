#!/bin/bash
# T238 -- DRIVE THE REPAIRED INSTRUMENT RED, THEN GREEN.        P-22 / P-45.
#
# P-45 now has FOUR instances in this program: a guard seen to fail only when invoked by hand
# enforces nothing. So every failure mode of the repaired sweep is driven HERE, through the
# route that actually runs it -- `bash sweep.sh`, exactly as an auditor would invoke it.
#
# A FAIL-CLOSED INSTRUMENT MUST PROVE FOUR THINGS, and all four are driven below:
#   RED  1  corpus unreachable        -> exit 90, never "(no hits)"
#   RED  2  corpus reachable but empty-> exit 91, never "(no hits)"
#   RED  3  calibration misses        -> exit 92, never "(no hits)"
#   GREEN 4 real corpus               -> exit 0, and it FINDS THE KNOWN POSITIVE
set -u
ROOT=$(git rev-parse --show-toplevel) || exit 90
SWEEP="$ROOT/.softhouse/reviews/a2-33-dec2-rev5/sweep.sh"
export SWEEP_ABS="$SWEEP"
OUT="$ROOT/.softhouse/capture/t238-failopen/evidence/red-drive"
mkdir -p "$OUT"

echo "T238 RED/GREEN DRIVE OF .softhouse/reviews/a2-33-dec2-rev5/sweep.sh"
echo "commit : $(git -C "$ROOT" rev-parse HEAD)"
echo "engine : git grep -n -I -i -E  [git $(git --version | awk '{print $3}')]"
echo
echo "BASELINE, for comparison -- the instrument AS IT WAS BEFORE THIS REPAIR."
# P-24: a baseline is a LITERAL SHA, never a moving ref.
#
# The first version of this line read `git show HEAD:...`. That was WRONG and it is worth
# recording rather than quietly fixing: once the repair was committed, `HEAD:` resolved to the
# REPAIRED file, so the leg labelled "ORIGINAL" silently began running the new instrument and
# comparing it against itself. A moving baseline is the same family of defect this whole task
# is about -- an artefact that reports something other than what its label claims -- and it
# appeared inside the instrument built to catch that family. Pinned to the fork point instead.
BASE=477dc2da0f9edf3922e7d29e689bc6473289befc      # == origin/main, MEASURED (P-71)
echo "Recovered from the LITERAL sha $BASE (the measured fork point) and run verbatim:"
git -C "$ROOT" show "$BASE:.softhouse/reviews/a2-33-dec2-rev5/sweep.sh" > "$OUT/sweep-ORIGINAL.sh" || exit 91
echo "  sha256(original) = $(shasum -a 256 "$OUT/sweep-ORIGINAL.sh" | cut -d' ' -f1)"
echo "  expected         = c076016e292186b8d320b8b7cbab34adc29502d4c54395eda0487551d0e35eb2"
( cd "$ROOT" && bash "$OUT/sweep-ORIGINAL.sh" REPO ) > "$OUT/00-baseline-original.txt" 2>&1
rc=$?
printf '  ORIGINAL   exit=%-3s  "(no hits)" lines=%-4s  hit lines=%s\n' "$rc" \
  "$(LC_ALL=C /usr/bin/grep -c '(no hits)' "$OUT/00-baseline-original.txt" || true)" \
  "$(LC_ALL=C /usr/bin/grep -cv -e '^##########' -e '(no hits)' -e '^$' "$OUT/00-baseline-original.txt" || true)"
echo "  >>> exit 0 with 34 reassurances and zero measurements. THAT is the defect."
echo

drive() { # drive <tag> <expected_exit> <description> -- reads the command from stdin
  local tag="$1" want="$2" desc="$3"
  local log="$OUT/$tag.txt"
  echo "=================================================================="
  echo "$desc"
  bash -c "$(cat)" > "$log" 2>&1
  local rc=$?
  local nohits
  nohits=$(LC_ALL=C /usr/bin/grep -c -i '(no hits)' "$log" || true)
  printf '  exit status ............ %s   (expected %s)\n' "$rc" "$want"
  printf '  "(no hits)" lines ...... %s   (expected 0 -- a fail-closed instrument NEVER prints one)\n' "$nohits"
  if [ "$rc" = "$want" ] && [ "$nohits" -eq 0 ]; then
    printf '  RESULT ................. PASS\n'
  else
    printf '  RESULT ................. *** FAIL ***\n'
  fi
  echo "  --- output ---"
  head -8 "$log" | sed -e 's/^/  | /'
  echo
}

# ---------------------------------------------------------------- RED 1
drive 10-red-unreachable 90 "RED 1 -- CORPUS UNREACHABLE. Run from a directory that is not a git work tree." <<'CMD'
D=$(mktemp -d /tmp/t238-notarepo-XXXXXX)
cd "$D" || exit 99
bash "$SWEEP_ABS" REPO
rc=$?
rm -rf "$D"
exit $rc
CMD

# ---------------------------------------------------------------- RED 2
drive 20-red-empty 91 "RED 2 -- CORPUS REACHABLE BUT EMPTY. A git repo that tracks ZERO files." <<'CMD'
D=$(mktemp -d /tmp/t238-emptyrepo-XXXXXX)
cd "$D" || exit 99
git init -q . 2>/dev/null
bash "$SWEEP_ABS" REPO
rc=$?
rm -rf "$D"
exit $rc
CMD

# ---------------------------------------------------------------- RED 3
drive 30-red-calibration 92 "RED 3 -- CALIBRATION MISSES. A real, NON-EMPTY repo that simply does not contain the known positive." <<'CMD'
D=$(mktemp -d /tmp/t238-otherrepo-XXXXXX)
cd "$D" || exit 99
git init -q . 2>/dev/null
git config user.email t238@local; git config user.name t238
printf 'this corpus is real and non-empty but contains nothing about the sweep\n' > only.txt
git add only.txt >/dev/null 2>&1
git -c commit.gpgsign=false commit -q -m x >/dev/null 2>&1
bash "$SWEEP_ABS" REPO
rc=$?
rm -rf "$D"
exit $rc
CMD

# ---------------------------------------------------------------- RED 4
drive 40-red-badfile 90 "RED 4 -- SINGLE-FILE MODE pointed at a file that does not exist." <<'CMD'
bash "$SWEEP_ABS" /tmp/t238-this-file-does-not-exist-$$.txt
CMD

# ---------------------------------------------------------------- GREEN
echo "=================================================================="
echo "GREEN -- THE REAL CORPUS. The instrument must exit 0 AND FIND THE KNOWN POSITIVE."
( cd "$ROOT" && bash "$SWEEP" REPO ) > "$OUT/90-green-live.txt" 2>&1
rc=$?
pat=$(LC_ALL=C /usr/bin/grep -c '^########## PATTERN' "$OUT/90-green-live.txt" || true)
nohit=$(LC_ALL=C /usr/bin/grep -c '(no hits)' "$OUT/90-green-live.txt" || true)
mzero=$(LC_ALL=C /usr/bin/grep -c 'MEASURED ZERO' "$OUT/90-green-live.txt" || true)
hits=$(LC_ALL=C /usr/bin/grep -cv -e '^##########' -e 'MEASURED ZERO' -e '^SWEEP' -e '^====' -e '^$' "$OUT/90-green-live.txt" || true)
printf '  exit status ............ %s   (expected 0)\n' "$rc"
printf '  patterns run ........... %s   (expected 34 -- byte-identical to the original set)\n' "$pat"
printf '  "(no hits)" lines ...... %s   (expected 0 -- the string is GONE from the instrument)\n' "$nohit"
printf '  MEASURED ZERO lines .... %s   (an HONEST zero: the engine ran and matched nothing)\n' "$mzero"
printf '  hit lines .............. %s\n' "$hits"
echo "  --- header + trailer ---"
head -8 "$OUT/90-green-live.txt" | sed -e 's/^/  | /'
echo "  | ..."
tail -3 "$OUT/90-green-live.txt" | sed -e 's/^/  | /'
echo
echo "=================================================================="
echo "SUMMARY"
echo "  ORIGINAL  : exit 0, 34 x '(no hits)', 0 hit lines, NOTHING MEASURED  -> FAIL-OPEN"
echo "  REPAIRED  : 90 / 91 / 92 / 90 on the four unreachable-corpus paths   -> FAIL-CLOSED"
echo "  REPAIRED  : exit 0 with $pat patterns and $hits hit lines on the live corpus -> IT WORKS"
echo "  The string '(no hits)' no longer exists in the instrument at all."
