#!/usr/bin/env bash
# T326 -- RUN THE WHOLE BAR IN BOTH DISK CONDITIONS.
#
# WHY THIS EXISTS SEPARATELY FROM 20-cross-host-drive.sh. That drive proves the CENSUS is
# host-invariant. This one proves the claim that actually matters to the two fires: THE BAR'S
# EXIT STATUS AND PROBE LINE ARE THE SAME whether or not untracked state is materialised. Those
# are different claims -- the census could be invariant and the wiring still reach a different
# verdict -- and P-45's whole lesson is that "the guard is fine" and "the path that actually
# executes is fine" are two statements.
#
#     P-45 -- "A test-only guard is not a guard. ... Rule: when hardening a check, verify the
#     path that ACTUALLY EXECUTES in CI/conformance calls it, not merely that a test does."
#     [VERIFIED: .softhouse/patterns.md:1472]
#
# THE CONDITIONS are the two the driver of fire 20260827-230001 actually had:
#     A  no `.softhouse/toolchain`                    (any worktree; the cloud fire)
#     B  `.softhouse/toolchain` + T82 run residue     (Buyan's Mac after a run)
#
# THE ASSERTION, in P-84's order -- PRESENCE BEFORE VALUE:
#     "P-84 -- 'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE
#     VALUE."   [VERIFIED: .softhouse/patterns.md:2782]
# so each condition is required to (1) PRINT the probe line, (2) have it read `up`, and (3) exit
# 0 -- and then the two conditions are required to agree on all three. A run that exits 2 with no
# probe line is reported as a FAILED HARD GUARD, never as an oracle outage.
#
# IT RUNS THE BAR TWICE, so it costs about twice a bar (~100 s). It is a capture instrument and
# is deliberately NOT wired into conformance.sh: wiring it would make every graded run pay for
# two extra bars, and it would recurse.
#
# EXIT: 0 both conditions agree and are green; 1 they disagree, or one is not green; 2 refusal.
# PROBE: `T326-BOTHCONDITIONS:` printed only on a path that reaches a verdict.

set -u

PROBE="T326-BOTHCONDITIONS:"
SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SELF_DIR/../../../.." && pwd)

BAR="$ROOT/.softhouse/conformance.sh"
TOOLCHAIN="$ROOT/.softhouse/toolchain"
RESIDUE="$ROOT/.softhouse/capture/t74-multiplesof/T82-guard-proofs/scratch"

[ -f "$BAR" ] || { echo "ERROR: no bar at $BAR. REFUSING (exit 2)." >&2; exit 2; }
for p in "$TOOLCHAIN" "$RESIDUE"; do
  if [ -e "$p" ]; then
    echo "ERROR: $p already exists; this instrument CREATES and REMOVES it and will not delete" >&2
    echo "ERROR: a pre-existing one. Run it in a fresh worktree. REFUSING (exit 2)." >&2
    exit 2
  fi
done

OUT="$SELF_DIR/../evidence"
mkdir -p "$OUT" || { echo "ERROR: cannot create $OUT. REFUSING (exit 2)." >&2; exit 2; }

CREATED=""
cleanup() { for c in $CREATED; do rm -rf "$c"; done; }
trap cleanup EXIT INT TERM

# run_bar <tag>  -> sets rc_<tag>, probe_<tag>, val_<tag>
run_bar() {
  tag=$1
  f="$OUT/20-bar-$tag.txt"
  # `bash`, never `sh`: sh exits 3, a wrong-interpreter refusal, which is not a result.
  ( cd "$ROOT" && bash .softhouse/conformance.sh ) >"$f" 2>&1
  rc=$?
  if LC_ALL=C grep -q 'reference oracle (.*) probe = ' "$f"; then
    probe=PRESENT
    val=$(LC_ALL=C sed -n 's/.*reference oracle (.*) probe = \([a-z][a-z]*\).*/\1/p' "$f" | tail -1)
  else
    probe=ABSENT
    val="(none)"
  fi
  printf '  %-22s exit=%-3s probe=%-8s value=%-8s  -> %s\n' "$tag" "$rc" "$probe" "$val" "$f"
  eval "rc_$tag=\$rc; probe_$tag=\$probe; val_$tag=\$val"
}

echo "T326 -- THE WHOLE BAR IN BOTH DISK CONDITIONS"
echo "root: $ROOT"
echo "HEAD: $(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo '(unknown)')"
echo "======================================================================================"

run_bar A_bare

mkdir -p "$TOOLCHAIN/go" "$TOOLCHAIN/gocache" "$TOOLCHAIN/gomodcache" || exit 2
CREATED="$CREATED $TOOLCHAIN"
mkdir -p "$RESIDUE" || exit 2
CREATED="$CREATED $RESIDUE"
: >"$RESIDUE/17a-capture.json" || exit 2

run_bar B_hoststate

echo "--------------------------------------------------------------------------------------"
fail=0

# (1) PRESENCE, in both conditions, before any value is read.
for tag in A_bare B_hoststate; do
  eval "p=\$probe_$tag; r=\$rc_$tag"
  if [ "$p" != PRESENT ]; then
    echo "  FAIL  $tag: NO PROBE LINE PRINTED with exit=$r."
    echo "        Under P-84 that is a FAILED HARD GUARD, not an oracle outage. Read the bar."
    fail=$((fail + 1))
  fi
done

# (2) VALUE and (3) EXIT, only once presence holds.
if [ "$fail" -eq 0 ]; then
  for tag in A_bare B_hoststate; do
    eval "v=\$val_$tag; r=\$rc_$tag"
    if [ "$v" != up ]; then
      echo "  FAIL  $tag: probe line present but reads '$v', not 'up'. The oracle is not up; this"
      echo "        instrument cannot distinguish a host-state defect from an outage in that state."
      fail=$((fail + 1))
    fi
    if [ "$r" != 0 ]; then
      echo "  FAIL  $tag: bar exited $r, not 0."
      fail=$((fail + 1))
    fi
  done
fi

# (4) THE ACTUAL CLAIM: the two conditions agree.
if [ "$rc_A_bare" = "$rc_B_hoststate" ] \
   && [ "$probe_A_bare" = "$probe_B_hoststate" ] \
   && [ "$val_A_bare" = "$val_B_hoststate" ]; then
  echo "  PASS  the two conditions AGREE: exit=$rc_A_bare probe=$probe_A_bare value=$val_A_bare"
else
  echo "  FAIL  THE TWO CONDITIONS DISAGREE. The bar's verdict is still a function of host state."
  echo "        A: exit=$rc_A_bare probe=$probe_A_bare value=$val_A_bare"
  echo "        B: exit=$rc_B_hoststate probe=$probe_B_hoststate value=$val_B_hoststate"
  fail=$((fail + 1))
fi

# (5) And the frontier probe line itself must carry the same cardinals in both conditions --
#     the specific number the driver watched move from 102 to 78.
fa=$(LC_ALL=C grep -h 'T316-DEADPATH-CENSUS:' "$OUT/20-bar-A_bare.txt" | tail -1)
fb=$(LC_ALL=C grep -h 'T316-DEADPATH-CENSUS:' "$OUT/20-bar-B_hoststate.txt" | tail -1)
if [ -z "$fa" ] || [ -z "$fb" ]; then
  echo "  FAIL  the T316 census probe line is missing from one or both bars. It is not possible"
  echo "        to compare cardinals that were never printed (P-81: an unreadable measurement is"
  echo "        an ERROR, never a zero)."
  fail=$((fail + 1))
elif [ "$fa" = "$fb" ]; then
  echo "  PASS  identical T316 census cardinals in both conditions:"
  echo "        $fa"
else
  echo "  FAIL  the T316 census cardinals DIFFER between conditions:"
  echo "        A: $fa"
  echo "        B: $fb"
  fail=$((fail + 1))
fi

echo "--------------------------------------------------------------------------------------"
if [ "$fail" -eq 0 ]; then
  echo "$PROBE GREEN fail=0"
  exit 0
fi
echo "$PROBE RED fail=$fail"
exit 1
