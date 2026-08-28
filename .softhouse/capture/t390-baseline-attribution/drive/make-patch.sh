#!/usr/bin/env bash
# T390 make-patch.sh -- BUILD THE EXACT conformance.sh PATCH, AS A REQUEST.
#
#   bash .softhouse/capture/t390-baseline-attribution/drive/make-patch.sh
#
# T390 may NOT edit `.softhouse/conformance.sh` -- T404 holds it this wave. So the wiring is
# shipped the way T360 shipped its: as a patch that has been APPLIED AND DRIVEN somewhere else,
# with the diff committed, so the task that lands it (T399) is copying a measured change rather
# than re-deriving one from prose.
#
# The patch is GENERATED, never typed. Every hunk is anchored on a line this script first checks
# occurs EXACTLY ONCE in the target; if an anchor is missing or ambiguous the generator REFUSES
# rather than producing a patch that would land somewhere surprising.
#
# WRITES (all inside T390's grant):
#   out/conformance-T390-wiring.patch   unified diff, verified to apply with `git apply --check`
#   out/conformance-PATCHED.sh          the patched file, for the end-to-end drive
set -uo pipefail

DRIVE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CAP=$(cd "$DRIVE/.." && pwd)
ROOT=$(cd "$CAP/../../.." && pwd)
SRC="$ROOT/.softhouse/conformance.sh"
GUARD="$DRIVE/guard-oracle-state-attributed.sh"
OUT="$CAP/out"
PATCHED="$OUT/conformance-PATCHED.sh"
PATCH="$OUT/conformance-T390-wiring.patch"

[ -f "$SRC" ]   || { echo "REFUSING: no $SRC" >&2; exit 2; }
[ -f "$GUARD" ] || { echo "REFUSING: no $GUARD" >&2; exit 2; }

# --- anchors, each asserted UNIQUE before anything is written -----------------------------
A1='GUARD_COST_BUDGETS="guard_graded_root_is_this_tree|60'
A2='guard_reconciler_ownership|500"'
A3='  guard_cost_census                               || failed=1'
A4='#     load_toolchain -> run_guards path a graded run takes, contacts NO oracle, and costs'

refuse_anchor() {
  echo "REFUSING: anchor occurs $2 times, expected exactly 1:" >&2
  echo "  $1" >&2
  exit 2
}
for a in A1 A2 A3 A4; do
  pat=${!a}
  n=$(LC_ALL=C grep -cF -- "$pat" "$SRC")
  [ "$n" = "1" ] || refuse_anchor "$pat" "$n"
  echo "anchor $a unique: ${pat:0:60}..."
done

# --- H1: the guard function, inserted immediately BEFORE the cost-budget table -------------
# Placed there because that is where the other guards' definitions end and the registration
# machinery begins; nothing about the position is load-bearing beyond "defined before used".
awk -v guardfile="$GUARD" -v a1="$A1" '
  index($0, a1) == 1 && !done {
    while ((getline line < guardfile) > 0) print line
    close(guardfile)
    print ""
    done = 1
  }
  { print }
' "$SRC" > "$PATCHED.tmp1" || exit 2

# --- H2: one row in GUARD_COST_BUDGETS -----------------------------------------------------
# 60 seconds, matching every other cheap guard. MEASURED, not guessed: three consecutive runs
# of the instrument on this host took 2s / 1s / 1s [out/COST-instrument.txt]. The budget is
# headroom for a slow docker, not an estimate of the cost.
awk -v a2="$A2" '
  index($0, a2) > 0 && !done {
    sub(/guard_reconciler_ownership\|500"/, "guard_reconciler_ownership|500\nguard_oracle_state_attributed|60\"")
    done = 1
  }
  { print }
' "$PATCHED.tmp1" > "$PATCHED.tmp2" || exit 2

# --- H3: the call in run_guards ------------------------------------------------------------
# LAST among the guards and immediately before guard_cost_census. Deliberate: this is the only
# guard in the file that leaves the machine, and the file's stated convention is cheapest-first
# so a fast local refusal prints before a slow one is paid for. It joins the `failed=1` tally
# rather than short-circuiting -- unlike guard_graded_root_is_this_tree it does not invalidate
# any other guard's answer, and one bad guard must not hide another.
awk -v a3="$A3" '
  index($0, a3) == 1 && !done {
    print "  # T390 -- the LAST guard, because it is the only one that leaves this machine. An"
    print "  # unreachable database SKIPS (see the function head); an UNATTRIBUTED row REFUSES."
    print "  timed_guard guard_oracle_state_attributed       || failed=1   # T390, instrument by T363"
    done = 1
  }
  { print }
' "$PATCHED.tmp2" > "$PATCHED.tmp3" || exit 2

# --- H4: correct the comment this wiring falsifies -----------------------------------------
# `--self-test` takes the run_guards path, so once this guard is wired that path DOES contact
# the oracle's database. Leaving the old sentence standing would make this file lie about
# itself -- the exact defect class this program keeps finding in prose cardinals (P-80).
awk -v a4="$A4" '
  index($0, a4) > 0 && !done {
    print "  #     `--self-test` is used for the end-to-end arms because it exercises the identical"
    print "  #     load_toolchain -> run_guards path a graded run takes. SINCE T390 THAT PATH DOES"
    print "  #     CONTACT THE ORACLE'\''S DATABASE, through guard_oracle_state_attributed, which is"
    print "  #     why that guard SKIPS rather than fails when the database is unreachable: this"
    print "  #     arm must keep working on a host with no docker. Cost is about 7s plus 1-2s for"
    print "  #     the baseline instrument [T390, measured]. The RED arm must also show it never"
    done = 1
    next
  }
  { print }
' "$PATCHED.tmp3" > "$PATCHED" || exit 2

# H4 replaced two source lines with six, and the second source line ("about 7s. The RED arm
# must also show it never reached the guards downstream of the") must now go, since its text
# was folded above. Assert it is where we think it is, then drop it.
nxt='#     about 7s. The RED arm must also show it never reached the guards downstream of the'
n=$(LC_ALL=C grep -cF -- "$nxt" "$PATCHED")
[ "$n" = "1" ] || { echo "REFUSING: H4 follow-on line occurs $n times, expected 1" >&2; exit 2; }
LC_ALL=C grep -vF -- "$nxt" "$PATCHED" > "$PATCHED.tmp4" && mv "$PATCHED.tmp4" "$PATCHED"

rm -f "$PATCHED.tmp1" "$PATCHED.tmp2" "$PATCHED.tmp3"

# --- the diff, and the proof that it applies ----------------------------------------------
( cd "$ROOT" && diff -u .softhouse/conformance.sh "$PATCHED" ) > "$PATCH"
# diff exits 1 when files differ, which is the expected case; 2 is a real error.
drc=$?
[ "$drc" -le 1 ] || { echo "REFUSING: diff failed rc=$drc" >&2; exit 2; }
[ -s "$PATCH" ]  || { echo "REFUSING: the patch is EMPTY -- no hunk landed" >&2; exit 2; }

# Rewrite the diff headers so `git apply` accepts it against the tracked path.
{
  printf -- '--- a/.softhouse/conformance.sh\n'
  printf -- '+++ b/.softhouse/conformance.sh\n'
  tail -n +3 "$PATCH"
} > "$PATCH.tmp" && mv "$PATCH.tmp" "$PATCH"

if ( cd "$ROOT" && git apply --check "$PATCH" ) 2>/dev/null; then
  echo "PATCH APPLIES CLEANLY: git apply --check ok"
else
  echo "REFUSING: git apply --check REJECTED the generated patch." >&2
  exit 1
fi

# --- shape assertions on the result, so a silently-empty hunk cannot pass ------------------
fails=0
chk() { # chk <what> <expected-count> <pattern>
  local n; n=$(LC_ALL=C grep -cF -- "$3" "$PATCHED")
  if [ "$n" = "$2" ]; then printf '  ok   %-52s = %s\n' "$1" "$n"
  else printf '  ***  %-52s = %s, expected %s\n' "$1" "$n" "$2"; fails=$((fails+1)); fi
}
echo "PATCHED FILE SHAPE"
chk "guard_oracle_state_attributed() definition"  1 "guard_oracle_state_attributed() {"
chk "GUARD_COST_BUDGETS row"                      1 "guard_oracle_state_attributed|60"
chk "timed_guard call in run_guards"              1 "timed_guard guard_oracle_state_attributed"
chk "the falsified 'contacts NO oracle' sentence" 0 "contacts NO oracle"
echo "  patch: $PATCH ($(wc -l < "$PATCH" | tr -d ' ') lines)"
[ "$fails" -eq 0 ] || exit 1
echo "GENERATOR VERDICT: patch built, applies cleanly, and has the shape it claims (exit 0)."
